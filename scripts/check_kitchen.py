"""Browser acceptance checks for HOME-03. Run with Python Playwright and a local Django server."""
import argparse
import json
from pathlib import Path
from statistics import median

from playwright.sync_api import expect, sync_playwright


def ready(page):
    page.wait_for_function("""() => {
      const root = document.querySelector('#home-03');
      return root && !root.hasAttribute('aria-busy') && root.querySelector('.k-base')?.complete;
    }""")


def click(page, selector):
    page.locator("#home-03 "+selector).click()
    ready(page)


def scene(page):
    return page.locator("#kitchen-data").evaluate("el => JSON.parse(el.textContent)")


def markers_hidden(page):
    page.wait_for_function("""() => {
      const hits = [...document.querySelectorAll('.k-hit')];
      return hits.length > 0 && hits.every(hit => {
        const style = getComputedStyle(hit);
        return style.opacity === '0' && style.pointerEvents === 'none';
      });
    }""")


def functional(browser, url):
    page = browser.new_page(viewport={"width":1440,"height":960})
    errors = []
    page.on("pageerror",lambda error: errors.append(str(error)))
    page.goto(url+"#home-03")
    ready(page)
    config = scene(page)
    for camera in config["views"]:
        click(page,f'[data-camera="{camera}"]')
        for slot_key,slot in config["slots"].items():
            page.locator(".k-viewport").hover(position={"x": 8, "y": 8})
            click(page,f'[data-slot="{slot_key}"]')
            expect(page.locator(f'[data-category="{slot_key}"]')).to_have_attribute("aria-pressed","true")
            for model in slot["models"]:
                click(page,f'[data-model="{model["id"]}"]')
                markers_hidden(page)
                for variant in model["variants"]:
                    click(page,f'[data-finish="{variant["id"]}"]')
                    markers_hidden(page)
                    expect(page.locator(".k-selection a")).to_have_attribute("href",variant["url"])
                    expect(page.locator(".k-stock")).to_contain_text(variant["availability"])
                    stored=page.evaluate("key=>JSON.parse(sessionStorage.getItem(key))","forma.kitchen."+config["id"])
                    assert stored[slot_key]=={"model":model["id"],"finish":variant["id"]}
    saved=page.evaluate("Object.entries(sessionStorage)")
    page.reload()
    ready(page)
    assert saved==page.evaluate("Object.entries(sessionStorage)")
    click(page,'[data-category="hood"]')
    link=page.locator(".k-selection a")
    link.click()
    expect(page.locator("h1")).to_contain_text("سایبان")
    page.go_back()
    ready(page)
    click(page,"[data-plus]")
    before=page.locator(".k-plane").get_attribute("style")
    page.locator(".k-viewport").press("ArrowLeft")
    assert page.locator(".k-plane").get_attribute("style")!=before
    page.locator(".k-viewport").press("Escape")
    expect(page.locator("[data-minus]")).to_be_disabled()
    click(page,".k-reset")
    expect(page.locator('[data-camera="A"]')).to_have_attribute("aria-pressed","true")
    assert page.evaluate("sessionStorage.getItem('forma.kitchen.'+JSON.parse(document.querySelector('#kitchen-data').textContent).id)") is None
    assert not errors,errors
    page.close()


def hotspot_visibility(browser, url):
    page = browser.new_page(viewport={"width": 1440, "height": 960})
    page.goto(url + "#home-03")
    ready(page)
    viewport = page.locator(".k-viewport")
    hit = viewport.locator(".k-hit").first
    page.locator("#kitchen-title").hover()
    expect(hit).to_have_css("opacity", "0")
    expect(hit).to_have_css("pointer-events", "none")
    viewport.hover(position={"x": 8, "y": 8})
    expect(hit).to_have_css("opacity", "1")
    hit.hover()
    expect(hit).to_have_css("pointer-events", "auto")
    # A keyboard user can enter the panel while the mouse is still over the photo.
    page.locator(".k-model").last.focus()
    page.keyboard.press("Enter")
    ready(page)
    markers_hidden(page)
    page.locator("#kitchen-title").hover()
    expect(hit).to_have_css("pointer-events", "none")
    expect(hit).to_have_css("opacity", "0")
    viewport.focus()
    page.keyboard.press("Tab")
    expect(hit).to_be_focused()
    expect(hit).to_have_css("opacity", "1")
    page.keyboard.press("Enter")
    expect(page.locator(".k-model[aria-pressed=true]")).to_be_focused()
    expect(hit).to_have_css("opacity", "0")
    page.close()

    page = browser.new_page(viewport={"width": 390, "height": 844}, has_touch=True, reduced_motion="reduce")
    page.goto(url + "#home-03")
    ready(page)
    viewport = page.locator(".k-viewport")
    hood = viewport.locator('[data-slot="hood"]')
    expect(hood).to_have_css("pointer-events", "none")
    viewport.tap(position={"x": 8, "y": 8})
    expect(hood).to_have_css("opacity", "1")
    hood.tap()
    expect(page.locator('[data-category="hood"]')).to_have_attribute("aria-pressed", "true")
    viewport.tap(position={"x": 8, "y": 8})
    expect(hood).to_have_css("pointer-events", "none")
    viewport.tap(position={"x": 8, "y": 8})
    page.locator('[data-category="sink"]').tap()
    expect(hood).to_have_css("opacity", "0")
    expect(page.locator('[data-category="sink"]')).to_have_attribute("aria-pressed", "true")
    for camera in scene(page)["views"]:
        page.locator(f'[data-camera="{camera}"]').tap()
        ready(page)
        for category, slot in scene(page)["slots"].items():
            page.locator(f'[data-category="{category}"]').tap()
            for model in slot["models"]:
                viewport.tap(position={"x": 8, "y": 8})
                page.locator(f'[data-model="{model["id"]}"]').tap()
                ready(page)
                markers_hidden(page)
                for finish in model["variants"]:
                    viewport.tap(position={"x": 8, "y": 8})
                    expect(hood).to_have_css("opacity", "1")
                    page.locator(f'[data-finish="{finish["id"]}"]').tap()
                    ready(page)
                    markers_hidden(page)
    page.close()


