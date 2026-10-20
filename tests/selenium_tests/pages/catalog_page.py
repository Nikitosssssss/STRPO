"""Страница каталога -- Page Object."""
from selenium.webdriver.common.by import By

from .base_page import BasePage


class CatalogPage(BasePage):
    # Локаторы собраны в одном месте: при изменении вёрстки правим только здесь.
    SEARCH_INPUT = (By.ID, "search-input")
    CATEGORY_SELECT = (By.ID, "category-select")
    SEARCH_BTN = (By.ID, "search-btn")
    PRODUCT_CARDS = (By.CSS_SELECTOR, "#product-grid .product-card")
    PRODUCT_NAMES = (By.CSS_SELECTOR, "#product-grid .product-name")
    EMPTY_STATE = (By.ID, "product-grid")

    def open(self):
        return super().open("/catalog")

    def product_names(self):
        return [el.text.strip() for el in self.find_all(self.PRODUCT_NAMES)]

    def search(self, phrase):
        self.type_into(self.SEARCH_INPUT, phrase)
        self.click(self.SEARCH_BTN)
        return self

    def select_category(self, category):
        select = self.find(self.CATEGORY_SELECT)
        for option in select.find_elements(By.TAG_NAME, "option"):
            if option.text == category:
                option.click()
                break
        self.click(self.SEARCH_BTN)
        return self

    def product_count(self):
        return len(self.find_all(self.PRODUCT_CARDS))

    def open_product_by_name(self, name):
        """Открывает страницу товара, найденного по тексту ссылки."""
        link = (By.XPATH, f"//span[@class='product-name' and text()='{name}']")
        self.click(link)
        from .product_page import ProductPage
        return ProductPage(self.driver)
