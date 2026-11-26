/* ROLEVE CAD — kapı/pencere + DXF (uygulama değişkenlerini sadece çağrı anında kullanır) */
const OPEN = ['door', 'win'];
const BG = '#121417';

/* ---------- kapı / pencere ---------- */
function opsList() { return D.ops || (D.ops = []); }
function opById(id) { return opsList().find(o => o.id === id); }
function segsAll() { const out = []; D.ents.forEach(e => { if (e.imp) return; prims(e).forEach(P => { if (P.k === 's' && vdist(P.a, P.b) > 1e-6) out.push(P); }); }); return out; }
function opN(o) { return vunit(vperp(vsub(o.b, o.a))); }
/* offset ikizi: kapının karşısındaki paralel çizgi (3–60 cm) → işaretli kalınlık */
function opTh(o) {
  const u = vunit(vsub(o.b, o.a)), n = vperp(u), L = vdist(o.a, o.b), m = vmul(vadd(o.a, o.b), 0.5); let best = 0;
  segsAll().forEach(P => {
    const d = vsub(P.b, P.a); if (Math.abs(vcross(vunit(d), u)) > 0.02) return;
    const dd = vdot(vsub(P.a, o.a), n); if (Math.abs(dd) < 0.03 || Math.abs(dd) > 0.6) return;
    const t1 = vdot(vsub(P.a, o.a), u), t2 = vdot(vsub(P.b, o.a), u); const lo = Math.min(t1, t2), hi = Math.max(t1, t2);
    if (hi < L * 0.5 - 1e-6 || lo > L * 0.5 + 1e-6) { void m; return; }
    if (!best || Math.abs(dd) < Math.abs(best)) best = dd;
  });
  return best;
}
function plInsert(e, p) {
  if (e.t !== 'pl') return false; const ps = prims(e);
  for (const P of ps) { if (vsame(P.a, p) || vsame(P.b, p)) return false; const r = nearPrim(P, p); if (r.d < CO) { e.p.splice(P.i + 1, 0, cl(p)); return true; } }
  return false;
}
function hostAt(X, Y) { const q = s2w(X, Y), R = 18 / view.s; let best = null; D.ents.forEach(e => { if (e.imp) return; prims(e).forEach(P => { if (P.k !== 's') return; const r = nearPrim(P, q); if (r.d <= R && (!best || r.d < best.d)) best = { e, P, d: r.d }; }); }); return best; }
function projSeg(P, p) { const d = vsub(P.b, P.a), t = Math.max(0, Math.min(1, vdot(vsub(p, P.a), d) / vdot(d, d))); return vadd(P.a, vmul(d, t)); }
function opPlace(sn, X, Y) {
  if (!S.opA) { const h = hostAt(X, Y); if (!h) { flash(); return; } S.opA = { eid: h.e.id, a: projSeg(h.P, sn.p), P: { a: cl(h.P.a), b: cl(h.P.b) } }; render(); return; }
  const A = S.opA, b = projSeg(A.P, sn.p); S.opA = null;
  if (vdist(A.a, b) < 0.2) { flash(); render(); return; }
  const o = { id: 'o' + (D.nid++), t: S.tool, a: cl(A.a), b: cl(b), hinge: 0, sw: 1 };
  const host = entById(A.eid); if (host) { plInsert(host, o.a); plInsert(host, o.b); }
  const th = opTh(o);
  if (th) { const n = vmul(opN(o), th); D.ents.forEach(e => { if (e === host || e.imp || e.t !== 'pl') return; const pa = vadd(o.a, n), pb = vadd(o.b, n); if (prims(e).some(P => P.k === 's' && nearPrim(P, pa).d < CO)) { plInsert(e, pa); plInsert(e, pb); } }); o.sw = th > 0 ? -1 : 1; }
  opsList().push(o); commit();
}
function opCycle(o) { const st = [[0, 1], [1, 1], [1, -1], [0, -1]]; let i = st.findIndex(s => s[0] === o.hinge && s[1] === o.sw); i = (i + 1) % 4; o.hinge = st[i][0]; o.sw = st[i][1]; }
function opDelete(o) {
  D.ops = opsList().filter(x => x !== o); const th = opTh(o), n = vmul(opN(o), th);
  const pts = [o.a, o.b].concat(th ? [vadd(o.a, n), vadd(o.b, n)] : []);
  pts.forEach(p => { if (opsList().some(x => vsame(x.a, p) || vsame(x.b, p))) return; D.ents.forEach(e => { if (e.t !== 'pl') return; const k = e.p.length; for (let i = 0; i < k; i++) { if (!vsame(e.p[i], p)) continue; if (!e.c && (i === 0 || i === k - 1)) continue; const a = e.p[(i - 1 + k) % k], b = e.p[(i + 1) % k]; if (Math.abs(vcross(vunit(vsub(p, a)), vunit(vsub(b, p)))) < 1e-6 && vdot(vsub(p, a), vsub(b, p)) > 0 && k > (e.c ? 3 : 2)) { e.p.splice(i, 1); } break; } }); });
}
function opHit(X, Y) { const q = s2w(X, Y), R = 16 / view.s; let best = null; opsList().forEach(o => { const th = opTh(o), n = vmul(opN(o), th / 2), m = [vadd(o.a, n), vadd(o.b, n)]; const d = Math.min(nearPrim({ k: 's', a: o.a, b: o.b }, q).d, nearPrim({ k: 's', a: m[0], b: m[1] }, q).d); if (d <= R && (!best || d < best.d)) best = { o, d }; }); return best; }
/* kenar kaydırma / köşe taşıma ile kapıların gelmesi */
function opsOnSeg(A, B) { return opsList().filter(o => nearPrim({ k: 's', a: A, b: B }, o.a).d < CO && nearPrim({ k: 's', a: A, b: B }, o.b).d < CO); }
function opGeo(o) {
  const th = opTh(o), n = opN(o), w = vdist(o.a, o.b), f = k => vmul(n, k);
  const t0 = th ? 0 : -0.05, t1 = th ? th : 0.05;
  const g = { th, n, w, jambs: [[o.a, vadd(o.a, f(t1))], [o.b, vadd(o.b, f(t1))]], lines: [], arc: null };
  if (!th) g.jambs = [[vadd(o.a, f(t0)), vadd(o.a, f(t1))], [vadd(o.b, f(t0)), vadd(o.b, f(t1))]];
  if (o.t === 'win') [t0, (t0 + t1) / 2, t1].forEach(k => g.lines.push([vadd(o.a, f(k)), vadd(o.b, f(k))]));
  else { const face = th && Math.sign(th) === o.sw ? th : 0; const H = vadd(o.hinge ? o.b : o.a, f(face)), J = vadd(o.hinge ? o.a : o.b, f(face)), E = vadd(H, vmul(n, o.sw * w)); g.lines.push([H, E]); g.arc = { c: H, r: w, e: E, j: J }; }
  g.band = th ? [o.a, o.b, vadd(o.b, f(th)), vadd(o.a, f(th))] : null;
  return g;
}
function drawOps() {
  opsList().forEach(o => {
    const g = opGeo(o), sel = S.selOp === o.id, col = sel ? '#6fb0ff' : o.t === 'door' ? '#e2e8f0' : '#7dd3fc';
    cx.strokeStyle = BG; cx.lineWidth = 5; cx.setLineDash([]); cx.beginPath(); cx.moveTo(...w2s(...o.a)); cx.lineTo(...w2s(...o.b)); if (g.th) { const n = vmul(g.n, g.th); cx.moveTo(...w2s(...vadd(o.a, n))); cx.lineTo(...w2s(...vadd(o.b, n))); } cx.stroke();
    if (g.band) { cx.fillStyle = BG; cx.beginPath(); g.band.forEach((p, i) => { const s = w2s(...p); if (i) cx.lineTo(...s); else cx.moveTo(...s); }); cx.closePath(); cx.fill(); }
    cx.strokeStyle = col; cx.lineWidth = sel ? 2.4 : 1.6; cx.beginPath(); g.jambs.concat(g.lines).forEach(([a, b]) => { cx.moveTo(...w2s(...a)); cx.lineTo(...w2s(...b)); }); cx.stroke();
    if (g.arc) { const H = w2s(...g.arc.c), E = w2s(...g.arc.e), J = w2s(...g.arc.j); const r = Math.hypot(E[0] - H[0], E[1] - H[1]); const a1 = Math.atan2(E[1] - H[1], E[0] - H[0]); let d = Math.atan2(J[1] - H[1], J[0] - H[0]) - a1; while (d > Math.PI) d -= TAU; while (d <= -Math.PI) d += TAU; cx.lineWidth = 1; cx.setLineDash([4, 3]); cx.beginPath(); cx.arc(H[0], H[1], r, a1, a1 + d, d < 0); cx.stroke(); cx.setLineDash([]); }
    if (sel) [o.a, o.b].forEach(p => { const s = w2s(...p); cx.fillStyle = '#2b6fd6'; cx.strokeStyle = '#fff'; cx.lineWidth = 1.2; cx.fillRect(s[0] - 6, s[1] - 6, 12, 12); cx.strokeRect(s[0] - 6, s[1] - 6, 12, 12); });
  });
  if (S.opA) { const a = w2s(...S.opA.a); cx.strokeStyle = '#4cd964'; cx.lineWidth = 2; cx.beginPath(); cx.arc(a[0], a[1], 6, 0, TAU); cx.stroke();
    if (S.snap && S.cur) { const b = w2s(...projSeg(S.opA.P, S.snap.p)); cx.lineWidth = 4; cx.beginPath(); cx.moveTo(...a); cx.lineTo(...b); cx.stroke(); lenLabel(S.opA.a, projSeg(S.opA.P, S.snap.p)); } }
}
function opPanel() {
  const o = S.tool === 'sec' && S.selOp && opById(S.selOp); if (!o || S.fly) return '';
  return (o.t === 'door' ? btn('oph', 'dhinge') + btn('ops', 'dswing') : '') + btn('opt', o.t === 'door' ? 'window' : 'door') + btn('opdel', 'erase', false, 'dng');
}

