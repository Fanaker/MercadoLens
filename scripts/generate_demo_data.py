"""Create deterministic, clearly synthetic retail data for MercadoLens."""
from __future__ import annotations
import csv
import random
from pathlib import Path
from datetime import date, datetime, timedelta

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / 'data' / 'raw'
RNG = random.Random(48126)

PRODUCTS = [
 ('F001','Pollo entero fresco','Frescos',19.90,14.10,85),
 ('F002','Carne molida premium','Frescos',28.90,20.40,64),
 ('F003','Filete de pollo','Frescos',26.50,18.20,80),
 ('F004','Huevos de granja x15','Frescos',12.90,9.20,110),
 ('F005','Queso fresco 500 g','Frescos',17.90,12.80,72),
 ('A001','Arroz extra 5 kg','Abarrotes',24.90,18.10,110),
 ('A002','Aceite vegetal 1 L','Abarrotes',10.90,7.70,130),
 ('A003','Azúcar rubia 1 kg','Abarrotes',4.90,3.40,145),
 ('A004','Fideos spaghetti 500 g','Abarrotes',5.50,3.60,120),
 ('A005','Atún en conserva 170 g','Abarrotes',7.80,5.40,95),
 ('A006','Leche evaporada 400 g','Abarrotes',4.70,3.15,150),
 ('B001','Agua mineral 625 ml','Bebidas',2.50,1.35,200),
 ('B002','Gaseosa cola 1.5 L','Bebidas',7.50,4.85,145),
 ('B003','Jugo de naranja 1 L','Bebidas',7.90,5.15,95),
 ('B004','Bebida isotónica 500 ml','Bebidas',5.90,3.90,110),
 ('L001','Detergente en polvo 900 g','Limpieza',14.50,10.10,80),
 ('L002','Lavavajilla líquido 750 ml','Limpieza',9.90,6.80,90),
 ('L003','Lejía multiusos 1 L','Limpieza',5.50,3.35,100),
 ('L004','Papel toalla x2','Limpieza',11.90,8.10,95),
 ('L005','Bolsas de basura x20','Limpieza',8.50,5.65,82),
 ('C001','Shampoo nutritivo 400 ml','Cuidado personal',21.90,15.40,70),
 ('C002','Jabón antibacterial x3','Cuidado personal',10.50,7.20,90),
 ('C003','Pasta dental 90 g','Cuidado personal',8.90,6.10,100),
 ('C004','Desodorante roll-on','Cuidado personal',15.90,11.20,72),
]
CATEGORIES = {'Frescos':1.50,'Abarrotes':1.70,'Bebidas':1.10,'Limpieza':0.88,'Cuidado personal':0.84}
CATS = list(CATEGORIES)
CHANNELS = ['Tienda física','WhatsApp','Delivery']


def write(path: Path, fields: list[str], rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w',newline='',encoding='utf-8-sig') as file:
        out=csv.DictWriter(file,fieldnames=fields)
        out.writeheader();out.writerows(rows)


def main():
    RAW.mkdir(parents=True, exist_ok=True)
    product_rows=[dict(sku=p[0],product_name=p[1],category=p[2],unit_price=p[3],unit_cost=p[4],initial_stock=p[5]) for p in PRODUCTS]
    write(RAW/'products.csv',list(product_rows[0]), product_rows)
    start=date(2026,5,1)
    last=date(2026,10,31)
    orders=[]
    seq=0
    line_id=0
    for day_no in range((last-start).days+1):
        d=start+timedelta(days=day_no)
        seasonal=1+day_no/183*0.22
        weekend=1.26 if d.weekday() in [5,6] else 1.0
        volume=round((10+RNG.uniform(-3.8,5.5))*seasonal*weekend)
        for _ in range(max(5,volume)):
            seq+=1
            order_id=f'VEN-{d.strftime("%Y%m%d")}-{seq:05d}'
            channel=RNG.choices(CHANNELS,[75,17,8])[0]
            hour=RNG.choices(range(8,21),[3,7,10,12,8,6,8,11,12,9,7,5,2])[0]
            minute=RNG.randint(0,59)
            payment=RNG.choices(['Yape','Efectivo','Tarjeta','Plin'],[38,30,22,10])[0]
            count=RNG.choices([1,2,3,4],[57,27,12,4])[0]
            items=RNG.sample(PRODUCTS,count)
            for sku,product,category,price,cost,_ in items:
                line_id+=1
                quantity=RNG.choices([1,2,3,4],[65,22,10,3])[0]
                discount=0 if RNG.random()<.88 else RNG.choice([0.5,1,1.5,2])
                # Some products have modest promotions over time.
                actual_price=round(price*(0.97 if RNG.random()<.11 else 1),2)
                orders.append(dict(line_id=f'LN-{line_id:07d}',order_id=order_id,
                    sold_at=f'{d.isoformat()} {hour:02d}:{minute:02d}:00',sku=sku,
                    quantity=quantity,unit_price=f'{actual_price:.2f}',unit_cost=f'{cost:.2f}',
                    discount=f'{min(discount,actual_price-0.01):.2f}',channel=channel,payment_method=payment))
    # Intentional, controlled quality issues: included in ETL audit and rejected when imported.
    for row in RNG.sample(orders,12):
        orders.append(dict(row))
    for i in range(8):
        record=dict(RNG.choice(orders[:1000]));record['line_id']=f'BAD-SKU-{i:03d}';record['sku']='UNKNOWN'
        orders.append(record)
    for i in range(5):
        record=dict(RNG.choice(orders[:1000]));record['line_id']=f'BAD-QTY-{i:03d}';record['quantity']='-3'
        orders.append(record)
    RNG.shuffle(orders)
    write(RAW/'sales.csv',list(orders[0]),orders)
    snapshots=[]
    for d in [start+timedelta(days=i) for i in range(0,184,7)]+[last]:
        for sku,product,category,price,cost,base in PRODUCTS:
            stock=max(0,int(base*(.55+RNG.random()*.85)))
            if d.month==10 and sku in ('B003','F005','L004'):stock=RNG.randrange(0,7)
            snapshots.append(dict(snapshot_date=d.isoformat(),sku=sku,stock_on_hand=stock,
                              reorder_point=max(8,int(base*.17))))
    write(RAW/'inventory_snapshots.csv',list(snapshots[0]),snapshots)
    print(f'Generated synthetic dataset: {len(product_rows)} products, {len(orders)} raw sales rows, {len(snapshots)} inventory rows')

if __name__=='__main__':main()
