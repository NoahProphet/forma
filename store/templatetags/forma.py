from functools import lru_cache
from hashlib import sha256

from django import template
from django.conf import settings
from django.templatetags.static import static

register = template.Library()
PERSIAN_DIGITS = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")


@lru_cache(maxsize=1)
def _stylesheet_digest(path, mtime_ns, size):
    # Reuse the digest across requests until the compiled bundle changes.
    return sha256(path.read_bytes()).hexdigest()[:16]


@register.simple_tag
def storefront_css_url():
    name = "css/storefront.css"
    path = settings.BASE_DIR / "static" / name
    stat = path.stat()
    version = _stylesheet_digest(path, stat.st_mtime_ns, stat.st_size)
    return f"{static(name)}?v={version}"


@register.filter
def fa(value):
    return str(value).translate(PERSIAN_DIGITS)


@register.filter
def toman(value):
    return fa(f"{value:,}").replace(",", "٬")
