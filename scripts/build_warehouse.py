"""Validate raw demo CSVs, build a SQLite star schema and keep an ETL audit trail.
Run from any working directory: python scripts/build_warehouse.py
"""
from __future__ import annotations
import csv
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'data'/'raw'
DB=ROOT/'data'/'warehouse'/'mercadolens.sqlite3'
REJECTS=ROOT/'data'/'warehouse'/'rejected_rows.csv'
CATEGORIES=['Frescos','Abarrotes','Bebidas','Limpieza','Cuidado personal']
CHANNELS=['Tienda física','WhatsApp','Delivery']
WEEKDAY=['Lun','Mar','Mié','Jue','Vie','Sáb','Dom']


def build_warehouse(raw_dir:Path=RAW, db_path:Path=DB, rejects_path:Path=REJECTS)->dict:
    db_path.parent.mkdir(parents=True,exist_ok=True)
    products=pd.read_csv(raw_dir/'products.csv',encoding='utf-8-sig',dtype={'sku':'string'})
    sales=pd.read_csv(raw_dir/'sales.csv',encoding='utf-8-sig',dtype={'line_id':'string','sku':'string','order_id':'string'})
    inventory=pd.read_csv(raw_dir/'inventory_snapshots.csv',encoding='utf-8-sig',dtype={'sku':'string'})
    mandatory=['line_id','order_id','sold_at','sku','quantity','unit_price','unit_cost','discount','channel','payment_method']
    if any(c not in sales.columns for c in mandatory):raise ValueError('Sales CSV is missing required headers')
    received=len(sales)
    duplicate_count=int(sales.duplicated(subset=['line_id']).sum())
    dup=sales.loc[sales.duplicated(subset=['line_id'],keep='first')].copy();dup['error']='duplicate_line_id'
    sales=sales.drop_duplicates(subset=['line_id'],keep='first').copy()
    parsed=pd.to_datetime(sales['sold_at'],format='%Y-%m-%d %H:%M:%S',errors='coerce')
    valid_skus=set(products['sku'].astype(str))
    numeric_cols=['quantity','unit_price','unit_cost','discount']
    for col in numeric_cols:sales[col]=pd.to_numeric(sales[col],errors='coerce')
    bad_sku=~sales['sku'].isin(valid_skus)
    bad_numeric=sales[numeric_cols].isna().any(axis=1) | (sales['quantity']<=0) | (sales['unit_price']<=0) | (sales['unit_cost']<0) | (sales['discount']<0) | (sales['discount']>=sales['unit_price'])
    bad_date=parsed.isna()
    bad_channel=~sales['channel'].isin(CHANNELS)
    invalid=bad_sku | bad_numeric | bad_date | bad_channel
    rejected=sales.loc[invalid].copy()
    rejected['error']=['unknown_sku' if sku else 'invalid_numbers' if num else 'invalid_timestamp' if dt else 'invalid_channel' for sku,num,dt in zip(bad_sku.loc[invalid],bad_numeric.loc[invalid],bad_date.loc[invalid])]
    rejected=pd.concat([dup,rejected],ignore_index=True)
    rejects_path.parent.mkdir(parents=True,exist_ok=True)
    rejected.to_csv(rejects_path,index=False,encoding='utf-8-sig')
    sales=sales.loc[~invalid].copy()
    sales['sold_at_dt']=parsed.loc[~invalid]
    sales['sale_date']=sales['sold_at_dt'].dt.strftime('%Y-%m-%d')
    sales['hour']=sales['sold_at_dt'].dt.hour.astype(int)
    sales['quantity']=sales['quantity'].astype(int)
    for name in ['unit_price','unit_cost','discount']:sales[name]=sales[name].astype(float)
    sales['gross_sales']=(sales['quantity']*sales['unit_price']).round(2)
    sales['net_sales']=(sales['gross_sales']-sales['quantity']*sales['discount']).round(2)
    sales['cogs']=(sales['quantity']*sales['unit_cost']).round(2)
    sales['gross_profit']=(sales['net_sales']-sales['cogs']).round(2)

    if db_path.exists():db_path.unlink()
    conn=sqlite3.connect(str(db_path))
    try:
        conn.executescript((ROOT/'sql'/'schema.sql').read_text(encoding='utf-8'))
        conn.executemany('INSERT INTO dim_category (category_id,category_name) VALUES (?,?)',[(i+1,x) for i,x in enumerate(CATEGORIES)])
        conn.executemany('INSERT INTO dim_channel (channel_id,channel_name) VALUES (?,?)',[(i+1,x) for i,x in enumerate(CHANNELS)])
        product_id={str(row.sku):i+1 for i,row in enumerate(products.itertuples())}
        category_id={category:i+1 for i,category in enumerate(CATEGORIES)}
        channel_id={channel:i+1 for i,channel in enumerate(CHANNELS)}
        conn.executemany('INSERT INTO dim_product (product_id,sku,product_name,category_id,list_price,unit_cost) VALUES (?,?,?,?,?,?)',[
            (i+1,str(r.sku),str(r.product_name),category_id[str(r.category)],float(r.unit_price),float(r.unit_cost)) for i,r in enumerate(products.itertuples())])
        all_dates=pd.date_range(sales['sale_date'].min(),sales['sale_date'].max(),freq='D')
        conn.executemany('INSERT INTO dim_date VALUES (?,?,?,?,?,?,?)',[
            (d.strftime('%Y-%m-%d'),int(d.year),int(d.month),d.strftime('%Y-%m'),int(d.dayofweek),WEEKDAY[d.dayofweek],int(d.day)) for d in all_dates])
        conn.executemany('''INSERT INTO fact_sales (line_id,order_id,sold_at,sale_date,hour,product_id,channel_id,payment_method,
              quantity,unit_price,unit_cost,discount,gross_sales,net_sales,cogs,gross_profit) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',[
                (str(r.line_id),str(r.order_id),r.sold_at_dt.strftime('%Y-%m-%d %H:%M:%S'),r.sale_date,int(r.hour),product_id[str(r.sku)],channel_id[str(r.channel)],str(r.payment_method),
                 int(r.quantity),float(r.unit_price),float(r.unit_cost),float(r.discount),float(r.gross_sales),float(r.net_sales),float(r.cogs),float(r.gross_profit)) for r in sales.itertuples()])
        inventory=inventory[inventory['sku'].isin(valid_skus)].copy()
        conn.executemany('INSERT INTO fact_inventory VALUES (?,?,?,?)',[
            (str(r.snapshot_date),product_id[str(r.sku)],int(r.stock_on_hand),int(r.reorder_point)) for r in inventory.itertuples()])
        conn.execute('INSERT INTO etl_runs (generated_at,rows_received,rows_loaded,duplicate_rows,rejected_rows,snapshot_rows,data_source) VALUES (?,?,?,?,?,?,?)',
            (datetime.now(timezone.utc).isoformat(timespec='seconds'),received,len(sales),duplicate_count,len(rejected)-duplicate_count,len(inventory),'CSV sintético · Comercial Rivera (demo)'))
        conn.commit()
        stats={'raw_rows':received,'loaded_rows':len(sales),'duplicates':duplicate_count,'rejected':len(rejected)-duplicate_count,'products':len(products),'inventory_snapshots':len(inventory),'database':str(db_path)}
        return stats
    finally:conn.close()

if __name__=='__main__':
    print('ETL completed:',build_warehouse())
