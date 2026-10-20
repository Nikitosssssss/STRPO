"""Сценарные автотесты магазина на Selenium WebDriver (лекции 5-6).

Покрытые лекционные приёмы:
  * запуск браузера через webdriver (здесь Edge -- Chromium-движок,
    ChromeDriver скачивается автоматически Selenium Manager'ом);
  * неявные (implicitly_wait) и явные (WebDriverWait) ожидания;
  * поиск элементов: By.ID, By.NAME, By.CSS_SELECTOR, By.XPATH;
  * работа с формами: input, checkbox, radiobutton, select;
  * get_attribute и execute_script;
  * модальные окна (switch_to.alert);
  * тестовый фреймворк unittest; тесты также совместимы с pytest;
  * Page Object Model (страницы в пакете pages/).

Запуск (сервер приложения поднимается тестами автоматически на порту 5001):
    python -m unittest discover -s tests\\selenium_tests -v
"""
import os
import socket
import sys
import threading
import time
import unittest
import urllib.request

from selenium import webdriver

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))


def _free_port():
    """Просим ОС выделить свободный порт (bind на порт 0)."""
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


PORT = _free_port()
BASE_URL = f"http://127.0.0.1:{PORT}"

_server_started = False


def start_app_server():
    """Запускает Flask-приложение в фоновом потоке (один раз на процесс тестов)."""
    global _server_started
    if _server_started:
        return

    from app import app

    thread = threading.Thread(
        target=lambda: app.run(host="127.0.0.1", port=PORT, threaded=True,
                               debug=False, use_reloader=False),
        daemon=True,
    )
    thread.start()
    # Ждём готовности сервера: OSError -- общий предок URLError и TimeoutError.
    for _ in range(100):
        try:
            urllib.request.urlopen(BASE_URL, timeout=3)
            _server_started = True
            return
        except OSError:
            time.sleep(0.2)
    raise RuntimeError("Сервер приложения не поднялся")


class CakeShopTestCase(unittest.TestCase):
    """Общая фикстура: сервер + браузер один раз на класс тестов."""

    @classmethod
    def setUpClass(cls):
        # Адрес сервера для всех Page Object'ов.
        from tests.selenium_tests.pages.base_page import BasePage
        BasePage.BASE_URL = BASE_URL

        start_app_server()

        # Браузер: Edge (Chromium). Selenium Manager сам подбирает драйвер --
        # вручную chromedriver.exe в PATH класть не нужно (в лекции 5
        # показана ручная установка, здесь используется автоматическая).
        options = webdriver.EdgeOptions()
        options.add_argument("--headless=new")
        options.add_argument("--window-size=1280,900")
        cls.driver = webdriver.Edge(options=options)
        cls.driver.implicitly_wait(5)   # неявное ожидание -- лекция 5

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()

    def setUp(self):
        # Каждый тест начинается с чистой сессии (пустая корзина).
        self.driver.delete_all_cookies()


class TestCatalogPage(CakeShopTestCase):

    def test_catalog_shows_all_products(self):
        from tests.selenium_tests.pages.catalog_page import CatalogPage
        catalog = CatalogPage(self.driver).open()
        self.assertGreaterEqual(catalog.product_count(), 9)

    def test_search_by_name(self):
        from tests.selenium_tests.pages.catalog_page import CatalogPage
        catalog = CatalogPage(self.driver).open().search("Наполеон")
        names = catalog.product_names()
        self.assertEqual(len(names), 1)
        self.assertIn("Наполеон классический", names[0])

    def test_search_without_results(self):
        from tests.selenium_tests.pages.catalog_page import CatalogPage
        catalog = CatalogPage(self.driver).open().search("пицца")
        self.assertEqual(catalog.product_count(), 0)

    def test_filter_by_category(self):
        from tests.selenium_tests.pages.catalog_page import CatalogPage
        catalog = CatalogPage(self.driver).open().select_category("Чизкейки")
        self.assertEqual(catalog.product_count(), 2)
        for name in catalog.product_names():
            self.assertIn("Чизкейк", name)


