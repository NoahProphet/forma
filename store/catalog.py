from django.conf import settings
from django.db.models import Prefetch

from .models import Product, Project, Variant


def products():
    items = Product.objects.filter(active=True).select_related("category", "brand")
    return items if settings.DEBUG else items.filter(is_demo=False)


def with_cards(items, variants=None):
    if variants is None:
        variants = Variant.objects.all()
    return items.prefetch_related(Prefetch(
        "variants", queryset=variants.select_related("finish"), to_attr="card_variants",
    ))


def projects():
    items = Project.objects.filter(published=True)
    return items if settings.DEBUG else items.filter(is_demo=False)
