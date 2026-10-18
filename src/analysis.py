"""Reproduce and audit the 2024 Black Pearl restaurant analysis.

Run from the repository root:

    python src/analysis.py

The script cleans the supplied workbook, reproduces the paper's main results,
adds diagnostic checks, writes tables, draws figures, and refreshes the
portfolio notebook.
"""

from __future__ import annotations

import json
import math
from itertools import combinations
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats


COLUMN_MAP = {
    "地区 Area": "region",
    "城市": "city",
    "钻级 Diamond Level": "diamond_level",
    "名字 Name": "restaurant_name",
    "菜系 Cuisine": "cuisine",
    " Total Score": "total_score",
    "Taste Score": "taste_score",
    "Environment Score": "environment_score",
    "Service Score": "service_score",
    "hello": "favourites_thousands",
    "评价量 # of evaluation  ": "review_count",
    "时长 / 年 Time / years": "years_open",
    'Winning "Annual Star Merchant" / times': "annual_star_count",
    'Listed on "Black Pearl Restaurant Guide"/ times': "black_pearl_listing_count",
    "人均价格/¥ Average price per person ": "avg_price_cny",
    "同城分店数量 / Number of branches in the same city": "branch_count",
    "Unnamed: 16": "notes",
    "收藏量 # of favourites": "favourites_count",
}

REGION_LABELS = {
    "上海 Shanghai": "Shanghai",
    "华北地区 North China": "North China",
    "偏西南地区 Southwest China": "Southwest China",
    "华中地区 Central China": "Central China",
    "华南地区 South China": "South China",
    "江浙地区 Jiangsu and Zhejiang region": "Jiangsu-Zhejiang",
}


def clean_data(raw_path: Path) -> pd.DataFrame:
    """Load the source workbook and apply transparent column-level cleaning."""
    raw = pd.read_excel(raw_path, sheet_name="Sheet1")
    missing_columns = sorted(set(COLUMN_MAP) - set(raw.columns))
    if missing_columns:
        raise ValueError(f"Missing expected columns: {missing_columns}")

    data = raw[list(COLUMN_MAP)].rename(columns=COLUMN_MAP).copy()
    data.insert(0, "source_row", np.arange(2, len(data) + 2))
    for column in ["region", "city", "restaurant_name", "cuisine", "notes"]:
        data[column] = data[column].map(
            lambda value: value.strip() if isinstance(value, str) else value
        )
    data["region_short"] = data["region"].map(REGION_LABELS)
    data["restaurant_key"] = (
        data["city"].astype(str).str.strip()
        + " | "
        + data["restaurant_name"].astype(str).str.strip()
    )

    # This source column is exactly favourites_count / 1,000. Retain it for
    # provenance and verify the relationship rather than silently deleting it.
    scale_error = (
        data["favourites_thousands"] * 1000 - data["favourites_count"]
    ).abs().max()
    if not np.isclose(scale_error, 0.0):
        raise ValueError("The favourites_thousands source field is inconsistent.")

    return data


