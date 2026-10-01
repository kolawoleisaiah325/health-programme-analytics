# Health Programme Analytics

A portfolio project for an immunisation programme reporting and decision platform.

## Decision question

Which facilities need follow-up because their monthly reports are missing, inconsistent, or below programme targets?

## Planned first version

- Read a facility register, monthly vaccination reports, and programme targets.
- Validate identifiers, reporting periods, duplicate submissions, and numeric values.
- Store approved data in PostgreSQL and analyse it with SQL.
- Present reporting completeness and performance against targets in Power BI.

Missing reports will be distinguished from reports containing zero doses. Doses delivered will not automatically be interpreted as numbers of fully vaccinated children or population coverage.

## Data

The first version will use clearly labelled synthetic demonstration data. It will not contain real patient records. Any findings from this data will demonstrate the workflow, not actual programme performance in Nigeria.

## Later milestones

Demand forecasting with time-based evaluation, followed by an evidence-grounded AI reporting assistant using validated metrics and human review.

## Current status

Synthetic inputs and an auditable validation pipeline are available. Warehouse
modelling, dashboarding, forecasting, and AI reporting are planned.

## Run the first milestone

From the project root, using the project's virtual environment on Windows:

```powershell
.\.venv\Scripts\python.exe .\src\check_setup.py
.\.venv\Scripts\python.exe .\src\generate_demo_data.py
.\.venv\Scripts\python.exe .\src\validate_data.py
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

The generator uses Python's standard library and a fixed random seed, so it does
not need pandas and produces the same files on repeated runs. The output is in
`data/synthetic/` and is committed for easy inspection.

| Source | Grain | Key fields | Rows |
| --- | --- | --- | ---: |
| `facilities.csv` | One fictional facility | `facility_id`, name, area, type | 6 |
| `monthly_reports.csv` | One submission | `report_id`, `facility_id`, `period`, `doses_delivered`, `reported_at` | 216 |
| `programme_targets.json` | One facility-month target | `facility_id`, `period`, `target_doses` | 216 |

The periods span January 2023 through December 2025. The intentionally inserted
quality cases are two missing facility-month reports, one submitted zero-dose
report, one negative dose count, one later resubmission, and one unknown facility
code. These are test cases, not observations about any real health programme.

## Validation outputs

`data/processed/facility_month_status.csv` has one row for every expected
facility-month. Its `reporting_status` is `accepted`, `missing`, or `invalid`.
`accepted_doses` is blank for missing and invalid reports, but can be `0` for
a valid submission. `submission_count` counts submissions, including rejected
ones, so data collection and data validity remain separate questions.

`data/processed/report_review.csv` keeps every submitted row with a decision:
`accepted`, `superseded`, or `rejected`, plus a reason code. Among valid
resubmissions for the same facility-month, the latest `reported_at` wins;
ties use `report_id` for a stable result. Invalid rows never become selected.
The three-source pipeline fails if a facility ID or target definition is
duplicated, since that would make joins ambiguous.

`data/processed/quality_summary.json` totals expected and submitted
facility-months, decision statuses, and issue codes. All outputs are derived
from fictional data and can be regenerated with the commands above.

## Planned tools

Python, pandas, PostgreSQL, SQL, Power BI, and Git.
