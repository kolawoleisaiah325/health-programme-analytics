# Management brief: immunisation reporting prototype

**Decision requested:** For this fictional demonstration, prioritise follow-up
of missing and invalid facility reports before interpreting the associated
performance or forecast. No decision about an actual facility is warranted.

The synthetic data has 216 expected facility-months. Reports arrived for 214
of them (99.1%), and 213 produced an accepted count. F003 in February 2025
and F006 in April 2025 have no report. F005 in June 2025 submitted a negative
count and needs correction. F001 in July 2025 submitted a valid zero; it
should be discussed as a reported operational value, not treated as missing.
Five accepted facility-months in 2025 were below the demonstration threshold
of 80% of their dose target.

**Recommended programme workflow:** Ask the relevant partner to submit the
two missing reports and correct the negative submission. Review the five
below-threshold months with facility teams to understand context before
inferring a cause. Keep the original submissions and correction history in
the audit table. Refresh the dashboard after corrections.

A 2026 service-volume forecast was backtested against nine complete months
in 2025. Holt-Winters had the lowest observed MAE (27.38 doses), compared
with 31.78 for the seasonal naïve baseline. This small synthetic test does
not validate procurement decisions. Missing data were imputed for the final
fit, the holdout was also used to choose the model, and delivered doses are
not the same as underlying demand.

**What the manager should ask next:** Do source records confirm the missing
and corrected submissions? Are target definitions comparable across
facilities? Were any low volumes caused by stockouts, staffing, or access
issues? Those causes cannot be determined from this dataset.

Sources: `data/processed/quality_summary.json`,
`data/processed/facility_month_status.csv`, and
`data/forecast/model_diagnostics.json`. All figures are synthetic.
