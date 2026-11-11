"""Business metrics. All aggregates are calculated with SQL over the star schema."""
from __future__ import annotations
import sqlite3
from pathlib import Path
from datetime import datetime

ROOT=Path(__file__).resolve().parents[2]
DB=ROOT/'data'/'warehouse'/'mercadolens.sqlite3'
MONTH_NAMES=['','enero','febrero','marzo','abril','mayo','junio','julio','agosto','septiembre','octubre','noviembre','diciembre']
DAY_NAMES=['Lun','Mar','Mié','Jue','Vie','Sáb','Dom']


def connection(db_path:Path=DB):
    if not db_path.is_file():raise FileNotFoundError('Warehouse missing. Run python scripts/generate_demo_data.py && python scripts/build_warehouse.py')
    conn=sqlite3.connect(db_path)
    conn.row_factory=sqlite3.Row
    return conn


def rows(conn, sql:str, params:tuple=()):
    return [dict(r) for r in conn.execute(sql,params).fetchall()]


def one(conn,sql:str,params:tuple=()):
    return dict(conn.execute(sql,params).fetchone())


def round_values(row:dict):
    for k,v in row.items():
        if isinstance(v,float):row[k]=round(v,2)
    return row


def stats(conn,month,channel):
    return round_values(one(conn,"""SELECT COALESCE(SUM(f.net_sales),0) AS revenue,
    COALESCE(SUM(f.gross_profit),0) AS profit,
    COALESCE(SUM(f.cogs),0) AS cost,
    COALESCE(SUM(f.quantity),0) AS units,
    COUNT(DISTINCT f.order_id) AS orders,
    COUNT(*) AS lines,
    ROUND(100.*COALESCE(SUM(f.gross_profit),0)/NULLIF(SUM(f.net_sales),0),1) AS margin
    FROM fact_sales f JOIN dim_channel ch ON f.channel_id=ch.channel_id
    WHERE substr(f.sale_date,1,7)=? AND (?='all' OR ch.channel_name=?)""",(month,channel,channel)))


