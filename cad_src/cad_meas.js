/* ROLEVE CAD — ölçü notları, nokta adları, lazer (çizimi hiç değiştirmez) */
const MEAS = ['m_pp', 'm_obj', 'm_ll', 'm_ab', 'm_g', 'tag'];
const MCAT = k => k === 'm_g' ? 'gonye' : k === 'm_ab' ? 'dik' : 'olcu';
const MCOLS = { olcu: '#f5a623', gonye: '#5aa9ff', dik: '#c08bff' };
const MCOL = '#f5a623';
function measList() { return D.meas || (D.meas = []); }
function nameList() { return D.names || (D.names = []); }
/* çizgiye bağlı tüm noktalar (kapı uçları, nokta adları, ölçü uçları) — geometri değişince birlikte gelir */
function attPts() {
  const out = [];
  opsList().forEach(o => { out.push([o, 'a'], [o, 'b']); });
  nameList().forEach(n => out.push([n, 'p']));
  measList().forEach(m => m.pts.forEach((_, i) => out.push([m.pts, i])));
  return out;
}
function attMoveVertex(old, P) { attPts().forEach(([o, k]) => { if (vsame(o[k], old)) o[k] = cl(P); }); }
function attMoveEdge(A, B, nA, nB, off) {
  attPts().forEach(([o, k]) => { const p = o[k]; if (vsame(p, A)) o[k] = cl(nA); else if (vsame(p, B)) o[k] = cl(nB); else if (nearPrim({ k: 's', a: A, b: B }, p).d < CO) o[k] = vadd(p, off); });
}
/* tek kenar seçimi: pline'da aynı doğrultudaki parçalar tek kenar (pline yapısı bozulmaz) */
function segAt(X, Y) {
  const q = s2w(X, Y), R = 18 / view.s; let best = null;
  D.ents.forEach(e => { if (e.imp) return; prims(e).forEach(P => { if (P.k !== 's') return; const r = nearPrim(P, q); if (r.d <= R && (!best || r.d < best.d)) best = { e, P, d: r.d }; }); });
  if (!best) return null;
  if (best.e.t === 'pl') { const run = plRuns(best.e).find(R2 => runSegs(best.e, R2).includes(best.P.i)); if (run) { const n = best.e.p.length; return { a: cl(best.e.p[run.i0]), b: cl(best.e.p[run.i1 % n]) }; } }
  return { a: cl(best.P.a), b: cl(best.P.b) };
}
function footOn(p, a, b) { const d = vsub(b, a), t = vdot(vsub(p, a), d) / (vdot(d, d) || 1); return vadd(a, vmul(d, t)); }
function measGeo(m) {
  const P = m.pts, f3 = v => v == null ? '' : v.toFixed(3);
  if (m.k === 'm_pp' || m.k === 'm_g') return { lines: [[P[0], P[1]]], labels: [[vmul(vadd(P[0], P[1]), 0.5), f3(m.v)]] };
  if (m.k === 'm_obj') { const n = vmul(vunit(vperp(vsub(P[1], P[0]))), 14 / view.s), a = vadd(P[0], n), b = vadd(P[1], n); return { lines: [[a, b]], labels: [[vmul(vadd(a, b), 0.5), f3(m.v)]], raw: [[P[0], P[1]]] }; }
  if (m.k === 'm_pl') { const f = footOn(P[0], P[1], P[2]); return { lines: [[P[0], f]], labels: [[vmul(vadd(P[0], f), 0.5), f3(m.v)]], seg: [[P[1], P[2]]] }; }
  if (m.k === 'm_ll') { const s = vmul(vadd(P[0], P[1]), 0.5), f = footOn(s, P[2], P[3]); return { lines: [[s, f]], labels: [[vmul(vadd(s, f), 0.5), f3(m.v)]], seg: [[P[0], P[1]], [P[2], P[3]]] }; }
  if (m.k === 'm_ab') return { lines: [[P[0], P[1]], [P[1], P[2]]], labels: [[vmul(vadd(P[0], P[1]), 0.5), f3(m.v)], [vmul(vadd(P[1], P[2]), 0.5), f3(m.v2)]] };
  return { lines: [], labels: [] };
}
function measNeed(k) { return { m_pp: ['p', 'ps'], m_pl: ['p', 's'], m_g: ['p', 'p'], m_obj: ['o'], m_ll: ['s', 's'], m_ab: ['p', 'p', 'p'] }[k] || []; }
function measDone() { const q = S.mq; return q && q.picks.length === measNeed(q.k).length; }
function measPts(q) { const out = []; q.picks.forEach(x => { if (x.p) out.push(x.p); else out.push(x.a, x.b); }); return out; }
function measPlace(sn, X, Y) {
  const t = S.tool;
  if (t === 'tag') { tagPlace(sn, X, Y); return; }
  if ((!S.mq || !S.mq.picks.length || measDone()) && !['end', 'int', 'mid'].includes(sn.k)) { const mh = measHit(X, Y); if (mh) { S.mq = null; S.selMeas = S.selMeas === mh.m.id ? null : mh.m.id; S.mv = null; ui(); render(); return; } }
  S.selMeas = null; if (S.mv && S.mv.id) S.mv = null;
  if (!S.mq || (S.mq.k !== t && !(t === 'm_pp' && S.mq.k === 'm_pl')) || measDone()) S.mq = { k: t, picks: [], dir0: null };
  const need = measNeed(S.mq.k)[S.mq.picks.length];
  if (need === 'o') { const oh = opHit(X, Y); const s = oh ? { a: cl(oh.o.a), b: cl(oh.o.b) } : segAt(X, Y); if (!s) { flash(); return; } S.mq.picks.push(s); }
  else if (need === 'ps') { if (['end', 'int', 'mid', 'trk'].includes(sn.k)) S.mq.picks.push({ p: cl(sn.p) }); else { const s = segAt(X, Y); if (!s) { flash(); return; } S.mq.k = 'm_pl'; S.mq.picks.push(s); } }
  else if (need === 'p') { S.mq.picks.push({ p: cl(sn.p) }); if (S.mq.picks.length === 1 && sn.P && sn.P.k === 's') S.mq.dir0 = vsub(sn.P.b, sn.P.a); }
  else { const s = segAt(X, Y); if (!s) { flash(); return; } S.mq.picks.push(s); }
  if (measDone()) { S.mv = { v: [LZ.pend != null ? LZ.pend.toFixed(3) : '', ''], act: 0, np: false }; LZ.pend = null; }
  ui(); render();
}
function measSnapOpts() {
  const q = S.mq, o = {}; if (!q || q.k !== 'm_ab' || measDone()) return o;
  const n = q.picks.length; if (!n) return o;
  const O = q.picks[0].p; o.trkPts = [O];
  if (n === 1) { o.from = O; o.dir = q.dir0; o.tbase = q.dir0; }
  if (n === 2) { const F = q.picks[1].p; o.from = F; o.dir = vsub(F, O); o.tbase = vsub(F, O); o.trkPts = [O, F]; }
  return o;
}
function measSave() {
  const vals = S.mv.v.map(s => s === '' ? null : parseFloat(s)); const two = S.mq ? S.mq.k === 'm_ab' : (S.selMeas && measById(S.selMeas).k === 'm_ab');
  if (vals[0] == null || isNaN(vals[0]) || (two && (vals[1] == null || isNaN(vals[1])))) { flash(); return; }
  if (S.selMeas) { const m = measById(S.selMeas); m.v = vals[0]; if (two) m.v2 = vals[1]; m.src = S.mv.src || m.src; S.selMeas = null; S.mv = null; commit(); ui(); return; }
  const m = { id: 'm' + (D.nid++), k: S.mq.k, pts: measPts(S.mq), v: vals[0], src: S.mv.src || 'typed' }; if (two) m.v2 = vals[1];
  measList().push(m); S.mq = null; S.mv = null; commit(); flashMeas(m.id); ui();
}
function measById(id) { return measList().find(m => m.id === id); }
let fmT; function flashMeas(id) { S.fm = id; clearTimeout(fmT); fmT = setTimeout(() => { S.fm = null; render(); }, 900); }
function measVis(m) { return S.vis[MCAT(m.k)] !== 0; }
function measHit(X, Y) { const q = s2w(X, Y), R = 14 / view.s; let best = null; measList().filter(measVis).forEach(m => measGeo(m).lines.forEach(([a, b]) => { const d = nearPrim({ k: 's', a, b }, q).d; if (d <= R && (!best || d < best.d)) best = { m, d }; })); return best; }
function drawMeas() {
  cx.font = 'bold 13px Arial'; cx.textAlign = 'center'; cx.textBaseline = 'middle';
  measList().filter(measVis).forEach(m => {
    const MC = MCOLS[MCAT(m.k)], g = measGeo(m), sel = S.selMeas === m.id || S.fm === m.id; cx.strokeStyle = sel ? '#ffd27a' : MC; cx.lineWidth = sel ? 2.4 : 1.3; cx.setLineDash([6, 4]);
    cx.beginPath(); g.lines.forEach(([a, b]) => { cx.moveTo(...w2s(...a)); cx.lineTo(...w2s(...b)); }); cx.stroke(); cx.setLineDash([]);
    g.labels.forEach(([p, t]) => { const s = w2s(...p); const w = cx.measureText(t).width + 6; cx.fillStyle = 'rgba(18,20,23,.85)'; cx.fillRect(s[0] - w / 2, s[1] - 9, w, 18); cx.fillStyle = sel ? '#ffd27a' : MC; cx.fillText(t, s[0], s[1]); });
  });
  const q = S.mq; if (q && MEAS.includes(S.tool)) {
    cx.strokeStyle = '#4cd964'; cx.lineWidth = 2;
    q.picks.forEach(x => { if (x.p) { const s = w2s(...x.p); cx.beginPath(); cx.arc(s[0], s[1], 7, 0, TAU); cx.stroke(); } else { cx.lineWidth = 4; cx.beginPath(); cx.moveTo(...w2s(...x.a)); cx.lineTo(...w2s(...x.b)); cx.stroke(); cx.lineWidth = 2; } });
    if (measDone()) { const g = measGeo({ k: q.k, pts: measPts(q) }); cx.strokeStyle = MCOLS[MCAT(q.k)]; cx.lineWidth = 1.6; cx.setLineDash([6, 4]); cx.beginPath(); g.lines.forEach(([a, b]) => { cx.moveTo(...w2s(...a)); cx.lineTo(...w2s(...b)); }); cx.stroke(); cx.setLineDash([]); }
    else if (q.k === 'm_ab' && S.snap && S.cur && q.picks.length) { const last = q.picks[q.picks.length - 1].p; cx.strokeStyle = MCOL; cx.setLineDash([6, 4]); cx.lineWidth = 1.6; cx.beginPath(); cx.moveTo(...w2s(...last)); cx.lineTo(...w2s(...S.snap.p)); cx.stroke(); cx.setLineDash([]); }
  }
  cx.textAlign = 'start'; cx.textBaseline = 'alphabetic';
}
function measPanel() {
  const sm = S.selMeas && measById(S.selMeas);
  if (S.fly || !(sm || (MEAS.includes(S.tool) && S.tool !== 'tag'))) return '';
  if (sm && (!S.mv || S.mv.id !== sm.id)) S.mv = { id: sm.id, v: [sm.v == null ? '' : sm.v.toFixed(3), sm.v2 == null ? '' : sm.v2.toFixed(3)], act: 0, np: false };
  const done = sm || measDone(), two = sm ? sm.k === 'm_ab' : S.tool === 'm_ab';
  const st = LZ.state === 'bağlı' ? 'bt' : LZ.state === 'bağlanıyor' ? 'btw' : LZ.state === 'koptu' ? 'btx' : 'bt0';
  let h = '';
  if (done) { const mv = S.mv; [0].concat(two ? [1] : []).forEach(i => { h += `<button class="mval ${mv.act === i ? 'act' : ''}" data-a="mv:${i}">${mv.v[i] || '0.000'}</button>`; }); }
  else if (LZ.pend != null) h += `<div class="mval pend">${LZ.pend.toFixed(3)}</div>`;
  h += btn('lzc', 'bt', false, st) + btn('lzt', 'laser', false, 'las');
  if (done) { h += btn('mback', 'clr'); if (S.mv.np) h += ['7', '8', '9', '4', '5', '6', '1', '2', '3', '.', '0'].map(k => `<button class="num k" data-a="mk:${k}">${k}</button>`).join(''); h += btn('mok', 'ok', false, 'okb wide2') + (sm ? btn('mdel', 'erase', false, 'dng') : ''); }
  return h;
}
function measBtn(a) {
  if (a === 'lzc') { laserConnect(); return true; }
  if (a === 'lzt') { laserTrigger(); return true; }
  if (a.startsWith('mv:')) { const i = +a.slice(3); if (S.mv.act === i) S.mv.np = !S.mv.np; else { S.mv.act = i; S.mv.np = true; S.mv.fresh = true; } ui(); return true; }
  if (a.startsWith('mk:')) { const i = S.mv.act; let s = S.mv.fresh ? '' : S.mv.v[i]; S.mv.fresh = false; const k = a.slice(3); if (k === '.' && s.includes('.')) return true; s += k; S.mv.v[i] = s; S.mv.src = 'typed'; ui(); return true; }
  if (a === 'mback') { const i = S.mv.act; S.mv.v[i] = S.mv.v[i].slice(0, -1); S.mv.fresh = false; ui(); return true; }
  if (a === 'mok') { measSave(); return true; }
  if (a === 'mdel') { D.meas = measList().filter(m => m.id !== S.selMeas); S.selMeas = null; S.mv = null; commit(); ui(); return true; }
  return false;
}
/* ---------- nokta adları ---------- */
function incName(s) { const m = /^(.*?)(\d+)$/.exec(s); if (!m) return s; const n = String(+m[2] + 1); return m[1] + (m[2].length > n.length ? n.padStart(m[2].length, '0') : n); }
function nameHit(X, Y) { let best = null; nameList().forEach(n => { const s = w2s(...n.p); const d = Math.hypot(s[0] - X, s[1] - Y); if (d < 16 && (!best || d < best.d)) best = { n, d }; }); return best; }
function tagPlace(sn, X, Y) {
  const h = nameHit(X, Y); if (h) { S.selName = h.n.id; ui(); render(); return; }
  if (!(sn.k === 'end' || sn.k === 'int' || sn.k === 'mid' || sn.k === 'near')) { flash(); return; }
  const nm = (S.nameNext || '1').trim() || '1'; const n = { id: 'n' + (D.nid++), n: nm, p: cl(sn.p) }; nameList().push(n); S.nameNext = incName(nm); S.selName = null; S.showNames = true; commit(); ui();
}
function namePanel() {
  if (S.fly || S.tool !== 'tag') return '';
  const n = S.selName && nameList().find(x => x.id === S.selName);
  return `<input id="nmIn" class="nmin ${n ? 'sel' : ''}" value="${(n ? n.n : (S.nameNext || '1')).replace(/"/g, '&quot;')}" autocomplete="off" autocapitalize="characters" spellcheck="false">` + (n ? btn('ndel', 'erase', false, 'dng') : '');
}
function drawNames() {
  if (!S.showNames) return; cx.font = 'bold 12px Arial';
  nameList().forEach(n => { const s = w2s(...n.p), sel = S.selName === n.id; cx.fillStyle = sel ? '#ffd27a' : '#7dffb0'; cx.beginPath(); cx.arc(s[0], s[1], 3.5, 0, TAU); cx.fill(); cx.fillText(n.n, s[0] + 6, s[1] - 6); });
}
/* ---------- lazer: Bosch GLM (v11'den aynen) ---------- */
const GLM_SVC = '02a6c0d0-0451-4000-b000-fb3210111989', GLM_CHR = '02a6c0d1-0451-4000-b000-fb3210111989';
const LZ = { dev: null, chr: null, state: 'yok', name: '', last: null, pend: null, raw: [], n: 0, hb: 0, auto: null, armed: false, wm: '', werr: '' };
const GLM_ON = [0xC0, 0x55, 0x02, 0x01, 0x00, 0x1A], GLM_TRIG = [0xC0, 0x56, 0x01, 0x00, 0x1E];
async function glmWrite(bytes) { const chr = LZ.chr; if (!chr) return false; const v = new Uint8Array(bytes); for (const f of ['writeValueWithResponse', 'writeValue', 'writeValueWithoutResponse']) { if (!chr[f]) continue; try { await chr[f](v); LZ.wm = f; return true; } catch (e) { LZ.werr = String((e && e.message) || e); } } return false; }
function laserParse(dv) { if (!dv || dv.byteLength < 11) return null; const b = i => dv.getUint8(i); if (b(0) !== 0xC0 || b(1) !== 0x55 || b(2) !== 0x10) return null; const v = dv.getFloat32(7, true); return isFinite(v) && v > 0.01 && v < 300 ? v : null; }
function laserValue(m) {
  LZ.last = m; const s = m.toFixed(3);
  if (S.selMeas && S.mv) { S.mv.v[S.mv.act] = s; S.mv.src = 'laser'; laserNext(); }
  else if (MEAS.includes(S.tool) && S.tool !== 'tag' && measDone() && S.mv) { S.mv.v[S.mv.act] = s; S.mv.src = 'laser'; laserNext(); }
  else LZ.pend = m;
  ui(); render();
}
function laserNext() { const two = S.mv.v.length > 1 && (S.tool === 'm_ab' || (S.selMeas && measById(S.selMeas) && measById(S.selMeas).k === 'm_ab')); if (two && S.mv.act === 0) S.mv.act = 1; S.mv.fresh = true; }
async function laserConnect() {
  if (!navigator.bluetooth) { alert('Bu tarayıcı Bluetooth\'a izin vermiyor.\niPhone Safari ve Chrome lazer metreye bağlanamaz (Apple izin vermiyor).\nApp Store\'dan "Bluefy – Web BLE Browser" kur, uygulamayı onda aç: aknergn09-maker.github.io/rolove/cad.html\nDeğeri elle de yazabilirsin.'); return; }
  if (LZ.state === 'bağlı') return;
  try { LZ.state = 'bağlanıyor'; ui(); const dev = await navigator.bluetooth.requestDevice({ filters: [{ namePrefix: 'GLM' }, { namePrefix: 'Bosch' }, { services: [GLM_SVC] }], optionalServices: [GLM_SVC] });
    LZ.dev = dev; LZ.name = dev.name || 'GLM'; dev.addEventListener('gattserverdisconnected', () => { LZ.state = 'koptu'; LZ.chr = null; ui(); setTimeout(() => { if (LZ.dev === dev && LZ.state === 'koptu') laserAttach(dev).catch(() => { LZ.state = 'koptu'; ui(); }); }, 1200); });
    await laserAttach(dev);
  } catch (e) { LZ.state = 'yok'; if (e && e.name !== 'NotFoundError') alert('Lazer bağlanamadı: ' + (e.message || e)); }
  ui();
}
async function laserAttach(dev) {
  LZ.state = 'bağlanıyor'; ui(); const srv = await dev.gatt.connect(); const svc = await srv.getPrimaryService(GLM_SVC); const chr = await svc.getCharacteristic(GLM_CHR); LZ.chr = chr; LZ.armed = false;
  if (!chr._rk) { chr._rk = true; chr.addEventListener('characteristicvaluechanged', e => { const dv = e.target.value;
    const b0 = dv.byteLength > 1 ? dv.getUint8(0) : 0, b1 = dv.byteLength > 1 ? dv.getUint8(1) : 0; if (b0 === 0xC0 && b1 === 0x11) { LZ.hb++; return; }
    LZ.n++; if (b0 === 0xC0 && b1 === 0x55) LZ.armed = true; const v = laserParse(dv); if (v != null) laserValue(v); }); }
  await chr.startNotifications();
  await new Promise(r => setTimeout(r, 250)); LZ.auto = await glmWrite(GLM_ON);
  clearInterval(LZ.rt); let k = 0; LZ.rt = setInterval(() => { if (LZ.armed || !LZ.chr || LZ.state !== 'bağlı' || ++k > 6) { clearInterval(LZ.rt); return; } glmWrite(GLM_ON); }, 2500);
  LZ.state = 'bağlı'; ui();
}
async function laserTrigger() { if (!LZ.chr) { laserConnect(); return; } const a = await glmWrite(GLM_TRIG); await new Promise(r => setTimeout(r, 700)); const b = await glmWrite(GLM_TRIG); if (!(a && b)) flash(); }
/* ---------- DXF: ölçüler (OLCU katmanı) ---------- */
function measDXFLines(nameOf) {
  const out = [];
  measList().forEach(m => {
    const g = measGeo(m), P = m.pts, f3 = v => v == null ? '?' : v.toFixed(3), N = nameOf;
    let txt;
    if (m.k === 'm_pp') txt = `NN ${N(P[0])} ${N(P[1])} ${f3(m.v)}`; else if (m.k === 'm_g') txt = `GN ${N(P[0])} ${N(P[1])} ${f3(m.v)}`;
    else if (m.k === 'm_obj') txt = `OB ${N(P[0])} ${N(P[1])} ${f3(m.v)}`; else if (m.k === 'm_pl') txt = `ND ${N(P[0])} ${N(P[1])}-${N(P[2])} ${f3(m.v)}`;
    else if (m.k === 'm_ll') txt = `CC ${N(P[0])}-${N(P[1])} ${N(P[2])}-${N(P[3])} ${f3(m.v)}`; else txt = `DA ${N(P[0])} ${N(P[1])} ${N(P[2])} ${f3(m.v)} ${f3(m.v2)}`;
    out.push({ cat: MCAT(m.k), lines: g.raw || g.lines, txt, at: g.labels[0][0], src: m.src, pts: m.k === 'm_ll' ? [] : P.filter((_, i) => !(m.k === 'm_pl' && i > 0)) });
  });
  return out;
}
