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
//   lensExplorer(el, { tokens, layers, top, pins, select, layerLabel })      a lens readout per layer and position
//   logitLens(el, same options)                                              the lens grid alone
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
  const run = s => s.replace(/\n/g, "↵\n");
  // Monospace marks a token as a token. Its edge spaces are kept, without visible marks, which read as noise.
  const tok = t => `<span class="tok">${FD.esc(String(t).replace(/\n/g, "↵"))}</span>`;
  const tokSvg = t => FD.esc(String(t).replace(/\n/g, "↵"));
  // A stepped key, rather than a gradient, so each step is a colour the view actually uses.
  const key = (scale, signed, label) => {
    const steps = signed ? [-1, -0.75, -0.5, -0.25, 0, 0.25, 0.5, 0.75, 1] : [0, 0.25, 0.5, 0.75, 1];
    return `<div class="iv-key"><span class="iv-key-steps">${steps.map(s => `<i style="background:${tint(s * scale, scale, signed)}"></i>`).join("")}</span>`
      + `<span class="iv-key-labels"><span>${signed ? "−" + f2(scale) : "0"}</span>${signed ? "<span>0</span>" : ""}<span>${f2(scale)}</span></span>${label ? `<span class="iv-key-label">${FD.esc(label)}</span>` : ""}</div>`;
  };
  return { tint, f2, show, run, tok, tokSvg, key };
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
      s += `<text class="${o.tokenRows ? "lab tok" : "lab"}" x="${L - 8}" y="${T + cell * i + cell / 2 + 4}" text-anchor="end" font-size="12">${o.tokenRows ? IV.tokSvg(r) : FD.esc(String(r))}</text>`;
      o.cols.forEach((c, j) => {
        if (o.mask && o.mask(i, j)) return;
        const v = o.values[i][j]; if (v == null) return;
        s += `<rect x="${L + cell * j + 0.5}" y="${T + cell * i + 0.5}" width="${cell - 1}" height="${cell - 1}" fill="${IV.tint(v, scale, signed, 90)}" tabindex="0" data-tip="${FD.esc(`${o.rowLabel || "Row"} ${IV.show(String(r))}, ${o.colLabel || "column"} ${IV.show(String(c))}: ${IV.f2(v)}`)}"/>`;
      });
    });
    o.cols.forEach((c, j) => { const x = L + cell * j + cell / 2; s += `<text class="${o.tokenCols !== false ? "lab tok" : "lab"}" transform="translate(${x + 4} ${T + cell * nr + 8}) rotate(-60)" text-anchor="end" font-size="12">${o.tokenCols !== false ? IV.tokSvg(c) : FD.esc(String(c))}</text>`; });
    if (o.rowLabel) s += `<text x="0" y="${T - 4}" font-size="12">${FD.esc(o.rowLabel)} ↓</text>`;
    if (o.colLabel) s += `<text x="${W - 8}" y="${H - 2}" text-anchor="end" font-size="12">${FD.esc(o.colLabel)} →</text>`;
    return FD.svg(W, H, o.label || "Heatmap", s) + keyHtml;
  });
}

