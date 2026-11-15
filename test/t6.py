import os, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
URL = (ROOT / 'index.html').as_uri()
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
            await pg.touchscreen.tap(r[0], r[1]); await pg.wait_for_timeout(70); return True
        async def ctap(x,y):
            r = await ev("(()=>{const r=document.querySelector('#cv').getBoundingClientRect(); return [r.left,r.top]})()"); await pg.touchscreen.tap(r[0]+x, r[1]+y); await pg.wait_for_timeout(80)
        # A odası 0..4 x 0..3, 30 cm duvar dışa (sağ dış yüz x=4.3)
        await ev("""(()=>{const P=RK.P; const C=[[0,0],[4,0],[4,3],[0,3]]; const ids=C.map(([x,y],i)=>{const id='q'+i; P.nodes.push({id,x,y}); return id}); for(let i=0;i<4;i++) P.lines.push({id:'l'+i,a:ids[i],b:ids[(i+1)%4],kind:'typed'}); P.walls.push({id:'W1',nodes:ids,closed:true,t:0.3,side:1}); RK.commit(); RK.view.s=150; RK.view.ox=-380; RK.view.oy=300; RK.commit();})()""")
        await btn('#tools button[data-tool=duvar]')
        for (yy, nm) in ((0,'alt'), (3,'üst')):
            q = await ev(f"RK.w2s(4.3+0.03,{yy}-0.04)"); c = await ev(f"RK.candidate({q[0]},{q[1]},{{}})"); w = await ev(f"RK.s2w({c['X']},{c['Y']})")
            ck(f'oda {nm} çizgisinin uzantısı ile duvar dış yüzü kesişimi', c.get('lab')=='Uzantı kesişimi' and abs(w[0]-4.3)<1e-6 and abs(w[1]-yy)<1e-6, [c.get('lab'), w])
        # oraya dokun → B odasını çiz: sağa 3, yukarı 3, sola (dış yüze dik)
        q = await ev("RK.w2s(4.3,0)"); await ctap(q[0]+2, q[1]+2)
        st = await ev("(()=>{const n=RK.P.nodes.find(x=>x.id===RK.S.chain.first); return [+n.x.toFixed(6),+n.y.toFixed(6)]})()")
        ck('dokununca nokta tam kesişimde', st==[4.3,0], st)
        # aks hiç uzatılmıyor: aks (x=4.15) ile alt çizgi uzantısı y=0 → (4.15,0) aks kesişimi verilmesin
        q = await ev("RK.w2s(4.15,-0.02)"); c = await ev(f"RK.candidate({q[0]},{q[1]},{{}})")
        ck('aksın uzantısı ile kesişim verilmez', not (c.get('lab') in ('Aks kesişimi',) ), c)
        await pg.screenshot(path='a3.png')
        ck('JS hatası yok', not errs, errs[:3]); await b.close()
    print('TOPLAM', sum(R), '/', len(R)); sys.exit(0 if all(R) else 1)
asyncio.run(main())
