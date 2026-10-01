// Create a Power Query text parameter named DataRoot with the repository path.
let
    Source = Csv.Document(
        File.Contents(DataRoot & "\data\processed\facility_month_status.csv"),
        [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]
    ),
    Headers = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),
    Types = Table.TransformColumnTypes(
        Headers,
        {
            {"facility_id", type text},
            {"facility_name", type text},
            {"area", type text},
            {"period", type text},
            {"target_doses", Int64.Type},
            {"reporting_status", type text},
            {"submission_count", Int64.Type},
            {"selected_report_id", type text},
            {"accepted_doses", Int64.Type},
            {"variance_doses", Int64.Type}
        }
    ),
    MonthStart = Table.AddColumn(
        Types, "month_start", each Date.FromText([period] & "-01"), type date
    )
in
    MonthStart
