import json
import cloudscraper
from datetime import datetime
from app import db
from app.models import Product, Category, Brand, PriceHistory


URL_PATHS = [
    "/darzoves-ir-vaisiai",
    "/pieno-gaminiai-ir-kiausiniai",
    "/duonos-gaminiai-ir-konditerija",
    "/mesa-zuvis-ir-kulinarija",
    "/bakaleja",
    "/saldytas-maistas",
    "/gerimai",
    "/kudikiu-ir-vaiku-prekes",
    "/kosmetika-ir-higiena",
    "/svaros-ir-gyvunu-prekes",
    "/namai-ir-laisvalaikis",
]

# atjauno datubāzi un izvada True/False par to vai ir vēl dati, ko skrāpēt no nākamās lapas:
def process_json(json_data):
    scrape_next = True

    for item in json_data:
        # par kategoriju
        category = Category.query.get(item["category_id"])
        if not category:
            category = Category(
                id=item["category_id"],
                name=item["category_name_full_path"],
                store="barbora_lt"
            )
            db.session.add(category)

        # par zīmolu
        brand = None
        if item.get("brand_id"):
            brand = Brand.query.get(item["brand_id"])
            if not brand:
                brand = Brand(
                    id=item["brand_id"],
                    name=item["brand_name"],
                    store="barbora_lt"
                )
                db.session.add(brand)

        # par produktu
        product = Product.query.get(item["id"])
        current_price = item["units"][0]["price"]
        full_price = item["units"][0].get("retail_price", current_price)
        last_modified = datetime.now()
        currently_listed = item["status"] == "active"

        if not product:
            product = Product(
                id=item["id"],
                name=item["title"],
                category_id=item["category_id"],
                current_price=current_price,
                full_price=full_price,
                last_modified=last_modified,
                currently_listed=currently_listed,
                brand_id=item["brand_id"] if brand else None,
                store="barbora_lt"
            )
            db.session.add(product)
        else:
    # Vesture tiek appildinata vienmer
            db.session.add(PriceHistory(
                product_id=product.id,
                current_price=current_price,
                full_price=full_price,
                date=datetime.now(),
                store="barbora_lt"
            ))

    # Atjauno produktu datus
            product.current_price = current_price
            product.full_price = full_price
            product.last_modified = last_modified
            product.currently_listed = currently_listed


    db.session.commit()

    if len(json_data) < 52:
        scrape_next = False

    return scrape_next


def scrape_barbora_lt():
    with db.engine.connect() as conn:
        conn.execute(db.text("UPDATE products SET currently_listed=FALSE"))
    # visas kategorijas:
    scraper = cloudscraper.create_scraper()

    for url_path in URL_PATHS:
        print(f"SCRAPING: {url_path}")
        # 1. līdz pēdējai lapai kategorijā:
        i = 1
        scrape_next = True
        while scrape_next:
            url = f"https://barbora.lt{url_path}?page={i}"
            response = scraper.get(url)
            text = response.text
            temp = text[text.rfind("window.b_productList = ") + len("window.b_productList = "):]
            json_data = json.loads(temp[: temp.find("</script>")].strip()[:-1])
            scrape_next = process_json(json_data)
            print(f"SCRAPED: {url} ({scrape_next})")
            i += 1


if __name__ == "__main__":
    from app import app
    with app.app_context():
        db.create_all()
        scrape_barbora_lt()
