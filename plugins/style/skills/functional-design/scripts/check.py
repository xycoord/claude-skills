"""Check a page against the functional-design rules a program can test.

    uv run --with playwright python check.py PAGE.html [--shots DIR]

Loads the page in headless Chromium at 1280px (light and dark) and at 390px, and prints every
failure with a few examples. The phone run only checks that the page doesn't break. Exits 1 if anything fails. With --shots, it also
saves full-page screenshots for you to look at, which this script can't do for you.
If Chromium is missing, run: uv run --with playwright playwright install chromium
"""
import argparse, glob, pathlib, sys
from playwright.sync_api import sync_playwright

PROBE = r"""
() => {
  const out = {}, add = (k, el, note) => { (out[k] ||= []).push(note || describe(el)); };
  const describe = el => { const t = (el.innerText || el.textContent || "").trim().replace(/\s+/g, " ").slice(0, 60);
    return `<${el.tagName.toLowerCase()}${el.className && typeof el.className === "string" ? "." + el.className.trim().split(/\s+/).join(".") : ""}> ${t}`; };
  const visible = el => { const r = el.getBoundingClientRect(), s = getComputedStyle(el); return r.width > 0 && r.height > 0 && s.visibility !== "hidden" && s.display !== "none"; };
  const inSvg = el => !!el.closest("svg");
  const ownText = el => [...el.childNodes].filter(n => n.nodeType === 3).map(n => n.textContent).join("").trim();
  // Any CSS colour (including color-mix and oklab results) to [r, g, b, a], by painting it on a 1px canvas.
  const cv = document.createElement("canvas"); cv.width = cv.height = 1; const cx = cv.getContext("2d", { willReadFrequently: true });
  const rgb = c => { if (!c || c === "transparent" || /rgba?\(0, 0, 0, 0\)/.test(c)) return [0, 0, 0, 0]; cx.clearRect(0, 0, 1, 1); cx.fillStyle = "#000"; cx.fillStyle = c; cx.fillRect(0, 0, 1, 1); const d = cx.getImageData(0, 0, 1, 1).data; return [d[0], d[1], d[2], d[3] / 255]; };
  const lum = ([r, g, b]) => { const f = v => (v /= 255) <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4; return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b); };
  const bgOf = el => { for (let e = el; e; e = e.parentElement) { const c = rgb(getComputedStyle(e).backgroundColor); if (c.length < 4 || c[3] > 0.9) return c; } return [255, 255, 255]; };
  const pageBg = rgb(getComputedStyle(document.body).backgroundColor).slice(0, 3).join();
  const isCode = el => !!el.closest("code, pre, kbd, samp, .id, .tok");
  const control = el => el.matches("input, select, textarea, button, #tip, #tip *");
  const inViz = el => !!el.closest("[data-viz]");  // views whose colour encodes values (interp.js) may tint backgrounds
  const emoji = /[\u{1F300}-\u{1FAFF}\u{2600}-\u{27BF}]/u;
  const cards = {};
  for (const el of document.body.querySelectorAll("*")) {
    if (!visible(el) || inSvg(el) || el.matches("script, style, link, meta")) continue;
    const s = getComputedStyle(el), text = ownText(el), size = parseFloat(s.fontSize);
    if (text) {
      if (size < 13) add("text smaller than 13px", el);
      if (s.textTransform === "uppercase" || (parseFloat(s.letterSpacing) > size * 0.05 && text === text.toUpperCase() && /[A-Z]{3}/.test(text))) add("spaced or uppercase labels", el);
      if (/mono|fira code|menlo|consolas|courier/i.test(s.fontFamily) && !isCode(el)) add("monospace outside IDs and code", el);
      if (/ · |·/.test(text)) add("metadata joined with middle dots", el);
      if (/[→↗›»]\s*$/.test(text) && el.closest("a, button")) add("arrow on a link or button", el);
      if (emoji.test(text)) add("emoji", el);
      const fg = rgb(s.color), bg = bgOf(el), L1 = lum(fg), L2 = lum(bg), ratio = (Math.max(L1, L2) + 0.05) / (Math.min(L1, L2) + 0.05);
      if (ratio < (size >= 24 ? 3 : 4.5)) add("low text contrast (under 4.5:1, or 3:1 at 24px and up)", el, `${describe(el)} (${ratio.toFixed(2)}:1)`);
    }
    if (s.boxShadow !== "none" && !control(el)) add("shadows", el);
    if (/gradient/.test(s.backgroundImage)) add("gradients", el);
    const bgc = rgb(s.backgroundColor);
    if (!inViz(el) && (bgc.length < 4 || bgc[3] > 0.05) && bgc.slice(0, 3).join() !== pageBg && !control(el) && !el.matches("pre, code, mark") && el !== document.body && el !== document.documentElement)
      add("tinted backgrounds (cards, panels, pills)", el);
    const r = el.getBoundingClientRect(), rad = parseFloat(s.borderTopLeftRadius);
    if (!control(el) && !inViz(el) && r.height < 32 && rad >= r.height / 2 - 1 && (s.borderTopStyle !== "none" || (bgc[3] ?? 1) > 0.05)) add("pills or badges", el);
    const boxed = ["Top", "Right", "Bottom", "Left"].every(k => s[`border${k}Style`] !== "none" && parseFloat(s[`border${k}Width`]) > 0);
    if (boxed && rad > 0 && parseFloat(s.paddingTop) >= 8 && !control(el)) { const k = el.tagName + "." + el.className; (cards[k] ||= []).push(el); }
  }
  const pb = rgb(getComputedStyle(document.body).backgroundColor);
  if (matchMedia("(prefers-color-scheme: light)").matches && !(pb.length >= 3 && pb.slice(0, 3).every(v => v >= 250) && (pb[3] ?? 1) > 0.9) && !(pb[3] === 0))
    add("page background isn't plain white", document.body, `body background is ${getComputedStyle(document.body).backgroundColor}`);
  for (const els of Object.values(cards)) if (els.length >= 2) els.forEach(el => add("cards (bordered, rounded boxes)", el));
  return out;
}
"""
TOUCH = r"""
() => {
  const out = [], seen = new Set();
  const w = Math.max(document.documentElement.scrollWidth, document.body.scrollWidth, innerWidth);
  if (w > 391) out.push(["scrolls sideways on a phone", `page is ${w}px wide on a 390px screen`]);
  for (const el of document.querySelectorAll("a, button, summary, input, select, textarea, [tabindex]")) {
    const r = el.getBoundingClientRect(), s = getComputedStyle(el);
    if (!r.width || s.visibility === "hidden") continue;
    if (el.matches("a") && s.display === "inline" && el.closest("p, li, dd, td, figcaption") && !el.closest("nav")) continue;  // links in sentences are exempt
    if (el.closest("svg")) continue;  // chart marks carry their own larger hit areas
    if (false && r.height < 43.5) { /* tap targets: off, because Logan reads these pages on a laptop */ const t = `<${el.tagName.toLowerCase()}> ${(el.innerText || el.value || "").trim().slice(0, 40)} (${Math.round(r.height)}px)`; if (!seen.has(t)) { seen.add(t); out.push(["tap targets under 44px", t]); } }
  }
  return out;
}
"""

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("page"); ap.add_argument("--shots")
    a = ap.parse_args()
    url = pathlib.Path(a.page).resolve().as_uri()
    fails, errors = {}, []
    with sync_playwright() as pw:
        try:
            b = pw.chromium.launch()
        except Exception:  # this Playwright's own browser isn't downloaded; use any Chromium already cached
            found = sorted(glob.glob(str(pathlib.Path.home() / ".cache/ms-playwright/chromium-*/chrome-linux*/chrome")))
            if not found: sys.exit("No Chromium found. Run: uv run --with playwright playwright install chromium")
            b = pw.chromium.launch(executable_path=found[-1])
        for tag, kw in [("desk", dict(viewport={"width": 1280, "height": 900}, color_scheme="light")),
                        ("dark", dict(viewport={"width": 1280, "height": 900}, color_scheme="dark")),
                        ("phone", dict(viewport={"width": 390, "height": 844}, device_scale_factor=2, is_mobile=True, has_touch=True))]:
            p = b.new_context(**kw).new_page()
            p.on("pageerror", lambda e, tag=tag: errors.append(f"{tag}: {e}"))
            p.goto(url); p.wait_for_load_state("networkidle"); p.wait_for_timeout(400)
            p.evaluate("document.querySelectorAll('details').forEach(d => d.open = true)")  # check what disclosures hide too
            p.wait_for_timeout(200)
            for k, v in p.evaluate(PROBE).items():
                fails.setdefault(k, {}).setdefault(tag, v)
            if tag == "phone":
                for k, v in p.evaluate(TOUCH):
                    fails.setdefault(k, {}).setdefault(tag, []).append(v)
            if a.shots:
                pathlib.Path(a.shots).mkdir(parents=True, exist_ok=True)
                p.screenshot(path=f"{a.shots}/{tag}.png", full_page=True)
        b.close()
    for e in errors: print("Script error:", e)
    for k, by in fails.items():
        n = max(len(v) for v in by.values())
        print(f"FAIL {k} ({n}, in {', '.join(by)})")
        for ex in list(dict.fromkeys(x for v in by.values() for x in v))[:5]: print("   ", ex)
    if not fails and not errors: print("All checks pass. Now look at the screenshots yourself.")
    sys.exit(1 if fails or errors else 0)

if __name__ == "__main__":
    main()
