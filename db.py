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


# izveido Rimi datubāzes tabulu struktūru:
def db_create_rimi(filename):
    conn = db_create_connection(filename)
    """
    kategorijas:
    galvenās kategorijas (1. līmeņa) - piem. SH-2 (Augļi un dārzeņi)
    apakškategorijas (2. līmeņa) - piem. SH-2-1 (Augļi un ogas)
    apakškategorijas (3. līmeņa) - piem. SH-2-1-3 (Banāni) 
    """
    sql = """
    CREATE TABLE IF NOT EXISTS categories(
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL
    );
    """
    db_update(conn, sql)

    # produkti:
    sql = """
    CREATE TABLE IF NOT EXISTS products(
        id INT PRIMARY KEY,
        name TEXT NOT NULL,
        category_id TEXT NOT NULL,
        current_price REAL NOT NULL,
        full_price REAL NOT NULL,
        last_modified DATETIME NOT NULL,
        currently_listed BOOLEAN NOT NULL,
        FOREIGN KEY(category_id) REFERENCES categories(id)
    );
    """
    db_update(conn, sql)

    # cenu izmaiņu vēsture (neieskaitot tagadējās produktu cenas - tās tiek pievienotas "history" tabulā pēc pašreizējo cenu izmaiņām datu ieguves brīdī):
    sql = """
    CREATE TABLE IF NOT EXISTS history(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INT NOT NULL,
        current_price REAL NOT NULL,
        full_price REAL NOT NULL,
        date DATETIME NOT NULL,
        FOREIGN KEY(product_id) REFERENCES products(id)
    );
    """
    db_update(conn, sql)

    conn.close()


# izveido Barbora datubāzes tabulu struktūru:
def db_create_barbora(filename):
    conn = db_create_connection(filename)
    # kategorijas (pilnais ceļš):
    sql = """
    CREATE TABLE IF NOT EXISTS categories(
        id TEXT PRIMARY KEY NOT NULL,
        name TEXT NOT NULL
    );
    """
    db_update(conn, sql)

    # zīmoli:
    sql = """
    CREATE TABLE IF NOT EXISTS brands(
        id INT PRIMARY KEY NOT NULL,
        name TEXT NOT NULL
    );
    """
    db_update(conn, sql)

    # produkti:
    sql = """
    CREATE TABLE IF NOT EXISTS products(
        id INT PRIMARY KEY NOT NULL,
        name TEXT NOT NULL,
        category_id TEXT NOT NULL,
        current_price REAL NOT NULL,
        full_price REAL NOT NULL,
        last_modified DATETIME NOT NULL,
        currently_listed BOOLEAN NOT NULL,
        brand_id INT,
        FOREIGN KEY(category_id) REFERENCES categories(id),
        FOREIGN KEY(brand_id) REFERENCES brands(id)
    );
    """
    db_update(conn, sql)

    # cenu izmaiņu vēsture (neieskaitot tagadējās produktu cenas - tās tiek pievienotas "history" tabulā pēc pašreizējo cenu izmaiņām datu ieguves brīdī):
    sql = """
    CREATE TABLE IF NOT EXISTS history(
        id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
        product_id INT NOT NULL,
        current_price REAL NOT NULL,
        full_price REAL NOT NULL,
        date DATETIME NOT NULL,
        FOREIGN KEY(product_id) REFERENCES products(id)
    );
    """
    db_update(conn, sql)

    conn.close()


if __name__ == "__main__":
    # izveido Rimi lv un lt datubāzes failus ar tabulām:
    filenames = ["rimi_lv.db", "rimi_lt.db"]
    for filename in filenames:
        if not os.path.exists(filename):
            db_create_rimi(filename)

    # izveido Barbora lv un lt datubāzes failus ar tabulām:
    filenames = ["barbora_lv.db", "barbora_lt.db"]
    for filename in filenames:
        if not os.path.exists(filename):
            db_create_barbora(filename)

        # conn = db_create_connection(filename)
        # db_update(conn, "DELETE FROM brands WHERE id IS NULL;")
        # conn. close()
