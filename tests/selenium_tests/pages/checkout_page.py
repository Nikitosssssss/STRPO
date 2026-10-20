"""Страница оформления заказа -- Page Object."""
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select

from .base_page import BasePage


class CheckoutPage(BasePage):
    FORM = (By.ID, "checkout-form")
    NAME = (By.ID, "name")
    PHONE = (By.ID, "phone")
    EMAIL = (By.ID, "email")
    ADDRESS = (By.ID, "address")
    DATE = (By.ID, "delivery_date")
    SLOT = (By.ID, "delivery_slot")
    COMMENT = (By.ID, "comment")
    AGREE = (By.ID, "agree")
    RADIO_DELIVERY = (By.ID, "delivery-type-delivery")
    RADIO_PICKUP = (By.ID, "delivery-type-pickup")
    SUBMIT = (By.ID, "submit-order-btn")
    FLASH_ERRORS = (By.CSS_SELECTOR, "#flashes .flash-error")
    SUCCESS_TITLE = (By.CSS_SELECTOR, "#order-success h1")

    def open(self):
        return super().open("/checkout")

    def choose_pickup(self):
        """Работа с radiobutton (лекция 6): click по label/инпуту."""
        self.click(self.RADIO_PICKUP)
        return self

    def agree_is_selected(self):
        """Работа с checkbox (лекция 6): проверка атрибута is_selected."""
        return self.find(self.AGREE).is_selected()

    def select_slot(self, value):
        """Раскрывающийся список (лекция 6): класс Select."""
        Select(self.find(self.SLOT)).select_by_value(value)
        return self

    def fill_valid_form(self):
        self.type_into(self.NAME, "Иванов Иван")
        self.type_into(self.PHONE, "+7(999)123-45-67")
        self.type_into(self.EMAIL, "ivanov@mail.ru")
        self.type_into(self.ADDRESS, "ул. Ленина, д. 42, кв. 10")
        self.type_into(self.DATE, "25.12.2026")
        self.select_slot("14:00-18:00")
        self.find(self.AGREE).click()
        return self

    def submit(self):
        self.click(self.SUBMIT)
        return self

    def error_messages(self):
        return [el.text.strip() for el in self.find_all(self.FLASH_ERRORS)]

    def success_title(self):
        return self.text_of(self.SUCCESS_TITLE)
