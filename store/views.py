from urllib.parse import urlencode

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.core.paginator import Paginator
from django.db import IntegrityError, OperationalError, transaction
from django.db.models import Count, Exists, F, Max, Min, OuterRef, Q, Subquery
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.templatetags.static import static
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.timezone import localdate
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods, require_POST
from django.views.decorators.vary import vary_on_headers

from .cart import BasketError, basket_key, basket_snapshot, basket_summary, change_basket
from .catalog import products, projects, with_cards
from .kitchen import kitchen_scene
from .forms import InquiryForm, QuantityForm, normalize_number
from .models import Article, Brand, Category, Finish, Inquiry, Variant

ORDERINGS = {
    "featured": ("منتخب فرما", ("-featured", "pk")),
    "new": ("تازه‌ترین‌ها", ("-pk",)),
    "price-asc": ("کمترین قیمت", (F("listing_price").asc(nulls_last=True), "pk")),
    "price-desc": ("بیشترین قیمت", (F("listing_price").desc(nulls_last=True), "pk")),
}

SHOWROOM_SHORTCUTS = (
    ("kitchen", "سینک", "سینک", "جنس، ابعاد و مدل‌های سینک آشپزخانه را بررسی کنید."),
    ("kitchen", "شیرآلات آشپزخانه", "شیر", "مدل‌ها و پرداخت‌های شیر آشپزخانه را ببینید."),
    ("kitchen", "هود", "هود", "مدل‌های هود آشپزخانه و ابعاد آن‌ها را ببینید."),
    ("kitchen", "اجاق صفحه‌ای", "اجاق", "اجاق‌های صفحه‌ای را بر اساس مدل و ابعاد بررسی کنید."),
    ("bath", "حمام و سرویس", "", "روشویی، کابینت و شیرآلات سرویس بهداشتی."),
    ("bath", "شیرآلات سرویس", "شیر", "مدل‌ها و پرداخت‌های شیر روشویی را ببینید."),
)


def page(request, template, title, description, image="", **context):
    origin = settings.SITE_ORIGIN
    return render(request, template, {
        "title": title,
        "description": description,
        "canonical": origin + request.path,
        "share_image": request.build_absolute_uri(image) if image.startswith("http") else origin + (
            image or static("media/hero.jpg")
        ),
        **context,
    })


def hx(request):
    return request.headers.get("HX-Request") == "true"


@never_cache
@require_http_methods(["GET", "POST"])
def register_account(request):
    if request.user.is_authenticated:
        return redirect("account")
    form = UserCreationForm(request.POST if request.method == "POST" else None)
    if form.is_valid():
        try:
            with transaction.atomic():
                user = form.save()
        except IntegrityError:
            form.add_error("username", "این نام کاربری در دسترس نیست.")
        else:
            login(request, user)
            return redirect("account")
    return render(request, "account/access.html", {
        "title": "ثبت‌نام در فرما", "form": form, "is_registration": True, "private_page": True,
    })


@never_cache
@login_required(login_url="login")
def account(request):
    return render(request, "account/profile.html", {"title": "حساب من", "private_page": True})


def home_category_tiles(items, categories):
    stocked = {category.slug: category for category in categories if category.has_products}
    shown = set()
    tiles = []
    shop_url = reverse("shop")

    for slug, label, term, description in SHOWROOM_SHORTCUTS:
        category = stocked.get(slug)
        if not category:
            continue
        matches = items.filter(category=category)
        if term:
            matches = search_products(matches, term)
        # A vanity photograph gives the bath overview a wider context than the tap tile.
        photos = matches if term else search_products(matches, "کابینت")
        representative = photos.exclude(image="").order_by("-featured", "pk").first()
        if not representative and term and not matches.exists():
            continue
        tiles.append({
            "label": label, "description": description,
            "image": representative.image if representative else category.image,
            "url": query_url(shop_url, {"category": slug, "q": term}),
        })
        shown.add(slug)

    for slug, category in stocked.items():
        if slug not in shown:
            representative = (
                items.filter(category=category).exclude(image="").order_by("-featured", "pk").first()
                if not category.image else None
            )
            tiles.append({
                "label": category.name, "description": category.description,
                "image": representative.image if representative else category.image,
                "url": query_url(shop_url, {"category": slug}),
            })
    return tiles


