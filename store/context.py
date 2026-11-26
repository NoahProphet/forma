from django.conf import settings
from django.utils.functional import SimpleLazyObject

from .cart import basket_count, basket_summary

ADDRESS = "رشت، بلوار ضیابری، فاز ۲، ساختمان خورشید، هایپر ساختمانی فرما"
PHONE = "01333516775"
MOBILE = "09112881592"


def site(request):
    cart_count = basket_count(request)
    return {
        "cart_count": cart_count,
        "header_basket": SimpleLazyObject(lambda: basket_summary(request) if cart_count else {}),
        "compare_count": len(request.session.get("compare", [])),
        "showroom_address": ADDRESS,
        "showroom_phone": PHONE,
        "showroom_mobile": MOBILE,
        "showroom_map": settings.SHOWROOM_MAP_URL,
        "showroom_whatsapp": settings.SHOWROOM_WHATSAPP_URL,
        "showroom_instagram": settings.SHOWROOM_INSTAGRAM_URL,
    }
