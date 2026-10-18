# Methodology and interpretation notes

## Sample versions

The workbook contains 233 observations. Historical regression-output sheets contain results for only the first 153 observations. Both versions are reproduced to establish provenance; substantive reporting uses the final 233-row sample.

## Core regression

Ordinary least squares estimates public total score from public taste, environment, and service subscores. Classical and HC3 robust standard errors are reported. Standardized coefficients are calculated by z-scoring the response and predictors before fitting the same model.

This regression describes conditional association among platform rating fields. It does not identify causal effects and does not estimate confidential Black Pearl jury weights.

## Diagnostics

- VIF checks linear dependence among the three predictors.
- Shapiro-Wilk assesses residual normality, although discrete rounded scores make perfect normality unlikely.
- A Breusch-Pagan auxiliary regression checks heteroskedasticity.
- Cook's distance flags observations above $4/n$ for review; it does not automatically justify deleting them.
- HC3 inference is emphasized when classical assumptions are questionable.

## Award counts

The two award counts are paired within restaurant. The project reports a paired Wilcoxon signed-rank test, Spearman correlation, rank-biserial correlation, and paired Cohen's $d_z$. Statistical difference and association answer different questions and are presented separately.

## Cuisine and region

The original Pearson chi-square statistic and Cramér's V are reproduced. Because 97.1% of expected cells are below five, the project adds a fixed-seed permutation p-value. Cuisine labels that explicitly name a region make part of the association structural.

## Regional prices

Regional price distributions are compared with Kruskal-Wallis testing. Pairwise Mann-Whitney tests use Holm correction for multiple comparisons.

## Diamond level

The three-diamond group has only five observations. The project reports descriptive statistics and a one-way ANOVA for audit purposes but does not train a multiclass prediction model on this imbalanced outcome.

## Reproducibility

`src/analysis.py` rebuilds all derived files from the source workbook. The permutation test uses seed `20261018` and 5,000 permutations.

