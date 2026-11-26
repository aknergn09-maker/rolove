/* ROLEVE CAD — geometri çekirdeği (DOM yok). Birimler metre, y yukarı. */
const TAU = Math.PI * 2, GE = 1e-9, CO = 1e-4;
const vsub = (a, b) => [a[0] - b[0], a[1] - b[1]], vadd = (a, b) => [a[0] + b[0], a[1] + b[1]], vmul = (a, k) => [a[0] * k, a[1] * k];
const vdot = (a, b) => a[0] * b[0] + a[1] * b[1], vcross = (a, b) => a[0] * b[1] - a[1] * b[0];
const vlen = a => Math.hypot(a[0], a[1]), vdist = (a, b) => Math.hypot(a[0] - b[0], a[1] - b[1]);
const vunit = a => { const l = vlen(a) || 1; return [a[0] / l, a[1] / l]; }, vperp = a => [-a[1], a[0]];
const vang = a => Math.atan2(a[1], a[0]), nrm = a => ((a % TAU) + TAU) % TAU, vsame = (a, b) => vdist(a, b) < CO;
const cl = p => [p[0], p[1]];

function prims(e) {
  if (e.t === 'line') return [{ k: 's', a: e.a, b: e.b, s0: 0, i: 0, e }];
  if (e.t === 'pl') {
    const out = [], n = e.p.length, m = e.c ? n : n - 1; let s = 0;
    for (let i = 0; i < m; i++) { const a = e.p[i], b = e.p[(i + 1) % n]; out.push({ k: 's', a, b, s0: s, i, e }); s += vdist(a, b); }
    return out;
  }
  if (e.t === 'cir') return [{ k: 'c', c: e.c, r: e.r, a0: 0, sw: TAU, e }];
  if (e.t === 'arc') return [{ k: 'c', c: e.c, r: e.r, a0: e.a0, sw: arcSw(e), e }];
  return [];
}
function arcSw(e) { const s = nrm(e.a1 - e.a0); return s < 1e-9 ? TAU : s; }
function entU(e) { if (e.t === 'cir') return TAU; if (e.t === 'arc') return arcSw(e); return prims(e).reduce((s, p) => s + vdist(p.a, p.b), 0); }
function periodic(e) { return e.t === 'cir' || (e.t === 'pl' && e.c); }
function inSweep(P, pt) { return P.sw >= TAU - 1e-9 || nrm(vang(vsub(pt, P.c)) - P.a0) <= P.sw + 1e-7; }
function uOf(P, pt) { return P.k === 's' ? P.s0 + vdist(P.a, pt) : nrm(vang(vsub(pt, P.c)) - P.a0) + (P.e.t === 'cir' ? 0 : 0); }
function ptAt(e, u) {
  if (e.t === 'cir' || e.t === 'arc') { const a0 = e.t === 'cir' ? 0 : e.a0; return [e.c[0] + e.r * Math.cos(a0 + u), e.c[1] + e.r * Math.sin(a0 + u)]; }
  const ps = prims(e); for (const P of ps) { const L = vdist(P.a, P.b); if (u <= P.s0 + L + GE || P === ps[ps.length - 1]) { const t = L ? Math.min(1, Math.max(0, (u - P.s0) / L)) : 0; return vadd(P.a, vmul(vsub(P.b, P.a), t)); } }
  return cl(ps[0].a);
}
function nearPrim(P, q) {
  if (P.k === 's') { const d = vsub(P.b, P.a), l2 = vdot(d, d) || 1; const t = Math.max(0, Math.min(1, vdot(vsub(q, P.a), d) / l2)); const p = vadd(P.a, vmul(d, t)); return { p, d: vdist(p, q), t }; }
  const a = vang(vsub(q, P.c)); let p;
  if (P.sw >= TAU - 1e-9 || nrm(a - P.a0) <= P.sw) p = vadd(P.c, [P.r * Math.cos(a), P.r * Math.sin(a)]);
  else { const p1 = vadd(P.c, [P.r * Math.cos(P.a0), P.r * Math.sin(P.a0)]), p2 = vadd(P.c, [P.r * Math.cos(P.a0 + P.sw), P.r * Math.sin(P.a0 + P.sw)]); p = vdist(p1, q) < vdist(p2, q) ? p1 : p2; }
  return { p, d: vdist(p, q) };
}
function nearEnt(e, q) { let best = null; prims(e).forEach(P => { const r = nearPrim(P, q); if (!best || r.d < best.d) best = { ...r, P }; }); if (best) best.u = uOf(best.P, best.p); return best; }

