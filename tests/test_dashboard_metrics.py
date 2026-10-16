"""Check dashboard calculations directly, without running Streamlit."""

import math
import unittest

import pandas as pd

from dashboard.metrics import (
    export_csv, facility_performance, followup_items, headline_metrics, monthly_totals,
)


def facility_months():
    """One facility-month of each kind, all with a target of 100 doses."""
    return pd.DataFrame([
        # period, facility, status, submissions, doses
        ("2025-01", "F001", "accepted", 1, 95.0),
        ("2025-01", "F002", "accepted", 1, 0.0),       # A reported zero.
        ("2025-02", "F001", "missing", 0, math.nan),
        ("2025-02", "F002", "invalid", 2, math.nan),
        ("2025-03", "F001", "accepted", 1, 79.0),      # Just below 80%.
        ("2025-03", "F002", "accepted", 1, 80.0),      # Exactly 80%.
    ], columns=["period", "facility_id", "reporting_status", "submission_count",
                "accepted_doses"]).assign(
        target_doses=100, area="Area A",
        facility_name=lambda frame: "Facility " + frame["facility_id"],
    )


class DashboardMetricsTest(unittest.TestCase):
    def test_headline_counts_and_denominators(self):
        counts = headline_metrics(facility_months(), threshold=0.8)
        self.assertEqual(counts["expected"], 6)
        self.assertEqual(counts["submitted"], 5)  # Invalid still counts as submitted.
        self.assertEqual(counts["accepted"], 4)
        self.assertEqual(counts["delivered"], 254)
        self.assertEqual(counts["comparable_target"], 400)  # Accepted months only.
        self.assertEqual((counts["missing"], counts["invalid"]), (1, 1))
        self.assertEqual(counts["below_threshold"], 2)  # The zero and the 79.

    def test_followup_puts_data_gaps_first_and_keeps_zero_distinct(self):
        items = followup_items(facility_months(), threshold=0.8)
        self.assertEqual(
            list(zip(items["period"], items["facility_id"], items["action"])),
            [
                ("2025-02", "F001", "Request report"),
                ("2025-02", "F002", "Resolve rejected submission"),
                ("2025-03", "F001", "Discuss low service volume"),
                ("2025-01", "F002", "Discuss low service volume"),
            ],
        )
        self.assertTrue(math.isnan(items.iloc[0]["accepted_doses"]))
        self.assertEqual(items.iloc[3]["accepted_doses"], 0)

    def test_month_with_no_accepted_report_has_unknown_total(self):
        totals = monthly_totals(facility_months()).set_index("period")
        self.assertTrue(math.isnan(totals.loc["2025-02", "delivered"]))
        self.assertTrue(math.isnan(totals.loc["2025-02", "target"]))
        self.assertEqual(totals.loc["2025-01", "delivered"], 95)

    def test_facility_attainment_uses_comparable_targets(self):
        facilities = facility_performance(facility_months()).set_index("facility_name")
        # F001: 95 + 79 over two accepted months; the missing month is excluded.
        self.assertAlmostEqual(facilities.loc["Facility F001", "attainment"], 87.0)
        self.assertEqual(facilities.loc["Facility F001", "reporting"], "2 / 3")

    def test_export_keeps_synthetic_label(self):
        lines = export_csv(facility_months().head(1)).decode("utf-8").splitlines()
        self.assertTrue(lines[0].endswith("data_label"))
        self.assertTrue(lines[1].endswith("synthetic demonstration data"))


if __name__ == "__main__":
    unittest.main()
