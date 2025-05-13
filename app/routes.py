from flask import render_template
from app import app

@app.route("/")
def dashboard():
    data = {
        "product_count": 325,
        "discounts": 18,
        "price_change": -2.4,
        "table_data": [
            {"group": "Sviests", "price": 2.10, "change": "+5.8%"},
            {"group": "Tomāti", "price": 1.50, "change": "+2%"},
            {"group": "Vīns", "price": 4.75, "change": "-1.2%"},
            {"group": "Gurķi", "price": 1.10, "change": "+0.5%"},
            {"group": "Piens", "price": 0.99, "change": "-0.9%"},
        ]
    }
    return render_template("dashboard.html", data=data)