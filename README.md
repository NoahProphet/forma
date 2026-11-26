# FORMA storefront

Persian RTL storefront for the FORMA showroom in Rasht, built with Django templates, Tailwind CSS and htmx. The `formamart.ir` workspace started empty. The implementation reuses the home and finish-selection references, wordmark and imagery from the neighboring `formaland.ir` prototype. No file was explicitly named Design 1, so the two matching FORMA mockups served as the visual baseline. The attached Persian requirements sheet served as the brief.

## Run locally

Python 3.12+ and Node.js 20+ are needed. From this folder in PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
npm ci
npm run build
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py seed_demo
.\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8011
```

Open [the local store](http://127.0.0.1:8011/). Run `manage.py createsuperuser` with the same Python executable to sign in at [Django admin](http://127.0.0.1:8011/admin/). Use `npm run watch` during template or CSS edits. The build copies pinned htmx and Vazirmatn assets locally, so the storefront needs no client-side CDN.

The demo command keeps existing records and runs only with `DJANGO_DEBUG=1`. Use a fresh database for production. In admin, add categories, brands, products, finishes, variant SKU/price/stock, and variant-specific galleries. Staff can also publish projects, attach their featured products, publish journal articles and mark requests as handled. Keep published slugs stable so shared links continue to resolve.

## Website sections

Use the [FORMA website section map](SECTIONS.md) to refer to specific pages, sections and shared components during design reviews.

## Browsing and checkout

- The homepage opens with a full-bleed showroom photograph and a Persian catalog link. The category gallery leads to the shop. HOME-03 shows the interactive kitchen when an environment is enabled, followed by project stories.
- The shop supports search, category, brand, finish, availability, a toman price range, sorting, pagination and a comparison list for up to three products. For a shareable local example, open [kitchen products with a matte-black KWC finish](http://127.0.0.1:8011/shop/?category=kitchen&brand=kwc&finish=black&stock=yes).
- Shop cards show model, finish and stock together with the price. Active filters can be removed individually on the results page and in the mobile drawer.
- On [the Arc product](http://127.0.0.1:8011/product/arc/) finish links update its imagery, SKU, price, stock, and purchase or quote action together. Product, project and article routes render directly on the server with Persian titles and sharing metadata.
- Cart writes use CSRF protection and server-side stock and quantity validation. Quantity changes update line totals, the basket total and the header count together. Both the cart and filters work with standard forms when JavaScript is disabled.
- Checkout saves a purchase enquiry with a snapshot of the basket and retains the cart. Contact forms save consultation, price and visit requests in the admin queue. A tracking number confirms a saved request. Staff follow-up currently happens through admin and the showroom phone.

## Verification

The [implementation report](HANDOFF.md) includes the phase checkpoints, screenshot comparisons, cross-browser results and production dependencies. The [kitchen asset guide](proof/kitchen/README.md) describes how to regenerate the scene and link real products.

Checked Chromium at 1440 and 390 px and checked for horizontal overflow at 320 px. Exercised category browsing, shareable filters, sorting, pagination, Back, product comparison, finish and gallery selection, cart totals and stock rejection, checkout and visit forms, direct product and project metadata, keyboard focus, a failed request, and the standard forms with JavaScript disabled. Django checks also covered CSRF enforcement, cart session isolation and the quote form's selected variant.

The redesign was compared to the previous home, shop, product and filled-cart layouts at 1440 and 390 px. The review informed the final material-photo crop, the consistent image framing on the shop, and the removal of a repeated project image. The Taste Skill checker reported open findings on its fixed screen-height rules and RTL alignment heuristics. The storefront uses content-sized sections so the next step in browsing is visible on the first screen.

## Content and launch dependencies

| Area | Current state and remaining work |
| --- | --- |
| Catalog and inventory | Local fixture products, brand assignments, prices, stock and projects are illustrative. Replace them with verified catalog data and building-category products. Staff can edit stock in Django admin. A live stock feed or inventory integration needs a source system. |
| Images and wordmark | The wordmark, catalog and project photographs come from the neighboring FORMA prototype. Confirm their usage clearance and replace development imagery with approved photography before launch. The separate HOME-03 environment uses original geometry and two credited CC0 material and lighting resources. |
| Showroom details | The address and landline/mobile are from `photo_2026-11-24_16-32-40.jpg`, the neighboring FORMA identity sheet. Confirm opening hours and supply the exact map pin and official profiles. Set `FORMA_MAP_URL`, `FORMA_WHATSAPP_URL` and `FORMA_INSTAGRAM_URL` to show the respective links. |
| Payment and fulfilment | Connect a payment provider, pricing and delivery rules, order lifecycle, and inventory reservation when those are available. The current checkout offers showroom coordination. |
| Requests and reviews | Contact and checkout requests are saved in Django admin. Configure the staff queue owner and delivery channel if notifications are needed. Add a review source and moderation process before publishing customer reviews. |
| Hosting, SSL and backups | Configure the production WSGI deployment, HTTPS, domain and allowed hosts. Set `DJANGO_DEBUG=0`, `DJANGO_SECRET_KEY`, `DJANGO_ALLOWED_HOSTS`, `FORMA_SITE_ORIGIN`, and persistent paths via `DJANGO_DB_PATH` and `DJANGO_MEDIA_ROOT`. Run `manage.py collectstatic` and serve static and uploaded media through the hosting layer. Agree on database and media backups, test a restore, and schedule session and abandoned-cart cleanup. |
| Analytics and SEO | Add the approved analytics property and any required consent controls. Persian descriptions, canonical URLs and Open Graph tags are rendered by Django. Confirm the canonical host and approved share imagery on the deployed origin. |

## References

- [LG US](https://www.lg.com/us/) for category-first navigation and image-led routes into shopping.
- [htmx documentation](https://htmx.org/docs/) for server-rendered swaps, URL history, loading indicators and out-of-band cart updates.
