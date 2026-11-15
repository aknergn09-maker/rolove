import os, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
URL = (ROOT / os.environ.get('PAGE', 'index.html')).as_uri()
OUT = ROOT / 'test' / 'out'; OUT.mkdir(exist_ok=True); os.chdir(OUT)
CHROME = os.environ.get('CHROME', '/usr/bin/google-chrome' if os.path.exists('/usr/bin/google-chrome') else None)
import asyncio, sys
from playwright.async_api import async_playwright
R=[]
def ck(n,ok,i=''): R.append(bool(ok)); print(('PASS ' if ok else 'FAIL ')+n, i if not ok else '')
AREAS = "Object.fromEntries(RK.P.rooms.map(r=>[r.name, r._f? +r._f.net.toFixed(3):null]))"
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path=CHROME, args=['--no-sandbox'])
        ctx=await b.new_context(**p.devices['iPhone 13']); pg=await ctx.new_page(); errs=[]
        pg.on('pageerror', lambda e: errs.append(e.stack[:300]))
        await pg.goto(URL); await pg.evaluate("localStorage.clear()"); await pg.reload(); await pg.wait_for_timeout(300); ev=pg.evaluate
        async def btn(sel):
            r = await ev(f"(()=>{{const e=document.querySelector('{sel}'); if(!e||e.disabled) return null; const r=e.getBoundingClientRect(); return [r.left+r.width/2, r.top+r.height/2]}})()")
            if not r: return False
            await pg.touchscreen.tap(r[0], r[1]); await pg.wait_for_timeout(70); return True
        async def org(): return await ev("(()=>{const r=document.querySelector('#cv').getBoundingClientRect(); return [r.left,r.top]})()")
        async def ctap(x,y): r=await org(); await pg.touchscreen.tap(r[0]+x, r[1]+y); await pg.wait_for_timeout(80)
        async def typ(v):
            if not await ev("!!document.querySelector('#sheet button[data-k=C]')"): await btn('#sheet button[data-a=np]')
            await btn('#sheet button[data-k="C"]')
            for ch in str(v): await btn(f'#sheet button[data-k="{ch}"]')
            await ev("RK.S.np=false; RK.commit()")
        async def W(x,y): return await ev(f"RK.w2s({x},{y})")
        async def stroke(wpts):
            r = await org(); cdp = await ctx.new_cdp_session(pg); sp = [await ev(f"RK.w2s({x},{y})") for x,y in wpts]
            tp = lambda x,y: [{'x':r[0]+x,'y':r[1]+y}]
            await cdp.send('Input.dispatchTouchEvent', {'type':'touchStart','touchPoints':tp(*sp[0])})
            for (x0,y0),(x1,y1) in zip(sp,sp[1:]):
                n=max(2,int(((x1-x0)**2+(y1-y0)**2)**.5/5))
                for k in range(1,n+1): await cdp.send('Input.dispatchTouchEvent', {'type':'touchMove','touchPoints':tp(x0+(x1-x0)*k/n, y0+(y1-y0)*k/n)})
            await cdp.send('Input.dispatchTouchEvent', {'type':'touchEnd','touchPoints':[]}); await pg.wait_for_timeout(120)
        await ev("""(()=>{const P=RK.P; P.nodes=[];P.lines=[];P.walls=[];P.rooms=[]; const C=[[0,0],[10,0],[10,8],[0,8]]; const ids=C.map(([x,y],i)=>{const id='s'+i; P.nodes.push({id,x,y}); return id}); for(let i=0;i<4;i++) P.lines.push({id:'S'+i,a:ids[i],b:ids[(i+1)%4],kind:'sketch'}); P.walls.push({id:'WS',nodes:ids,closed:true,t:0.2,side:1}); P.rooms.push({id:'rS',name:'Bina',ax:5,ay:4}); RK.commit();})()""")
        a = await ev(AREAS)
        if abs(a['Bina']-80)<1e-6: await ev("RK.P.walls[0].side*=-1; RK.commit()"); a = await ev(AREAS)
        ck('iskelet: duvar içe, alan iç yüzden 9.6×7.6=72.96', abs(a['Bina']-72.96)<1e-6, a)
        await btn('#fFit'); await btn('#tools button[data-tool=cizgi]')
        q = await W(4,7.8); await ctap(q[0], q[1]); st = await ev("(()=>{const n=RK.P.nodes.find(x=>x.id===RK.S.chain.first); return [+n.x.toFixed(4),+n.y.toFixed(4)]})()")
        ck('başlangıç iç yüzde', abs(st[1]-7.8)<1e-4, st)
        await typ(280); await btn('#sheet button[data-a=ar][data-v="3"]')
        q = await W(9.8,5); await ctap(q[0], q[1])
        a = await ev(AREAS); new=[k for k in a if k!='Bina']
        ck('iç yüze dokununca oda oluştu: 5.8×2.8=16.24, iskelet 72.96-16.24=56.72', len(new)==1 and abs(a[new[0]]-16.24)<1e-6 and abs(a['Bina']-56.72)<1e-6 and await ev("RK.S.chain")==None, a)
        # serbest çizimle de
        await btn('#tools button[data-tool=serbest]'); await stroke([(0.2,3),(4,3),(4,0.2)])
        a = await ev(AREAS); ck('serbest: iç yüzden iç yüze çizim oda oldu (3.8×2.8=10.64), çıkıntı sorusu yok', any(abs(v-10.64)<1e-6 for v in a.values() if v) and not await ev('!!RK.S.strokeAsk'), a)
        await btn('#fFit'); await pg.screenshot(path='o5.png')
        # dışa doğru duvar (iç çizgi referans) da aynı: dış yüz sınır sayılır
        await ev("RK.P.walls[0].side*=-1; RK.commit()"); a = await ev(AREAS); ck('duvar yönü çevrilince alanlar çizgiden', a['Bina'] is not None, a)
        ck('JS hatası yok', not errs, errs[:3]); await b.close()
    print('TOPLAM', sum(R), '/', len(R)); sys.exit(0 if all(R) else 1)
asyncio.run(main())