/* ---------- DXF dışa aktarma (R12) ---------- */
function dxfStr(t) { return String(t).replace(/[^\x20-\x7e]/g, ch => '\\U+' + ch.charCodeAt(0).toString(16).toUpperCase().padStart(4, '0')); }
function pointNames() {
  const pts = []; const add = p => { if (!pts.some(q => vsame(q, p))) pts.push(cl(p)); };
  D.ents.forEach(e => { if (e.imp) return; if (e.t === 'line') { add(e.a); add(e.b); } else if (e.t === 'pl') e.p.forEach(add); else if (e.t === 'arc') { const a = arcPts(e); add(a[0]); add(a[2]); } });
  opsList().forEach(o => { add(o.a); add(o.b); });
  return pts.map((p, i) => ({ name: 'X' + (i + 1), p }));
}
function makeDXF() {
  const E = [], f = v => (Math.round(v * 10000) / 10000).toString(), deg = r => nrm(r) * 180 / Math.PI;
  const line = (ly, a, b) => E.push('0', 'LINE', '8', ly, '10', f(a[0]), '20', f(a[1]), '30', '0', '11', f(b[0]), '21', f(b[1]), '31', '0');
  const ent = (e, ly) => {
    if (e.t === 'line') line(ly, e.a, e.b);
    else if (e.t === 'pl') { E.push('0', 'POLYLINE', '8', ly, '66', '1', '10', '0', '20', '0', '30', '0', '70', e.c ? '1' : '0'); e.p.forEach(p => E.push('0', 'VERTEX', '8', ly, '10', f(p[0]), '20', f(p[1]), '30', '0')); E.push('0', 'SEQEND', '8', ly); }
    else if (e.t === 'cir') E.push('0', 'CIRCLE', '8', ly, '10', f(e.c[0]), '20', f(e.c[1]), '30', '0', '40', f(e.r));
    else if (e.t === 'arc') E.push('0', 'ARC', '8', ly, '10', f(e.c[0]), '20', f(e.c[1]), '30', '0', '40', f(e.r), '50', f(deg(e.a0)), '51', f(deg(e.a1)));
    else if (e.t === 'pt') E.push('0', 'POINT', '8', ly, '10', f(e.p[0]), '20', f(e.p[1]), '30', '0');
  };
  D.ents.forEach(e => ent(e, e.imp ? 'IMPORT' : 'CIZIM'));
  opsList().forEach(o => { const g = opGeo(o), ly = o.t === 'door' ? 'KAPI' : 'PENCERE'; g.jambs.concat(g.lines).forEach(([a, b]) => line(ly, a, b));
    if (g.arc) { const e = vsub(g.arc.e, g.arc.c), j = vsub(g.arc.j, g.arc.c); const a1 = vang(e), a2 = vang(j); const ccw = vcross(e, j) > 0; E.push('0', 'ARC', '8', ly, '10', f(g.arc.c[0]), '20', f(g.arc.c[1]), '30', '0', '40', f(g.arc.r), '50', f(deg(ccw ? a1 : a2)), '51', f(deg(ccw ? a2 : a1))); } });
  pointNames().forEach(t => { E.push('0', 'POINT', '8', 'NOKTA', '10', f(t.p[0]), '20', f(t.p[1]), '30', '0'); E.push('0', 'TEXT', '8', 'NOKTA', '10', f(t.p[0] + 0.05), '20', f(t.p[1] + 0.05), '30', '0', '40', '0.1', '1', dxfStr(t.name)); });
  const LY = [['CIZIM', 7], ['KAPI', 2], ['PENCERE', 4], ['NOKTA', 1], ['IMPORT', 8]];
  const T = ['0', 'SECTION', '2', 'HEADER', '9', '$ACADVER', '1', 'AC1009', '9', '$DWGCODEPAGE', '3', 'ANSI_1254', '0', 'ENDSEC', '0', 'SECTION', '2', 'TABLES', '0', 'TABLE', '2', 'LAYER', '70', String(LY.length)];
  LY.forEach(([n, c]) => T.push('0', 'LAYER', '2', n, '70', '0', '62', String(c), '6', 'CONTINUOUS')); T.push('0', 'ENDTAB', '0', 'ENDSEC', '0', 'SECTION', '2', 'ENTITIES');
  return T.concat(E, ['0', 'ENDSEC', '0', 'EOF']).join('\r\n') + '\r\n';
}
async function shareOrDownload(text, name, type) {
  const blob = new Blob([text], { type }); const fl = new File([blob], name, { type });
  try { if (navigator.canShare && navigator.canShare({ files: [fl] })) { await navigator.share({ files: [fl] }); return true; } } catch (er) { if (er.name === 'AbortError') return false; }
  const u = URL.createObjectURL(blob); const a = document.createElement('a'); a.href = u; a.download = name; document.body.appendChild(a); a.click(); a.remove(); return true;
}
function exportDXF() { const d = new Date(), z = v => String(v).padStart(2, '0'); const n = `cizim_${d.getFullYear()}${z(d.getMonth() + 1)}${z(d.getDate())}_${z(d.getHours())}${z(d.getMinutes())}.dxf`; window._lastDXF = makeDXF(); window._lastDXFName = n; shareOrDownload(window._lastDXF, n, 'application/dxf').then(ok => { if (ok) flashOk(D.ents.map(e => e.id), false); }); }

