"""Check public storefront pages on the seeded development server and optionally capture views."""
import argparse
from io import BytesIO
from pathlib import Path
from urllib.parse import urljoin, urlsplit

from PIL import Image
from playwright.sync_api import sync_playwright


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:8011")
    parser.add_argument("--engine", choices=["chromium", "firefox", "webkit"], default="chromium")
    parser.add_argument("--widths", nargs="+", type=int, default=[320, 390, 768, 1024, 1440])
    parser.add_argument("--capture", type=Path)
    args = parser.parse_args()
    issues = set()
    links = set()
    with sync_playwright() as pw:
        browser = getattr(pw, args.engine).launch()
        page = browser.new_page(locale="fa-IR", reduced_motion="reduce")
        page.on("pageerror", lambda error: issues.add(str(error)))
        page.on("console", lambda msg: issues.add(msg.text) if msg.type == "error" else None)
        paths = dict(home="/", shop="/shop/", product="/product/arc/", brands="/brands/",
                     projects="/projects/", journal="/journal/", about="/about/", faq="/faq/",
                     contact="/contact/", login="/login/", register="/register/", cart="/cart/",
                     checkout="/checkout/", compare="/compare/", empty="/shop/?q=forma-no-results")
        for listing, name, selector in [("projects", "project", ".project-card a"),
                                        ("journal", "article", ".journal-card h2 a")]:
            page.goto(args.url + paths[listing])
            paths[name] = page.locator(selector).first.get_attribute("href")
        page.goto(args.url + "/#home-03")
        page.locator(".k-selection a").wait_for()
        paths["preview"] = page.locator(".k-selection a").get_attribute("href")
        for width in args.widths:
            page.set_viewport_size({"width": width, "height": 844 if width < 768 else 960})
            for name, path in paths.items():
                response = page.goto(urljoin(args.url, path))
                assert response.ok, (path, response.status)
                page.evaluate("document.fonts.ready")
                report = page.evaluate("""() => ({
                  width:document.documentElement.scrollWidth, lang: document.documentElement.lang,
                  dir: document.documentElement.dir, title:document.title,
                  h1:document.querySelectorAll('main h1').length,
                  urls:[...document.querySelectorAll('a[href],img[src]')].map(el=>el.href||el.src),
                  og:document.querySelector('meta[property="og:title"]')?.content
                })""")
                if (report["width"] > width or report["lang"] != "fa" or report["dir"] != "rtl"
                        or report["h1"] != 1 or not report["title"]):
                    issues.add(f"{name} at {width}: width={report['width']}, headings={report['h1']}")
                if name in ("product", "project", "article") and report["og"] != report["title"]:
                    issues.add(f"{path} sharing title")
                for url in report["urls"]:
                    if urlsplit(url).netloc == urlsplit(args.url).netloc:
                        links.add(url.split("#")[0])
                if args.capture and width in (390, 1440) and name in (
                    "home", "shop", "product", "brands", "contact", "faq", "journal",
                ):
                    args.capture.mkdir(parents=True, exist_ok=True)
                    # Capture loaded images and final layout, including lazy in-viewport images.
                    page.evaluate("""() => Promise.all([...document.images].filter(i=>{
                        let r=i.getBoundingClientRect();return r.top<innerHeight && r.bottom>0
                    }).map(i=>i.decode().catch(()=>{})))""")
                    image = Image.open(BytesIO(page.screenshot()))
                    image.save(args.capture / f"{name}-{width}.webp", quality=82)
        for url in sorted(links):
            response = page.request.get(url)
            if not response.ok:
                issues.add(f"{response.status} {url}")
        print(f"{args.engine}: {len(paths)} pages at {args.widths}, {len(links)} local links and images.")
        browser.close()
    if issues:
        raise SystemExit("\n".join(sorted(issues)))


if __name__ == "__main__":
    main()