def _ols_core(y: np.ndarray, x: np.ndarray) -> dict:
    y = np.asarray(y, dtype=float)
    x = np.asarray(x, dtype=float)
    design = np.column_stack([np.ones(len(y)), x])
    xtx_inv = np.linalg.inv(design.T @ design)
    params = np.linalg.lstsq(design, y, rcond=None)[0]
    fitted = design @ params
    residuals = y - fitted
    n, k = design.shape
    df_resid = n - k
    sse = float(residuals @ residuals)
    sst = float(((y - y.mean()) ** 2).sum())
    mse = sse / df_resid
    r_squared = 1 - sse / sst
    adjusted_r_squared = 1 - (1 - r_squared) * (n - 1) / df_resid
    covariance = mse * xtx_inv
    standard_error = np.sqrt(np.diag(covariance))
    t_stat = params / standard_error
    p_value = 2 * stats.t.sf(np.abs(t_stat), df_resid)
    critical = stats.t.ppf(0.975, df_resid)

    leverage = np.sum((design @ xtx_inv) * design, axis=1)
    hc3_weights = residuals**2 / np.maximum(1 - leverage, 1e-12) ** 2
    hc3_meat = design.T @ (design * hc3_weights[:, None])
    hc3_covariance = xtx_inv @ hc3_meat @ xtx_inv
    hc3_standard_error = np.sqrt(np.diag(hc3_covariance))
    hc3_t_stat = params / hc3_standard_error
    hc3_p_value = 2 * stats.t.sf(np.abs(hc3_t_stat), df_resid)

    model_df = k - 1
    f_stat = ((sst - sse) / model_df) / mse
    f_p_value = stats.f.sf(f_stat, model_df, df_resid)

    cooks_distance = (
        (residuals**2 / (k * mse)) * leverage / np.maximum(1 - leverage, 1e-12) ** 2
    )

    return {
        "params": params,
        "standard_error": standard_error,
        "t_stat": t_stat,
        "p_value": p_value,
        "ci_low": params - critical * standard_error,
        "ci_high": params + critical * standard_error,
        "hc3_standard_error": hc3_standard_error,
        "hc3_t_stat": hc3_t_stat,
        "hc3_p_value": hc3_p_value,
        "fitted": fitted,
        "residuals": residuals,
        "leverage": leverage,
        "cooks_distance": cooks_distance,
        "n": n,
        "k": k,
        "df_resid": df_resid,
        "sse": sse,
        "mse": mse,
        "rmse": math.sqrt(mse),
        "r_squared": r_squared,
        "adjusted_r_squared": adjusted_r_squared,
        "f_stat": f_stat,
        "f_p_value": f_p_value,
    }


def ols_fit(data: pd.DataFrame, y_col: str, x_cols: list[str]) -> tuple[pd.DataFrame, dict]:
    """OLS with classical and HC3 inference, implemented with NumPy/SciPy."""
    model_data = data[[y_col, *x_cols]].dropna()
    fit = _ols_core(model_data[y_col].to_numpy(), model_data[x_cols].to_numpy())
    terms = ["Intercept", *x_cols]
    table = pd.DataFrame(
        {
            "term": terms,
            "coefficient": fit["params"],
            "standard_error": fit["standard_error"],
            "t_stat": fit["t_stat"],
            "p_value": fit["p_value"],
            "ci_95_low": fit["ci_low"],
            "ci_95_high": fit["ci_high"],
            "hc3_standard_error": fit["hc3_standard_error"],
            "hc3_t_stat": fit["hc3_t_stat"],
            "hc3_p_value": fit["hc3_p_value"],
        }
    )
    return table, fit


def standardized_betas(data: pd.DataFrame, y_col: str, x_cols: list[str]) -> pd.DataFrame:
    z = data[[y_col, *x_cols]].dropna().apply(lambda s: (s - s.mean()) / s.std(ddof=1))
    fit = _ols_core(z[y_col].to_numpy(), z[x_cols].to_numpy())
    return pd.DataFrame(
        {
            "term": x_cols,
            "standardized_beta": fit["params"][1:],
        }
    )


def vif_table(data: pd.DataFrame, x_cols: list[str]) -> pd.DataFrame:
    rows = []
    clean = data[x_cols].dropna()
    for col in x_cols:
        other_cols = [candidate for candidate in x_cols if candidate != col]
        fit = _ols_core(clean[col].to_numpy(), clean[other_cols].to_numpy())
        rows.append(
            {
                "term": col,
                "auxiliary_r_squared": fit["r_squared"],
                "vif": 1 / (1 - fit["r_squared"]),
            }
        )
    return pd.DataFrame(rows)


def holm_adjust(p_values: np.ndarray) -> np.ndarray:
    p_values = np.asarray(p_values, dtype=float)
    order = np.argsort(p_values)
    sorted_p = p_values[order]
    adjusted_sorted = np.maximum.accumulate(
        np.minimum(1.0, sorted_p * (len(sorted_p) - np.arange(len(sorted_p))))
    )
    adjusted = np.empty_like(adjusted_sorted)
    adjusted[order] = adjusted_sorted
    return adjusted


