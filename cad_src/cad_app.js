/* ROLEVE CAD — uygulama */
const VER = 'cad-1.9';
const KEY = 'rcad1_doc';
const cv = document.getElementById('cv'), cx = cv.getContext('2d');
let D = { ents: [], nid: 1 };
let view = { s: 50, ox: 0, oy: 0 };
let hist = [], hi = -1;
const S = {
  tool: 'sec', draw: 'line', edit: 'offset', fly: null, sel: new Set(),
  chain: null, cir: null, arc: null, pick: null, sum: 0, sumH: [], offD: 0.2, offStr: '',
  snaps: { end: 1, mid: 1, near: 1, orth: 1, xy: 0, trk: 1 },
  cur: null, snap: null, drag: null, preview: null, hl: null, acq: [], flash: null, npOpen: false, open: 'door', selOp: null, opA: null, arm: 0, thMax: 0.6, setStr: '', autoCut: 1
};
const DRAW = ['line', 'pl', 'cir', 'arc'], EDIT = ['offset', 'trim', 'extend', 'fillet', 'flat', 'move', 'copy', 'explode', 'join', 'erase'];
const SNAPK = [['end', 's_end'], ['mid', 's_mid'], ['near', 's_near'], ['orth', 's_orth'], ['xy', 's_xy'], ['trk', 'trk']];
const ICON = { door: 'door', win: 'window', line: 'line', pl: 'pline', cir: 'circle', arc: 'arc', offset: 'offset', trim: 'trim', extend: 'extend', fillet: 'fillet', flat: 'flat', move: 'move', copy: 'copy', explode: 'explode', join: 'join', erase: 'erase' };
const svg = k => `<svg viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" fill="none">${ICONS[k] || ''}</svg>`;

/* ---------- belge ---------- */
const entById = id => D.ents.find(e => e.id === id);
function addEnt(e) { e.id = 'e' + (D.nid++); D.ents.push(e); return e; }
function delEnt(e) { D.ents = D.ents.filter(x => x !== e); S.sel.delete(e.id); }
function replEnt(e, list) { const i = D.ents.indexOf(e); D.ents.splice(i, 1); S.sel.delete(e.id); list.forEach((n, k) => { n.id = 'e' + (D.nid++); D.ents.splice(i + k, 0, n); }); }
let CACHE = { v: -1 };
function invalidate() { CACHE = { v: -1 }; }
function commit() { invalidate(); hist = hist.slice(0, hi + 1); hist.push(JSON.stringify(D)); if (hist.length > 300) hist.shift(); hi = hist.length - 1; save(); render(); }
function save() { try { localStorage.setItem(KEY, JSON.stringify({ D, view, snaps: S.snaps, offD: S.offD, draw: S.draw, edit: S.edit, open: S.open, thMax: S.thMax, autoCut: S.autoCut })); } catch (e) { } }
function load() { try { const o = JSON.parse(localStorage.getItem(KEY) || 'null'); if (o) { D = o.D || D; view = o.view || view; Object.assign(S.snaps, o.snaps || {}); S.offD = o.offD || 0.2; S.draw = o.draw || 'line'; S.edit = o.edit || 'offset'; S.open = o.open || 'door'; S.thMax = o.thMax || 0.6; S.autoCut = o.autoCut == null ? 1 : o.autoCut; } } catch (e) { } D.ops = D.ops || []; hist = [JSON.stringify(D)]; hi = 0; }
function undo() {
  if (S.chain && S.chain.pts.length === 1) { S.chain = null; ui(); render(); return; }
  if (S.cir) { S.cir = null; ui(); render(); return; } if (S.arc) { S.arc.pts.pop(); if (!S.arc.pts.length) S.arc = null; ui(); render(); return; }
  if (S.opA) { S.opA = null; render(); return; }
  if (hi <= 0) return; hi--; D = JSON.parse(hist[hi]); D.ops = D.ops || []; invalidate(); if (S.selOp && !opById(S.selOp)) S.selOp = null;
  if (S.chain) { S.chain.pts.pop(); if (S.chain.k === 'pl' && S.chain.pts.length < 2) { S.chain.eid = null; } }
  S.sel = new Set([...S.sel].filter(id => entById(id))); save(); render();
}
function redo() { if (hi >= hist.length - 1) return; hi++; D = JSON.parse(hist[hi]); D.ops = D.ops || []; invalidate(); S.chain = null; save(); render(); }

/* ---------- görünüm ---------- */
let W = 0, H = 0, DPR = 1;
function resize() { DPR = window.devicePixelRatio || 1; W = innerWidth; H = innerHeight; cv.width = W * DPR; cv.height = H * DPR; cv.style.width = W + 'px'; cv.style.height = H + 'px'; if (!view.ox && !view.oy) { view.ox = W * 0.42; view.oy = H * 0.55; } render(); }
const w2s = (x, y) => [view.ox + x * view.s, view.oy - y * view.s];
const s2w = (X, Y) => [(X - view.ox) / view.s, (view.oy - Y) / view.s];
function fit() {
  const pts = []; D.ents.forEach(e => { if (e.t === 'line') pts.push(e.a, e.b); else if (e.t === 'pl') pts.push(...e.p); else if (e.t === 'pt') pts.push(e.p); else { pts.push([e.c[0] - e.r, e.c[1] - e.r], [e.c[0] + e.r, e.c[1] + e.r]); } });
  if (!pts.length) { view.s = 50; view.ox = W * 0.42; view.oy = H * 0.55; render(); save(); return; }
  const xs = pts.map(p => p[0]), ys = pts.map(p => p[1]); const x0 = Math.min(...xs), x1 = Math.max(...xs), y0 = Math.min(...ys), y1 = Math.max(...ys);
  const aw = W - 90 - 30, ah = H - 140; view.s = Math.min(400, Math.max(2, Math.min(aw / Math.max(x1 - x0, 0.5), ah / Math.max(y1 - y0, 0.5))));
  view.ox = 15 + aw / 2 - (x0 + x1) / 2 * view.s; view.oy = 70 + ah / 2 + (y0 + y1) / 2 * view.s; render(); save();
}

