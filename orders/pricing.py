from django.conf import settings


def shipping_cost(amount):
    """هزینه ارسال: رایگان برای خرید بالاتر از آستانه."""
    if amount <= 0 or amount >= settings.FREE_SHIPPING_THRESHOLD:
        return 0
    return settings.SHIPPING_COST
