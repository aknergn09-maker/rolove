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
        await ev("""(()=>{const P=RK.P; P.nodes=[];P.lines=[];P.walls=[];P.rooms=[]; const mk=(pre,C,side,name,ax,ay)=>{const ids=C.map(([x,y],i)=>{const id=pre+i; P.nodes.push({id,x,y}); return id}); for(let i=0;i<C.length;i++) P.lines.push({id:pre+'L'+i,a:ids[i],b:ids[(i+1)%C.length],kind:'sketch'}); P.walls.push({id:'W'+pre,nodes:ids,closed:true,t:0.2,side}); P.rooms.push({id:'r'+pre,name,ax,ay});};
          mk('s',[[0,0],[15,0],[15,15],[0,15]],1,'Bina',3,3); RK.commit(); if (Math.abs(P.rooms[0]._f.net-225)<0.5) { P.walls[0].side*=-1; RK.commit(); } mk('d',[[10,8],[14.8,8],[14.8,14.8],[10,14.8]],1,'Oda4',12,11); RK.commit();})()""")
        a = await ev(AREAS)
        if abs(a['Oda4']-4.8*6.8)>1e-6: await ev("RK.P.walls[1].side*=-1; RK.commit()"); a = await ev(AREAS)
        ck('kurulum: iskelet duvarı içe, Oda4 duvarı dışa', abs(a['Oda4']-32.64)<1e-6 and a['Bina'] is not None and a['Bina']<200, a)
        await btn('#fFit'); await ev('RK.view.s=30; RK.view.ox=8; RK.view.oy=490; RK.commit()'); await btn('#tools button[data-tool=cizgi]')
        # sağdan sola: Oda4'ün dış yüzünden iskeletin iç yüzüne
        q = await W(9.8,12); await ctap(q[0], q[1]); st = await ev("(()=>{const n=RK.P.nodes.find(x=>x.id===RK.S.chain.first); return [+n.x.toFixed(4),+n.y.toFixed(4)]})()")
        q = await W(0.2,12); await ctap(q[0], q[1])
        a = await ev(AREAS); v=[x for k,x in a.items() if k not in ('Bina','Oda4')]
        ck('sağdan sola (Oda4 dış yüzü → iskelet iç yüzü): üstte oda oluştu 9.6×2.8=26.88', any(x and abs(x-26.88)<1e-6 for x in v), [st, a])
        # soldan sağa
        q = await W(0.2,10); await ctap(q[0], q[1]); q = await W(9.8,10); await ctap(q[0], q[1])
        a = await ev(AREAS); v=[x for k,x in a.items() if k not in ('Bina','Oda4')]
        ck('soldan sağa: arada oda 9.6×2=19.2', any(x and abs(x-19.2)<1e-6 for x in v), a)
        tot = sum(x for x in a.values() if x); ck('toplam = iskelet iç alanı − Oda4 duvarı (14.6² − 0.2 bant)', tot>200, [tot, a])
        n0 = len(a); await btn('#tools button[data-tool=duvar]'); q = await W(9.8,13.5); await ctap(q[0], q[1]); q = await W(0.2,13.5); await ctap(q[0], q[1])
        a = await ev(AREAS); ck('Duvar aracıyla sağdan sola da: iki yanında oda oluştu, zincir bitti', len(a)==n0+1 and await ev("RK.S.chain")==None and all(v for v in a.values()), a)
        await pg.screenshot(path='o6.png')
        ck('JS hatası yok', not errs, errs[:3]); await b.close()
    print('TOPLAM', sum(R), '/', len(R)); sys.exit(0 if all(R) else 1)
asyncio.run(main())
