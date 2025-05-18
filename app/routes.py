from flask import render_template, request
from app import app
import os
from sqlalchemy import create_engine, MetaData, Table, select, desc
from sqlalchemy.orm import sessionmaker
from collections import defaultdict

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
    per_page = 30

    chart_labels = []
    chart_data = []

    for key, db_file in dbMap.items():
        db_path = os.path.join(os.path.dirname(__file__), "..", db_file)
        engine = create_engine(f"sqlite:///{db_path}")
        metadata = MetaData()
        metadata.reflect(bind=engine)

        if "products" not in metadata.tables:
            continue

        products = metadata.tables["products"]
        conn = engine.connect()
        rows = conn.execute(select(products)).fetchall()
        prices = [r.current_price for r in rows if r.current_price is not None]

        avg = round(sum(prices) / len(prices), 2) if prices else 0
        chart_labels.append(key)
        chart_data.append(avg)

    # -- Statistika no izvēlētā veikala
    db_path = os.path.join(os.path.dirname(__file__), "..", dbMap[selected])
    engine = create_engine(f"sqlite:///{db_path}")
    metadata = MetaData()
    metadata.reflect(bind=engine)
    products_table = metadata.tables["products"]
    history_table = metadata.tables["history"]
    conn = engine.connect()

    rows = conn.execute(select(products_table)).fetchall()
    total_products = len(rows)

    result = []
    discount_count = 0
    total_current = 0
    total_previous = 0

    for row in rows:
        product_id = row.id
        current_price = row.current_price
        name = row.name
        total_current += current_price

        last_row = conn.execute(
            select(history_table.c.current_price)
            .where(history_table.c.product_id == product_id)
            .order_by(desc(history_table.c.date))
            .limit(1)
        ).fetchone()

        previous_price = last_row[0] if last_row else current_price
        total_previous += previous_price

        if previous_price == 0 or current_price == previous_price:
            continue

        change_percent = round(((current_price - previous_price) / previous_price) * 100, 2)

        if change_percent < 0:
            discount_count += 1

        result.append({
            "group": name,
            "price": current_price,
            "previous": previous_price,
            "change": f"{change_percent:+.2f}%"
        })

    price_change_percent = 0
    if total_previous > 0:
        price_change_percent = round(((total_current - total_previous) / total_previous) * 100, 2)

    total_pages = (len(result) + per_page - 1) // per_page
    paginated = result[(page - 1) * per_page: page * per_page]

    data = {
        "product_count": total_products,
        "discounts": discount_count,
        "price_change": price_change_percent,
        "table_data": paginated,
        "current_page": page,
        "total_pages": total_pages
    }

    return render_template("dashboard.html",
        data=data,
        selected=selected,
        chart_labels=chart_labels,
        chart_data=chart_data
    )
# PILNA PRODUKTU LAPA (bez lapošanas pagaidām)
@app.route("/all", methods=["GET"])
def dashboard_all_products():
    selected = request.args.get("veikals", "barbora_lv")
    engine, productsTable, _ = get_engine_and_tables(selected)
    conn = engine.connect()

    rows = conn.execute(select(productsTable)).fetchall()

    tableData = [{
        "name": row.name,
        "category": row.category_id,
        "current_price": row.current_price,
        "full_price": row.full_price,
        "modified": row.last_modified,
        "available": row.currently_listed
    } for row in rows]

    data = {
        "productCount": len(tableData),
        "table_data": tableData
    }

    return render_template("all_products.html", data=data, selected=selected)
