// Logan's functional-design views for model internals. Paste after base.js and charts.js (it uses FD from charts.js).
// These views use colour to encode values, so each sits in a container marked data-viz, which the check
// script exempts from its rules against tinted backgrounds. Encodings follow one rule:
//   a signed value (for or against something) uses --div-neg / --div-pos with neutral at zero;
//   a magnitude uses the one-hue --seq scale from pale to dark.
// Views shown together share one scale (pass the same `scale`), or their colours can't be compared.
//
//   tokenText(el, { tokens: [[text, value], ...], scale, signed, label })    per-token values over text
//   topExamples(el, { title, note, examples: [{ tokens, max }], hist, scale }) a feature's top-activating contexts
//   heatmap(el, { rows, cols, values, signed, scale, rowLabel, colLabel, mask }) values over two axes
//   logitLens(el, { layers, positions, cells })                               top prediction per layer and position
//   graph(el, { columns, edges })                                             an attribution or circuit graph

const IV = (() => {
  // A value's colour: mixed into the page background, so text on it stays readable and dark mode works.
  const tint = (v, scale, signed, max = 70) => {
    const a = Math.max(-1, Math.min(1, v / scale));
    if (signed) return a === 0 ? "transparent" : `color-mix(in oklab, var(${a > 0 ? "--div-pos" : "--div-neg"}) ${Math.round(Math.abs(a) * max)}%, var(--bg))`;
    return `color-mix(in oklab, var(--seq) ${Math.round(Math.max(0, a) * max)}%, var(--bg))`;
  };
  const f2 = v => (Math.abs(v) >= 10 ? v.toFixed(1) : v.toFixed(2));
  const show = s => s.replace(/\n/g, "↵").replace(/^ /, " ").replace(/ $/, " ");
  const run = s => s.replace(/\n/g, "↵\n");  // in running text a token wraps normally; show() keeps edge spaces visible for labels
  // A stepped key, rather than a gradient, so each step is a colour the view actually uses.
  const key = (scale, signed, label) => {
    const steps = signed ? [-1, -0.75, -0.5, -0.25, 0, 0.25, 0.5, 0.75, 1] : [0, 0.25, 0.5, 0.75, 1];
    return `<div class="iv-key"><span class="iv-key-steps">${steps.map(s => `<i style="background:${tint(s * scale, scale, signed)}"></i>`).join("")}</span>`
      + `<span class="iv-key-labels"><span>${signed ? "−" + f2(scale) : "0"}</span>${signed ? "<span>0</span>" : ""}<span>${f2(scale)}</span></span>${label ? `<span class="iv-key-label">${FD.esc(label)}</span>` : ""}</div>`;
  };
  return { tint, f2, show, run, key };
})();

// Per-token values laid over the text itself: a pale tint behind each token, exact value on hover or focus.
function tokenText(el, o) {
  const signed = o.signed !== false, scale = o.scale || Math.max(...o.tokens.map(([, v]) => Math.abs(v))) || 1;
  el.setAttribute("data-viz", "");
  el.innerHTML = `<p class="iv-text">${o.tokens.map(([t, v]) => `<span class="iv-tok" tabindex="0" style="background:${IV.tint(v, scale, signed)}" data-tip="${FD.esc(`${JSON.stringify(t)}: ${IV.f2(v)}`)}">${FD.esc(IV.run(t))}</span>`).join("")}</p>${o.noKey ? "" : IV.key(scale, signed, o.label)}`;
}

