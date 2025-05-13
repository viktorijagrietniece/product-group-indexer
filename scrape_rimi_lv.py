import requests
import json
from lxml.html import fromstring  # https://lxml.de/lxmlhtml.html
import concurrent.futures
from db import *
from fake_useragent import UserAgent
import time
from datetime import datetime

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
def scrape_rimi_lv_page(page=1, return_max_page=False):
    url = f"https://www.rimi.lv/e-veikals/lv/meklesana?currentPage={page}&pageSize=100&query="
    response = requests.get(url, headers={"user-agent": UA.random})
    if response.status_code != 200:
        if response.status_code == 504:
            # pagaida 1 sekundi un mēģina vēlreiz:
            print(f"TRYING AGAIN: (page={page})")
            time.sleep(1)
            return scrape_rimi_lv_page(page, return_max_page)
        raise Exception(f"ERROR ({response.status_code}): {url}")
    # HTML parsēšana:
    html = fromstring(response.text)
    products = []
    # produkti pēc klases "js-product-container":
    for div in html.xpath('//div[contains(@class, "js-product-container")]'):
        # visi nepieciešamie dati (cena te var būt kļūdaina un zīmols netiek norādīts):
        product = json.loads(div.get("data-gtm-eec-product"))
        # šāds ir elemeta piemērs, kas satur pašreizējo cenu (ar atlaidi, ja tāda ir):
        """
        <div class="price-tag card__price">
            <span>4</span>
            <div>
                <sup>29</sup>
                <sub>€/kg</sub>
            </div>
        </div>
        """
        # šāds ir elemeta piemērs, kas satur pilno cenu (bez atlaides):
        """
        <div class="old-price-tag card__old-price">
            <span>0,99€</span>
        </div>
        """
        # iegūst pašreizējo un pilno cenu, ja pašreizējo cenu nevar iegūt, tad preci nepievieno sarakstam (šādos gadījumos prece nav pieejama):
        price_divs = div.xpath('.//div[contains(@class, "price-tag")]')
        if price_divs:
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
    if products:
        print(f"SCARPED: scrape_rimi_lv_page (page={page})")
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
    else:
        print(f"DIDNT ADD PRODUCTS FROM: scrape_rimi_lv_page (page={page})")
        return products


# vias lapas (produktiem):
# ! lai uzlabotu ātrumu var paspēlēties ar "max_workers" vērtību:
def scrape_rimi_lv_pages():
    # 1. lapa:
    all_products, max_page = scrape_rimi_lv_page(page=1, return_max_page=True)
    # 2. līdz pēdējai lapai:
    pages = [i for i in range(2, max_page + 1)]
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_page) as pool:
            for products in list(pool.map(scrape_rimi_lv_page, pages)):
                all_products += products
        print("SCARPED: scrape_rimi_lv_pages")
        return all_products
    except Exception as e:
        print(e)
        return all_products


# tikai kategorijas:
def scrape_rimi_lv_categories():
    url = "https://www.rimi.lv/e-veikals/api/v1/content/category-tree?locale=lv"
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
        print("SCARPED: scrape_rimi_lv_categories")
        return categories
    raise Exception(f"ERROR ({response.status_code}): {url}")


# iegūst datus un saglabā datubāzē:
def scrape_rimi_lv():
    print("STARTED: scrape_rimi_lv")
    filename = "rimi_lv.db"
    if not os.path.exists(filename):
        db_create(filename)
    # scrape:
    categories = scrape_rimi_lv_categories()
    products = scrape_rimi_lv_pages()
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
    db_update(
        conn=conn, sql=f"""UPDATE products SET currently_listed=FALSE;"""
    )  # no sākuma visiem ierakstiem piešķir currently_listed=FALSE
    for product in products:
        """
        visus datus izņemot:
        - valūtu "currency", kas ir "EUR"
        - "brand", jo tas vienmēr uzrādās kā "None"
        - "currency", jo tās vērtība var būt kļūdaina:
        """
        (
            id,
            name,
            category_id,
            brand,
            price,
            currency,
            current_price,
            full_price,
            last_modified,
        ) = tuple(product.values())
        product = (
            id,
            name,
            category_id,
            current_price,
            full_price,
            last_modified,
            True,
        )  # currently_listed=True
        sql = f"""SELECT current_price, full_price, last_modified FROM products WHERE id={id};"""
        results = db_get(conn=conn, sql=sql)
        if not results:
            sql = f"""INSERT INTO products (id,name,category_id,current_price,full_price,last_modified,currently_listed) VALUES(?,?,?,?,?,?,?);"""
            db_insert(conn, sql, product)
        else:
            old_current_price, old_full_price, old_last_modified = results[0]
            if current_price != old_current_price and full_price != old_full_price:
                # atjauno produkta cenas:
                sql = f"""UPDATE products SET current_price = {current_price}, full_price = {full_price}, last_modified='{last_modified}', currently_listed=TRUE WHERE id = {id};"""  # currently_listed=TRUE
                db_update(conn=conn, sql=sql)
                # "history" tabulai pievieno vecās cenu vērtības:
                history = (
                    id,
                    old_current_price,
                    old_full_price,
                    old_last_modified,
                )
                sql = f"""INSERT INTO history (product_id,current_price,full_price,date) VALUES(?,?,?,?);"""
                db_insert(conn, sql, history)
            else:
                sql = f"""UPDATE products SET currently_listed=TRUE WHERE id={id};"""
                db_update(conn=conn, sql=sql)
    print("UPDATED: products")
    conn.close()
    print("FINISHED: scrape_rimi_lv")


if __name__ == "__main__":
    scrape_rimi_lv()
