// Logan's functional-design charts. Paste after base.js and call the function for each chart.
// Every chart draws at its container's real width (so text keeps its size on a phone), redraws on
// resize, uses the kit's colour tokens, labels series directly, and puts each value in a data-tip
// that base.js shows on hover, tap or focus. Colour: c: 1–8 is a series slot (var(--s1)…), and
// c: "crit" / "warn" / "good" is a status. Reference rows and lines are always grey.
//
//   dotChart(el, { metric, from, to, rows, refs, lines, fmt })        a few values with their ranges
//   lineChart(el, { metric, xLabel, x, series, lines, from, to, fmt }) trends over time, layer, …
//   barChart(el, { metric, cats, parts, lines, fmt })                 totals and what they're made of
//   distChart(el, { metric, bins, upper, lower, threshold })          a score distribution per class

const FD = (() => {
  const esc = s => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/"/g, "&quot;");
  const col = c => c === undefined ? "var(--s1)" : typeof c === "number" ? `var(--s${c})` : `var(--${c === "warn" ? "warn-ink" : c})`;
  const measure = (() => { const cv = document.createElement("canvas").getContext("2d"); return (s, px, w = 400) => { cv.font = `${w} ${px}px ${getComputedStyle(document.body).fontFamily}`; return cv.measureText(s).width; }; })();
  const wrap = (s, px, max) => { if (measure(s, px) <= max || !s.includes(" ")) return [s]; const w = s.split(" "); let a = w.shift(); while (w.length && measure(a + " " + w[0], px) <= max) a += " " + w.shift(); return [a, w.join(" ")]; };
  const text = (x, y, s, cls = "", extra = "") => `<text class="${cls}" x="${x}" y="${y}" font-size="13"${extra}>${esc(s)}</text>`;
  const svg = (W, H, label, body, top = 0) => `<svg class="chart" width="${W}" height="${H}" viewBox="0 ${top} ${W} ${H}" role="img" aria-label="${esc(label)}">${body}</svg>`;
  const ticks = (a, b, n = 5) => { const raw = (b - a) / n, mag = 10 ** Math.floor(Math.log10(raw)), step = [1, 2, 2.5, 5, 10].map(m => m * mag).find(s => s >= raw); const out = []; for (let t = Math.ceil(a / step) * step; t <= b + step * 1e-6; t += step) out.push(+t.toFixed(10)); return out; };
  const hit = (x, y, tip, r = 14) => `<circle cx="${x}" cy="${y}" r="${r}" fill="transparent" tabindex="0" data-tip="${esc(tip)}"/>`;
  const draw = (el, fn) => { const go = () => { const w = Math.floor(el.clientWidth); if (w && el.dataset.w != w) { el.dataset.w = w; el.innerHTML = fn(Math.max(260, w)); } }; go(); addEventListener("resize", go); document.fonts && document.fonts.ready.then(() => { delete el.dataset.w; go(); }); };
  return { esc, col, measure, wrap, text, svg, ticks, hit, draw };
})();