def award_tests(data: pd.DataFrame) -> pd.DataFrame:
    annual = data["annual_star_count"].to_numpy()
    black_pearl = data["black_pearl_listing_count"].to_numpy()
    differences = annual - black_pearl

    wilcoxon = stats.wilcoxon(annual, black_pearl, alternative="two-sided")
    spearman = stats.spearmanr(annual, black_pearl)
    nonzero = differences[differences != 0]
    ranks = stats.rankdata(np.abs(nonzero))
    positive_rank_sum = ranks[nonzero > 0].sum()
    negative_rank_sum = ranks[nonzero < 0].sum()
    rank_biserial = (positive_rank_sum - negative_rank_sum) / (
        positive_rank_sum + negative_rank_sum
    )
    paired_cohens_dz = differences.mean() / differences.std(ddof=1)
    pooled_sd = math.sqrt((annual.var(ddof=1) + black_pearl.var(ddof=1)) / 2)
    paper_style_d = (annual.mean() - black_pearl.mean()) / pooled_sd

    return pd.DataFrame(
        [
            {"metric": "annual_star_mean", "value": annual.mean()},
            {"metric": "black_pearl_listing_mean", "value": black_pearl.mean()},
            {"metric": "mean_paired_difference", "value": differences.mean()},
            {"metric": "median_paired_difference", "value": np.median(differences)},
            {"metric": "wilcoxon_statistic", "value": wilcoxon.statistic},
            {"metric": "wilcoxon_p_value", "value": wilcoxon.pvalue},
            {"metric": "rank_biserial_correlation", "value": rank_biserial},
            {"metric": "spearman_rho", "value": spearman.statistic},
            {"metric": "spearman_p_value", "value": spearman.pvalue},
            {"metric": "paired_cohens_dz", "value": paired_cohens_dz},
            {
                "metric": "paper_style_pooled_d_not_paired",
                "value": paper_style_d,
            },
        ]
    )


def cuisine_region_test(
    data: pd.DataFrame, permutations: int = 5000, seed: int = 20261018
) -> pd.DataFrame:
    complete = data[["region", "cuisine"]].dropna()
    table = pd.crosstab(complete["region"], complete["cuisine"])
    chi_squared, asymptotic_p, degrees_freedom, expected = stats.chi2_contingency(table)
    n = int(table.to_numpy().sum())
    rows, columns = table.shape
    cramers_v = math.sqrt(chi_squared / (n * min(rows - 1, columns - 1)))

    region_lookup = {label: index for index, label in enumerate(table.index.tolist())}
    cuisine_lookup = {label: index for index, label in enumerate(table.columns.tolist())}
    region_codes = complete["region"].map(region_lookup).to_numpy(dtype=int)
    cuisine_codes = complete["cuisine"].map(cuisine_lookup).to_numpy(dtype=int)
    if (region_codes < 0).any() or (cuisine_codes < 0).any():
        raise ValueError("Unexpected unmapped label in the cuisine-region test.")
    rng = np.random.default_rng(seed)
    exceedances = 0
    for _ in range(permutations):
        permuted = rng.permutation(cuisine_codes)
        counts = np.bincount(
            region_codes * columns + permuted,
            minlength=rows * columns,
        ).reshape(rows, columns)
        permuted_chi_squared = np.sum((counts - expected) ** 2 / expected)
        exceedances += int(permuted_chi_squared >= chi_squared)
    permutation_p = (exceedances + 1) / (permutations + 1)

    return pd.DataFrame(
        [
            {"metric": "complete_observations", "value": n},
            {"metric": "chi_squared", "value": chi_squared},
            {"metric": "degrees_freedom", "value": degrees_freedom},
            {"metric": "asymptotic_p_value", "value": asymptotic_p},
            {"metric": "cramers_v", "value": cramers_v},
            {"metric": "expected_cells", "value": expected.size},
            {"metric": "expected_cells_below_5", "value": int((expected < 5).sum())},
            {
                "metric": "expected_cells_below_5_pct",
                "value": float((expected < 5).mean() * 100),
            },
            {"metric": "permutations", "value": permutations},
            {"metric": "permutation_p_value", "value": permutation_p},
        ]
    )


