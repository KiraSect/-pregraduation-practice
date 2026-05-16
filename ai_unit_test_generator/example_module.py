import re

def normalize_email(email):
    if not isinstance(email, str):
        raise TypeError("email должен быть строкой")
    email = email.strip().lower()
    if "@" not in email:
        raise ValueError("некорректный email")
    return email

def calculate_discount(price, percent):
    if price < 0 or percent < 0:
        raise ValueError("значения должны быть положительными")
    return round(price - (price * percent / 100), 2)

def extract_hashtags(text):
    if not text:
        return []
    return re.findall(r"#(\w+)", text)