// A lens over the residual stream (the logit lens, the J-lens or any tuned lens): what each layer is poised to
// say at each token position. top[l][p] is that cell's readout, [[token, probability], ...] sorted best first.
// The grid shows each cell's top token, with the final layer at the top and the prompt along the bottom, so it
// reads like the residual stream flowing upward. Shading shows the top token's probability, or the rank of a
// pinned token (darker is a better rank, on a log scale). Selecting a cell shows its full readout; pinning a
// token from it tracks that token's rank through the layers at the selected position.
//   lensExplorer(el, { tokens, layers, top, pins, select: [layerIndex, position], layerLabel, lens })
//   logitLens(el, same options): the grid alone, without the panels underneath.
function lensExplorer(el, o) {
  el.setAttribute("data-viz", "");
  const NL = o.layers.length, NP = o.tokens.length, K = o.top[0][0].length, lens = o.lens || "lens";
  const st = { sel: o.select || [NL - 1, NP - 1], pins: [], slot: {}, shade: "prob" };
  const pin = t => { if (st.pins.includes(t)) { st.pins = st.pins.filter(x => x !== t); if (st.shade === t) st.shade = st.pins[0] || "prob"; } else { st.pins.push(t); st.slot[t] = st.slot[t] || (Object.keys(st.slot).length % 8) + 1; st.shade = t; } };
  (o.pins || []).forEach(pin);
  const rankOf = (t, l, p) => { const i = o.top[l][p].findIndex(([x]) => x === t); return i < 0 ? null : i + 1; };
  const rankTint = r => r == null ? "transparent" : IV.tint(1 - Math.log(r) / Math.log(K + 1), 1, false, 62);
  const q = t => FD.esc(JSON.stringify(t));
  const pct = v => v >= 0.1 ? `${(v * 100).toFixed(0)}%` : v >= 0.001 ? `${(v * 100).toFixed(1)}%` : "<0.1%";
  const lab = l => `${o.layerLabel || "Layer"} ${o.layers[l]}`;

  const grid = () => {
    const rows = [...Array(NL).keys()].reverse().map(l => `<tr><th scope="row">${o.layers[l]}</th>${o.tokens.map((_, p) => {
      const [t, pr] = o.top[l][p][0], r = st.shade === "prob" ? null : rankOf(st.shade, l, p), sel = st.sel[0] === l && st.sel[1] === p;
      const bg = st.shade === "prob" ? IV.tint(pr, 1, false, 62) : rankTint(r);
      const tip = `${lab(l)}, after ${JSON.stringify(o.tokens[p])}: ${o.top[l][p].slice(0, 5).map(([x, v]) => `${JSON.stringify(x)} ${pct(v)}`).join(", ")}${st.shade !== "prob" ? `. ${JSON.stringify(st.shade)} is ${r ? "rank " + r : "not in the top " + K}` : ""}`;
      return `<td class="${sel ? "lx-sel" : ""}" tabindex="${sel ? 0 : -1}" data-l="${l}" data-p="${p}" style="background:${bg}" data-tip="${FD.esc(tip)}">${IV.tok(t)}</td>`;
    }).join("")}</tr>`).join("");
    return `<div class="tablewrap"><table class="lx-grid" style="min-width:${52 + NP * 84}px"><colgroup><col class="lx-lcol">${o.tokens.map(() => "<col>").join("")}</colgroup>`
      + `<tbody>${rows}</tbody><tfoot><tr><th scope="col" class="lx-corner">${FD.esc(o.layerLabel || "Layer")}</th>${o.tokens.map((t, p) => `<th scope="col" class="${st.sel[1] === p ? "lx-cur" : ""}">${IV.tok(t)}</th>`).join("")}</tr></tfoot></table></div>`;
  };
  const shadeCtl = () => `<div class="lx-ctl"><label>Shading<select class="lx-shade">${[["prob", "Probability of the top token"], ...st.pins.map(t => [t, `Rank of ${t.trim() || JSON.stringify(t)}`])].map(([v, n]) => `<option value="${FD.esc(v)}"${st.shade === v ? " selected" : ""}>${FD.esc(n)}</option>`).join("")}</select></label>`
    + `<div class="lx-key">${st.shade === "prob" ? IV.key(1, false, "Probability") : `<div class="iv-key"><span class="iv-key-steps">${[1, 2, 5, 10, K].map(r => `<i style="background:${rankTint(r)}"></i>`).join("")}<i style="background:transparent"></i></span><span class="iv-key-labels"><span>rank 1</span><span>${K}</span><span>not in top ${K}</span></span></div>`}</div></div>`;
  const readout = () => {
    const [l, p] = st.sel, list = o.top[l][p].slice(0, 10);
    return `<div class="lx-panel"><h3>${FD.esc(lab(l))}, after ${IV.tok(o.tokens[p])}</h3><ol class="lx-read">${list.map(([t, v], i) => `<li><span class="lx-rank">${i + 1}</span><button type="button" class="lx-tok${st.pins.includes(t) ? " lx-pinned" : ""}" data-tok="${FD.esc(t)}" aria-pressed="${st.pins.includes(t)}" title="${st.pins.includes(t) ? "Unpin" : "Pin to track its rank"}">${st.pins.includes(t) ? `<span class="sw" style="--c: var(--s${st.slot[t]})"></span>` : ""}<span class="lx-t">${IV.tok(t)}</span></button><span class="lx-barw" aria-hidden="true"><span class="lx-bar" style="width:${(v * 100).toFixed(1)}%"></span></span><span class="lx-p">${pct(v)}</span></li>`).join("")}</ol><p class="lx-hint">Select a token to pin it and track its rank.</p></div>`;
  };
  const trajectory = () => {
    const p = st.sel[1];
    if (!st.pins.length) return `<div class="lx-panel"><h3>Rank by layer, after ${IV.tok(o.tokens[p])}</h3><p class="lx-hint">Pinned tokens appear here.</p></div>`;
    return `<div class="lx-panel"><h3>Rank by layer, after ${IV.tok(o.tokens[p])}</h3><div class="lx-traj"></div><ul class="lx-pins">${st.pins.map(t => `<li><span class="sw" style="--c: var(--s${st.slot[t]})">${IV.tok(t)}</span><button type="button" class="lx-unpin" data-tok="${FD.esc(t)}">Unpin</button></li>`).join("")}</ul></div>`;
  };
  const drawTraj = () => {
    const slot = el.querySelector(".lx-traj"); if (!slot) return; delete slot.dataset.w;
    FD.draw(slot, W0 => {
      const W = Math.min(W0, 520), Lm = 40, R = 16, T = 22, PH = 180, H = T + PH + 40, p = st.sel[1];
      const X = l => Lm + (W - Lm - R) * l / Math.max(1, NL - 1), Y = r => T + PH * Math.log(r) / Math.log(K + 1), Yout = T + PH;
      let s = "";
      [1, 2, 5, 10, 20, 50].filter(r => r < K).forEach(r => { s += `<line class="grid" x1="${Lm}" x2="${W - R}" y1="${Y(r)}" y2="${Y(r)}"/><text x="${Lm - 8}" y="${Y(r) + 4}" text-anchor="end" font-size="12">${r}</text>`; });
      s += `<text x="${Lm - 8}" y="${Yout + 4}" text-anchor="end" font-size="12">>${K}</text>`;
      const every = Math.ceil(NL / 6);
      o.layers.forEach((lv, l) => { if (l % every === 0 || l === NL - 1) s += `<text x="${X(l)}" y="${T + PH + 18}" text-anchor="middle" font-size="12">${lv}</text>`; });
      s += `<text x="${(Lm + W - R) / 2}" y="${H - 4}" text-anchor="middle" font-size="12">${FD.esc(o.layerLabel || "Layer")}</text><text x="${Lm - 8}" y="${T - 10}" text-anchor="end" font-size="12">Rank</text>`;
      s += `<line class="ref" x1="${X(st.sel[0])}" x2="${X(st.sel[0])}" y1="${T}" y2="${T + PH}"/>`;
      st.pins.forEach(t => {
        const c = `var(--s${st.slot[t]})`, pts = o.layers.map((_, l) => { const r = rankOf(t, l, p); return [X(l), r ? Y(r) : Yout, r]; });
        s += `<polyline fill="none" stroke="${c}" stroke-width="2" stroke-linejoin="round" points="${pts.map(([x, y]) => x + "," + y).join(" ")}"/>`;
        pts.forEach(([x, y, r], l) => { s += `<circle cx="${x}" cy="${y}" r="${l === st.sel[0] ? 4.5 : 2.5}" fill="${c}"/>` + FD.hit(x, y, `${JSON.stringify(t)}, ${lab(l)}: ${r ? "rank " + r : "not in the top " + K}`, 8); });
      });
      return FD.svg(W, H, `Rank by layer of the pinned tokens`, s);
    });
  };
  const render = () => {
    el.innerHTML = shadeCtl() + grid() + (o.gridOnly ? "" : `<div class="lx-detail">${readout()}${trajectory()}</div>`);
    if (!o.gridOnly) drawTraj();
  };
  const select = (l, p, focus) => { st.sel = [Math.max(0, Math.min(NL - 1, l)), Math.max(0, Math.min(NP - 1, p))]; render(); if (focus) el.querySelector(".lx-sel")?.focus(); };
  el.addEventListener("click", e => {
    const td = e.target.closest(".lx-grid td"); if (td) return select(+td.dataset.l, +td.dataset.p, true);
    const b = e.target.closest("[data-tok]"); if (b) { pin(b.dataset.tok); render(); }
  });
  el.addEventListener("change", e => { if (e.target.matches(".lx-shade")) { st.shade = e.target.value; render(); el.querySelector(".lx-shade").focus(); } });
  el.addEventListener("keydown", e => {
    if (!e.target.closest(".lx-grid td")) return;
    const d = { ArrowUp: [1, 0], ArrowDown: [-1, 0], ArrowLeft: [0, -1], ArrowRight: [0, 1] }[e.key];
    if (d) { e.preventDefault(); select(st.sel[0] + d[0], st.sel[1] + d[1], true); }
  });
  render();
}
function logitLens(el, o) { lensExplorer(el, { ...o, gridOnly: true }); }

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