def home(request):
    items = products()
    categories = list(Category.objects.annotate(has_products=Exists(items.filter(category_id=OuterRef("pk")))))
    home_projects = list(projects().prefetch_related("gallery")[:2])
    for project in home_projects:
        if project.is_demo and project.image.name == "demo/hero.jpg":
            detail = list(project.gallery.all())
            if detail:
                project.card_image = detail[-1].image
    return page(
        request, "home.html", "تجهیزات آشپزخانه، حمام و ساختمان در رشت",
        "فروشگاه و شوروم فرما در رشت. محصولات آشپزخانه، حمام و ساختمان را ببینید، مقایسه کنید و برای بازدید یا استعلام هماهنگ کنید.",
        home_categories=home_category_tiles(items, categories), kitchen=kitchen_scene(),
        building_consult=any(category.slug == "building" and not category.has_products for category in categories),
        featured=with_cards(items.filter(featured=True).order_by("pk")).first(),
        projects=home_projects,
    )


def filter_value(request, field):
    return request.GET.get(field, "").strip()[:120]


def price_filter(request, field):
    value = normalize_number(filter_value(request, field)).replace("٬", "").replace(",", "")
    return int(value) if value.isascii() and value.isdecimal() and len(value) <= 10 else None


def query_url(path, fields, **updates):
    query = urlencode({
        key: value for key, value in (fields | updates).items() if value not in ("", None)
    }, doseq=True)
    return f"{path}?{query}" if query else path


def search_products(items, term):
    sku_match = Variant.objects.filter(product_id=OuterRef("pk"), sku__icontains=term)
    return items.filter(
        Q(name__icontains=term) | Q(model__icontains=term) | Q(brand__name__icontains=term)
        | Q(category__name__icontains=term) | Q(description__icontains=term) | Exists(sku_match)
    )


def filter_chips(path, filters, category, brands, finishes):
    brand_names = {brand.slug: brand.name for brand in brands}
    finish_names = {finish.slug: finish.name for finish in finishes}
    choices = (
        ("category", "دسته", category.name if category else filters["category"]),
        ("q", "جست‌وجو", filters["q"]),
        ("finish", "رنگ و پرداخت", finish_names.get(filters["finish"], filters["finish"])),
        ("stock", "", "فقط موجودها" if filters["stock"] == "yes" else ""),
        ("low", "حداقل قیمت", filters["low"]),
        ("high", "حداکثر قیمت", filters["high"]),
    )
    return [
        {"key": key, "label": label, "value": value, "is_price": key in {"low", "high"},
         "url": query_url(path, filters, **{key: ""})}
        for key, label, value in choices if value not in ("", None)
    ] + [
        {"key": f"brand-{index}", "label": "برند", "value": brand_names.get(slug, slug),
         "url": query_url(path, filters, brand=[value for value in filters["brand"] if value != slug])}
        for index, slug in enumerate(filters["brand"])
    ]


def sample_state(items):
    demo_flags = {item.is_demo for item in items}
    if demo_flags == {True, False}:
        return "mixed"
    return "all" if True in demo_flags else ""


