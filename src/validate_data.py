r"""Validate synthetic programme inputs and keep an auditable report history.

Run from the repository root with:
    .\.venv\Scripts\python.exe .\src\validate_data.py
"""

import argparse
import csv
import json
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = PROJECT_ROOT / "data" / "synthetic"
DEFAULT_OUTPUT = PROJECT_ROOT / "data" / "processed"


def read_csv(path, required_columns):
    with path.open(newline="", encoding="utf-8") as source:
        reader = csv.DictReader(source)
        if not reader.fieldnames or not set(required_columns) <= set(reader.fieldnames):
            raise ValueError(f"{path.name} needs columns: {', '.join(required_columns)}")
        return list(reader)


def write_csv(path, rows, columns):
    with path.open("w", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(output, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def parse_period(value):
    """Accept only complete YYYY-MM labels, returning the first day of the month."""
    if not isinstance(value, str) or len(value) != 7 or value[4] != "-":
        raise ValueError("bad_period")
    try:
        year, month = int(value[:4]), int(value[5:])
        return date(year, month, 1)
    except ValueError as error:
        raise ValueError("bad_period") from error


def nonnegative_integer(value):
    """Reject blanks, decimals, negatives, and booleans as dose counts."""
    if isinstance(value, bool) or not str(value).isdigit():
        raise ValueError("invalid_doses")
    return int(value)


def first_day_after(period_start):
    return date(
        period_start.year + period_start.month // 12,
        period_start.month % 12 + 1,
        1,
    )


def load_dimensions(input_dir):
    """Fail the run if the facility register or target table is ambiguous."""
    facility_rows = read_csv(
        input_dir / "facilities.csv",
        ("facility_id", "facility_name", "area", "facility_type"),
    )
    facilities = {}
    for row in facility_rows:
        facility_id = row["facility_id"].strip()
        if not facility_id or facility_id in facilities:
            raise ValueError(f"Blank or repeated facility ID: {facility_id!r}")
        facilities[facility_id] = row

    with (input_dir / "programme_targets.json").open(encoding="utf-8") as source:
        target_rows = json.load(source)
    if not isinstance(target_rows, list):
        raise ValueError("programme_targets.json must contain a list")

    targets = {}
    for row in target_rows:
        facility_id = row["facility_id"]
        period = row["period"]
        parse_period(period)
        if facility_id not in facilities:
            raise ValueError(f"Target references unknown facility: {facility_id}")
        key = (facility_id, period)
        if key in targets:
            raise ValueError(f"Repeated target for facility-month: {key}")
        targets[key] = nonnegative_integer(row["target_doses"])
    return facilities, targets


def review_reports(input_dir, facilities, targets):
    """Reject invalid submissions and select the latest valid resubmission."""
    source_rows = read_csv(
        input_dir / "monthly_reports.csv",
        ("report_id", "facility_id", "period", "doses_delivered", "reported_at"),
    )
    review_rows = []
    eligible = defaultdict(list)
    counts_by_month = Counter()
    seen_ids = set()

    for source_row in source_rows:
        row = dict(source_row)
        row["review_status"] = "rejected"
        issues = []
        report_id = row["report_id"]
        key = (row["facility_id"], row["period"])

        if not report_id or report_id in seen_ids:
            issues.append("duplicate_or_blank_report_id")
        seen_ids.add(report_id)
        if row["facility_id"] not in facilities:
            issues.append("unknown_facility")
        try:
            period_start = parse_period(row["period"])
        except ValueError:
            issues.append("bad_period")
            period_start = None
        if (
            period_start is not None
            and row["facility_id"] in facilities
            and key not in targets
        ):
            issues.append("period_without_target")
        try:
            nonnegative_integer(row["doses_delivered"])
        except ValueError:
            issues.append("invalid_doses")
        try:
            reported_at = date.fromisoformat(row["reported_at"])
            if period_start and reported_at < first_day_after(period_start):
                issues.append("report_before_period_end")
        except (TypeError, ValueError):
            issues.append("bad_reported_at")
            reported_at = None

        if key in targets:
            counts_by_month[key] += 1
        if not issues:
            eligible[key].append((reported_at, report_id, row))
        row["issue_code"] = ";".join(issues)
        review_rows.append(row)

    selected = {}
    for key, submissions in eligible.items():
        winner = max(submissions, key=lambda item: (item[0], item[1]))[2]
        selected[key] = winner
        for _, _, row in submissions:
            if row is winner:
                row["review_status"] = "accepted"
            else:
                row["review_status"] = "superseded"
                row["issue_code"] = "later_valid_submission"

    return review_rows, selected, counts_by_month


def build_facility_months(facilities, targets, selected, counts_by_month):
    """Create one row per expected facility-month, including missing reports."""
    result = []
    for (facility_id, period), target in sorted(targets.items()):
        submission = selected.get((facility_id, period))
        count = counts_by_month[(facility_id, period)]
        status = "accepted" if submission else "invalid" if count else "missing"
        doses = int(submission["doses_delivered"]) if submission else None
        result.append(
            {
                "facility_id": facility_id,
                "facility_name": facilities[facility_id]["facility_name"],
                "area": facilities[facility_id]["area"],
                "period": period,
                "target_doses": target,
                "reporting_status": status,
                "submission_count": count,
                "selected_report_id": submission["report_id"] if submission else "",
                "accepted_doses": doses if doses is not None else "",
                "variance_doses": doses - target if doses is not None else "",
            }
        )
    return result


def run_pipeline(input_dir=DEFAULT_INPUT, output_dir=DEFAULT_OUTPUT):
    facilities, targets = load_dimensions(input_dir)
    review_rows, selected, counts_by_month = review_reports(
        input_dir, facilities, targets
    )
    facility_months = build_facility_months(
        facilities, targets, selected, counts_by_month
    )
    status_counts = Counter(row["reporting_status"] for row in facility_months)
    review_counts = Counter(row["review_status"] for row in review_rows)
    issue_counts = Counter(
        issue
        for row in review_rows
        for issue in row["issue_code"].split(";")
        if issue
    )
    summary = {
        "data_label": "synthetic demonstration data",
        "expected_facility_months": len(targets),
        "submitted_facility_months": sum(
            row["submission_count"] > 0 for row in facility_months
        ),
        "reporting_status_counts": dict(sorted(status_counts.items())),
        "submission_review_counts": dict(sorted(review_counts.items())),
        "issue_counts": dict(sorted(issue_counts.items())),
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(
        output_dir / "facility_month_status.csv",
        facility_months,
        (
            "facility_id", "facility_name", "area", "period", "target_doses",
            "reporting_status", "submission_count", "selected_report_id",
            "accepted_doses", "variance_doses",
        ),
    )
    write_csv(
        output_dir / "report_review.csv",
        review_rows,
        (
            "report_id", "facility_id", "period", "doses_delivered",
            "reported_at", "review_status", "issue_code",
        ),
    )
    with (output_dir / "quality_summary.json").open("w", encoding="utf-8") as output:
        json.dump(summary, output, indent=2)
        output.write("\n")
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    summary = run_pipeline(args.input_dir, args.output_dir)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