// A few values with their ranges: dot = estimate, line = its range (say what the range is in the caption).
// rows: [{ label, v, lo, hi, c }], refs: the same shape, drawn hollow and grey under a "References" heading,
// each labelled with what it is ("Skyline: probe trained on this set", "Shuffled labels"), lines: [{ v, label }] dashed vertical references such as chance.
function dotChart(el, o) {
  const f = o.fmt || (v => v.toFixed(2));
  FD.draw(el, slotW => {
    const W = Math.min(slotW, 680), narrow = W < 460, L = narrow ? 120 : 200, R = narrow ? 52 : 120, rowH = narrow ? 38 : 30, top = 26;
    const all = [...o.rows, ...(o.refs || [])], lo = o.from ?? Math.min(...all.map(d => d.lo ?? d.v), ...(o.lines || []).map(l => l.v)), hi = o.to ?? Math.max(...all.map(d => d.hi ?? d.v));
    const x = v => L + (W - L - R) * (v - lo) / (hi - lo);
    let y = top, s = "";
    const row = (d, ref) => {
      const cy = y + rowH / 2, c = ref ? "var(--muted)" : FD.col(d.c), lines = narrow ? FD.wrap(d.label, 13, L - 10) : [d.label];
      s += `<text class="${ref ? "ref-lab" : "lab"}" x="0" y="${cy + 4 - (lines.length - 1) * 7}" font-size="13">${lines.map((t, k) => `<tspan x="0" dy="${k ? 15 : 0}">${FD.esc(t)}</tspan>`).join("")}</text>`;
      if (d.lo !== undefined && d.hi - d.lo > (hi - lo) * 0.01) s += `<path d="M${x(d.lo)} ${cy}H${x(d.hi)}M${x(d.lo)} ${cy - 5}v10M${x(d.hi)} ${cy - 5}v10" stroke="${c}" stroke-width="2" fill="none"/>`;
      s += `<circle cx="${x(d.v)}" cy="${cy}" r="4.5" fill="${ref ? "var(--bg)" : c}" stroke="${c}" stroke-width="2"/>`;
      s += FD.hit(x(d.v), cy, `${d.label}: ${f(d.v)}${d.lo !== undefined && d.hi > d.lo ? ` (${f(d.lo)}–${f(d.hi)})` : ""}`);
      s += `<text class="${ref ? "" : "val"}" x="${W - R + 12}" y="${cy + 4}" font-size="13">${f(d.v)}${narrow || d.lo === undefined || d.hi === d.lo ? "" : `<tspan class="rng" dx="8">${f(d.lo)}–${f(d.hi)}</tspan>`}</text>`;
      y += rowH;
    };
    [...o.rows].sort((a, b) => (o.lowerIsBetter ? a.v - b.v : b.v - a.v)).forEach(d => row(d, false));
    if (o.refs && o.refs.length) { y += 8; s += `<text x="0" y="${y + 14}" font-size="12" font-weight="600">${FD.esc(o.refsLabel || "References")}</text>`; y += 22; o.refs.forEach(d => row(d, true)); }
    const H = y + 22; let g = "";
    FD.ticks(lo, hi).forEach(t => { g += `<line class="grid" x1="${x(t)}" x2="${x(t)}" y1="${top - 4}" y2="${H - 22}"/><text x="${x(t)}" y="${H - 6}" text-anchor="middle" font-size="12">${f(t)}</text>`; });
    (o.lines || []).forEach(l => { g += `<line class="ref" x1="${x(l.v)}" x2="${x(l.v)}" y1="${top - 2}" y2="${H - 22}"/><text class="ref-lab" x="${x(l.v)}" y="${top - 10}" text-anchor="middle" font-size="12">${FD.esc(l.label)} ${f(l.v)}</text>`; });
    g += `<text x="${W - R}" y="${H + 12}" text-anchor="end" font-size="12">${FD.esc(o.metric)}</text>`;
    return FD.svg(W, H + 26, o.metric, g + s, -8);
  });
}

