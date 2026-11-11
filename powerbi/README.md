# Guía de Power BI · MercadoLens

## Qué incluye esta integración

Este repositorio proporciona **una fuente analítica reproducible**, seis CSV con modelo estrella, medidas DAX documentadas y una consulta Power Query M de ejemplo. **No incluye un `.pbix` ni se afirma que haya sido construido o publicado un informe en Power BI Desktop.** La interfaz mostrada en las capturas es una app web propia.

1. Si modificas los datos, ejecuta `python scripts/build_warehouse.py` y `python scripts/export_powerbi.py` desde la raíz.
2. Abre Power BI Desktop → **Obtener datos → Texto/CSV** e importa los seis archivos de `data/powerbi/` (codificación UTF-8).
3. Revisa la tipificación numérica, fechas y claves enteras en Power Query.
4. En la vista de modelo, crea relaciones **1 a muchos** y filtrado en una sola dirección:

| Tabla (1) | Columna clave | Tabla (*) | Clave foránea |
|---|---|---|---|
| `dim_date` | `sale_date` | `fact_sales` | `sale_date` |
| `dim_product` | `product_id` | `fact_sales` | `product_id` |
| `dim_product` | `product_id` | `fact_inventory` | `product_id` |
| `dim_channel` | `channel_id` | `fact_sales` | `channel_id` |
| `dim_category` | `category_id` | `dim_product` | `category_id` |

5. Marca `dim_date` como tabla de fechas. Las fechas CSV se almacenan como `YYYY-MM-DD`.
6. Copia las medidas desde [DAX_MEASURES.md](DAX_MEASURES.md); para porcentajes usa el formato `0.0%` y para ingresos `S/ #,##0`.
7. Usa un filtro por `dim_date[month_key]` y opcionalmente `dim_channel[channel_name]`.

### Verificación de resultados

Con todos los canales y **octubre de 2026** deben aparecer aproximadamente `S/ 13,591.70` en ingresos netos y `S/ 3,991.30` en utilidad bruta, utilizando el dataset incluido. Los importes pueden variar si regeneras o reemplazas los CSV.

> Los CSV están poblados con datos sintéticos, sin información real de comercios ni clientes. Las medidas DAX son plantillas preparadas, no un informe `.pbix` verificado en Power BI Desktop.
