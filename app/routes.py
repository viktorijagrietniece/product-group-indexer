from flask import render_template, request
from app import app
import os
from sqlalchemy import create_engine, MetaData, Table, select, desc
from sqlalchemy.orm import sessionmaker

# Karte starp veikalu kodiem un attiecīgajiem lokālajiem .db failiem
dbMap = {
    "barbora_lv": "barbora_lv.db",
    "barbora_lt": "barbora_lt.db",
    "rimi_lv": "rimi_lv.db",
    "rimi_lt": "rimi_lt.db"
}

# Palīgfunkcija, kas uzstāda pieslēgumu un tabulu objektus
def get_engine_and_tables(selected):
    dbFile = dbMap.get(selected, "barbora_lv.db")
    baseDir = os.path.abspath(os.path.dirname(__file__))
    dbPath = os.path.join(baseDir, "..", dbFile)
    engine = create_engine(f"sqlite:///{dbPath}")
    metadata = MetaData()
    metadata.reflect(bind=engine)
    return engine, metadata.tables["products"], metadata.tables["history"]

# GALVENĀ LAPĀ — rāda produktus ar cenu izmaiņām, lapošana + filtrēšana
@app.route("/", methods=["GET"])
def dashboard_changes_only():
    selected = request.args.get("veikals", "barbora_lv")
    page = int(request.args.get("page", 1))
    per_page = 15

    engine, products_table, history_table = get_engine_and_tables(selected)
    conn = engine.connect()
    products = conn.execute(select(products_table)).fetchall()

    result = []

    for product in products:
        product_id = product.id
        current_price = product.current_price
        name = product.name

        last_history_row = conn.execute(
            select(history_table.c.current_price)
            .where(history_table.c.product_id == product_id)
            .order_by(desc(history_table.c.date))
            .limit(1)
        ).fetchone()

        previous_price = last_history_row[0] if last_history_row else current_price

        if previous_price == 0:
            change_percent = 0
        else:
            change_percent = round(((current_price - previous_price) / previous_price) * 100, 2)

        if change_percent == 0:
            continue

        result.append({
            "group": name,
            "price": current_price,
            "previous": previous_price,
            "change": f"{change_percent:+.2f}%"
        })

    total = len(result)
    start = (page - 1) * per_page
    end = start + per_page
    paginated = result[start:end]

    # Aizsardzība, lai vienmēr būtu lapošanas info
    if not paginated:
        data = {
            "product_count": 0,
            "discounts": 0,
            "price_change": 0,
            "table_data": [],
            "current_page": page,
            "total_pages": 1
        }
    else:
        data = {
            "product_count": total,
            "discounts": 0,
            "price_change": 0,
            "table_data": paginated,
            "current_page": page,
            "total_pages": (total + per_page - 1) // per_page
        }

    return render_template("dashboard.html", data=data, selected=selected)

# PILNA PRODUKTU LAPA (bez lapošanas pagaidām)
@app.route("/all", methods=["GET"])
def dashboard_all_products():
    selected = request.args.get("veikals", "barbora_lv")
    engine, products_table, _ = get_engine_and_tables(selected)
    conn = engine.connect()

    rows = conn.execute(select(products_table)).fetchall()

    table_data = [{
        "name": row.name,
        "category": row.category_id,
        "current_price": row.current_price,
        "full_price": row.full_price,
        "modified": row.last_modified,
        "available": row.currently_listed
    } for row in rows]

    data = {
        "product_count": len(table_data),
        "table_data": table_data
    }

    return render_template("all_products.html", data=data, selected=selected)
