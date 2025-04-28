import requests
import json
from lxml.html import fromstring  # https://lxml.de/lxmlhtml.html
import concurrent.futures
from db import *
from fake_useragent import UserAgent

UA = UserAgent()

"""
scrape_rimi_lt_page un scrape_rimi_lt_pages:

max pageSize=100
currentPage sākas ar 1 nevis 0
jāizmanto "user-agent", lai iegūtu datus
"""


# vienu lapu (produktiem):
def scrape_rimi_lt_page(page=1, return_max_page=False):
    url = f"https://www.rimi.lt/e-parduotuve/lt/paieska?currentPage={page}&pageSize=100&query="
    response = requests.get(url, headers={"user-agent": UA.random})
    if response.status_code != 200:
        raise Exception(f"ERROR ({response.status_code}): {url}")
    # HTML parsēšana:
    html = fromstring(response.text)
    products = []
    # produkti pēc klases "js-product-container":
    for div in html.xpath('//div[contains(@class, "js-product-container")]'):
        products.append(json.loads(div.get("data-gtm-eec-product")))
    # izmet kļūdu, ja netika iegūti produktu ieraksti:
    if products:
        print(f"SCARPED: scrape_rimi_lt_page (page={page})")
        # print(page)
        if return_max_page:
            # izvada maksimālo lapu skaitu:
            max_page = int(
                html.xpath('//li[@class="pagination__item"][last()]/a')[
                    0
                ].text_content()
            )
            return products, max_page
        return products
    raise Exception(f"ERROR ({response.status_code}): {url}")


# vias lapas (produktiem):
# ! lai uzlabotu ātrumu var paspēlēties ar "max_workers" vērtību:
def scrape_rimi_lt_pages():
    # 1. lapa:
    all_products, max_page = scrape_rimi_lt_page(page=1, return_max_page=True)
    # 2. līdz pēdējai lapai:
    pages = [i for i in range(2, max_page + 1)]
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_page) as pool:
            for products in list(pool.map(scrape_rimi_lt_page, pages)):
                all_products += products
        return all_products
    except Exception as e:
        print(e)
        print(f"INFO: scraped only {len(all_products)} products")
        print("SCARPED: scrape_rimi_lt_pages")
        return all_products


# tikai kategorijas:
def scrape_rimi_lt_categories():
    url = "https://www.rimi.lt/e-parduotuve/api/v1/content/category-tree?locale=lt"
    response = requests.get(url, headers={"user-agent": ""})
    categories = []
    if response.status_code != 200:
        raise Exception(f"ERROR ({response.status_code}): {url}")
    # galvenās kategorijas:
    for main_category in json.loads(response.text)["categories"]:
        main_category_id = main_category["url"]
        main_category_id = main_category_id[main_category_id.rfind("/") + 1 :]
        categories.append((main_category_id, main_category["name"]))
        # 2. līmeņa kategorijas:
        for subcategory1 in main_category["descendants"]:
            subcategory1_id = subcategory1["url"]
            subcategory1_id = subcategory1_id[subcategory1_id.rfind("/") + 1 :]
            categories.append((subcategory1_id, subcategory1["name"]))
            # 3. līmeņa kategorijas:
            for subcategory2 in subcategory1["descendants"]:
                subcategory2_id = subcategory2["url"]
                subcategory2_id = subcategory2_id[subcategory2_id.rfind("/") + 1 :]
                categories.append((subcategory2_id, subcategory2["name"]))
    # izmet kļūdu, ja netika iegūtas kategorijas:
    if categories:
        print("SCARPED: scrape_rimi_lt_categories")
        return categories
    raise Exception(f"ERROR ({response.status_code}): {url}")


# iegūst datus un saglabā datubāzē:
def scrape_rimi_lt():
    print("STARTED: scrape_rimi_lt")
    filename = "rimi_lt.db"
    if not os.path.exists(filename):
        db_create(filename)
    # scrape:
    categories = scrape_rimi_lt_categories()
    products = scrape_rimi_lt_pages()
    conn = db_create_connection(filename)
    # categories:
    for c in categories:
        id, name = c
        sql = f"""SELECT id FROM categories WHERE id='{id}';"""
        if not db_get(conn=conn, sql=sql):
            sql = f"""INSERT INTO categories (id,name) VALUES(?,?);"""
            db_insert(conn, sql, c)
    print("UPDATED: categories")
    # products:
    for product in products:
        # visus datus izņemot valūtu "currency", kas ir "EUR" un "brand", jo tas vienmēr uzrādās kā "None":
        id, name, category_id, brand, price, currency = tuple(product.values())
        product = (id, name, category_id, price)
        sql = f"""SELECT id FROM products WHERE id={id};"""
        if not db_get(conn=conn, sql=sql):
            sql = (
                f"""INSERT INTO products (id,name,category_id,price) VALUES(?,?,?,?);"""
            )
            db_insert(conn, sql, product)
        else:
            sql = f"""UPDATE products SET price = {price} WHERE id = {id};"""
            db_update(conn=conn, sql=sql)
    print("UPDATED: products")
    conn.close()
    print("FINISHED: scrape_rimi_lt")


if __name__ == "__main__":
    scrape_rimi_lt()