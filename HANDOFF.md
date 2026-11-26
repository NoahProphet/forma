# FORMA implementation and recovery log

Delivery is complete on branch `feature/home-03-showroom-refinements`. [Pull request #1](https://github.com/NoahProphet/forma/pull/1) is open for review. All requested work and checkpoints are recorded below.

- [x] Verify the packed kitchen and render two models with two finishes for each of four categories in both approved cameras.
- [x] Implement HOME-03, read-only demo details and the SKU binding adapter. Three Django tests passed, including all preview links, baked asset coverage and real inventory updates.
- [x] Compare a combined four-fixture change against two independent Cycles reference renders. Mean absolute errors within the equipment regions ranged from 1.31 to 1.78 on a 0–255 channel scale.
- [x] Validate HOME-03 in Chromium at five widths. The 390 px cold test on a 4 Mbps link with 150 ms latency and 4× CPU slowdown measured 597 ms to ready and 76,694 bytes. Eight cached swaps measured 30 ms median and 31 ms maximum.
- [x] Polish. Fixed short-page footers, active mobile navigation, optional form labels, keyboard links to invalid fields and ambiguous Persian FAQ wording. Checked 18 pages at five widths, 70 internal links/images, form recovery and Django tests.
- [x] Animate. Added a 180 ms material-image transition after finish or gallery selection and 160 ms feedback on the updated header quantity. Verified keyboard activation, no-motion alternatives, stock rejection, drawer focus, sharing, Back and no-JavaScript shopping.
- [x] Layout. Replaced mobile journal tiles with image/title rows, simplified the brand directory and widened the checkout form on tablets and desktop. Verified populated checkout, brand destinations, all 18 pages and five widths. The layout detector returned zero findings.
- [x] Delight. Added a copy action beside the selected finish SKU. Confirmed the actual clipboard value for two finishes, keyboard activation, denied-permission selection fallback, 320 px and no-JavaScript rendering.
- [x] Run the site-wide audit and archive the screenshot comparisons.
- [x] Pushed the feature branch and opened [pull request #1](https://github.com/NoahProphet/forma/pull/1) for review. The base is the empty initialization commit.

The generated web assets and editable scene are in the repository. The renderer and its temporary PNG outputs can be regenerated independently of Django. The remote was empty on inspection. The local `main` is an empty base commit. No customer database, sessions, environment files or virtual environments belong in the pull request.

## Recheck HOME-03

With Django running locally on port 8011 and the development catalog loaded, run `python scripts/check_kitchen.py` using a Python installation with Playwright and Chromium. Run `.venv/Scripts/python.exe manage.py test` for the isolated Django tests. Software emulation covers a throttled mobile connection and CPU. Physical Android hardware was unavailable on the workstation.

## Morning review

Open the [local kitchen](http://127.0.0.1:8011/#home-03) to review the approved architecture. Changing either camera keeps all four fixture selections. Each category has two fictional models with two finishes each. The scene supports direct object clicks, labeled hotspots, category buttons, keyboard operation, zoom, drag-to-pan, refresh restoration and reset. The preview pages show the chosen model, finish and illustrative availability.

| Checkpoint | Principal files and outcome |
| --- | --- |
| `35839e5` · Implementation | `proof/kitchen/`, `store/kitchen.py`, `store/kitchens/`, `templates/kitchen/`, `static/kitchens/`, `static/js/kitchen.js`, `static/css/kitchen.css`. Approved room, asset pipeline, catalog adapter, runtime and fixture pages. |
| `9607098` · Polish | Shared stylesheet, header, FAQ and inquiry form. Improved current-page cues, optional fields, linked validation and short-page footers. |
| `2d036ee` · Animate | Variant view, product and cart partials and shared stylesheet. Material image changes and updated quantities get brief feedback. Reduced-motion users receive the updated content immediately. |
| `16a1bd9` · Layout | Brand index and shared stylesheet. Mobile journal entries use an image and title per row. Brand names form a ruled directory. Checkout gives more room to contact information. |
| `ce59222` · Delight | Product purchase partial, shared icons, JavaScript and styles. The selected finish SKU can be copied for showroom conversations. If clipboard permission is denied, the code is selected for manual copying. |
| `6691556` · Final QA fixes | Kitchen initialization, shop drawer, category markup, base layout, shopping and kitchen browser checks, isolated request tests and review images. |

## Verification

| Test | Result |
| --- | --- |
| Public pages | Chromium, Firefox and WebKit each visited 18 page types at 320, 390, 768, 1024 and 1440 CSS px. All returned successfully in Persian RTL with one main heading. The final pass resolved 72 distinct internal destinations and image URLs per engine, with no page overflow or unexpected console errors. Direct product, project and journal detail titles matched their Open Graph titles. |
| Shopping | All three engines passed shareable filters, sorting, Back, keyboard skip link, product finish changes, unavailable variant quote action, cart updates, line and order totals, stock rejection, checkout access and failed-request recovery. Additional Chromium checks covered comparison, pagination, multi-brand selection, cart preview, search, drawer focus, active filter removal and ordinary form submissions with scripts disabled. |
| Forms and accounts | Five Django tests passed against an isolated database. Coverage includes catalog bindings, asset coverage, preview URLs, CSRF, basket session isolation, stock changes, Persian numerals, checkout snapshots and quote/visit/consultation records. Separate browser tests exercised registration, login, logout, invalid passwords and guest cart retention on a disposable database. |
| Kitchen | All three engines passed model and finish changes in both views, direct hotspots, zoom, keyboard panning, reset, session restoration and recovery from a failed camera image. Independent Cycles renders checked the composite against the room with four changed fixtures. |
| Accessibility | The final axe-core WCAG A/AA scan covered 11 representative pages at both 390 and 1440 px, including a populated cart and checkout. It returned zero violations. Manual interaction tests checked focus after swaps, drawer Escape, skip navigation and reduced motion. |
| Performance | Final Chromium test at 390 px, 2× pixel density, 4 Mbps download, 150 ms network latency and 4× CPU slowdown. No kitchen image loaded before approach. First ready frame took **599 ms** and **76,755 bytes** including component JS and CSS. Eight cached changes measured **30 ms median and 31 ms maximum**. All 80 shipped scene image assets together occupy 1,484,268 bytes. |
| Build and technical checks | Tailwind build, Django checks and migration consistency passed. Production settings check reported two domain-policy warnings for HSTS subdomains and preload. Confirm subdomain TLS coverage with the hosting owner before enabling them. |

The browser audit found that Firefox could restore a direct kitchen URL with the viewport above the scene. Explicit kitchen links now initialize the scene immediately. WebKit skipped the early skip-navigation link with its default tab behavior, so it now has an explicit tab stop. The filter drawer now retains the form and focuses its error on a failed submission. A successful explicit submission closes the drawer and focuses the result count. Catalog text retains full contrast during its entrance transition.

The Impeccable layout detector reported zero layout findings. Its broader source scan flagged the intentional warm palette and advisory differences between the original design inventory and existing shop/header tokens, including pill controls, swatches and semantic feedback colors. The project uses Django static tags, so rendered-browser contrast checks supplemented the source scan.

## Screenshots

Each comparison pairs the approved implementation checkpoint on the left with the final storefront on the right. The home and shop captures also document continuity through the site-wide changes.

| View | Mobile | Desktop |
| --- | --- | --- |
| Home | [390 px](review/home-390.webp) | [1440 px](review/home-1440.webp) |
| Shop | [390 px](review/shop-390.webp) | [1440 px](review/shop-1440.webp) |
| Product | [390 px](review/product-390.webp) | [1440 px](review/product-1440.webp) |
| Interactive kitchen | [Mobile picker](review/kitchen-390.webp) | [Original configuration](review/kitchen-1440.webp) · [Second camera with all four fixtures changed](review/kitchen-camera-b.webp) |
| Supporting pages | [Journal](review/journal-390.webp) | [Brands](review/brands-1440.webp) · [FAQ](review/faq-1440.webp) |

## Reproduce the review

Follow the [local setup instructions](README.md#run-locally) to install dependencies, migrate, seed the development catalog and start the server. In a separate Python environment with Pillow and Playwright installed, run `python -m playwright install chromium firefox webkit`. For each engine, run the following with the local Django server active.

```powershell
foreach ($engine in 'chromium', 'firefox', 'webkit') {
  python scripts/audit_pages.py --engine $engine
  python scripts/check_shopping.py --engine $engine
  python scripts/check_kitchen.py --engine $engine
}
```

## Release dependencies and decisions

- The prototype reuses FORMA references and the supplied Persian business brief. No file explicitly named Design 1 was present. The approved kitchen scene, fictional fixtures and credited CC0 walnut and environment assets are included in the [asset guide](proof/kitchen/README.md).
- Production defaults to the featured-product fallback. Enable demo mode explicitly for a public visual preview, or bind verified geometry and finish assets to actual SKUs for catalog mode. Staff maintain real availability in Django admin. Configurator-specific ordering and assets are versioned in the repository.
- Two synchronized pre-rendered views preserve the approved lighting within the measured mobile budget. A new model or room requires offline rendering. Within a paired reflective group, asset counts grow with the combinations of its fixtures. The camera positions are fixed. Configurations persist within the current browser tab.
- Checkout records requests for showroom follow-up. Payment, fulfilment, live inventory feeds, verified project and product imagery, official map and social links, notifications, analytics, hosting, HTTPS and backup operations still require the inputs listed in the [storefront README](README.md). Browser-engine and throttling checks ran on Windows. Physical Android, iPhone, native Safari and assistive-technology hardware remain unverified.
