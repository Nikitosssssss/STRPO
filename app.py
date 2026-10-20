"""Интернет-магазин тортов -- учебное веб-приложение на Flask.

Запуск:  python app.py  ->  http://127.0.0.1:5000
"""
from flask import (
    Flask, abort, flash, g, redirect, render_template, request, session, url_for,
)

import database as db
from validation import is_valid_quantity

DELIVERY_COST = 300          # стоимость доставки, руб.
PICKUP_COST = 0              # самовывоз бесплатный


def create_app():
    app = Flask(__name__)
    app.secret_key = "cake-shop-demo-secret-key"  # для сессий и flash-сообщений

    app.teardown_appcontext(db.close_connection)
    with app.app_context():
        db.init_db()                          # создаём БД при первом запуске

    return app


app = create_app()


# ---------- Вспомогательные функции для корзины (хранится в сессии) ---------

def get_cart():
    """Корзина -- словарь {product_id (str): количество} в сессии Flask."""
    return session.get("cart", {})


def cart_details():
    """Присоединяет к корзине данные товаров и считает суммы."""
    cart = get_cart()
    products = db.products_by_ids(db.get_connection(), [int(k) for k in cart])
    items = [
        {"product": p, "quantity": cart[str(p["id"])],
         "sum": p["price"] * cart[str(p["id"])]}
        for p in products
    ]
    items_total = sum(i["sum"] for i in items)
    count = sum(i["quantity"] for i in items)
    return items, items_total, count


@app.context_processor
def inject_cart_count():
    """Количество товаров в корзине доступно во всех шаблонах (в т.ч. в меню)."""
    _, _, count = cart_details()
    return {"cart_count": count}


# ------------------------------- Маршруты ------------------------------------

@app.route("/")
def index():
    """Главная страница: приветствие и ссылки на каталог."""
    products = db.find_products(db.get_connection())
    featured = products[:3]
    return render_template("index.html", featured=featured)


@app.route("/catalog")
def catalog():
    """Каталог с фильтром по категории и текстовым поиском."""
    query = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip()
    products = db.find_products(db.get_connection(), query or None,
                                category or None)
    categories = db.all_categories(db.get_connection())
    return render_template("catalog.html", products=products,
                           categories=categories, query=query,
                           category=category)


@app.route("/product/<int:product_id>")
def product(product_id):
    """Страница товара с формой добавления в корзину."""
    item = db.get_product(db.get_connection(), product_id)
    if item is None:
        abort(404)
    return render_template("product.html", product=item)


@app.post("/cart/add/<int:product_id>")
def cart_add(product_id):
    """Добавление товара в корзину (POST-форма со страницы товара)."""
    item = db.get_product(db.get_connection(), product_id)
    if item is None:
        abort(404)

    quantity_raw = request.form.get("quantity", "1")
    if not is_valid_quantity(quantity_raw):
        flash("Количество -- целое число от 1 до 99", "error")
        return redirect(url_for("product", product_id=product_id))

    cart = get_cart()
    key = str(product_id)
    cart[key] = min(cart.get(key, 0) + int(quantity_raw), 99)
    session["cart"] = cart
    session.modified = True
    flash(f"«{item['name']}» добавлен в корзину", "success")
    return redirect(url_for("cart"))


@app.route("/cart")
def cart():
    """Содержимое корзины."""
    items, items_total, _ = cart_details()
    return render_template("cart.html", items=items, items_total=items_total)


@app.post("/cart/update")
def cart_update():
    """Изменение количества одного товара (POST из корзины)."""
    product_id = request.form.get("product_id", "")
    quantity_raw = request.form.get("quantity", "0")

    cart = get_cart()
    if product_id in cart and is_valid_quantity(quantity_raw):
        cart[product_id] = int(quantity_raw)
        session["cart"] = cart
        session.modified = True
    flash("Корзина обновлена", "success")
    return redirect(url_for("cart"))


@app.post("/cart/remove/<int:product_id>")
def cart_remove(product_id):
    """Удаление товара из корзины."""
    cart = get_cart()
    cart.pop(str(product_id), None)
    session["cart"] = cart
    session.modified = True
    flash("Товар удалён из корзины", "success")
    return redirect(url_for("cart"))


@app.post("/cart/clear")
def cart_clear():
    """Полная очистка корзины."""
    session.pop("cart", None)
    session.modified = True
    flash("Корзина очищена", "success")
    return redirect(url_for("cart"))


@app.route("/checkout", methods=["GET", "POST"])
def checkout():
    """Оформление заказа: показывает форму, затем валидирует и сохраняет."""
    items, items_total, _ = cart_details()
    if not items:
        flash("Корзина пуста -- сначала выберите торты в каталоге", "error")
        return redirect(url_for("catalog"))

    if request.method == "POST":
        from validation import validate_checkout
        clean, errors = validate_checkout(request.form)

        delivery_cost = (DELIVERY_COST
                         if clean["delivery_type"] == "delivery" else PICKUP_COST)
        clean["delivery_cost"] = delivery_cost

        if errors:
            for field, message in errors.items():
                flash(message, "error")
            return render_template("checkout.html", form=clean,
                                   items=items, items_total=items_total,
                                   delivery_cost=delivery_cost), 400

        order_items = [(i["product"], i["quantity"]) for i in items]
        order_id = db.create_order(db.get_connection(), clean,
                                   order_items, items_total, delivery_cost)
        session.pop("cart", None)          # корзина обнуляется после заказа
        session.modified = True
        return redirect(url_for("order_success", order_id=order_id))

    # GET: форма с значениями по умолчанию
    form = {"delivery_type": "delivery", "delivery_slot": "10:00-14:00"}
    return render_template("checkout.html", form=form, items=items,
                           items_total=items_total, delivery_cost=DELIVERY_COST)


@app.route("/order/<int:order_id>")
def order_success(order_id):
    """Страница успешного оформления заказа."""
    order, order_items = db.get_order(db.get_connection(), order_id)
    if order is None:
        abort(404)
    return render_template("order_success.html", order=order,
                           items=order_items)


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
