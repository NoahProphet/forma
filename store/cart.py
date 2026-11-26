from uuid import uuid4

from django.conf import settings
from django.db import transaction
from django.db.models import Sum

from .models import CartLine, Variant


class BasketError(Exception):
    pass


def basket_key(request):
    key = request.session.get("basket_key")
    if not key:
        key = uuid4().hex
        request.session["basket_key"] = key
    return key


def basket_lines(request):
    items = CartLine.objects.filter(basket=request.session.get("basket_key", ""))
    items = items.filter(variant__product__active=True)
    if not settings.DEBUG:
        items = items.filter(variant__product__is_demo=False)
    return items.select_related("variant__product", "variant__finish").order_by("pk")


def basket_count(request):
    if not request.session.get("basket_key"):
        return 0
    return basket_lines(request).aggregate(total=Sum("quantity"))["total"] or 0


def allowed_quantity(variant, quantity):
    return variant.purchasable and 1 <= quantity <= min(variant.stock, 99)


@transaction.atomic
def change_basket(request, variant, *, quantity, operation):
    key = basket_key(request)
    query = CartLine.objects.filter(basket=key, variant=variant)
    line = query.select_for_update().first()

    if operation == "remove":
        query.delete()
        return
    variant = Variant.objects.select_for_update().get(pk=variant.pk)
    if operation == "add":
        quantity += line.quantity if line else 0
    elif line is None:
        raise BasketError("این کالا در سبد خرید نیست.")

    if not allowed_quantity(variant, quantity):
        raise BasketError("تعداد درخواستی قابل تأمین نیست. موجودی یا تعداد را بررسی کنید.")
    if line:
        query.update(quantity=quantity)
    else:
        CartLine.objects.create(basket=key, variant=variant, quantity=quantity)


def basket_summary(request):
    rows = list(basket_lines(request))
    for line in rows:
        line.amount = line.quantity * line.variant.price if line.variant.price is not None else None
        line.can_request = allowed_quantity(line.variant, line.quantity)
        line.max_quantity = min(line.variant.stock or 0, 99)
        line.image = line.variant.image or line.variant.product.image
    return {
        "rows": rows,
        "total": sum(line.amount or 0 for line in rows),
        "can_request": bool(rows) and all(line.can_request for line in rows),
        "basket_demo": any(line.variant.product.is_demo for line in rows),
    }


def basket_snapshot(rows):
    return [{
        "product": row.variant.product.name,
        "finish": row.variant.finish.name,
        "sku": row.variant.sku,
        "quantity": row.quantity,
        "unit_price_toman": row.variant.price,
    } for row in rows]
