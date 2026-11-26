from django import template

register = template.Library()
PERSIAN_DIGITS = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")


@register.filter
def fa(value):
    return str(value).translate(PERSIAN_DIGITS)


@register.filter
def toman(value):
    return fa(f"{value:,}").replace(",", "٬")
