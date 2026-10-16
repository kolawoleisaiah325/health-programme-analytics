"""Create fictional immunisation programme inputs with repeatable quality issues."""

import argparse
import csv
import json
import math
import random
from datetime import date
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data" / "synthetic"
RANDOM_SEED = 42
FIRST_YEAR = 2023
MONTH_COUNT = 36

# Facility-months whose regular report is changed. None means no report at
# all: a missing report must not become a zero-dose report.
REPORT_OVERRIDES = {
    ("F003", "2025-02"): None,
    ("F006", "2025-04"): None,
    ("F001", "2025-07"): 0,  # A submitted, valid zero-dose report.
    ("F005", "2025-06"): -4,  # An invalid count for the quality review to catch.
    # Valid but low counts, like a stockout month, for performance follow-up.
    ("F004", "2025-03"): 95,
    ("F002", "2025-09"): 90,
    ("F006", "2025-10"): 120,
    ("F003", "2025-11"): 100,
}

# Extra submissions appended after the regular reports. Each one exercises a
# validation rule; "report_id": None means "assign the next free ID".
EXTRA_SUBMISSIONS = [
    # A later valid resubmission; do not add both reports together.
    {"report_id": None, "facility_id": "F002", "period": "2025-05",
     "doses_delivered": 125, "reported_at": ("2025-05", 19)},
    # A facility code absent from the register.
    {"report_id": None, "facility_id": "F999", "period": "2025-08",
     "doses_delivered": 90, "reported_at": ("2025-08", 6)},
    # Reuses the first report's ID, so it cannot be told apart in an audit.
    {"report_id": "R0001", "facility_id": "F004", "period": "2025-09",
     "doses_delivered": 150, "reported_at": ("2025-09", 12)},
    # A month that does not exist.
    {"report_id": None, "facility_id": "F002", "period": "2025-13",
     "doses_delivered": 120, "reported_at": "2026-01-08"},
    # A real month outside the agreed reporting frame.
    {"report_id": None, "facility_id": "F001", "period": "2026-01",
     "doses_delivered": 101, "reported_at": "2026-02-06"},
    # A submission date that cannot be parsed.
    {"report_id": None, "facility_id": "F003", "period": "2025-10",
     "doses_delivered": 130, "reported_at": "not-a-date"},
    # Submitted before the reporting month had ended.
    {"report_id": None, "facility_id": "F004", "period": "2025-11",
     "doses_delivered": 140, "reported_at": "2025-11-20"},
]


def reporting_periods():
    """Return monthly YYYY-MM labels starting in January of FIRST_YEAR."""
    return [
        f"{FIRST_YEAR + index // 12}-{index % 12 + 1:02d}"
        for index in range(MONTH_COUNT)
    ]


def submission_date(period, day=6):
    """Give a submission date in the month after the reporting period."""
    year, month = map(int, period.split("-"))
    return date(year + month // 12, month % 12 + 1, day).isoformat()


def write_csv(path, rows, columns):
    """Write rows with a stable column order, UTF-8 and LF line endings."""
    with path.open("w", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(output, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def expected_doses(facility_number, month_index, rng):
    """Facility size, a gentle upward trend, winter seasonality and noise."""
    trend = 0.5 * month_index
    seasonal = 8 * math.cos(2 * math.pi * (month_index % 12) / 12)
    return round(85 + 12 * facility_number + trend + seasonal + rng.randint(-9, 9))


def generate(output_dir=DATA_DIR, seed=RANDOM_SEED):
    """Build three sources that later pipeline stages will join and validate."""
    rng = random.Random(seed)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

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
        for month_index, period in enumerate(reporting_periods()):
            key = (facility["facility_id"], period)
            doses = expected_doses(facility_number, month_index, rng)
            targets.append(
                {
                    "facility_id": facility["facility_id"],
                    "period": period,
                    "target_doses": 100 + 12 * facility_number,
                }
            )
            if key in REPORT_OVERRIDES:
                doses = REPORT_OVERRIDES[key]
                if doses is None:
                    continue
            reports.append(
                {
                    "report_id": f"R{len(reports) + 1:04d}",
                    "facility_id": facility["facility_id"],
                    "period": period,
                    "doses_delivered": doses,
                    "reported_at": submission_date(period),
                }
            )

    for extra in EXTRA_SUBMISSIONS:
        reported_at = extra["reported_at"]
        if isinstance(reported_at, tuple):
            reported_at = submission_date(*reported_at)
        reports.append(
            {
                **extra,
                "report_id": extra["report_id"] or f"R{len(reports) + 1:04d}",
                "reported_at": reported_at,
            }
        )

    write_csv(
        output_dir / "facilities.csv",
        facilities,
        ("facility_id", "facility_name", "area", "facility_type"),
    )
    write_csv(
        output_dir / "monthly_reports.csv",
        reports,
        ("report_id", "facility_id", "period", "doses_delivered", "reported_at"),
    )
    with (output_dir / "programme_targets.json").open(
        "w", encoding="utf-8", newline="\n"
    ) as output:
        json.dump(targets, output, indent=2)
        output.write("\n")

    print(
        f"Generated {len(facilities)} facilities, {len(reports)} reports, "
        f"and {len(targets)} targets in {output_dir}"
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DATA_DIR)
    parser.add_argument("--seed", type=int, default=RANDOM_SEED)
    args = parser.parse_args()
    generate(args.output_dir, args.seed)


if __name__ == "__main__":
    main()