/* kesişimler */
function segSeg(a, b, c, d, inf) {
  const r = vsub(b, a), s = vsub(d, c), den = vcross(r, s); if (Math.abs(den) < 1e-12) return [];
  const t = vcross(vsub(c, a), s) / den, u = vcross(vsub(c, a), r) / den;
  if (!inf && (t < -1e-9 || t > 1 + 1e-9 || u < -1e-9 || u > 1 + 1e-9)) return [];
  return [{ p: vadd(a, vmul(r, t)), t, u }];
}
function lineCirc(a, b, c, r) {
  const d = vsub(b, a), f = vsub(a, c), A = vdot(d, d), B = 2 * vdot(f, d), C = vdot(f, f) - r * r; const D = B * B - 4 * A * C; if (D < 0 || A < 1e-18) return [];
  const sq = Math.sqrt(D), ts = D < 1e-14 ? [-B / (2 * A)] : [(-B - sq) / (2 * A), (-B + sq) / (2 * A)]; return ts.map(t => ({ t, p: vadd(a, vmul(d, t)) }));
}
function circCirc(c1, r1, c2, r2) {
  const d = vdist(c1, c2); if (d < 1e-12 || d > r1 + r2 + 1e-9 || d < Math.abs(r1 - r2) - 1e-9) return [];
  const a = (r1 * r1 - r2 * r2 + d * d) / (2 * d), h = Math.sqrt(Math.max(0, r1 * r1 - a * a)); const m = vadd(c1, vmul(vsub(c2, c1), a / d)); const n = vperp(vunit(vsub(c2, c1)));
  return h < 1e-9 ? [{ p: m }] : [{ p: vadd(m, vmul(n, h)) }, { p: vsub(m, vmul(n, h)) }];
}
function primInts(P, Q) {
  if (P.k === 's' && Q.k === 's') return segSeg(P.a, P.b, Q.a, Q.b).map(x => x.p);
  if (P.k === 's') return lineCirc(P.a, P.b, Q.c, Q.r).filter(x => x.t >= -1e-9 && x.t <= 1 + 1e-9 && inSweep(Q, x.p)).map(x => x.p);
  if (Q.k === 's') return primInts(Q, P);
  return circCirc(P.c, P.r, Q.c, Q.r).filter(x => inSweep(P, x.p) && inSweep(Q, x.p)).map(x => x.p);
}
function cutsOn(e, ents) {
  const us = [], ps = prims(e);
  ents.forEach(f => { if (f === e) return; const qs = prims(f); ps.forEach(P => qs.forEach(Q => primInts(P, Q).forEach(pt => us.push(uOf(P, pt))))); });
  return uniqSort(us);
}
function uniqSort(us) { us.sort((a, b) => a - b); const o = []; us.forEach(u => { if (!o.length || u - o[o.length - 1] > 1e-7) o.push(u); }); return o; }

