# Importē nepieciešamās bibliotēkas
from flask import render_template, request
from app import app, db
from sqlalchemy import MetaData, Table, select

# Flask maršruts sākuma lapai
@app.route("/", methods=["GET"])
def dashboard():
# Saņem no URL, kurš veikals ir izvēlēts (noklusēti: barbora_lv)
    selected = request.args.get("veikals", "barbora_lv")
# Inicializē metadatus (bez .bind — jo SQLAlchemy 2.x metīs errorus)
    metadata = MetaData()
# Ielādē "products" tabulu no datubāzes
    products_table = Table('products', metadata, autoload_with=db.engine)
# Mēģina nolasīt 20 produktus no DB (beigu versijai var noņemt)
    try:
        stmt = select(products_table).where(products_table.c.store == selected).limit(20)
        with db.engine.connect() as conn:
            rows = conn.execute(stmt).fetchall()
    except Exception as e:
        print(f"Datu bāzes kļūda: {e}")
        rows = []
# Formatē datus tabulai (produkts + cena + placeholder izmaiņas)
    table_data = [
        {"group": row.name, "price": row.current_price, "change": "+0%"}
        for row in rows
    ]
# Papildu dati virsrakstiem/statistikai (vēl nav reāli aprēķināti)
    data = {
        "product_count": len(rows),
        "discounts": 0,
        "price_change": 0,
        "table_data": table_data
    }
# Atgriež dashboard.html veidni kopā ar datiem
    return render_template("dashboard.html", data=data, selected=selected)