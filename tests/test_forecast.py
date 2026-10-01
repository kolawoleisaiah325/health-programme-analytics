"""Verify the temporal split and the meaning of missing observations."""

import csv
import tempfile
import unittest
from pathlib import Path

from src.forecast_service_volume import run_forecast


class ForecastTest(unittest.TestCase):
    def test_forecast_uses_only_complete_holdout_months(self):
        with tempfile.TemporaryDirectory() as temporary_dir:
            output_dir = Path(temporary_dir)
            diagnostics = run_forecast(output_dir=output_dir)
            with (output_dir / "service_volume_forecast.csv").open(
                newline="", encoding="utf-8"
            ) as source:
                rows = list(csv.DictReader(source))
            self.assertEqual(len(diagnostics["scored_holdout_months"]), 9)
            self.assertEqual(
                diagnostics["excluded_incomplete_holdout_months"],
                ["2025-02", "2025-04", "2025-06"],
            )
            self.assertEqual(diagnostics["imputed_facility_months_for_refit"], 3)
            self.assertEqual(len(rows), 12)
            self.assertEqual(rows[0]["period"], "2026-01")
            self.assertEqual(rows[-1]["period"], "2026-12")
            self.assertTrue(all(int(r["predicted_doses"]) >= 0 for r in rows))


if __name__ == "__main__":
    unittest.main()
