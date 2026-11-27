/* ROLEVE GÖNYE — PC arayüzü */
const VERP = 'gonye-1.1';
const $ = s => document.querySelector(s);
const ST = { dxfTxt: null, dxfName: '', totTxt: null, totName: '', M: null, tot: [], R: null };
const OPT = Object.assign({}, G.DEF);
function readFile(f) { return new Promise((ok, no) => { const r = new FileReader(); r.onload = () => { const b = new Uint8Array(r.result); let t; try { t = new TextDecoder('utf-8', { fatal: true }).decode(b); } catch (e) { t = new TextDecoder('windows-1254').decode(b); } ok(t); }; r.onerror = no; r.readAsArrayBuffer(f); }); }
async function takeFiles(files) {
  for (const f of files) { const n = f.name.toLowerCase(), t = await readFile(f);
    if (n.endsWith('.dxf')) { ST.dxfTxt = t; ST.dxfName = f.name; } else { ST.totTxt = t; ST.totName = f.name; } }
  load();
}
function load() {
  ST.R = null; $('#out').innerHTML = ''; $('#dl').style.display = 'none';
  if (ST.dxfTxt) { try { ST.M = G.buildModel(G.parseDXF(ST.dxfTxt)); } catch (e) { ST.M = null; msg('DXF okunamadı: ' + e.message, 'bad'); } }
  ST.tot = ST.totTxt ? G.readTotal(ST.totTxt) : [];
  const M = ST.M; let h = '';
  h += `<div class="f ${ST.dxfTxt ? 'ok' : ''}"><b>Kroki DXF</b> ${ST.dxfName || '<i>bekleniyor</i>'}</div>`;
  h += `<div class="f ${ST.totTxt ? 'ok' : ''}"><b>Total</b> ${ST.totName || '<i>yok (isteğe bağlı)</i>'}${ST.tot.length ? ' · ' + ST.tot.length + ' nokta' : ''}</div>`;
  if (M) { const user = M.list.filter(n => n.user).map(n => n.name), tset = new Set(ST.tot.map(t => t.name)), match = M.list.filter(n => tset.has(n.name)).map(n => n.name);
    h += `<div class="sum">${M.list.length} nokta (${user.length} senin verdiğin) · ${M.segs.length} kroki kenarı · ${M.meas.length} ölçü · ${M.ops.length} kapı/pencere</div>`;
    h += `<div class="sum">Total ile eşleşen: <b>${match.length ? match.length + ' nokta' + (match.length > 12 ? ' (' + match.slice(0, 12).join(', ') + '…)' : ' (' + match.join(', ') + ')') : 'yok'}</b>${user.filter(u => !tset.has(u)).length && ST.tot.length ? ' · totalde bulunmayan adlar: ' + user.filter(u => !tset.has(u)).join(', ') : ''}</div>`;
    if (match.length < 2) h += `<div class="warn">${match.length === 0 ? 'Total ile eşleşen nokta yok: sonuç yerel koordinatta, ölçek ve gönye yine düzeltilir.' : 'Sadece 1 total noktası eşleşti: konum doğru, yön krokideki gibi kalır.'}</div>`;
    if (!M.meas.length) h += `<div class="warn">DXF'te ölçü yok: sadece total noktalarına oturtulur.</div>`; }
  $('#info').innerHTML = h; $('#run').disabled = !M; draw();
}
function msg(t, c) { $('#info').insertAdjacentHTML('beforeend', `<div class="${c || 'warn'}">${t}</div>`); }
function run() {
  if (!ST.M) return; const t0 = performance.now();
  try { ST.R = G.adjust(ST.M, ST.tot, OPT); } catch (e) { msg('Hesap yapılamadı: ' + e.message, 'bad'); return; }
  const R = ST.R, mm = v => (v * 1000).toFixed(1);
  const rows = R.res.filter(r => r.m || r.k === 'TOTAL'); const seen = new Set();
  let h = `<h3>Sonuç</h3><div class="sum">${R.iter} adımda çözüldü (${Math.round(performance.now() - t0)} ms) · kroki ölçeği ×${R.K.toFixed(3)}</div>`;
  h += '<table><tr><th>Tür</th><th>Ölçü</th><th>Girilen</th><th>Düzeltme</th><th></th></tr>';
  const TR = { NN: 'nokta–nokta', OB: 'obje', GN: 'gönye', ND: 'noktadan dik', CC: 'iki duvar arası', 'DA-ayak': 'dik ayak', 'DA-boy': 'dik boy', 'DA-dik': 'dik açı', TOTAL: 'total' };
  rows.forEach(r => { if (r.k === 'TOTAL') { if (seen.has(r.name)) return; seen.add(r.name); return; }
    const isAng = r.k === 'DA-dik', bad = isAng ? Math.abs(r.r) > 1 : Math.abs(r.r) > 0.03, mid = isAng ? Math.abs(r.r) > 0.3 : Math.abs(r.r) > 0.01;
    const val = r.k === 'DA-boy' ? r.m.v2 : r.k === 'DA-dik' ? 90 : r.m.v;
    h += `<tr class="${bad ? 'bad' : mid ? 'mid' : ''}"><td>${TR[r.k] || r.k}</td><td>${r.m.txt.replace(/ L$/, '')}</td><td>${isAng ? '90°' : val.toFixed(3) + ' m'}</td><td>${isAng ? r.r.toFixed(2) + '°' : (-r.r >= 0 ? '+' : '') + mm(-r.r) + ' mm'}</td><td>${bad ? 'kontrol et' : mid ? 'dikkat' : 'iyi'}</td></tr>`; });
  h += '</table>';
  const sqN = R.squared.length, rel = R.released;
  h += `<h3>Gönye</h3><div class="sum"><b>${sqN}</b> köşe tam 90°'ye kırıldı (${OPT.squareTol}°'den yakın olanlar).${rel.length ? ` <b>${rel.length}</b> köşe kırılmadı, çünkü kırınca bir total ${(OPT.maxTot * 100).toFixed(0)} cm'den fazla kayıyor ya da bir ölçü ${(OPT.maxMeas * 100).toFixed(0)} cm'den fazla bozuluyordu: ${rel.map(r => r.v).join(', ')}` : ''}</div>`;
  const ts = R.totShift.slice().sort((a, b) => b.d - a.d);
  if (ts.length) { const med = ts[ts.length >> 1].d; h += `<h3>Totalden kayma</h3><div class="sum">Ortanca ${(med * 100).toFixed(1)} cm · en çok kayanlar: ${ts.slice(0, 8).map(t => `<span class="${t.d > OPT.maxTot ? 'bad' : t.d > OPT.maxTot / 2 ? 'warn' : ''}">${t.name}: ${(t.d * 100).toFixed(1)} cm</span>`).join(' · ')}</div>`;
    const far = ts.filter(t => t.d > OPT.maxTot); if (far.length) h += `<div class="warn">${far.map(t => t.name).join(', ')} krokideki yerinden ${(OPT.maxTot * 100).toFixed(0)} cm'den uzak okunmuş. Krokide doğru duvara/köşeye konduğunu ya da totalin doğru yüzeyden okunduğunu kontrol et.</div>`; }
  const ang = R.res.filter(r => r.k === 'kroki-aci').sort((a, b) => Math.abs(b.r) - Math.abs(a.r)).slice(0, 8);
  if (ang.length) h += '<h3>Krokiye göre en çok düzelen köşeler</h3><div class="sum">' + ang.map(r => `${r.v}: ${(-r.r).toFixed(2)}°`).join(' · ') + '</div>';
  if (R.unmatchedTotals.length) h += `<div class="sum">Krokide olmayan total noktaları DXF'e ayrı katmanda (TOTAL_DIGER) eklenir: ${R.unmatchedTotals.slice(0, 30).join(', ')}${R.unmatchedTotals.length > 30 ? '…' : ''}</div>`;
  $('#out').innerHTML = h; $('#dl').style.display = 'flex'; draw();
}
function download(text, name, type) { const a = document.createElement('a'); a.href = URL.createObjectURL(new Blob([text], { type })); a.download = name; document.body.appendChild(a); a.click(); a.remove(); }
function baseName() { return (ST.dxfName || 'kroki').replace(/\.dxf$/i, ''); }
/* önizleme */
function draw() {
  const cv = $('#cv'), r = cv.getBoundingClientRect(), dpr = devicePixelRatio || 1; cv.width = r.width * dpr; cv.height = r.height * dpr; const c = cv.getContext('2d'); c.setTransform(dpr, 0, 0, dpr, 0, 0); c.fillStyle = '#121417'; c.fillRect(0, 0, r.width, r.height);
  const M = ST.M; if (!M) return; const R = ST.R, P = n => R ? R.coords[n] : M.names[n].sk;
  const pts = M.list.map(n => P(n.name)).filter(Boolean); if (!pts.length) return;
  const key = (R ? 'R' : 'S') + M.list.length;
  if (!VW || VW.key !== key) { const xs = pts.map(p => p[0]), ys = pts.map(p => p[1]), x0 = Math.min(...xs), x1 = Math.max(...xs), y0 = Math.min(...ys), y1 = Math.max(...ys);
    const s0 = Math.min((r.width - 40) / Math.max(x1 - x0, 0.5), (r.height - 40) / Math.max(y1 - y0, 0.5)); VW = { key, s: s0, cx: (x0 + x1) / 2, cy: (y0 + y1) / 2 }; }
  const s = VW.s, w = p => [r.width / 2 + (p[0] - VW.cx) * s, r.height / 2 - (p[1] - VW.cy) * s];
  c.strokeStyle = '#e8e8e8'; c.lineWidth = 1.4; M.drawn.forEach(d => { const q = d.ns.map(n => n && P(n)); if (q.some(x => !x)) return; c.beginPath(); q.forEach((p, i) => { const a = w(p); if (i) c.lineTo(...a); else c.moveTo(...a); }); if (d.c) c.closePath(); c.stroke(); });
  const resOf = m => R ? R.res.filter(x => x.m === m) : [];
  M.meas.forEach(m => { const bad = resOf(m).some(x => x.k === 'DA-dik' ? Math.abs(x.r) > 1 : Math.abs(x.r) > 0.03), mid = resOf(m).some(x => x.k === 'DA-dik' ? Math.abs(x.r) > 0.3 : Math.abs(x.r) > 0.01);
    c.strokeStyle = !R ? (m.k === 'GN' ? '#5aa9ff' : m.k === 'DA' ? '#c08bff' : '#f5a623') : bad ? '#ff5d5d' : mid ? '#ffcf70' : '#4cd964'; c.setLineDash([6, 4]); c.lineWidth = 1.2; c.beginPath();
    const seg = (a, b) => { if (!P(a) || !P(b)) return; c.moveTo(...w(P(a))); c.lineTo(...w(P(b))); };
    if (m.k === 'DA') { seg(m.o, m.f); seg(m.f, m.c); } else if (m.a && m.b && m.k !== 'CC') seg(m.a, m.b); c.stroke(); c.setLineDash([]); });
  if (R) { const sq = new Set(R.squared.map(q => q.v)); R.res.filter(x => x.k === 'kroki-aci').forEach(x => { const p = P(x.v); if (!p) return; const a = w(p); const isSq = sq.has(x.v); if (isSq) { c.strokeStyle = '#4cd964'; c.lineWidth = 1; c.strokeRect(a[0] - 3, a[1] - 3, 6, 6); } }); R.released.forEach(q => { const p = P(q.v); if (!p) return; const a = w(p); c.strokeStyle = '#ffb347'; c.lineWidth = 2; c.beginPath(); c.arc(a[0], a[1], 6, 0, Math.PI * 2); c.stroke(); }); }
  c.font = '11px Arial'; M.list.forEach(n => { const p = P(n.name); if (!p) return; const a = w(p), tot = R && R.matched.includes(n.name); c.fillStyle = tot ? '#5aa9ff' : n.user ? '#7dffb0' : '#8a929c'; c.beginPath(); c.arc(a[0], a[1], tot ? 4 : 2.5, 0, Math.PI * 2); c.fill(); if (n.user || tot) c.fillText(n.name, a[0] + 5, a[1] - 5); });
  if (R) { c.strokeStyle = '#5aa9ff'; ST.tot.filter(t => !R.coords[t.name]).forEach(t => { const a = w(t.p); c.beginPath(); c.moveTo(a[0], a[1] - 5); c.lineTo(a[0] + 4.5, a[1] + 3); c.lineTo(a[0] - 4.5, a[1] + 3); c.closePath(); c.stroke(); }); }
}
let VW = null;
/* önizleme: tekerlek = yakınlaştır, sürükle = kaydır */
(() => { const cv = $('#cv'); let dr = null;
  cv.addEventListener('wheel', e => { if (!VW) return; e.preventDefault(); const r = cv.getBoundingClientRect(), k = Math.exp(-e.deltaY * 0.0015); const mx = (e.clientX - r.left - r.width / 2) / VW.s + VW.cx, my = -(e.clientY - r.top - r.height / 2) / VW.s + VW.cy; VW.s *= k; VW.cx = mx - (e.clientX - r.left - r.width / 2) / VW.s; VW.cy = my + (e.clientY - r.top - r.height / 2) / VW.s; draw(); }, { passive: false });
  cv.addEventListener('pointerdown', e => { if (VW) { dr = { x: e.clientX, y: e.clientY, cx: VW.cx, cy: VW.cy }; cv.setPointerCapture(e.pointerId); } });
  cv.addEventListener('pointermove', e => { if (!dr) return; VW.cx = dr.cx - (e.clientX - dr.x) / VW.s; VW.cy = dr.cy + (e.clientY - dr.y) / VW.s; draw(); });
  cv.addEventListener('pointerup', () => { dr = null; }); cv.addEventListener('dblclick', () => { VW = null; draw(); }); })();
