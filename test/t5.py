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
        await ev("""(()=>{const P=RK.P; const C=[[0,0],[4,0],[4,3],[0,3]]; const ids=C.map(([x,y],i)=>{const id='q'+i; P.nodes.push({id,x,y}); return id}); for(let i=0;i<4;i++) P.lines.push({id:'l'+i,a:ids[i],b:ids[(i+1)%4],kind:'typed'}); P.walls.push({id:'W1',nodes:ids,closed:true,t:0.3,side:1});
          P.nodes.push({id:'m1',x:2,y:0},{id:'m2',x:2,y:3}); P.lines=P.lines.filter(l=>l.id!=='l0'&&l.id!=='l2'); P.lines.push({id:'a1',a:'q0',b:'m1',kind:'typed'},{id:'a2',a:'m1',b:'q1',kind:'typed'},{id:'b1',a:'q2',b:'m2',kind:'typed'},{id:'b2',a:'m2',b:'q3',kind:'typed'},{id:'mm',a:'m1',b:'m2',kind:'typed'});
          P.walls[0].nodes=['q0','m1','q1','q2','m2','q3']; P.walls.push({id:'W2',nodes:['m1','m2'],closed:false,t:0.2,side:1}); RK.commit(); RK.view.s=200; RK.view.ox=-150; RK.view.oy=250; RK.commit();})()""")
        await btn('#tools button[data-tool=duvar]')
        axx = await ev("(()=>{const a=RK.P.walls[1]; return a.side})()")
        X = 1.9 if axx==1 else 2.1
        # aks ile iç çizgi (y=0) kesişimi → gerçek çizgi bölünür
        q = await ev(f"RK.w2s({X}+0.04,0.05)"); c = await ev(f"RK.candidate({q[0]},{q[1]},{{}})"); w = await ev(f"RK.s2w({c['X']},{c['Y']})")
        ck('aks ile oda çizgisi kesişimi yakalanır', c['type'] in ('int','end') and abs(w[0]-X)<1e-6 and abs(w[1])<1e-6, [c, w])
        nl = await ev("RK.P.lines.length"); await ctap(c['X'], c['Y'])
        n = await ev("(()=>{const n=RK.P.nodes.find(x=>x.id===RK.S.chain.first); return [+n.x.toFixed(6), +n.y.toFixed(6), RK.P.lines.filter(l=>l.a===n.id||l.b===n.id).length]})()")
        ck('  oraya dokununca nokta çizgi üstünde, çizgi bölündü', n[:2]==[X,0] and n[2]==2 and await ev("RK.P.lines.length")==nl+1, [n, nl, await ev("RK.P.lines.length")])
        await btn('#sheet button[data-a=end]')
        # iki duvar yüzünün kesişimi (iç duvar yüzü x=1.8 ile dış duvarın iç... ) dış yüz y=3.3 ile iç duvar yüzü uzantısı yok → yüz-yüz: W1 dış yüz ile W2 kapak
        q = await ev("RK.w2s(1.2, -0.3-0.03)"); c = await ev(f"RK.candidate({q[0]},{q[1]},{{}})")
        ck('duvar dış yüzü üstü yakalanır', c['type'] in ('near','mid'), c)
        ck('JS hatası yok', not errs, errs[:3]); await pg.screenshot(path='a2.png'); await b.close()
    print('TOPLAM', sum(R), '/', len(R)); sys.exit(0 if all(R) else 1)
asyncio.run(main())
