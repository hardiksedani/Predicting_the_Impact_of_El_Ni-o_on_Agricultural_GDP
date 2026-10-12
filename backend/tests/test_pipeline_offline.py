"""The former automatic pipeline must not import or train on legacy sample data."""

import unittest
from unittest.mock import patch

from app.services import pipeline


class LegacyPipelineDisabledTest(unittest.TestCase):
    def test_legacy_service_entrypoint_is_disabled_before_any_read_or_write(self):
        with patch.object(pipeline, "get_db") as database:
            with self.assertRaisesRegex(ValueError, "disabled"):
                pipeline.run_full_pipeline()
            database.assert_not_called()


if __name__ == "__main__":
    unittest.main()
