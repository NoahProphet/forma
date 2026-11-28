from django.conf import settings
from django.db.models import Prefetch, prefetch_related_objects

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


def project_cards(queryset):
    cards = list(queryset)
    # Use the approved detail photograph for the demo project whose cover is the homepage hero.
    featured_details = [p for p in cards if p.is_demo and p.image.name == "demo/hero.jpg"]
    prefetch_related_objects(featured_details, "gallery")
    for project in featured_details:
        gallery = list(project.gallery.all())
        if gallery:
            project.card_image = gallery[-1].image
    return cards
