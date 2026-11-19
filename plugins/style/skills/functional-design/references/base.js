// Logan's functional-design scripts. Paste into a <script> at the end of the page body.

// The bookkeeping disclosure (<details class="more" data-remember>) stays open once opened.
// One fixed key, so pages on the same site share the choice. Pages still work when storage is blocked.
(() => {
  const KEY = "logan-details-open";
  let open = false;
  try { open = localStorage.getItem(KEY) === "1"; } catch (e) {}
  document.querySelectorAll("details[data-remember]").forEach(d => {
    d.open = open;
    d.addEventListener("toggle", () => { if (printing) return; try { localStorage.setItem(KEY, d.open ? "1" : "0"); } catch (e) {} });
  });
  let printing = false;
  addEventListener("beforeprint", () => { printing = true; document.querySelectorAll("details[data-remember]").forEach(d => { d.dataset.was = d.open ? "1" : "0"; d.open = true; }); });
  addEventListener("afterprint", () => { document.querySelectorAll("details[data-remember]").forEach(d => { d.open = d.dataset.was === "1"; }); setTimeout(() => printing = false); });
})();

// Exact values on hover, tap or keyboard focus, for any element with a data-tip (plain text) or data-tip-html attribute.
// Give chart marks a larger transparent twin carrying the same data-tip, so they're easy to tap.
(() => {
  let tip = document.getElementById("tip");
  if (!tip) { tip = document.createElement("div"); tip.id = "tip"; tip.hidden = true; document.body.appendChild(tip); }
  const show = (el, x, y) => {
    if (el.dataset.tipHtml != null) tip.innerHTML = el.dataset.tipHtml; else tip.textContent = el.dataset.tip;  // tip-html is built by the kit from escaped strings
    tip.hidden = false;
    tip.style.left = Math.max(8, Math.min(innerWidth - tip.offsetWidth - 8, x + 12)) + "px";
    tip.style.top = Math.max(8, Math.min(innerHeight - tip.offsetHeight - 8, y - tip.offsetHeight - 10)) + "px";
  };
  const at = e => { const el = e.target.closest && e.target.closest("[data-tip], [data-tip-html]"); if (el) show(el, e.clientX, e.clientY); else tip.hidden = true; };
  document.addEventListener("pointermove", at);
  document.addEventListener("pointerdown", at);
  document.addEventListener("focusin", e => { const el = e.target.closest("[data-tip], [data-tip-html]"); if (el) { const r = el.getBoundingClientRect(); show(el, r.left + r.width / 2, r.top); } });
  document.addEventListener("focusout", () => tip.hidden = true);
  addEventListener("scroll", () => tip.hidden = true, { passive: true });
})();

// The way back. An artifact has no back button, so a link with data-back returns through the history
// (to the same scroll position on the page I came from) when there is one, and follows its href when there isn't.
document.addEventListener("click", e => {
  const a = e.target.closest && e.target.closest("a[data-back]");
  let same = false; try { same = new URL(document.referrer).origin === location.origin; } catch (err) {}
  if (a && same && history.length > 1) { e.preventDefault(); history.back(); }
});
