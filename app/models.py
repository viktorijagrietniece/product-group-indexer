from app import db
from datetime import datetime

class Category(db.Model):
    __tablename__ = 'categories'
    id = db.Column(db.String, primary_key=True)
    name = db.Column(db.String, nullable=False)
    store = db.Column(db.String, nullable=False, default="unknown")


class Brand(db.Model):
    __tablename__ = 'brands'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    store = db.Column(db.String, nullable=False, default="unknown")


class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    category_id = db.Column(db.String, db.ForeignKey('categories.id'), nullable=False)
    current_price = db.Column(db.Float, nullable=False)
    full_price = db.Column(db.Float, nullable=False)
    last_modified = db.Column(db.DateTime, default=datetime.utcnow)
    currently_listed = db.Column(db.Boolean, default=True)
    brand_id = db.Column(db.Integer, db.ForeignKey('brands.id'), nullable=True)
    store = db.Column(db.String, nullable=False, default="unknown")


class PriceHistory(db.Model):
    __tablename__ = 'history'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    current_price = db.Column(db.Float, nullable=False)
    full_price = db.Column(db.Float, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    store = db.Column(db.String, nullable=False, default="unknown")

