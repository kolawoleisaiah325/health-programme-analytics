"""Verify the temporal split and the meaning of missing observations."""

import csv
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from src import forecast_service_volume
from src.forecast_service_volume import (
    BACKTEST_HORIZON, METHODS, PROCESSED, load_monthly_series, rolling_backtest,
    run_forecast,
)


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
            self.assertFalse(
                set(diagnostics["scored_holdout_months"])
                & set(diagnostics["excluded_incomplete_holdout_months"])
            )
            self.assertEqual(diagnostics["imputed_facility_months_for_refit"], 3)
            self.assertEqual(len(rows), 12)
            self.assertEqual(rows[0]["period"], "2026-01")
            self.assertEqual(rows[-1]["period"], "2026-12")
            self.assertTrue(all(int(r["predicted_doses"]) >= 0 for r in rows))

    def test_backtest_never_trains_on_the_months_it_scores(self):
        _, monthly = load_monthly_series(PROCESSED / "facility_month_status.csv")
        calls = []
        real_predict = forecast_service_volume.predict

        def recording_predict(method, history, horizon):
            calls.append((len(history), horizon))
            return real_predict(method, history, horizon)

        with mock.patch.object(forecast_service_volume, "predict", recording_predict):
            origins, _, _, _ = rolling_backtest(monthly)
        # Each origin fits on exactly the months before it, never later ones.
        expected = [(origin, BACKTEST_HORIZON) for origin in origins for _ in METHODS]
        self.assertEqual(calls, expected)


if __name__ == "__main__":
    unittest.main()
