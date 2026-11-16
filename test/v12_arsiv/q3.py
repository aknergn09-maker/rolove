# v12: duvar yüzündeki T düğümü, çelişen uzun ölçüde yüzde kalır
import asyncio, pathlib, json, sys
from playwright.async_api import async_playwright
import os
PAGE=os.environ.get('PAGE','onizleme.html')
R=[]
def ck(n,ok,i=''): R.append(bool(ok)); print(('PASS ' if ok else 'FAIL ')+n, i if not ok else '')
async def main():
  async with async_playwright() as p:
    b=await p.chromium.launch(args=['--no-sandbox']); ctx=await b.new_context(**p.devices['iPhone 13']); pg=await ctx.new_page(); ev=pg.evaluate
    errs=[]; pg.on('pageerror', lambda e: errs.append(str(e)))
    await pg.goto((pathlib.Path(__file__).resolve().parent.parent/PAGE).as_uri()); await ev("localStorage.clear()"); await pg.reload(); await pg.wait_for_timeout(300)
    async def btn(sel):
      r = await ev(f"(()=>{{const e=document.querySelector('{sel}'); if(!e||e.disabled) return null; const r=e.getBoundingClientRect(); return [r.left+r.width/2, r.top+r.height/2]}})()")
      if not r: return False
      await pg.touchscreen.tap(r[0], r[1]); await pg.wait_for_timeout(90); return True
    async def ctap(x,y):
      r = await ev("(()=>{const r=document.querySelector('#cv').getBoundingClientRect(); return [r.left,r.top]})()"); q = await ev(f"RK.w2s({x},{y})"); await pg.touchscreen.tap(r[0]+q[0], r[1]+q[1]); await pg.wait_for_timeout(200)
    await ev("RK.view.s=40; RK.view.ox=60; RK.view.oy=290; RK.commit()")
    await btn('#tabs button[data-tab=cizim]'); await btn('#cats button[data-cat=ciz]'); await btn('#tools button[data-tool=duvar]')
    for x,y in [(0,0),(6,0),(6,4),(0,4),(0,0)]: await ctap(x,y)
    await btn('#tools button[data-tool=cizgi]')
    for x,y in [(3,0),(3,4)]: await ctap(x,y)
    await btn('#sheet button[data-a=done]')
    INFO = """(()=>{const P=RK.P; return {lines:P.lines.map(l=>{const a=P.nodes.find(n=>n.id===l.a),b=P.nodes.find(n=>n.id===l.b);return [l.id,+a.x.toFixed(3),+a.y.toFixed(3),+b.x.toFixed(3),+b.y.toFixed(3)]}), rooms:P.rooms.filter(r=>!r.kind).map(r=>+RK.rA(r).toFixed(3)), offs:(P.offs||[]).length, wq:(P.wq||[]).length, walls:(P.walls||[]).length}})()"""
    # ölç: partisyon (x=3) çizgisini 4.5 yap ; sonra iç alt çizgiyi
    for desc, sel, m in [('sol iç duvar 4.0', "l=>{const a=RK.P.nodes.find(n=>n.id===l.a),b=RK.P.nodes.find(n=>n.id===l.b);return Math.abs(a.x)<0.01&&Math.abs(b.x)<0.01}", 4.0), ('sağ iç duvar 4.0', "l=>{const a=RK.P.nodes.find(n=>n.id===l.a),b=RK.P.nodes.find(n=>n.id===l.b);return Math.abs(a.x-6)<0.01&&Math.abs(b.x-6)<0.01}", 4.0), ('partisyon 4.5', "l=>{const a=RK.P.nodes.find(n=>n.id===l.a),b=RK.P.nodes.find(n=>n.id===l.b);return Math.abs(a.x-3)<0.01&&Math.abs(b.x-3)<0.01}", 4.5)]:
      r = await ev(f"(()=>{{const ls=RK.P.lines.filter({sel}); if(!ls.length) return 'yok'; RK.applyMeasure(ls[0], {m}); return document.querySelector('#toast').textContent}})()")
      last=r
    bad = await ev("""(()=>{const P=RK.P; const out=[]; P.wq.forEach(q=>[[0,1],[3,2]].forEach(([s0,s1])=>{const A=P.nodes.find(n=>n.id===q.n[s0]),B=P.nodes.find(n=>n.id===q.n[s1]); P.nodes.forEach(n=>{if(n===A||n===B) return; const dx=B.x-A.x,dy=B.y-A.y,L=Math.hypot(dx,dy); const t=((n.x-A.x)*dx+(n.y-A.y)*dy)/L/L; if(t<=0.01||t>=0.99) return; const d=((n.x-A.x)*dy-(n.y-A.y)*dx)/L; if(Math.abs(d)>1e-6&&Math.abs(d)<0.05) out.push([n.id,d.toFixed(4)])})})); return out})()""")
    ck('çelişen uzun ölçü: T düğümü duvar yüzünde kaldı (dış çizginin dışına taşmadı)', not bad, bad)
    ck('  çelişki kullanıcıya uyarıldı', 'çelişiyor' in last, last)
    ck('JS hatası yok', not errs, errs[:2])
    print('TOPLAM', sum(R), '/', len(R)); sys.exit(0 if all(R) else 1)
    await b.close()
asyncio.run(main())
