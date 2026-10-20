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
    ADD_FIRST_BTN = (By.CSS_SELECTOR, "#product-grid form button")
    FLASH_SUCCESS = (By.CSS_SELECTOR, "#flashes .flash-success")
    EMPTY_STATE = (By.ID, "product-grid")

    def open(self):
        return super().open("/catalog")

    def product_names(self):
        return [el.text.strip() for el in self.find_all(self.PRODUCT_NAMES)]

    def search(self, phrase):
        self.type_into(self.SEARCH_INPUT, phrase)
        self.click(self.SEARCH_BTN)
        # Страховка от редкой гонки «потерянного клика» в headless-браузере:
        # если перехода не случилось -- повторяем нажатие один раз.
        if "q=" not in self.driver.current_url:
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

    def add_first_to_cart(self):
        """Кнопка «В корзину» на карточке: после нажатия пользователь
        остаётся в каталоге -- возвращаем текст flash-подтверждения."""
        self.click(self.ADD_FIRST_BTN)
        return self.wait_visible(self.FLASH_SUCCESS).text

    def open_product_by_name(self, name):
        """Открывает страницу товара, найденного по тексту ссылки."""
        link = (By.XPATH, f"//span[@class='product-name' and text()='{name}']")
        self.click(link)
        from .product_page import ProductPage
        return ProductPage(self.driver)
