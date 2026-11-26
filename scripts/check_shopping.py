"""Exercise the seeded catalog and cart. Requires a local server and Python Playwright."""
import argparse
from urllib.parse import urlsplit

from playwright.sync_api import expect, sync_playwright


def check(browser, base):
    page = browser.new_page(viewport={"width": 1440, "height": 960}, reduced_motion="reduce")
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.goto(base + "/shop/")
    page.keyboard.press("Tab")
    expect(page.locator(".skip-link")).to_be_focused()
    page.evaluate("window.samePage = true")
    page.locator("#category-sidebar-kitchen").click()
    page.wait_for_url("**category=kitchen**")
    page.locator("#brand-kwc").check()
    page.wait_for_url("**brand=kwc**")
    page.wait_for_function("!document.querySelector('.htmx-settling')")
    shared = page.url
    page.locator("#catalog-sort").select_option("price-desc")
    page.wait_for_url("**sort=price-desc**")
    assert page.evaluate("window.samePage")
    page.go_back()
    expect(page.locator("#catalog-sort")).to_have_value("featured")
    page.goto(shared)
    expect(page.locator("#brand-kwc")).to_be_checked()
    page.locator("#card-arc .product-title a").click()
    page.evaluate("window.samePage = true")
    page.locator("#finish-steel").click()
    expect(page.locator(".purchase .stock")).to_have_text("ناموجود")
    assert "kind=quote" in page.locator(".purchase-button").get_attribute("href")
    page.locator("#finish-black").click()
    expect(page.locator("[data-sku]")).to_have_text("ARC-01-BK")
    page.locator("button.purchase-button").click()
    expect(page.locator("#cart-count")).to_contain_text("۱")
    assert page.evaluate("window.samePage")
    page.locator("#add-status a").click()
    page.evaluate("window.samePage = true")
    page.locator(".quantity-form input[name=quantity]").fill("۲")
    page.locator(".quantity-form button").click()
    expect(page.locator(".basket-line-total")).to_contain_text("۲۳٬۸۰۰٬۰۰۰")
    expect(page.locator(".summary-total")).to_contain_text("۲۳٬۸۰۰٬۰۰۰")
    expect(page.locator("#cart-count")).to_contain_text("۲")
    assert page.evaluate("window.samePage")
    page.locator(".quantity-form input[name=quantity]").fill("۴")
    page.locator(".quantity-form button").click()
    expect(page.locator("#cart-content [role=alert]")).to_be_visible()
    expect(page.locator("#cart-count")).to_contain_text("۲")
    page.locator(".order-summary .button").click()
    assert urlsplit(page.url).path == "/checkout/"
    expect(page.locator("#request")).to_contain_text("پرداخت آنلاین در دسترس نیست")
    page.set_viewport_size({"width": 320, "height": 800})
    page.goto(base + "/shop/?q=forma-no-results")
    expect(page.locator(".empty-state")).to_be_visible()
    page.locator("#open-filters").click()
    page.route("**/shop/?**", lambda route: route.abort() if route.request.headers.get("hx-request") else route.continue_())
    page.locator("#apply-filters").click()
    expect(page.locator("dialog [data-network-status]")).to_be_focused()
    page.keyboard.press("Escape")
    expect(page.locator("#open-filters")).to_be_focused()
    assert not errors, errors
    page.close()


if __name__ == "__main__":
    cli = argparse.ArgumentParser()
    cli.add_argument("--url", default="http://127.0.0.1:8011")
    cli.add_argument("--engine", choices=["chromium", "firefox", "webkit"], default="chromium")
    args = cli.parse_args()
    with sync_playwright() as pw:
        browser = getattr(pw, args.engine).launch()
        check(browser, args.url)
        browser.close()
    print(f"{args.engine}: filters, Back, variants, purchase, quantity, stock and recovery passed.")
