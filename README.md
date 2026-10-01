# Health Programme Analytics

A portfolio demonstration for a Data Science and AI Manager role. It answers:
**Which fictional facilities need follow-up because reports are missing,
invalid, or below an operational target?** All data and results are synthetic.
There are no patient records or claims about real Nigerian facilities.

The project includes multi-source ingestion and validation, an auditable
PostgreSQL warehouse design, advanced SQL views, a working interactive
dashboard, a time-series forecasting comparison, and a local AI-assisted
draft report with citation and number checks.

## Run on Windows

From this repository in PowerShell:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe .\run_all.py
.\.venv\Scripts\python.exe -m streamlit run dashboard/app.py
```

`run_all.py` generates the fictional source files, validates them, compares
forecasting methods, drafts a review brief, and runs tests. The dashboard
opens in a browser. If local Ollama with `llama3.2:latest` is unavailable,
the reporting step uses a clearly recorded deterministic fallback. You can
force that path with `python src/report_assistant.py --offline`.

To load PostgreSQL, set `PG_DSN` to a **development database** connection
string and run `python src/load_postgres.py`. The loader transactionally
replaces only tables in the `portfolio_health` schema. `sql/analysis.sql`
contains example decision queries. GitHub Actions tests the loader and SQL
views against a temporary PostgreSQL service.

## What each part does

| Component | Main files | Decision protected |
| --- | --- | --- |
| Synthetic sources | `src/generate_demo_data.py`, `data/synthetic/` | Reproducible multi-source demonstration |
| Data quality | `src/validate_data.py`, `data/processed/` | Missing, invalid, resubmitted, and zero reports stay distinct |
| Warehouse | `sql/`, `src/load_postgres.py` | Consistent facility-month facts and auditable submissions |
| Dashboard | `dashboard/app.py`, `powerbi/` | Reporting and comparable target metrics |
| Forecast | `src/forecast_service_volume.py`, `data/forecast/` | Time-based evaluation against a baseline |
| Reporting | `src/report_assistant.py`, `reports/` | Cited draft with verified source numbers and human review |

The source data has six fictional facilities and 36 months, creating 216
expected facility-months. Intentional quality cases include two missing
reports, one submitted zero, one negative count, a later resubmission, and
an unknown facility. The processed fact table contains 213 accepted, two
missing, and one invalid facility-month. The raw review log retains every
submission and its decision.

The forecast models **delivered doses**, not unique vaccinated children,
coverage, true vaccine demand, or health outcomes. It trains on 2023–2024
and compares methods on complete months in 2025. Forecast bands are
illustrative, and the small synthetic holdout does not demonstrate real
programme impact.

## Learn and present the work

- [Code walkthrough](docs/code_walkthrough.md): concepts and important lines in execution order.
- [Architecture](docs/architecture.md) and [data dictionary](docs/data_dictionary.md).
- [Evaluation report](docs/evaluation_report.md) and [management brief](docs/management_brief.md).
- [Responsible data and AI design](docs/governance.md), [concept note](docs/concept_note.md), and [five-minute demo](docs/five_minute_demo.md).
- [Power BI build kit](powerbi/README.md): Power Query, DAX, relationships, and layout. Power BI Desktop was unavailable here, so no native `.pbix` or `.pbip` has been verified.

This repository uses GitHub Actions for repeatable tests. It proposes an
Azure operating architecture in the architecture document, but does not
claim a cloud deployment or legal compliance certification.