@vary_on_headers("HX-Request")
def shop(request):
    filters = {field: filter_value(request, field) for field in ("q", "category", "finish", "stock", "sort")}
    filters.update(
        brand=list(dict.fromkeys(value.strip()[:120] for value in request.GET.getlist("brand") if value.strip())),
        low=price_filter(request, "low"), high=price_filter(request, "high"),
    )
    sort = filters["sort"] if filters["sort"] in ORDERINGS else "featured"
    filters["sort"] = sort
    all_items = products()
    items = all_items
    categories = list(Category.objects.all())
    category = next((option for option in categories if option.slug == filters["category"]), None)
    if filters["q"]:
        items = search_products(items, filters["q"])

    variants = Variant.objects.all()
    if filters["finish"]:
        variants = variants.filter(finish__slug=filters["finish"])
    if filters["stock"] == "yes":
        variants = variants.filter(stock__gt=0)
    unpriced_range = variants
    if filters["low"] is not None:
        variants = variants.filter(price__gte=filters["low"])
    if filters["high"] is not None:
        variants = variants.filter(price__lte=filters["high"])

    matching = variants.filter(product_id=OuterRef("pk"))
    in_category = items.filter(category__slug=filters["category"]) if filters["category"] else items
    price_scope = in_category.filter(brand__slug__in=filters["brand"]) if filters["brand"] else in_category
    price_bounds = unpriced_range.filter(product__in=price_scope).aggregate(low=Min("price"), high=Max("price"))
    if any((filters["finish"], filters["stock"] == "yes", filters["low"] is not None, filters["high"] is not None)):
        items = items.filter(Exists(matching))
    brand_scope = items.filter(category__slug=filters["category"]) if filters["category"] else items
    if filters["brand"]:
        items = items.filter(brand__slug__in=filters["brand"])
    category_counts = dict(items.order_by().values("category_id").annotate(total=Count("pk")).values_list("category_id", "total"))
    brand_counts = dict(brand_scope.order_by().values("brand_id").annotate(total=Count("pk")).values_list("brand_id", "total"))
    if filters["category"]:
        items = items.filter(category__slug=filters["category"])
    if sort.startswith("price"):
        direction = "" if sort == "price-asc" else "-"
        items = items.annotate(listing_price=Subquery(
            matching.exclude(price=None).order_by(f"{direction}price").values("price")[:1]
        ))
        variants = variants.order_by(F("price").desc(nulls_last=True) if direction else F("price").asc(nulls_last=True), "pk")

    path = reverse("shop")
    selected_page = Paginator(with_cards(items.order_by(*ORDERINGS[sort][1]), variants), 6).get_page(
        normalize_number(filter_value(request, "page"))
    )
    catalog_title = category.name if category else "فروشگاه"
    brand_options = list(Brand.objects.filter(product__in=all_items).distinct())
    finish_options = list(Finish.objects.filter(variant__product__in=all_items).distinct())
    if any(item.card_variants and item.card_variants[0].purchasable for item in selected_page):
        basket_key(request)
    scopes = [{"slug": "", "name": "همه محصولات", "count": sum(category_counts.values())}]
    scopes.extend({"slug": option.slug, "name": option.name, "count": category_counts.get(option.pk, 0)} for option in categories)
    for scope in scopes:
        scope["url"] = query_url(path, filters, category=scope["slug"])
    page_links = [
        {"number": number, "url": query_url(path, filters, page=number)} if isinstance(number, int) else None
        for number in selected_page.paginator.get_elided_page_range(selected_page.number, on_each_side=1, on_ends=1)
    ] if selected_page.has_other_pages() else []
    near_results = {key: filters[key] for key in ("q", "category", "sort")}
    has_facets = any(value for value in (filters["brand"], filters["finish"], filters["stock"] == "yes")) or any(
        filters[key] is not None for key in ("low", "high")
    )
    context = {
        "catalog_title": catalog_title, "category": category, "scopes": scopes,
        "brand_facets": [{"brand": brand, "count": brand_counts.get(brand.pk, 0)} for brand in brand_options
                         if brand_counts.get(brand.pk, 0) or brand.slug in filters["brand"]],
        "finish_options": finish_options, "price_bounds": price_bounds, "page_links": page_links,
        "active_filters": filter_chips(path, filters, category, brand_options, finish_options),
        "clear_filters_url": query_url(path, near_results) if has_facets else "",
        "sample_state": sample_state(selected_page),
        "filters": filters, "sort_options": ORDERINGS.items(), "result": selected_page,
        "previous_url": query_url(path, filters, page=selected_page.previous_page_number()) if selected_page.has_previous() else "",
        "next_url": query_url(path, filters, page=selected_page.next_page_number()) if selected_page.has_next() else "",
    }
    description = f"مشاهده و مقایسه محصولات {category.name if category else 'آشپزخانه، حمام و ساختمان'} در فروشگاه فرما، رشت."
    if hx(request):
        response = render(request, "partials/catalog.html", context | {"partial": True})
        response["HX-Push-Url"] = request.get_full_path()
        return response
    return page(request, "shop.html", catalog_title, description, **context)