/* alt parça (u1→u2, periyodikte sarmalı) */
function subEnt(e, u1, u2) {
  if (e.t === 'line') return { t: 'line', a: ptAt(e, u1), b: ptAt(e, u2) };
  if (e.t === 'cir' || e.t === 'arc') { const a0 = e.t === 'cir' ? 0 : e.a0; return { t: 'arc', c: cl(e.c), r: e.r, a0: nrm(a0 + u1), a1: nrm(a0 + u2) }; }
  const U = entU(e); if (u2 < u1) u2 += U;
  const ps = prims(e), pts = [ptAt(e, u1 % U)];
  const vs = []; ps.forEach(P => vs.push(P.s0 + vdist(P.a, P.b)));
  for (let lap = 0; lap < 2; lap++) ps.forEach((P, i) => { const s = vs[i] + lap * U; if (s > u1 + 1e-9 && s < u2 - 1e-9) pts.push(cl(P.b)); });
  pts.push(ptAt(e, u2 > U + 1e-12 ? u2 - U : u2));
  return { t: 'pl', p: pts, c: false };
}
function trimEnt(e, q, ents) {
  const cuts = cutsOn(e, ents), U = entU(e), u0 = nearEnt(e, q).u;
  if (periodic(e)) {
    if (cuts.length < 2) return null;
    let i = cuts.findIndex(u => u > u0); if (i < 0) i = 0; const hi = cuts[i], lo = cuts[(i - 1 + cuts.length) % cuts.length];
    return [subEnt(e, hi, lo)];
  }
  const inner = cuts.filter(u => u > 1e-7 && u < U - 1e-7); if (!inner.length) return null;
  const lo = Math.max(0, ...inner.filter(u => u < u0)), hi = Math.min(U, ...inner.filter(u => u > u0));
  const out = []; if (lo > 1e-7) out.push(subEnt(e, 0, lo)); if (hi < U - 1e-7) out.push(subEnt(e, hi, U));
  if (e.t === 'arc' && !out.length) return null;
  return out;
}
function rayHit(o, d, ents, skip) { /* o'dan d yönünde ilk kesişim (t>0) */
  let best = null; const far = vadd(o, d);
  ents.forEach(f => { if (f === skip) return; prims(f).forEach(Q => {
    let hs = [];
    if (Q.k === 's') hs = segSeg(o, far, Q.a, Q.b, true).filter(x => x.u >= -1e-9 && x.u <= 1 + 1e-9).map(x => ({ t: x.t, p: x.p }));
    else hs = lineCirc(o, far, Q.c, Q.r).filter(x => inSweep(Q, x.p));
    hs.forEach(h => { if (h.t > 1e-7 && (!best || h.t < best.t)) best = h; });
  }); });
  return best;
}
function extendEnt(e, q, ents) {
  if (e.t === 'line' || (e.t === 'pl' && !e.c)) {
    const pts = e.t === 'line' ? [e.a, e.b] : e.p, u0 = nearEnt(e, q).u, U = entU(e), atEnd = u0 > U / 2;
    const n = pts.length, end = atEnd ? pts[n - 1] : pts[0], prev = atEnd ? pts[n - 2] : pts[1];
    const h = rayHit(end, vunit(vsub(end, prev)), ents, e); if (!h) return null;
    const ne = JSON.parse(JSON.stringify(e)); const np = cl(h.p);
    if (e.t === 'line') { if (atEnd) ne.b = np; else ne.a = np; } else { if (atEnd) ne.p[n - 1] = np; else ne.p[0] = np; }
    return ne;
  }
  if (e.t === 'arc') {
    const sw = arcSw(e), u0 = nearEnt(e, q).u, atEnd = u0 > sw / 2; let best = null;
    const C = { k: 'c', c: e.c, r: e.r, a0: 0, sw: TAU };
    ents.forEach(f => { if (f === e) return; prims(f).forEach(Q => primInts(C, Q).forEach(pt => { const th = vang(vsub(pt, e.c)); const dd = atEnd ? nrm(th - e.a1) : nrm(e.a0 - th); if (dd > 1e-7 && dd < TAU - sw - 1e-7 && (best === null || dd < best)) best = dd; })); });
    if (best === null) return null; const ne = JSON.parse(JSON.stringify(e)); if (atEnd) ne.a1 = nrm(e.a1 + best); else ne.a0 = nrm(e.a0 - best); return ne;
  }
  return null;
}
/* fillet r=0: iki çizgiyi kesişimde birleştir */
function filletEnts(e1, q1, e2, q2) {
  const s1 = nearEnt(e1, q1), s2 = nearEnt(e2, q2); if (!s1 || !s2 || s1.P.k !== 's' || s2.P.k !== 's') return null;
  const X = segSeg(s1.P.a, s1.P.b, s2.P.a, s2.P.b, true)[0]; if (!X) return null;
  const fix = (e, s, tx) => {
    const P = s.P, d = vsub(P.b, P.a), tp = vdot(vsub(s.p, P.a), d) / (vdot(d, d) || 1); const ne = JSON.parse(JSON.stringify(e)); const x = cl(X.p);
    if (e.t === 'line') { if (tx > tp) ne.b = x; else ne.a = x; return ne; }
    if (e.c) return null; const i = P.i, n = e.p.length;
    if (tx > tp) { ne.p = ne.p.slice(0, i + 1).concat([x]); } else { ne.p = [x].concat(ne.p.slice(i + 1)); }
    void n; return ne;
  };
  const d1 = vsub(s1.P.b, s1.P.a), d2 = vsub(s2.P.b, s2.P.a);
  const tx1 = vdot(vsub(X.p, s1.P.a), d1) / vdot(d1, d1), tx2 = vdot(vsub(X.p, s2.P.a), d2) / vdot(d2, d2);
  if (e1 === e2) return null;
  const n1 = fix(e1, s1, tx1), n2 = fix(e2, s2, tx2); if (!n1 || !n2) return null; return [n1, n2];
}
/* offset */
function offsetEnt(e, dist, q) {
  if (e.t === 'line') { const n = vunit(vperp(vsub(e.b, e.a))), sg = vcross(vsub(e.b, e.a), vsub(q, e.a)) > 0 ? 1 : -1; const o = vmul(n, dist * sg); return { t: 'line', a: vadd(e.a, o), b: vadd(e.b, o) }; }
  if (e.t === 'cir' || e.t === 'arc') { const r = vdist(q, e.c) > e.r ? e.r + dist : e.r - dist; if (r <= 1e-6) return null; const ne = JSON.parse(JSON.stringify(e)); ne.r = r; return ne; }
  if (e.t === 'pl') {
    const s = nearEnt(e, q), P = s.P, sg = vcross(vsub(P.b, P.a), vsub(q, P.a)) > 0 ? 1 : -1, ps = prims(e), n = e.p.length;
    const L = ps.map(P => { const nn = vmul(vunit(vperp(vsub(P.b, P.a))), dist * sg); return { a: vadd(P.a, nn), b: vadd(P.b, nn), nn }; });
    const pts = e.p.map((p, i) => {
      const before = e.c ? L[(i - 1 + L.length) % L.length] : (i > 0 ? L[i - 1] : null), after = e.c ? L[i % L.length] : (i < L.length ? L[i] : null);
      if (!before) return after.a; if (!after) return before.b;
      const X = segSeg(before.a, before.b, after.a, after.b, true)[0]; return X ? X.p : after.a;
    });
    void n; return { t: 'pl', p: pts, c: e.c };
  }
  return null;
}
/* üç noktadan yay */
function arc3(p1, p2, p3) {
  const ax = p1[0], ay = p1[1], bx = p2[0], by = p2[1], cx = p3[0], cy = p3[1]; const d = 2 * (ax * (by - cy) + bx * (cy - ay) + cx * (ay - by)); if (Math.abs(d) < 1e-12) return null;
  const ux = ((ax * ax + ay * ay) * (by - cy) + (bx * bx + by * by) * (cy - ay) + (cx * cx + cy * cy) * (ay - by)) / d, uy = ((ax * ax + ay * ay) * (cx - bx) + (bx * bx + by * by) * (ax - cx) + (cx * cx + cy * cy) * (bx - ax)) / d;
  const c = [ux, uy], r = vdist(c, p1), ccw = vcross(vsub(p2, p1), vsub(p3, p2)) > 0;
  return ccw ? { t: 'arc', c, r, a0: nrm(vang(vsub(p1, c))), a1: nrm(vang(vsub(p3, c))) } : { t: 'arc', c, r, a0: nrm(vang(vsub(p3, c))), a1: nrm(vang(vsub(p1, c))) };
}
function arcPts(e) { const sw = arcSw(e); return [ptAt(e, 0), ptAt(e, sw / 2), ptAt(e, sw)]; }
/* join: uç uca değen çizgi/açık pline'ları birleştir */
function chainPts(e) { return e.t === 'line' ? [cl(e.a), cl(e.b)] : e.p.map(cl); }
function joinEnts(list) {
  const pool = list.filter(e => e.t === 'line' || (e.t === 'pl' && !e.c)); if (pool.length < 2) return null;
  let pts = chainPts(pool[0]); const used = new Set([pool[0]]); let grew = true;
  while (grew) { grew = false; for (const f of pool) { if (used.has(f)) continue; const q = chainPts(f), A = pts[0], B = pts[pts.length - 1];
    if (vsame(B, q[0])) pts = pts.concat(q.slice(1)); else if (vsame(B, q[q.length - 1])) pts = pts.concat(q.reverse().slice(1));
    else if (vsame(A, q[q.length - 1])) pts = q.concat(pts.slice(1)); else if (vsame(A, q[0])) pts = q.reverse().concat(pts.slice(1)); else continue;
    used.add(f); grew = true; } }
  if (used.size < 2) return null; let c = false; if (pts.length > 3 && vsame(pts[0], pts[pts.length - 1])) { pts.pop(); c = true; }
  return { ent: { t: 'pl', p: pts, c }, used: [...used] };
}
function explodeEnt(e) { if (e.t !== 'pl') return null; return prims(e).map(P => ({ t: 'line', a: cl(P.a), b: cl(P.b) })); }
/* aynı doğrultudaki ardışık pline parçaları = tek kenar */
function plRuns(e) {
  const ps = prims(e), m = ps.length, col = (i, j) => { const a = vunit(vsub(ps[i].b, ps[i].a)), b = vunit(vsub(ps[j].b, ps[j].a)); return Math.abs(vcross(a, b)) < 1e-6 && vdot(a, b) > 0; };
  let start = 0; if (e.c && m > 1) { let k = 0; while (k < m && col((start - 1 + m) % m, start)) { start = (start + 1) % m; k++; } if (k >= m) start = 0; }
  const runs = []; let cur = null;
  for (let k = 0; k < m; k++) { const i = (start + k) % m; if (cur && col(cur.j, i)) cur.j = i; else { if (cur) runs.push(cur); cur = { i, j: i }; } }
  if (cur) runs.push(cur);
  return runs.map(r => ({ i0: r.i, i1: (r.j + 1) % (e.c ? m : m + 1) }));
}
/* kapalı alanlar: tüm doğru parçalarının düzlem grafı */
function faces(ents) {
  const segs = []; ents.forEach(e => prims(e).forEach(P => { if (P.k === 's') { if (vdist(P.a, P.b) > 1e-9) segs.push(P); return; }
    const n = Math.max(6, Math.ceil(P.sw / (TAU / 64))); let prev = vadd(P.c, [P.r * Math.cos(P.a0), P.r * Math.sin(P.a0)]);
    for (let k = 1; k <= n; k++) { const a = P.a0 + P.sw * k / n, q = vadd(P.c, [P.r * Math.cos(a), P.r * Math.sin(a)]); segs.push({ k: 's', a: prev, b: q }); prev = q; } }));
  const ts = segs.map(() => [0, 1]);
  for (let i = 0; i < segs.length; i++) for (let j = i + 1; j < segs.length; j++) { const x = segSeg(segs[i].a, segs[i].b, segs[j].a, segs[j].b)[0]; if (x) { ts[i].push(x.t); ts[j].push(x.u); } }
  const key = p => Math.round(p[0] * 1e4) + ',' + Math.round(p[1] * 1e4); const nodes = new Map(), adj = new Map(), E = new Set();
  const node = p => { const k = key(p); if (!nodes.has(k)) { nodes.set(k, p); adj.set(k, new Set()); } return k; };
  segs.forEach((P, i) => { const t = uniqSort(ts[i].map(v => Math.max(0, Math.min(1, v)))); for (let k = 0; k + 1 < t.length; k++) { const a = node(vadd(P.a, vmul(vsub(P.b, P.a), t[k]))), b = node(vadd(P.a, vmul(vsub(P.b, P.a), t[k + 1]))); if (a !== b) { adj.get(a).add(b); adj.get(b).add(a); } } });
  let ch = true; while (ch) { ch = false; adj.forEach((s, k) => { if (s.size === 1) { const o = [...s][0]; adj.get(o).delete(k); s.clear(); ch = true; } }); }
  const ord = new Map(); adj.forEach((s, k) => { const p = nodes.get(k); ord.set(k, [...s].sort((a, b) => vang(vsub(nodes.get(a), p)) - vang(vsub(nodes.get(b), p)))); });
  const out = [];
  adj.forEach((s, u) => s.forEach(v => { if (E.has(u + '>' + v)) return; const loop = []; let a = u, b = v, g = 0;
    while (!E.has(a + '>' + b) && g++ < 10000) { E.add(a + '>' + b); loop.push(nodes.get(a)); const L = ord.get(b), i = L.indexOf(a); const c = L[(i - 1 + L.length) % L.length]; a = b; b = c; }
    let A = 0; for (let i = 0; i < loop.length; i++) { const p = loop[i], q = loop[(i + 1) % loop.length]; A += p[0] * q[1] - q[0] * p[1]; }
    if (A > 1e-8) out.push(loop); }));
  return out;
}

