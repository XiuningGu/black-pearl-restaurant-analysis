# Data dictionary

| Field | Type | Meaning |
|---|---|---|
| `source_row` | integer | Original Excel row number, including the header offset |
| `region` | text | Original bilingual regional grouping |
| `city` | text | Original city label |
| `diamond_level` | integer | Black Pearl one-, two-, or three-diamond category |
| `restaurant_name` | text | Restaurant name as collected |
| `cuisine` | text | Cuisine label; one value is missing |
| `total_score` | numeric | Public platform total score |
| `taste_score` | numeric | Public taste subscore |
| `environment_score` | numeric | Public environment subscore |
| `service_score` | numeric | Public service subscore |
| `favourites_thousands` | numeric | Source `hello` field; equals favourites divided by 1,000 |
| `review_count` | integer | Number of public evaluations/reviews |
| `years_open` | numeric | Reported operating duration in years |
| `annual_star_count` | integer | Number of Annual Star Merchant recognitions |
| `black_pearl_listing_count` | integer | Number of Black Pearl Guide listings |
| `avg_price_cny` | numeric | Average price per person in CNY |
| `branch_count` | integer | Number of branches in the same city |
| `notes` | text | Manually collected notes such as ingredient ratings |
| `favourites_count` | numeric | Raw number of favourites |
| `region_short` | text | Clean English region label used in figures |
| `restaurant_key` | text | Review key formed from city and restaurant name |

## Provenance

The observations were manually collected for the original 2024 research project from public restaurant pages. The processed file trims surrounding whitespace and standardizes column names but does not silently deduplicate records.

