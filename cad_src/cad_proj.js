/* ROLEVE CAD — krokiler (işler), otomatik ara kayıtlar, dış yedek */
const PIDX = 'rcad1_idx', PKEY = id => 'rcad1_p_' + id, SKEY = id => 'rcad1_s_' + id;
let IDX = null;
function lsGet(k) { try { return JSON.parse(localStorage.getItem(k) || 'null'); } catch (e) { return null; } }
function lsSet(k, v) {
  const s = JSON.stringify(v);
  for (let t = 0; t < 4; t++) { try { localStorage.setItem(k, s); return true; } catch (e) { if (!trimSnaps()) break; } }
  return false;
}
function trimSnaps() { /* yer kalmadıysa en eski ara kayıtları sil */ let did = false; (IDX ? IDX.list : []).forEach(p => { const a = lsGet(SKEY(p.id)); if (a && a.length > 2) { a.splice(0, Math.ceil(a.length / 2)); try { localStorage.setItem(SKEY(p.id), JSON.stringify(a)); did = true; } catch (e) { } } }); return did; }
function newId() { return 'k' + Date.now().toString(36) + Math.random().toString(36).slice(2, 6); }
function projLoadIdx(legacyD, legacyView) {
  IDX = lsGet(PIDX);
  if (!IDX || !IDX.list || !IDX.list.length) {
    const id = newId(); IDX = { cur: id, list: [{ id, name: 'Kroki 1', ts: Date.now(), n: legacyD ? (legacyD.ents || []).length : 0 }], bk: 0 };
    lsSet(PKEY(id), { D: legacyD || { ents: [], nid: 1 }, view: legacyView || null }); lsSet(PIDX, IDX);
  }
  if (!IDX.list.some(p => p.id === IDX.cur)) IDX.cur = IDX.list[0].id;
  const o = lsGet(PKEY(IDX.cur)) || { D: { ents: [], nid: 1 }, view: null };
  const sn = lsGet(SKEY(IDX.cur)); if ((!sn || !sn.length) && o.D && (o.D.ents || []).length) lsSet(SKEY(IDX.cur), [{ ts: Date.now(), D: o.D }]);
  return o;
}
function projCur() { return IDX && IDX.list.find(p => p.id === IDX.cur); }
function projSave(Dd, v) {
  if (!IDX) return; const p = projCur(); if (!p) return; p.ts = Date.now(); p.n = Dd.ents.length;
  lsSet(PKEY(p.id), { D: Dd, view: v }); lsSet(PIDX, IDX);
  const sn = lsGet(SKEY(p.id)) || []; const last = sn[sn.length - 1];
  if (Dd.ents.length && (!last || Date.now() - last.ts > 10 * 60 * 1000)) { sn.push({ ts: Date.now(), D: Dd }); while (sn.length > 12) sn.shift(); lsSet(SKEY(p.id), sn); }
}
function projSwitch(id) {
  save(); const o = lsGet(PKEY(id)); if (!o) return; IDX.cur = id; lsSet(PIDX, IDX);
  D = o.D; D.ops = D.ops || []; D.meas = D.meas || []; D.names = D.names || []; D.notes = D.notes || []; hist = [JSON.stringify(D)]; hi = 0; invalidate();
  { const sn = lsGet(SKEY(id)); if ((!sn || !sn.length) && D.ents.length) lsSet(SKEY(id), [{ ts: Date.now(), D }]); }
  S.sel.clear(); S.selOp = null; S.selMeas = null; S.selName = null; S.selNote = null; S.chain = null; S.mq = null; S.mv = null;
  if (o.view) view = o.view; else fit(); ui(); render();
}
function projNew(name, Dd) {
  save(); const id = newId(); const nm = name || ('Kroki ' + (IDX.list.length + 1)); IDX.list.unshift({ id, name: nm, ts: Date.now(), n: Dd ? Dd.ents.length : 0 });
  lsSet(PKEY(id), { D: Dd || { ents: [], nid: 1 }, view: null }); lsSet(PIDX, IDX); projSwitch(id); if (!Dd) fit();
}
function projDelete(id) {
  IDX.list = IDX.list.filter(p => p.id !== id); try { localStorage.removeItem(PKEY(id)); localStorage.removeItem(SKEY(id)); } catch (e) { }
  if (!IDX.list.length) { projNew('Kroki 1'); return; }
  if (IDX.cur === id) { IDX.cur = null; const nx = IDX.list.slice().sort((a, b) => b.ts - a.ts)[0]; IDX.cur = nx.id; lsSet(PIDX, IDX); const o = lsGet(PKEY(nx.id)); D = o.D; hist = [JSON.stringify(D)]; hi = 0; invalidate(); if (o.view) view = o.view; }
  lsSet(PIDX, IDX); ui(); render();
}
function fmtT(ts) { const d = new Date(ts), z = v => String(v).padStart(2, '0'); return `${z(d.getDate())}.${z(d.getMonth() + 1)} ${z(d.getHours())}:${z(d.getMinutes())}`; }
const esc = s => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/"/g, '&quot;');
function backupOld() { return IDX && IDX.list.some(p => p.n) && Date.now() - (IDX.bk || 0) > 3 * 24 * 3600 * 1000; }
function projPanel() {
  if (S.fly !== 'proj') return ''; const cur = projCur();
  let h = `<div class="pph"><input id="ppName" value="${esc(cur ? cur.name : '')}" autocomplete="off" spellcheck="false">${btn('pnew', 'newdoc')}${btn('pdup', 'copy')}</div><div class="ppl">`;
  IDX.list.slice().sort((a, b) => b.ts - a.ts).forEach(p => { const on = p.id === IDX.cur, armed = S.parm === p.id && S.arm > Date.now();
    h += `<div class="ppi ${on ? 'on' : ''}"><button class="ppo" data-a="popen:${p.id}"><b>${esc(p.name)}</b><span>${fmtT(p.ts)} · ${p.n} obje</span></button>${on ? '' : btn('pdel:' + p.id, 'erase', false, armed ? 'dng' : '')}</div>`; });
  h += '</div>';
  const sn = (cur && lsGet(SKEY(cur.id))) || [];
  if (sn.length) h += '<div class="pps">Önceki halleri</div><div class="ppv">' + sn.slice().reverse().map((s, i) => `<button data-a="psnap:${sn.length - 1 - i}">${fmtT(s.ts)} · ${s.D.ents.length}</button>`).join('') + '</div>';
  h += `<div class="ppb"><button class="pbk ${backupOld() ? 'old' : ''}" data-a="bkout">Yedek al</button><button class="pbk" data-a="bkin">Yedekten yükle</button></div><div class="pps">${IDX.bk ? 'Son yedek: ' + fmtT(IDX.bk) : 'Henüz yedek alınmadı'}</div>`;
  return h;
}
function projBtn(a) {
  if (a === 'proj') { S.fly = S.fly === 'proj' ? null : 'proj'; ui(); return true; }
  if (a === 'pnew') { projNew(); S.fly = 'proj'; ui(); return true; }
  if (a === 'pdup') { const cur = projCur(); projNew(cur.name + ' (kopya)', JSON.parse(JSON.stringify(D))); S.fly = 'proj'; ui(); return true; }
  if (a.startsWith('popen:')) { projSwitch(a.slice(6)); S.fly = null; ui(); return true; }
  if (a.startsWith('pdel:')) { const id = a.slice(5); if (S.parm === id && S.arm > Date.now()) { S.arm = 0; S.parm = null; projDelete(id); S.fly = 'proj'; } else { S.parm = id; S.arm = Date.now() + 3000; setTimeout(ui, 3100); } ui(); return true; }
  if (a.startsWith('psnap:')) { const sn = lsGet(SKEY(IDX.cur)) || [], s = sn[+a.slice(6)]; if (s) { D = JSON.parse(JSON.stringify(s.D)); D.ops = D.ops || []; D.meas = D.meas || []; D.names = D.names || []; D.notes = D.notes || []; S.sel.clear(); commit(); fit(); flashOk(D.ents.map(e => e.id), false); } S.fly = null; ui(); return true; }
  if (a === 'bkout') { backupOut(); return true; }
  if (a === 'bkin') { S.fly = null; ui(); document.getElementById('bkIn').click(); return true; }
  return false;
}
function backupOut() {
  save(); const d = new Date(), z = v => String(v).padStart(2, '0');
  const data = { app: 'roleve-cad', v: 1, ts: Date.now(), projects: IDX.list.map(p => ({ id: p.id, name: p.name, ts: p.ts, ...(lsGet(PKEY(p.id)) || {}) })) };
  const n = `kroki_yedek_${d.getFullYear()}${z(d.getMonth() + 1)}${z(d.getDate())}_${z(d.getHours())}${z(d.getMinutes())}.json`;
  window._lastBackup = data; window._lastBackupName = n;
  shareOrDownload(JSON.stringify(data), n, 'application/json').then(ok => { if (ok) { IDX.bk = Date.now(); lsSet(PIDX, IDX); ui(); } });
}
function backupIn(txt) {
  let data; try { data = JSON.parse(txt); } catch (e) { flash(); return 0; }
  if (!data || data.app !== 'roleve-cad' || !Array.isArray(data.projects)) { flash(); return 0; }
  save(); let added = 0;
  data.projects.forEach(p => { if (!p.D) return; const ex = IDX.list.find(q => q.id === p.id); const exD = ex && lsGet(PKEY(ex.id));
    if (ex && exD && JSON.stringify(exD.D) === JSON.stringify(p.D)) return;
    const id = newId(), name = IDX.list.some(q => q.name === p.name) ? p.name + ' (yedek)' : p.name;
    IDX.list.push({ id, name, ts: p.ts || Date.now(), n: (p.D.ents || []).length }); lsSet(PKEY(id), { D: p.D, view: p.view || null }); added++; });
  lsSet(PIDX, IDX); S.fly = 'proj'; ui(); return added;
}
function projName() { const p = projCur(); return p ? p.name : 'kroki'; }
