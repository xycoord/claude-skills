// Logan's default page scripts. Paste into a <script> at the end of the page body.

// The bookkeeping disclosure (<details class="more" data-remember>) stays open once opened.
// One fixed key, so pages on the same site share the choice. Pages still work when storage is blocked.
(() => {
  const KEY = "logan-details-open";
  let open = false;
  try { open = localStorage.getItem(KEY) === "1"; } catch (e) {}
  document.querySelectorAll("details[data-remember]").forEach(d => {
    d.open = open;
    d.addEventListener("toggle", () => { try { localStorage.setItem(KEY, d.open ? "1" : "0"); } catch (e) {} });
  });
  addEventListener("beforeprint", () => document.querySelectorAll("details[data-remember]").forEach(d => d.open = true));
})();

// Exact values on hover, tap or keyboard focus, for any element with a data-tip attribute.
// Give chart marks a larger transparent twin carrying the same data-tip, so they're easy to tap.
(() => {
  let tip = document.getElementById("tip");
  if (!tip) { tip = document.createElement("div"); tip.id = "tip"; tip.hidden = true; document.body.appendChild(tip); }
  const show = (el, x, y) => {
    tip.textContent = el.dataset.tip; tip.hidden = false;
    tip.style.left = Math.max(8, Math.min(innerWidth - tip.offsetWidth - 8, x + 12)) + "px";
    tip.style.top = Math.max(8, Math.min(innerHeight - tip.offsetHeight - 8, y - tip.offsetHeight - 10)) + "px";
  };
  const at = e => { const el = e.target.closest && e.target.closest("[data-tip]"); if (el) show(el, e.clientX, e.clientY); else tip.hidden = true; };
  document.addEventListener("pointermove", at);
  document.addEventListener("pointerdown", at);
  document.addEventListener("focusin", e => { const el = e.target.closest("[data-tip]"); if (el) { const r = el.getBoundingClientRect(); show(el, r.left + r.width / 2, r.top); } });
  document.addEventListener("focusout", () => tip.hidden = true);
  addEventListener("scroll", () => tip.hidden = true, { passive: true });
})();
