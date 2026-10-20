"""Юнит-тесты модуля validation (лекция 6: unittest и pytest).

Файл написан в стиле unittest (классы, self.assertEqual) -- как в лекции,
-- но запускается и через pytest, что демонстрирует их совместимость
(pytest обратно совместим с unittest).
"""
import sys
import os
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from validation import (
    is_valid_name, is_valid_phone, is_valid_email, is_valid_date,
    is_valid_quantity, normalize_phone, validate_checkout,
)


class TestNameValidation(unittest.TestCase):

    def test_valid_full_name(self):
        self.assertTrue(is_valid_name("Иванов Иван"))

    def test_valid_three_words_and_hyphen(self):
        self.assertTrue(is_valid_name("Рождественская-Кузнецова Анна Петровна"))

    def test_single_word_is_invalid(self):
        self.assertFalse(is_valid_name("Иван"))

    def test_lowercase_is_invalid(self):
        self.assertFalse(is_valid_name("иванов иван"))

    def test_digits_are_invalid(self):
        self.assertFalse(is_valid_name("Иванов123 Иван"))


class TestPhoneValidation(unittest.TestCase):

    def test_valid_phone(self):
        self.assertTrue(is_valid_phone("+7(999)123-45-67"))

    def test_missing_plus_is_invalid(self):
        self.assertFalse(is_valid_phone("8(999)123-45-67"))

    def test_normalize_loose_formats(self):
        self.assertEqual(normalize_phone("8 999 123 45 67"), "+7(999)123-45-67")
        self.assertEqual(normalize_phone("+7-999-123-45-67"), "+7(999)123-45-67")
        self.assertEqual(normalize_phone("+7(999)1234567"), "+7(999)123-45-67")

    def test_normalize_garbage_returns_none(self):
        self.assertIsNone(normalize_phone("звоните в телеграм"))


class TestEmailValidation(unittest.TestCase):

    def test_valid_emails(self):
        for email in ("user@mail.ru", "anna.petrova@company.org", "a+b@sub.domain.com"):
            with self.subTest(email=email):
                self.assertTrue(is_valid_email(email))

    def test_invalid_emails(self):
        for email in ("user@mail", "user@@mail.ru", "@mail.ru", "user mail.ru"):
            with self.subTest(email=email):
                self.assertFalse(is_valid_email(email))


class TestDateValidation(unittest.TestCase):

    def test_valid_date(self):
        self.assertTrue(is_valid_date("25.12.2026"))

    def test_format_check(self):
        self.assertFalse(is_valid_date("2026.12.25"))
        self.assertFalse(is_valid_date("25/12/2026"))

    def test_semantic_check(self):
        # Формат верный (ДД.ММ.ГГГГ), но 31 февраля не существует.
        self.assertFalse(is_valid_date("31.02.2026"))


class TestQuantityValidation(unittest.TestCase):

    def test_valid_quantities(self):
        for q in ("1", "5", "99"):
            with self.subTest(q=q):
                self.assertTrue(is_valid_quantity(q))

    def test_leading_zero_is_invalid(self):
        # Негативный lookahead (?!0\d) из лекции 1.
        self.assertFalse(is_valid_quantity("01"))

    def test_out_of_range_is_invalid(self):
        self.assertFalse(is_valid_quantity("0"))
        self.assertFalse(is_valid_quantity("100"))


class TestValidateCheckout(unittest.TestCase):

    VALID = {
        "name": "Иванов Иван",
        "phone": "+7(999)123-45-67",
        "email": "ivanov@mail.ru",
        "address": "ул. Ленина, 42",
        "delivery_date": "25.12.2026",
        "delivery_slot": "10:00-14:00",
        "delivery_type": "delivery",
        "comment": "",
    }

    def test_valid_form_has_no_errors(self):
        clean, errors = validate_checkout(self.VALID)
        self.assertEqual(errors, {})
        self.assertEqual(clean["phone"], "+7(999)123-45-67")

    def test_phone_is_normalized_before_save(self):
        data = dict(self.VALID, phone="8 999 123 45 67")
        clean, errors = validate_checkout(data)
        self.assertEqual(errors, {})
        self.assertEqual(clean["phone"], "+7(999)123-45-67")

    def test_pickup_replaces_address(self):
        data = dict(self.VALID, delivery_type="pickup", address="")
        clean, errors = validate_checkout(data)
        self.assertEqual(errors, {})
        self.assertTrue(clean["address"].startswith("Самовывоз"))

    def test_errors_are_reported_per_field(self):
        data = dict(self.VALID, name="иван", phone="123", email="bad")
        _, errors = validate_checkout(data)
        self.assertEqual(set(errors), {"name", "phone", "email"})

    def test_double_spaces_in_name_are_squeezed(self):
        data = dict(self.VALID, name="Иванов    Иван")
        clean, errors = validate_checkout(data)
        self.assertEqual(errors, {})
        self.assertEqual(clean["name"], "Иванов Иван")


if __name__ == "__main__":
    unittest.main()
