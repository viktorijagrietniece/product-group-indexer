# Importē nepieciešamās bibliotēkas
from flask import render_template, request
from app import app
import os
from sqlalchemy import create_engine, Column, Integer, String, Float, MetaData, Table
from sqlalchemy.orm import sessionmaker

# Karte starp veikalu nosaukumiem un to attiecīgajiem datubāzes failiem
dbMap = {
    "barbora_lv": "barbora_lv.db",
    "barbora_lt": "barbora_lt.db",
    "rimi_lv": "rimi_lv.db",
    "rimi_lt": "rimi_lt.db"
}
# Flask maršruts sākuma lapai
@app.route("/", methods=["GET"])
def dashboard():
# Saņem no URL, kurš veikals ir izvēlēts (noklusēti: barbora_lv)
    selected = request.args.get("veikals", "barbora_lv")
# Dabūjam faila nosaukumu no mapes, ja nav atrodams, ņem noklusēto
    dbFile = dbMap.get(selected, "barbora_lv.db")
# Izveidojam absolūto ceļu līdz .db failam
    baseDir = os.path.abspath(os.path.dirname(__file__))
    dbPath = os.path.join(baseDir, "..", dbFile)
# SQLAlchemy engine tiek izveidots lai pieslēgtos pie konkrētā SQLite faila
    engine = create_engine(f"sqlite:///{dbPath}")
# Inicializē metadatus (bez .bind — jo SQLAlchemy 2.x metīs errorus)
    metadata = MetaData()
# Ielādē "products" tabulu no datubāzes
    products_table = Table('products', metadata, autoload_with=engine)
# Izveido sesiju ar šo datubāzi (ORM interfeiss)
    Session = sessionmaker(bind=engine)
    session = Session()
# Mēģina nolasīt 20 produktus no DB (beigu versijai var noņemt)
    try:
        rows = session.query(products_table).limit(20).all()
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