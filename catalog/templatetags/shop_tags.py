from django import template
from django.utils.safestring import mark_safe

register = template.Library()
_FA = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")


@register.filter
def fa(value):
    """تبدیل ارقام به فارسی."""
    return str(value).translate(_FA)


@register.filter
def toman(value):
    try:
        n = int(value)
    except (TypeError, ValueError):
        return ""
    return mark_safe(f"{n:,}".replace(",", "٬").translate(_FA) + " تومان")


@register.filter
def num(value):
    try:
        return f"{int(value):,}".replace(",", "٬").translate(_FA)
    except (TypeError, ValueError):
        return ""


@register.filter
def jdate(value, fmt="%Y/%m/%d"):
    if not value:
        return ""
    try:
        import jdatetime
        from django.utils import timezone
        if timezone.is_aware(value):
            value = timezone.localtime(value)
        return jdatetime.datetime.fromgregorian(datetime=value).strftime(fmt).translate(_FA)
    except Exception:
        return str(value.date()).translate(_FA)


@register.filter
def stars(value):
    try:
        full = round(float(value))
    except (TypeError, ValueError):
        full = 0
    return "★" * full + "☆" * (5 - full)


@register.simple_tag(takes_context=True)
def qs_replace(context, **kwargs):
    params = context["request"].GET.copy()
    for k, v in kwargs.items():
        params[k] = v
    return params.urlencode()