@vary_on_headers("HX-Request")
def product(request, slug):
    item = get_object_or_404(products(), slug=slug)
    variants = list(item.variants.select_related("finish").prefetch_related("gallery"))
    finish = filter_value(request, "finish")
    variant = next((v for v in variants if v.finish.slug == finish), variants[0] if variants else None)
    photos = list(variant.gallery.all()) if variant else []
    main_image = variant.image if variant and variant.image else item.image if not variant or variant == variants[0] else None
    gallery = [{"id": "main", "image": main_image, "alt": f"{item.name}، {variant.finish.name}" if variant else item.name}] if main_image else []
    if main_image and not photos:
        gallery.append(gallery[0] | {"id": "detail", "alt": f"نمای نزدیک {gallery[0]['alt']}", "zoom": True})
    gallery += [{"id": str(photo.pk), "image": photo.image, "alt": photo.alt} for photo in photos]
    active_photo = next((photo for photo in gallery if photo["id"] == filter_value(request, "photo")), gallery[0] if gallery else None)
    if variant and variant.purchasable:
        basket_key(request)
    context = {"product": item, "variants": variants, "variant": variant, "gallery": gallery, "photo": active_photo}
    if hx(request):
        return render(request, "partials/product-choice.html", {**context, "gallery_changed": True})
    related = list(with_cards(products().filter(category=item.category).exclude(pk=item.pk))[:3])
    image = gallery[0]["image"].url if gallery else item.image.url if item.image else ""
    return page(
        request, "product.html", item.name,
        item.description[:155] or f"مشخصات و گزینه‌های پرداخت {item.name} در فروشگاه فرما، رشت.",
        image, related=related, sample_state=sample_state(related), private_page=item.is_demo, **context,
    )


@require_POST
def change_comparison(request, slug):
    item = get_object_or_404(products(), slug=slug)
    selected = request.session.get("compare", [])
    if item.pk in selected:
        selected.remove(item.pk)
    elif len(selected) < 3:
        selected.append(item.pk)
    else:
        messages.error(request, "برای مقایسه محصول جدید، یکی از سه محصول فعلی را حذف کنید.")
    request.session["compare"] = selected
    destination = request.POST.get("next", "")
    if not destination.startswith("/") or not url_has_allowed_host_and_scheme(destination, {request.get_host()}):
        destination = reverse("shop")
    return redirect(destination)


def compare(request):
    selected = request.session.get("compare", [])
    compared = {item.pk: item for item in with_cards(products().filter(pk__in=selected))}
    return page(request, "compare.html", "مقایسه محصولات", "محصولات منتخب خود را از نظر جنس، ابعاد، پرداخت و قیمت مقایسه کنید.",
                compared=[compared[pk] for pk in selected if pk in compared], private_page=True)


@never_cache
def cart(request):
    return page(request, "cart.html", "سبد خرید", "محصولات، پرداخت و تعداد کالاهای انتخابی خود را بررسی کنید.",
                private_page=True, **basket_summary(request))


@require_POST
@never_cache
def cart_change(request, pk):
    variant = get_object_or_404(Variant.objects.select_related("product", "finish").filter(product__in=products()), pk=pk)
    operation = request.POST.get("operation", "")
    shop_return = request.POST.get("shop_return", "")
    from_shop = operation == "add" and shop_return.split("#", 1)[0].split("?", 1)[0] == reverse("shop")
    form = QuantityForm(request.POST)
    error = ""
    if operation not in {"add", "set", "remove"}:
        error = "این عملیات برای سبد خرید قابل انجام نیست."
    elif operation != "remove" and not form.is_valid():
        error = "تعداد را به صورت عددی از ۱ تا ۹۹ وارد کنید."
    else:
        try:
            change_basket(request, variant, quantity=form.cleaned_data.get("quantity", 0) if operation != "remove" else 0,
                          operation=operation)
        except BasketError as problem:
            error = str(problem)
        except OperationalError:
            error = "سبد خرید در حال به‌روزرسانی است. دوباره تلاش کنید."
    if hx(request):
        if operation == "add":
            template = "partials/shop/add-status.html" if from_shop else "partials/add-status.html"
            return render(request, template, {"error": error, "added": not error, "swap_count": True, "variant": variant},
                          status=422 if error else 200)
        return render(request, "partials/cart-content.html", basket_summary(request) | {
            "error": error, "updated": not error, "swap_count": True,
        }, status=422 if error else 200)
    if error:
        messages.error(request, error)
    elif operation == "add":
        messages.success(request, "محصول به سبد خرید اضافه شد.")
    if operation == "add":
        if from_shop:
            return redirect(shop_return)
        return redirect(query_url(variant.product.get_absolute_url(), {"finish": variant.finish.slug}) + "#purchase")
    return redirect("cart")


