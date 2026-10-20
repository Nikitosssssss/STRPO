"""Страница товара -- Page Object."""
from selenium.webdriver.common.by import By

from .base_page import BasePage


class ProductPage(BasePage):
    NAME = (By.ID, "product-name")
    PRICE = (By.ID, "product-price")
    QTY_INPUT = (By.ID, "quantity")
    ADD_BTN = (By.ID, "add-to-cart-btn")
    FLASH_SUCCESS = (By.CSS_SELECTOR, "#flashes .flash-success")

    def open(self, product_id=1):
        return super().open(f"/product/{product_id}")

    def product_name(self):
        return self.text_of(self.NAME)

    def product_price(self):
        return self.text_of(self.PRICE)

    def set_quantity(self, quantity):
        self.type_into(self.QTY_INPUT, str(quantity))
        return self

    def quantity_value(self):
        """Читаем атрибут value поля ввода методом get_attribute (лекция 6)."""
        return self.attribute_of(self.QTY_INPUT, "value")

    def add_to_cart(self):
        """Нажимает «Добавить в корзину»: приложение остаётся на странице
        товара, поэтому ждём flash-подтверждение, затем переходим в корзину
        явно (как покупатель по ссылке в меню)."""
        self.click(self.ADD_BTN)
        self.wait_visible(self.FLASH_SUCCESS)
        from .cart_page import CartPage
        return CartPage(self.driver).open()
