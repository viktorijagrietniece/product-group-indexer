import requests
import json
from db import *
from fake_useragent import UserAgent
import time
from datetime import datetime

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
def scrape_barbora_lv_page(url, conn):
    scrape_next = True
    response = requests.get(url, headers={"user-agent": UA.random})
    if response.status_code != 200:
        if response.status_code == 504:
            # pagaida 1 sekundi un mēģina vēlreiz:
            print(f"TRYING AGAIN: {url}")
            time.sleep(1)
            return scrape_barbora_lv_page(url, conn)
        raise Exception(f"ERROR ({response.status_code}): {url}")
    # HTML parsēšana:
    text = response.text
    temp = text[
        text.rfind("window.b_productList = ") + len("window.b_productList = ") :
    ]
    json_data = json.loads(temp[: temp.find("</script>")].strip()[:-1])
    for product in json_data:
        # par kategoriju:
        category_id = product["category_id"]
        category_name = product["category_name_full_path"]
        sql = f"INSERT OR REPLACE INTO categories(id,name) VALUES (?,?);"
        db_insert(conn=conn, sql=sql, values=(category_id, category_name))

        # par zīmolui:
        brand_id = product["brand_id"]
        if brand_id:
            brand_name = product["brand_name"]
            sql = f"INSERT OR REPLACE INTO brands(id,name) VALUES (?,?);"
            db_insert(conn=conn, sql=sql, values=(brand_id, brand_name))

        # par produktu:
        id = product["id"]
        name = product["title"]
        current_price = product["units"][0]["price"]  # ir arī product['price']
        if product["units"][0].get("retail_price"):
            full_price = product["units"][0]["retail_price"]  # cena bez atlaides
        else:
            full_price = current_price
        results = db_get(
            conn=conn,
            sql=f"SELECT current_price, full_price, last_modified FROM products WHERE id={id};",
        )
        last_modified = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        currently_listed = True if product["status"] == "active" else False
        if not results:
            # jauns produkts:
            product = (
                id,
                name,
                category_id,
                current_price,
                full_price,
                last_modified,
                currently_listed,
                brand_id,
            )
            sql = f"""INSERT INTO products (id,name,category_id,current_price,full_price,last_modified,currently_listed,brand_id) VALUES(?,?,?,?,?,?,?,?);"""
            db_insert(conn, sql, product)
        else:
            # atjauno produkta cenas:
            sql = f"""UPDATE products SET current_price = {current_price}, full_price = {full_price}, last_modified='{last_modified}', currently_listed={currently_listed} WHERE id = {id};"""
            db_update(conn=conn, sql=sql)
        # history:
        history = (
            id,
            current_price,
            full_price,
            last_modified,
        )
        sql = f"""INSERT INTO history (product_id,current_price,full_price,date) VALUES(?,?,?,?);"""
        db_insert(conn, sql, history)

    if len(json_data) < 52:
        scrape_next = False
    print(f"SCRAPED: {url} ({scrape_next})")
    return scrape_next


def scrape_barbora_lv():
    filename = "barbora_lv.db"
    if not os.path.exists(filename):
        db_create_barbora(filename)

    conn = db_create_connection(filename)
    sql = f"UPDATE products SET currently_listed=FALSE;"  # no sākuma visiem ierakstiem piešķir currently_listed=FALSE
    db_update(conn=conn, sql=sql)
    # visas kategorijas:
    for url_path in URL_PATHS:
        print(f"SCRAPING: {url_path}")
        # 1. līdz pēdējai lapai kategorijā:
        i = 1
        scrape_next = True
        while scrape_next:
            url = f"https://barbora.lv{url_path}?page={i}"
            scrape_next = scrape_barbora_lv_page(url, conn)
            i += 1
    conn.close()


if __name__ == "__main__":
    scrape_barbora_lv()
