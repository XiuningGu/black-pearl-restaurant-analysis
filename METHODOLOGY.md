# Methodology and interpretation notes

## Sample and historical worksheets

The analysis uses all 233 restaurant rows from `Sheet1`. The remaining worksheets are preserved as historical Excel outputs. One older regression output used only the first 153 observations; `results/regression_sample_comparison.csv` documents that version difference for quality control.

## Core regression

Ordinary least squares estimates public total score from public taste, environment and service subscores. The result table includes classical and HC3 robust standard errors. Standardized coefficients are calculated by z-scoring the response and predictors before fitting the same model.

This is a descriptive model of related platform rating fields. It does not identify causal effects and does not estimate confidential Black Pearl jury weights.

## Diagnostics

- VIF checks linear dependence among the three predictors.
- Shapiro–Wilk assesses residual normality, with the caveat that scores are rounded and discrete.
- The Koenker form of the Breusch–Pagan test regresses squared residuals on all three predictors and reports an LM statistic with three degrees of freedom.
- Cook's distance flags observations above $4/n$ for review; it does not justify automatic deletion.
- HC3 inference is emphasized because heteroskedasticity is detected.

## Award counts

The two award counts are paired within restaurants. The analysis reports a paired Wilcoxon signed-rank test, Spearman correlation, rank-biserial correlation and paired Cohen's $d_z$. Difference and association answer different questions.

## Cuisine and region

The contingency table is sparse: 97.1% of expected cells are below five. Cramér's V is retained as a descriptive effect size, and inference uses a fixed-seed permutation test. With zero exceedances among 5,000 permutations, $(0+1)/(5000+1)$ is reported as a Monte Carlo estimate/resolution bound rather than an exact p-value. Cuisine labels also encode geography, so part of the association is structural.

## Regional prices and diamond level

Regional price distributions are compared with Kruskal–Wallis testing. Pairwise Mann–Whitney tests use Holm correction. The three-diamond group has only five observations, so the project reports descriptive statistics and a one-way ANOVA but does not train a multiclass prediction model.

## Running and validation

`src/analysis.py` generates the public CSV, internal cleaned CSV, result tables, figures and output-free notebook from the preserved workbook. Randomized analysis uses seed `20261018` and 5,000 permutations. Dependency versions are pinned in `requirements.txt`.
