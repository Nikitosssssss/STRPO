"""Базовый класс страницы -- паттерн Page Object Model (лекция 6).

Каждая страница приложения описывается собственным классом-наследником
BasePage, который инкапсулирует поиск элементов (By.ID, By.NAME,
By.CSS_SELECTOR, By.XPATH -- приёмы из лекции 5) и действия с ними.
Тесты работают только с методами страниц и не обращаются к драйверу напрямую.
"""
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class BasePage:
    BASE_URL = "http://127.0.0.1:5001"
    CART_COUNT = (By.ID, "cart-count")   # счётчик корзины в шапке сайта

    def __init__(self, driver, timeout=5):
        self.driver = driver
        self.url = self.BASE_URL
        self.wait = WebDriverWait(driver, timeout)

    # --- Навигация ---------------------------------------------------------

    def open(self, path="/"):
        """Открывает страницу по относительному пути."""
        self.driver.get(self.url + path)
        return self

    # --- Поиск элементов (лекция 5) ----------------------------------------

    def find(self, locator):
        """locator -- кортеж (By.XXX, 'значение')."""
        return self.driver.find_element(*locator)

    def find_all(self, locator):
        return self.driver.find_elements(*locator)

    def wait_visible(self, locator):
        """Явное ожидание появления элемента (лекция 6: WebDriverWait)."""
        return self.wait.until(EC.visibility_of_element_located(locator))

    # --- Типовые действия ---------------------------------------------------

    def click(self, locator):
        self.wait_visible(locator)
        self.find(locator).click()

    def type_into(self, locator, text):
        """Очищает поле и вводит текст (send_keys -- лекция 5)."""
        field = self.wait_visible(locator)
        field.clear()
        field.send_keys(text)

    def text_of(self, locator):
        return self.find(locator).text.strip()

    def attribute_of(self, locator, name):
        """Метод get_attribute -- лекция 6."""
        return self.find(locator).get_attribute(name)

    def header_cart_count(self):
        """Счётчик корзины в шапке доступен с любой страницы."""
        return self.text_of(self.CART_COUNT)
