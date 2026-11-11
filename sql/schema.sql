PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS dim_category (
  category_id INTEGER PRIMARY KEY, category_name TEXT UNIQUE NOT NULL
);
CREATE TABLE IF NOT EXISTS dim_product (
  product_id INTEGER PRIMARY KEY, sku TEXT UNIQUE NOT NULL,
  product_name TEXT NOT NULL, category_id INTEGER NOT NULL REFERENCES dim_category(category_id),
  list_price REAL NOT NULL, unit_cost REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS dim_channel (
  channel_id INTEGER PRIMARY KEY, channel_name TEXT UNIQUE NOT NULL
);
CREATE TABLE IF NOT EXISTS dim_date (
  sale_date TEXT PRIMARY KEY, year INTEGER NOT NULL, month INTEGER NOT NULL,
  month_key TEXT NOT NULL, day_of_week INTEGER NOT NULL, weekday_label TEXT NOT NULL,
  day_of_month INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS fact_sales (
  line_id TEXT PRIMARY KEY, order_id TEXT NOT NULL, sold_at TEXT NOT NULL,
  sale_date TEXT NOT NULL REFERENCES dim_date(sale_date), hour INTEGER NOT NULL,
  product_id INTEGER NOT NULL REFERENCES dim_product(product_id),
  channel_id INTEGER NOT NULL REFERENCES dim_channel(channel_id),
  payment_method TEXT NOT NULL,
  quantity INTEGER NOT NULL CHECK(quantity>0), unit_price REAL NOT NULL,
  unit_cost REAL NOT NULL, discount REAL NOT NULL,
  gross_sales REAL NOT NULL, net_sales REAL NOT NULL, cogs REAL NOT NULL,
  gross_profit REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS fact_inventory (
  snapshot_date TEXT NOT NULL, product_id INTEGER NOT NULL REFERENCES dim_product(product_id),
  stock_on_hand INTEGER NOT NULL, reorder_point INTEGER NOT NULL,
  PRIMARY KEY(snapshot_date, product_id)
);
CREATE TABLE IF NOT EXISTS etl_runs (
  run_id INTEGER PRIMARY KEY, generated_at TEXT NOT NULL,
  rows_received INTEGER NOT NULL, rows_loaded INTEGER NOT NULL,
  duplicate_rows INTEGER NOT NULL, rejected_rows INTEGER NOT NULL,
  snapshot_rows INTEGER NOT NULL, data_source TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_sales_date ON fact_sales(sale_date);
CREATE INDEX IF NOT EXISTS idx_sales_product ON fact_sales(product_id);
CREATE INDEX IF NOT EXISTS idx_sales_channel ON fact_sales(channel_id);
CREATE INDEX IF NOT EXISTS idx_inventory_date ON fact_inventory(snapshot_date);
