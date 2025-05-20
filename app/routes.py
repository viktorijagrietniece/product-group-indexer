# Importē nepieciešamās bibliotēkas
from flask import render_template, request
from app import app, db
from app.models import Product, PriceHistory
from sqlalchemy import desc
import joblib
import os
from sklearn.metrics.pairwise import cosine_similarity
from collections import defaultdict
from datetime import datetime, timedelta
import pandas as pd
from app.models import Category
from sqlalchemy import desc, func

#SĀKUMA LAPA AR GRAFIKIEM
@app.route("/", methods=["GET"])
def dashboard():
    selected = request.args.get("veikals", "barbora_lv")
    selected_category = request.args.get("kategorija", "")
    page = int(request.args.get("page", 1))
    per_page = 30

    def shorten_category_id(cat_id):
        parts = cat_id.split("-")
        return "-".join(parts[:2]) if len(parts) >= 2 else cat_id

    # Tiek ielādēti produktu kategoriju nosaukumi
    category_names_map = {}
    kategorijas = Category.query.filter_by(store=selected).all()
    if kategorijas:
        df_kategorijas = pd.DataFrame([{
            "id": c.id,
            "name": c.name
        } for c in kategorijas])
        df_kategorijas["id_lvl1"] = df_kategorijas["id"].apply(shorten_category_id)
        df_nosaukumi = df_kategorijas.drop_duplicates("id_lvl1")[["id_lvl1", "name"]]
        category_names_map = dict(zip(df_nosaukumi["id_lvl1"], df_nosaukumi["name"]))

    query = Product.query.filter_by(store=selected)
    if selected_category:
        query = query.filter(Product.category_id.ilike(f"{selected_category}%"))
    products = query.all()
    total_products = len(products)
    product_ids = [p.id for p in products]

    result = []
    discount_count = 0
    total_current = 0
    total_previous = 0

    # Iepriekšējās cenas uzglabā
    history_map = {}
    if product_ids:
        history_rows = (
            db.session.query(PriceHistory.product_id, PriceHistory.current_price)
            .filter(PriceHistory.product_id.in_(product_ids))
            .order_by(PriceHistory.product_id, desc(PriceHistory.date))
            .all()
        )
        for row in history_rows:
            if row.product_id not in history_map:
                history_map[row.product_id] = row.current_price

    for p in products:
        current_price = p.current_price
        previous_price = history_map.get(p.id)

        if previous_price is None:
            previous_price = current_price

        if previous_price == 0:
            continue

        change_percent = round(((current_price - previous_price) / previous_price) * 100, 2)

        if change_percent == 0:
            continue

        if change_percent < 0:
            discount_count += 1

        result.append({
            "group": p.name,
            "price": current_price,
            "previous": previous_price,
            "change": f"{change_percent:+.2f}%"
        })

        total_current += current_price
        total_previous += previous_price

    price_change_percent = round(((total_current - total_previous) / total_previous) * 100, 2) if total_previous else 0
    total_pages = (len(result) + per_page - 1) // per_page
    paginated = result[(page - 1) * per_page: page * per_page]

    # Vidējo cenu noteikšana pa periodiem
    last_days = [datetime.utcnow().date() - timedelta(days=i) for i in range(2, -1, -1)]
    history_data = defaultdict(lambda: {str(d): 0 for d in last_days})
    counts = defaultdict(lambda: {str(d): 0 for d in last_days})

    rows = db.session.query(
        PriceHistory.store,
        func.date(PriceHistory.date),
        PriceHistory.current_price
    ).filter(
        PriceHistory.date >= datetime.utcnow() - timedelta(days=14)
    ).all()

    for store, date, price in rows:
        d_str = str(date)
        if d_str in history_data[store]:
            history_data[store][d_str] += price
            counts[store][d_str] += 1

    chart_series = {}
    for store in history_data:
        chart_series[store] = [
            round(history_data[store][str(d)] / counts[store][str(d)], 2)
            if counts[store][str(d)] > 0 else None
            for d in last_days
        ]
    chart_labels = [str(d) for d in last_days]

    # Svārstības cenās pa produktu grupām
    volatility_rows = db.session.query(
        Product.category_id,
        PriceHistory.current_price
    ).join(PriceHistory, Product.id == PriceHistory.product_id)\
     .filter(Product.store == selected)\
     .filter(PriceHistory.date >= datetime.utcnow() - timedelta(days=14))\
     .all()

    df_vol = pd.DataFrame([{
        "category": shorten_category_id(r[0]),
        "price": r[1]
    } for r in volatility_rows])

    volatility_data = {"labels": [], "values": []}
    if not df_vol.empty:
        volatility = (
            df_vol.groupby("category")["price"]
            .std()
            .round(3)
            .sort_values(ascending=False)
        )
        volatility_data = {
            "labels": [category_names_map.get(cat, cat) for cat in volatility.index],
            "values": [float(v) for v in volatility.values.tolist()]
        }

    # Dropdown izvēle
    all_categories = sorted(set(shorten_category_id(p.category_id) for p in Product.query.filter_by(store=selected).all()))

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
                           selected_category=selected_category,
                           kategorijas=all_categories,
                           category_names=category_names_map,
                           chart_labels=chart_labels,
                           chart_series=chart_series,
                           volatility_data=volatility_data)




