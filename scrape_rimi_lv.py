import requests
import json
from lxml.html import fromstring  # https://lxml.de/lxmlhtml.html
import concurrent.futures
from db import *

"""
scrape_rimi_lv_page un scrape_rimi_lv_pages:

max pageSize=100
currentPage sākas ar 1 nevis 0
jāizmanto "user-agent", lai iegūtu datus
"""


# vienu lapu (produktiem):
def scrape_rimi_lv_page(page=1, return_max_page=False):
    url = f"https://www.rimi.lv/e-veikals/lv/meklesana?currentPage={page}&pageSize=100&query="
    response = requests.get(url, headers={"user-agent": ""})
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
        if return_max_page:
            # izvada maksimālo lapu skaitu:
            max_page = int(html.xpath('//li[@class="pagination__item"][last()]/a')[0].text_content())
            return products, max_page
        return products
    raise Exception(f"ERROR ({response.status_code}): {url}")


# vias lapas (produktiem):
# ! lai uzlabotu ātrumu var paspēlēties ar "max_workers" daudzumu un pamēģināt lietot dažādas "user-agent" vērtības:
def scrape_rimi_lv_pages():
    # 1. lapa:
    all_products, max_page = scrape_rimi_lv_page(page=1, return_max_page=True)
    # 2. līdz pēdējai lapai:
    pages = [i for i in range(2, max_page + 1)]
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as pool:
            for products in list(pool.map(scrape_rimi_lv_page, pages)):
                all_products += products
        return all_products
    except Exception as e:
        print(e)
        print(f"INFO: scraped only {len(all_products)} products")
        return all_products


# tikai kategorijas:
def scrape_rimi_lv_categories():
    url = "https://www.rimi.lv/e-veikals/api/v1/content/category-tree?locale=lv"
    response = requests.get(url, headers={"user-agent": ""})
    main_categories = []
    subcategories = []
    if response.status_code != 200:
        raise Exception(f"ERROR ({response.status_code}): {url}")
    # galvenās kategorijas:
    for main_category in json.loads(response.text)["categories"]:
        main_category_id = main_category["url"]
        main_category_id = main_category_id[main_category_id.rfind("/") + 1 :]
        main_categories.append((main_category_id, main_category["name"]))
        # apakškategorijas:
        for subcategory in main_category["descendants"]:
            subcategory_id = subcategory["url"]
            subcategory_id = subcategory_id[subcategory_id.rfind("/") + 1 :]
            subcategories.append((subcategory_id, subcategory["name"], main_category_id))
    # izmet kļūdu, ja netika iegūtas kategorijas:
    if main_categories and subcategories:
        return main_categories, subcategories
    raise Exception(f"ERROR ({response.status_code}): {url}")


# iegūst datus un saglabā datubāzē:
def scrape_rimi_lv():
    # scrape:
    main_categories, subcategories = scrape_rimi_lv_categories()
    products = scrape_rimi_lv_pages()
    conn = db_create_connection()
    # main_categories:
    for mc in main_categories:
        id, name = mc
        sql = f"SELECT id FROM main_categories WHERE id='{id}';"
        if not db_get2(conn=conn, sql=sql):
            sql = f'INSERT INTO main_categories (id,name) VALUES("{id}","{name}");'
            db_update2(conn=conn, sql=sql)
    # subcategories:
    for s in subcategories:
        id, name, main_categories_id = s
        sql = f"SELECT id FROM subcategories WHERE id='{id}';"
        if not db_get2(conn=conn, sql=sql):
            sql = f'INSERT INTO subcategories (id,name,main_category_id) VALUES("{id}","{name}","{main_categories_id}");'
            db_update2(conn=conn, sql=sql)
    # products:
    for product in products:
        # visus datus izņemot valūtu "currency", kas ir "EUR" un "brand", jo tas vienmēr uzrādās kā "None":
        id, name, subcategories_id, brand, price, currency = tuple(product.values())
        product = (id, name, subcategories_id, price)
        sql = f"SELECT id FROM products WHERE id={id};"
        if not db_get2(conn=conn, sql=sql):
            sql = f"INSERT INTO products (id,name,subcategory_id,price) VALUES{product};"
            db_update2(conn=conn, sql=sql)
        else:
            sql = f"UPDATE products SET price = {price} WHERE id = {id};"
            db_update2(conn=conn, sql=sql)
    conn.close()


if __name__ == "__main__":
    scrape_rimi_lv()
