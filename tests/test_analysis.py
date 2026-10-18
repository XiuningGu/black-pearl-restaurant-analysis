import sys
import unittest
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.analysis import (  # noqa: E402
    build_public_dataset,
    clean_data,
    cuisine_region_test,
    ols_fit,
    regression_diagnostics,
)


class AnalysisChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = clean_data(ROOT / "data/raw/black_pearl_2024.xlsx")
        cls.predictors = ["taste_score", "environment_score", "service_score"]

    def test_source_and_public_dataset_shape(self):
        public = build_public_dataset(self.data)
        self.assertEqual(self.data.shape[0], 233)
        self.assertEqual(public.shape, (233, 25))
        self.assertEqual(public["restaurant_id"].iloc[0], "BP-0001")
        self.assertEqual(public["restaurant_id"].iloc[-1], "BP-0233")
        self.assertEqual(public["cuisine_source"].isna().sum(), 1)
        self.assertEqual(public["ingredient_score"].notna().sum(), 21)
        self.assertTrue(np.issubdtype(public["favourites_count"].dtype, np.integer))
        self.assertNotIn("notes", public.columns)
        self.assertNotIn("favourites_thousands", public.columns)

    def test_core_ols_values(self):
        table, fit = ols_fit(self.data, "total_score", self.predictors)
        expected = np.array([0.1816506481, 0.6173553274, 0.1963265234, 0.1435760469])
        np.testing.assert_allclose(table["coefficient"].to_numpy(), expected, rtol=0, atol=1e-9)
        self.assertAlmostEqual(fit["r_squared"], 0.8924588896, places=9)
        service_p = table.loc[table["term"] == "service_score", "hc3_p_value"].iloc[0]
        self.assertAlmostEqual(service_p, 0.0512102150, places=9)

    def test_diagnostics_use_all_predictors(self):
        _, fit = ols_fit(self.data, "total_score", self.predictors)
        diagnostics = regression_diagnostics(self.data, fit, self.predictors).set_index("metric")
        self.assertEqual(diagnostics.loc["koenker_breusch_pagan_df", "value"], 3)
        self.assertAlmostEqual(
            diagnostics.loc["koenker_breusch_pagan_p_value", "value"],
            4.60453e-6,
            delta=2e-10,
        )

    def test_permutation_result_is_seeded_and_reports_resolution(self):
        first = cuisine_region_test(self.data, permutations=100, seed=20261018)
        second = cuisine_region_test(self.data, permutations=100, seed=20261018)
        self.assertTrue(first.equals(second))
        metrics = first.set_index("metric")["value"]
        self.assertIn("permutation_exceedances", metrics.index)
        self.assertEqual(metrics["permutation_p_value"], 1 / 101)


if __name__ == "__main__":
    unittest.main()
