import sqlite3
import os

FILENAME = "rimi_lv.db"


# izvada datubāzes konektoru:
def db_create_connection():
    conn = sqlite3.connect(FILENAME)
    return conn


# nevajag norādīt datubāzes konektoru:
def db_get(sql):
    conn = sqlite3.connect(FILENAME)
    cur = conn.cursor()
    cur.execute("pragma encoding=UTF8")
    cur.execute(sql)
    result = cur.fetchall()
    conn.close()
    return result


def db_update(sql):
    conn = sqlite3.connect(FILENAME, check_same_thread=False, timeout=10)
    conn.execute("pragma journal_mode=WAL;")
    cur = conn.cursor()
    cur.execute("pragma encoding=UTF8")
    cur.execute(sql)
    conn.commit()
    conn.close()


# vajag norādīt datubāzes konektoru (efektīvāk/ātrāk veicot vairākas SQL komandas pēc kārtas):
def db_get2(conn, sql):
    cur = conn.cursor()
    cur.execute("pragma encoding=UTF8")
    cur.execute(sql)
    result = cur.fetchall()
    return result


def db_update2(conn, sql):
    cur = conn.cursor()
    cur.execute("pragma encoding=UTF8")
    cur.execute(sql)
    conn.commit()


# izveido datubāzes tabulu struktūru:
def db_create():
    # galvenās kategorijas:
    sql = """
    CREATE TABLE main_categories(
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL
    );
    """
    db_update(sql)

    # apakškategorijas:
    sql = """
    CREATE TABLE subcategories(
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        main_category_id,
        FOREIGN KEY(main_category_id) REFERENCES main_categories(id)
    );
    """
    db_update(sql)

    # produkti:
    sql = """
    CREATE TABLE products(
        id INT PRIMARY KEY,
        name TEXT NOT NULL,
        subcategory_id TEXT NOT NULL,
        price REAL NOT NULL,
        FOREIGN KEY(subcategory_id) REFERENCES subcategories(id)
    );
    """
    db_update(sql)


if __name__ == "__main__":
    # izveido datubāzes failu ar tabulām:
    if not os.path.exists(FILENAME):
        db_create()

    # testi:
    sql = """SELECT * FROM main_categories;"""
    results = db_get(sql)
    if results:
        print(len(results))
        print(results[0])

    sql = """SELECT * FROM subcategories;"""
    results = db_get(sql)
    if results:
        print(len(results))
        print(results[0])

    sql = """SELECT * FROM products;"""
    results = db_get(sql)
    if results:
        print(len(results))
        print(results[0])
