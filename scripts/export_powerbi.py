"""Export warehouse star-schema tables to UTF-8 CSV for Power BI Desktop."""
from pathlib import Path
import sqlite3
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
DATABASE=ROOT/'data/warehouse/mercadolens.sqlite3'
TARGET=ROOT/'data/powerbi'
TABLES=['dim_date','dim_category','dim_product','dim_channel','fact_sales','fact_inventory']

def export(db_path:Path=DATABASE, target:Path=TARGET):
    target.mkdir(parents=True,exist_ok=True)
    if not db_path.exists():raise FileNotFoundError('Warehouse not found: run scripts/build_warehouse.py first')
    with sqlite3.connect(db_path) as conn:
        for table in TABLES:
            frame=pd.read_sql_query(f'SELECT * FROM {table}',conn)
            frame.to_csv(target/f'{table}.csv',index=False,encoding='utf-8-sig')
            print(f'Exported {table}: {len(frame)} rows')

if __name__=='__main__':export()
