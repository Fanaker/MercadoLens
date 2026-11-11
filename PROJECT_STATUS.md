# Estado de entrega — MercadoLens v1.0.0

**Estado:** entregable autónomo para GitHub. Sin hosting ni cuentas externas.

## Entregado

- Generador reproducible de ventas, productos e inventario sintéticos (mayo–octubre 2026).
- ETL de Pandas con esquema SQL relacional, eliminación de duplicados y archivo de rechazo.
- Almacén SQLite precargado con modelo estrella y métricas calculadas por SQL.
- FastAPI para dashboard interactivo, filtros y exportación CSV.
- Frontend responsive con 7 secciones y navegación en español.
- Siete capturas renderizadas desde la interfaz con cifras reales del almacén sintético.
- Tablas CSV para Power BI, relaciones explicadas, DAX y plantilla Power Query M.
- README, arquitectura, diccionario de datos, SQL y GitHub Actions.

## Verificado en el entorno de creación

- `python scripts/generate_demo_data.py` — completó la generación.
- `python scripts/build_warehouse.py` — cargó 3.852 líneas válidas, detectó 12 duplicados y 13 filas inválidas.
- `python scripts/export_powerbi.py` — exportó las seis tablas.
- `python -m pytest backend/tests -q` — 6 pruebas superadas.
- `node --check frontend/app.js` — sintaxis correcta.
- Navegador Chromium (renderizado sin errores JavaScript), 7 capturas generadas.
- API HTTP `/api/health` respondió correctamente con SQLite.

## Alcance que no debe exagerarse

- No se generó archivo `.pbix`; se entregan recursos listos para armar un informe en Power BI.
- Las capturas pertenecen a la web propia, no a Power BI Desktop.
- El backend se ha comprobado localmente en el entorno de creación, no en todos los equipos Windows.
- No hay datasets reales, login, infraestructura cloud ni despliegue público.
- El dashboard utiliza JavaScript estándar, no React, ni TypeScript.
