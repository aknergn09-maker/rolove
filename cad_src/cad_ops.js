/* ROLEVE CAD — kapı/pencere + DXF (uygulama değişkenlerini sadece çağrı anında kullanır) */
const OPEN = ['door', 'win'];
const BG = '#121417';

/* ---------- kapı / pencere ---------- */
function opsList() { return D.ops || (D.ops = []); }
function opById(id) { return opsList().find(o => o.id === id); }
function segsAll() { const out = []; D.ents.forEach(e => { if (e.imp) return; prims(e).forEach(P => { if (P.k === 's' && vdist(P.a, P.b) > 1e-6) out.push(P); }); }); return out; }
function opN(o) { return vunit(vperp(vsub(o.b, o.a))); }
/* offset ikizi: kapının karşısındaki paralel çizgi (3–60 cm) → işaretli kalınlık */
function opCands(o) { /* kapı ortasının karşısındaki paralel çizgiler (ayar sınırı içinde), yakından uzağa */
  const u = vunit(vsub(o.b, o.a)), n = vperp(u), L = vdist(o.a, o.b), out = [];
  segsAll().forEach(P => {
    const d = vsub(P.b, P.a); if (Math.abs(vcross(vunit(d), u)) > 0.02) return;
    const dd = vdot(vsub(P.a, o.a), n); if (Math.abs(dd) < 0.03 || Math.abs(dd) > (S.thMax || 0.6) + 1e-9) return;
    const t1 = vdot(vsub(P.a, o.a), u), t2 = vdot(vsub(P.b, o.a), u); if (Math.max(t1, t2) < L * 0.5 - 1e-6 || Math.min(t1, t2) > L * 0.5 + 1e-6) return;
    if (!out.some(x => Math.abs(x - dd) < 1e-4)) out.push(dd);
  });
  return out.sort((a, b) => Math.abs(a) - Math.abs(b));
}
function opTh(o) { /* kapının seçtiği kalınlık: o.th = 0 → tek çizgi; yoksa hatırlanan değere en yakın aday */
  if (o.th === 0) return 0; const c = opCands(o); if (!c.length) return 0; if (o.th == null) return c[0];
  let best = c[0]; c.forEach(x => { if (Math.abs(x - o.th) < Math.abs(best - o.th)) best = x; }); return best;
}
function plRemoveAt(p) {
  if (opsList().some(x => vsame(x.a, p) || vsame(x.b, p))) return;
  D.ents.forEach(e => { if (e.t !== 'pl') return; const k = e.p.length; for (let i = 0; i < k; i++) { if (!vsame(e.p[i], p)) continue; if (!e.c && (i === 0 || i === k - 1)) continue; const a = e.p[(i - 1 + k) % k], b = e.p[(i + 1) % k]; if (Math.abs(vcross(vunit(vsub(p, a)), vunit(vsub(b, p)))) < 1e-6 && vdot(vsub(p, a), vsub(b, p)) > 0 && k > (e.c ? 3 : 2)) e.p.splice(i, 1); break; } });
}
function twinInsert(o, th) { if (!th) return; const n = vmul(opN(o), th), pa = vadd(o.a, n), pb = vadd(o.b, n); D.ents.forEach(e => { if (e.imp || e.t !== 'pl') return; if (prims(e).some(P => P.k === 's' && nearPrim(P, pa).d < CO)) { plInsert(e, pa); plInsert(e, pb); } }); }
function twinRemove(o, th) { if (!th) return; const n = vmul(opN(o), th); plRemoveAt(vadd(o.a, n)); plRemoveAt(vadd(o.b, n)); }
/* kalınlık düğmesi: en yakın → tek çizgi → sonraki paralel çizgi … */
function opWall(o) {
  const c = opCands(o), opts = c.concat([0]), cur = opTh(o); let i = 0, bd = Infinity; opts.forEach((x, k) => { const d = Math.abs(x - cur); if (d < bd) { bd = d; i = k; } });
  const nx = opts[(i + 1) % opts.length]; twinRemove(o, cur); o.th = nx; twinInsert(o, nx); if (nx) o.sw = nx > 0 ? -1 : 1;
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
  const c = opCands(o), th = c.length ? c[0] : 0; o.th = th;
  if (th) { twinInsert(o, th); o.sw = th > 0 ? -1 : 1; }
  opsList().push(o); commit();
}
function opCycle(o) { const st = [[0, 1], [1, 1], [1, -1], [0, -1]]; let i = st.findIndex(s => s[0] === o.hinge && s[1] === o.sw); i = (i + 1) % 4; o.hinge = st[i][0]; o.sw = st[i][1]; }
function opDelete(o) {
  const th = opTh(o); D.ops = opsList().filter(x => x !== o); plRemoveAt(o.a); plRemoveAt(o.b); twinRemove(o, th);
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
  return (o.t === 'door' ? btn('oph', 'dhinge') + btn('ops', 'dswing') : '') + btn('opw', 'wallth') + btn('opt', o.t === 'door' ? 'window' : 'door') + btn('opdel', 'erase', false, 'dng');
}

