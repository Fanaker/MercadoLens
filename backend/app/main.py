"""MercadoLens: demo-first analytics API and standalone dashboard."""
from __future__ import annotations
import csv
import io
import re
import sqlite3
from pathlib import Path
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from .analytics import build_dashboard, connection

ROOT=Path(__file__).resolve().parents[2]
WEB=ROOT/'frontend'
app=FastAPI(title='MercadoLens Analytics API',version='1.0.0',description='SQL-driven retail analytics over synthetic data')

@app.get('/api/health')
def health():
    try:
        with connection() as conn:
            count=conn.execute('SELECT COUNT(*) FROM fact_sales').fetchone()[0]
        return {'status':'ok','sales_lines':count,'dataset':'synthetic'}
    except (FileNotFoundError,sqlite3.Error) as exc:
        raise HTTPException(503,str(exc)) from exc

@app.get('/api/dashboard')
def dashboard(month:str=Query('2026-10',pattern=r'^\d{4}-\d{2}$'),channel:str='all'):
    try:return build_dashboard(month,channel)
    except ValueError as exc:raise HTTPException(422,str(exc)) from exc
    except (FileNotFoundError,sqlite3.Error) as exc:raise HTTPException(503,str(exc)) from exc

EXPORTS={'sales': 'SELECT f.line_id,f.order_id,f.sold_at,p.sku,p.product_name,c.category_name AS category,ch.channel_name AS channel,f.payment_method,f.quantity,f.net_sales,f.cogs,f.gross_profit FROM fact_sales f JOIN dim_product p ON p.product_id=f.product_id JOIN dim_category c ON p.category_id=c.category_id JOIN dim_channel ch ON ch.channel_id=f.channel_id ORDER BY f.sold_at',
         'products':'SELECT p.sku,p.product_name,c.category_name AS category,p.list_price,p.unit_cost FROM dim_product p JOIN dim_category c ON p.category_id=c.category_id ORDER BY p.sku',
         'inventory':'SELECT i.snapshot_date,p.sku,p.product_name,i.stock_on_hand,i.reorder_point FROM fact_inventory i JOIN dim_product p ON p.product_id=i.product_id ORDER BY i.snapshot_date,p.sku'}

@app.get('/api/export/{dataset}')
def export_dataset(dataset:str):
    if dataset not in EXPORTS:raise HTTPException(404,'Unknown dataset')
    with connection() as conn:
        cursor=conn.execute(EXPORTS[dataset]);columns=[x[0] for x in cursor.description]
        records=cursor.fetchall()
    output=io.StringIO();writer=csv.writer(output);writer.writerow(columns)
    writer.writerows(records)
    data='\ufeff'+output.getvalue()
    return StreamingResponse(iter([data.encode('utf-8')]),media_type='text/csv; charset=utf-8',
      headers={'Content-Disposition':f'attachment; filename="mercadolens_{dataset}.csv"'})

assets_dir = WEB / 'assets'
if assets_dir.is_dir():
    app.mount('/assets', StaticFiles(directory=str(assets_dir)), name='assets')

@app.get('/')
def index():return FileResponse(WEB/'index.html')

@app.get('/{file_name}')
def web_asset(file_name:str):
    if file_name not in ('app.js','styles.css','favicon.svg'):raise HTTPException(404,'Not found')
    return FileResponse(WEB/file_name)
