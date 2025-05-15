import json
from db import *
from datetime import datetime
import cloudscraper

# manuāli jāmaina vai jāizmanto javascript ģenerējoša metode:
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
def process_json(json_data, conn):
    scrape_next = True
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
            old_current_price, old_full_price, old_last_modified = results[0]
            if current_price != old_current_price and full_price != old_full_price:
                # atjauno produkta cenas:
                sql = f"""UPDATE products SET current_price = {current_price}, full_price = {full_price}, last_modified='{last_modified}', currently_listed={currently_listed} WHERE id = {id};"""  # currently_listed=TRUE
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
                sql = f"""UPDATE products SET currently_listed={currently_listed} WHERE id={id};"""
                db_update(conn=conn, sql=sql)
    if len(json_data) < 52:
        scrape_next = False
    return scrape_next


def scrape_barbora_lt():
    filename = "barbora_lt.db"
    if not os.path.exists(filename):
        db_create_barbora(filename)

    conn = db_create_connection(filename)
    sql = f"UPDATE products SET currently_listed=FALSE;"  # no sākuma visiem ierakstiem piešķir currently_listed=FALSE
    db_update(conn=conn, sql=sql)
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
            temp = text[
                text.rfind("window.b_productList = ") + len("window.b_productList = ") :
            ]
            json_data = json.loads(temp[: temp.find("</script>")].strip()[:-1])
            scrape_next = process_json(json_data, conn)
            print(f"SCRAPED: {url} ({scrape_next})")
            i += 1
    conn.close()


if __name__ == "__main__":
    scrape_barbora_lt()