class TestProductAndCart(CakeShopTestCase):

    def test_add_to_cart_with_quantity(self):
        from tests.selenium_tests.pages.catalog_page import CatalogPage
        catalog = CatalogPage(self.driver).open()
        product = catalog.open_product_by_name("Наполеон классический")
        self.assertEqual(product.product_name(), "Наполеон классический")

        product.set_quantity(2)
        # get_attribute: значение поля ввода читается атрибутом value.
        self.assertEqual(product.quantity_value(), "2")

        cart = product.add_to_cart()
        self.assertEqual(cart.row_count(), 1)
        self.assertEqual(cart.header_cart_count(), "2")
        self.assertEqual(cart.total(), "4800 ₽")

    def test_add_from_catalog_stays_on_catalog(self):
        """Добавление из каталога не открывает корзину: пользователь
        остаётся на той же странице, подтверждение -- flash-сообщение."""
        from tests.selenium_tests.pages.catalog_page import CatalogPage
        catalog = CatalogPage(self.driver).open()
        flash_text = catalog.add_first_to_cart()
        self.assertIn("добавлен в корзину", flash_text)
        self.assertIn("/catalog", self.driver.current_url)
        self.assertEqual(catalog.header_cart_count(), "1")

    def test_remove_item_from_cart(self):
        from tests.selenium_tests.pages.catalog_page import CatalogPage
        cart = CatalogPage(self.driver).open() \
            .open_product_by_name("Медовик") \
            .add_to_cart()
        self.assertEqual(cart.row_count(), 1)
        cart.remove_first_row()
        self.assertTrue(cart.is_empty())

    def test_clear_cart_accepts_confirm_dialog(self):
        """Модальное окно confirm() обрабатывается через switch_to.alert."""
        from tests.selenium_tests.pages.catalog_page import CatalogPage
        cart = CatalogPage(self.driver).open() \
            .open_product_by_name("Медовик") \
            .add_to_cart()
        dialog_text = cart.clear_with_confirm(accept=True)
        self.assertIn("Очистить корзину", dialog_text)
        self.assertTrue(cart.is_empty())

    def test_clear_cart_dismiss_keeps_items(self):
        from tests.selenium_tests.pages.catalog_page import CatalogPage
        cart = CatalogPage(self.driver).open() \
            .open_product_by_name("Медовик") \
            .add_to_cart()
        cart.clear_with_confirm(accept=False)
        self.assertEqual(cart.row_count(), 1)

    def test_cart_row_recalc_via_execute_script(self):
        """execute_script: вызываем клиентскую функцию пересчёта суммы строки."""
        from tests.selenium_tests.pages.catalog_page import CatalogPage
        cart = CatalogPage(self.driver).open() \
            .open_product_by_name("Наполеон классический") \
            .add_to_cart()
        self.assertEqual(cart.first_row_sum(), "2400 ₽")

        row = cart.first_row()
        self.driver.execute_script(
            "var row = arguments[0];"
            "var input = row.querySelector('.qty-input');"
            "input.value = '3';"
            "recalcRow(row);",
            row,
        )
        self.assertEqual(cart.first_row_sum(), "7200 ₽")


class TestCheckout(CakeShopTestCase):

    def _cart_with_items(self):
        from tests.selenium_tests.pages.catalog_page import CatalogPage
        return CatalogPage(self.driver).open() \
            .open_product_by_name("Наполеон классический") \
            .set_quantity(1) \
            .add_to_cart()

    def test_full_order_flow(self):
        cart = self._cart_with_items()
        checkout = cart.go_to_checkout()

        # checkbox «согласие» не отмечен до клика (лекция 6: is_selected)
        self.assertFalse(checkout.agree_is_selected())

        checkout.fill_valid_form().submit()
        self.assertIn("оформлен", checkout.success_title())

    def test_pickup_radio_disables_address_requirement(self):
        from tests.selenium_tests.pages.catalog_page import CatalogPage
        checkout = CatalogPage(self.driver).open() \
            .open_product_by_name("Медовик") \
            .add_to_cart() \
            .go_to_checkout()
        checkout.choose_pickup()

        from tests.selenium_tests.pages.checkout_page import CheckoutPage
        self.assertTrue(checkout.find(CheckoutPage.RADIO_PICKUP).is_selected())

        checkout.type_into(CheckoutPage.NAME, "Петрова Анна")
        checkout.type_into(CheckoutPage.PHONE, "+7(913)555-01-02")
        checkout.type_into(CheckoutPage.EMAIL, "anna@yandex.ru")
        checkout.type_into(CheckoutPage.DATE, "26.12.2026")
        checkout.select_slot("18:00-22:00")
        checkout.find(CheckoutPage.AGREE).click()
        checkout.submit()
        self.assertIn("оформлен", checkout.success_title())

    def test_invalid_form_shows_errors(self):
        checkout = self._cart_with_items().go_to_checkout()
        # Отправляем пустую форму: серверная валидация (regex) должна
        # вернуть ошибки для каждого некорректного поля.
        checkout.submit()
        errors = " | ".join(checkout.error_messages())
        for fragment in ("фамилию и имя", "Телефон", "e-mail", "адрес", "ДД.ММ.ГГГГ"):
            self.assertIn(fragment, errors)


if __name__ == "__main__":
    unittest.main()