// Trends: one line per series over a numeric x. series: [{ name, c, ys }] with ys aligned to x.
// Labels sit at each line's right end; lines: [{ v, label }] are dashed horizontal references.
function lineChart(el, o) {
  const f = o.fmt || (v => v.toFixed(2));
  FD.draw(el, slotW => {
    const W = Math.min(slotW, 680), narrow = W < 460, L = 40, R = narrow ? 70 : 120, T = 14, PH = narrow ? 180 : 210, H = T + PH + 44;
    const vals = o.series.flatMap(s => s.ys.filter(v => v != null)).concat((o.lines || []).map(l => l.v));
    const a = o.from ?? Math.min(...vals), b = o.to ?? Math.max(...vals), xa = o.x[0], xb = o.x[o.x.length - 1];
    const X = v => L + (W - L - R) * (v - xa) / (xb - xa), Y = v => T + PH * (1 - (v - a) / (b - a));
    let s = "";
    FD.ticks(a, b, 4).forEach(t => { s += `<line class="grid" x1="${L}" x2="${W - R}" y1="${Y(t)}" y2="${Y(t)}"/><text x="${L - 8}" y="${Y(t) + 4}" text-anchor="end" font-size="12">${f(t)}</text>`; });
    const every = Math.ceil(o.x.length / (narrow ? 5 : 10));
    o.x.forEach((v, i) => { if (i % every === 0 || i === o.x.length - 1) s += `<text x="${X(v)}" y="${T + PH + 18}" text-anchor="middle" font-size="12">${FD.esc(o.xFmt ? o.xFmt(v) : v)}</text>`; });
    s += `<text x="${(L + W - R) / 2}" y="${H - 4}" text-anchor="middle" font-size="12">${FD.esc(o.xLabel || "")}</text>`;
    (o.lines || []).forEach(l => { s += `<line class="ref" x1="${L}" x2="${W - R}" y1="${Y(l.v)}" y2="${Y(l.v)}"/>`; });
    const ends = [];
    o.series.forEach(se => {
      const c = FD.col(se.c), pts = se.ys.map((v, i) => v == null ? null : [X(o.x[i]), Y(v), v, o.x[i]]).filter(Boolean);
      s += `<polyline fill="none" stroke="${c}" stroke-width="2" stroke-linejoin="round" points="${pts.map(p => p[0] + "," + p[1]).join(" ")}"/>`;
      pts.forEach(p => { s += `<circle cx="${p[0]}" cy="${p[1]}" r="3" fill="${c}"/>` + FD.hit(p[0], p[1], `${se.name}, ${o.xFmt ? o.xFmt(p[3]) : p[3]}: ${f(p[2])}`, 9); });
      const last = pts[pts.length - 1]; ends.push({ y: last[1] + 4, t: se.name, c });
    });
    (o.lines || []).forEach(l => ends.push({ y: Y(l.v) + 4, t: `${l.label} ${f(l.v)}`, ref: true }));
    ends.sort((p, q) => p.y - q.y); for (let i = 1; i < ends.length; i++) if (ends[i].y - ends[i - 1].y < 15) ends[i].y = ends[i - 1].y + 15;
    ends.forEach(e => { s += `<text class="${e.ref ? "ref-lab" : "lab"}" x="${W - R + 8}" y="${e.y}" font-size="12">${FD.esc(e.t)}</text>`; });
    return FD.svg(W, H, o.metric, s);
  });
}

