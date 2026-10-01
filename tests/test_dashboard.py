"""Run the dashboard without a browser to catch runtime errors."""

import unittest
from pathlib import Path

from streamlit.testing.v1 import AppTest


class DashboardTest(unittest.TestCase):
    def test_dashboard_renders_with_generated_data(self):
        app_file = Path(__file__).resolve().parents[1] / "dashboard" / "app.py"
        app = AppTest.from_file(str(app_file), default_timeout=60).run()
        self.assertEqual(len(app.exception), 0)
        self.assertEqual(app.title[0].value, "Health programme performance")
        self.assertEqual(app.metric[0].value, "99.1%")
        self.assertEqual(app.metric[1].value, "213 / 216")

    def test_area_period_empty_selection_and_reset(self):
        app_file = Path(__file__).resolve().parents[1] / "dashboard" / "app.py"
        app = AppTest.from_file(str(app_file), default_timeout=60).run()
        app.multiselect[0].set_value(["Demo Area A"]).run()
        self.assertEqual(len(app.exception), 0)
        self.assertEqual(app.metric[1].value, "107 / 108")
        app.select_slider[0].set_value(("2023-02", "2025-12")).run()
        self.assertEqual(app.metric[1].value, "104 / 105")
        app.multiselect[0].set_value([]).run()
        self.assertEqual(len(app.exception), 0)
        self.assertEqual(len(app.metric), 0)
        self.assertIn("Select at least one area", app.info[0].value)
        app.button[0].click().run()
        self.assertEqual(len(app.exception), 0)
        self.assertEqual(app.metric[1].value, "213 / 216")

    def test_action_categories_keep_missing_and_reported_zero_distinct(self):
        app_file = Path(__file__).resolve().parents[1] / "dashboard" / "app.py"
        app = AppTest.from_file(str(app_file), default_timeout=60).run()
        app.selectbox[0].select("Missing reports").run()
        actions = next(table.value for table in app.dataframe if "action" in table.value.columns)
        self.assertEqual(len(actions), 2)
        self.assertTrue(actions["accepted_doses"].isna().all())
        self.assertEqual(set(actions["action"]), {"Request report"})
        app.select_slider[0].set_value(("2025-07", "2025-07")).run()
        self.assertEqual(len(app.exception), 0)
        self.assertIn("No follow-up items", app.success[0].value)
        app.selectbox[0].select("Below target").run()
        actions = next(table.value for table in app.dataframe if "action" in table.value.columns)
        reported_zero = actions[actions["facility_name"] == "Demo Facility 01"].iloc[0]
        self.assertEqual(reported_zero["accepted_doses"], 0)
        self.assertEqual(reported_zero["action"], "Discuss low service volume")


if __name__ == "__main__":
    unittest.main()