/* ---------- yakalama ---------- */
function allInts() {
  if (CACHE.ints) return CACHE.ints; const out = [], E = D.ents;
  for (let i = 0; i < E.length; i++) { const A = prims(E[i]); for (let j = i + 1; j < E.length; j++) { const B = prims(E[j]); A.forEach(P => B.forEach(Q => primInts(P, Q).forEach(p => out.push(p)))); } }
  return (CACHE.ints = out);
}
function keyPts(ex) {
  const out = []; D.ents.forEach(e => { if (ex && ex.has(e.id)) return;
    if (e.t === 'line') out.push({ p: e.a, P: prims(e)[0] }, { p: e.b, P: prims(e)[0] });
    else if (e.t === 'pl') { const ps = prims(e); e.p.forEach((p, i) => out.push({ p, P: ps[Math.min(i, ps.length - 1)] })); }
    else if (e.t === 'arc') { const a = arcPts(e); out.push({ p: a[0] }, { p: a[2] }, { p: e.c }); }
    else if (e.t === 'pt') out.push({ p: e.p });
    else out.push({ p: e.c }); });
  if (!ex) opsList().forEach(o => out.push({ p: o.a }, { p: o.b }));
  return out;
}
function snapAt(X, Y, o) {
  o = o || {}; const q = s2w(X, Y), R = 18 / view.s, ex = o.ex, sn = S.snaps; let best = null;
  const ents = D.ents.filter(e => !(ex && ex.has(e.id)));
  const consider = (p, k, P, g) => { const d = vdist(p, q); if (d <= R && (!best || d < best.d - 1e-12)) best = { p: cl(p), k, P, d, g }; };
  if (sn.end) { keyPts(ex).forEach(k => consider(k.p, 'end', k.P)); (o.extra || []).forEach(p => consider(p, 'end')); if (!ex) allInts().forEach(p => consider(p, 'int')); else intsAmong(ents).forEach(p => consider(p, 'int')); }
  if (best) return best;
  if (sn.mid) { ents.forEach(e => { if (e.t === 'arc') consider(arcPts(e)[1], 'mid'); else prims(e).forEach(P => { if (P.k === 's') consider(vmul(vadd(P.a, P.b), 0.5), 'mid', P); }); }); }
  if (best) return best;
  const segs = []; ents.forEach(e => prims(e).forEach(P => { if (P.k === 's' && vdist(P.a, P.b) > 1e-6) segs.push(P); }));
  let dirs = [];
  if (o.from) { const base = o.dir ? vunit(o.dir) : [1, 0]; if (sn.orth) { const b = o.dir ? base : [1, 0]; dirs.push(b, vperp(b), vmul(b, -1), vmul(vperp(b), -1)); } if (sn.xy) dirs.push([1, 0], [0, 1], [-1, 0], [0, -1]); }
  if (dirs.length && vdist(q, o.from) > 1e-9) {
    const u = vunit(vsub(q, o.from)); let bd = dirs[0]; dirs.forEach(d => { if (vdot(d, u) > vdot(bd, u)) bd = d; });
    const proj = vadd(o.from, vmul(bd, Math.max(0, vdot(vsub(q, o.from), bd)))); const far = vadd(o.from, bd);
    let hit = null; const tryP = (p, k, g) => { const d = vdist(p, proj); if (d <= R && vdot(vsub(p, o.from), bd) > 1e-9 && (!hit || d < hit.d)) hit = { p: cl(p), k, d, g }; };
    if (sn.near) ents.forEach(e => prims(e).forEach(P => { if (P.k === 's') segSeg(o.from, far, P.a, P.b, true).forEach(x => { if (x.u >= -1e-9 && x.u <= 1 + 1e-9) tryP(x.p, 'int'); }); else lineCirc2(o.from, far, P).forEach(p => tryP(p, 'int')); }));
    if (sn.trk) trkLines(segs, o).forEach(L => { const x = segSeg(o.from, far, L.a, vadd(L.a, L.d), true)[0]; if (!x) return; const go = trkOrigin(L, x.p); if (go && vdist(x.p, proj) <= 10 / view.s) tryP(x.p, 'trk', [go, x.p]); });
    if (hit) return { ...hit, g: [[o.from, hit.p]].concat(hit.g ? [hit.g] : []), ortho: true };
    return { p: proj, k: 'orth', g: [[o.from, proj]], ortho: true };
  }
  if (sn.near) ents.forEach(e => prims(e).forEach(P => { const r = nearPrim(P, q); consider(r.p, 'near', P); }));
  if (best) return best;
  if (sn.trk) {
    const RT = 10 / view.s, near = [];
    trkLines(segs, o).forEach(L => { const l2 = vdot(L.d, L.d), t = vdot(vsub(q, L.a), L.d) / l2, p = vadd(L.a, vmul(L.d, t)); const go = trkOrigin(L, p); if (go && vdist(p, q) <= RT) near.push({ L, p, go }); });
    for (let i = 0; i < near.length; i++) for (let j = i + 1; j < near.length; j++) { const x = segSeg(near[i].L.a, vadd(near[i].L.a, near[i].L.d), near[j].L.a, vadd(near[j].L.a, near[j].L.d), true)[0]; if (x) { const g1 = trkOrigin(near[i].L, x.p), g2 = trkOrigin(near[j].L, x.p); if (g1 && g2) consider(x.p, 'trk', null, [[g1, x.p], [g2, x.p]]); } }
    if (best) return best;
    near.sort((a, b) => vdist(a.p, q) - vdist(b.p, q)); if (near[0]) { const n = near[0]; return { p: n.p, k: 'trk', P: n.L.P, g: [[n.go, n.p]] }; }
  }
  return { p: q, k: 'free' };
}
/* aks takibi çizgileri: çizgi uzantıları + hiza noktalarından 90° çizgiler */
function trkLines(segs, o) {
  const out = segs.map(P => ({ a: P.a, d: vsub(P.b, P.a), P }));
  const pts = (o.trkPts || []).concat(S.acq); if (!pts.length) return out;
  const b = o.tbase ? vunit(o.tbase) : null, dirs = []; if (b) dirs.push(b, vperp(b)); if (S.snaps.xy || !b) dirs.push([1, 0], [0, 1]);
  const seen = []; pts.forEach(p => { if (seen.some(q => vsame(q, p))) return; seen.push(p); dirs.forEach(d => out.push({ a: p, d, pt: true })); });
  return out;
}
function trkOrigin(L, x) { if (L.pt) return vdist(L.a, x) > 1e-6 ? L.a : null; const t = vdot(vsub(x, L.a), L.d) / vdot(L.d, L.d); if (t > -1e-6 && t < 1 + 1e-6) return null; return t < 0 ? L.a : vadd(L.a, L.d); }
function lineCirc2(a, b, P) { const d = vsub(b, a), f = vsub(a, P.c), A = vdot(d, d), B = 2 * vdot(f, d), C = vdot(f, f) - P.r * P.r, Dd = B * B - 4 * A * C; if (Dd < 0) return []; const s = Math.sqrt(Dd); return [(-B - s) / (2 * A), (-B + s) / (2 * A)].map(t => vadd(a, vmul(d, t))).filter(p => inSweep(P, p)); }
function intsAmong(E) { const out = []; for (let i = 0; i < E.length; i++) { const A = prims(E[i]); for (let j = i + 1; j < E.length; j++) prims(E[j]).forEach(Q => A.forEach(P => primInts(P, Q).forEach(p => out.push(p)))); } return out; }

/* ---------- isabet ---------- */
function hitEnt(X, Y, tolPx) { const q = s2w(X, Y), R = (tolPx || 16) / view.s; let best = null; D.ents.forEach(e => { if (e.imp) return; const r = nearEnt(e, q); if (r && r.d <= R && (!best || r.d < best.d)) best = { e, d: r.d, r }; }); return best; }

