// Plantilla orientativa de Power Query M: hecho fact_sales.
// Sustituye la ruta en File.Contents por la de tu equipo.
let
    Source = Csv.Document(
        File.Contents("C:\\ruta\\a\\MercadoLens\\data\\powerbi\\fact_sales.csv"),
        [Delimiter=",", Columns=16, Encoding=65001, QuoteStyle=QuoteStyle.Csv]
    ),
    Headers = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    Types = Table.TransformColumnTypes(Headers, {
        {"line_id", type text}, {"order_id", type text}, {"sold_at", type datetime},
        {"sale_date", type date}, {"hour", Int64.Type},
        {"product_id", Int64.Type}, {"channel_id", Int64.Type},
        {"payment_method", type text}, {"quantity", Int64.Type},
        {"unit_price", type number}, {"unit_cost", type number},
        {"discount", type number}, {"gross_sales", type number},
        {"net_sales", type number}, {"cogs", type number},
        {"gross_profit", type number}
    }, "en-US")
in
    Types
