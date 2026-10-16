"""Check the decisions that would change a programme dashboard."""

import csv
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from src.validate_data import (
    DEFAULT_INPUT, nonnegative_integer, parse_period, run_pipeline,
)


REPORT_COLUMNS = ("report_id", "facility_id", "period", "doses_delivered", "reported_at")


def read_rows(path):
    with path.open(newline="", encoding="utf-8") as source:
        return list(csv.DictReader(source))


class ValidationPipelineTest(unittest.TestCase):
    def test_expected_quality_cases_and_selected_report(self):
        with tempfile.TemporaryDirectory() as temporary_dir:
            output_dir = Path(temporary_dir)
            summary = run_pipeline(DEFAULT_INPUT, output_dir)
            months = {
                (row["facility_id"], row["period"]): row
                for row in read_rows(output_dir / "facility_month_status.csv")
            }
            reviews = read_rows(output_dir / "report_review.csv")

            self.assertEqual(summary["expected_facility_months"], 216)
            self.assertEqual(summary["submitted_facility_months"], 214)
            self.assertEqual(
                summary["reporting_status_counts"],
                {"accepted": 213, "invalid": 1, "missing": 2},
            )
            self.assertEqual(
                summary["submission_review_counts"],
                {"accepted": 213, "rejected": 7, "superseded": 1},
            )
            # The demo data plants one case for every validation rule.
            self.assertEqual(
                set(summary["issue_counts"]),
                {
                    "bad_period", "bad_reported_at", "duplicate_or_blank_report_id",
                    "invalid_doses", "later_valid_submission",
                    "period_without_target", "report_before_period_end",
                    "unknown_facility",
                },
            )
            self.assertEqual(months[("F003", "2025-02")]["reporting_status"], "missing")
            self.assertEqual(months[("F003", "2025-02")]["accepted_doses"], "")
            self.assertEqual(months[("F001", "2025-07")]["accepted_doses"], "0")
            self.assertEqual(months[("F005", "2025-06")]["reporting_status"], "invalid")
            self.assertEqual(months[("F005", "2025-06")]["accepted_doses"], "")
            self.assertEqual(months[("F002", "2025-05")]["accepted_doses"], "125")
            self.assertEqual(len(reviews), 221)
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


class ValidationRuleTest(unittest.TestCase):
    """Each rule on a tiny hand-made input, independent of the demo data."""

    def review(self, reports):
        """Run one facility with targets for 2025-01 and 2025-02."""
        with tempfile.TemporaryDirectory() as temporary_dir:
            input_dir = Path(temporary_dir) / "input"
            output_dir = Path(temporary_dir) / "output"
            input_dir.mkdir()
            (input_dir / "facilities.csv").write_text(
                "facility_id,facility_name,area,facility_type\n"
                "F001,Test Facility,Test Area,Clinic\n",
                encoding="utf-8",
            )
            (input_dir / "programme_targets.json").write_text(json.dumps([
                {"facility_id": "F001", "period": "2025-01", "target_doses": 100},
                {"facility_id": "F001", "period": "2025-02", "target_doses": 100},
            ]), encoding="utf-8")
            with (input_dir / "monthly_reports.csv").open(
                "w", newline="", encoding="utf-8"
            ) as output:
                writer = csv.DictWriter(output, fieldnames=REPORT_COLUMNS)
                writer.writeheader()
                writer.writerows(reports)
            run_pipeline(input_dir, output_dir)
            months = {
                row["period"]: row
                for row in read_rows(output_dir / "facility_month_status.csv")
            }
            return read_rows(output_dir / "report_review.csv"), months

    @staticmethod
    def report(report_id="R1", period="2025-01", doses="10",
               reported_at="2025-02-05", facility_id="F001"):
        return {"report_id": report_id, "facility_id": facility_id, "period": period,
                "doses_delivered": doses, "reported_at": reported_at}

    def assert_rejected_with(self, report, issue_code):
        reviews, _ = self.review([report])
        self.assertEqual(reviews[0]["review_status"], "rejected")
        self.assertIn(issue_code, reviews[0]["issue_code"].split(";"))

    def test_each_rule_rejects_its_case(self):
        cases = {
            "unknown_facility": self.report(facility_id="F999"),
            "bad_period": self.report(period="2025-13"),
            "period_without_target": self.report(period="2025-03", reported_at="2025-04-05"),
            "invalid_doses": self.report(doses="-4"),
            "bad_reported_at": self.report(reported_at="not-a-date"),
            "report_before_period_end": self.report(reported_at="2025-01-20"),
        }
        for issue_code, report in cases.items():
            with self.subTest(issue_code):
                self.assert_rejected_with(report, issue_code)

    def test_repeated_report_id_rejects_the_later_row(self):
        reviews, _ = self.review([
            self.report(report_id="R1"),
            self.report(report_id="R1", period="2025-02", reported_at="2025-03-05"),
        ])
        self.assertEqual(reviews[0]["review_status"], "accepted")
        self.assertEqual(reviews[1]["issue_code"], "duplicate_or_blank_report_id")

    def test_same_day_resubmission_uses_report_id_to_break_tie(self):
        reviews, months = self.review([
            self.report(report_id="R2", doses="20"),
            self.report(report_id="R1", doses="10"),
        ])
        self.assertEqual(months["2025-01"]["selected_report_id"], "R2")
        self.assertEqual(
            [row["review_status"] for row in reviews], ["accepted", "superseded"]
        )

    def test_later_invalid_resubmission_keeps_earlier_valid_report(self):
        reviews, months = self.review([
            self.report(report_id="R1", doses="10"),
            self.report(report_id="R2", doses="-1", reported_at="2025-02-20"),
        ])
        self.assertEqual(months["2025-01"]["reporting_status"], "accepted")
        self.assertEqual(months["2025-01"]["accepted_doses"], "10")
        self.assertEqual(months["2025-01"]["submission_count"], "2")
        self.assertEqual(reviews[1]["review_status"], "rejected")

    def test_month_with_only_rejected_reports_is_invalid_not_missing(self):
        _, months = self.review([self.report(doses="abc")])
        self.assertEqual(months["2025-01"]["reporting_status"], "invalid")
        self.assertEqual(months["2025-02"]["reporting_status"], "missing")

    def test_value_parsers(self):
        self.assertEqual(nonnegative_integer("0"), 0)
        for value in ("", "-1", "1.5", " 3", True):
            with self.subTest(value=value), self.assertRaises(ValueError):
                nonnegative_integer(value)
        self.assertEqual(parse_period("2025-12").month, 12)
        for value in ("2025-1", "2025-00", "2025/01", None):
            with self.subTest(value=value), self.assertRaises(ValueError):
                parse_period(value)


if __name__ == "__main__":
    unittest.main()
