"""Catch copies of rules and quoted figures that drift from the source of truth."""

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
METHOD_LABELS = {
    "Seasonal naïve": "seasonal_naive",
    "Ridge trend and seasonality": "ridge_trend_seasonal",
    "Holt-Winters": "holt_winters",
}
# Forecast numbers can differ slightly across platforms' numeric libraries.
TOLERANCE = 0.05


def read(relative_path):
    return (ROOT / relative_path).read_text(encoding="utf-8")


def read_json(relative_path):
    return json.loads(read(relative_path))


class ThresholdConsistencyTest(unittest.TestCase):
    def test_sql_and_dax_use_the_shared_threshold(self):
        threshold = read_json("programme_rules.json")["follow_up_threshold"]
        for relative_path in ("sql/schema.sql", "sql/analysis.sql", "powerbi/measures.dax"):
            copies = re.findall(r"target_doses\]?\s*\*\s*([0-9.]+)", read(relative_path))
            with self.subTest(relative_path):
                self.assertTrue(copies, "threshold expression not found")
                self.assertEqual({float(value) for value in copies}, {threshold})


class DocumentedFiguresTest(unittest.TestCase):
    def setUp(self):
        self.diagnostics = read_json("data/forecast/model_diagnostics.json")
        self.quality = read_json("data/processed/quality_summary.json")

    def test_evaluation_report_forecast_table(self):
        report = read("docs/evaluation_report.md")
        rows = re.findall(r"^\| ([^|]+?) \| ([\d.]+) \| ([\d.]+)% \|$", report, re.M)
        documented = {METHOD_LABELS[label]: (float(mae), float(wape))
                      for label, mae, wape in rows}
        self.assertEqual(set(documented), set(self.diagnostics["candidate_scores"]))
        for method, scores in self.diagnostics["candidate_scores"].items():
            with self.subTest(method):
                self.assertAlmostEqual(documented[method][0], scores["mae"], delta=TOLERANCE)
                self.assertAlmostEqual(
                    documented[method][1], scores["wape_percent"], delta=TOLERANCE
                )
        band = float(re.search(r"approximately\s+([\d.]+)\s+doses", report).group(1))
        self.assertAlmostEqual(
            band, self.diagnostics["illustrative_error_band_doses"], delta=TOLERANCE
        )
        self.assertIn(f"{self.diagnostics['scored_forecasts']} scored forecasts", report)

    def test_management_brief_quotes_selected_model_error(self):
        brief = read("docs/management_brief.md")
        selected = self.diagnostics["selected_model"]
        mae = self.diagnostics["candidate_scores"][selected]["mae"]
        quoted = [float(value) for value in re.findall(r"MAE ([\d.]+) doses", brief)]
        self.assertTrue(any(abs(value - mae) <= TOLERANCE for value in quoted))

    def test_quality_figures_in_docs(self):
        submitted = self.quality["submitted_facility_months"]
        expected = self.quality["expected_facility_months"]
        completeness = f"{100 * submitted / expected:.1f}%"
        accepted = self.quality["reporting_status_counts"]["accepted"]
        for relative_path in ("docs/evaluation_report.md", "docs/management_brief.md"):
            text = read(relative_path)
            with self.subTest(relative_path):
                for figure in (completeness, str(submitted), str(expected), str(accepted)):
                    self.assertIn(figure, text)


if __name__ == "__main__":
    unittest.main()
