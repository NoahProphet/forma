from pathlib import Path
from shutil import copyfile

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from store.models import Article, Brand, Category, Finish, Product, Project, ProjectImage, Variant


class Command(BaseCommand):
    help = "Load the local FORMA prototype catalog and sample project imagery."

    @transaction.atomic
    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError("Demo data can only be loaded with DJANGO_DEBUG=1.")

        source = settings.BASE_DIR / "static" / "media"
        destination = settings.MEDIA_ROOT / "demo"
        destination.mkdir(parents=True, exist_ok=True)

        def media(stem):
            filename = f"{stem}.jpg"
            target = destination / filename
            if not target.exists():
                copyfile(source / filename, target)
            return (Path("demo") / filename).as_posix()

        categories = {}
        for order, (slug, name, description, image) in enumerate([
            ("kitchen", "آشپزخانه", "سینک، شیرآلات، اجاق و هود آشپزخانه را بر اساس اندازه و پرداخت پیدا کنید.", "kitchen"),
            ("bath", "حمام و سرویس", "روشویی، کابینت و شیرآلات مناسب فضای خود را پیدا کنید.", "bath"),
            ("building", "تجهیزات ساختمان", "برای انتخاب تجهیزات و متریال ساختمان با شوروم فرما در رشت هماهنگ کنید.", ""),
        ]):
            categories[slug], _ = Category.objects.get_or_create(slug=slug, defaults={
                "name": name, "description": description, "image": media(image) if image else "", "order": order,
            })

        brands = {}
        for name in ("FORMA", "KWC", "Alton"):
            brands[name], _ = Brand.objects.get_or_create(slug=name.lower(), defaults={"name": name, "is_demo": True})

        finishes = {}
        for slug, name, color in [
            ("gold", "طلایی شامپاینی", "#c6a571"), ("black", "مشکی مات", "#292828"),
            ("bronze", "برنز برس‌خورده", "#87634a"), ("steel", "استیل برس‌خورده", "#a9a8a3"),
            ("ivory", "شیری مات", "#e9dfcc"), ("glass", "شیشه مشکی", "#2d2b2d"),
            ("stone", "سنگ کرم", "#ceb995"), ("wood", "گردویی", "#725137"),
        ]:
            finishes[slug], _ = Finish.objects.get_or_create(slug=slug, defaults={"name": name, "color": color})

        items = {}
        for slug, name, model, brand, category, image, material, size, finish, price, stock, featured in [
            ("arc", "شیر آشپزخانه آرک", "ARC 01", "KWC", "kitchen", "faucet", "آلیاژ برنج", "ارتفاع ۳۸ سانتی‌متر", "gold", 12900000, 5, True),
            ("edge", "سینک زیرکار اِج", "EDGE 60", "Alton", "kitchen", "sink", "استیل ضدزنگ", "۶۰ × ۴۵ سانتی‌متر", "steel", 8700000, 3, True),
            ("forma-bowl", "روشویی کاسه‌ای فرم", "BOWL 42", "FORMA", "bath", "basin", "سرامیک", "قطر ۴۲ سانتی‌متر", "ivory", 5900000, 6, True),
            ("line", "اجاق صفحه‌ای لاین", "LINE 60", "Alton", "kitchen", "cooktop", "شیشه سرامیکی", "۶۰ × ۵۲ سانتی‌متر", "glass", None, 2, True),
            ("stone", "روشویی سنگی استون", "STONE 50", "FORMA", "bath", "bath", "سنگ طبیعی", "قطر ۵۰ سانتی‌متر", "stone", None, 2, False),
            ("shade", "هود دیواری شِید", "SHADE 90", "Alton", "kitchen", "hood", "فولاد با پوشش رنگ", "عرض ۹۰ سانتی‌متر", "steel", None, 3, False),
            ("wood", "کابینت روشویی وود", "WOOD 80", "FORMA", "bath", "vanity", "روکش چوب", "عرض ۸۰ سانتی‌متر", "wood", 16800000, 2, False),
            ("wall", "شیر دیواری روشویی", "WALL 20", "KWC", "bath", "wall", "آلیاژ برنج", "طول آبریز ۲۰ سانتی‌متر", "bronze", 6400000, 0, False),
        ]:
            product, _ = Product.objects.get_or_create(slug=slug, defaults={
                "name": name, "model": model, "brand": brands[brand], "category": categories[category],
                "image": media(image), "material": material, "size": size, "featured": featured, "is_demo": True,
            })
            if not product.is_demo:
                continue
            items[slug] = product
            Variant.objects.get_or_create(product=product, finish=finishes[finish], defaults={
                "sku": model.replace(" ", "-") + ("-GD" if slug == "arc" else ""),
                "image": media(image), "price": price, "stock": stock, "order": 0,
            })

        if "arc" in items:
            arc = items["arc"]
            for order, (finish, suffix, price, stock) in enumerate([
                ("black", "BK", 11900000, 3), ("bronze", "BZ", None, None), ("steel", "ST", 12300000, 0),
            ], start=1):
                Variant.objects.get_or_create(product=arc, finish=finishes[finish], defaults={
                    "sku": f"ARC-01-{suffix}", "image": media(f"faucet-{finish}"),
                    "price": price, "stock": stock, "order": order,
                })

        for slug, title, summary, body, cover, photos, related in [
            ("walnut-and-stone", "آشپزخانه با سنگ و گردو", "ترکیب چوب گردویی، جزیره سنگی و فلز شامپاینی در آشپزخانه.",
             "نور طبیعی، رگه‌های سنگ و بافت چوب را در کنار هم نشان می‌دهد. اگر شیری با پرداخت گرم انتخاب می‌کنید، نمونه آن را کنار صفحه و دستگیره‌ها در نور آشپزخانه ببینید.",
             "hero", [("sink", "سینک و شیر شامپاینی روی صفحه سنگی"), ("hood", "هود دیواری و کابینت گردویی")], ("arc", "edge")),
            ("stone-and-brass", "روشویی سنگی با شیر دیواری", "ترکیب سنگ کرم و شیر دیواری با پرداخت گرم برای سرویس بهداشتی.",
             "ابعاد کاسه و پیش‌آمدگی شیر را با هم بررسی کنید. جای خروج آب در میانه کاسه و فاصله مناسب برای شست‌وشو به انتخاب مدل کمک می‌کند.",
             "vanity", [("bath", "کاسه سنگی با شیرآلات دیواری"), ("wall", "جزئیات آبریز و بافت دیوار")], ("stone", "wall")),
        ]:
            project, created = Project.objects.get_or_create(slug=slug, defaults={
                "title": title, "summary": summary, "body": body, "image": media(cover), "is_demo": True,
            })
            if created:
                project.products.set(items[key] for key in related if key in items)
                for order, (image, alt) in enumerate(photos):
                    ProjectImage.objects.create(project=project, image=media(image), alt=alt, order=order)

        for slug, title, summary, body, image in [
            ("kitchen-materials", "انتخاب متریال برای آشپزخانه",
             "سنگ، چوب و پرداخت شیرآلات را در نور آشپزخانه کنار هم ببینید.",
             "پیش از انتخاب، نمونه سطوح را در نور روز و نور مصنوعی کنار هم بگذارید. رنگ یک پرداخت در شوروم و در فضای خانه ممکن است متفاوت به نظر برسد.\n\nبرای آشپزخانه‌های پرکاربرد، دسترسی به سینک و نظافت روزانه را هم در نظر بگیرید. از فروشنده بخواهید شیوه نگهداری سطح را مطابق راهنمای سازنده توضیح دهد.", "kitchen"),
            ("washbasin-guide", "راهنمای انتخاب روشویی",
             "محل نصب، ارتفاع کاسه و جای خروج آب را پیش از خرید بررسی کنید.",
             "عرض دیوار و فاصله در تا روشویی را اندازه بگیرید و جای لوله‌ها را مشخص کنید. برای مدل‌های رومیزی، ارتفاع صفحه و کاسه را با هم در نظر بگیرید.\n\nارتفاع و پیش‌آمدگی آبریز باید با کاسه هماهنگ باشد. پیش از سفارش، نقشه نصب سازنده را با نصاب بررسی کنید.", "basin"),
            ("care-for-brushed-finishes", "مراقبت از شیرآلات برس‌خورده",
             "شیوه تمیز کردن پرداخت برس‌خورده را از راهنمای سازنده همان مدل بررسی کنید.",
             "برای نظافت روزمره، در صورت تأیید سازنده از دستمال نرم استفاده کنید و سطح را پس از شست‌وشو خشک کنید. مواد ساینده ممکن است روی پرداخت بعضی شیرآلات اثر بگذارند.\n\nپیش از استفاده از شوینده تخصصی، دستورالعمل همان مدل را بخوانید و از محصول مناسب آن پرداخت استفاده کنید.", "faucet"),
        ]:
            Article.objects.get_or_create(slug=slug, defaults={
                "title": title, "summary": summary, "body": body, "image": media(image), "published": True,
            })

        self.stdout.write(self.style.SUCCESS("FORMA development catalog is ready."))
