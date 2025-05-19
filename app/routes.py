# Importē nepieciešamās bibliotēkas
from flask import render_template, request
from app import app, db
from app.models import Product, PriceHistory
from sqlalchemy import desc

# Flask maršruts sākuma lapai
@app.route("/", methods=["GET"])
def dashboard():
    # Saņem no URL, kurš veikals ir izvēlēts (noklusēti: barbora_lv)
    selected = request.args.get("veikals", "barbora_lv")
    page = int(request.args.get("page", 1))
    per_page = 30

    try:
        # Dabū visus produktus no izvēlētā veikala
        products = Product.query.filter_by(store=selected).all()
        total_products = len(products)

        product_ids = [p.id for p in products]
        result = []
        discount_count = 0
        total_current = 0
        total_previous = 0

        # Dabū iepriekšējās cenas no vēstures tabulas (pēdējā cena katram produktam)
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
        # Atrodi produktus ar cenu izmaiņām
        for p in products:
            current_price = p.current_price
            previous_price = history_map.get(p.id, current_price)
            
            # Ja nav cenu izmaiņu, izlaiž
            if previous_price == 0 or current_price == previous_price:
                continue

            total_current += current_price
            total_previous += previous_price

            # Aprēķina procentuālo izmaiņu
            change_percent = round(((current_price - previous_price) / previous_price) * 100, 2)
            if change_percent < 0:
                discount_count += 1

            result.append({
                "group": p.name,
                "price": current_price,
                "previous": previous_price,
                "change": f"{change_percent:+.2f}%"
            })
        # Kopējā cenu izmaiņu statistika
        price_change_percent = round(((total_current - total_previous) / total_previous) * 100, 2) if total_previous else 0
        total_pages = (len(result) + per_page - 1) // per_page
        paginated = result[(page - 1) * per_page: page * per_page]

    except Exception as e:
        print(f"Datu bāzes kļūda: {e}")
        paginated = []
        total_products = 0
        discount_count = 0
        price_change_percent = 0
        total_pages = 1

    # Gatavo grafika datus — vidējā cena katrā veikalā
    chart_labels = []
    chart_data = []
    for store in ["barbora_lv", "barbora_lt", "rimi_lv", "rimi_lt"]:
        prices = [p.current_price for p in Product.query.filter_by(store=store).all() if p.current_price]
        avg = round(sum(prices) / len(prices), 2) if prices else 0
        chart_labels.append(store)
        chart_data.append(avg)

    # Apvieno visus datus, kas tiks nodoti HTML
    data = {
        "product_count": total_products,
        "discounts": discount_count,
        "price_change": price_change_percent,
        "table_data": paginated,
        "current_page": page,
        "total_pages": total_pages
    }
    
    # Atgriež dashboard.html veidni kopā ar datiem
    return render_template("dashboard.html",
        data=data,
        selected=selected,
        chart_labels=chart_labels,
        chart_data=chart_data
    )

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
