# Data dictionary and metric definitions

All source records are synthetic and reproducible with `src/generate_demo_data.py`.

| Dataset | Grain | Key | Notes |
| --- | --- | --- | --- |
| `data/synthetic/facilities.csv` | One facility | `facility_id` | Fictional names, areas and types |
| `data/synthetic/monthly_reports.csv` | One submission | `report_id` | Multiple submissions may share a facility and period |
| `data/synthetic/programme_targets.json` | One facility-month | `facility_id`, `period` | The expected reporting frame |
| `data/processed/facility_month_status.csv` | One expected facility-month | `facility_id`, `period` | Selected values and reporting status |
| `data/processed/report_review.csv` | One source submission | Source row order | Every submission's decision and reason |
| `data/forecast/service_volume_forecast.csv` | One future month | `period` | Illustrative service-volume forecast |

`period` is a `YYYY-MM` reporting month. `doses_delivered` is a count of doses
recorded by one submission. It is not a count of unique children or completed
vaccination courses. `reported_at` is the submission date; it determines the
latest valid resubmission. `target_doses` is a fictional monthly operational
target. It is not a population denominator.

In the processed table, `reporting_status` is one of:

- `accepted`: a valid submission was selected; `accepted_doses` is a nonnegative integer, including zero.
- `missing`: no submission exists; `accepted_doses` is blank.
- `invalid`: one or more submissions exist, but none is valid; `accepted_doses` is blank.

`submission_count` counts source submissions for that facility-month, even
if they were rejected or superseded. `selected_report_id` identifies the
accepted submission. `variance_doses` is `accepted_doses - target_doses` and
is blank when no report was accepted.

The review log uses `review_status` values `accepted`, `superseded`, and
`rejected`. `issue_code` explains rejection or supersession. An unknown
facility stays in this log and never enters the facility-month fact table.

The dashboard metrics are:

- **Reporting completeness:** facility-months with any submission / expected facility-months.
- **Acceptance rate:** facility-months with an accepted submission / expected facility-months.
- **Delivered doses:** sum of accepted doses. This total is incomplete when reporting is incomplete.
- **Comparable target attainment:** accepted doses / targets for accepted facility-months only.
- **Follow-up threshold:** accepted doses below 80% of the target. This is a demonstration rule, not a clinical standard.

The time-series target is monthly **delivered doses**, a service-volume
measure. A stockout can suppress recorded delivery and make it a poor proxy
for actual demand. No procurement benefit is claimed.