@require_http_methods(["GET", "POST"])
@never_cache
def checkout(request):
    summary = basket_summary(request)
    form = InquiryForm(request.POST if request.method == "POST" else None, kind=Inquiry.Kind.BASKET)
    if request.method == "POST":
        if not summary["can_request"]:
            messages.error(request, "پیش از ثبت درخواست، تعداد یا موجودی کالاهای سبد را بررسی کنید.")
            return redirect("cart")
        if form.is_valid():
            inquiry = form.save(commit=False)
            inquiry.kind = Inquiry.Kind.BASKET
            inquiry.basket = basket_snapshot(summary["rows"])
            inquiry.save()
            messages.success(request, f"درخواست خرید با شماره پیگیری {inquiry.pk} ثبت شد. وضعیت خرید را با شوروم هماهنگ کنید.")
            return redirect("checkout")
    return page(request, "checkout.html", "هماهنگی خرید", "مرور سبد و ثبت درخواست خرید برای پیگیری شوروم فرما.",
                form=form, private_page=True, **summary)


def brands(request):
    entries = Brand.objects.all()
    if not settings.DEBUG:
        entries = entries.filter(is_demo=False)
    return page(request, "brands.html", "برندها", "برندهای تجهیزات آشپزخانه و حمام در فروشگاه فرما.", brands=entries)


def project_index(request):
    return page(request, "projects.html", "پروژه‌ها", "فضاها و ترکیب‌هایی برای انتخاب تجهیزات و متریال پروژه خود.",
                projects=projects())


def project(request, slug):
    item = get_object_or_404(projects().prefetch_related("gallery"), slug=slug)
    related = with_cards(products().filter(project=item))
    return page(request, "project.html", item.title, item.summary, item.image.url if item.image else "",
                project=item, related=related, private_page=item.is_demo)


def articles():
    return Article.objects.filter(published=True).filter(Q(published_at__lte=localdate()) | Q(published_at=None))


def journal(request):
    return page(request, "journal.html", "مجله فرما", "راهنمای انتخاب، نصب و نگهداری تجهیزات آشپزخانه و حمام.", articles=articles())


def article(request, slug):
    item = get_object_or_404(articles(), slug=slug)
    return page(request, "article.html", item.title, item.summary, item.image.url if item.image else "", article=item)


def about(request):
    return page(request, "about.html", "درباره فرما", "با شوروم فرما و مجموعه تجهیزات آشپزخانه، حمام و ساختمان در رشت آشنا شوید.")


@require_http_methods(["GET", "POST"])
@never_cache
def contact(request):
    kinds = [Inquiry.Kind.CONSULT, Inquiry.Kind.QUOTE, Inquiry.Kind.VISIT]
    kind = request.GET.get("kind")
    kind = kind if kind in kinds else Inquiry.Kind.CONSULT
    slug = filter_value(request, "product")
    finish = filter_value(request, "finish")
    selected_product = get_object_or_404(products(), slug=slug) if slug and kind == Inquiry.Kind.QUOTE else None
    variant = get_object_or_404(selected_product.variants.select_related("finish"), finish__slug=finish) if selected_product and finish else None
    form = InquiryForm(request.POST if request.method == "POST" else None, kind=kind)
    if request.method == "POST" and form.is_valid():
        inquiry = form.save(commit=False)
        inquiry.kind = kind
        inquiry.variant = variant
        if selected_product and not variant:
            inquiry.basket = [{"product": selected_product.name, "model": selected_product.model}]
        inquiry.save()
        messages.success(request, f"درخواست شما با شماره پیگیری {inquiry.pk} ثبت شد.")
        return redirect(request.get_full_path() + "#request")
    return page(request, "contact.html", "تماس و بازدید از شوروم فرما در رشت",
                "نشانی و تلفن شوروم فرما در رشت. درخواست مشاوره، استعلام قیمت یا هماهنگی بازدید ثبت کنید.",
                kinds=kinds, kind=kind, form=form, selected_product=selected_product, variant=variant, private_page=True)


def faq(request):
    return page(request, "faq.html", "پرسش‌های متداول", "پاسخ پرسش‌های متداول درباره مقایسه، موجودی و بازدید از شوروم فرما.")


def csrf_failure(request, reason=""):
    return render(request, "403.html", status=403)
