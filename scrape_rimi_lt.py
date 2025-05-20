import requests
import json
from lxml.html import fromstring
import concurrent.futures
from datetime import datetime
import time
from fake_useragent import UserAgent

from app import db
from app.models import Product, Category, PriceHistory

UA = UserAgent()

"""
- max pageSize=100
- currentPage sākas ar 1 nevis 0
- jāizmanto "user-agent", lai iegūtu datus
- "data-gtm-eec-product" vērtība mēdz izvadīt nepareizu cenu, tāpēc ir:
    jālieto vērtības no price-tag klases objekta
    (ja nepieciešams - cenu bez atlaides var iegūt no old-price-tag klases objekta)
"""

# vienu lapu (produktiem):
def scrape_rimi_lt_page(page=1, return_max_page=False):
    url = f"https://www.rimi.lt/e-parduotuve/lt/paieska?currentPage={page}&pageSize=100&query="
    response = requests.get(url, headers={"user-agent": UA.random})
    if response.status_code != 200:
        if response.status_code == 504:
            # pagaida 1 sekundi un mēģina vēlreiz:
            print(f"TRYING AGAIN: (page={page})")
            time.sleep(1)
            return scrape_rimi_lt_page(page, return_max_page)
        raise Exception(f"ERROR ({response.status_code}): {url}")
    # HTML parsēšana:
    html = fromstring(response.text)
    products = []
    # produkti pēc klases "js-product-container":
    for div in html.xpath('//div[contains(@class, "js-product-container")]'):
        try:
            product = json.loads(div.get("data-gtm-eec-product"))

            price_divs = div.xpath('.//div[contains(@class, "price-tag")]')
            if not price_divs:
                continue

            price = price_divs[0].getchildren()
            product["current_price"] = float(
                f"{price[0].text_content()}.{price[1].getchildren()[0].text_content()}"
            )

            old_price_divs = div.xpath('.//div[contains(@class, "old-price-tag")]')
            if old_price_divs:
                product["full_price"] = float(
                    old_price_divs[0]
                    .getchildren()[0]
                    .text_content()[:-1]
                    .replace(",", ".")
                )
            else:
                product["full_price"] = product["current_price"]

            product["last_modified"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            products.append(product)
        except Exception as e:
            print(f"Skipping malformed product: {e}")
            continue

    if return_max_page and products:
        try:
            max_page = int(html.xpath('//li[@class="pagination__item"][last()]/a')[0].text_content())
            return products, max_page
        except:
            return products, 1

    return products


def scrape_rimi_lt_pages():
    all_products, max_page = scrape_rimi_lt_page(page=1, return_max_page=True)
    pages = [i for i in range(2, max_page + 1)]

    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as pool:
            for products in pool.map(scrape_rimi_lt_page, pages):
                all_products += products
        return all_products
    except Exception as e:
        print(e)
        return all_products


def scrape_rimi_lt_categories():
    url = "https://www.rimi.lt/e-parduotuve/api/v1/content/category-tree?locale=lt"
    response = requests.get(url, headers={"user-agent": ""})
    if response.status_code != 200:
        raise Exception(f"ERROR ({response.status_code}): {url}")

    categories = []
    for main in json.loads(response.text)["categories"]:
        main_id = main["url"].split("/")[-1]
        categories.append((main_id, main["name"]))

        for sub1 in main["descendants"]:
            sub1_id = sub1["url"].split("/")[-1]
            categories.append((sub1_id, sub1["name"]))

            for sub2 in sub1["descendants"]:
                sub2_id = sub2["url"].split("/")[-1]
                categories.append((sub2_id, sub2["name"]))

    return categories


def scrape_rimi_lt():
    print("STARTED: scrape_rimi_lt")

    for cat_id, cat_name in scrape_rimi_lt_categories():
        if not db.session.get(Category, cat_id):
            db.session.add(Category(id=cat_id, name=cat_name, store="rimi_lt"))

    db.session.commit()
    print("UPDATED: categories")

    with db.engine.connect() as conn:
        conn.execute(db.text("UPDATE products SET currently_listed=FALSE"))

    products = scrape_rimi_lt_pages()
    
    for item in products:
        item["category_id"] = item.get("category")
        if not all(k in item for k in ("id", "name", "category_id", "current_price", "full_price", "last_modified")):
            print(f"Skipping incomplete product: {item}")
            continue

        id = item["id"]
        name = item["name"]
        category_id = item["category_id"]
        if not db.session.get(Category, category_id):
            print(f"Creating missing category: {category_id}")
            db.session.add(Category(id=category_id, name="Unknown", store="rimi_lt"))

        current_price = item["current_price"]
        full_price = item["full_price"]
        last_modified = datetime.strptime(item["last_modified"], "%Y-%m-%d %H:%M:%S")
        currently_listed = True

        product = db.session.get(Product, id)

        if product:
            # Vesture tiek appildinata vienmer
            db.session.add(
                PriceHistory(
                    product_id=id,
                    current_price=current_price,
                    full_price=full_price,
                    date=datetime.now(),
                    store="rimi_lt"
                )
            )

            # Atjauno eksistejosus prduktus
            product.current_price = current_price
            product.full_price = full_price
            product.last_modified = last_modified
            product.currently_listed = currently_listed

        else:
            # Pievieno pirmreizejus produktus
            product = Product(
                id=id,
                name=name,
                category_id=category_id,
                current_price=current_price,
                full_price=full_price,
                last_modified=last_modified,
                currently_listed=currently_listed,
                store="rimi_lt"
            )
            db.session.add(product)



    db.session.commit()
    print("FINISHED: scrape_rimi_lt")


if __name__ == "__main__":
    from app import app
    with app.app_context():
        scrape_rimi_lt()
