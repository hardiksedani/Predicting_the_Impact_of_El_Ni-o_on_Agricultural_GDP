"""Regression tests that keep legacy models and data out of official predictions."""

import asyncio
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pandas as pd

from app.constants import (
    MODEL_NAMES,
    OFFICIAL_CLIMATE_METHOD,
    OFFICIAL_TARGET_SOURCE,
)
from app.services import ml
from app.services import scenario_service
from app.services.ingestion.states import INDIAN_STATES
from app.models.schemas import ScenarioRequest
from app.routers import dashboard


PANEL_HASH = "a" * 64


def _metrics() -> dict:
    states = sorted(INDIAN_STATES)
    return {
        "data_source": OFFICIAL_TARGET_SOURCE,
        "climate_method": OFFICIAL_CLIMATE_METHOD,
        "panel_sha256": PANEL_HASH,
        "panel_rows": len(states),
        "run_id": "run_20260930_120000_1234abcd",
        "train_years": [2020],
        "test_years": [2021],
        "training_states": states,
        "feature_columns": ml.model_feature_columns(states),
        "models": {name: {} for name in MODEL_NAMES},
        "artifact_sha256": {name: "b" * 64 for name in MODEL_NAMES},
    }


def _database(metrics: dict, *, panel_hash: str = PANEL_HASH):
    panel_docs = [
        SimpleNamespace(to_dict=lambda state=state: {
            "state": state,
            "year": 2020,
            "source": OFFICIAL_TARGET_SOURCE,
            "climate_method": OFFICIAL_CLIMATE_METHOD,
            "panel_sha256": panel_hash,
        })
        for state in INDIAN_STATES
    ]
    metric_doc = SimpleNamespace(exists=True, to_dict=lambda: metrics)

    def collection(name):
        if name == "model_metrics":
            return SimpleNamespace(document=lambda _id: SimpleNamespace(get=lambda: metric_doc))
        return SimpleNamespace(stream=lambda: panel_docs)

    return SimpleNamespace(collection=collection)


class OfficialModelGuardTest(unittest.TestCase):
    def test_only_matching_current_panel_exposes_metrics(self):
        metrics = _metrics()
        with patch.object(ml, "get_db", return_value=_database(metrics)):
            self.assertEqual(ml.get_model_metrics(), metrics)
        with patch.object(ml, "get_db", return_value=_database(metrics, panel_hash="c" * 64)):
            self.assertIsNone(ml.get_model_metrics())

    def test_missing_state_features_or_artifact_checksums_hide_run(self):
        metrics = _metrics()
        metrics["feature_columns"] = ["rainfall_mm", "avg_temperature_c", "oni_index"]
        with patch.object(ml, "get_db", return_value=_database(metrics)):
            self.assertIsNone(ml.get_model_metrics())
        metrics = _metrics()
        metrics.pop("artifact_sha256")
        with patch.object(ml, "get_db", return_value=_database(metrics)):
            self.assertIsNone(ml.get_model_metrics())

    def test_legacy_latest_file_is_never_loaded(self):
        with tempfile.TemporaryDirectory() as temporary_dir:
            Path(temporary_dir, "linear_regression_latest.joblib").write_bytes(b"legacy-model")
            blob = SimpleNamespace(exists=lambda: False)
            storage = SimpleNamespace(blob=lambda path: blob)
            with (
                patch.object(ml, "LOCAL_MODEL_CACHE_DIR", temporary_dir),
                patch.object(ml, "get_storage", return_value=storage),
            ):
                with self.assertRaisesRegex(FileNotFoundError, "Verified official model"):
                    ml.load_model("linear_regression", _metrics())

    def test_inference_uses_same_state_features_and_requires_artifact(self):
        metrics = _metrics()
        model = SimpleNamespace(predict=lambda features: [200.0])
        with (
            patch.object(ml, "get_model_metrics", return_value=metrics),
            patch.object(ml, "get_state_historical_avg_gdp", return_value=100.0),
            patch.object(ml, "load_model", return_value=model) as loader,
        ):
            result = ml.predict_gdp("Assam", 900.0, 27.0, 1.2, "linear_regression")
            self.assertEqual(result["predictions"][0]["predicted_gdp_cr"], 200.0)
            loader.assert_called_once_with("linear_regression", metrics)

        with (
            patch.object(ml, "get_model_metrics", return_value=metrics),
            patch.object(ml, "get_state_historical_avg_gdp", return_value=100.0),
            patch.object(ml, "load_model", side_effect=FileNotFoundError("missing")),
        ):
            with self.assertRaisesRegex(FileNotFoundError, "missing"):
                ml.predict_gdp("Assam", 900.0, 27.0, 1.2, "linear_regression")

    def test_prediction_baseline_excludes_held_out_years(self):
        rows = [
            SimpleNamespace(to_dict=lambda: {"year": 2020, "agricultural_gdp_cr": 100.0,
                                             "panel_sha256": PANEL_HASH}),
            SimpleNamespace(to_dict=lambda: {"year": 2021, "agricultural_gdp_cr": 1000.0,
                                             "panel_sha256": PANEL_HASH}),
        ]
        query = SimpleNamespace(stream=lambda: rows)
        database = SimpleNamespace(collection=lambda _: SimpleNamespace(
            where=lambda *_args: query))
        with patch.object(ml, "get_db", return_value=database):
            self.assertEqual(ml.get_state_historical_avg_gdp("Assam", _metrics()), 100.0)

    def test_automatic_or_legacy_training_inputs_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "Supply data/processed/official_panel.csv"):
            ml.train_all_models()
        legacy = pd.DataFrame([{"state": "Assam", "target_source": "sample"}])
        with self.assertRaisesRegex(ValueError, "Only the RBI/NSO"):
            ml.train_all_models(legacy)

    def test_scenario_never_falls_back_to_partial_or_legacy_models(self):
        metrics = _metrics()
        request = ScenarioRequest(state="Assam", rainfall=900.0, temperature=27.0,
                                  oni_index=1.2, model="xgboost")
        with (
            patch.object(scenario_service, "get_model_metrics", return_value=metrics),
            patch.object(scenario_service, "get_state_historical_avg_gdp", return_value=100.0),
            patch.object(scenario_service, "load_model", side_effect=FileNotFoundError("missing official run")),
        ):
            with self.assertRaisesRegex(FileNotFoundError, "missing official run"):
                scenario_service.run_scenario_simulation(request)

    def test_dashboard_ignores_legacy_prediction_log(self):
        metrics = _metrics()
        log_rows = [
            SimpleNamespace(to_dict=lambda: {"state": "Assam", "model_used": "xgboost",
                                             "created_at": "2026-09-30T13:00:00Z"}),
            SimpleNamespace(to_dict=lambda: {"state": "Bihar", "model_used": "xgboost",
                                             "created_at": "2026-09-30T12:00:00Z",
                                             "panel_sha256": PANEL_HASH,
                                             "model_run_id": metrics["run_id"]}),
        ]
        query = SimpleNamespace(stream=lambda: log_rows)
        database = SimpleNamespace(collection=lambda _: SimpleNamespace(
            order_by=lambda *_args, **_kwargs: SimpleNamespace(limit=lambda _n: query)))
        with (
            patch.object(dashboard, "get_db", return_value=database),
            patch.object(dashboard, "get_model_metrics", return_value=metrics),
            patch.object(dashboard, "fetch_climate_dataframe", return_value=pd.DataFrame()),
        ):
            result = asyncio.run(dashboard.dashboard_summary())
        self.assertEqual(result.latest_prediction["state"], "Bihar")


if __name__ == "__main__":
    unittest.main()
