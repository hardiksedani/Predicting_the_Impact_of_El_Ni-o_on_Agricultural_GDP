"""Keep catalogue visibility separate from model prediction coverage."""

import asyncio
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from app.routers.states import list_states
from app.constants import OFFICIAL_CLIMATE_METHOD, OFFICIAL_TARGET_SOURCE
from app.services.ingestion.states import INDIAN_STATES
from app.services.ml import predict_gdp


class StateCatalogTest(unittest.TestCase):
    def test_all_states_listed_but_only_trained_state_available(self):
        documents = [SimpleNamespace(to_dict=lambda: {
            "state": "Andhra Pradesh", "year": 2020,
            "agricultural_gdp_cr": 123.0,
            "source": OFFICIAL_TARGET_SOURCE,
            "climate_method": OFFICIAL_CLIMATE_METHOD,
            "panel_sha256": "a" * 64,
        })]
        collection = SimpleNamespace(stream=lambda: documents)
        database = SimpleNamespace(collection=lambda _: collection)
        with (
            patch("app.routers.states.get_db", return_value=database),
            patch("app.routers.states.get_model_metrics", return_value={
                "training_states": ["Andhra Pradesh"],
                "panel_sha256": "a" * 64,
            }),
        ):
            response = asyncio.run(list_states())

        self.assertEqual(len(response.states), len(INDIAN_STATES))
        by_name = {state.state: state for state in response.states}
        self.assertTrue(by_name["Andhra Pradesh"].prediction_available)
        self.assertFalse(by_name["Assam"].prediction_available)
        self.assertFalse(by_name["Telangana"].prediction_available)

    def test_prediction_rejects_state_outside_training_panel(self):
        with patch("app.services.ml.get_model_metrics", return_value={
            "training_states": ["Andhra Pradesh"],
        }):
            with self.assertRaisesRegex(ValueError, "not in the trained panel"):
                predict_gdp("Telangana", 800, 28, 1.0)

    def test_legacy_run_without_state_metadata_is_not_assumed_covered(self):
        with patch("app.services.ml.get_model_metrics", return_value={"panel_rows": 150}):
            with self.assertRaisesRegex(ValueError, "does not record training-state coverage"):
                predict_gdp("Andhra Pradesh", 800, 28, 1.0)


if __name__ == "__main__":
    unittest.main()
