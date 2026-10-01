# Learn the code, step by step

Start at `src/generate_demo_data.py`, then read `src/validate_data.py`,
`sql/schema.sql`, `src/load_postgres.py`, `src/forecast_service_volume.py`,
`dashboard/app.py`, and `src/report_assistant.py`. The data flows in that order.

## 1. Generate the sources

`PROJECT_ROOT = Path(__file__).resolve().parents[1]` finds the repository
from the script's location. `__file__` means “this source file.” `resolve()`
turns it into an absolute path. `parents[1]` moves from `src/` to the project
root. This makes the script work regardless of the terminal's current folder.

`rng = random.Random(42)` creates a private random number generator with a
fixed seed. Every run draws the same sequence, so the CSV and JSON files are
reproducible. The generator loops over six fictional facilities and 36 months.
It writes one target per facility-month, then writes the submitted reports.
It deliberately skips two reports and inserts several quality problems. The
different source formats simulate a partner-data integration task.

## 2. Validate without losing the audit trail

`csv.DictReader` returns a dictionary for each row using the CSV headers as
keys. The validator forms a **natural key** with `(facility_id, period)`.
That tuple means “this facility in this month.” The target table must have
exactly one target for each such key; otherwise the pipeline stops.

Each submitted row passes rules for facility ID, month, nonnegative integer
count, and a submission date after the reporting month. An invalid row is
kept in `report_review.csv` with its reason. Valid resubmissions are grouped
by natural key. The expression
`max(submissions, key=lambda item: (item[0], item[1]))` selects the latest
submission date, using report ID to break a same-day tie. Other valid
submissions become `superseded`.

The facility-month output starts from **all targets**, not from reports.
That is why it includes a row even when nothing was submitted. Its status
logic is: selected valid row → `accepted`; otherwise at least one submission
→ `invalid`; otherwise → `missing`. The code uses `None` for unknown doses
and writes a blank CSV cell. It preserves a submitted `0` as the number zero.

Think through this example: F001 in July 2025 submitted zero doses. If a
dashboard replaced blanks with zero, F003's absent February report would
look identical to F001. That would lead to the wrong follow-up action.

## 3. Store the result in PostgreSQL

`sql/schema.sql` defines the database structure. `PRIMARY KEY` prevents two
rows for the same facility-month. The foreign key links each facility-month
to the facility register. `CHECK` constraints prevent negative accepted
counts and require a dose value only for accepted rows. The audit table uses
a source-row number as its key, preserving even malformed or duplicate
report IDs.

`src/load_postgres.py` reads the validated CSV files and runs parameterized
`INSERT` statements. `%s` placeholders let the driver transmit values
separately from SQL text. The `with psycopg.connect(...)` block is a
transaction: all project tables update together or roll back together. The
loader replaces only tables in `portfolio_health`; it never touches other
schemas. `PG_DSN` supplies the connection string outside the repository.

The SQL view `v_monthly_performance` uses `COUNT(*) FILTER (WHERE ...)` to
count accepted, missing, and invalid rows in one grouped query. Its target
sum includes only accepted months. `v_facility_trend` uses the window
function `LAG` to retrieve the prior month's accepted count for each
facility without collapsing monthly rows. `sql/analysis.sql` shows joins,
grouping, `NULLIF` to avoid division by zero, and `DENSE_RANK` for area
review priority.

## 4. Forecast without using future information in training

The forecast trains on 2023–2024 and evaluates on 2025. It compares three
methods: last year's same month (seasonal naïve), ridge regression with a
time trend and annual sine/cosine features, and Holt-Winters seasonal
smoothing. Each method predicts 2025 without seeing 2025 outcomes during
fit. Model error is measured only for the nine 2025 months where all six
facilities have accepted reports. A partial month's observed total would
understate service volume and unfairly penalize forecasts.

MAE is the average absolute difference between predicted and observed dose
counts. WAPE is the total absolute error divided by total observed doses.
The chosen method has the smallest holdout MAE. The same holdout selected
and assessed the model, so this error estimate may be optimistic; an
independent future period would provide a stronger assessment.

For the final 2026 fit, three incomplete 2025 facility-months borrow that
facility's value from the same month in 2024. This is labelled as an
assumption and is never treated as observed truth in the holdout score.
The forecast's shaded range uses an empirical holdout error size; it is
not a calibrated probability interval. Delivered doses are not latent
commodity demand.

## 5. Turn data into a management dashboard

`dashboard/app.py` uses `st.cache_data` to avoid rereading files on every
interaction. Input file modification times form the cache key, so a pipeline
refresh reloads the data. Area and month controls filter the fact table. The four
cards answer different questions: Was a report submitted? Was it accepted?
How many doses were recorded? How did accepted months compare with their
targets? The denominator for target attainment includes only accepted
months. The follow-up table shows missing, invalid, and below-threshold
facility-months with different actions.

The dashboard keeps presentation separate from the source records:

- `.streamlit/config.toml` supplies the light theme and navy sidebar;
  `dashboard/style.css` controls card spacing, typography and responsive sizing.
- `st.session_state` remembers the selected areas and period. The reset
  callback selects all areas and clears the slider's saved state, restoring
  its default range before Streamlit redraws the page.
- `monthly_totals()` groups facility records into monthly chart values.
  `sum(min_count=1)` requires at least one known value; a completely unknown
  month's total stays blank rather than becoming zero.
- `chart_style()` applies consistent colours, axes and hover behaviour.
  Amber markers identify partial monthly totals in the performance chart.
- `export_csv()` adds a synthetic-data label to each exported row. The
  action-list download follows both the sidebar and category filters.
- The forecast shows its programme-wide scope explicitly. Its historical
  line has gaps where reporting was incomplete; its model is not refitted
  when a user changes the dashboard filters.

The dashboard tests change area and period, clear the selection, reset it,
and check that missing reports and valid zero reports produce different actions.

`powerbi/` contains equivalent Power Query imports and DAX measures.
`CALCULATE` changes the filter context for a measure; `DIVIDE` handles a
zero denominator safely. Power BI Desktop was unavailable here, so those
definitions need a desktop verification pass before claiming a native
Power BI report.

## 6. Draft a report with checked evidence

`src/report_assistant.py` builds an evidence pack from files produced by
earlier stages. It sends a short, qualitative version to the local Ollama
model. The model returns JSON with a summary, actions, and evidence IDs.
`validate_draft` rejects missing citations, unknown evidence IDs, numeric
claims in model prose, and several unsupported causal phrases. Exact
numbers are rendered from the source files by Python, not composed by the
model. If the model is unavailable or fails validation, deterministic
language is used and the failure is recorded. The output remains a draft
for human review; the validator cannot prove every sentence is correct.

## 7. Repeat the work and inspect failures

The scripts and dependencies are versioned. Unit tests check missing versus
zero, resubmission selection, duplicate targets, forecast split, dashboard
rendering, and LLM output rules. GitHub Actions additionally loads a real
temporary PostgreSQL database and queries its views. A failed check stops
the pipeline from being represented as verified.

To practise for an interview, explain **the decision each stage protects**:
the validator protects report credibility, the SQL model protects metric
definitions, the forecast protects against time leakage and missing-data
bias, and the assistant protects against unsupported claims.
