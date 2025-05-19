from flask import render_template, request
from app import app
from sqlalchemy import create_engine, MetaData, Table, select, desc, func
from dotenv import load_dotenv
import os
# Ielādē .env failu
load_dotenv()
# Izveido savienojumu ar PostgreSQL
dbURL = (
    f"postgresql+psycopg2://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}"
    f"@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}"
)
# Izveido SQLAlchemy engine priekš datu bāzes savienojuma
engine = create_engine(dbURL)
metadata = MetaData()
# Ielādē tabulu struktūras no datu bāzes
metadata.reflect(bind=engine)
productsTable = metadata.tables["products"]
historyTable = metadata.tables["history"]
# GALVENĀ LAPĀ — rāda produktus ar cenu izmaiņām, statistika un diagramma
@app.route("/", methods=["GET"])
# Route handler priekš galvenās lapas lai parādītu tikai produktu ierakstus ar cenu izmaiņām
def dashboard_changes_only():
    selected = request.args.get("veikals", "barbora_lv")
    page = int(request.args.get("page", 1))
    perPage = 30
    conn = engine.connect()
    # Diagramma — vidējā cena katrā veikalā
    storeRows = conn.execute(select(productsTable.c.store).distinct()).fetchall()
    chartLabels = []
    chartData = []
    for row in storeRows:
        store = row.store
        rows = conn.execute(select(productsTable.c.current_price).where(productsTable.c.store == store)).fetchall()
        prices = [r.current_price for r in rows if r.current_price]
        avg = round(sum(prices) / len(prices), 2) if prices else 0
        chartLabels.append(store)
        chartData.append(avg)
    # Tabulai — tikai produkti ar cenu izmaiņām no izvēlētā veikala
    product_rows = conn.execute(
        select(productsTable)
        .where(productsTable.c.store == selected)
        .where(productsTable.c.current_price.isnot(None))
        .where(productsTable.c.full_price.isnot(None))
        .where(productsTable.c.current_price != productsTable.c.full_price)
    ).fetchall()
    result = []
    discountCount = 0
    totalCurrent = 0
    totalPrevious = 0

    for row in product_rows:
        name = row.name
        currentPrice = row.current_price
        previousPrice = row.full_price

        totalCurrent += currentPrice
        totalPrevious += previousPrice

        changePercent = round(((currentPrice - previousPrice) / previousPrice) * 100, 2)
        if changePercent < 0:
            discountCount += 1

        result.append({
            "group": name,
            "price": currentPrice,
            "previous": previousPrice,
            "change": f"{changePercent:+.2f}%"
        })

    # Kartīšu statistika
    priceChangePercent = (
        round(((totalCurrent - totalPrevious) / totalPrevious) * 100, 2)
        if totalPrevious > 0 else 0
    )
    productCount = len(product_rows)
    totalPages = (len(result) + perPage - 1) // perPage
    paginated = result[(page - 1) * perPage: page * perPage]
    data = {
        "product_count": productCount,
        "discounts": discountCount,
        "price_change": priceChangePercent,
        "table_data": paginated,
        "current_page": page,
        "total_pages": totalPages
    }
    print("Rendering dashboard with:")
    print("Products:", len(result))
    print("Labels:", chartLabels)
    print("ChartData:", chartData)
    # Renderē HTML veidni ar datiem
    return render_template("dashboard.html",
        data=data,
        selected=selected,
        chart_labels=chartLabels,
        chart_data=chartData
    )
# PILNĀ PRODUKTU LAPA
@app.route("/all", methods=["GET"])
def dashboard_all_products():
    # Route handler priekš visu produktu tabulas
    selected = request.args.get("veikals", "barbora_lv")
    page = int(request.args.get("page", 1))
    perPage = 50
    conn = engine.connect()
    rows = conn.execute(select(productsTable).where(productsTable.c.store == selected)).fetchall()
    tableData = [{
        "name": row.name,
        "category": row.category_id,
        "current_price": row.current_price,
        "full_price": row.full_price,
        "modified": row.last_modified,
        "available": row.currently_listed
    } for row in rows]
    totalPages = (len(tableData) + perPage - 1) // perPage
    paginated = tableData[(page - 1) * perPage : page * perPage]
    data = {
        "product_count": len(tableData),
        "table_data": paginated,
        "current_page" : page,
        "total_pages": totalPages
    }
    # Renderē HTML veidni ar datiem
    return render_template("all_products.html", data=data, selected=selected)