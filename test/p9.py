# ÖNİZLEME: lazer ölçeklemede oda içindeki objeler (eleman, merdiven çerçevesi, iç detay) odayla birlikte kayar
import os, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
URL = (ROOT / os.environ.get('PAGE', 'onizleme.html')).as_uri()
OUT = ROOT / 'test' / 'out'; OUT.mkdir(exist_ok=True); os.chdir(OUT)
CHROME = os.environ.get('CHROME', '/usr/bin/google-chrome' if os.path.exists('/usr/bin/google-chrome') else None)
import asyncio, sys
from playwright.async_api import async_playwright
R=[]
def ck(n,ok,i=''): R.append(bool(ok)); print(('PASS ' if ok else 'FAIL ')+n, i if not ok else '')
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path=CHROME, args=['--no-sandbox'])
        ctx=await b.new_context(**p.devices['iPhone 13']); pg=await ctx.new_page(); errs=[]
        pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto(URL); await pg.evaluate("localStorage.clear()"); await pg.reload(); await pg.wait_for_timeout(300); ev=pg.evaluate
        async def btn(sel):
            r = await ev(f"(()=>{{const e=document.querySelector('{sel}'); if(!e||e.disabled) return null; const r=e.getBoundingClientRect(); return [r.left+r.width/2, r.top+r.height/2]}})()")
            if not r: return False
            await pg.touchscreen.tap(r[0], r[1]); await pg.wait_for_timeout(80); return True
        async def ctap(x,y):
            r = await ev("(()=>{const r=document.querySelector('#cv').getBoundingClientRect(); return [r.left,r.top]})()"); await pg.touchscreen.tap(r[0]+x, r[1]+y); await pg.wait_for_timeout(100)
        async def W(x,y): return await ev(f"RK.w2s({x},{y})")
        await ev("""(()=>{const P=RK.P; P.nodes=[];P.lines=[];P.walls=[];P.rooms=[];P.openings=[];
          const sq=(pre,C,closed)=>{const ids=C.map(([x,y],i)=>{const id=pre+i; P.nodes.push({id,x,y}); return id}); for(let i=0;i<(closed?C.length:C.length-1);i++) P.lines.push({id:'L'+pre+i,a:ids[i],b:ids[(i+1)%C.length],kind:'sketch'}); return ids};
          sq('a',[[0,0],[4,0],[4,3],[0,3]],true); sq('e',[[3,2],[3.5,2],[3.5,2.5],[3,2.5]],true); sq('m',[[0.5,0.5],[1.5,0.5],[1.5,2],[0.5,2]],true); sq('d',[[2,1],[2.6,1.4]],false);
          P.rooms.push({id:'rA',name:'Salon',ax:2.5,ay:0.7}); P.rooms.push({id:'rE',name:'Kolon',ax:3.25,ay:2.25,kind:'eleman'}); P.rooms.push({id:'rM',name:'Merdiven',ax:1,ay:1.2,kind:'merdiven'}); RK.commit(); RK.view.s=60; RK.view.ox=60; RK.view.oy=330; RK.commit();})()""")
        a0 = await ev("[+RK.rA(RK.P.rooms[0]).toFixed(3), RK.P.rooms.map(r=>!!r._f)]")
        ck('kurulum: salon 12 − merdiven 1.5 = 10.5, kolon ve merdiven alanı var', a0==[10.5,[True,True,True]], a0)
        if await ev("!!document.querySelector('#tabs')"): await btn('#tabs button[data-tab=olcum]')
        await btn('#tools button[data-tool=olc]')
        q = await W(2, 0); await ctap(*q); await ev("RK.laserValue(5)"); await btn('#sheet button[data-a=msok]')
        rel = await ev("""(()=>{const n=id=>RK.P.nodes.find(q=>q.id===id); const A=n('a0'), C=n('a2'); const W=C.x-A.x, H=C.y-A.y; const c=(ids)=>{const ps=ids.map(n); return [(ps.reduce((s,p)=>s+p.x,0)/ps.length-A.x)/W, (ps.reduce((s,p)=>s+p.y,0)/ps.length-A.y)/H]}; return {W:+W.toFixed(3), H:+H.toFixed(3), e:c(['e0','e1','e2','e3']).map(v=>+v.toFixed(4)), m:c(['m0','m1','m2','m3']).map(v=>+v.toFixed(4)), d:c(['d0','d1']).map(v=>+v.toFixed(4)), es:+(n('e1').x-n('e0').x).toFixed(3)}})()""")
        ck('lazer 5.00: oda 1.25 kat büyüdü (5.00 × 3.75)', rel['W']==5 and rel['H']==3.75, rel)
        ck('  kolon odadaki yerini korudu (merkez oranı 0.8125, 0.75)', rel['e']==[0.8125,0.75], rel['e'])
        ck('  merdiven çerçevesi odadaki yerini korudu (0.25, 0.4167)', rel['m']==[0.25,0.4167], rel['m'])
        ck('  iç detay çizgisi odadaki yerini korudu (0.575, 0.4)', rel['d']==[0.575,0.4], rel['d'])
        ck('  kolon da ölçeklendi (0.50 → 0.625)', rel['es']==0.625, rel['es'])
        a1 = await ev("RK.P.rooms.map(r=>[r.name, r._f? +RK.rA(r).toFixed(4):null])")
        ck('  alanlar: salon 18.75 − merdiven 2.344 = 16.406, merdiven ve kolon hâlâ odanın içinde', [r[0] for r in a1]==['Salon','Kolon','Merdiven'] and all(abs(r[1]-e)<2e-4 for r,e in zip(a1,[16.40625,0.390625,2.34375])), a1)
        await btn('#fFit'); await pg.screenshot(path='p9.png')
        ck('JS hatası yok', not errs, errs[:3]); await b.close()
    print('TOPLAM', sum(R), '/', len(R)); sys.exit(0 if all(R) else 1)
asyncio.run(main())
