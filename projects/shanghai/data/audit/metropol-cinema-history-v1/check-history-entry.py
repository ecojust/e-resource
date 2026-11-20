import argparse
import base64
import io
from PIL import Image
import hashlib
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

parser = argparse.ArgumentParser(
    description="Check the historical cinema entry through the district directory and the real map."
)
parser.add_argument("--url", required=True, help="Shanghai project root URL")
parser.add_argument("--output", type=Path, required=True)
parser.add_argument("--viewport", choices=["desktop", "mobile", "both"], default="both")
parser.add_argument("--project", type=Path, default=Path(__file__).resolve().parents[3])
args = parser.parse_args()
base = args.output.resolve()
base.mkdir(parents=True, exist_ok=True)
id = "huangpu-metropol-cinema-historic-front"
url = args.url.rstrip("/")
root = args.project.resolve()
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
meta = json.loads((root / "assets/models/candidates" / id / "manifest.json").read_bytes())


def read_map(page):
    return page.evaluate(
        """id => {
          const app = window.__SHANGHAI_APP__, scene = app.scene, map = scene.map;
          const center = map.getCenter(), state = scene.getCandidateIntegrationState();
          return {
            pose: [center.lng, center.lat, map.getZoom(), map.getPitch(), map.getBearing()],
            hash: location.hash,
            render_record: scene.getLandmarkState().some(record => record.id === id),
            active: state.active.some(record => record.id === id),
            clips: state.clips.some(record => record.id === id),
            collision: [scene.collisionAt(121.46997,31.23784), scene.collisionAt(121.469555,31.23780)],
            location: document.getElementById('location-name').textContent
          };
        }""",
        id,
    )


def screenshot(cdp):
    shot = cdp.send("Page.captureScreenshot", {"format":"png","fromSurface":False,"captureBeyondViewport":False})
    return base64.b64decode(shot["data"])


def crop_digest(png, rect):
    with Image.open(io.BytesIO(png)) as image:
        left, top = round(rect["x"] + 5), round(rect["y"] + 5)
        right, bottom = round(rect["x"] + rect["width"] - 5), round(rect["y"] + rect["height"] - 5)
        return hashlib.sha256(image.crop((left,top,right,bottom)).tobytes()).hexdigest()


def verify_city_label(page, historical_requests):
    panel = page.locator("#panel-toggle")
    if panel.get_attribute("aria-expanded") == "false":
        panel.click()
    page.locator("#place-search").fill("大光明")
    page.locator('[data-place="huangpu-grand-theatre"]').click()
    title = page.locator("#location-name").inner_text()
    assert title.startswith("大光明大戏院") and not page.locator("#history-open").is_visible()
    if panel.get_attribute("aria-expanded") == "true":
        panel.click()
    count = page.locator("#landmark-count").inner_text()
    assert count == "91"
    page.evaluate("""() => {
      const s=window.__SHANGHAI_APP__.scene, m=s.map;
      m.stop(); m.setMaxBounds(null); m.setCenterClampedToGround(true);
      m.jumpTo({center:[121.45,31.2],zoom:8,pitch:0,bearing:0,elevation:0,
                padding:{top:0,bottom:0,left:0,right:0}});
      s.refreshBuildingBeacons();
    }""")
    page.wait_for_function("""() => {
      const s=window.__SHANGHAI_APP__.scene,b=s.getBuildingBeaconState();
      return b.viewportLabelCount===91 && !b.overlapFallbackCount && b.sourceIds.every(id=>s.map.isSourceLoaded(id));
    }""", timeout=360000,polling=600)
    labels = page.evaluate("""id => {
      const s=window.__SHANGHAI_APP__.scene,b=s.getBuildingBeaconState(),p=b.labelPositions.find(r=>r.id===id);
      return {count:b.count,viewport_label_count:b.viewportLabelCount,exact_hits:b.labelPositions.filter(r=>s.pickBuildingBeacon(r)===r.id).length,
              target:p,hit:s.pickBuildingBeacon(p),hit_element:document.elementFromPoint(p.x,p.y)?.tagName};
    }""",id)
    assert labels["exact_hits"]==labels["count"]==91 and labels["hit"]==id and labels["hit_element"]=="CANVAS", labels
    assert not historical_requests
    page.mouse.click(labels["target"]["x"],labels["target"]["y"])
    page.wait_for_function("""id=>new URLSearchParams(location.hash.slice(1)).get('landmark')===id""",arg=id,timeout=120000)
    page.locator("#history-open").wait_for(state="visible")
    page.wait_for_function("""() => {
        const s=window.__SHANGHAI_APP__.scene;
        return !s.map.isMoving() && s.collisionAt(121.46997,31.23784)==='building'
               && s.collisionAt(121.469555,31.23780)===null;
    }""",timeout=240000,polling=500)
    state = read_map(page)
    assert state["location"]=="大上海大戏院历史立面（1933年建筑）" and not state["active"] and not state["clips"] and not state["render_record"]
    assert not page.locator("#history-dialog").is_visible() and not historical_requests
    return {"from_landmark":"huangpu-grand-theatre","from_title":title,"to_landmark":id,"before_click":{"labels":labels},
            "after_mouse_click":state,"archive_requests_before_explicit_action":len(historical_requests),
            "action":page.locator("#history-open").inner_text()}


