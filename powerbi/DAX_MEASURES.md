# MercadoLens · Medidas DAX para Power BI

Medidas listas para copiar al **modelo estrella importado** desde `data/powerbi/`. Los nombres de las tablas corresponden exactamente a los CSV exportados. Crea una tabla de medidas opcional y agrega estas medidas individualmente.

```dax
Ingresos Netos = SUM(fact_sales[net_sales])

Ventas Brutas = SUM(fact_sales[gross_sales])

Costo de Ventas = SUM(fact_sales[cogs])

Utilidad Bruta = [Ingresos Netos] - [Costo de Ventas]

Margen Bruto % = DIVIDE([Utilidad Bruta], [Ingresos Netos], 0)

Unidades Vendidas = SUM(fact_sales[quantity])

Pedidos = DISTINCTCOUNT(fact_sales[order_id])

Ticket Promedio = DIVIDE([Ingresos Netos], [Pedidos], 0)

Ingreso Mes Anterior =
    CALCULATE([Ingresos Netos], DATEADD(dim_date[sale_date], -1, MONTH))

Crecimiento Mensual % =
    DIVIDE([Ingresos Netos] - [Ingreso Mes Anterior], [Ingreso Mes Anterior], 0)

Participación Categoría % =
    DIVIDE([Ingresos Netos], CALCULATE([Ingresos Netos], ALL(dim_category[category_name])), 0)

Productos Vendidos = DISTINCTCOUNT(fact_sales[product_id])
```

> **Importante:** asigna tipo de datos **Fecha** a `dim_date[sale_date]` y `fact_sales[sale_date]` antes de usar `DATEADD`. Marca `dim_date` como tabla de fechas. En Power BI, utiliza visualizaciones para gráficos; el dashboard web incluido es una implementación distinta, no una captura de Power BI.

## Visualizaciones sugeridas

| Página | Visual | Campos |
|---|---|---|
| Resumen | Tarjetas | Ingresos Netos, Utilidad Bruta, Margen Bruto %, Ticket Promedio |
| Resumen | Línea | dim_date[sale_date], Ingresos Netos, Utilidad Bruta |
| Categorías | Barras | dim_category[category_name], Ingresos Netos |
| Productos | Tabla | dim_product[product_name], Unidades Vendidas, Utilidad Bruta |
| Horarios | Matriz | dim_date[weekday_label], fact_sales[hour], Ingresos Netos |

> Para analizar inventario usa la instantánea más reciente dentro del período; **no sumes `stock_on_hand` entre fechas**, pues generaría doble conteo.
