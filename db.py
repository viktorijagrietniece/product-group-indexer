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
    """
    kategorijas:
    galvenās kategorijas (1. līmeņa) - piem. SH-2 (Augļi un dārzeņi)
    apakškategorijas (2. līmeņa) - piem. SH-2-1 (Augļi un ogas)
    apakškategorijas (3. līmeņa) - piem. SH-2-1-3 (Banāni) 
    """
    sql = """
    CREATE TABLE categories(
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL
    );
    """
    db_update(conn, sql)

    # produkti:
    sql = """
    CREATE TABLE products(
        id INT PRIMARY KEY,
        name TEXT NOT NULL,
        category_id TEXT NOT NULL,
        price REAL NOT NULL,
        FOREIGN KEY(category_id) REFERENCES categories(id)
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

    # testi (daudzums un 1. ierakts):
    print("rimi_lv.db")
    filename = "rimi_lv.db"
    conn = db_create_connection(filename)

    sql = """SELECT * FROM categories;"""
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

    # testi (daudzums un 1. ierakts):
    print("rimi_lt.db")
    filename = "rimi_lt.db"
    conn = db_create_connection(filename)

    sql = """SELECT * FROM categories;"""
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
