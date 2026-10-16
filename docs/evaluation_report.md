# Evaluation report

All results below come from **synthetic demonstration data**. They do not
measure a real programme or predict actual Nigerian service delivery.

## Data quality

The source has 6 fictional facilities and 36 months, giving 216 expected
facility-months. There are 221 submitted report rows, but submissions are
not the same as covered facility-months: two months have no submission,
one has a resubmission, and seven rows break a validation rule. The demo
data plants one case for every rule: an unknown facility code, a negative
count, a repeated report ID, an impossible month (`2025-13`), a month
outside the target frame, an unreadable submission date, and a report
dated before its month had ended.

The pipeline finds 214 facility-months with at least one submission
(99.1% reporting completeness), 213 with an accepted count, two missing,
and one with only an invalid negative count. The submission audit retains
213 accepted rows, seven rejected rows, and one superseded row. F001 in July
2025 is a submitted, valid zero, proving that null and zero remain distinct.

These counts were checked with integration tests against the versioned
synthetic files. Each rule also has a unit test on a small hand-made input,
as do same-day resubmission ties and an invalid correction that arrives
after a valid report. The pipeline rejects duplicate facility-month targets
before writing outputs. Future partner datasets would need additional
checks for schema changes, unit mismatches, late reporting, and conflicting
facility identifiers.

## Forecast design and result

The target is monthly **doses delivered**, an operational service-volume
measure. The first fit uses January 2023–December 2024. A rolling-origin
backtest then refits every method at each month from January to July 2025,
using only earlier months, and forecasts the next six months. Only months
with complete accepted reports are scored. February, April, and June are
excluded because a missing or invalid facility report would depress the
observed total. This gives 30 scored forecasts across nine complete months.

| Method | Backtest MAE, doses | Backtest WAPE |
| --- | ---: | ---: |
| Seasonal naïve | 41.40 | 5.15% |
| Ridge trend and seasonality | 45.87 | 5.70% |
| Holt-Winters | 42.30 | 5.26% |

The seasonal naïve baseline has the lowest MAE, and Holt-Winters is within
a dose of it. On this little data the more complex methods do not earn
their place, so the simplest one is used. Errors are dominated by
months with planted low but valid reports, including F001's July zero,
which a model trained on normal months cannot anticipate.

Months before a forecast origin that had a missing or invalid facility
report are filled from the same facility's prior-year month for fitting
only. They are never scored. The illustrative error band uses the
empirical 80th percentile of absolute backtest errors, approximately
70.00 doses. It comes from forecasts up to six months ahead, so 12-month
errors are likely larger. It is **not** a calibrated 80% prediction interval.

The same backtest selected and evaluated the model, so its error estimate
may be optimistic. A future rollout would reserve a later independent
period, test stability across facilities, and compare decisions under
realistic stock and supply constraints. Recorded doses can understate
demand during stockouts, so no procurement benefit is claimed from this
forecast.

## Reporting assistant

The local Ollama model drafts short qualitative statements using a limited
evidence pack. The program adds verified numbers and citations. It rejects
unknown citations, model-authored numbers (digits and spelled-out
quantities such as "two" or "half"), malformed outputs, and selected
causal claims. Unit tests cover those cases. A successful validation means
the output passed these checks; it does not prove every interpretation is
correct. Human review remains required before any external use.

## Operational acceptance criteria

Before considering real programme data: agree indicator definitions with
programme staff; validate data use authority and access; profile partner
source quality; reconcile a sample to source records; run a prospective
forecast test; and have a human sign off each management recommendation.
