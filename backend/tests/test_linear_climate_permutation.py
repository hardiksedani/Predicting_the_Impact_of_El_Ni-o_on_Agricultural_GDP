"""Checks that chart values are measured from held-out predictions, not placeholders."""

import unittest

import pandas as pd

from app.services.ml import _linear_climate_permutation_on_test


class _KnownModel:
    def predict(self, features):
        return (
            0.2 * features["rainfall_mm"]
            + 3.0 * features["avg_temperature_c"]
            + 5.0 * features["oni_index"]
            + 100.0 * features["state__assam"]
        )


class LinearClimatePermutationTest(unittest.TestCase):
    def setUp(self):
        rows = []
        for year, oni in zip(range(2021, 2025), [-0.8, 0.1, 1.2, 0.5]):
            for state, offset in [("Assam", 0), ("Bihar", 1)]:
                rain = 700 + (year - 2021) * 80 + offset * 140
                temp = 24 + (year - 2021) * 1.5 + offset * 2
                target = 0.2 * rain + 3 * temp + 5 * oni + (100 if state == "Assam" else 0)
                rows.append({
                    "state": state, "year": year, "rainfall_mm": rain,
                    "avg_temperature_c": temp, "oni_index": oni,
                    "agricultural_gdp_cr": target,
                })
        self.panel = pd.DataFrame(rows)

    def test_uses_real_predictions_without_mutating_panel(self):
        original = self.panel.copy(deep=True)
        first = _linear_climate_permutation_on_test(_KnownModel(), self.panel, ["Assam", "Bihar"])
        second = _linear_climate_permutation_on_test(_KnownModel(), self.panel, ["Assam", "Bihar"])

        self.assertEqual(first, second)
        self.assertEqual(first["baseline_rmse_cr"], 0.0)
        self.assertEqual(set(first["rmse_change_cr"]), {
            "rainfall_mm", "avg_temperature_c", "oni_index",
        })
        self.assertTrue(all(value > 0 for value in first["rmse_change_cr"].values()))
        pd.testing.assert_frame_equal(self.panel, original)

    def test_oni_must_be_shared_by_year(self):
        self.panel.loc[0, "oni_index"] = 0.4
        with self.assertRaisesRegex(ValueError, "one value per financial year"):
            _linear_climate_permutation_on_test(_KnownModel(), self.panel, ["Assam", "Bihar"])


if __name__ == "__main__":
    unittest.main()
