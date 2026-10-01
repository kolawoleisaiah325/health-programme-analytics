"""Replace this project's PostgreSQL tables with validated portfolio data."""

import csv
import os
from datetime import date
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def rows_from_csv(path):
    with path.open(newline="", encoding="utf-8") as source:
        return list(csv.DictReader(source))


def load_database(dsn):
    try:
        import psycopg
    except ImportError as error:
        raise SystemExit("Install requirements.txt before loading PostgreSQL") from error

    source_dir = PROJECT_ROOT / "data" / "synthetic"
    processed_dir = PROJECT_ROOT / "data" / "processed"
    facilities = rows_from_csv(source_dir / "facilities.csv")
    months = rows_from_csv(processed_dir / "facility_month_status.csv")
    reviews = rows_from_csv(processed_dir / "report_review.csv")
    schema_sql = (PROJECT_ROOT / "sql" / "schema.sql").read_text(encoding="utf-8")

    # A connection context commits every statement together or rolls all of
    # them back. The replacement touches only the portfolio_health schema.
    with psycopg.connect(dsn, connect_timeout=5) as connection:
        with connection.cursor() as cursor:
            for statement in schema_sql.split(";"):
                if statement.strip():
                    cursor.execute(statement)
            cursor.execute(
                "TRUNCATE portfolio_health.report_review, "
                "portfolio_health.facility_month, portfolio_health.facility"
            )
            cursor.executemany(
                "INSERT INTO portfolio_health.facility "
                "(facility_id, facility_name, area, facility_type) "
                "VALUES (%s, %s, %s, %s)",
                [
                    (r["facility_id"], r["facility_name"], r["area"], r["facility_type"])
                    for r in facilities
                ],
            )
            cursor.executemany(
                "INSERT INTO portfolio_health.facility_month "
                "(facility_id, month_start, target_doses, reporting_status, "
                "submission_count, selected_report_id, accepted_doses, variance_doses) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                [
                    (
                        r["facility_id"],
                        date.fromisoformat(r["period"] + "-01"),
                        int(r["target_doses"]),
                        r["reporting_status"],
                        int(r["submission_count"]),
                        r["selected_report_id"] or None,
                        int(r["accepted_doses"]) if r["accepted_doses"] else None,
                        int(r["variance_doses"]) if r["variance_doses"] else None,
                    )
                    for r in months
                ],
            )
            cursor.executemany(
                "INSERT INTO portfolio_health.report_review "
                "(source_row_number, report_id, facility_id, period, "
                "doses_delivered_text, reported_at_text, review_status, issue_code) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                [
                    (
                        index,
                        r["report_id"],
                        r["facility_id"],
                        r["period"],
                        r["doses_delivered"],
                        r["reported_at"],
                        r["review_status"],
                        r["issue_code"],
                    )
                    for index, r in enumerate(reviews, start=1)
                ],
            )
            cursor.execute(
                "SELECT COUNT(*), COUNT(*) FILTER (WHERE reporting_status = 'accepted') "
                "FROM portfolio_health.facility_month"
            )
            expected, accepted = cursor.fetchone()
            if (expected, accepted) != (len(months), sum(
                r["reporting_status"] == "accepted" for r in months
            )):
                raise ValueError("Database row counts differ from validated input")
    return {"facilities": len(facilities), "facility_months": expected,
            "accepted_facility_months": accepted, "reviewed_submissions": len(reviews)}


if __name__ == "__main__":
    dsn = os.environ.get("PG_DSN")
    if not dsn:
        raise SystemExit("Set PG_DSN to a development PostgreSQL connection string")
    print(load_database(dsn))
