# Power BI build kit

The repository includes a working Streamlit dashboard for immediate review.
Power BI Desktop is not installed on the development computer, so these Power
Query and DAX definitions have not been opened or verified in Power BI Desktop.
No `.pbix` or `.pbip` file is claimed.

In Power BI Desktop, create a text parameter called `DataRoot` set to the
absolute path of this repository, without a trailing slash. Create three
blank queries named `FacilityMonth`, `Facilities`, and `Forecast`. Paste the
corresponding `.pq` contents into each query's Advanced Editor. Apply changes.

In Model view, relate `Facilities[facility_id]` (one) to
`FacilityMonth[facility_id]` (many), with single-direction filtering. Keep
`Forecast` disconnected: its national totals must not respond to an area
slicer. Hide duplicate facility name and area columns in `FacilityMonth`.

Create the measures in `measures.dax` one at a time. Format Reporting
Completeness and Target Attainment as percentages with one decimal. Add an
area slicer from `Facilities`, a month slicer from `FacilityMonth`, four KPI
cards, a monthly delivered-versus-target line chart, a reporting-status bar
chart, and a facility follow-up table. Put the forecast on a separate page
with its synthetic-data caveat.

The target measure deliberately sums targets only where reports were accepted.
For an unreported facility-month, the delivered value is unknown, so it is not
valid to interpret a missing row as zero performance. The Streamlit dashboard
uses these same definitions; its page and key displayed metrics are tested.

Power Query functions and DAX measures follow Microsoft's documentation:

- https://learn.microsoft.com/en-us/powerquery-m/csv-document
- https://learn.microsoft.com/en-us/powerquery-m/file-contents
- https://learn.microsoft.com/dax/calculate-function-dax
- https://learn.microsoft.com/en-us/power-query/connectors/postgresql

The `.pq` queries can also be used in Excel Power Query; load the resulting
tables into Power Pivot for equivalent measures and pivots.
