import sqlite3
import os


# izvada datubāzes konektoru:
def db_create_connection(filename):
    conn = sqlite3.connect(filename)
    return conn


# vajag norādīt datubāzes konektoru (efektīvāk/ātrāk veicot vairākas SQL komandas pēc kārtas):
def db_get(conn, sql):
    try:
        cur = conn.cursor()
        cur.execute("pragma encoding=UTF8")
        cur.execute(sql)
        result = cur.fetchall()
        return result
    except Exception as e:
        print(sql)
        raise Exception(e)


def db_update(conn, sql):
    try:
        cur = conn.cursor()
        cur.execute("pragma encoding=UTF8")
        cur.execute(sql)
        conn.commit()
    except Exception as e:
        print(sql)
        raise Exception(e)


def db_insert(conn, sql, values):
    try:
        cur = conn.cursor()
        cur.execute("pragma encoding=UTF8")
        cur.execute(sql, values)
        conn.commit()
    except Exception as e:
        print(sql)
        raise Exception(e)


# izveido datubāzes tabulu struktūru:
def db_create(filename):
    conn = db_create_connection(filename)

    # galvenās kategorijas:
    sql = """
    CREATE TABLE main_categories(
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL
    );
    """
    db_update(conn, sql)

    # apakškategorijas:
    sql = """
    CREATE TABLE subcategories(
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        main_category_id,
        FOREIGN KEY(main_category_id) REFERENCES main_categories(id)
    );
    """
    db_update(conn, sql)

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
    db_update(conn, sql)

    conn.close()


if __name__ == "__main__":
    # izveido Rimi lv un lt datubāzes failus ar tabulām:
    filenames = ["rimi_lv.db", "rimi_lt.db"]
    for filename in filenames:
        if not os.path.exists(filename):
            db_create(filename)

    # testi:
    filename = "rimi_lt.db"
    conn = db_create_connection(filename)

    sql = """SELECT * FROM main_categories;"""
    results = db_get(conn, sql)
    if results:
        print(len(results))
        print(results[0])

    sql = """SELECT * FROM subcategories;"""
    results = db_get(conn, sql)
    if results:
        print(len(results))
        print(results[0])

    sql = """SELECT * FROM products;"""
    results = db_get(conn, sql)
    if results:
        print(len(results))
        print(results[0])

    conn.close()