// Totals and their parts: one bar per category, stacked parts with a 2px gap, the total above each bar,
// part names labelled at the last bar. parts: [{ name, c, values }]. lines: [{ v, label }] horizontal references.
function barChart(el, o) {
  const f = o.fmt || (v => v.toFixed(0));
  FD.draw(el, slotW => {
    const W = Math.min(slotW, 680), narrow = W < 460, L = 44, R = narrow ? 76 : 120, T = 22, PH = 200, H = T + PH + 40;
    const totals = o.cats.map((_, i) => o.parts.reduce((s, p) => s + p.values[i], 0));
    const b = Math.max(...totals, ...(o.lines || []).map(l => l.v)) * 1.08, Y = v => T + PH * (1 - v / b);
    const band = (W - L - R) / o.cats.length, bw = Math.min(40, band * 0.6);
    let s = "";
    FD.ticks(0, b, 4).forEach(t => { s += `<line class="grid" x1="${L}" x2="${W - R}" y1="${Y(t)}" y2="${Y(t)}"/><text x="${L - 8}" y="${Y(t) + 4}" text-anchor="end" font-size="12">${f(t)}</text>`; });
    o.cats.forEach((cat, i) => {
      const x = L + band * i + (band - bw) / 2; let acc = 0;
      o.parts.forEach(p => {
        const v = p.values[i]; if (!v) return;
        const y0 = Y(acc), y1 = Y(acc + v); acc += v;
        s += `<rect x="${x}" y="${y1 + 1}" width="${bw}" height="${Math.max(0, y0 - y1 - 2)}" rx="2" fill="${FD.col(p.c)}" tabindex="0" data-tip="${FD.esc(`${cat}, ${p.name}: ${f(v)}`)}"/>`;
      });
      s += `<text class="val" x="${x + bw / 2}" y="${Y(totals[i]) - 6}" text-anchor="middle" font-size="12">${f(totals[i])}</text>`;
      if (!narrow || o.cats.length <= 7 || i % 2 === 0 || i === o.cats.length - 1) s += `<text x="${x + bw / 2}" y="${T + PH + 18}" text-anchor="middle" font-size="12">${FD.esc(cat)}</text>`;
    });
    (o.lines || []).forEach(l => { s += `<line class="ref" x1="${L}" x2="${W - R}" y1="${Y(l.v)}" y2="${Y(l.v)}"/>`; });
    const last = o.cats.length - 1, ends = []; let acc = 0;
    o.parts.forEach(p => { const v = p.values[last]; if (v) ends.push({ y: Y(acc + v / 2) + 4, t: p.name }); acc += v; });
    (o.lines || []).forEach(l => ends.push({ y: Y(l.v) + 4, t: l.label, ref: true }));
    ends.sort((p, q) => p.y - q.y); for (let i = 1; i < ends.length; i++) if (ends[i].y - ends[i - 1].y < 15) ends[i].y = ends[i - 1].y + 15;
    ends.forEach(e => { s += `<text class="${e.ref ? "ref-lab" : "lab"}" x="${W - R + 8}" y="${e.y}" font-size="12">${FD.esc(e.t)}</text>`; });
    s += `<text x="${L - 8}" y="${T - 10}" text-anchor="end" font-size="12">${FD.esc(o.metric)}</text>`;
    return FD.svg(W, H, o.metric, s);
  });
}

// A score distribution for two classes: one above the axis, one below, with the threshold as a dashed line.
// upper/lower: { name, counts } over equal-width bins from 0 to 1; c is the series slot for both.
function distChart(el, o) {
  FD.draw(el, slotW => {
    const W = Math.min(slotW, 680), L = 70, R = 12, half = 80, T = 18, mid = T + half, H = mid + half + 40, n = o.upper.counts.length;
    const max = Math.max(...o.upper.counts, ...o.lower.counts), bw = (W - L - R) / n, X = v => L + (W - L - R) * v, h = c => half * c / max, c = FD.col(o.c);
    let s = `<line class="grid" x1="${L}" x2="${W - R}" y1="${mid}" y2="${mid}"/>`;
    const bins = (cls, up, op) => cls.counts.forEach((k, i) => { if (k) s += `<rect x="${X(i / n) + 1}" y="${up ? mid - h(k) - 1 : mid + 1}" width="${bw - 2}" height="${h(k)}" rx="1.5" fill="${c}" opacity="${op}" tabindex="0" data-tip="${FD.esc(`${cls.name}, score ${(i / n).toFixed(2)}–${((i + 1) / n).toFixed(2)}: ${k}`)}"/>`; });
    bins(o.upper, true, 0.45); bins(o.lower, false, 1);
    s += FD.text(0, T + 16, o.upper.name, "lab") + FD.text(0, mid + half - 4, o.lower.name, "lab");
    if (o.threshold != null) s += `<line class="ref" x1="${X(o.threshold)}" x2="${X(o.threshold)}" y1="${T - 6}" y2="${mid + half}"/><text class="ref-lab" x="${X(o.threshold) + 6}" y="${T + 2}" font-size="12">threshold ${o.threshold.toFixed(2)}</text>`;
    [0, 0.25, 0.5, 0.75, 1].forEach(t => s += `<text x="${X(t)}" y="${mid + half + 18}" text-anchor="middle" font-size="12">${t.toFixed(2)}</text>`);
    s += `<text x="${W - R}" y="${H - 2}" text-anchor="end" font-size="12">${FD.esc(o.metric || "Score")}</text>`;
    return FD.svg(W, H, o.metric || "Score distribution", s);
  });
}
