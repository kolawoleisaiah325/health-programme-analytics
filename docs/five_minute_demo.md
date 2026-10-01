# Five-minute portfolio demonstration

**0:00–0:45 — Decision.** Open the dashboard. Explain the manager's question:
which facility-months need follow-up, and can the data support that action?
State that all data is synthetic.

**0:45–1:30 — Source problem.** Open the three source files. Point out that
facilities, monthly submissions, and targets have different grains. Show
F002's two May 2025 submissions and the intentionally missing F003 report.

**1:30–2:15 — Quality controls.** Run `src/validate_data.py`. In the review
log, show the accepted resubmission, the rejected negative count, and the
unknown facility. In the facility-month table, contrast F001's valid zero
with F003's blank missing value.

**2:15–3:00 — SQL and dashboard.** Show `v_monthly_performance` and the
dashboard. Explain reporting completeness versus accepted-month target
attainment. Filter to an area and display the follow-up table. If asked
about Power BI, show the M queries, DAX measures, and model relationship
specification; state that Desktop authoring remains unverified.

**3:00–3:45 — Forecast.** Show the seasonal naïve baseline, time split, three
incomplete holdout months, and Holt-Winters result. Explain why the error
band is illustrative and why delivered doses do not prove demand.

**3:45–4:30 — AI review.** Open the brief and its validation JSON. Show that
the model supplies cited qualitative prose while Python inserts exact
figures. Demonstrate that a fake numeric claim fails its test. Emphasise
human sign-off.

**4:30–5:00 — Management conclusion.** Recommend resolving source quality
issues before interpreting low-volume months. Describe the next real-data
pilot gates: definitions, legal basis, partner reconciliation, prospective
model validation, and accountable owners.