def mobile_performance(browser,url):
    page=browser.new_page(viewport={"width":390,"height":844},device_scale_factor=2,is_mobile=True,has_touch=True)
    cdp=page.context.new_cdp_session(page)
    cdp.send("Network.enable")
    cdp.send("Network.setCacheDisabled",{"cacheDisabled":True})
    cdp.send("Network.emulateNetworkConditions",{"offline":False,"latency":150,
             "downloadThroughput":500000,"uploadThroughput":180000,"connectionType":"cellular4g"})
    cdp.send("Emulation.setCPUThrottlingRate",{"rate":4})
    page.goto(url)
    page.wait_for_load_state("networkidle")
    assert not page.evaluate("performance.getEntriesByType('resource').some(r=>r.name.includes('/kitchens/'))")
    page.evaluate("performance.mark('approach');document.querySelector('#home-03').scrollIntoView()")
    ready(page)
    page.wait_for_function("Array.from(document.querySelectorAll('.k-model img')).every(i=>i.complete && i.naturalWidth)")
    stats=page.evaluate("""() => ({readyMs:Math.round(performance.now()-performance.getEntriesByName('approach')[0].startTime),
       initialAssetBytes:performance.getEntriesByType('resource').filter(r=>r.name.includes('/kitchens/') || ['kitchen.js','kitchen.css'].includes(new URL(r.name).pathname.split('/').pop())).reduce((n,r)=>n+r.transferSize,0)})""")
    click(page,'[data-finish="graphite"]')
    durations=[]
    for value in ("champagne","graphite")*4:
        durations.append(page.evaluate("""value=>new Promise(resolve=>{
          const root=document.querySelector('#home-03');
          const start=performance.now();
          const observer=new MutationObserver(()=>{
            if(root.hasAttribute('aria-busy'))return;
            observer.disconnect();requestAnimationFrame(()=>requestAnimationFrame(()=>resolve(performance.now()-start)));
          });
          observer.observe(root,{attributes:true,attributeFilter:['aria-busy']});
          root.querySelector('[data-finish="'+value+'"]').click();
        })""",value))
    stats.update(cachedMedianMs=round(median(durations)),cachedMaxMs=round(max(durations)))
    page.close()
    return stats


def responsive(browser,url,output):
    for width in (320,390,768,1024,1440):
        page=browser.new_page(viewport={"width":width,"height":900},reduced_motion="reduce")
        page.goto(url+"#home-03")
        ready(page)
        assert page.evaluate("document.documentElement.scrollWidth===innerWidth"),width
        click(page,"[data-plus]")
        click(page,'[data-camera="B"]')
        click(page,".k-reset")
        if output and width in (390,1440):
            output.mkdir(exist_ok=True,parents=True)
            page.locator("#home-03").screenshot(path=str(output/f"kitchen-{width}.png"))
        page.close()


def failure_and_retry(browser,url):
    page=browser.new_page()
    page.goto(url+"#home-03")
    ready(page)
    page.route("**/B-*.webp",lambda route:route.abort())
    page.locator('[data-camera="B"]').click()
    expect(page.locator(".k-retry")).to_be_visible()
    expect(page.locator('[data-camera="A"]')).to_have_attribute("aria-pressed","true")
    page.unroute("**/B-*.webp")
    click(page,".k-retry")
    expect(page.locator('[data-camera="B"]')).to_have_attribute("aria-pressed","true")
    page.close()


if __name__=="__main__":
    cli=argparse.ArgumentParser()
    cli.add_argument("--url",default="http://127.0.0.1:8011/")
    cli.add_argument("--engine", choices=["chromium", "firefox", "webkit"], default="chromium")
    cli.add_argument("--output",type=Path)
    args=cli.parse_args()
    with sync_playwright() as runner:
        browser=getattr(runner, args.engine).launch()
        hotspot_visibility(browser,args.url)
        functional(browser,args.url)
        failure_and_retry(browser,args.url)
        responsive(browser,args.url,args.output)
        if args.engine == "chromium":
            print(json.dumps(mobile_performance(browser,args.url),indent=2))
        print(f"{args.engine}: configuration, camera changes, zoom, persistence, recovery and responsive checks passed.")
        browser.close()

