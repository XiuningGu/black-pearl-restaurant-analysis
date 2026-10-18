# Public dataset dictionary

The definitions below apply to `data/public/black_pearl_restaurants.csv` and the `restaurants` worksheet in `data/public/black_pearl_restaurants.xlsx`.

| Field | Type | Meaning |
|---|---|---|
| `restaurant_id` | text | Stable project ID in source-row order |
| `source_row` | integer | Original Excel row number, including the header row offset |
| `region_cn` | text | Standardized Chinese region label |
| `region_en` | text | Standardized English region label |
| `region_source` | text | Original bilingual region value |
| `city_cn` | text | Standardized Chinese city/location label |
| `city_en` | text | Standardized English city/location label; obvious source spelling/case errors are corrected |
| `city_source` | text | Original bilingual city/location value |
| `diamond_level` | integer | Black Pearl one-, two- or three-diamond category |
| `restaurant_name` | text | Restaurant name as collected |
| `cuisine_source` | text | Original cuisine label; one value is missing |
| `cuisine_category_cn` | text | Text before the first hyphen, or the full cuisine label when no hyphen exists |
| `cuisine_detail_cn` | text | Text after the first hyphen when present |
| `total_score` | numeric | Public platform total score |
| `taste_score` | numeric | Public taste subscore |
| `environment_score` | numeric | Public environment subscore |
| `service_score` | numeric | Public service subscore |
| `review_count` | integer | Number of public evaluations/reviews recorded at collection |
| `favourites_count` | integer | Number of public favourites recorded at collection |
| `years_open` | numeric | Reported operating duration in years |
| `annual_star_count` | integer | Number of Annual Star Merchant recognitions recorded |
| `black_pearl_listing_count` | integer | Number of Black Pearl Guide listings recorded |
| `avg_price_cny` | numeric | Average price per person in CNY |
| `branch_count` | integer | Number of branches in the same city recorded at collection |
| `ingredient_score` | numeric | Ingredient score parsed from the source note field; available for 21 records |

The internal file `data/processed/black_pearl_clean.csv` retains audit fields, including the raw note text, the redundant `favourites_thousands` field and a city/name review key. It is not the recommended public download.
