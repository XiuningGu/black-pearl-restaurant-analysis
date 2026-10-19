# Dataset card

## Summary

This dataset contains 233 restaurants listed in the Black Pearl Restaurant Guide. Restaurant attributes and public rating fields were manually compiled from publicly visible Dianping/Meituan restaurant pages for an independent data-analysis project.

## Provenance

- Source platforms: Dianping/Meituan public restaurant pages.
- Collection method: manual transcription and organization in Excel.
- Exact collection date: not retained.
- Per-record source URLs: not retained.
- Guide/sample context: project materials identify the sample as the 2024 Black Pearl restaurant analysis dataset.

These missing provenance details are disclosed rather than reconstructed. Numeric counts and ratings should be treated as a historical snapshot, not current platform values.

## Contents

- 233 rows and 25 columns in the public release.
- Six project-defined regions and 23 city/location labels.
- Public ratings, engagement counts, price, operating duration, branch count, award/listing counts and cuisine labels.
- Stable project IDs and source-row references for traceability.

The canonical release is `data/public/black_pearl_restaurants.csv`. The Excel file contains the same table with filters, frozen headers and formatting.

## Cleaning decisions

- Source labels are retained in `*_source` fields.
- Region and city/location labels are also provided as separate Chinese and English fields.
- `顺德 shunde` is normalized to `Shunde`, and `天津 Tianjing` to `Tianjin`, while the original values remain available.
- `江西 Jiangxi` is retained even though Jiangxi is a province rather than a city; two records use this source label.
- Cuisine is split once at the first hyphen into category and detail fields.
- The unnamed source note field contains ingredient scores for 21 records; these are parsed into numeric `ingredient_score` values.
- The source `hello` column is omitted from the public release because it is exactly favourites divided by 1,000.
- Potential duplicate city/name keys are retained pending source verification.

## Known limitations

- The sample includes only selected listed restaurants and is not representative of all restaurants.
- One cuisine value is missing.
- Public ratings and counts may have changed since collection.
- Manual transcription may contain errors that cannot be checked without the original URLs and dates.
- Rating components and total score are related platform fields; regression coefficients are associations, not causal effects or hidden guide weights.
- Diamond-level groups are strongly imbalanced.

## Responsible use

Use the dataset for learning, portfolio review and independent analysis with clear attribution to this repository and to Dianping/Meituan as the underlying public-page source. This repository does not claim ownership of platform content or grant a separate license for commercial redistribution. Users should review applicable platform terms and verify records before publication, operational use or commercial reuse.