/* ---------- DXF dışa aktarma (R12) ---------- */
function dxfStr(t) { return String(t).replace(/[^\x20-\x7e]/g, ch => '\\U+' + ch.charCodeAt(0).toString(16).toUpperCase().padStart(4, '0')); }
function pointNames() {
  const pts = [], used = new Set(); nameList().forEach(n => { pts.push({ name: n.n, p: cl(n.p), user: true }); used.add(n.n); });
  const add = p => { if (!pts.some(q => vsame(q.p, p))) pts.push({ p: cl(p) }); };
  D.ents.forEach(e => { if (e.imp) return; if (e.t === 'line') { add(e.a); add(e.b); } else if (e.t === 'pl') e.p.forEach(add); else if (e.t === 'arc') { const a = arcPts(e); add(a[0]); add(a[2]); } });
  opsList().forEach(o => { add(o.a); add(o.b); });
  measList().forEach(m => { m.pts.forEach(add); if (m.k === 'm_pl') add(footOn(m.pts[0], m.pts[1], m.pts[2])); });
  let k = 1; pts.forEach(t => { if (t.name) return; while (used.has('X' + k)) k++; t.name = 'X' + k; used.add(t.name); });
  return pts;
}
function makeDXF() {
  const E = [], f = v => (Math.round(v * 10000) / 10000).toString(), deg = r => nrm(r) * 180 / Math.PI;
  let OX = 0; const T = p => [p[0] + OX, p[1]];
  const line = (ly, a, b) => { a = T(a); b = T(b); E.push('0', 'LINE', '8', ly, '10', f(a[0]), '20', f(a[1]), '30', '0', '11', f(b[0]), '21', f(b[1]), '31', '0'); };
  const text = (ly, p, h, t) => { p = T(p); E.push('0', 'TEXT', '8', ly, '10', f(p[0]), '20', f(p[1]), '30', '0', '40', f(h), '1', dxfStr(t), '7', 'ARIAL'); };
  const point = (ly, p) => { p = T(p); E.push('0', 'POINT', '8', ly, '10', f(p[0]), '20', f(p[1]), '30', '0'); };
  const ent = (e, ly) => {
    if (e.t === 'line') line(ly, e.a, e.b);
    else if (e.t === 'pl') { E.push('0', 'POLYLINE', '8', ly, '66', '1', '10', '0', '20', '0', '30', '0', '70', e.c ? '1' : '0'); e.p.forEach(q => { const p = T(q); E.push('0', 'VERTEX', '8', ly, '10', f(p[0]), '20', f(p[1]), '30', '0'); }); E.push('0', 'SEQEND', '8', ly); }
    else if (e.t === 'cir') { const c = T(e.c); E.push('0', 'CIRCLE', '8', ly, '10', f(c[0]), '20', f(c[1]), '30', '0', '40', f(e.r)); }
    else if (e.t === 'arc') { const c = T(e.c); E.push('0', 'ARC', '8', ly, '10', f(c[0]), '20', f(c[1]), '30', '0', '40', f(e.r), '50', f(deg(e.a0)), '51', f(deg(e.a1))); }
    else if (e.t === 'pt') point(ly, e.p);
  };
  /* kapı/pencere: her biri tek blok (BLOCK + INSERT); blok içi katman 0 → INSERT'in katmanını/rengini alır */
  const B = [], bname = {}; opsList().forEach((o, k) => { const nm = (o.t === 'door' ? 'KAPI_' : 'PENCERE_') + (k + 1); bname[o.id] = nm; const g = opGeo(o), bl = (a, b) => B.push('0', 'LINE', '8', '0', '10', f(a[0]), '20', f(a[1]), '30', '0', '11', f(b[0]), '21', f(b[1]), '31', '0');
    B.push('0', 'BLOCK', '8', '0', '2', nm, '70', '0', '10', f(o.a[0]), '20', f(o.a[1]), '30', '0', '3', nm); g.jambs.concat(g.lines).forEach(([a, b]) => bl(a, b));
    if (g.arc) { const e = vsub(g.arc.e, g.arc.c), j = vsub(g.arc.j, g.arc.c); const a1 = vang(e), a2 = vang(j); const ccw = vcross(e, j) > 0; B.push('0', 'ARC', '8', '0', '10', f(g.arc.c[0]), '20', f(g.arc.c[1]), '30', '0', '40', f(g.arc.r), '50', f(deg(ccw ? a1 : a2)), '51', f(deg(ccw ? a2 : a1))); }
    B.push('0', 'ENDBLK', '8', '0'); });
  const opsOut = (lyK, lyP) => opsList().forEach(o => { const p = T(o.a); E.push('0', 'INSERT', '8', o.t === 'door' ? lyK : lyP, '2', bname[o.id], '10', f(p[0]), '20', f(p[1]), '30', '0'); });
  const PN = pointNames(), nameOf = p => { const t = PN.find(x => vsame(x.p, p)); return t ? t.name : '?'; }, ML = measDXFLines(nameOf);
  /* kopya 1 (gerçek koordinat): çizim, kapı/pencere, nokta adları, ölçüler */
  D.ents.forEach(e => ent(e, e.imp ? 'IMPORT' : 'CIZIM')); opsOut('KAPI', 'PENCERE');
  PN.forEach(t => { const ly = t.user ? 'NOKTA_AD' : 'NOKTA_X'; point(ly, t.p); text(ly, [t.p[0] + 0.05, t.p[1] + 0.05], 0.1, t.name); });
  const measOut = (cat, ly) => ML.filter(o => o.cat === cat).forEach(o => { o.lines.forEach(([a, b]) => line(ly, a, b)); text(ly, o.at, 0.08, o.txt + (o.src === 'laser' ? ' L' : '')); });
  measOut('olcu', 'OLCU');
  noteList().forEach(n => { if (!n.s) return; point('NOT', n.p); n.s.split('\n').forEach((ln, i) => { if (ln.trim()) text('NOT', [n.p[0] + 0.08, n.p[1] - 0.15 * i], 0.1, ln.slice(0, 250)); }); });
  /* PC programı için gizli bilgi (META katmanı donuk): kapı/pencere hangi iki noktaya bağlı */
  opsList().forEach(o => text('META', o.a, 0.05, `OP ${bname[o.id]} ${nameOf(o.a)} ${nameOf(o.b)} ${o.t}`));
  /* kopya 2 ve 3: aynı çizim sağa kaydırılmış — gönye, dik ayak/dik boy */
  const own = D.ents.filter(e => !e.imp), xs = [], ys = [];
  own.forEach(e => { if (e.t === 'line') { xs.push(e.a[0], e.b[0]); ys.push(e.a[1], e.b[1]); } else if (e.t === 'pl') e.p.forEach(p => { xs.push(p[0]); ys.push(p[1]); }); else if (e.c) { xs.push(e.c[0] - e.r, e.c[0] + e.r); ys.push(e.c[1] + e.r); } });
  const x0 = xs.length ? Math.min(...xs) : 0, W = xs.length ? Math.max(...xs) - x0 : 10, yT = ys.length ? Math.max(...ys) : 0, step = Math.max(W, 1) * 1.5;
  [['gonye', 'GONYE', 'KOPYA_GONYE', 'GONYE'], ['dik', 'DIKAYAK', 'KOPYA_DIKAYAK', 'DIK AYAK / DIK BOY']].forEach(([cat, ly, lyC, title], k) => {
    if (!ML.some(o => o.cat === cat)) return; OX = step * (k + 1);
    own.forEach(e => ent(e, lyC)); opsOut(lyC, lyC); measOut(cat, ly);
    const used = []; ML.filter(o => o.cat === cat).forEach(o => o.pts.forEach(p => { if (used.some(q => vsame(q, p))) return; used.push(p); text(ly, [p[0] + 0.05, p[1] + 0.05], 0.1, nameOf(p)); }));
    text(ly, [x0, yT + 0.4], 0.25, title);
  });
  OX = 0;
  const LY = [['CIZIM', 7], ['KAPI', 2], ['PENCERE', 4], ['NOKTA_AD', 3], ['NOKTA_X', 1], ['OLCU', 30], ['NOT', 2], ['GONYE', 5], ['DIKAYAK', 6], ['KOPYA_GONYE', 8], ['KOPYA_DIKAYAK', 8], ['IMPORT', 8]];
  const H = ['0', 'SECTION', '2', 'HEADER', '9', '$ACADVER', '1', 'AC1009', '9', '$DWGCODEPAGE', '3', 'ANSI_1254', '0', 'ENDSEC', '0', 'SECTION', '2', 'TABLES', '0', 'TABLE', '2', 'LAYER', '70', String(LY.length + 1)];
  LY.push(['META', 8]); LY.forEach(([n, c]) => H.push('0', 'LAYER', '2', n, '70', n === 'META' ? '1' : '0', '62', String(c), '6', 'CONTINUOUS')); H.push('0', 'ENDTAB', '0', 'TABLE', '2', 'STYLE', '70', '1', '0', 'STYLE', '2', 'ARIAL', '70', '0', '40', '0', '41', '1', '50', '0', '71', '0', '42', '0.1', '3', 'arial.ttf', '4', '', '0', 'ENDTAB', '0', 'ENDSEC', '0', 'SECTION', '2', 'BLOCKS'); B.forEach(x => H.push(x)); H.push('0', 'ENDSEC', '0', 'SECTION', '2', 'ENTITIES');
  return H.concat(E, ['0', 'ENDSEC', '0', 'EOF']).join('\r\n') + '\r\n';
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
  /* bölümleri sırayla oku: BLOCKS (blok tanımları) ve ENTITIES */
  const blocks = {}; let out = [], cur = null, poly = null, blk = null, sect = null, list = out;
  const conv = (T, g, ly) => {
    const n = k => (g[k] || []).map(Number), v = k => Number((g[k] || [0])[0]);
    if (T === 'LINE') return [{ t: 'line', a: [v(10), v(20)], b: [v(11), v(21)], lay: ly }];
    if (T === 'LWPOLYLINE') { const xs = n(10), ys = n(20); const p = xs.map((x, k) => [x, ys[k]]); return p.length >= 2 ? [{ t: 'pl', p, c: !!(v(70) & 1), lay: ly }] : []; }
    if (T === 'CIRCLE') return [{ t: 'cir', c: [v(10), v(20)], r: v(40), lay: ly }];
    if (T === 'ARC') return [{ t: 'arc', c: [v(10), v(20)], r: v(40), a0: nrm(v(50) * Math.PI / 180), a1: nrm(v(51) * Math.PI / 180), lay: ly }];
    if (T === 'POINT') return [{ t: 'pt', p: [v(10), v(20)], lay: ly }];
    if (T === 'INSERT') return [{ t: 'ins', name: (g[2] || [''])[0], at: [v(10), v(20)], sx: g[41] ? v(41) : 1, sy: g[42] ? v(42) : 1, rot: v(50) * Math.PI / 180, lay: ly }];
    return [];
  };
  const flush = () => { if (!cur) return; const g = cur.g, ly = (g[8] || ['0'])[0], T = cur.type, v = k => Number((g[k] || [0])[0]);
    if (T === 'POLYLINE') poly = { p: [], c: !!(v(70) & 1), lay: ly };
    else if (T === 'VERTEX' && poly) poly.p.push([v(10), v(20)]);
    else if (T === 'SEQEND' && poly) { if (poly.p.length >= 2) list.push({ t: 'pl', p: poly.p, c: poly.c, lay: poly.lay }); poly = null; }
    else if (T === 'BLOCK') { blk = { name: (g[2] || [''])[0], base: [v(10), v(20)], ents: [] }; list = blk.ents; }
    else if (T === 'ENDBLK') { if (blk) blocks[blk.name] = blk; blk = null; list = out; }
    else conv(T, g, ly).forEach(e => list.push(e));
    cur = null; };
  for (let i = 0; i < pr.length; i++) { const [c, val] = pr[i];
    if (c === 0) { flush(); if (val === 'SECTION') { sect = null; continue; } if (val === 'ENDSEC') { sect = null; continue; } cur = (sect === 'BLOCKS' || sect === 'ENTITIES') ? { type: val, g: {} } : null; continue; }
    if (c === 2 && !cur && sect === null) { sect = val; continue; }
    if (cur) (cur.g[c] = cur.g[c] || []).push(val); }
  flush();
  /* INSERT → blok içeriğini yerine koy (konum, ölçek, dönme; iç içe en fazla 4 kat) */
  const place = (e, ins, base, depth) => {
    const c = Math.cos(ins.rot), sn = Math.sin(ins.rot), tf = p => { const x = (p[0] - base[0]) * ins.sx, y = (p[1] - base[1]) * ins.sy; return [ins.at[0] + x * c - y * sn, ins.at[1] + x * sn + y * c]; };
    const ly = !e.lay || e.lay === '0' ? ins.lay : e.lay;
    if (e.t === 'line') return [{ t: 'line', a: tf(e.a), b: tf(e.b), lay: ly }];
    if (e.t === 'pl') return [{ t: 'pl', p: e.p.map(tf), c: e.c, lay: ly }];
    if (e.t === 'pt') return [{ t: 'pt', p: tf(e.p), lay: ly }];
    if (e.t === 'cir' || e.t === 'arc') { const k = Math.abs(ins.sx); const r = { ...e, c: tf(e.c), r: e.r * k, lay: ly }; if (e.t === 'arc') { const mir = ins.sx * ins.sy < 0; const a0 = mir ? Math.PI - e.a1 : e.a0, a1 = mir ? Math.PI - e.a0 : e.a1; r.a0 = nrm(a0 + ins.rot); r.a1 = nrm(a1 + ins.rot); } return [r]; }
    if (e.t === 'ins' && depth < 4) { const b = blocks[e.name]; if (!b) return []; const inner = { ...e, at: tf(e.at), rot: e.rot + ins.rot, sx: e.sx * ins.sx, sy: e.sy * ins.sy, lay: ly }; return b.ents.flatMap(x => place(x, inner, b.base, depth + 1)); }
    return [];
  };
  const res = []; out.forEach(e => { if (e.t !== 'ins') { res.push(e); return; } const b = blocks[e.name]; if (b) b.ents.forEach(x => place(x, e, b.base, 0).forEach(y => res.push(y))); });
  return res.filter(e => (e.t !== 'pl' || e.p.length >= 2) && (e.t !== 'cir' && e.t !== 'arc' || e.r > 0));
}
function importDXF(txt) { const list = parseDXF(txt); if (!list.length) { flash(); return 0; } list.forEach(e => { e.imp = true; addEnt(e); }); commit(); fit(); return list.length; }
