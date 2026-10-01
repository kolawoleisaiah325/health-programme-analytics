# Concept note: trusted programme performance data

**Problem:** Programme managers receive facility reports, targets, and partner
spreadsheets with inconsistent identifiers and late corrections. A simple
dashboard can display incorrect totals if it treats missing reports as zero
or adds resubmissions together.

**Proposed solution:** Standardise partner inputs, retain every source
submission, validate business rules, and publish one approved facility-month
record. Load approved data into a PostgreSQL warehouse. Provide managers
with a reporting-quality view, a facility follow-up list, a separately
evaluated service-volume forecast, and a cited draft narrative that requires
human approval.

**Prototype scope:** One immunisation programme, one target definition,
facility-month aggregates, and a small number of partner sources. The
repository demonstrates the workflow with synthetic data. It does not
ingest real RHIS/HMIS data or make clinical recommendations.

**Delivery gates:** (1) agree indicators and source ownership; (2) reconcile
sample source records and corrections; (3) run data-quality checks; (4)
review dashboard metrics with programme users; (5) evaluate models on a
future time period; (6) review privacy, access, and AI output controls;
(7) approve an operating plan and named technical owners.

**Indicative team:** a data engineer for integration and warehouse design, a
data scientist for analysis and forecast evaluation, a programme lead for
indicator and decision review, and a privacy/security reviewer for real
data access. A manager would set acceptance criteria, review code and
findings, resolve partner definition conflicts, and present implications to
stakeholders. Effort and cost require discovery of source systems, update
frequency, and hosting requirements; the prototype cannot justify a budget
estimate on its own.

**Success measures for a real pilot:** independently verified reporting
completeness, fewer unresolved data-quality issues, reproducible metric
definitions, documented decision use, and prospective forecast performance
against a pre-agreed baseline. Any claimed programme impact would need a
separate evaluation design.
