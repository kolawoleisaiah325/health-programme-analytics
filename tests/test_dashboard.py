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


if __name__ == "__main__":
    unittest.main()
