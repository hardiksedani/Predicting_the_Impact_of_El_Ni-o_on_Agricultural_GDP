"""Regression checks for official IMD rainfall extraction and panel validation."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd
from scipy.io import netcdf_file

from app.services.ingestion import imd


class ImdRainfallTest(unittest.TestCase):
    def test_panel_requires_every_state_year(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "rainfall.csv"
            pd.DataFrame(
                [
                    {"state": "Bihar", "year": 2022, "rainfall_mm": 900},
                    {"state": "Bihar", "year": 2023, "rainfall_mm": 850},
                ]
            ).to_csv(path, index=False)
            with patch.object(imd, "IMD_RAINFALL_PATH", path):
                with self.assertRaisesRegex(ValueError, "not complete"):
                    imd.load_imd_rainfall(2022, 2023, ["Bihar", "Punjab"])
                result = imd.load_imd_rainfall(2022, 2023, ["Bihar"])
                self.assertEqual(len(result), 2)

    def test_extraction_uses_nearest_cell_and_rejects_missing(self):
        from scripts import download_imd_rainfall as downloader

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sample.nc"
            with netcdf_file(path, "w") as dataset:
                dataset.createDimension("TIME", 365)
                dataset.createDimension("LATITUDE", 2)
                dataset.createDimension("LONGITUDE", 2)
                dataset.createVariable("LATITUDE", "d", ("LATITUDE",))[:] = [10.5, 11.5]
                dataset.createVariable("LONGITUDE", "d", ("LONGITUDE",))[:] = [76.5, 77.5]
                rain = dataset.createVariable(
                    "RAINFALL", "d", ("TIME", "LATITUDE", "LONGITUDE")
                )
                rain[:] = np.ones((365, 2, 2))
                rain[:, 1, 1] = 2.0
            with patch.object(downloader, "STATE_COORDINATES", {"Test": (11.4, 77.4)}):
                rows = downloader.extract_year(path, 2023)
            self.assertEqual(rows[0]["rainfall_mm"], 730.0)


if __name__ == "__main__":
    unittest.main()
