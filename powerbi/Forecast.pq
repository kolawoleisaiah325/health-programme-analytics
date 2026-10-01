// Create a Power Query text parameter named DataRoot with the repository path.
let
    Source = Csv.Document(
        File.Contents(DataRoot & "\data\forecast\service_volume_forecast.csv"),
        [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]
    ),
    Headers = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),
    Types = Table.TransformColumnTypes(
        Headers,
        {
            {"period", type text},
            {"predicted_doses", Int64.Type},
            {"lower_illustrative", Int64.Type},
            {"upper_illustrative", Int64.Type},
            {"model", type text},
            {"data_label", type text}
        }
    ),
    MonthStart = Table.AddColumn(
        Types, "month_start", each Date.FromText([period] & "-01"), type date
    )
in
    MonthStart