/* ---------- tutamaklar ---------- */
function gripsOf(e) {
  const g = [];
  if (e.t === 'line') { g.push({ k: 'v', i: 0, p: e.a }, { k: 'v', i: 1, p: e.b }, { k: 'm', p: vmul(vadd(e.a, e.b), 0.5) }); }
  else if (e.t === 'pl') { e.p.forEach((p, i) => g.push({ k: 'v', i, p })); plRuns(e).forEach(r => g.push({ k: 'm', run: r, p: vmul(vadd(e.p[r.i0], e.p[r.i1 % e.p.length]), 0.5) })); }
  else if (e.t === 'cir') { g.push({ k: 'c', p: e.c }); [0, 1, 2, 3].forEach(i => g.push({ k: 'r', p: vadd(e.c, [e.r * Math.cos(i * Math.PI / 2), e.r * Math.sin(i * Math.PI / 2)]) })); }
  else if (e.t === 'arc') { const a = arcPts(e); g.push({ k: 'a', i: 0, p: a[0] }, { k: 'a', i: 1, p: a[1] }, { k: 'a', i: 2, p: a[2] }, { k: 'c', p: e.c }); }
  return g;
}
function gripAt(X, Y) { let best = null; const so = S.selOp && opById(S.selOp); if (so) ['a', 'b'].forEach(w => { const s = w2s(...so[w]); const d = Math.hypot(s[0] - X, s[1] - Y); if (d < 24 && (!best || d < best.d)) best = { e: { id: '__op' }, op: so.id, g: { k: 'od', w, p: so[w] }, d }; }); S.sel.forEach(id => { const e = entById(id); if (!e) return; gripsOf(e).forEach(g => { const s = w2s(g.p[0], g.p[1]); const d = Math.hypot(s[0] - X, s[1] - Y); if (d < 24 && (!best || d < best.d - 2 || (g.k === 'm' && d <= best.d + 2))) best = { e, g, d }; }); }); return best; }
/* nokta çakışanlar: diğer objelerin uç/köşe noktaları */
function coincident(p, skipE, skipI) {
  const out = []; D.ents.forEach(f => {
    if (f.t === 'line') { if (!(f === skipE && skipI === 0) && vsame(f.a, p)) out.push({ f, set: v => { f.a = v; }, other: f.b }); if (!(f === skipE && skipI === 1) && vsame(f.b, p)) out.push({ f, set: v => { f.b = v; }, other: f.a }); }
    else if (f.t === 'pl') f.p.forEach((q, i) => { if (f === skipE && i === skipI) return; if (vsame(q, p)) { const n = f.p.length; const nb = (i > 0 || f.c) ? f.p[(i - 1 + n) % n] : (n > 1 ? f.p[1] : null); out.push({ f, set: v => { f.p[i] = v; }, other: (i === 0 && !f.c) ? f.p[1] : nb, end: !f.c && (i === 0 || i === n - 1) }); } });
  });
  return out;
}
function applyVertex(e, i, P) {
  const old = e.t === 'line' ? cl(i === 0 ? e.a : e.b) : cl(e.p[i]);
  coincident(old, e, i).forEach(c => c.set(cl(P))); opsList().forEach(o => { if (vsame(o.a, old)) o.a = cl(P); if (vsame(o.b, old)) o.b = cl(P); });
  if (e.t === 'line') { if (i === 0) e.a = cl(P); else e.b = cl(P); } else e.p[i] = cl(P);
}
function lineX(p, d, q, e) { const x = segSeg(p, vadd(p, d), q, vadd(q, e), true)[0]; return x ? x.p : null; }
/* kenarı paralel kaydır: komşular kendi doğrultusunda uzar/kısalır */
function applyEdge(e, g, P) {
  let A, B, idx;
  if (e.t === 'line') { A = cl(e.a); B = cl(e.b); }
  else { const n = e.p.length; A = cl(e.p[g.run.i0]); B = cl(e.p[g.run.i1 % n]); idx = []; let k = g.run.i0; for (let s = 0; s <= n; s++) { idx.push(k % n); if (k % n === g.run.i1 % n) break; k++; } }
  const t = vunit(vsub(B, A)), nn = vperp(t), M = vmul(vadd(A, B), 0.5), d = vdot(vsub(P, M), nn); if (Math.abs(d) < 1e-9) return;
  const off = vmul(nn, d), A2 = vadd(A, off); const opsE = opsOnSeg(A, B);
  const neighDir = (V, isA) => {
    if (e.t === 'pl') { const n = e.p.length, i = isA ? g.run.i0 : g.run.i1 % n, j = isA ? i - 1 : i + 1; if (e.c || (j >= 0 && j < n)) { const q = e.p[(j + n) % n]; return { q, dir: vsub(V, q) }; } }
    const cs = coincident(V, e, e.t === 'line' ? (isA ? 0 : 1) : (isA ? g.run.i0 : g.run.i1 % e.p.length)).filter(c => c.other && !vsame(c.other, V));
    if (cs.length === 1) return { q: cs[0].other, dir: vsub(V, cs[0].other) }; return null;
  };
  const newEnd = (V, isA) => { const nb = neighDir(V, isA); if (nb && Math.abs(vcross(vunit(nb.dir), t)) > 1e-6) { const x = lineX(nb.q, nb.dir, A2, t); if (x) return x; } return vadd(V, off); };
  const nA = newEnd(A, true), nB = newEnd(B, false);
  /* T bağlantıları: kenarın üstünde biten uçlar */
  const tees = []; D.ents.forEach(f => { if (f === e) return; const ends = f.t === 'line' ? [[0, f.a, f.b], [1, f.b, f.a]] : (f.t === 'pl' && !f.c ? [[0, f.p[0], f.p[1]], [f.p.length - 1, f.p[f.p.length - 1], f.p[f.p.length - 2]]] : []);
    ends.forEach(([i, p, o]) => { if (vsame(p, A) || vsame(p, B)) return; const r = nearPrim({ k: 's', a: A, b: B }, p); if (r.d < CO && r.t > 1e-6 && r.t < 1 - 1e-6) { const x = Math.abs(vcross(vunit(vsub(p, o)), t)) > 1e-6 ? lineX(o, vsub(p, o), A2, t) : vadd(p, off); if (x) tees.push({ f, i, x }); } }); });
  const cA = coincident(A, e, e.t === 'line' ? 0 : g.run.i0), cB = coincident(B, e, e.t === 'line' ? 1 : g.run.i1 % (e.p ? e.p.length : 2));
  cA.forEach(c => c.set(cl(nA))); cB.forEach(c => c.set(cl(nB)));
  opsE.forEach(o => { o.a = vadd(o.a, off); o.b = vadd(o.b, off); });
  tees.forEach(({ f, i, x }) => { if (f.t === 'line') { if (i === 0) f.a = cl(x); else f.b = cl(x); } else f.p[i] = cl(x); });
  if (e.t === 'line') { e.a = cl(nA); e.b = cl(nB); }
  else { idx.forEach((k, j) => { if (j === 0) e.p[k] = cl(nA); else if (j === idx.length - 1) e.p[k] = cl(nB); else e.p[k] = vadd(e.p[k], off); }); }
}
function applyGrip(e, g, P) {
  if (g.k === 'v') applyVertex(e, g.i, P);
  else if (g.k === 'm') applyEdge(e, g, P);
  else if (g.k === 'c') { const d = vsub(P, e.c); e.c = cl(P); if (e.t === 'arc') { } void d; }
  else if (g.k === 'r') { e.r = Math.max(1e-3, vdist(P, e.c)); }
  else if (g.k === 'a') { const a = arcPts(e); a[g.i] = P; const n = arc3(a[0], a[1], a[2]); if (n) Object.assign(e, { c: n.c, r: n.r, a0: n.a0, a1: n.a1 }); }
}
function gripDir(e, g) { if (e.t === 'line') return vsub(e.b, e.a); if (e.t === 'pl' && g.k === 'v') { const n = e.p.length, j = g.i > 0 ? g.i - 1 : (e.c ? n - 1 : 1); return vsub(e.p[g.i], e.p[j]); } return null; }

/* ---------- çizim zinciri ---------- */
function chainAdd(p, snapP) {
  const c = S.chain;
  if (!c) { S.chain = { k: S.tool, pts: [cl(p)], dir0: snapP && snapP.k === 's' ? vsub(snapP.b, snapP.a) : null, eid: null }; render(); return; }
  const last = c.pts[c.pts.length - 1]; if (vsame(p, last)) { endChain(); return; }
  const closing = vsame(p, c.pts[0]) && c.pts.length >= 3;
  if (c.k === 'line') { addEnt({ t: 'line', a: cl(last), b: cl(p) }); c.pts.push(cl(p)); commit(); if (closing) endChain(); return; }
  if (closing && c.pts.length >= 3) { const e = entById(c.eid); if (e) { e.c = true; commit(); } endChain(); return; }
  c.pts.push(cl(p));
  if (!c.eid || !entById(c.eid)) { const e = addEnt({ t: 'pl', p: c.pts.map(cl), c: false }); c.eid = e.id; } else entById(c.eid).p = c.pts.map(cl);
  commit();
}
function endChain() { S.acq = []; S.chain = null; S.sum = 0; S.sumH = []; S.full = false; ui(); render(); }
function chainDir() { const c = S.chain; if (!c) return null; if (c.pts.length >= 2) return vsub(c.pts[c.pts.length - 1], c.pts[c.pts.length - 2]); return c.dir0; }
function quickArrow(dx, dy) { const c = S.chain; if (!c || !S.sum) return; const last = c.pts[c.pts.length - 1]; const p = vadd(last, vmul([dx, dy], S.sum / 100)); S.sum = 0; S.sumH = []; chainAdd(p); ui(); }