/* ---------- DXF içe aktarma ---------- */
function parseDXF(txt) {
  const L = txt.split(/\r?\n/); const pr = []; for (let i = 0; i + 1 < L.length; i += 2) pr.push([parseInt(L[i].trim(), 10), L[i + 1].trim()]);
  let i = 0; while (i < pr.length && !(pr[i][0] === 2 && pr[i][1] === 'ENTITIES')) i++;
  const out = []; let cur = null, poly = null;
  const flush = () => { if (!cur) return; const g = cur.g, n = k => (g[k] || []).map(Number), v = k => Number((g[k] || [0])[0]); const ly = (g[8] || ['0'])[0];
    const T = cur.type;
    if (T === 'LINE') out.push({ t: 'line', a: [v(10), v(20)], b: [v(11), v(21)], lay: ly });
    else if (T === 'LWPOLYLINE') { const xs = n(10), ys = n(20); const p = xs.map((x, k) => [x, ys[k]]); if (p.length >= 2) out.push({ t: 'pl', p, c: !!(v(70) & 1), lay: ly }); }
    else if (T === 'POLYLINE') poly = { p: [], c: !!(v(70) & 1), lay: ly };
    else if (T === 'VERTEX' && poly) poly.p.push([v(10), v(20)]);
    else if (T === 'SEQEND' && poly) { if (poly.p.length >= 2) out.push({ t: 'pl', p: poly.p, c: poly.c, lay: poly.lay }); poly = null; }
    else if (T === 'CIRCLE') out.push({ t: 'cir', c: [v(10), v(20)], r: v(40), lay: ly });
    else if (T === 'ARC') out.push({ t: 'arc', c: [v(10), v(20)], r: v(40), a0: nrm(v(50) * Math.PI / 180), a1: nrm(v(51) * Math.PI / 180), lay: ly });
    else if (T === 'POINT') out.push({ t: 'pt', p: [v(10), v(20)], lay: ly });
    cur = null; };
  for (i++; i < pr.length; i++) { const [c, val] = pr[i]; if (c === 0) { flush(); if (val === 'ENDSEC') break; cur = { type: val, g: {} }; } else if (cur) (cur.g[c] = cur.g[c] || []).push(val); }
  flush();
  return out.filter(e => (e.t !== 'pl' || e.p.length >= 2) && (e.t !== 'cir' && e.t !== 'arc' || e.r > 0));
}
function importDXF(txt) { const list = parseDXF(txt); if (!list.length) { flash(); return 0; } list.forEach(e => { e.imp = true; addEnt(e); }); commit(); fit(); return list.length; }
