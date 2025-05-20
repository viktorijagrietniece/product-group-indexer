import requests
import json
from datetime import datetime
from fake_useragent import UserAgent
import time

from app import db
from app.models import Product, Category, Brand, PriceHistory

# manuāli jāmaina vai jāizmanto javascript ģenerējoša metode:
URL_PATHS = [
    "/piena-produkti-un-olas",
    "/augli-un-darzeni",
    "/maize-un-konditorejas-izstradajumi",
    "/gala-zivs-un-gatava-kulinarija",
    "/bakaleja",
    "/saldeta-partika",
    "/dzerieni",
    "/zidainu-un-bernu-preces",
    "/kosmetika-un-higiena",
    "/viss-tirisanai-un-majdzivniekiem",
    "/majai-un-atputai",
]

UA = UserAgent()

# atjauno datubāzi un izvada True/False par to vai ir vēl dati, ko skrāpēt no nākamās lapas:
def scrape_barbora_lv_page(url):
    scrape_next = True
    response = requests.get(url, headers={"user-agent": UA.random})

    if response.status_code != 200:
        if response.status_code == 504:
            # pagaida 1 sekundi un mēģina vēlreiz:
            print(f"TRYING AGAIN: {url}")
            time.sleep(1)
            return scrape_barbora_lv_page(url)
        raise Exception(f"ERROR ({response.status_code}): {url}")
    # HTML parsēšana:
    text = response.text
    temp = text[text.rfind("window.b_productList = ") + len("window.b_productList = "):]
    json_data = json.loads(temp[: temp.find("</script>")].strip()[:-1])

    for item in json_data:
        # par kategoriju:
        category = Category.query.get(item["category_id"])
        if not category:
            category = Category(
                id=item["category_id"],
                name=item["category_name_full_path"],
                store="barbora_lv"
            )
            db.session.add(category)

        # par zīmolu:
        brand = None
        if item.get("brand_id"):
            brand = Brand.query.get(item["brand_id"])
            if not brand:
                brand = Brand(
                    id=item["brand_id"],
                    name=item["brand_name"],
                    store="barbora_lv"
                )
                db.session.add(brand)

        # par produktu:
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
                store="barbora_lv"
            )
            db.session.add(product)
        else:
    # Vesture tiek appildinata vienmer
            db.session.add(PriceHistory(
                product_id=product.id,
                current_price=current_price,
                full_price=full_price,
                date=datetime.now(),
                store="barbora_lv"
            ))

    # Atjauno produktu datus
            product.current_price = current_price
            product.full_price = full_price
            product.last_modified = last_modified
            product.currently_listed = currently_listed


    db.session.commit()

    if len(json_data) < 52:
        scrape_next = False

    print(f"SCRAPED: {url} ({scrape_next})")
    return scrape_next


def scrape_barbora_lv():
    with db.engine.connect() as conn:
        conn.execute(db.text("UPDATE products SET currently_listed=FALSE"))

    for url_path in URL_PATHS:
        print(f"SCRAPING: {url_path}")
        # 1. līdz pēdējai lapai kategorijā:
        i = 1
        scrape_next = True
        while scrape_next:
            url = f"https://barbora.lv{url_path}?page={i}"
            scrape_next = scrape_barbora_lv_page(url)
            i += 1


if __name__ == "__main__":
    from app import app
    with app.app_context():
        scrape_barbora_lv()