/* offset otomatik kesme: sadece yeni offset kesilir.
   1) başka kapalı alanın içine giren, 2) mevcut çizginin üstüne binen, 3) başka alana offset mesafesinden yakın kalan parçalar silinir */
function inPoly(q, P) { let c = false; for (let i = 0, j = P.length - 1; i < P.length; j = i++) { const a = P[i], b = P[j]; if ((a[1] > q[1]) !== (b[1] > q[1]) && q[0] < (b[0] - a[0]) * (q[1] - a[1]) / (b[1] - a[1]) + a[0]) c = !c; } return c; }
function offsetCut(ne, src, d, ents) {
  const others = ents.filter(e => e !== src && e !== ne && !e.imp && e.t !== 'pt');
  const sp = src.t === 'line' ? src.a : src.t === 'pl' ? src.p[0] : src.t === 'arc' ? arcPts(src)[0] : vadd(src.c, [src.r, 0]);
  const inside = (m, e) => e.t === 'pl' ? inPoly(m, e.p) : vdist(m, e.c) < e.r - 1e-6;
  const rooms = others.filter(e => ((e.t === 'pl' && e.c) || e.t === 'cir') && !inside(sp, e));
  const U = entU(ne); const us = cutsOn(ne, others);
  /* üst üste binen paralel parçaların uçlarından da böl */
  const segs = []; others.forEach(e => prims(e).forEach(Q => { if (Q.k === 's') segs.push(Q); }));
  prims(ne).forEach(P => { if (P.k !== 's') return; const d0 = vsub(P.b, P.a), L = vlen(d0); if (L < 1e-9) return; const u = vmul(d0, 1 / L);
    segs.forEach(Q => { if (Math.abs(vcross(u, vunit(vsub(Q.b, Q.a)))) > 1e-7 || Math.abs(vcross(u, vsub(Q.a, P.a))) > 1e-4) return;
      [Q.a, Q.b].forEach(x => { const t = vdot(vsub(x, P.a), u); if (t > 1e-7 && t < L - 1e-7) us.push(P.s0 + t); }); }); });
  if (ne.t === 'pl') prims(ne).forEach(P => us.push(P.s0));
  const per0 = periodic(ne) && ne.t === 'pl';
  const cuts = uniqSort(us.filter(u => (per0 ? u >= 0 : u > 1e-7) && u < U - 1e-7));
  const per = periodic(ne), bounds = per ? cuts : [0].concat(cuts, [U]);
  if (per && !cuts.length) bounds.push(0, U);
  const iv = []; const n = per ? bounds.length : bounds.length - 1;
  for (let k = 0; k < n; k++) { let a = bounds[k], b = per ? bounds[(k + 1) % bounds.length] : bounds[k + 1]; if (per && b <= a) b += U; if (per && bounds.length === 2 && !cuts.length && k) break; iv.push([a, b]); }
  const bad = ([a, b]) => {
    const m = ptAt(ne, ((a + b) / 2) % U);
    if (others.some(e => { const r = nearEnt(e, m); return r && r.d < 1e-4; })) return true;
    if (rooms.some(e => inside(m, e))) return true;
    if (rooms.some(e => { const r = nearEnt(e, m); return r && r.d < d - 1e-6; })) return true;
    return false;
  };
  const keep = iv.map(x => !bad(x)); if (keep.every(Boolean)) return [ne]; if (!keep.some(Boolean)) return [];
  const runs = []; let start = per ? keep.indexOf(false) + 1 : 0;
  for (let g = 0, k = start; g < iv.length; g++, k++) { const i = k % iv.length; if (!keep[i]) continue; const last = runs[runs.length - 1]; if (last && last.end === (i - 1 + iv.length) % iv.length && (per || i > 0)) { last.b = iv[i][1]; last.end = i; } else runs.push({ a: iv[i][0], b: iv[i][1], end: i }); }
  return runs.map(r => { const a = r.a % U; let b = r.b % U; if (b < 1e-9) b = U; if (ne.t === 'line') return subEnt(ne, a, b); if (ne.t === 'cir') return subEnt(ne, a, b > a ? b : b + 0); return subEnt(ne, a, b); });
}
if (typeof module !== 'undefined') module.exports = { offsetCut, inPoly, prims, trimEnt, extendEnt, filletEnts, offsetEnt, arc3, joinEnts, explodeEnt, plRuns, faces, subEnt, nearEnt, entU, cutsOn, rayHit, arcSw, arcPts, segSeg, primInts };