def region_price_tests(data: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    groups = {
        region: group["avg_price_cny"].dropna().to_numpy()
        for region, group in data.groupby("region_short", sort=True)
    }
    kruskal = stats.kruskal(*groups.values())
    omnibus = pd.DataFrame(
        [
            {"metric": "kruskal_h", "value": kruskal.statistic},
            {"metric": "kruskal_p_value", "value": kruskal.pvalue},
            {"metric": "number_of_regions", "value": len(groups)},
        ]
    )

    pairwise_rows = []
    for first, second in combinations(groups, 2):
        test = stats.mannwhitneyu(groups[first], groups[second], alternative="two-sided")
        pairwise_rows.append(
            {
                "region_1": first,
                "region_2": second,
                "n_1": len(groups[first]),
                "n_2": len(groups[second]),
                "median_1_cny": np.median(groups[first]),
                "median_2_cny": np.median(groups[second]),
                "u_statistic": test.statistic,
                "p_value": test.pvalue,
            }
        )
    pairwise = pd.DataFrame(pairwise_rows)
    pairwise["p_value_holm"] = holm_adjust(pairwise["p_value"].to_numpy())
    pairwise["significant_0_05"] = pairwise["p_value_holm"] < 0.05
    return omnibus, pairwise.sort_values("p_value_holm").reset_index(drop=True)


def regression_diagnostics(data: pd.DataFrame, fit: dict) -> pd.DataFrame:
    residuals = fit["residuals"]
    fitted = fit["fitted"]
    shapiro = stats.shapiro(residuals)
    auxiliary = _ols_core(residuals**2, fitted[:, None])
    breusch_pagan_lm = len(residuals) * auxiliary["r_squared"]
    breusch_pagan_p = stats.chi2.sf(breusch_pagan_lm, 1)
    cooks_threshold = 4 / len(residuals)
    return pd.DataFrame(
        [
            {"metric": "shapiro_w", "value": shapiro.statistic},
            {"metric": "shapiro_p_value", "value": shapiro.pvalue},
            {"metric": "breusch_pagan_lm", "value": breusch_pagan_lm},
            {"metric": "breusch_pagan_p_value", "value": breusch_pagan_p},
            {"metric": "cooks_distance_threshold_4_over_n", "value": cooks_threshold},
            {
                "metric": "observations_above_cooks_threshold",
                "value": int((fit["cooks_distance"] > cooks_threshold).sum()),
            },
            {"metric": "maximum_cooks_distance", "value": fit["cooks_distance"].max()},
        ]
    )


def _write_figures(data: pd.DataFrame, regression: pd.DataFrame, fit: dict, figures_dir: Path) -> None:
    plt.style.use("seaborn-v0_8-whitegrid")
    figures_dir.mkdir(parents=True, exist_ok=True)

    score_columns = [
        ("total_score", "Total score"),
        ("taste_score", "Taste score"),
        ("environment_score", "Environment score"),
        ("service_score", "Service score"),
    ]
    fig, axes = plt.subplots(2, 2, figsize=(10, 7), sharex=True)
    bins = np.arange(3.85, 5.06, 0.1)
    for axis, (column, title) in zip(axes.flat, score_columns):
        axis.hist(data[column], bins=bins, color="#2F6B8A", edgecolor="white")
        axis.axvline(data[column].mean(), color="#D95F02", linewidth=1.8, label="Mean")
        axis.set_title(title)
        axis.set_ylabel("Restaurants")
        axis.legend(frameon=False)
    axes[1, 0].set_xlabel("Score")
    axes[1, 1].set_xlabel("Score")
    fig.suptitle("Distribution of public platform ratings (n=233)", fontsize=14)
    fig.tight_layout()
    fig.savefig(figures_dir / "score_distributions.png", dpi=180, bbox_inches="tight")
    plt.close(fig)

    coef = regression[regression["term"] != "Intercept"].copy()
    labels = ["Taste", "Environment", "Service"]
    xerr = np.vstack(
        [
            coef["coefficient"] - coef["ci_95_low"],
            coef["ci_95_high"] - coef["coefficient"],
        ]
    )
    fig, axis = plt.subplots(figsize=(8, 4.5))
    positions = np.arange(len(coef))
    axis.errorbar(
        coef["coefficient"],
        positions,
        xerr=xerr,
        fmt="o",
        color="#2F6B8A",
        ecolor="#7A9E9F",
        capsize=4,
    )
    axis.axvline(0, color="black", linewidth=0.8)
    axis.set_yticks(positions, labels)
    axis.invert_yaxis()
    axis.set_xlabel("Unstandardized OLS coefficient (95% CI)")
    axis.set_title("Association with total score")
    fig.tight_layout()
    fig.savefig(figures_dir / "regression_coefficients.png", dpi=180, bbox_inches="tight")
    plt.close(fig)

    counts = (
        data.groupby(["annual_star_count", "black_pearl_listing_count"])
        .size()
        .reset_index(name="restaurants")
    )
    fig, axis = plt.subplots(figsize=(7, 5.5))
    scatter = axis.scatter(
        counts["annual_star_count"],
        counts["black_pearl_listing_count"],
        s=counts["restaurants"] * 18,
        c=counts["restaurants"],
        cmap="Blues",
        alpha=0.8,
        edgecolor="white",
    )
    axis.set_xlabel("Annual Star Merchant count")
    axis.set_ylabel("Black Pearl listing count")
    axis.set_title("Award-count relationship (bubble size = restaurants)")
    fig.colorbar(scatter, ax=axis, label="Restaurants")
    fig.tight_layout()
    fig.savefig(figures_dir / "award_relationship.png", dpi=180, bbox_inches="tight")
    plt.close(fig)

    order = [
        "Shanghai",
        "North China",
        "Southwest China",
        "Central China",
        "South China",
        "Jiangsu-Zhejiang",
    ]
    price_groups = [
        data.loc[data["region_short"] == region, "avg_price_cny"].to_numpy()
        for region in order
    ]
    fig, axis = plt.subplots(figsize=(10, 5.5))
    axis.boxplot(price_groups, tick_labels=order, showfliers=True)
    axis.set_ylabel("Average price per person (CNY)")
    axis.set_title("Price distribution by region")
    axis.tick_params(axis="x", rotation=25)
    fig.tight_layout()
    fig.savefig(figures_dir / "price_by_region.png", dpi=180, bbox_inches="tight")
    plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(10, 4.5))
    axes[0].scatter(fit["fitted"], fit["residuals"], alpha=0.65, color="#2F6B8A")
    axes[0].axhline(0, color="black", linewidth=0.8)
    axes[0].set_xlabel("Fitted total score")
    axes[0].set_ylabel("Residual")
    axes[0].set_title("Residuals vs fitted")
    stats.probplot(fit["residuals"], dist="norm", plot=axes[1])
    axes[1].set_title("Normal Q-Q plot")
    fig.tight_layout()
    fig.savefig(figures_dir / "residual_diagnostics.png", dpi=180, bbox_inches="tight")
    plt.close(fig)


