"""Страница корзины -- Page Object."""
from selenium.webdriver.common.by import By

from .base_page import BasePage


class CartPage(BasePage):
    CART_ROWS = (By.CSS_SELECTOR, "#cart-table tbody tr.cart-row")
    CART_EMPTY = (By.ID, "cart-empty")
    TOTAL = (By.ID, "cart-total")
    CLEAR_BTN = (By.ID, "clear-cart-btn")
    CHECKOUT_BTN = (By.ID, "checkout-btn")
    CART_COUNT = (By.ID, "cart-count")

    def open(self):
        return super().open("/cart")

    def row_count(self):
        return len(self.find_all(self.CART_ROWS))

    def is_empty(self):
        return len(self.find_all(self.CART_EMPTY)) > 0

    def total(self):
        return self.text_of(self.TOTAL)

    def header_cart_count(self):
        return self.text_of(self.CART_COUNT)

    def first_row(self):
        return self.find_all(self.CART_ROWS)[0]

    def first_row_sum(self):
        row = self.first_row()
        return row.find_element(By.CSS_SELECTOR, ".row-sum").text.strip()

    def first_row_input(self):
        return self.first_row().find_element(By.CSS_SELECTOR, ".qty-input")

    def remove_first_row(self):
        self.first_row().find_element(
            By.CSS_SELECTOR, "form[action*='remove'] button").click()
        return self

    def clear_with_confirm(self, accept=True):
        """Нажимает «Очистить корзину»: появляется модальное окно confirm(),
        работаем с ним через driver.switch_to.alert (лекция 6)."""
        self.click(self.CLEAR_BTN)
        alert = self.driver.switch_to.alert
        text = alert.text
        if accept:
            alert.accept()
        else:
            alert.dismiss()
        return text

    def go_to_checkout(self):
        self.click(self.CHECKOUT_BTN)
        from .checkout_page import CheckoutPage
        return CheckoutPage(self.driver)
