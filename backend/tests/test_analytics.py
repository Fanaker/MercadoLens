"""Small tests covering the commercial logic and HTTP contract."""
from pathlib import Path
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.analytics import build_dashboard,connection
from scripts.build_warehouse import build_warehouse

ROOT=Path(__file__).resolve().parents[2]
client=TestClient(app)

def test_october_metrics_match_sql():
    data=build_dashboard('2026-10','all')
    with connection() as conn:
        row=conn.execute("SELECT sum(net_sales),sum(gross_profit),count(distinct order_id) FROM fact_sales WHERE substr(sale_date,1,7)='2026-10'").fetchone()
    assert abs(data['kpis']['revenue']-row[0])<.01
    assert abs(data['kpis']['profit']-row[1])<.01
    assert data['kpis']['orders']==row[2]
    assert abs(sum(x['revenue'] for x in data['categories'])-data['kpis']['revenue'])<.05


def test_channels_partition_total():
    base=build_dashboard('2026-10','all')['kpis']['revenue']
    values=sum(build_dashboard('2026-10',channel)['kpis']['revenue'] for channel in ['Tienda física','WhatsApp','Delivery'])
    assert abs(base-values)<.02


def test_etl_deduplicates_and_validates(tmp_path):
    db=tmp_path/'warehouse.sqlite3'
    result=build_warehouse(ROOT/'data/raw',db,tmp_path/'rejects.csv')
    assert result['loaded_rows']>3000
    assert result['duplicates']==12
    assert result['rejected']==13
    with connection(db) as conn:
        assert conn.execute('PRAGMA foreign_key_check').fetchall()==[]
        assert conn.execute('select count(*) from fact_sales').fetchone()[0]==result['loaded_rows']


def test_api_dashboard_validates_input():
    ok=client.get('/api/dashboard',params={'month':'2026-10','channel':'WhatsApp'})
    assert ok.status_code==200
    assert ok.json()['meta']['channel']=='WhatsApp'
    assert client.get('/api/dashboard',params={'month':'2026-12'}).status_code==422
    assert client.get('/api/dashboard',params={'month':'2026-10','channel':'unknown'}).status_code==422


def test_csv_export_and_health():
    assert client.get('/api/health').json()['status']=='ok'
    resp=client.get('/api/export/sales')
    assert resp.status_code==200 and 'text/csv' in resp.headers['content-type']
    assert 'line_id' in resp.text and 'sku' in resp.text
    assert client.get('/api/export/unknown').status_code==404


def test_frontend_served():
    html=client.get('/')
    assert html.status_code==200 and 'MercadoLens' in html.text
    assert client.get('/app.js').status_code==200
    assert client.get('/styles.css').status_code==200
