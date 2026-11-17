# Ölç: duvarın diğer yüzüne dokunup ölçmek — ölçü yüze uygulanır (köşe uzantıları düşülür)
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
            await pg.touchscreen.tap(r[0], r[1]); await pg.wait_for_timeout(80); return True
        async def ctap(x,y):
            r = await ev("(()=>{const r=document.querySelector('#cv').getBoundingClientRect(); return [r.left,r.top]})()"); await pg.touchscreen.tap(r[0]+x, r[1]+y); await pg.wait_for_timeout(100)
        async def W(x,y): return await ev(f"RK.w2s({x},{y})")
        async def typ(v):
            if not await ev("!!document.querySelector('#sheet button[data-k=C]')"): await btn('#sheet button[data-a=np]')
            await btn('#sheet button[data-k="C"]')
            for ch in str(v): await btn(f'#sheet button[data-k="{ch}"]')
        SETUP = """((side)=>{const P=RK.P; P.nodes=[];P.lines=[];P.walls=[];P.rooms=[];P.openings=[]; const C=[[0,0],[4,0],[4,3],[0,3]]; const ids=C.map(([x,y],i)=>{const id='a'+i; P.nodes.push({id,x,y}); return id}); for(let i=0;i<4;i++) P.lines.push({id:'A'+i,a:ids[i],b:ids[(i+1)%4],kind:'sketch'}); P.walls.push({id:'WA',nodes:ids,closed:true,t:0.2,side}); P.rooms.push({id:'rA',name:'A',ax:2,ay:1.5}); RK.commit(); if (side==='flip') {P.walls[0].side=1;} RK.view.s=60; RK.view.ox=60; RK.view.oy=250; RK.commit(); return RK.wallGeom(P.walls[0]).Q.some(q=>q[1]<-0.1)})"""
        L0 = "+RK.lineLen(RK.P.lines.find(l=>l.id==='A0')).toFixed(3)"
        if await ev("!!document.querySelector('#tabs')"): await btn('#tabs button[data-tab=olcum]')
        else: await btn('#cats button[data-cat=olc]')
        await btn('#tools button[data-tool=olc]')
        for side in (1, -1):
            out = await ev(SETUP + f"({side})"); fy = -0.2 if out else 0.2; face = 4.4 if out else 3.6
            q = await W(2, fy); await ctap(*q)
            ck(f'[{"dış" if out else "iç"} bant] diğer yüze dokununca alt çizgi seçildi, panel yüz boyunu gösteriyor {face:.2f}', await ev("RK.S.ms.sel")=='A0' and ('%.3f' % face).replace('.',',') in await ev("document.querySelector('#sheet').textContent") or ('%.3f' % face) in await ev("document.querySelector('#sheet').textContent"), await ev("document.querySelector('#sheet').textContent"))
            await typ(int(round((face+0.1)*100))); await btn('#sheet button[data-a=msok]')
            ck(f'  yüze {face+0.1:.2f} yazıldı → çizgi {4.1:.2f}, yüz {face+0.1:.2f}', await ev(L0)==4.1, [await ev(L0), await ev("document.querySelector('#toast').textContent")])
            # lazer önce gelir, sonra yüze dokunulur
            await ev("RK.laserValue(%s)" % (face)); q = await W(2, fy); await ctap(*q); await btn('#sheet button[data-a=msok]')
            ck('  lazer sonra yüze dokunuş → çizgi 4.00', await ev(L0)==4.0, await ev(L0))
            q = await W(2, 0); await ctap(*q); ck('  çizginin kendisine dokununca yüz seçimi yok', await ev("RK.S.ms.sel")=='A0' and not await ev("RK.S.ms.fs"), await ev("RK.S.ms.fs"))
            await ev("RK.S.ms.sel=null; RK.commit()")
        await pg.screenshot(path='t20.png')
        ck('JS hatası yok', not errs, errs[:3]); await b.close()
    print('TOPLAM', sum(R), '/', len(R)); sys.exit(0 if all(R) else 1)
asyncio.run(main())
