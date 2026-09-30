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

Project scope documented. Implementation and evaluation have not started.

## Planned tools

Python, pandas, PostgreSQL, SQL, Power BI, and Git.
