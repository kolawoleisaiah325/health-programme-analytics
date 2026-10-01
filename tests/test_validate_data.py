"""Check the decisions that would change a programme dashboard."""

import csv
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from src.validate_data import DEFAULT_INPUT, run_pipeline


class ValidationPipelineTest(unittest.TestCase):
    def test_expected_quality_cases_and_selected_report(self):
        with tempfile.TemporaryDirectory() as temporary_dir:
            output_dir = Path(temporary_dir)
            summary = run_pipeline(DEFAULT_INPUT, output_dir)
            with (output_dir / "facility_month_status.csv").open(
                newline="", encoding="utf-8"
            ) as source:
                months = {
                    (row["facility_id"], row["period"]): row
                    for row in csv.DictReader(source)
                }
            with (output_dir / "report_review.csv").open(
                newline="", encoding="utf-8"
            ) as source:
                reviews = list(csv.DictReader(source))

            self.assertEqual(summary["expected_facility_months"], 216)
            self.assertEqual(summary["submitted_facility_months"], 214)
            self.assertEqual(
                summary["reporting_status_counts"],
                {"accepted": 213, "invalid": 1, "missing": 2},
            )
            self.assertEqual(
                summary["submission_review_counts"],
                {"accepted": 213, "rejected": 2, "superseded": 1},
            )
            self.assertEqual(months[("F003", "2025-02")]["reporting_status"], "missing")
            self.assertEqual(months[("F003", "2025-02")]["accepted_doses"], "")
            self.assertEqual(months[("F001", "2025-07")]["accepted_doses"], "0")
            self.assertEqual(months[("F005", "2025-06")]["reporting_status"], "invalid")
            self.assertEqual(months[("F005", "2025-06")]["accepted_doses"], "")
            self.assertEqual(months[("F002", "2025-05")]["accepted_doses"], "125")
            self.assertTrue(
                any(row["issue_code"] == "unknown_facility" for row in reviews)
            )
            self.assertEqual(len(months), 216)

    def test_repeated_target_stops_the_pipeline(self):
        with tempfile.TemporaryDirectory() as temporary_dir:
            temporary_path = Path(temporary_dir)
            input_dir = temporary_path / "input"
            input_dir.mkdir()
            for filename in ("facilities.csv", "monthly_reports.csv"):
                shutil.copyfile(DEFAULT_INPUT / filename, input_dir / filename)
            with (DEFAULT_INPUT / "programme_targets.json").open(
                encoding="utf-8"
            ) as source:
                targets = json.load(source)
            targets.append(dict(targets[0]))
            with (input_dir / "programme_targets.json").open(
                "w", encoding="utf-8"
            ) as output:
                json.dump(targets, output)

            with self.assertRaisesRegex(ValueError, "Repeated target"):
                run_pipeline(input_dir, temporary_path / "output")
            self.assertFalse((temporary_path / "output").exists())


if __name__ == "__main__":
    unittest.main()
