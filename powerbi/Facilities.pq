// Create a Power Query text parameter named DataRoot with the repository path.
let
    Source = Csv.Document(
        File.Contents(DataRoot & "\data\synthetic\facilities.csv"),
        [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]
    ),
    Headers = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),
    Types = Table.TransformColumnTypes(
        Headers,
        {
            {"facility_id", type text},
            {"facility_name", type text},
            {"area", type text},
            {"facility_type", type text}
        }
    )
in
    Types