/* ---------- işaretçi ---------- */
const ptrs = new Map(); let G = null;
cv.addEventListener('pointerdown', ev => {
  ev.preventDefault(); cv.setPointerCapture(ev.pointerId); ptrs.set(ev.pointerId, [ev.clientX, ev.clientY]);
  if (S.fly || S.full) { S.fly = null; S.full = false; ui(); }
  document.body.classList.add('touching');
  if (ptrs.size === 2) { const [a, b] = [...ptrs.values()]; G = { k: 'pinch', d0: Math.hypot(a[0] - b[0], a[1] - b[1]), c0: [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2], v0: { ...view } }; S.cur = null; S.drag = null; render(); return; }
  if (ptrs.size > 2) return;
  const X = ev.clientX, Y = ev.clientY; G = { k: 'one', x0: X, y0: Y, moved: false };
  const t = S.tool;
  if (t === 'sec') { const gp = gripAt(X, Y); if (gp) { G.k = 'grip'; G.gp = gp; G.base = JSON.stringify(D); G.orig = cl(gp.g.p); } else G.k = 'tap'; }
  else if (DRAW.includes(t) || OPEN.includes(t)) { G.k = 'place'; }
  else if (t === 'move' || t === 'copy') { G.k = 'mv'; }
  else G.k = 'tap';
  pmove(X, Y);
});
cv.addEventListener('pointermove', ev => {
  if (!ptrs.has(ev.pointerId)) return; ptrs.set(ev.pointerId, [ev.clientX, ev.clientY]); if (!G) return;
  if (G.k === 'pinch' && ptrs.size === 2) { const [a, b] = [...ptrs.values()]; const d = Math.hypot(a[0] - b[0], a[1] - b[1]), c = [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2]; const k = d / (G.d0 || 1), v = G.v0; const ns = Math.max(1, Math.min(3000, v.s * k)); const w = [(G.c0[0] - v.ox) / v.s, (v.oy - G.c0[1]) / v.s]; view.s = ns; view.ox = c[0] - w[0] * ns; view.oy = c[1] + w[1] * ns; render(); return; }
  pmove(ev.clientX, ev.clientY);
});
function pmove(X, Y) {
  if (!G || G.k === 'none') return; const dx = X - G.x0, dy = Y - G.y0; if (Math.hypot(dx, dy) > 8) G.moved = true;
  if (G.k === 'tap' && G.moved) { G.k = 'pan'; G.v0 = { ...view }; }
  if (G.k === 'pan') { view.ox = G.v0.ox + dx; view.oy = G.v0.oy + dy; render(); return; }
  if (G.k === 'place') { const o = drawSnapOpts(); S.snap = snapAt(X, Y, o); acquire(S.snap); S.cur = [X, Y]; render(); return; }
  if (G.k === 'grip' && G.gp.op) { D = JSON.parse(G.base); const o = opById(G.gp.op), w = G.gp.g.w, old = cl(o[w]); let sn = snapAt(X, Y, {}); if (vdist(sn.p, old) < 1e-6) sn = { p: s2w(X, Y), k: 'free' }; S.snap = sn; S.cur = [X, Y]; if (G.moved) { const u = vunit(vsub(o.b, o.a)); const np = vadd(old, vmul(u, vdot(vsub(sn.p, old), u))); const th = opTh(o), tn = vmul(opN(o), th); coincident(old, null, -1).forEach(c => c.set(cl(np))); if (th) coincident(vadd(old, tn), null, -1).forEach(c => c.set(vadd(np, tn))); o[w] = cl(np); } invalidate(); render(); return; }
  if (G.k === 'grip') { const { e, g } = G.gp; D = JSON.parse(G.base); const e2 = entById(e.id); const sn = snapAt(X, Y, { ex: new Set([e.id]), from: g.k === 'm' ? null : G.orig, dir: gripDir(e2, g) }); S.snap = sn; S.cur = [X, Y]; if (G.moved) applyGrip(e2, g, sn.p); invalidate(); render(); return; }
  if (G.k === 'mv') { if (!G.base0) { G.sb = snapAt(G.x0, G.y0, {}); G.base0 = G.sb.p; G.doc = JSON.stringify(D); G.h0 = hitEnt(G.x0, G.y0); }
    if (!G.moved) { S.snap = G.sb; S.cur = [X, Y]; render(); return; }
    if (!G.ids) { if (!S.sel.size && G.h0) S.sel.add(G.h0.e.id); G.ids = new Set(S.sel); if (!G.ids.size) { G.k = 'pan'; G.v0 = { ...view }; return; } }
    D = JSON.parse(G.doc); const sn = snapAt(X, Y, { ex: G.ids, from: G.base0 }); S.snap = sn; S.cur = [X, Y]; const dl = vsub(sn.p, G.base0);
    const sel = D.ents.filter(e => G.ids.has(e.id)), onSel = o => sel.some(e => [o.a, o.b].every(p => { const r = nearEnt(e, p); return r && r.d < CO; }));
    if (S.tool === 'move') { const mo = opsList().filter(onSel); sel.forEach(e => moveEnt(e, dl)); mo.forEach(o => { o.a = vadd(o.a, dl); o.b = vadd(o.b, dl); }); } else { G.copies = []; sel.forEach(e => { const c = JSON.parse(JSON.stringify(e)); moveEnt(c, dl); G.copies.push(c); }); G.opc = opsList().filter(onSel).map(o => ({ ...o, a: vadd(o.a, dl), b: vadd(o.b, dl) })); }
    S.preview = S.tool === 'copy' ? G.copies : null; invalidate(); render(); }
}
function acquire(sn) { if (!sn || !(sn.k === 'end' || sn.k === 'int' || sn.k === 'mid')) return; if (S.acq.some(p => vsame(p, sn.p))) return; S.acq.push(cl(sn.p)); if (S.acq.length > 2) S.acq.shift(); }
function moveEnt(e, d) { if (e.t === 'line') { e.a = vadd(e.a, d); e.b = vadd(e.b, d); } else if (e.t === 'pl') e.p = e.p.map(p => vadd(p, d)); else e.c = vadd(e.c, d); }
function drawSnapOpts() {
  const t = S.tool, o = {};
  if ((t === 'line' || t === 'pl') && S.chain) { const c = S.chain; o.from = c.pts[c.pts.length - 1]; o.dir = chainDir(); if (c.pts.length >= 2) o.extra = [c.pts[0]]; o.trkPts = c.pts.slice(0, -1); o.tbase = c.pts.length >= 2 ? vsub(c.pts[1], c.pts[0]) : c.dir0; }
  if (t === 'cir' && S.cir) { o.from = S.cir.c; }
  return o;
}
function pend(ev) {
  ptrs.delete(ev.pointerId); if (!ptrs.size) document.body.classList.remove('touching'); if (!G) return; if (G.k === 'pinch') { if (ptrs.size === 0) { G = null; save(); } return; }
  const X = ev.clientX, Y = ev.clientY, g = G; G = null; S.cur = null; S.preview = null;
  if (g.k === 'pan') { save(); render(); return; }
  if (g.k === 'none') return;
  if (g.k === 'grip') { if (g.moved) commit(); else { D = JSON.parse(g.base); render(); } S.snap = null; render(); return; }
  if (g.k === 'mv') { if (!g.moved) { const h = hitEnt(X, Y); if (h) { if (S.sel.has(h.e.id)) S.sel.delete(h.e.id); else S.sel.add(h.e.id); } else S.sel.clear(); S.snap = null; render(); return; }
    if (S.tool === 'copy' && g.copies) { D = JSON.parse(g.doc); g.copies.forEach(c => addEnt(c)); (g.opc || []).forEach(o => { o.id = 'o' + (D.nid++); opsList().push(o); }); } commit(); S.snap = null; render(); return; }
  if (g.k === 'place') { const sn = snapAt(X, Y, drawSnapOpts()); S.snap = null; if (OPEN.includes(S.tool)) { const oh = opHit(X, Y); if (!S.opA && oh && !g.moved) { if (oh.o.t === 'door' && S.tool === 'door') { opCycle(oh.o); commit(); } else { oh.o.t = S.tool; commit(); } return; } opPlace(sn, g.x0, g.y0); return; } placePoint(sn); return; }
  if (g.k === 'tap') { tapTool(X, Y); }
}
cv.addEventListener('pointerup', pend); cv.addEventListener('pointercancel', ev => { ptrs.delete(ev.pointerId); if (!ptrs.size) document.body.classList.remove('touching'); G = null; S.cur = null; render(); });
function placePoint(sn) {
  const t = S.tool, p = sn.p;
  if (t === 'line' || t === 'pl') { chainAdd(p, sn.P); ui(); return; }
  if (t === 'cir') { if (!S.cir) { S.cir = { c: cl(p) }; ui(); render(); return; } const r = vdist(p, S.cir.c); if (r > 1e-4) { addEnt({ t: 'cir', c: S.cir.c, r }); S.cir = null; commit(); ui(); } return; }
  if (t === 'arc') { if (!S.arc) { S.arc = { pts: [cl(p)] }; ui(); render(); return; } if (vsame(p, S.arc.pts[S.arc.pts.length - 1])) return; S.arc.pts.push(cl(p)); if (S.arc.pts.length === 3) { const a = arc3(...S.arc.pts); S.arc = null; if (a) { addEnt(a); commit(); } else render(); ui(); } else render(); }
}
function chainEnds(e) { if (e.t === 'line') return [e.a, e.b]; if (e.t === 'pl') return e.c ? e.p : [e.p[0], e.p[e.p.length - 1]]; if (e.t === 'arc') { const a = arcPts(e); return [a[0], a[2]]; } return []; }
let flashT; function flashOk(ids, dots) { S.flash = { ids: new Set(ids), dots }; clearTimeout(flashT); flashT = setTimeout(() => { S.flash = null; render(); }, 1000); render(); }
function flash() { cv.classList.remove('nope'); void cv.offsetWidth; cv.classList.add('nope'); }
function tapTool(X, Y) {
  const t = S.tool, h = hitEnt(X, Y), q = s2w(X, Y);
  if (t === 'sec') { const oh = opHit(X, Y); if (oh && (!h || oh.d <= h.d + 1e-9 || true)) { S.selOp = S.selOp === oh.o.id ? null : oh.o.id; S.sel.clear(); render(); ui(); return; } S.selOp = null; if (h) { if (S.sel.has(h.e.id)) S.sel.delete(h.e.id); else S.sel.add(h.e.id); } else S.sel.clear(); render(); ui(); return; }
  if (t === 'trim') { if (!h) return; const r = trimEnt(h.e, h.r.p, D.ents); if (!r) { flash(); return; } replEnt(h.e, r); commit(); return; }
  if (t === 'extend') { if (!h) return; const r = extendEnt(h.e, h.r.p, D.ents); if (!r) { flash(); return; } replEnt(h.e, [r]); commit(); return; }
  if (t === 'fillet') { if (!h) { S.pick = null; render(); return; } if (!S.pick) { S.pick = { id: h.e.id, q: h.r.p }; render(); return; } const e1 = entById(S.pick.id); const r = e1 && filletEnts(e1, S.pick.q, h.e, h.r.p); S.pick = null; if (!r) { flash(); render(); return; } const i1 = D.ents.indexOf(e1), i2 = D.ents.indexOf(h.e); r[0].id = e1.id; r[1].id = h.e.id; D.ents[i1] = r[0]; D.ents[i2] = r[1]; commit(); return; }
  if (t === 'offset') { if (!S.pick) { if (h) { S.pick = { id: h.e.id }; render(); } return; } const e = entById(S.pick.id); S.pick = null; const r = e && offsetEnt(e, S.offD, q); if (!r) { render(); return; } const pcs = S.autoCut ? offsetCut(r, e, S.offD, D.ents) : [r]; if (!pcs.length) { flash(); render(); return; } const ex = S.autoCut ? cutExisting(pcs, e, S.offD, D.ents) : []; const fl = []; ex.forEach(({ f, repl }) => { if (repl.length) { replEnt(f, repl); repl.forEach(x => fl.push(x.id)); } else delEnt(f); }); pcs.forEach(addEnt); commit(); if (pcs.length > 1 || pcs[0] !== r || ex.length) flashOk(pcs.map(x => x.id).concat(fl), true); return; }
  if (t === 'flat') { if (!h || h.e.t !== 'pl') { flash(); return; } if (flattenAt(h.e, h.r.p)) { commit(); flashOk([h.e.id], false); } else flash(); return; }
  if (t === 'erase') { const oh = opHit(X, Y); if (oh) { opDelete(oh.o); commit(); return; } if (h) { delEnt(h.e); commit(); } return; }
  if (t === 'explode') { if (h) { const r = explodeEnt(h.e); if (r) { replEnt(h.e, r); commit(); flashOk(r.map(x => x.id), true); } else flash(); } return; }
  if (t === 'join') {
    if (!h) { S.sel.clear(); render(); return; }
    if (S.sel.has(h.e.id)) { S.sel.delete(h.e.id); render(); return; }
    if (!S.sel.size) { const r = joinChain(h.e); if (r) { applyJoin(r); commit(); flashOk([r.ent.id], true); } else { S.sel.add(h.e.id); render(); } return; }
    const set = D.ents.filter(e => S.sel.has(e.id)).concat([h.e]); const r = joinEnts(set);
    if (r && r.used.includes(h.e)) { applyJoin(r); commit(); flashOk([r.ent.id], true); } else flash(); return;
  }
}
/* Düzleştir: girinti/çıkıntı (iki yanı aynı hizada) silinir; kademe (iki yanı paralel kayık) uzun duvarın hizasına çekilir */
function isOpPt(p) { return opsList().some(o => vsame(o.a, p) || vsame(o.b, p)); }
function runSegs(e, R) { const m = prims(e).length, out = []; let k = R.i0; for (let g = 0; g <= m; g++) { if (k % (e.c ? m : m + 1) === R.i1 % (e.c ? m : m + 1) && g) break; out.push(k % m); k++; if (!e.c && k > m) break; } return out; }
function plClean(e, near) {
  for (let i = e.p.length - 1; i > 0; i--) if (vsame(e.p[i], e.p[i - 1])) e.p.splice(i, 1);
  if (e.c) while (e.p.length > 1 && vsame(e.p[0], e.p[e.p.length - 1])) e.p.pop();
  near.forEach(q => { const k = e.p.length; for (let i = 0; i < k; i++) { if (!vsame(e.p[i], q) || isOpPt(q)) continue; if (!e.c && (i === 0 || i === k - 1)) break; const a = e.p[(i - 1 + k) % k], b = e.p[(i + 1) % k]; if (Math.abs(vcross(vunit(vsub(q, a)), vunit(vsub(b, q)))) < 1e-6 && vdot(vsub(q, a), vsub(b, q)) > 0 && k > (e.c ? 3 : 2)) e.p.splice(i, 1); break; } });
}
function flattenAt(e, q) {
  const runs = plRuns(e), m = runs.length; if (m < 3) return false; const n = e.p.length, seg = nearEnt(e, q).P.i;
  const r = runs.findIndex(R => runSegs(e, R).includes(seg)); if (r < 0) return false;
  const get = i => e.c ? runs[((i % m) + m) % m] : (i >= 0 && i < m ? runs[i] : null);
  const P0 = R => e.p[R.i0], P1 = R => e.p[R.i1 % n], dirOf = R => vunit(vsub(P1(R), P0(R))), lenOf = R => vdist(P0(R), P1(R));
  const tol = 26 / view.s, nearRun = k => { const R = get(k); return R && runSegs(e, R).some(i => nearPrim(prims(e)[i], q).d <= tol); };
  const WS = []; [[r, r], [r - 1, r + 1], [r, r + 2], [r - 2, r]].forEach(w => WS.push(w)); [-1, 1, -2, 2].forEach(c => [[r + c, r + c], [r + c - 1, r + c + 1]].forEach(w => WS.push(w)));
  for (const pass of [0, 1]) for (const [a, b] of WS) {
    const P = get(a - 1), N = get(b + 1); if (!P || !N || P === N || b - a + 3 > m) continue;
    let nr = false; for (let k = a; k <= b; k++) if (nearRun(k)) nr = true; if (!nr) continue;
    const dp = dirOf(P), dn = dirOf(N); if (Math.abs(vcross(dp, dn)) > 0.02 || vdot(dp, dn) <= 0) continue;
    const lim = Math.min(lenOf(P), lenOf(N)); let okW = true; for (let k = a; k <= b; k++) if (lenOf(get(k)) >= lim) okW = false; if (!okW) continue;
    const v1 = P1(P), v4 = P0(N), off = Math.abs(vcross(dp, vsub(v4, v1))); if (pass === 0 ? off >= 1e-4 : off < 1e-4) continue;
    /* pencere içindeki köşeler (P sonu → N başı) */
    const idx = []; let k = P.i1 % n; for (let g = 0; g <= n; g++) { idx.push(k); if (k === N.i0 % n) break; k = (k + 1) % n; }
    if (idx.some(i => isOpPt(e.p[i]))) return false;
    if (off < 1e-4) { const del = new Set(idx); e.p = e.p.filter((_, i) => !del.has(i)); plClean(e, []); return true; }
    const keepP = lenOf(P) >= lenOf(N), A = cl(v1), B = cl(v4);
    const del = new Set(idx.slice(1, -1)); e.p = e.p.filter((_, i) => !del.has(i));
    const R2 = plRuns(e), short = R2.find(R => vsame(keepP ? e.p[R.i0] : e.p[R.i1 % e.p.length], keepP ? B : A) && Math.abs(vcross(vunit(vsub(e.p[R.i1 % e.p.length], e.p[R.i0])), dp)) < 0.02);
    if (!short) return false;
    applyEdge(e, { k: 'm', run: short }, keepP ? A : B); plClean(e, [A, B]); return true;
  }
  return false;
}
function joinChain(e0) {
  const pool = D.ents.filter(e => !e.imp && (e.t === 'line' || (e.t === 'pl' && !e.c))); if (!pool.includes(e0)) return null;
  const ends = e => { const p = chainPts(e); return [p[0], p[p.length - 1]]; };
  const deg = p => pool.reduce((n, e) => n + ends(e).filter(q => vsame(q, p)).length, 0);
  const set = [e0]; let grew = true;
  while (grew) { grew = false; for (const e of set.slice()) for (const p of ends(e)) { if (deg(p) !== 2) continue; const f = pool.find(x => !set.includes(x) && ends(x).some(q => vsame(q, p))); if (f) { set.push(f); grew = true; } } }
  return joinEnts(set);
}
function applyJoin(r) { const i = Math.min(...r.used.map(e => D.ents.indexOf(e))); D.ents = D.ents.filter(e => !r.used.includes(e)); r.ent.id = 'e' + (D.nid++); D.ents.splice(i, 0, r.ent); S.sel = new Set([r.ent.id]); }