# PILNA PRODUKTU LAPA
@app.route("/all", methods=["GET"])
def dashboard_all_products():
    # Saņem no URL, kurš veikals ir izvēlēts (noklusēti: barbora_lv)
    selected = request.args.get("veikals", "barbora_lv")
    page = int(request.args.get("page", 1))
    per_page = 50
    
    # Dabū visus produktus no izvēlētā veikala
    products = Product.query.filter_by(store=selected).all()
    
    # Formatē datus tabulai
    table_data = [{
        "name": p.name,
        "category": p.category_id,
        "current_price": p.current_price,
        "full_price": p.full_price,
        "modified": p.last_modified,
        "available": p.currently_listed
    } for p in products]

    total_pages = (len(table_data) + per_page - 1) // per_page
    paginated = table_data[(page - 1) * per_page: page * per_page]

    data = {
        "productCount": len(table_data),
        "table_data": paginated,
        "current_page": page,
        "total_pages": total_pages
    }

    # Atgriež all_products.html veidni kopā ar datiem
    return render_template("all_products.html", data=data, selected=selected)



@app.route("/grouper", methods=["GET", "POST"])
def grouper_page():
    kategorija = None
    nosaukums = ""
    veikals = "barbora_lv"
    veikali = ["barbora_lv", "barbora_lt", "rimi_lv", "rimi_lt"]
    lidzigie_produkti = []

    if request.method == "POST":
        nosaukums = request.form.get("nosaukums")
        veikals = request.form.get("veikals")

        modela_cels = f"models/model_{veikals}.pkl"
        vektora_cels = f"models/vectorizer_{veikals}.pkl"

        if os.path.exists(modela_cels) and os.path.exists(vektora_cels):
            modelis = joblib.load(modela_cels)
            vektorizetajs = joblib.load(vektora_cels)

            # Vektorizē ievadi un prognozē kategoriju
            ieeja = vektorizetajs.transform([nosaukums])
            kategorija = modelis.predict(ieeja)[0]

            # Dabū visus produktus no veikala
            visi_produkti = Product.query.filter_by(store=veikals).all()
            nosaukumi = [p.name for p in visi_produkti]
            produkti_karte = {p.name: p for p in visi_produkti}

            # Vektorizē visus produktus
            visi_vektori = vektorizetajs.transform(nosaukumi)

            # Aprēķina cosine līdzību
            similarity_scores = cosine_similarity(ieeja, visi_vektori)[0]

            top_idx = similarity_scores.argsort()[::-1]
            prioritizetie = []
            citi = []

            for i in top_idx:
                nos = nosaukumi[i]
                if nos.lower() == nosaukums.lower():
                    continue
                if nosaukums.lower() in nos.lower():
                    prioritizetie.append(nos)
                else:
                    citi.append(nos)

            top_n = (prioritizetie + citi)[:20]  # prioritāri nosaukuma sakritības

            # Veido rezultātu sarakstu ar cenām
            lidzigie_produkti = [{
                "name": produkti_karte[n].name,
                "price": produkti_karte[n].current_price
            } for n in top_n if produkti_karte[n].current_price is not None]

            # Kārto pēc cenas augošā secībā
            lidzigie_produkti = sorted(lidzigie_produkti, key=lambda x: x["price"])
        else:
            kategorija = "Modelis nav pieejams izvēlētajam veikalam."

    return render_template("grouper.html",
                           nosaukums=nosaukums,
                           kategorija=kategorija,
                           veikals=veikals,
                           veikali=veikali,
                           lidzigie_produkti=lidzigie_produkti)


