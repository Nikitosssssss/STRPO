"""Валидация данных формы заказа с помощью модуля re (лекция 1: регулярные выражения).

Демонстрируемые приёмы из лекции:
  * символьные классы и метасимволы (\\d, \\s, [А-ЯЁ]);
  * квантификаторы ({3}, +, *, ?);
  * группировки и извлечение частей строки (m.groups());
  * именованные группы (?P<...>);
  * «просмотр вперёд» (?=...) -- lookahead;
  * re.match / re.fullmatch / re.sub / re.search.
"""
import re
from datetime import datetime

# Имя: минимум два слова, каждое с заглавной буквы (кириллица или латиница),
# допустим дефис в фамилиях типа "Рождественская-Кузнецова".
# Квантификатор {2,} -- два и более повтора, скобки с ?: -- несохраняющая группа.
NAME_RE = re.compile(
    r"^[А-ЯЁA-Z][а-яёa-z]+(?:-[А-ЯЁA-Z][а-яёa-z]+)?"
    r"(?:\s+[А-ЯЁA-Z][а-яёa-z]+(?:-[А-ЯЁA-Z][а-яёa-z]+)?)+$"
)

# Телефон в «человекочитаемом» формате: +7(999)123-45-67.
# \\d{3} -- ровно три цифры, \\d{2} -- ровно две; экранированные скобки.
PHONE_RE = re.compile(r"^\+7\(\d{3}\)\d{3}-\d{2}-\d{2}$")

# «Мягкий» шаблон телефона с именованными группами: используется функцией
# normalize_phone, чтобы привести записи вида 8 999 123 45 67 к единому виду.
PHONE_LOOSE_RE = re.compile(
    r"^\+?(?P<country>[78])\D*(?P<code>\d{3})\D*(?P<a>\d{3})\D*(?P<b>\d{2})\D*(?P<c>\d{2})$"
)

# Email: символьный класс с перечислением, квантификаторы + и {2,},
# экранированная точка перед доменом верхнего уровня.
EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$")

# Дата доставки в формате ДД.ММ.ГГГГ.
DATE_RE = re.compile(r"^(?P<day>\d{2})\.(?P<month>\d{2})\.(?P<year>\d{4})$")

# Количество товара: 1-99, негативный «просмотр вперёд» (?!0) запрещает
# ведущий ноль вида 01 или 0 -- приём lookahead из лекции 1.
QUANTITY_RE = re.compile(r"^(?!0)\d{1,2}$")

# Комментарий необязателен, но не длиннее 500 символов.
COMMENT_MAX_LEN = 500


def normalize_phone(raw):
    """Приводит телефон почти в любом формате к +7(999)123-45-67.

    Извлекает части номера именованными группами (?P<...>) и собирает строку
    заново -- приём «группировки» из лекции 1.
    """
    m = PHONE_LOOSE_RE.match(raw.strip())
    if not m:
        return None
    parts = m.groupdict()
    return "+7({code}){a}-{b}-{c}".format(**parts)


def is_valid_name(value):
    return bool(NAME_RE.fullmatch(value.strip()))


def is_valid_phone(value):
    return bool(PHONE_RE.fullmatch(value.strip()))


def is_valid_email(value):
    return bool(EMAIL_RE.fullmatch(value.strip()))


def is_valid_date(value):
    """Проверяет формат ДД.ММ.ГГГГ регулярным выражением и корректность
    даты средствами стандартной библиотеки (regex не умеет сравнивать числа)."""
    m = DATE_RE.fullmatch(value.strip())
    if not m:
        return False
    try:
        datetime.strptime(value.strip(), "%d.%m.%Y")
    except ValueError:
        return False
    return True


def is_valid_quantity(value):
    return bool(QUANTITY_RE.fullmatch(str(value).strip()))


def validate_checkout(data):
    """Проверяет словарь данных формы заказа.

    Возвращает (clean_data, errors), где errors -- словарь
    'поле -> текст ошибки для пользователя'.
    """
    errors = {}

    name = (data.get("name") or "").strip()
    phone_raw = (data.get("phone") or "").strip()
    email = (data.get("email") or "").strip()
    address = (data.get("address") or "").strip()
    delivery_date = (data.get("delivery_date") or "").strip()
    delivery_slot = (data.get("delivery_slot") or "").strip()
    delivery_type = data.get("delivery_type") or "delivery"
    comment = (data.get("comment") or "").strip()

    if not is_valid_name(name):
        errors["name"] = ("Укажите фамилию и имя с заглавной буквы, "
                          "например: Иванов Иван")
    else:
        # re.sub: сжимаем повторные пробелы между словами имени.
        name = re.sub(r"\s+", " ", name)

    phone = normalize_phone(phone_raw) or phone_raw
    if not is_valid_phone(phone):
        errors["phone"] = "Телефон в формате +7(999)123-45-67"
    if not is_valid_email(email):
        errors["email"] = "Некорректный e-mail, например user@mail.ru"

    if delivery_type == "delivery" and len(address) < 5:
        errors["address"] = "Для доставки укажите адрес (минимум 5 символов)"
    if delivery_type == "pickup":
        address = "Самовывоз: ул. Ленина, 42"

    if not is_valid_date(delivery_date):
        errors["delivery_date"] = "Дата в формате ДД.ММ.ГГГГ"
    if delivery_slot not in ("10:00-14:00", "14:00-18:00", "18:00-22:00"):
        errors["delivery_slot"] = "Выберите интервал доставки"

    if len(comment) > COMMENT_MAX_LEN:
        errors["comment"] = f"Комментарий длиннее {COMMENT_MAX_LEN} символов"

    clean = {
        "name": name,
        "phone": phone,
        "email": email,
        "address": address,
        "delivery_date": delivery_date,
        "delivery_slot": delivery_slot,
        "delivery_type": delivery_type,
        "comment": comment,
    }
    return clean, errors
