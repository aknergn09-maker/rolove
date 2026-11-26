/* ROLEVE GÖNYE — PC dengeleme çekirdeği (DOM yok). Koordinat: x = Y (doğu), y = X (kuzey) — AutoCAD/NetCAD DXF düzeni. */
const G = (() => {
  const sub = (a, b) => [a[0] - b[0], a[1] - b[1]], add = (a, b) => [a[0] + b[0], a[1] + b[1]], mul = (a, k) => [a[0] * k, a[1] * k];
  const dot = (a, b) => a[0] * b[0] + a[1] * b[1], cross = (a, b) => a[0] * b[1] - a[1] * b[0], len = a => Math.hypot(a[0], a[1]), dist = (a, b) => len(sub(a, b));
  const TAU = Math.PI * 2, wrap = a => { while (a > Math.PI) a -= TAU; while (a <= -Math.PI) a += TAU; return a; };

  /* ---------- DXF okuma (R12/LW, bloklar, yazılar) ---------- */
  function parseDXF(txt) {
    const L = txt.split(/\r?\n/), pr = []; for (let i = 0; i + 1 < L.length; i += 2) pr.push([parseInt(L[i].trim(), 10), L[i + 1].replace(/\s+$/, '')]);
    const out = { ents: [], blocks: {} }; let list = out.ents, cur = null, poly = null, blk = null, sect = null;
    const flush = () => {
      if (!cur) return; const g = cur.g, T = cur.type, ly = (g[8] || ['0'])[0].trim(), v = k => Number((g[k] || [0])[0]), n = k => (g[k] || []).map(Number);
      if (T === 'POLYLINE') poly = { t: 'pl', p: [], c: !!(v(70) & 1), layer: ly };
      else if (T === 'VERTEX' && poly) poly.p.push([v(10), v(20)]);
      else if (T === 'SEQEND' && poly) { list.push(poly); poly = null; }
      else if (T === 'LWPOLYLINE') { const xs = n(10), ys = n(20); list.push({ t: 'pl', p: xs.map((x, k) => [x, ys[k]]), c: !!(v(70) & 1), layer: ly }); }
      else if (T === 'LINE') list.push({ t: 'line', a: [v(10), v(20)], b: [v(11), v(21)], layer: ly });
      else if (T === 'CIRCLE') list.push({ t: 'cir', c: [v(10), v(20)], r: v(40), layer: ly });
      else if (T === 'ARC') list.push({ t: 'arc', c: [v(10), v(20)], r: v(40), a0: v(50) * Math.PI / 180, a1: v(51) * Math.PI / 180, layer: ly });
      else if (T === 'POINT') list.push({ t: 'pt', p: [v(10), v(20)], layer: ly });
      else if (T === 'TEXT' || T === 'MTEXT') list.push({ t: 'text', p: [v(10), v(20)], s: decode((g[1] || [''])[0]).trim(), layer: ly });
      else if (T === 'INSERT') list.push({ t: 'ins', name: (g[2] || [''])[0].trim(), at: [v(10), v(20)], sx: g[41] ? v(41) : 1, sy: g[42] ? v(42) : 1, rot: v(50) * Math.PI / 180, layer: ly });
      else if (T === 'BLOCK') { blk = { name: (g[2] || [''])[0].trim(), base: [v(10), v(20)], ents: [] }; list = blk.ents; }
      else if (T === 'ENDBLK') { if (blk) out.blocks[blk.name] = blk; blk = null; list = out.ents; }
      cur = null;
    };
    for (let i = 0; i < pr.length; i++) { const [c, val] = pr[i];
      if (c === 0) { flush(); const V = val.trim(); if (V === 'SECTION' || V === 'ENDSEC') { sect = null; continue; } cur = (sect === 'BLOCKS' || sect === 'ENTITIES') ? { type: V, g: {} } : null; continue; }
      if (c === 2 && !cur && sect === null) { sect = val.trim(); continue; }
      if (cur) (cur.g[c] = cur.g[c] || []).push(val); }
    flush(); return out;
  }
  function decode(s) { return s.replace(/\\U\+([0-9A-Fa-f]{4})/g, (_, h) => String.fromCharCode(parseInt(h, 16))); }

  /* ---------- total dosyası: NCN (ad Y X Z ...) ya da CSV (ad,X,Y,Z) — 7 haneli değer X (kuzey) ---------- */
  function readTotal(txt) {
    const out = [];
    txt.split(/\r?\n/).forEach(line => {
      const t = line.trim(); if (!t) return;
      const parts = t.includes(',') || t.includes(';') ? t.split(/[;,]/).map(s => s.trim()) : t.split(/\s+/);
      const name = (parts[0] || '').replace(/^"|"$/g, ''); const nums = parts.slice(1).map(s => parseFloat(s.replace(/"/g, ''))).filter(v => !isNaN(v));
      if (!name || nums.length < 2) return;
      let a = nums[0], b = nums[1]; let X, Y; if (Math.abs(a) >= 1e6 && Math.abs(b) < 1e6) { X = a; Y = b; } else if (Math.abs(b) >= 1e6 && Math.abs(a) < 1e6) { X = b; Y = a; } else { Y = a; X = b; }
      out.push({ name, p: [Y, X], z: nums[2] || 0 });
    });
    return out;
  }

  /* ---------- telefon DXF'inden model ---------- */
  function buildModel(dx) {
    const E = dx.ents, names = {}, PT = [];
    const nameLayers = ['NOKTA_AD', 'NOKTA_X', 'NOKTA'];
    E.filter(e => e.t === 'pt' && nameLayers.includes(e.layer)).forEach(e => PT.push(e));
    E.filter(e => e.t === 'text' && nameLayers.includes(e.layer)).forEach(t => {
      const q = sub(t.p, [0.05, 0.05]); let best = null; PT.forEach(p => { const d = dist(p.p, q); if (d < 0.02 && (!best || d < best.d)) best = { p, d }; });
      const p = best ? best.p.p : q; names[t.s] = { name: t.s, sk: [p[0], p[1]], user: t.layer === 'NOKTA_AD' };
    });
    const list = Object.values(names);
    const nameAt = p => { let best = null; list.forEach(n => { const d = dist(n.sk, p); if (d < 2e-3 && (!best || d < best.d)) best = { n, d }; }); return best ? best.n.name : null; };
    /* kroki kenarları */
    const segs = [], arcs = [], circles = [], drawn = [];
    E.filter(e => e.layer === 'CIZIM').forEach(e => {
      if (e.t === 'pl') { const ns = e.p.map(nameAt); drawn.push({ t: 'pl', ns, c: e.c }); const m = e.c ? e.p.length : e.p.length - 1; for (let i = 0; i < m; i++) { const a = ns[i], b = ns[(i + 1) % e.p.length]; if (a && b && a !== b) segs.push([a, b]); } }
      else if (e.t === 'line') { const a = nameAt(e.a), b = nameAt(e.b); drawn.push({ t: 'line', ns: [a, b] }); if (a && b && a !== b) segs.push([a, b]); }
      else if (e.t === 'arc') { const pa = add(e.c, [e.r * Math.cos(e.a0), e.r * Math.sin(e.a0)]), pb = add(e.c, [e.r * Math.cos(e.a1), e.r * Math.sin(e.a1)]); let sw = e.a1 - e.a0; while (sw <= 0) sw += TAU; arcs.push({ a: nameAt(pa), b: nameAt(pb), sw, e }); }
      else if (e.t === 'cir') circles.push(e);
    });
    /* ölçüler */
    const meas = [];
    E.filter(e => e.t === 'text' && ['OLCU', 'GONYE', 'DIKAYAK'].includes(e.layer)).forEach(t => {
      const tok = t.s.split(/\s+/), k = tok[0], laser = tok[tok.length - 1] === 'L'; if (laser) tok.pop();
      const num = s => parseFloat(s), pair = s => s.split('-');
      if (['NN', 'OB', 'GN'].includes(k) && tok.length === 4) meas.push({ k, a: tok[1], b: tok[2], v: num(tok[3]), laser, txt: t.s });
      else if (k === 'ND' && tok.length === 4) { const [a, b] = pair(tok[2]); meas.push({ k, p: tok[1], a, b, v: num(tok[3]), laser, txt: t.s }); }
      else if (k === 'CC' && tok.length === 4) { const [a, b] = pair(tok[1]), [c, d] = pair(tok[2]); meas.push({ k, a, b, c, d, v: num(tok[3]), laser, txt: t.s }); }
      else if (k === 'DA' && tok.length === 6) meas.push({ k, o: tok[1], f: tok[2], c: tok[3], v: num(tok[4]), v2: num(tok[5]), laser, txt: t.s });
    });
    const ops = E.filter(e => e.t === 'text' && e.layer === 'META' && e.s.startsWith('OP ')).map(t => { const [, blk, a, b, kind] = t.s.split(/\s+/); return { blk, a, b, kind }; });
    const inserts = E.filter(e => e.t === 'ins' && (e.layer === 'KAPI' || e.layer === 'PENCERE'));
    return { names, list, segs, arcs, circles, drawn, meas, ops, inserts, blocks: dx.blocks };
  }

  /* ---------- benzerlik dönüşümü (Helmert) ---------- */
  function helmert(src, dst) {
    const n = src.length; if (!n) return { a: 1, b: 0, tx: 0, ty: 0 };
    if (n === 1) return { a: 1, b: 0, tx: dst[0][0] - src[0][0], ty: dst[0][1] - src[0][1] };
    let sx = [0, 0], dx = [0, 0]; src.forEach((p, i) => { sx = add(sx, p); dx = add(dx, dst[i]); }); sx = mul(sx, 1 / n); dx = mul(dx, 1 / n);
    let A = 0, B = 0, S = 0; src.forEach((p, i) => { const u = sub(p, sx), w = sub(dst[i], dx); A += dot(u, w); B += cross(u, w); S += dot(u, u); });
    const a = A / S, b = B / S; return { a, b, tx: dx[0] - (a * sx[0] - b * sx[1]), ty: dx[1] - (b * sx[0] + a * sx[1]) };
  }
  const applyH = (h, p) => [h.a * p[0] - h.b * p[1] + h.tx, h.b * p[0] + h.a * p[1] + h.ty];

  /* ---------- dengeleme ---------- */
  const DEF = { sLaser: 0.003, sTyped: 0.01, sTotal: 0.0005, sAngle: 2, sStraight: 0.05, sLenRel: 0.05, sLenAbs: 0.03, sOnLine: 0.002, sRight: 0.2 };
  function adjust(M, totals, opt) {
    opt = Object.assign({}, DEF, opt || {});
    const idx = {}; M.list.forEach((n, i) => { idx[n.name] = i; }); const N = M.list.length, NK = 2 * N; const nP = NK + 1;
    const tot = {}; totals.forEach(t => { tot[t.name] = t; });
    const matched = M.list.filter(n => tot[n.name]);
    const H = helmert(matched.map(n => n.sk), matched.map(n => tot[n.name].p)); const K0 = Math.hypot(H.a, H.b) || 1;
    const X = new Float64Array(nP); M.list.forEach((n, i) => { const p = applyH(H, n.sk); X[2 * i] = p[0]; X[2 * i + 1] = p[1]; }); X[NK] = K0;
    const P = (i, x) => [x[2 * i], x[2 * i + 1]];
    const obs = []; const O = (vars, f, s, info) => obs.push({ vars, f, s, info });
    const I = nm => idx[nm];
    /* total: sabit */
    matched.forEach(n => { const i = idx[n.name], t = tot[n.name].p; O([2 * i], x => x[2 * i] - t[0], opt.sTotal, { k: 'TOTAL', name: n.name, axis: 'Y' }); O([2 * i + 1], x => x[2 * i + 1] - t[1], opt.sTotal, { k: 'TOTAL', name: n.name, axis: 'X' }); });
    /* zayıf konum (datum, tekilliği önler) */
    M.list.forEach((n, i) => { const x0 = X[2 * i], y0 = X[2 * i + 1]; O([2 * i], x => x[2 * i] - x0, 50, { k: 'prior' }); O([2 * i + 1], x => x[2 * i + 1] - y0, 50, { k: 'prior' }); });
    if (matched.length < 2) { O([NK], x => x[NK] - 1, 0.02, { k: 'prior' }); }
    const pv = (i) => [2 * i, 2 * i + 1];
    /* ölçüler */
    M.meas.forEach(m => {
      const s = m.laser ? opt.sLaser : opt.sTyped;
      if (['NN', 'OB', 'GN'].includes(m.k)) { const a = I(m.a), b = I(m.b); if (a == null || b == null) return; O(pv(a).concat(pv(b)), x => dist(P(a, x), P(b, x)) - m.v, s, { k: m.k, m }); }
      else if (m.k === 'ND') { const p = I(m.p), a = I(m.a), b = I(m.b); if ([p, a, b].includes(undefined)) return; const sg = Math.sign(cross(sub(P(b, X), P(a, X)), sub(P(p, X), P(a, X)))) || 1; O(pv(p).concat(pv(a), pv(b)), x => sg * cross(sub(P(b, x), P(a, x)), sub(P(p, x), P(a, x))) / dist(P(a, x), P(b, x)) - m.v, s, { k: m.k, m }); }
      else if (m.k === 'CC') { const a = I(m.a), b = I(m.b), c = I(m.c), d = I(m.d); if ([a, b, c, d].includes(undefined)) return; const mid = x => mul(add(P(a, x), P(b, x)), 0.5); const sg = Math.sign(cross(sub(P(d, X), P(c, X)), sub(mid(X), P(c, X)))) || 1; O(pv(a).concat(pv(b), pv(c), pv(d)), x => sg * cross(sub(P(d, x), P(c, x)), sub(mid(x), P(c, x))) / dist(P(c, x), P(d, x)) - m.v, s, { k: m.k, m }); }
      else if (m.k === 'DA') { const o = I(m.o), f = I(m.f), c = I(m.c); if ([o, f, c].includes(undefined)) return;
        O(pv(o).concat(pv(f)), x => dist(P(o, x), P(f, x)) - m.v, s, { k: 'DA-ayak', m });
        O(pv(f).concat(pv(c)), x => dist(P(f, x), P(c, x)) - m.v2, s, { k: 'DA-boy', m });
        const sg = Math.sign(cross(sub(P(o, X), P(f, X)), sub(P(c, X), P(f, X)))) || 1;
        O(pv(o).concat(pv(f), pv(c)), x => (wrap(Math.atan2(cross(sub(P(o, x), P(f, x)), sub(P(c, x), P(f, x))), dot(sub(P(o, x), P(f, x)), sub(P(c, x), P(f, x)))) - sg * Math.PI / 2)) * 180 / Math.PI, opt.sRight, { k: 'DA-dik', m }); }
    });
    /* kroki şekli: kenar boyları (ortak ölçek K ile), köşe açıları, düz duvarlar */
    const uniq = new Set(), edges = []; M.segs.forEach(([a, b]) => { const k = a < b ? a + '|' + b : b + '|' + a; if (uniq.has(k)) return; uniq.add(k); edges.push([a, b]); });
    edges.forEach(([an, bn]) => { const a = I(an), b = I(bn), L0 = dist(M.names[an].sk, M.names[bn].sk); if (L0 < 1e-6) return; O(pv(a).concat(pv(b), [NK]), x => dist(P(a, x), P(b, x)) - x[NK] * L0, opt.sLenAbs + opt.sLenRel * L0, { k: 'kroki-boy', a: an, b: bn }); });
    const nb = {}; edges.forEach(([a, b]) => { (nb[a] = nb[a] || []).push(b); (nb[b] = nb[b] || []).push(a); });
    Object.keys(nb).forEach(vn => { const V = M.names[vn].sk, ns = nb[vn].slice().sort((p, q) => Math.atan2(...sub(M.names[p].sk, V).reverse()) - Math.atan2(...sub(M.names[q].sk, V).reverse())); if (ns.length < 2) return;
      for (let k = 0; k < ns.length; k++) { if (ns.length === 2 && k === 1) break; const an = ns[k], bn = ns[(k + 1) % ns.length]; const u0 = sub(M.names[an].sk, V), w0 = sub(M.names[bn].sk, V); const th0 = Math.atan2(cross(u0, w0), dot(u0, w0));
        const straight = Math.abs(Math.abs(th0) - Math.PI) < 0.5 * Math.PI / 180; const v = I(vn), a = I(an), b = I(bn);
        O(pv(v).concat(pv(a), pv(b)), x => { const u = sub(P(a, x), P(v, x)), w = sub(P(b, x), P(v, x)); return wrap(Math.atan2(cross(u, w), dot(u, w)) - th0) * 180 / Math.PI; }, straight ? opt.sStraight : opt.sAngle, { k: straight ? 'duz-duvar' : 'kroki-aci', v: vn }); } });
    /* kenar üstündeki adlı noktalar (çizgi üstü nokta adı, dik ayak ucu) kenarda kalır */
    M.list.forEach(n => { if (nb[n.name]) return; edges.forEach(([an, bn]) => { const A = M.names[an].sk, B = M.names[bn].sk, d = sub(B, A), t = dot(sub(n.sk, A), d) / dot(d, d); if (t <= 1e-4 || t >= 1 - 1e-4) return; if (Math.abs(cross(d, sub(n.sk, A))) / len(d) > 2e-3) return; const p = I(n.name), a = I(an), b = I(bn); O(pv(p).concat(pv(a), pv(b)), x => cross(sub(P(b, x), P(a, x)), sub(P(p, x), P(a, x))) / dist(P(a, x), P(b, x)), opt.sOnLine, { k: 'kenarda', name: n.name }); }); });
    /* Gauss-Newton (yoğun normal denklemler, Cholesky) */
    let it = 0, dxMax = 1;
    for (; it < 25 && dxMax > 1e-7; it++) {
      const Nm = new Float64Array(nP * nP), bv = new Float64Array(nP);
      obs.forEach(o => { const w = 1 / (o.s * o.s), r0 = o.f(X), g = o.vars.map(j => { const h = 1e-6, old = X[j]; X[j] = old + h; const r1 = o.f(X); X[j] = old - h; const r2 = o.f(X); X[j] = old; return (r1 - r2) / (2 * h); });
        for (let p = 0; p < g.length; p++) { const jp = o.vars[p]; bv[jp] -= w * g[p] * r0; for (let q = 0; q < g.length; q++) Nm[jp * nP + o.vars[q]] += w * g[p] * g[q]; } });
      for (let j = 0; j < nP; j++) Nm[j * nP + j] += 1e-9 + Nm[j * nP + j] * 1e-12;
      const dx = chol(Nm, bv, nP); dxMax = 0; for (let j = 0; j < nP; j++) { X[j] += dx[j]; if (j < NK) dxMax = Math.max(dxMax, Math.abs(dx[j])); }
    }
    const coords = {}; M.list.forEach((n, i) => { coords[n.name] = [X[2 * i], X[2 * i + 1]]; });
    const res = obs.filter(o => o.info.k !== 'prior').map(o => ({ ...o.info, r: o.f(X), s: o.s }));
    return { coords, K: X[NK], H, matched: matched.map(n => n.name), iter: it, res, unmatchedTotals: totals.filter(t => !idx.hasOwnProperty(t.name)).map(t => t.name) };
  }
  function chol(A, b, n) {
    const L = new Float64Array(n * n);
    for (let i = 0; i < n; i++) for (let j = 0; j <= i; j++) { let s = A[i * n + j]; for (let k = 0; k < j; k++) s -= L[i * n + k] * L[j * n + k]; if (i === j) L[i * n + i] = Math.sqrt(Math.max(s, 1e-18)); else L[i * n + j] = s / L[j * n + j]; }
    const y = new Float64Array(n); for (let i = 0; i < n; i++) { let s = b[i]; for (let k = 0; k < i; k++) s -= L[i * n + k] * y[k]; y[i] = s / L[i * n + i]; }
    const x = new Float64Array(n); for (let i = n - 1; i >= 0; i--) { let s = y[i]; for (let k = i + 1; k < n; k++) s -= L[k * n + i] * x[k]; x[i] = s / L[i * n + i]; }
    return x;
  }

  /* ---------- dengelenmiş DXF ---------- */
  function outputDXF(M, R, totals) {
    const E = [], f = v => (Math.round(v * 10000) / 10000).toString(), deg = r => ((r * 180 / Math.PI) % 360 + 360) % 360;
    const C = n => R.coords[n];
    const line = (ly, a, b) => E.push('0', 'LINE', '8', ly, '10', f(a[0]), '20', f(a[1]), '30', '0', '11', f(b[0]), '21', f(b[1]), '31', '0');
    const text = (ly, p, h, t) => E.push('0', 'TEXT', '8', ly, '10', f(p[0]), '20', f(p[1]), '30', '0', '40', f(h), '1', String(t).replace(/[^\x20-\x7e]/g, ch => '\\U+' + ch.charCodeAt(0).toString(16).toUpperCase().padStart(4, '0')), '7', 'ARIAL');
    const point = (ly, p) => E.push('0', 'POINT', '8', ly, '10', f(p[0]), '20', f(p[1]), '30', '0');
    M.drawn.forEach(d => { const pts = d.ns.map(n => n && C(n)); if (pts.some(p => !p)) return;
      if (d.t === 'line') line('CIZIM', pts[0], pts[1]);
      else { E.push('0', 'POLYLINE', '8', 'CIZIM', '66', '1', '10', '0', '20', '0', '30', '0', '70', d.c ? '1' : '0'); pts.forEach(p => E.push('0', 'VERTEX', '8', 'CIZIM', '10', f(p[0]), '20', f(p[1]), '30', '0')); E.push('0', 'SEQEND', '8', 'CIZIM'); } });
    M.arcs.forEach(a => { if (!a.a || !a.b) return; const A = C(a.a), B = C(a.b), ch = dist(A, B), r = ch / (2 * Math.sin(a.sw / 2)); const m = mul(add(A, B), 0.5), u = mul(sub(B, A), 1 / ch), n = [-u[1], u[0]], h = Math.sqrt(Math.max(0, r * r - ch * ch / 4)) * (a.sw > Math.PI ? -1 : 1); const c = add(m, mul(n, h)); E.push('0', 'ARC', '8', 'CIZIM', '10', f(c[0]), '20', f(c[1]), '30', '0', '40', f(r), '50', f(deg(Math.atan2(A[1] - c[1], A[0] - c[0]))), '51', f(deg(Math.atan2(B[1] - c[1], B[0] - c[0])))); });
    const Hs = helmert(M.list.map(n => n.sk), M.list.map(n => C(n.name))), Ks = Math.hypot(Hs.a, Hs.b);
    M.circles.forEach(c => { const p = applyH(Hs, c.c); E.push('0', 'CIRCLE', '8', 'CIZIM', '10', f(p[0]), '20', f(p[1]), '30', '0', '40', f(c.r * Ks)); });
    /* kapı/pencere blokları: a ucuna, a→b doğrultusu ve boyuyla */
    const B = []; M.ops.forEach(o => { const blk = M.blocks[o.blk]; if (!blk || !C(o.a) || !C(o.b)) return; const ska = M.names[o.a].sk, skb = M.names[o.b].sk;
      const rot = Math.atan2(...sub(C(o.b), C(o.a)).reverse()) - Math.atan2(...sub(skb, ska).reverse()), sc = dist(C(o.a), C(o.b)) / (dist(ska, skb) || 1);
      E.push('0', 'INSERT', '8', o.kind === 'door' ? 'KAPI' : 'PENCERE', '2', o.blk, '10', f(C(o.a)[0]), '20', f(C(o.a)[1]), '30', '0', '41', f(sc), '42', f(sc), '50', f(deg(rot))); });
    Object.values(M.blocks).forEach(b => { if (!M.ops.some(o => o.blk === b.name)) return; B.push('0', 'BLOCK', '8', '0', '2', b.name, '70', '0', '10', f(b.base[0]), '20', f(b.base[1]), '30', '0', '3', b.name);
      b.ents.forEach(e => { if (e.t === 'line') B.push('0', 'LINE', '8', '0', '10', f(e.a[0]), '20', f(e.a[1]), '30', '0', '11', f(e.b[0]), '21', f(e.b[1]), '31', '0'); else if (e.t === 'arc') B.push('0', 'ARC', '8', '0', '10', f(e.c[0]), '20', f(e.c[1]), '30', '0', '40', f(e.r), '50', f(deg(e.a0)), '51', f(deg(e.a1))); }); B.push('0', 'ENDBLK', '8', '0'); });
    M.list.forEach(n => { const p = C(n.name), ly = R.matched.includes(n.name) ? 'NOKTA_TOTAL' : n.user ? 'NOKTA_AD' : 'NOKTA_X'; point(ly, p); text(ly, add(p, [0.05, 0.05]), 0.1, n.name); });
    totals.filter(t => !R.coords[t.name]).forEach(t => { point('TOTAL_DIGER', t.p); text('TOTAL_DIGER', add(t.p, [0.05, 0.05]), 0.1, t.name); });
    M.meas.forEach(m => { const ly = m.k === 'GN' ? 'GONYE' : m.k === 'DA' ? 'DIKAYAK' : 'OLCU'; const pts = ['a', 'b', 'p', 'o', 'f', 'c'].map(k => m[k] && C(m[k])).filter(Boolean); if (m.k === 'DA') { line(ly, C(m.o), C(m.f)); line(ly, C(m.f), C(m.c)); } else if (['NN', 'OB', 'GN'].includes(m.k)) line(ly, C(m.a), C(m.b)); if (pts.length) text(ly, mul(pts.reduce(add, [0, 0]), 1 / pts.length), 0.08, m.txt); });
    const LY = [['CIZIM', 7], ['KAPI', 2], ['PENCERE', 4], ['NOKTA_TOTAL', 5], ['NOKTA_AD', 3], ['NOKTA_X', 1], ['TOTAL_DIGER', 5], ['OLCU', 30], ['GONYE', 5], ['DIKAYAK', 6]];
    const H = ['0', 'SECTION', '2', 'HEADER', '9', '$ACADVER', '1', 'AC1009', '9', '$DWGCODEPAGE', '3', 'ANSI_1254', '0', 'ENDSEC', '0', 'SECTION', '2', 'TABLES', '0', 'TABLE', '2', 'LAYER', '70', String(LY.length)];
    LY.forEach(([n, c]) => H.push('0', 'LAYER', '2', n, '70', '0', '62', String(c), '6', 'CONTINUOUS'));
    H.push('0', 'ENDTAB', '0', 'TABLE', '2', 'STYLE', '70', '1', '0', 'STYLE', '2', 'ARIAL', '70', '0', '40', '0', '41', '1', '50', '0', '71', '0', '42', '0.1', '3', 'arial.ttf', '4', '', '0', 'ENDTAB', '0', 'ENDSEC', '0', 'SECTION', '2', 'BLOCKS'); B.forEach(x => H.push(x)); H.push('0', 'ENDSEC', '0', 'SECTION', '2', 'ENTITIES');
    return H.concat(E, ['0', 'ENDSEC', '0', 'EOF']).join('\r\n') + '\r\n';
  }
  function coordCSV(M, R) { return 'AD;Y;X;KAYNAK\r\n' + M.list.map(n => { const p = R.coords[n.name]; return `${n.name};${p[0].toFixed(3)};${p[1].toFixed(3)};${R.matched.includes(n.name) ? 'TOTAL' : n.user ? 'AD' : 'PROGRAM'}`; }).join('\r\n') + '\r\n'; }
  return { parseDXF, readTotal, buildModel, adjust, outputDXF, coordCSV, helmert, applyH, DEF };
})();
if (typeof module !== 'undefined') module.exports = G;
