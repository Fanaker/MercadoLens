-- MercadoLens · Sample analytics queries on the star schema.
-- Run in SQLiteStudio or with: sqlite3 data/warehouse/mercadolens.sqlite3 < sql/analytics_queries.sql

-- Monthly revenue, cost, gross profit and orders
SELECT substr(sale_date, 1, 7) AS month,
       ROUND(SUM(net_sales), 2) AS net_revenue,
       ROUND(SUM(cogs), 2) AS cost_of_goods,
       ROUND(SUM(gross_profit), 2) AS gross_profit,
       ROUND(100.0 * SUM(gross_profit) / NULLIF(SUM(net_sales),0),1) AS gross_margin_pct,
       COUNT(DISTINCT order_id) AS orders
FROM fact_sales GROUP BY month ORDER BY month;

-- Top products during October 2026
SELECT p.sku, p.product_name, c.category_name,
       ROUND(SUM(f.net_sales),2) AS revenue, SUM(f.quantity) AS units,
       ROUND(SUM(f.gross_profit),2) AS gross_profit
FROM fact_sales f
JOIN dim_product p ON f.product_id=p.product_id
JOIN dim_category c ON p.category_id=c.category_id
WHERE f.sale_date>='2026-10-01' AND f.sale_date<'2026-11-01'
GROUP BY p.product_id ORDER BY revenue DESC LIMIT 10;

-- Stock under reorder threshold, most recent snapshot
SELECT p.sku, p.product_name, i.stock_on_hand, i.reorder_point
FROM fact_inventory i JOIN dim_product p ON i.product_id=p.product_id
WHERE i.snapshot_date=(SELECT MAX(snapshot_date) FROM fact_inventory)
  AND i.stock_on_hand<=i.reorder_point
ORDER BY (i.stock_on_hand-i.reorder_point), i.stock_on_hand;

-- Sales heatmap by day of week (Monday=0) and hour
SELECT (CAST(strftime('%w',sale_date) AS INTEGER)+6)%7 AS weekday,
       hour, ROUND(SUM(net_sales),2) AS revenue
FROM fact_sales
WHERE sale_date>='2026-10-01' AND sale_date<'2026-11-01'
GROUP BY weekday,hour ORDER BY weekday,hour;
