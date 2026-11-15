import os, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
URL = (ROOT / os.environ.get('PAGE', 'index.html')).as_uri()
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
        # 4x3 oda, 30 cm duvar (dışa); x=0..4, y=0..3
        await ev("""(()=>{const P=RK.P; const C=[[0,0],[4,0],[4,3],[0,3]]; const ids=C.map(([x,y],i)=>{const id='q'+i; P.nodes.push({id,x,y}); return id}); for(let i=0;i<4;i++) P.lines.push({id:'l'+i,a:ids[i],b:ids[(i+1)%4],kind:'typed'}); P.walls.push({id:'W1',nodes:ids,closed:true,t:0.3,side:1}); RK.commit(); RK.view.s=60; RK.view.ox=60; RK.view.oy=300; RK.commit();})()""")
        await btn('#tools button[data-tool=duvar]')
        # aks: sağ duvar aksı x=4.15
        q = await ev("RK.w2s(4.15+0.05, 0.9)"); c = await ev(f"RK.candidate({q[0]},{q[1]},{{}})")
        w = await ev(f"RK.s2w({c['X']},{c['Y']})")
        ck('iç duvarın aksı yakalanır (x=4.15)', c.get('lab')=='Aks' and abs(w[0]-4.15)<1e-6, [c, w])
        q = await ev("RK.w2s(4.15, 3.15)"); c = await ev(f"RK.candidate({q[0]+3},{q[1]+2},{{}})"); w = await ev(f"RK.s2w({c['X']},{c['Y']})")
        ck('kapalı duvar köşesinde aks–aks noktası verilmez', c.get('lab') not in ('Aks ucu','Aks kesişimi'), [c,w])
        # dışarıdan (2,5) başla, aşağı doğru üst duvarın aksına dik otur
        q = await ev("RK.w2s(2, 4.8)"); await ctap(q[0], q[1])
        q = await ev("RK.w2s(2.02, 3.13)"); c = await ev(f"RK.candidate({q[0]},{q[1]},{{fromId: RK.S.chain.last}})"); w = await ev(f"RK.s2w({c['X']},{c['Y']})")
        ck('orto yönünde aksa dik oturur', c.get('lab')=='Aksa dik' and abs(w[1]-3.15)<1e-6 and abs(w[0]-2)<1e-6, [c, w])
        q = await ev("RK.w2s(2.03, 3.32)"); c = await ev(f"RK.candidate({q[0]},{q[1]},{{fromId: RK.S.chain.last}})"); w = await ev(f"RK.s2w({c['X']},{c['Y']})")
        ck('orto yönünde duvar dış yüzüne dik oturur', c['type']=='perp' and abs(w[1]-3.3)<1e-6, [c, w])
        await btn('#sheet button[data-a=end]')
        # gerçek çizgiye dik: sol duvar çizgisine (x=0) soldan gel
        await btn('#tools button[data-tool=cizgi]')
        q = await ev("RK.w2s(-1.0, 1.2)"); await ctap(q[0], q[1])
        q = await ev("RK.w2s(-0.27, 1.21)"); c = await ev(f"RK.candidate({q[0]},{q[1]},{{fromId: RK.S.chain.last}})"); w = await ev(f"RK.s2w({c['X']},{c['Y']})")
        ck('çizgi aracında duvar dış yüzüne dik oturur', c['type'] in ('perp',) and abs(w[0]-(-0.3))<1e-6, [c, w])
        # duvarsız gerçek çizgiye dik: yeni serbest çizgi y=-2 boyunca
        await btn('#sheet button[data-a=end]')
        await ev("""(()=>{const P=RK.P; P.nodes.push({id:'z1',x:0,y:-2},{id:'z2',x:4,y:-2}); P.lines.push({id:'zl',a:'z1',b:'z2',kind:'typed'}); RK.commit();})()""")
        await ev("RK.view.oy=120; RK.commit()"); q = await ev("RK.w2s(2.5, -3.2)"); await ctap(q[0], q[1])
        q = await ev("RK.w2s(2.53, -2.06)"); c = await ev(f"RK.candidate({q[0]},{q[1]},{{fromId: RK.S.chain.last}})")
        await ev(f"(()=>{{}})()"); r = await ev("RK.w2s(2.53,-2.06)")
        await ctap(r[0], r[1])
        nn = await ev("(()=>{const n=RK.P.nodes.find(x=>x.id===RK.S.chain.last); return [+n.x.toFixed(6),+n.y.toFixed(6), RK.P.lines.filter(l=>l.a===n.id||l.b===n.id).length]})()")
        ck('çizgiye dik düşer ve T bağlanır (çizgi bölünür)', c['type']=='perp' and nn[1]==-2 and abs(nn[0]-2.5)<1e-6 and nn[2]==3, [c, nn])
        ck('JS hatası yok', not errs, errs[:3]); await pg.screenshot(path='a1.png'); await b.close()
    print('TOPLAM', sum(R), '/', len(R)); sys.exit(0 if all(R) else 1)
asyncio.run(main())
