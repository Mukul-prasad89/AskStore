import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "store.db")


def get_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def create_tables():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS brands (
            brand_id INTEGER PRIMARY KEY AUTOINCREMENT,
            brand_name TEXT NOT NULL UNIQUE
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS t_shirts (
            tshirt_id INTEGER PRIMARY KEY AUTOINCREMENT,
            brand_id INTEGER NOT NULL,
            product_name TEXT NOT NULL,
            size TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            FOREIGN KEY (brand_id) REFERENCES brands(brand_id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pricing (
            pricing_id INTEGER PRIMARY KEY AUTOINCREMENT,
            tshirt_id INTEGER NOT NULL UNIQUE,
            price REAL NOT NULL,
            discount REAL NOT NULL DEFAULT 0,
            FOREIGN KEY (tshirt_id) REFERENCES t_shirts(tshirt_id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sales (
            sale_id INTEGER PRIMARY KEY AUTOINCREMENT,
            tshirt_id INTEGER NOT NULL,
            quantity_sold INTEGER NOT NULL,
            sale_date TEXT NOT NULL,
            FOREIGN KEY (tshirt_id) REFERENCES t_shirts(tshirt_id)
        )
    """)

    conn.commit()
    conn.close()


def seed_data():
    conn = get_connection()
    cursor = conn.cursor()

    # Check if data already exists (idempotent)
    cursor.execute("SELECT COUNT(*) FROM brands")
    if cursor.fetchone()[0] > 0:
        conn.close()
        return

    # Brands
    brands = [
        ("Jack & Jones",),
        ("Van Heusen",),
        ("Nike",),
        ("Adidas",),
    ]
    cursor.executemany("INSERT INTO brands (brand_name) VALUES (?)", brands)

    # T-Shirts
    t_shirts = [
        (1, "Classic Cotton T-Shirt", "S", 15),
        (1, "Classic Cotton T-Shirt", "M", 22),
        (1, "Classic Cotton T-Shirt", "L", 18),
        (1, "Slim Fit Polo", "M", 10),
        (1, "Slim Fit Polo", "XL", 8),
        (2, "Premium Formal T-Shirt", "S", 12),
        (2, "Premium Formal T-Shirt", "M", 20),
        (2, "Premium Formal T-Shirt", "L", 14),
        (2, "Ultra Light T-Shirt", "M", 25),
        (2, "Ultra Light T-Shirt", "XL", 11),
        (3, "Dri-FIT T-Shirt", "M", 20),
        (3, "Dri-FIT T-Shirt", "L", 12),
        (3, "Dri-FIT T-Shirt", "XL", 16),
        (3, "Sportswear Tee", "S", 18),
        (3, "Sportswear Tee", "XXL", 7),
        (4, "Essentials T-Shirt", "M", 25),
        (4, "Essentials T-Shirt", "L", 19),
        (4, "Essentials T-Shirt", "XL", 13),
        (4, "Performance Tee", "S", 9),
        (4, "Performance Tee", "XXL", 6),
    ]
    cursor.executemany(
        "INSERT INTO t_shirts (brand_id, product_name, size, quantity) VALUES (?, ?, ?, ?)",
        t_shirts,
    )

    # Pricing
    pricing = [
        (1, 1299, 10),
        (2, 1299, 10),
        (3, 1299, 10),
        (4, 1899, 15),
        (5, 1899, 15),
        (6, 1599, 20),
        (7, 1599, 20),
        (8, 1599, 20),
        (9, 999, 5),
        (10, 999, 5),
        (11, 2499, 10),
        (12, 2499, 10),
        (13, 2499, 10),
        (14, 1799, 25),
        (15, 1799, 25),
        (16, 1199, 15),
        (17, 1199, 15),
        (18, 1199, 15),
        (19, 2199, 30),
        (20, 2199, 30),
    ]
    cursor.executemany(
        "INSERT INTO pricing (tshirt_id, price, discount) VALUES (?, ?, ?)", pricing
    )

    # Sales
    sales = [
        (1, 5, "2025-07-01"),
        (2, 8, "2025-07-02"),
        (3, 3, "2025-07-03"),
        (6, 4, "2025-07-04"),
        (7, 6, "2025-07-05"),
        (11, 10, "2025-07-06"),
        (12, 7, "2025-07-07"),
        (16, 9, "2025-07-08"),
        (17, 5, "2025-07-09"),
        (4, 2, "2025-07-10"),
        (9, 11, "2025-07-11"),
        (13, 4, "2025-07-12"),
        (14, 6, "2025-07-13"),
        (19, 3, "2025-07-14"),
        (5, 1, "2025-07-15"),
        (8, 5, "2025-07-16"),
        (10, 3, "2025-07-17"),
        (15, 2, "2025-07-18"),
        (20, 4, "2025-07-19"),
        (3, 7, "2025-07-20"),
        (11, 12, "2025-07-21"),
        (16, 8, "2025-07-22"),
        (7, 3, "2025-07-23"),
        (9, 6, "2025-07-24"),
        (12, 5, "2025-07-25"),
    ]
    cursor.executemany(
        "INSERT INTO sales (tshirt_id, quantity_sold, sale_date) VALUES (?, ?, ?)",
        sales,
    )

    conn.commit()
    conn.close()


def execute_sql(sql: str) -> tuple[list[str], list[dict], int]:
    """Execute a SELECT query and return (columns, rows, row_count)."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(sql)
    columns = [desc[0] for desc in cursor.description]
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return columns, rows, len(rows)


def init_db():
    create_tables()
    seed_data()


if __name__ == "__main__":
    init_db()
    print("Database initialized and seeded.")
