"""Слой доступа к данным интернет-магазина тортов.

Используется SQLite -- встроенная реляционная СУБД Python (модуль sqlite3),
внешних зависимостей и интеграций не требуется (учебный проект).
"""
import os
import sqlite3

from flask import g

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "cake_shop.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS products (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL,
    category    TEXT    NOT NULL,
    description TEXT    NOT NULL,
    price       INTEGER NOT NULL,           -- цена в рублях (целое число)
    weight      TEXT    NOT NULL,           -- например, "1,2 кг"
    emoji       TEXT    NOT NULL            -- визуализация вместо картинок
);

CREATE TABLE IF NOT EXISTS orders (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_name  TEXT NOT NULL,
    phone          TEXT NOT NULL,
    email          TEXT NOT NULL,
    address        TEXT NOT NULL,
    delivery_date  TEXT NOT NULL,
    delivery_slot  TEXT NOT NULL,
    delivery_type  TEXT NOT NULL,           -- 'delivery' или 'pickup'
    comment        TEXT,
    delivery_cost  INTEGER NOT NULL,
    items_total    INTEGER NOT NULL,
    total          INTEGER NOT NULL,
    created_at     TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE TABLE IF NOT EXISTS order_items (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id     INTEGER NOT NULL REFERENCES orders(id),
    product_id   INTEGER NOT NULL REFERENCES products(id),
    product_name TEXT    NOT NULL,
    quantity     INTEGER NOT NULL,
    price        INTEGER NOT NULL
);
"""

# Демонстрационные товары, которыми заполняется пустая база при первом запуске.
SEED_PRODUCTS = [
    ("Наполеон классический", "Классика",
     "Слоёные коржи на сливочном масле, заварной крем на желтках.",
     2400, "1,5 кг", "🎂"),
    ("Медовик", "Классика",
     "Медовые коржи со сметанным кремом и карамельной крошкой.",
     2100, "1,4 кг", "🍯"),
    ("Красный бархат", "Бисквитные",
     "Красные бисквитные коржи, крем-чиз и вишнёвая прослойка.",
     2600, "1,6 кг", "❤️"),
    ("Чизкейк Нью-Йорк", "Чизкейки",
     "Песочная основа, сливочный сыр, запекание на водяной бане.",
     2300, "1,2 кг", "🧀"),
    ("Чизкейк брауни", "Чизкейки",
     "Шоколадная основа-брауни и классический чизкейк сверху.",
     2500, "1,3 кг", "🍫"),
    ("Муссовый «Три шоколада»", "Муссовые",
     "Три слоя мусса: белый, молочный и тёмный шоколад, зеркальная глазурь.",
     3100, "1,0 кг", "✨"),
    ("Муссовый «Манго-маракуйя»", "Муссовые",
     "Тропический мусс с бисквитной основой и ягодным конфи.",
     2900, "1,0 кг", "🥭"),
    ("Торт «Праздничный»", "Праздничные",
     "Бисквит, крем, декор из свежих ягод и шоколада -- под заказ.",
     3500, "2,0 кг", "🎉"),
    ("Торт «Свадебный»", "Праздничные",
     "Трёхъярусный торт с кремовым декором, вес и начинка по согласованию.",
     9000, "4,5 кг", "💍"),
]


def get_connection():
    """Возвращает соединение с БД, одно на время запроса (паттерн g во Flask)."""
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_connection(_exc=None):
    """Закрывает соединение по окончании запроса (телеметрия teardown во Flask)."""
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db(seed_if_empty=True):
    """Создаёт таблицы по схеме и заполняет демонстрационными товарами."""
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.executescript(SCHEMA)
        if seed_if_empty:
            count = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
            if count == 0:
                conn.executemany(
                    "INSERT INTO products (name, category, description, price, weight, emoji) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    SEED_PRODUCTS,
                )
        conn.commit()
    finally:
        conn.close()


# --- Запросы к каталогу -----------------------------------------------------

def all_categories(conn):
    rows = conn.execute(
        "SELECT DISTINCT category FROM products ORDER BY category"
    ).fetchall()
    return [r["category"] for r in rows]


def find_products(conn, query=None, category=None):
    """Поиск и фильтрация каталога.

    Параметр query фильтруется SQL-оператором LIKE с экранированием
    спецсимволов, category -- точное совпадение. Оба параметра необязательны.
    """
    sql = "SELECT * FROM products WHERE 1=1"
    params = []
    if category:
        sql += " AND category = ?"
        params.append(category)
    if query:
        sql += " AND (name LIKE ? ESCAPE '\\' OR description LIKE ? ESCAPE '\\')"
        like = "%" + query.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"
        params += [like, like]
    sql += " ORDER BY id"
    return conn.execute(sql, params).fetchall()


def get_product(conn, product_id):
    return conn.execute(
        "SELECT * FROM products WHERE id = ?", (product_id,)
    ).fetchone()


def products_by_ids(conn, ids):
    if not ids:
        return []
    marks = ",".join("?" * len(ids))
    return conn.execute(
        f"SELECT * FROM products WHERE id IN ({marks})", list(ids)
    ).fetchall()


# --- Заказы ------------------------------------------------------------------

def create_order(conn, form_data, items, items_total, delivery_cost):
    """Сохраняет заказ и его позиции, возвращает id созданного заказа."""
    cursor = conn.execute(
        "INSERT INTO orders (customer_name, phone, email, address, delivery_date,"
        " delivery_slot, delivery_type, comment, delivery_cost, items_total, total)"
        " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            form_data["name"], form_data["phone"], form_data["email"],
            form_data["address"], form_data["delivery_date"],
            form_data["delivery_slot"], form_data["delivery_type"],
            form_data.get("comment") or None,
            delivery_cost, items_total, items_total + delivery_cost,
        ),
    )
    order_id = cursor.lastrowid
    conn.executemany(
        "INSERT INTO order_items (order_id, product_id, product_name, quantity, price)"
        " VALUES (?, ?, ?, ?, ?)",
        [
            (order_id, p["id"], p["name"], qty, p["price"])
            for p, qty in items
        ],
    )
    conn.commit()
    return order_id


def get_order(conn, order_id):
    order = conn.execute(
        "SELECT * FROM orders WHERE id = ?", (order_id,)
    ).fetchone()
    if order is None:
        return None, []
    items = conn.execute(
        "SELECT * FROM order_items WHERE order_id = ? ORDER BY id", (order_id,)
    ).fetchall()
    return order, items
