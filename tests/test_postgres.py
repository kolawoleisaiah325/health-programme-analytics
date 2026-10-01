"""Query the real PostgreSQL schema in CI's temporary database."""

import os
import unittest


@unittest.skipUnless(os.environ.get("PG_DSN"), "PG_DSN is not set")
class PostgreSQLIntegrationTest(unittest.TestCase):
    def test_loaded_warehouse_and_views(self):
        import psycopg

        with psycopg.connect(os.environ["PG_DSN"]) as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM portfolio_health.facility")
                self.assertEqual(cursor.fetchone()[0], 6)
                cursor.execute("SELECT COUNT(*) FROM portfolio_health.facility_month")
                self.assertEqual(cursor.fetchone()[0], 216)
                cursor.execute("SELECT COUNT(*) FROM portfolio_health.report_review")
                self.assertEqual(cursor.fetchone()[0], 216)
                cursor.execute(
                    "SELECT SUM(missing_facility_months), "
                    "SUM(invalid_facility_months), SUM(accepted_facility_months) "
                    "FROM portfolio_health.v_monthly_performance"
                )
                self.assertEqual(cursor.fetchone(), (2, 1, 213))
                cursor.execute(
                    "SELECT accepted_doses FROM portfolio_health.facility_month "
                    "WHERE facility_id = 'F001' AND month_start = DATE '2025-07-01'"
                )
                self.assertEqual(cursor.fetchone()[0], 0)
                cursor.execute(
                    "SELECT COUNT(*) FROM portfolio_health.v_facility_followup "
                    "WHERE recommended_followup = 'Resolve rejected submission'"
                )
                self.assertEqual(cursor.fetchone()[0], 1)
                cursor.execute(
                    "SELECT COUNT(*) FROM portfolio_health.v_facility_trend "
                    "WHERE prior_month_accepted_doses IS NOT NULL"
                )
                self.assertGreater(cursor.fetchone()[0], 0)


if __name__ == "__main__":
    unittest.main()