def build_dashboard(month='2026-10', channel='all', db_path:Path=DB):
    with connection(db_path) as conn:
        months=[r['month_key'] for r in rows(conn,'SELECT DISTINCT month_key FROM dim_date ORDER BY month_key')]
        if month not in months:raise ValueError(f'Unavailable month: {month}')
        if channel not in ['all','Tienda física','WhatsApp','Delivery']:raise ValueError('Unknown sales channel')
        idx=months.index(month)
        previous=months[idx-1] if idx else None
        current=stats(conn,month,channel)
        prev=stats(conn,previous,channel) if previous else None
        pct_change=(current['revenue']-prev['revenue'])/prev['revenue']*100 if prev and prev['revenue'] else 0
        current['ticket']=round(current['revenue']/current['orders'],2) if current['orders'] else 0
        current['margin']=current['margin'] or 0
        current['revenue_change']=round(pct_change,1)
        current['orders_change']=round((current['orders']-prev['orders'])/prev['orders']*100,1) if prev and prev['orders'] else 0
        current['ticket_change']=round((current['ticket']-prev['revenue']/prev['orders'])/(prev['revenue']/prev['orders'])*100,1) if prev and prev['orders'] else 0
        current['margin_change']=round(current['margin']-(prev['margin'] or 0),1) if prev else 0
        params=(month,channel,channel)
        daily=rows(conn,"""SELECT f.sale_date AS date, round(SUM(f.net_sales),2) AS revenue,
         round(SUM(f.gross_profit),2) AS profit, count(DISTINCT f.order_id) AS orders
         FROM fact_sales f JOIN dim_channel ch ON f.channel_id=ch.channel_id
         WHERE substr(f.sale_date,1,7)=? AND (?='all' OR ch.channel_name=?) GROUP BY f.sale_date ORDER BY f.sale_date""",params)
        cats=rows(conn,"""SELECT cat.category_name AS name,
         round(sum(f.net_sales),2) AS revenue, round(sum(f.gross_profit),2) AS profit,
         sum(f.quantity) AS units, count(DISTINCT f.order_id) AS orders,
         round(100.*sum(f.gross_profit)/nullif(sum(f.net_sales),0),1) AS margin
         FROM fact_sales f JOIN dim_product p ON f.product_id=p.product_id
         JOIN dim_category cat ON p.category_id=cat.category_id
         JOIN dim_channel ch ON f.channel_id=ch.channel_id
         WHERE substr(f.sale_date,1,7)=? AND (?='all' OR ch.channel_name=?)
         GROUP BY cat.category_id ORDER BY revenue DESC""",params)
        for c in cats:c['share']=round(100*c['revenue']/current['revenue'],1) if current['revenue'] else 0
        products=rows(conn,"""SELECT p.sku AS sku,p.product_name AS name,cat.category_name AS category,
          round(sum(f.net_sales),2) AS revenue, round(sum(f.gross_profit),2) AS profit,
          sum(f.quantity) AS units, count(DISTINCT f.order_id) AS orders,
          round(100.*sum(f.gross_profit)/nullif(sum(f.net_sales),0),1) AS margin
          FROM fact_sales f JOIN dim_product p ON f.product_id=p.product_id
          JOIN dim_category cat ON p.category_id=cat.category_id
          JOIN dim_channel ch ON f.channel_id=ch.channel_id
          WHERE substr(f.sale_date,1,7)=? AND (?='all' OR ch.channel_name=?)
          GROUP BY p.product_id ORDER BY revenue DESC""",params)
        # Inventory is independent of sales channel. Use last available snapshot up to selected month.
        month_end=month+'-31'
        inventory=rows(conn,"""SELECT p.sku,p.product_name AS name,cat.category_name AS category,
         inv.stock_on_hand AS stock,inv.reorder_point AS reorder_point,inv.snapshot_date,
         CASE WHEN inv.stock_on_hand<=inv.reorder_point THEN 'low' ELSE 'ok' END AS status
         FROM fact_inventory inv JOIN dim_product p ON p.product_id=inv.product_id
         JOIN dim_category cat ON cat.category_id=p.category_id
         WHERE inv.snapshot_date=(SELECT max(snapshot_date) FROM fact_inventory WHERE snapshot_date<=?)
         ORDER BY (inv.stock_on_hand-inv.reorder_point),inv.stock_on_hand""",(month_end,))
        inv_map={i['sku']:i for i in inventory}
        for p in products:
            inv=inv_map.get(p['sku'],{})
            p['stock']=inv.get('stock',0);p['reorder_point']=inv.get('reorder_point',0)
            p['stock_status']=inv.get('status','ok')
        hours=rows(conn,"""SELECT CAST(strftime('%w',f.sale_date) AS INTEGER) AS sqlite_weekday,
          f.hour AS hour,round(sum(f.net_sales),2) AS revenue,count(DISTINCT f.order_id) AS orders
          FROM fact_sales f JOIN dim_channel ch ON f.channel_id=ch.channel_id
          WHERE substr(f.sale_date,1,7)=? AND (?='all' OR ch.channel_name=?)
          GROUP BY sqlite_weekday,f.hour ORDER BY sqlite_weekday,f.hour""",params)
        for h in hours:h['day']=(h.pop('sqlite_weekday')+6)%7
        monthly=rows(conn,"""SELECT substr(f.sale_date,1,7) AS month,
         round(sum(f.net_sales),2) AS revenue,round(sum(f.gross_profit),2) AS profit,
         count(DISTINCT f.order_id) AS orders
         FROM fact_sales f JOIN dim_channel ch ON f.channel_id=ch.channel_id
         WHERE (?='all' OR ch.channel_name=?)
         GROUP BY substr(f.sale_date,1,7) ORDER BY month""",(channel,channel))
        channels=rows(conn,"""SELECT ch.channel_name AS name,round(sum(f.net_sales),2) AS revenue,
         count(DISTINCT f.order_id) AS orders
         FROM fact_sales f JOIN dim_channel ch ON f.channel_id=ch.channel_id
         WHERE substr(f.sale_date,1,7)=? GROUP BY ch.channel_id ORDER BY revenue DESC""",(month,))
        payments=rows(conn,"""SELECT f.payment_method AS name, round(sum(f.net_sales),2) AS revenue
         FROM fact_sales f JOIN dim_channel ch ON f.channel_id=ch.channel_id
         WHERE substr(f.sale_date,1,7)=? AND (?='all' OR ch.channel_name=?)
         GROUP BY f.payment_method ORDER BY revenue DESC""",params)
        etl=one(conn,'SELECT * FROM etl_runs ORDER BY run_id DESC LIMIT 1')
        low=[r for r in inventory if r['status']=='low']
        topcat=max(cats,key=lambda c:c['revenue']) if cats else None
        best_margin=max(cats,key=lambda c:c['margin']) if cats else None
        busiest=max(hours,key=lambda h:h['revenue']) if hours else None
        # Deterministic suggestions calculated from real aggregations of the synthetic records.
        insights=[]
        if topcat:insights.append(dict(type='growth',tag='VENTAS',title=f"{topcat['name']} impulsa el negocio",description=f"Aporta el {topcat['share']:.1f}% de los ingresos del mes. Conviene priorizar su disponibilidad y exhibición.",metric=f"{topcat['share']:.1f}%",action='Revisar categorías'))
        if low:insights.append(dict(type='alert',tag='INVENTARIO',title=f"{len(low)} productos requieren reposición",description=f"{low[0]['name']} registra {low[0]['stock']} unidades frente a un mínimo de {low[0]['reorder_point']}.",metric=f"{len(low):02d}",action='Ver productos'))
        if best_margin:insights.append(dict(type='profit',tag='RENTABILIDAD',title=f"Mejor margen: {best_margin['name']}",description=f"Esta categoría tiene un margen bruto del {best_margin['margin']:.1f}%. Puedes estudiar oportunidades de venta cruzada.",metric=f"{best_margin['margin']:.1f}%",action='Ver rentabilidad'))
        if busiest:insights.append(dict(type='time',tag='OPERACIONES',title=f"Pico de demanda: {DAY_NAMES[busiest['day']]} {busiest['hour']:02d}:00",description='Concentra uno de los intervalos con mayor facturación del periodo. Ajusta la cobertura operativa.',metric=f"{busiest['hour']:02d}:00",action='Ver horarios'))
        return {
            'meta':{'month':month,'month_label':f"{MONTH_NAMES[int(month[5:])].capitalize()} {month[:4]}",
                    'channel':channel,'months':months,'latest_month':months[-1],
                    'demo':True,'store':'Comercial Rivera','currency':'PEN','etl_at':etl['generated_at'], 'date_count':one(conn,'SELECT COUNT(*) AS n FROM dim_date')['n']},
            'kpis':current,'previous':prev,'daily':daily,'categories':cats,'products':products,
            'inventory':inventory,'hours':hours,'monthly':monthly,'channels':channels,'payments':payments,
            'insights':insights,'quality':etl,'low_stock_count':len(low)
        }