/* ---------- araç seçimi ---------- */
function setTool(t, quiet) {
  S.full = false; S.acq = []; S.chain = null; S.cir = null; S.arc = null; S.pick = null; S.sum = 0; S.sumH = [];
  if (DRAW.includes(t)) S.draw = t; if (EDIT.includes(t)) S.edit = t; if (OPEN.includes(t)) S.open = t; S.opA = null; if (t !== 'sec') S.selOp = null;
  if (!quiet && ['erase', 'explode', 'join'].includes(t) && S.sel.size) {
    const sel = D.ents.filter(e => S.sel.has(e.id)); let fl = [];
    if (t === 'erase') sel.forEach(delEnt);
    if (t === 'explode') sel.forEach(e => { const r = explodeEnt(e); if (r) { replEnt(e, r); fl = fl.concat(r.map(x => x.id)); } });
    if (t === 'join') { const r = joinEnts(sel); if (r) { applyJoin(r); fl = [r.ent.id]; } else flash(); }
    S.sel.clear(); commit(); t = 'sec'; if (fl.length) flashOk(fl, true);
  }
  if (t !== 'sec' && t !== 'move' && t !== 'copy') S.sel.clear();
  S.tool = t; S.fly = null; ui(); render(); save();
}

/* ---------- arayüz ---------- */
const col = document.getElementById('col'), fly = document.getElementById('fly'), qp = document.getElementById('qp'), np = document.getElementById('np');
function drawing() { return DRAW.includes(S.tool) && !!(S.chain || S.cir || S.arc); }
function btn(a, icon, on, extra) { return `<button class="b ${on ? 'on' : ''} ${extra || ''}" data-a="${a}">${svg(icon)}</button>`; }
function ui() {
  const t = S.tool, mini = drawing() && !S.full;
  col.className = mini ? 'mini' : ''; qp.className = mini ? 'mini' : '';
  if (mini) col.innerHTML = btn('full', 'menu') + btn('undo', 'undo') + btn('redo', 'redo') + btn('fit', 'fit'); else col.innerHTML = btn('undo', 'undo') + btn('redo', 'redo') + '<i></i>' + btn('sec', 'sel', t === 'sec') + btn('fly:draw', ICON[S.draw], DRAW.includes(t)) + btn('fly:edit', ICON[S.edit], EDIT.includes(t)) + btn('fly:open', ICON[S.open], OPEN.includes(t)) + '<i></i>' + btn('fly:snap', 'snap', false, S.fly === 'snap' ? 'open' : '') + '<i></i>' + btn('fit', 'fit') + btn('fly:file', 'folder', false, S.fly === 'file' ? 'open' : '') + btn('fly:set', 'gear', false, S.fly === 'set' ? 'open' : '') + `<div class="ver">${VER.replace('cad-', '')}</div>`;
  if (S.fly) {
    let h = ''; if (S.fly === 'draw') h = DRAW.map(k => btn('t:' + k, ICON[k], t === k)).join(''); if (S.fly === 'edit') h = EDIT.map(k => btn('t:' + k, ICON[k], t === k)).join(''); if (S.fly === 'set') { const v = S.setStr !== '' ? S.setStr : String(Math.round(S.thMax * 100)); h = `<div class="lab">${svg('wallth')}</div><div class="sum">${v}</div>` + ['7', '8', '9', '4', '5', '6', '1', '2', '3', '0'].map(k => `<button class="num k" data-a="sk:${k}">${k}</button>`).join('') + btn('skback', 'clr') + btn('skok', 'ok', false, 'okb') + btn('scut', 'offcut', S.autoCut, 'sn wide'); }
    if (S.fly === 'open') h = OPEN.map(k => btn('t:' + k, ICON[k], t === k)).join(''); if (S.fly === 'file') h = btn('exp', 'exp') + btn('imp', 'imp') + btn('new', 'newdoc', false, S.arm > Date.now() ? 'dng' : ''); if (S.fly === 'snap') h = SNAPK.map(([k, ic]) => btn('s:' + k, ic, S.snaps[k], 'sn')).join('');
    fly.innerHTML = h; fly.className = S.fly === 'set' ? 'g3' : ''; fly.style.display = S.fly === 'set' ? 'grid' : 'flex'; const b = col.querySelector(`[data-a="fly:${S.fly}"]`); const r = b.getBoundingClientRect(); fly.style.top = '0px'; const fh = fly.offsetHeight; fly.style.top = Math.max(8, Math.min(innerHeight - fh - 8, r.top - 6)) + 'px';
  } else fly.style.display = 'none';
  if (!S.fly && (t === 'line' || t === 'pl')) {
    const d = chainDir(), c = S.chain; let ar = [];
    if (c) { if (c.pts.length < 2 && !d) ar = ['up', 'down', 'left', 'right']; else { const v = d || [1, 0]; ar = Math.abs(v[0]) >= Math.abs(v[1]) ? ['up', 'down'] : ['left', 'right']; } }
    qp.innerHTML = `<div class="sum">${S.sum || 0}</div><button class="num" data-a="q:10">10</button><button class="num" data-a="q:50">50</button><button class="num" data-a="q:100">100</button>${btn('qback', 'clr')}` + ar.map(k => btn('qa:' + k, k, false, S.sum ? '' : 'dis')).join('') + (c ? btn('qok', 'ok', false, 'okb') : '');
    qp.style.display = 'grid';
  } else qp.style.display = 'none';
  const opp = document.getElementById('opp'), oh = opPanel(); opp.innerHTML = oh; opp.style.display = oh ? 'grid' : 'none';
  if (!S.fly && t === 'offset') { const v = S.offStr !== '' ? S.offStr : String(Math.round(S.offD * 1000) / 10);
    if (!S.npOpen) { np.innerHTML = `<button class="num chip" data-a="kopen">${v}</button>`; np.className = 'mini'; }
    else { np.className = ''; np.innerHTML = `<div class="sum">${v}</div>` + ['7', '8', '9', '4', '5', '6', '1', '2', '3', '.', '0'].map(k => `<button class="num k" data-a="k:${k}">${k}</button>`).join('') + btn('kback', 'clr') + `<button class="b okb kok" data-a="kok">${svg('ok')}</button>`; }
    np.style.display = 'grid'; }
  else np.style.display = 'none';
}
function onBtn(a) {
  if (a === 'undo') { undo(); ui(); return; } if (a === 'redo') { redo(); ui(); return; }
  if (a === 'full') { S.full = true; ui(); return; }
  if (a.startsWith('sk:')) { S.setStr = (S.setStr + a.slice(3)).slice(0, 3); ui(); return; }
  if (a === 'scut') { S.autoCut = S.autoCut ? 0 : 1; save(); ui(); return; }
  if (a === 'skback') { S.setStr = S.setStr.slice(0, -1); ui(); return; }
  if (a === 'skok') { const v = parseInt(S.setStr, 10); if (v >= 5 && v <= 300) S.thMax = v / 100; S.setStr = ''; S.fly = null; save(); invalidate(); ui(); render(); return; }
  if (a === 'exp') { S.fly = null; ui(); exportDXF(); return; }
  if (a === 'imp') { S.fly = null; ui(); document.getElementById('fileIn').click(); return; }
  if (a === 'new') { if (S.arm > Date.now()) { S.arm = 0; D = { ents: [], nid: 1, ops: [] }; S.sel.clear(); S.selOp = null; S.fly = null; commit(); fit(); ui(); } else { S.arm = Date.now() + 3000; ui(); setTimeout(ui, 3100); } return; }
  if (a === 'oph' || a === 'ops' || a === 'opt' || a === 'opdel' || a === 'opw') { const o = opById(S.selOp); if (!o) return; if (a === 'opw') opWall(o); if (a === 'oph') o.hinge = o.hinge ? 0 : 1; if (a === 'ops') o.sw = -o.sw; if (a === 'opt') o.t = o.t === 'door' ? 'win' : 'door'; if (a === 'opdel') { opDelete(o); S.selOp = null; } commit(); ui(); return; }
  if (a === 'sec') { setTool('sec'); return; } if (a === 'fit') { fit(); return; }
  if (a.startsWith('fly:')) { const f = a.slice(4); S.setStr = ''; if (S.fly === f) { S.fly = null; ui(); return; }
    if (f === 'draw' && S.tool !== S.draw) setTool(S.draw, true); if (f === 'edit' && S.tool !== S.edit) setTool(S.edit, true); if (f === 'open' && S.tool !== S.open) setTool(S.open, true);
    S.fly = f; ui(); render(); return; }
  if (a.startsWith('t:')) { setTool(a.slice(2)); return; }
  if (a.startsWith('s:')) { const k = a.slice(2); S.snaps[k] = S.snaps[k] ? 0 : 1; save(); ui(); return; }
  if (a.startsWith('q:')) { const v = +a.slice(2); S.sum += v; S.sumH.push(v); ui(); return; }
  if (a === 'qback') { const v = S.sumH.pop(); if (v) S.sum -= v; ui(); return; }
  if (a.startsWith('qa:')) { const k = a.slice(3); quickArrow(...{ up: [0, 1], down: [0, -1], left: [-1, 0], right: [1, 0] }[k]); return; }
  if (a === 'qok') { endChain(); ui(); return; }
  if (a.startsWith('k:')) { let s = S.offStr; const k = a.slice(2); if (k === '.' && s.includes('.')) return; s += k; S.offStr = s; const v = parseFloat(s); if (v > 0) S.offD = v / 100; save(); ui(); return; }
  if (a === 'kopen') { S.npOpen = true; S.offStr = ''; ui(); return; }
  if (a === 'kok') { S.npOpen = false; S.offStr = ''; ui(); return; }
  if (a === 'kback') { S.offStr = S.offStr.slice(0, -1); const v = parseFloat(S.offStr); if (v > 0) S.offD = v / 100; ui(); return; }
}
let BP = null;
document.addEventListener('pointerdown', ev => { const b = ev.target.closest('button[data-a]'); BP = b ? { b, x: ev.clientX, y: ev.clientY } : null; }, true);
document.addEventListener('pointerup', ev => { const p = BP; BP = null; if (!p) return; const b = ev.target.closest('button[data-a]'); if (b !== p.b || Math.hypot(ev.clientX - p.x, ev.clientY - p.y) > 12) return; ev.preventDefault(); onBtn(b.dataset.a); }, true);
document.addEventListener('pointercancel', () => { BP = null; }, true);