def _stream_output(text: str) -> dict:
    return {"name": "stdout", "output_type": "stream", "text": text.rstrip() + "\n"}


def _markdown_cell(source: str) -> dict:
    return {"cell_type": "markdown", "metadata": {}, "source": source.splitlines(keepends=True)}


def _code_cell(source: str, execution_count: int, output: str | None = None) -> dict:
    outputs = [] if output is None else [_stream_output(output)]
    return {
        "cell_type": "code",
        "execution_count": execution_count,
        "metadata": {},
        "outputs": outputs,
        "source": source.splitlines(keepends=True),
    }


def _build_notebook(project_root: Path, outputs: dict[str, pd.DataFrame]) -> None:
    notebook_path = project_root / "notebooks" / "black_pearl_python_replication.ipynb"
    regression_comparison = outputs["regression_comparison"].round(6).to_string(index=False)
    regression_table = outputs["regression"].round(6).to_string(index=False)
    beta_table = outputs["standardized_betas"].round(6).to_string(index=False)
    vif = outputs["vif"].round(4).to_string(index=False)
    awards = outputs["awards"].round(6).to_string(index=False)
    cuisine_region = outputs["cuisine_region"].round(6).to_string(index=False)
    region_omnibus = outputs["region_omnibus"].round(6).to_string(index=False)
    diamond = outputs["diamond_summary"].round(4).to_string(index=False)

    cells = [
        _markdown_cell(
            "# Black Pearl Restaurant Analysis: Python Replication\n\n"
            "This notebook reproduces the core statistical results in the original 2024 report "
            "using the final 233-restaurant dataset. It also audits sample versions, effect-size "
            "definitions, model assumptions, and claims that the original report could not support."
        ),
        _code_cell(
            "from pathlib import Path\n"
            "import sys\n"
            "import pandas as pd\n\n"
            "ROOT = Path.cwd().resolve()\n"
            "if ROOT.name == 'notebooks':\n"
            "    ROOT = ROOT.parent\n"
            "sys.path.insert(0, str(ROOT))\n"
            "from src.analysis import run_analysis\n\n"
            "# Rebuild every result and figure from the source workbook.\n"
            "artifacts = run_analysis(ROOT, build_notebook=False)\n"
            "data = pd.read_csv(ROOT / 'data/processed/black_pearl_clean.csv')\n"
            "print(f'Loaded {len(data)} restaurants and {len(data.columns)} cleaned fields.')",
            1,
            "Loaded 233 restaurants and 21 cleaned fields.",
        ),
        _markdown_cell(
            "## 1. Data audit\n\n"
            "The final source contains 233 restaurants. The workbook's old regression-output "
            "sheets used only the first 153 observations, while the coefficients printed in the "
            "paper came from all 233 observations. The `hello` field is exactly favourites divided "
            "by 1,000 and is retained only for provenance. Three city-name keys require manual review."
        ),
        _code_cell(
            "quality = pd.read_csv(ROOT / 'results/data_quality_summary.csv')\n"
            "print(quality.to_string(index=False))",
            2,
            outputs["data_quality"].to_string(index=False),
        ),
        _markdown_cell(
            "## 2. Descriptive results\n\n"
            "The published means for environment score (4.697), favourites (68,135), reviews "
            "(3,043), and years open (7.08) all match the 233-row dataset.\n\n"
            "![Score distributions](../figures/score_distributions.png)"
        ),
        _markdown_cell(
            "## 3. Sample-version reconciliation\n\n"
            "The table below explains why the historical workbook output and the final paper differ."
        ),
        _code_cell(
            "comparison = pd.read_csv(ROOT / 'results/regression_sample_comparison.csv')\n"
            "print(comparison.round(6).to_string(index=False))",
            3,
            regression_comparison,
        ),
        _markdown_cell(
            "## 4. Core OLS replication\n\n"
            "The response is the public platform total score. Predictors are the public taste, "
            "environment, and service subscores. These estimates reproduce the formula in the paper. "
            "They do **not** reveal the confidential Black Pearl jury selection weights."
        ),
        _code_cell(
            "regression = pd.read_csv(ROOT / 'results/core_regression.csv')\n"
            "print(regression.round(6).to_string(index=False))",
            4,
            regression_table,
        ),
        _markdown_cell(
            "The fitted equation is:\n\n"
            "$$\\widehat{TotalScore}=0.1817+0.6174(Taste)+0.1963(Environment)+0.1436(Service)$$\n\n"
            "Model $R^2=0.8925$ and adjusted $R^2=0.8911$. The paper called the three slopes "
            "standardized coefficients, but they are unstandardized slopes.\n\n"
            "![Regression coefficients](../figures/regression_coefficients.png)"
        ),
        _code_cell(
            "betas = pd.read_csv(ROOT / 'results/standardized_betas.csv')\n"
            "vif = pd.read_csv(ROOT / 'results/vif.csv')\n"
            "print('Standardized coefficients')\n"
            "print(betas.round(6).to_string(index=False))\n"
            "print('\\nVariance inflation factors')\n"
            "print(vif.round(4).to_string(index=False))",
            5,
            "Standardized coefficients\n"
            + beta_table
            + "\n\nVariance inflation factors\n"
            + vif,
        ),
        _markdown_cell(
            "The VIF values are below 5, although service has the highest shared variance. "
            "Because the outcome and predictors are rounded platform ratings, diagnostics should "
            "be interpreted cautiously. HC3 robust standard errors are included in the result table.\n\n"
            "![Residual diagnostics](../figures/residual_diagnostics.png)"
        ),
        _markdown_cell("## 5. Award-count analysis"),
        _code_cell(
            "awards = pd.read_csv(ROOT / 'results/award_tests.csv')\n"
            "print(awards.round(6).to_string(index=False))",
            6,
            awards,
        ),
        _markdown_cell(
            "The paired Wilcoxon test is significant and the counts are strongly associated "
            "(Spearman $\\rho=0.709$). The paper's $d=0.246$ can be reproduced only by using an "
            "independent-samples pooled standard deviation; paired $d_z$ is about 0.295 in magnitude.\n\n"
            "![Award relationship](../figures/award_relationship.png)"
        ),
        _markdown_cell("## 6. Cuisine and region"),
        _code_cell(
            "cuisine_region = pd.read_csv(ROOT / 'results/cuisine_region_test.csv')\n"
            "print(cuisine_region.round(6).to_string(index=False))",
            7,
            cuisine_region,
        ),
        _markdown_cell(
            "Cramér's V reproduces the paper (about 0.616), but 97.1% of expected cells are below "
            "5. The asymptotic chi-square p-value should not be trusted on its own, so this project "
            "adds a fixed-seed permutation test. Cuisine names are also geographically encoded, "
            "which makes part of the association structural rather than surprising."
        ),
        _markdown_cell("## 7. Regional price differences and diamond-level limitation"),
        _code_cell(
            "regional = pd.read_csv(ROOT / 'results/region_price_omnibus.csv')\n"
            "diamond = pd.read_csv(ROOT / 'results/diamond_summary.csv')\n"
            "print('Regional price test')\n"
            "print(regional.round(6).to_string(index=False))\n"
            "print('\\nDiamond-level summary')\n"
            "print(diamond.round(4).to_string(index=False))",
            8,
            "Regional price test\n"
            + region_omnibus
            + "\n\nDiamond-level summary\n"
            + diamond,
        ),
        _markdown_cell(
            "Only five observations are three-diamond restaurants, so a three-class prediction "
            "model would be unstable. A simple one-way ANOVA gives $p=0.846$, not the 0.489 value "
            "stated in the report; the earlier mixed-model specification was not preserved.\n\n"
            "![Regional prices](../figures/price_by_region.png)"
        ),
        _markdown_cell(
            "## Conclusion\n\n"
            "The Python analysis successfully reproduces the paper's main 233-row regression and "
            "descriptive statistics. The strongest defensible conclusion is that taste has the "
            "largest conditional association with the public total rating among listed restaurants. "
            "The analysis does not recover Black Pearl's confidential selection algorithm, and the "
            "diamond-level sample is too imbalanced for a reliable multiclass prediction model."
        ),
    ]

    notebook = {
        "cells": cells,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {"name": "python", "version": "3.11"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    notebook_path.write_text(json.dumps(notebook, ensure_ascii=False, indent=1), encoding="utf-8")


def run_analysis(project_root: Path, build_notebook: bool = True) -> dict[str, pd.DataFrame]:
    project_root = Path(project_root).resolve()
    raw_path = project_root / "data" / "raw" / "black_pearl_2024.xlsx"
    processed_dir = project_root / "data" / "processed"
    results_dir = project_root / "results"
    figures_dir = project_root / "figures"
    processed_dir.mkdir(parents=True, exist_ok=True)
    results_dir.mkdir(parents=True, exist_ok=True)

    data = clean_data(raw_path)
    data.to_csv(processed_dir / "black_pearl_clean.csv", index=False, encoding="utf-8-sig")

    duplicate_name_records = int(data.duplicated("restaurant_name", keep=False).sum())
    duplicate_key_records = int(data.duplicated("restaurant_key", keep=False).sum())
    quality = pd.DataFrame(
        [
            {"check": "restaurant_rows", "value": len(data)},
            {"check": "regions", "value": data["region"].nunique()},
            {"check": "city_labels", "value": data["city"].nunique()},
            {"check": "cuisine_labels_non_missing", "value": data["cuisine"].nunique(dropna=True)},
            {"check": "missing_cuisine", "value": int(data["cuisine"].isna().sum())},
            {"check": "three_diamond_rows", "value": int((data["diamond_level"] == 3).sum())},
            {"check": "duplicate_name_records", "value": duplicate_name_records},
            {"check": "duplicate_city_name_records", "value": duplicate_key_records},
            {"check": "non_empty_notes", "value": int(data["notes"].notna().sum())},
        ]
    )
    quality.to_csv(results_dir / "data_quality_summary.csv", index=False)
    data.loc[data.duplicated("restaurant_key", keep=False)].sort_values("restaurant_key").to_csv(
        results_dir / "duplicate_city_name_review.csv", index=False, encoding="utf-8-sig"
    )

    descriptive_columns = [
        "total_score",
        "taste_score",
        "environment_score",
        "service_score",
        "favourites_count",
        "review_count",
        "years_open",
        "annual_star_count",
        "black_pearl_listing_count",
        "avg_price_cny",
        "branch_count",
    ]
    descriptive = data[descriptive_columns].describe().T.reset_index(names="variable")
    descriptive.to_csv(results_dir / "descriptive_statistics.csv", index=False)

    predictors = ["taste_score", "environment_score", "service_score"]
    old_table, old_fit = ols_fit(data.iloc[:153], "total_score", predictors)
    regression, fit = ols_fit(data, "total_score", predictors)
    regression.to_csv(results_dir / "core_regression.csv", index=False)

    metrics = pd.DataFrame(
        [
            {"metric": "observations", "value": fit["n"]},
            {"metric": "r_squared", "value": fit["r_squared"]},
            {"metric": "adjusted_r_squared", "value": fit["adjusted_r_squared"]},
            {"metric": "rmse", "value": fit["rmse"]},
            {"metric": "f_stat", "value": fit["f_stat"]},
            {"metric": "f_p_value", "value": fit["f_p_value"]},
        ]
    )
    metrics.to_csv(results_dir / "core_regression_metrics.csv", index=False)

    comparison = pd.DataFrame(
        {
            "term": regression["term"],
            "coefficient_first_153": old_table["coefficient"],
            "coefficient_all_233": regression["coefficient"],
        }
    )
    comparison = pd.concat(
        [
            comparison,
            pd.DataFrame(
                [
                    {
                        "term": "R-squared",
                        "coefficient_first_153": old_fit["r_squared"],
                        "coefficient_all_233": fit["r_squared"],
                    },
                    {
                        "term": "Adjusted R-squared",
                        "coefficient_first_153": old_fit["adjusted_r_squared"],
                        "coefficient_all_233": fit["adjusted_r_squared"],
                    },
                ]
            ),
        ],
        ignore_index=True,
    )
    comparison.to_csv(results_dir / "regression_sample_comparison.csv", index=False)

    betas = standardized_betas(data, "total_score", predictors)
    betas.to_csv(results_dir / "standardized_betas.csv", index=False)
    vif = vif_table(data, predictors)
    vif.to_csv(results_dir / "vif.csv", index=False)
    diagnostics = regression_diagnostics(data, fit)
    diagnostics.to_csv(results_dir / "regression_diagnostics.csv", index=False)

    awards = award_tests(data)
    awards.to_csv(results_dir / "award_tests.csv", index=False)
    cuisine_region = cuisine_region_test(data)
    cuisine_region.to_csv(results_dir / "cuisine_region_test.csv", index=False)
    region_omnibus, region_pairwise = region_price_tests(data)
    region_omnibus.to_csv(results_dir / "region_price_omnibus.csv", index=False)
    region_pairwise.to_csv(results_dir / "region_price_pairwise.csv", index=False)

    diamond_summary = (
        data.groupby("diamond_level")["total_score"]
        .agg(observations="count", mean_total_score="mean", sd_total_score="std")
        .reset_index()
    )
    diamond_groups = [
        group["total_score"].to_numpy() for _, group in data.groupby("diamond_level")
    ]
    diamond_anova = stats.f_oneway(*diamond_groups)
    diamond_summary["anova_f"] = diamond_anova.statistic
    diamond_summary["anova_p_value"] = diamond_anova.pvalue
    diamond_summary.to_csv(results_dir / "diamond_summary.csv", index=False)

    _write_figures(data, regression, fit, figures_dir)

    outputs = {
        "data_quality": quality,
        "descriptive": descriptive,
        "regression": regression,
        "regression_metrics": metrics,
        "regression_comparison": comparison,
        "standardized_betas": betas,
        "vif": vif,
        "diagnostics": diagnostics,
        "awards": awards,
        "cuisine_region": cuisine_region,
        "region_omnibus": region_omnibus,
        "region_pairwise": region_pairwise,
        "diamond_summary": diamond_summary,
    }
    if build_notebook:
        _build_notebook(project_root, outputs)
    return outputs


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    generated = run_analysis(root, build_notebook=True)
    print("Analysis complete.")
    print(generated["regression"].round(6).to_string(index=False))
