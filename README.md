# Сладкий дом — интернет-магазин тортов

Учебный веб-проект по курсу «Современные технологии разработки
программного обеспечения». Python + Flask + SQLite, корзина в сессии,
валидация форм регулярными выражениями, автотесты Selenium + Page Object
Model, юнит-тесты pytest/unittest. Внешних интеграций нет.

## Быстрый старт

```bash
# 1. Виртуальное окружение (Windows PowerShell)
python -m venv .venv
.venv\Scripts\activate

# 2. Зависимости
pip install -r requirements.txt

# 3. Запуск (база данных создаётся и наполняется автоматически)
python app.py
```

Приложение: http://127.0.0.1:5000

## Тесты

```bash
# Юнит-тесты валидации (pytest; совместимо с unittest)
pytest tests\test_validation.py -v

# Selenium-тесты сценария заказа (unittest; браузер Edge в headless-режиме)
python -m unittest discover -s tests\selenium_tests -v
```

## Структура проекта

```
app.py                  маршруты Flask, корзина в сессии
database.py             слой SQLite: схема, каталог, заказы
validation.py           регулярные выражения для проверки формы заказа
templates/              шаблоны Jinja2 (наследование от base.html)
static/css/style.css    стили
tests/test_validation.py            юнит-тесты (pytest/unittest)
tests/selenium_tests/pages/         Page Object Model
tests/selenium_tests/test_order_flow.py   сценарные Selenium-тесты
ОТЧЕТ_О_РАЗРАБОТКЕ.md   документация лекционных приёмов с примерами кода
```
