# Adding real data without changing its meaning

Recommendation: add Nigeria annual immunisation coverage as the first real-data
page. Keep the fictional facility pipeline as a clearly labelled engineering
demonstration with reproducible quality cases. This is a proposed next phase;
no real dataset has been ingested by the current dashboard.

## Verified starting sources

- [WHO/UNICEF Estimates of National Immunization Coverage (WUENIC)](https://www.who.int/teams/immunization-vaccines-and-biologicals/immunization-analysis-and-insights/global-monitoring/immunization-coverage/who-unicef-estimates-of-national-immunization-coverage)
  provide estimated coverage by country, year and vaccine. WHO describes the
  inputs as country-reported data and survey data.
- [UNICEF immunisation country products](https://data.unicef.org/resources/immunization-country-profiles/)
  include a Nigeria package with datasets, profiles and interpretation materials.
- [WHO Immunization Data Portal](https://immunizationdata.who.int/)
  supports exploration and downloads of immunisation data. Choose the dataset
  and revision explicitly before building an importer.

Sources reviewed on 1 October 2026. Verify the release and reuse conditions of
the exact download when implementing; this document is not a licence grant.

## Smallest useful real-data feature

1. Download an official coverage dataset and its metadata. Preserve the raw
   file, source URL, release date, retrieval time and checksum. Record the
   data's reuse/attribution conditions before committing it publicly.
2. Select Nigeria and a small set of vaccine indicators, initially DTP1, DTP3
   and MCV1 where available. Model one record per country, year, vaccine and
   estimate revision. Keep units and source/estimate type explicit.
3. Validate unique keys, year ranges, valid vaccine identifiers, missingness
   and percentage bounds for these estimates. Investigate unexpected values
   rather than clipping them silently. Never replace a missing year with zero.
4. Add a separate, visibly labelled public-data page with annual trends,
   percentage-point changes, a DTP1–DTP3 coverage gap and source footnotes.
   A gap between annual estimates is descriptive; it does not track individual
   children through a vaccination series.
5. Reconcile selected values against the official country profile before
   publishing. Explain revisions and the uncertainty of estimates in the brief.

Annual national coverage can demonstrate real-data ingestion, validation,
visualisation and interpretation. It does not establish monthly facility dose
counts, facility targets, report completeness or commodity demand. Do not expand
annual percentages into invented monthly records or join them onto the fictional
facilities as if they were observed facility results.

## Later operational forecasting phase

To forecast real monthly service volume, obtain an authorised, suitably
aggregated HMIS/RHIS or programme export with stable facility IDs, monthly counts,
reporting status and enough historical periods. Check what may be shared before
using it in a public repository. Preserve the distinction between delivered
doses, coverage and demand; rerun temporal validation with the new data.

Interview framing: the synthetic pipeline demonstrates controlled quality and
failure cases, while the public-data page demonstrates source scrutiny and
honest interpretation at the data's actual geographic and time resolution.