/* olaylar */
document.addEventListener('dragover', e => { e.preventDefault(); $('#drop').classList.add('on'); });
document.addEventListener('dragleave', e => { if (e.target === document.documentElement || e.target === document.body) $('#drop').classList.remove('on'); });
document.addEventListener('drop', e => { e.preventDefault(); $('#drop').classList.remove('on'); takeFiles([...e.dataTransfer.files]); });
$('#pick').addEventListener('change', e => { takeFiles([...e.target.files]); e.target.value = ''; });
$('#run').addEventListener('click', run);
$('#dxf').addEventListener('click', () => ST.R && download(G.outputDXF(ST.M, ST.R, ST.tot), baseName() + '_gonye.dxf', 'application/dxf'));
$('#csv').addEventListener('click', () => ST.R && download(G.coordCSV(ST.M, ST.R), baseName() + '_koordinat.csv', 'text/csv'));
const SETS = [['squareTol', 'Gönyeye kırma sınırı (°, 0 = kapalı)'], ['sTotal', 'Total payı (m)'], ['maxTot', 'Total en çok kayma (m)'], ['maxMeas', 'Ölçü en çok bozulma (m)'], ['sLaser', 'Lazer ölçüsü (m)'], ['sTyped', 'Elle yazılan ölçü (m)'], ['sAngle', 'Kroki köşe açısı (°)'], ['sStraight', 'Düz duvar (°)'], ['sLenRel', 'Kroki boy oranı'], ['sRight', 'Dik ayak dik açısı (°)']];
$('#sets').innerHTML = SETS.map(([k, t]) => `<label>${t}<input type="number" step="any" data-k="${k}" value="${OPT[k]}"></label>`).join('');
$('#sets').addEventListener('input', e => { const k = e.target.dataset.k; const v = parseFloat(e.target.value); if (k && (v > 0 || (k === 'squareTol' && v === 0))) OPT[k] = v; });
addEventListener('resize', draw);
$('#ver').textContent = VERP; load();
window.GN = { ST, run, load, takeFiles, G };
