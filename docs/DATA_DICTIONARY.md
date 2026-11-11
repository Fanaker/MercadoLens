# Diccionario de datos

## Fuentes de entrada (`data/raw/`)

| Archivo | Campos principales | Significado |
|---|---|---|
| `products.csv` | `sku`, `product_name`, `category`, `unit_price`, `unit_cost`, `initial_stock` | Catálogo y precio/costo de referencia |
| `sales.csv` | `line_id`, `order_id`, `sold_at`, `sku`, `quantity`, `unit_price`, `unit_cost`, `discount`, `channel`, `payment_method` | Ventas a nivel de ítem, con fecha y hora |
| `inventory_snapshots.csv` | `snapshot_date`, `sku`, `stock_on_hand`, `reorder_point` | Fotos semanales de inventario |

## Tablas de destino (`data/warehouse/mercadolens.sqlite3`)

| Tabla | Granularidad | Llave |
|---|---|---|
| `dim_category` | Una fila por categoría | `category_id` |
| `dim_product` | Una fila por producto | `product_id` (único `sku`) |
| `dim_channel` | Una fila por canal | `channel_id` |
| `dim_date` | Una fila por fecha | `sale_date` (`YYYY-MM-DD`) |
| `fact_sales` | Una fila por línea de pedido | `line_id` |
| `fact_inventory` | Una fila por producto e instantánea | (`snapshot_date`,`product_id`) |
| `etl_runs` | Una fila por ejecución ETL | `run_id` |

Campos cuantitativos en `fact_sales`: `quantity` (entero), `gross_sales`, `net_sales`, `cogs`, `gross_profit` (PEN), `unit_price`, `unit_cost`, `discount`. Los indicadores se calculan desde los campos de hechos, nunca de números fijos en el frontend.

**Registros de calidad:** `rejected_rows.csv` incluye filas con identificadores duplicados, SKU desconocidos y cantidades inválidas creados expresamente para demostrar validaciones.

**Datos ficticios:** Comercial Rivera, productos, ventas y existencias son sintéticos y reproducibles por semilla. No contienen datos personales ni bancarios.
