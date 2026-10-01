# Draft programme decision brief

**Synthetic demonstration data | Human review required before use**

Generation method: local Ollama model llama3.2:latest with output validation.

## Evidence checked from source files

- **E1:** 214 of 216 expected facility-months had a submitted report. Source: `data/processed/quality_summary.json`.
- **E2:** Accepted: 213; missing: 2; invalid: 1. Source: `data/processed/quality_summary.json`.
- **E3:** Unresolved facility-months: F003 2025-02: missing; F005 2025-06: invalid; F006 2025-04: missing. Source: `data/processed/facility_month_status.csv`.
- **E4:** 5 accepted facility-months in 2025 were below 80% of their dose target. Source: `data/processed/facility_month_status.csv`.
- **E5:** Forecast method: holt_winters; holdout MAE: 27.38 doses across 9 complete synthetic months. Source: `data/forecast/model_diagnostics.json`.

## Interpretation

Facility-month reports are mostly submitted, but some are missing or invalid. [E1] [E2]

## Recommended review actions

- Verify facility-month reports for completeness and validity. [E1] [E2] [E3]
- Identify and follow up on specific missing and invalid reports. [E1] [E2] [E3]
- Review service-volume forecasts for accuracy and completeness. [E4] [E5]

## Review checklist

- Confirm source period, facility definitions, and target definitions.
- Check each recommendation against the cited record and local context.
- Do not treat delivered doses as unique children, coverage, or latent demand.
- Approve or edit this draft with a named human reviewer before sharing.
