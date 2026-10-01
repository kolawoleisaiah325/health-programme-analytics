"""Create fictional immunisation programme inputs with repeatable quality issues."""

import csv
import json
import random
from datetime import date
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data" / "synthetic"
RANDOM_SEED = 42


def reporting_periods():
    """Return 36 monthly labels, from January 2023 through December 2025."""
    return [f"{2023 + index // 12}-{index % 12 + 1:02d}" for index in range(36)]


def submission_date(period, day=6):
    """Give a submission date in the month after the reporting period."""
    year, month = map(int, period.split("-"))
    return date(year + month // 12, month % 12 + 1, day).isoformat()


def write_csv(path, rows, columns):
    """Write rows with a stable column order and portable UTF-8 encoding."""
    with path.open("w", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(output, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def generate():
    """Build three sources that later pipeline stages will join and validate."""
    rng = random.Random(RANDOM_SEED)
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    facilities = [
        {
            "facility_id": f"F{number:03d}",
            "facility_name": f"Demo Facility {number:02d}",
            "area": "Demo Area A" if number <= 3 else "Demo Area B",
            "facility_type": "Clinic" if number % 2 else "Health centre",
        }
        for number in range(1, 7)
    ]

    reports = []
    targets = []
    for facility_number, facility in enumerate(facilities, start=1):
        for period in reporting_periods():
            month_number = int(period[-2:])
            seasonal_change = 9 if month_number in (1, 2, 11, 12) else -4
            normal_doses = (
                85 + 12 * facility_number + seasonal_change + rng.randint(-9, 9)
            )

            targets.append(
                {
                    "facility_id": facility["facility_id"],
                    "period": period,
                    "target_doses": 100 + 12 * facility_number,
                }
            )

            # A missing report has no row. It must not become a zero-dose report.
            if (facility["facility_id"], period) in {
                ("F003", "2025-02"),
                ("F006", "2025-04"),
            }:
                continue

            doses = normal_doses
            if (facility["facility_id"], period) == ("F001", "2025-07"):
                doses = 0  # A submitted, valid zero-dose report.
            if (facility["facility_id"], period) == ("F005", "2025-06"):
                doses = -4  # An invalid count for the quality review to catch.

            reports.append(
                {
                    "report_id": f"R{len(reports) + 1:04d}",
                    "facility_id": facility["facility_id"],
                    "period": period,
                    "doses_delivered": doses,
                    "reported_at": submission_date(period),
                }
            )

    reports.append(
        {
            "report_id": f"R{len(reports) + 1:04d}",
            "facility_id": "F002",
            "period": "2025-05",
            "doses_delivered": 125,
            "reported_at": submission_date("2025-05", day=19),
        }
    )  # A later resubmission; do not add both reports together.
    reports.append(
        {
            "report_id": f"R{len(reports) + 1:04d}",
            "facility_id": "F999",
            "period": "2025-08",
            "doses_delivered": 90,
            "reported_at": submission_date("2025-08"),
        }
    )  # A facility code absent from the register.

    write_csv(
        DATA_DIR / "facilities.csv",
        facilities,
        ("facility_id", "facility_name", "area", "facility_type"),
    )
    write_csv(
        DATA_DIR / "monthly_reports.csv",
        reports,
        ("report_id", "facility_id", "period", "doses_delivered", "reported_at"),
    )
    with (DATA_DIR / "programme_targets.json").open("w", encoding="utf-8") as output:
        json.dump(targets, output, indent=2)
        output.write("\n")

    print(f"Generated {len(facilities)} facilities, {len(reports)} reports, ")
    print(f"and {len(targets)} targets in {DATA_DIR}")


if __name__ == "__main__":
    generate()