// A feature's top-activating contexts, strongest first: each a window of text around its peak token,
// with the peak's value on the right, and the distribution of the feature's activations above them.
function topExamples(el, o) {
  const scale = o.scale || Math.max(...o.examples.map(e => e.max)) || 1;
  el.setAttribute("data-viz", "");
  let h = "";
  if (o.hist) h += `<div class="iv-hist"></div>`;
  h += `<ol class="iv-examples">${[...o.examples].sort((a, b) => b.max - a.max).map(e => `<li><p class="iv-text">${e.tokens.map(([t, v]) => `<span class="iv-tok" tabindex="0" style="background:${IV.tint(v, scale, false)}" data-tip="${FD.esc(`${JSON.stringify(t)}: ${IV.f2(v)}`)}">${FD.esc(IV.run(t))}</span>`).join("")}</p><span class="iv-max">${IV.f2(e.max)}</span></li>`).join("")}</ol>`;
  h += IV.key(scale, false, o.label || "Activation");
  el.innerHTML = h;
  if (o.hist) {
    const slot = el.querySelector(".iv-hist");
    FD.draw(slot, W0 => {
      const W = Math.min(W0, 680), H = 90, L = 4, B = 20, n = o.hist.counts.length, bw = (W - L) / n, max = Math.max(...o.hist.counts);
      let s = o.hist.counts.map((c, i) => c ? `<rect x="${L + i * bw + 1}" y="${H - B - (H - B - 6) * c / max}" width="${bw - 2}" height="${(H - B - 6) * c / max}" rx="1.5" fill="var(--seq)" tabindex="0" data-tip="${FD.esc(`${IV.f2(o.hist.from + (o.hist.to - o.hist.from) * i / n)}–${IV.f2(o.hist.from + (o.hist.to - o.hist.from) * (i + 1) / n)}: ${c.toLocaleString()} tokens`)}"/>` : "").join("");
      s += `<text x="${L}" y="${H - 4}" font-size="12">${IV.f2(o.hist.from)}</text><text x="${W}" y="${H - 4}" text-anchor="end" font-size="12">${IV.f2(o.hist.to)}</text><text x="${W / 2}" y="${H - 4}" text-anchor="middle" font-size="12">${FD.esc(o.hist.label || "Activation, over tokens where it fires")}</text>`;
      return FD.svg(W, H, o.hist.label || "Activation distribution", s);
    });
  }
}

// Values over two axes, such as attention from each query token to each key, or a probe's score by layer
// and position. Row and column labels can be tokens. mask(i, j) hides cells that can't exist (causal attention).
function heatmap(el, o) {
  const signed = !!o.signed, flat = o.values.flat().filter(v => v != null);
  const scale = o.scale || (signed ? Math.max(...flat.map(Math.abs)) : Math.max(...flat)) || 1;
  el.setAttribute("data-viz", "");
  const keyHtml = IV.key(scale, signed, o.label);
  FD.draw(el, W0 => {
    const nr = o.rows.length, nc = o.cols.length, L = Math.min(150, 12 + Math.max(...o.rows.map(r => FD.measure(IV.show(String(r)), 12)))), T = 14;
    const cell = Math.max(14, Math.min(34, Math.floor((Math.min(W0, 900) - L - 8) / nc))), W = L + cell * nc + 8;
    const bot = Math.min(110, 16 + Math.max(...o.cols.map(c => FD.measure(IV.show(String(c)), 12)))), H = T + cell * nr + bot;
    let s = "";
    o.rows.forEach((r, i) => {
      s += `<text class="lab" x="${L - 8}" y="${T + cell * i + cell / 2 + 4}" text-anchor="end" font-size="12">${FD.esc(IV.show(String(r)))}</text>`;
      o.cols.forEach((c, j) => {
        if (o.mask && o.mask(i, j)) return;
        const v = o.values[i][j]; if (v == null) return;
        s += `<rect x="${L + cell * j + 0.5}" y="${T + cell * i + 0.5}" width="${cell - 1}" height="${cell - 1}" fill="${IV.tint(v, scale, signed, 90)}" tabindex="0" data-tip="${FD.esc(`${o.rowLabel || "Row"} ${IV.show(String(r))}, ${o.colLabel || "column"} ${IV.show(String(c))}: ${IV.f2(v)}`)}"/>`;
      });
    });
    o.cols.forEach((c, j) => { const x = L + cell * j + cell / 2; s += `<text class="lab" transform="translate(${x + 4} ${T + cell * nr + 8}) rotate(-60)" text-anchor="end" font-size="12">${FD.esc(IV.show(String(c)))}</text>`; });
    if (o.rowLabel) s += `<text x="0" y="${T - 4}" font-size="12">${FD.esc(o.rowLabel)} ↓</text>`;
    if (o.colLabel) s += `<text x="${W - 8}" y="${H - 2}" text-anchor="end" font-size="12">${FD.esc(o.colLabel)} →</text>`;
    return FD.svg(W, H, o.label || "Heatmap", s) + keyHtml;
  });
}

// The logit lens: the model's top next-token prediction read from each layer at each position,
// with the cell shaded by that prediction's probability. cells[layer][position] = [token, p].
function logitLens(el, o) {
  el.setAttribute("data-viz", "");
  el.innerHTML = `<div class="tablewrap"><table class="iv-lens"><thead><tr><th>Layer</th>${o.positions.map(p => `<th>${FD.esc(IV.show(p))}</th>`).join("")}</tr></thead><tbody>${o.layers.map((l, i) => `<tr><th>${l}</th>${o.cells[i].map(([t, p], j) => `<td tabindex="0" style="background:${IV.tint(p, 1, false, 62)}" data-tip="${FD.esc(`Layer ${l}, after ${JSON.stringify(o.positions[j])}: ${JSON.stringify(t)} at ${(p * 100).toFixed(0)}%`)}">${FD.esc(IV.show(t))}</td>`).join("")}</tr>`).join("")}</tbody></table></div>${IV.key(1, false, "Probability of the top prediction")}`;
}