def run(browser, n, w, h):
    c = browser.new_context(
        viewport={"width": w, "height": h},
        has_touch=n == "mobile",
        is_mobile=n == "mobile",
        device_scale_factor=1,
        accept_downloads=True,
        ignore_https_errors=True,
    )
    p = c.new_page()
    cdp = c.new_cdp_session(p)
    p.set_default_timeout(200000)
    p.on("console", lambda m: print(n, m.type, m.text[:450], flush=True) if m.type == "error" else None)
    errs = []
    p.on("pageerror", lambda error: (errs.append(str(error)), print(n, "pageerror", error, flush=True)))
    history = []
    p.on(
        "request", lambda request: history.append(request.url) if "/" + id + "/" in request.url else None
    )
    p.goto(url + "/landmarks.html", wait_until="domcontentloaded")
    card = p.locator("#building-" + id)
    assert card.get_by_text("查看历史立面").count() == 1
    card.get_by_role("heading").get_by_role("link").click(timeout=30000)
    print(n, "selected", p.url, flush=True)
    p.wait_for_function(
        "Boolean(window.__SHANGHAI_APP__) || document.querySelector('#retry-button')?.hidden===false",
        polling=500,
        timeout=260000,
    )
    assert p.evaluate("Boolean(window.__SHANGHAI_APP__)"), p.locator("#loading-message").inner_text()
    p.wait_for_function("document.querySelector('#loading').classList.contains('loaded')", timeout=160000)
    p.wait_for_timeout(1200)
    print(
        n,
        "ready",
        p.locator("#history-open").is_visible(),
        p.locator("#start-walk").is_visible(),
        flush=True,
    )
    pre = read_map(p)
    assert (
        id in pre["hash"]
        and not pre["render_record"]
        and not pre["active"]
        and not pre["clips"]
        and not history
    )
    assert p.locator("#history-open").is_visible() and not p.locator("#start-walk").is_visible()
    assert pre["collision"] == ["building", None], pre
    p.wait_for_function("getComputedStyle(document.querySelector('#loading')).visibility==='hidden'", timeout=120000)
    p.evaluate("""() => new Promise(done => {
      const m=window.__SHANGHAI_APP__.scene.map;
      m.once('render',()=>{m.once('render',()=>done());m.triggerRepaint()});m.triggerRepaint();
    })""")
    (base / (n + "-site.png")).write_bytes(screenshot(cdp))
    beacon = None
    if n == "desktop":
        beacon = verify_city_label(p, history)
        print(n, "91 labels and real click verified", flush=True)
        (base / "beacon-position.json").write_text(json.dumps(beacon,ensure_ascii=False,indent=2)+"\n")
        pre = read_map(p)
    (p.locator("#history-open").tap() if n == "mobile" else p.locator("#history-open").click())
    f = p.frame_locator("#history-frame")
    f.locator("#status").filter(has_text="12,808").wait_for(timeout=240000)
    assert p.locator("#history-dialog").is_visible() and f.locator("canvas").is_visible()
    assert f.locator("#downloads a").count() == 4
    if n == "mobile":
        assert p.evaluate("document.documentElement.scrollWidth===innerWidth")
    assert f.locator("body").evaluate("el=>el.scrollWidth<=innerWidth")
    shot = screenshot(cdp)
    (base / (n + "-archive.png")).write_bytes(shot)
    cv = f.locator("canvas")
    r = cv.bounding_box()
    a = crop_digest(shot, r)
    print(n, "archive ready", flush=True)
    x = r["x"] + r["width"] * 0.45
    y = r["y"] + r["height"] * 0.48
    if n == "mobile":
        touch = c.new_cdp_session(p)
        for i in range(7):
            touch.send(
                "Input.dispatchTouchEvent",
                {
                    "type": "touchStart" if i == 0 else "touchMove",
                    "touchPoints": [{"x": x + 9 * i, "y": y + 3 * i}],
                },
            )
        touch.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})
        touch.detach()
    else:
        p.mouse.move(x, y)
        p.mouse.down()
        p.mouse.move(x + 54, y + 21, steps=6)
        p.mouse.up()
    p.wait_for_timeout(400)
    b = crop_digest(screenshot(cdp), r)
    print(n, "orbit sampled", a, b, flush=True)
    assert a != b
    a_before = a
    f.locator("#detail").select_option("lod")
    f.locator("#status").filter(has_text="9,072").wait_for(timeout=240000)
    print(n, "LOD verified",flush=True)
    dl = {}
    for a in f.locator("#downloads a").all():
        href = a.get_attribute("href")
        role = next(k for k, asset in meta["assets"].items() if href.endswith("/" + asset["file"]))
        with p.expect_download() as downloaded:
            a.click()
        file = downloaded.value.path()
        dl[role] = sha(file)
        assert dl[role] == meta["assets"][role]["sha256"]
    print(n, "four downloads verified", flush=True)
    before = read_map(p)
    if n == "desktop":
        cv.click()
        p.keyboard.press("Escape")
    else:
        link = f.locator("#site-return")
        link.scroll_into_view_if_needed()
        link.tap(position={"x":32,"y":10})
    p.wait_for_function("!document.querySelector('#history-dialog').open", polling=250, timeout=180000)
    p.locator("#history-dialog").wait_for(state="hidden", timeout=180000)
    p.wait_for_function("!document.querySelector('#history-frame').getAttribute('src')")
    post = read_map(p)
    print(n, "closed", flush=True)
    assert (
        before["pose"] == post["pose"]
        and post["pose"] == pre["pose"]
        and post["hash"] == pre["hash"]
        and post["collision"] == pre["collision"]
    )
    opened_focus = p.evaluate("document.activeElement.id")
    assert opened_focus == "history-open"
    (p.locator("#history-open").tap() if n == "mobile" else p.locator("#history-open").click())
    p.locator("#history-close").click()
    p.locator("#history-dialog").wait_for(state="hidden")
    assert read_map(p)["pose"] == post["pose"]
    assert not post["render_record"] and not post["active"] and not post["clips"]
    # Ensure another destination cannot fetch or re-open the historical model.
    count = len(history)
    menu = p.locator("#panel-toggle")
    if menu.get_attribute("aria-expanded") == "false":
        menu.click()
    search = p.locator("#place-search")
    search.fill("大光明")
    p.locator('[data-place="huangpu-grand-theatre"]').click()
    p.wait_for_function("!document.querySelector('#history-open').offsetWidth")
    assert not p.locator("#history-open").is_visible() and len(history) == count
    # A direct selection inside the map exposes the same explicit action.
    if menu.get_attribute("aria-expanded") == "false":
        menu.click()
    search.fill("大上海大戏院")
    p.locator('[data-place="' + id + '"]').click()
    p.locator("#history-open").wait_for(state="visible")
    assert not p.locator("#history-dialog").is_visible() and len(history) == count
    bound = [
        "index.html",
        "landmarks.html",
        "metropol-cinema-history.html",
        "data/candidate-city-integrations.json",
        "src/app.js",
        "src/candidate-city-integrations.js",
        "src/map-scene.js",
        "src/historical-view.js",
        "src/historical-view.css",
        "src/precise-registration-ui.js",
        "src/candidate-asset-viewer.js",
    ]
    assert not errs, errs
    r = {
        "passed": True,
        "directory_and_in_map_selection_verified": True,
        "viewport": [w, h],
        "source_url": url,
        "city_beacon": beacon,
        "catalog_destinations": json.loads((root / "data/candidate-city-integrations.json").read_text())[
            "resulting_city_count"
        ],
        "input_sha256": {path: sha(root / path) for path in bound},
        "screens": {k: sha(base / (n + "-" + k + ".png")) for k in ("site", "archive")},
        "history_requests_before_open": 0,
        "site_before": pre,
        "site_after": post,
        "close_method": "Escape inside the viewer" if n == "desktop" else "Inner return link",
        "outer_return_button_checked": True,
        "restored_focus": opened_focus,
        "rotated_model": True,
        "canvas_crop_sha256_before_after_orbit": [a_before, b],
        "selected_lod": True,
        "verified_download_sha256": dl,
        "capture_method": "Chromium viewport composition; canvas crop for orbit comparison",
        "other_destination_historic_requests": len(history) - count,
        "page_errors": errs,
    }
    (base / (n + ".json")).write_text(json.dumps(r, ensure_ascii=False, indent=2) + "\n")
    print(n, "completed", flush=True)
    c.close()


with sync_playwright() as pw:
    browser = pw.chromium.launch(
        executable_path="/usr/bin/chromium",
        headless=True,
        args=[
            "--no-sandbox",
            "--remote-debugging-port=9345",
            "--use-angle=swiftshader",
            "--enable-unsafe-swiftshader",
            "--ignore-certificate-errors",
            "--disable-dev-shm-usage",
        ],
    )
    for n, w, h in [("desktop", 1160, 790), ("mobile", 390, 844)]:
        if args.viewport in ("both", n):
            run(browser, n, w, h)
    browser.close()