/* ---------- çizim ---------- */
function pathEnt(e) {
  cx.beginPath();
  if (e.t === 'line') { const a = w2s(...e.a), b = w2s(...e.b); cx.moveTo(...a); cx.lineTo(...b); }
  else if (e.t === 'pl') { e.p.forEach((p, i) => { const s = w2s(...p); if (i) cx.lineTo(...s); else cx.moveTo(...s); }); if (e.c) cx.closePath(); }
  else if (e.t === 'cir') { const c = w2s(...e.c); cx.arc(c[0], c[1], e.r * view.s, 0, TAU); }
  else if (e.t === 'arc') { const c = w2s(...e.c); cx.arc(c[0], c[1], e.r * view.s, -e.a0, -(e.a0 + arcSw(e)), true); }
}
function render() {
  if (!W) return; cx.setTransform(DPR, 0, 0, DPR, 0, 0); cx.fillStyle = '#121417'; cx.fillRect(0, 0, W, H);
  if (!CACHE.faces) CACHE.faces = faces(D.ents.filter(e => !e.imp));
  cx.fillStyle = 'rgba(90,160,255,0.09)'; CACHE.faces.forEach(f => { cx.beginPath(); f.forEach((p, i) => { const s = w2s(...p); if (i) cx.lineTo(...s); else cx.moveTo(...s); }); cx.closePath(); cx.fill(); });
  cx.lineWidth = 1.6; cx.lineJoin = 'round'; cx.lineCap = 'round';
  D.ents.forEach(e => { const sel = S.sel.has(e.id), pk = S.pick && S.pick.id === e.id; cx.strokeStyle = pk ? '#f5a623' : sel ? '#6fb0ff' : e.imp ? '#6b7480' : '#e8e8e8'; if (e.t === 'pt') { const s = w2s(...e.p); cx.lineWidth = 1.2; cx.beginPath(); cx.moveTo(s[0] - 4, s[1] - 4); cx.lineTo(s[0] + 4, s[1] + 4); cx.moveTo(s[0] + 4, s[1] - 4); cx.lineTo(s[0] - 4, s[1] + 4); cx.stroke(); return; } cx.lineWidth = sel || pk ? 2.6 : 1.6; cx.setLineDash(sel ? [8, 5] : []); pathEnt(e); cx.stroke(); });
  cx.setLineDash([]);
  drawOps();
  if (S.flash) { const cols = ['#4cd964', '#ffcf70']; let k = 0; S.flash.ids.forEach(id => { const e = entById(id); if (!e) return; cx.strokeStyle = cols[(k++) % 2]; cx.lineWidth = 4; pathEnt(e); cx.stroke(); if (S.flash.dots) chainEnds(e).forEach(p => { const s = w2s(...p); cx.fillStyle = '#fff'; cx.beginPath(); cx.arc(s[0], s[1], 4.5, 0, TAU); cx.fill(); }); }); }
  if (S.preview) { cx.strokeStyle = '#4cd964'; cx.lineWidth = 1.6; S.preview.forEach(e => { pathEnt(e); cx.stroke(); }); }
  /* tutamaklar */
  if (S.tool === 'sec') S.sel.forEach(id => { const e = entById(id); if (!e) return; gripsOf(e).forEach(g => { const s = w2s(...g.p); cx.fillStyle = g.k === 'm' ? '#f5a623' : '#2b6fd6'; cx.strokeStyle = '#fff'; cx.lineWidth = 1.2; cx.fillRect(s[0] - 6, s[1] - 6, 12, 12); cx.strokeRect(s[0] - 6, s[1] - 6, 12, 12); }); });
  /* lastik bant */
  const sn = S.snap, cur = S.cur && G && (G.k === 'place') ? sn : null;
  if (cur) {
    cx.strokeStyle = '#4cd964'; cx.lineWidth = 1.6; cx.setLineDash([6, 4]); const p = w2s(...cur.p);
    if ((S.tool === 'line' || S.tool === 'pl') && S.chain) { const a = w2s(...S.chain.pts[S.chain.pts.length - 1]); cx.beginPath(); cx.moveTo(...a); cx.lineTo(...p); cx.stroke(); lenLabel(S.chain.pts[S.chain.pts.length - 1], cur.p); }
    if (S.tool === 'cir' && S.cir) { const c = w2s(...S.cir.c); cx.beginPath(); cx.arc(c[0], c[1], vdist(cur.p, S.cir.c) * view.s, 0, TAU); cx.stroke(); lenLabel(S.cir.c, cur.p); }
    if (S.tool === 'arc' && S.arc) { if (S.arc.pts.length === 2) { const a = arc3(S.arc.pts[0], S.arc.pts[1], cur.p); if (a) { pathEnt(a); cx.stroke(); } } else { const a = w2s(...S.arc.pts[0]); cx.beginPath(); cx.moveTo(...a); cx.lineTo(...p); cx.stroke(); } }
    cx.setLineDash([]);
  }
  if (S.chain && S.chain.pts.length && S.tool === 'line') { const a = w2s(...S.chain.pts[S.chain.pts.length - 1]); cx.strokeStyle = '#4cd964'; cx.beginPath(); cx.arc(a[0], a[1], 5, 0, TAU); cx.stroke(); }
  if (S.chain && S.tool === 'pl') { const a = w2s(...S.chain.pts[S.chain.pts.length - 1]); cx.strokeStyle = '#4cd964'; cx.beginPath(); cx.arc(a[0], a[1], 5, 0, TAU); cx.stroke(); }
  if (S.cir) { const a = w2s(...S.cir.c); cx.fillStyle = '#4cd964'; cx.fillRect(a[0] - 3, a[1] - 3, 6, 6); }
  if (S.arc) S.arc.pts.forEach(p => { const a = w2s(...p); cx.fillStyle = '#4cd964'; cx.fillRect(a[0] - 3, a[1] - 3, 6, 6); });
  /* yakalama işareti + kılavuzlar */
  if (sn && S.cur) {
    (sn.g || []).forEach(g => { if (!g) return; cx.strokeStyle = 'rgba(255,207,112,.8)'; cx.lineWidth = 1; cx.setLineDash([4, 4]); cx.beginPath(); cx.moveTo(...w2s(...g[0])); cx.lineTo(...w2s(...g[1])); cx.stroke(); }); cx.setLineDash([]);
    const p = w2s(...sn.p); cx.strokeStyle = '#7dffb0'; cx.lineWidth = 2; cx.beginPath();
    if (sn.k === 'end') cx.rect(p[0] - 7, p[1] - 7, 14, 14); else if (sn.k === 'mid') { cx.moveTo(p[0], p[1] - 8); cx.lineTo(p[0] + 8, p[1] + 6); cx.lineTo(p[0] - 8, p[1] + 6); cx.closePath(); }
    else if (sn.k === 'int') { cx.moveTo(p[0] - 7, p[1] - 7); cx.lineTo(p[0] + 7, p[1] + 7); cx.moveTo(p[0] + 7, p[1] - 7); cx.lineTo(p[0] - 7, p[1] + 7); }
    else if (sn.k === 'near') { cx.moveTo(p[0] - 7, p[1] - 7); cx.lineTo(p[0] + 7, p[1] - 7); cx.lineTo(p[0] - 7, p[1] + 7); cx.lineTo(p[0] + 7, p[1] + 7); cx.closePath(); }
    else if (sn.k === 'trk') { cx.arc(p[0], p[1], 5, 0, TAU); } else { cx.moveTo(p[0] - 9, p[1]); cx.lineTo(p[0] + 9, p[1]); cx.moveTo(p[0], p[1] - 9); cx.lineTo(p[0], p[1] + 9); }
    cx.stroke();
    loupe(p);
  }
}
function lenLabel(a, b) { const d = vdist(a, b); if (d < 1e-3) return; const m = w2s(...vmul(vadd(a, b), 0.5)); cx.font = 'bold 14px Arial'; cx.fillStyle = '#ffcf70'; cx.fillText(d.toFixed(2), m[0] + 8, m[1] - 8); }
function loupe(p) {
  const R = 52, Z = 2, x = Math.min(W - 90 - R, Math.max(R + 6, p[0])), y = p[1] - 120 < R + 6 ? p[1] + 120 : p[1] - 120;
  cx.save(); cx.beginPath(); cx.arc(x, y, R, 0, TAU); cx.clip(); cx.fillStyle = '#121417'; cx.fillRect(x - R, y - R, 2 * R, 2 * R);
  cx.setTransform(1, 0, 0, 1, 0, 0); const sw = R * 2 / Z * DPR; cx.drawImage(cv, p[0] * DPR - sw / 2, p[1] * DPR - sw / 2, sw, sw, (x - R) * DPR, (y - R) * DPR, 2 * R * DPR, 2 * R * DPR);
  cx.restore(); cx.setTransform(DPR, 0, 0, DPR, 0, 0); cx.strokeStyle = '#7dffb0'; cx.lineWidth = 1.5; cx.beginPath(); cx.arc(x, y, R, 0, TAU); cx.stroke(); cx.strokeStyle = 'rgba(125,255,176,.6)'; cx.lineWidth = 1; cx.beginPath(); cx.moveTo(x - 8, y); cx.lineTo(x + 8, y); cx.moveTo(x, y - 8); cx.lineTo(x, y + 8); cx.stroke();
}

window.CAD = { get D() { return D; }, set D(v) { D = v; D.ops = D.ops || []; invalidate(); }, makeDXF, importDXF, parseDXF, pointNames, S, get view() { return view; }, w2s, s2w, commit, setTool, render, ui, fit, undo, redo };
addEventListener('resize', resize);
document.getElementById('fileIn').addEventListener('change', async ev => { const f = ev.target.files[0]; if (!f) return; try { importDXF(await f.text()); } catch (er) { flash(); } ev.target.value = ''; });
load(); ui(); resize();
if ('serviceWorker' in navigator && location.protocol === 'https:') navigator.serviceWorker.register('sw.js').catch(() => {});
