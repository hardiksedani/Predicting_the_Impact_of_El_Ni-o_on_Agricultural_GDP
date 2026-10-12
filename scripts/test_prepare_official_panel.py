"""Checks for the official-data preparation path; never fits a model."""

import unittest

import numpy as np
import pandas as pd

from prepare_official_panel import (
    ECONOMIC, OUTPUT, REPORT, aggregate_financial_year, load_oni,
    load_points, load_targets, nearest,
)
from sync_official_panel import validated_panel
from sync_official_panel import expected_documents, verify_collection


class OfficialPanelTests(unittest.TestCase):
    def test_representative_points_cover_28_states(self):
        points = load_points()
        self.assertEqual(len(points), 28)
        self.assertTrue(points["point_label"].notna().all())

    def test_rbi_targets_are_separate_from_older_price_bases(self):
        if not ECONOMIC.is_file():
            self.skipTest("Run the economic extraction first")
        targets = load_targets(2011, 2024)
        self.assertEqual(len(targets), 28 * 14)
        self.assertEqual(int(targets["agricultural_gdp_cr"].isna().sum()), 7)
        andhra = targets.loc[(targets["state"] == "Andhra Pradesh") & (targets["year"] == 2011)]
        self.assertEqual(float(andhra.iloc[0]["agricultural_gdp_cr"]), 52040.52)

    def test_oni_has_one_financial_year_value_from_complete_seasons(self):
        oni = load_oni(2011, 2024)
        self.assertEqual(oni["year"].tolist(), list(range(2011, 2025)))
        self.assertTrue(np.isfinite(oni["oni_index"]).all())

    def test_april_to_march_aggregation(self):
        dates = pd.date_range("2011-01-01", "2012-12-31", freq="D")
        daily = pd.DataFrame({
            "state": "Test State", "date": dates,
            "rainfall_mm_daily": 1.0, "avg_temperature_c_daily": 25.0,
            "rainfall_grid_lat": 20.0, "rainfall_grid_lon": 80.0,
            "temperature_grid_lat": 20.5, "temperature_grid_lon": 80.5,
        })
        annual = aggregate_financial_year(daily, 2011, 2011)
        self.assertEqual(len(annual), 1)
        self.assertEqual(int(annual.iloc[0]["expected_days"]), 366)
        self.assertEqual(float(annual.iloc[0]["rainfall_mm"]), 366.0)
        self.assertEqual(float(annual.iloc[0]["avg_temperature_c"]), 25.0)

    def test_nearest_grid_rejects_outside_point(self):
        self.assertEqual(nearest(np.array([10.0, 11.0, 12.0]), 10.6), 1)
        with self.assertRaises(ValueError):
            nearest(np.array([10.0, 11.0, 12.0]), 15.0)

    def test_prepared_panel_matches_provenance_report(self):
        if not OUTPUT.is_file() or not REPORT.is_file():
            self.skipTest("Run official panel preparation first")
        panel, digest = validated_panel()
        self.assertEqual(len(panel), 385)
        self.assertEqual(panel["state"].nunique(), 28)
        self.assertEqual(len(digest), 64)

    def test_sync_guard_rejects_changed_website_row(self):
        if not OUTPUT.is_file() or not REPORT.is_file():
            self.skipTest("Run official panel preparation first")
        panel, digest = validated_panel()
        one_row = panel.head(1)
        doc_id, fields = next(iter(expected_documents(one_row, digest).items()))

        class Snapshot:
            id = doc_id

            def to_dict(self):
                changed = fields.copy()
                changed["agricultural_gdp_cr"] = -1.0
                return changed

        with self.assertRaisesRegex(ValueError, "differs from the validated panel"):
            verify_collection(one_row, digest, [Snapshot()])


if __name__ == "__main__":
    unittest.main()