// An attribution or circuit graph, laid out in columns from inputs on the left to outputs on the right.
// columns: [{ label, nodes: [{ id, label, note }] }], edges: [{ from, to, w }] with w signed.
// Edge width shows |w|, colour its sign; hovering or focusing a node fades everything not connected to it.
function graph(el, o) {
  el.setAttribute("data-viz", "");
  const maxW = Math.max(...o.edges.map(e => Math.abs(e.w))) || 1;
  FD.draw(el, W0 => {
    const nc = o.columns.length, W = Math.max(W0, nc * 170), colW = (W - 40) / nc, nodeW = Math.min(150, colW - 30), nodeH = 40, gap = 18, T = 26;
    const pos = {}; let H = 0;
    o.columns.forEach((c, ci) => { const tot = c.nodes.length * (nodeH + gap); H = Math.max(H, tot); });
    o.columns.forEach((c, ci) => { const off = (H - c.nodes.length * (nodeH + gap)) / 2; c.nodes.forEach((n, ni) => { pos[n.id] = { x: 20 + colW * ci + (colW - nodeW) / 2, y: T + off + ni * (nodeH + gap), n }; }); });
    let s = `<defs><marker id="iv-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M0 0L10 5L0 10z" fill="var(--muted)"/></marker></defs>`;
    o.columns.forEach((c, ci) => { s += `<text x="${20 + colW * ci + colW / 2}" y="12" text-anchor="middle" font-size="12">${FD.esc(c.label)}</text>`; });
    o.edges.forEach(e => {
      const a = pos[e.from], b = pos[e.to]; if (!a || !b) return;
      const x1 = a.x + nodeW, y1 = a.y + nodeH / 2, x2 = b.x, y2 = b.y + nodeH / 2, mx = (x1 + x2) / 2;
      s += `<path class="iv-edge" data-from="${e.from}" data-to="${e.to}" d="M${x1} ${y1}C${mx} ${y1} ${mx} ${y2} ${x2 - 2} ${y2}" fill="none" stroke="var(${e.w > 0 ? "--div-pos" : "--div-neg"})" stroke-opacity="0.75" stroke-width="${(1 + 5 * Math.abs(e.w) / maxW).toFixed(2)}"><title>${FD.esc(`${pos[e.from].n.label} → ${pos[e.to].n.label}: ${e.w > 0 ? "+" : ""}${IV.f2(e.w)}`)}</title></path>`;
    });
    Object.entries(pos).forEach(([id, p]) => {
      s += `<g class="iv-node" data-id="${id}" tabindex="0" data-tip="${FD.esc(p.n.label + (p.n.note ? `: ${p.n.note}` : ""))}"><rect class="box" x="${p.x}" y="${p.y}" width="${nodeW}" height="${nodeH}" rx="4"/>`
        + `<text x="${p.x + nodeW / 2}" y="${p.y + (p.n.note ? 17 : 24)}" text-anchor="middle" font-size="13">${FD.esc(p.n.label)}</text>`
        + (p.n.note ? `<text class="note" x="${p.x + nodeW / 2}" y="${p.y + 32}" text-anchor="middle" font-size="12">${FD.esc(p.n.note)}</text>` : "") + `</g>`;
    });
    return `<svg class="diagram iv-graph" width="${W}" height="${T + H}" viewBox="0 0 ${W} ${T + H}" role="img" aria-label="${FD.esc(o.label || "Attribution graph")}">${s}</svg>`;
  });
  const focus = id => {
    const keep = new Set([id]); el.querySelectorAll(".iv-edge").forEach(p => { if (p.dataset.from === id) keep.add(p.dataset.to); if (p.dataset.to === id) keep.add(p.dataset.from); });
    el.querySelectorAll(".iv-node").forEach(g => g.classList.toggle("iv-dim", id && !keep.has(g.dataset.id)));
    el.querySelectorAll(".iv-edge").forEach(p => p.classList.toggle("iv-dim", id && p.dataset.from !== id && p.dataset.to !== id));
  };
  el.addEventListener("pointerover", e => { const g = e.target.closest(".iv-node"); focus(g ? g.dataset.id : null); });
  el.addEventListener("pointerleave", () => focus(null));
  el.addEventListener("focusin", e => { const g = e.target.closest(".iv-node"); if (g) focus(g.dataset.id); });
  el.addEventListener("focusout", () => focus(null));
}
