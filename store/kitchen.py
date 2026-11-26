"""Resolve scene placements into demo options or published catalog variants."""
import json
from copy import deepcopy
from functools import lru_cache
from pathlib import Path
from urllib.parse import urlencode

from django.conf import settings
from django.http import Http404
from django.templatetags.static import static
from django.urls import reverse

from .models import Variant


@lru_cache(maxsize=8)
def _recipe(scene_id):
    return json.loads((Path(__file__).parent/"kitchens"/f"{scene_id}.json").read_text(encoding="utf-8"))


def kitchen_scene():
    mode = settings.KITCHEN_MODE
    if mode not in ("demo", "catalog"):
        return None
    try:
        scene = deepcopy(_recipe(settings.KITCHEN_SCENE))
    except FileNotFoundError:
        return None
    scene["demo"] = mode == "demo"
    scene["assetRoot"] = static(f"kitchens/{scene['id']}/")
    skus = [v["sku"] for slot in scene["slots"].values() for m in slot["models"]
            for v in m["variants"] if v.get("sku")]
    live = {} if scene["demo"] else {v.sku:v for v in Variant.objects.select_related("product","finish").filter(
        sku__in=skus,product__active=True,product__is_demo=False
    )}
    for category,slot in scene["slots"].items():
        models = []
        for model in slot["models"]:
            variants = []
            for option in model["variants"]:
                if scene["demo"]:
                    url = reverse("kitchen-demo",args=[category,model["id"]])
                    option["url"] = url+"?"+urlencode({"finish":option["id"]})
                else:
                    variant = live.get(option.get("sku"))
                    if variant is None:
                        continue
                    model["name"] = variant.product.name
                    option.update(name=variant.finish.name,color=variant.finish.color,stock=variant.stock,
                                  url=variant.product.get_absolute_url()+"?"+urlencode({"finish":variant.finish.slug}))
                option["thumb"] = scene["assetRoot"]+option["thumb"]
                option["availability"] = "موجودی نامشخص" if option["stock"] is None else (
                    "موجود" if option["stock"]>0 else "ناموجود")
                variants.append(option)
            if variants:
                model["variants"] = variants
                models.append(model)
        slot["models"] = models[:4]
    if not any(s["models"] for s in scene["slots"].values()):
        return None
    return scene


def demo_detail(request, category, model):
    from .views import page
    if settings.KITCHEN_MODE!="demo":
        raise Http404
    scene = kitchen_scene()
    slot = scene["slots"].get(category) if scene else None
    product = next((m for m in slot["models"] if m["id"]==model),None) if slot else None
    if not product:
        raise Http404
    finish = request.GET.get("finish",product["variants"][0]["id"])
    option = next((v for v in product["variants"] if v["id"]==finish),None)
    if not option:
        raise Http404
    return page(request,"kitchen/detail.html", slot["name"]+" "+product["name"]+" · "+option["name"],
                "محصول فرضی برای بررسی طراحی آشپزخانه تعاملی فرما.",option["thumb"],
                slot=slot,model=product,option=option,private_page=True)

