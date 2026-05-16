def final_price(price, discount):
    if price < 0:
        raise ValueError("Цена не может быть меньше 0")
    if discount < 0:
        raise ValueError("Скидка не может быть меньше 0")

    return round(price - discount, 2)
