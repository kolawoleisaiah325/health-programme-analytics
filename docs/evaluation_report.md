# Evaluation report

All results below come from **synthetic demonstration data**. They do not
measure a real programme or predict actual Nigerian service delivery.

## Data quality

The source has 6 fictional facilities and 36 months, giving 216 expected
facility-months. There are 216 submitted report rows, but submissions are
not the same as covered facility-months: two months have no submission,
one has a resubmission, and one row uses an unknown facility code.

The pipeline finds 214 facility-months with at least one submission
(99.1% reporting completeness), 213 with an accepted count, two missing,
and one with only an invalid negative count. The submission audit retains
213 accepted rows, two rejected rows, and one superseded row. F001 in July
2025 is a submitted, valid zero, proving that null and zero remain distinct.

These counts were checked with integration tests against the versioned
synthetic files. The pipeline also rejects duplicate facility-month targets
before writing outputs. Future partner datasets would need additional
checks for schema changes, unit mismatches, late reporting, and conflicting
facility identifiers.

## Forecast design and result

The target is monthly **doses delivered**, an operational service-volume
measure. Models train on January 2023–December 2024. They forecast all of
2025 without training on it. Only the nine 2025 months with complete accepted
reports are scored; February, April, and June are excluded because a missing
or invalid facility report would depress the observed total.

| Method | Holdout MAE, doses | Holdout WAPE |
| --- | ---: | ---: |
| Seasonal naïve | 31.78 | 4.19% |
| Ridge trend and seasonality | 33.89 | 4.47% |
| Holt-Winters | 27.38 | 3.61% |

Holt-Winters has the lowest observed MAE in this small synthetic holdout.
After model selection, the final fit fills three incomplete facility-months
from the same facility's prior-year month. The illustrative error band uses
the empirical 80th percentile of absolute holdout errors, approximately
32.63 doses. It is **not** a calibrated 80% prediction interval.

The same holdout selected and evaluated the model; its error estimate may
be optimistic. Only nine complete months were available. A future rollout
would reserve a later independent period, test stability across facilities,
and compare decisions under realistic stock and supply constraints. Recorded
doses can understate demand during stockouts, so no procurement benefit is
claimed from this forecast.

## Reporting assistant

The local Ollama model drafts short qualitative statements using a limited
evidence pack. The program adds verified numbers and citations. It rejects
unknown citations, model-authored numbers, malformed outputs, and selected
causal claims. Unit tests cover those cases. A successful validation means
the output passed these checks; it does not prove every interpretation is
correct. Human review remains required before any external use.

## Operational acceptance criteria

Before considering real programme data: agree indicator definitions with
programme staff; validate data use authority and access; profile partner
source quality; reconcile a sample to source records; run a prospective
forecast test; and have a human sign off each management recommendation.
