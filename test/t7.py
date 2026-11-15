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
        async def typ(v):
            if not await ev("!!document.querySelector('#sheet button[data-k=C]')"): await btn('#sheet button[data-a=np]')
            await btn('#sheet button[data-k="C"]')
            for ch in str(v): await btn(f'#sheet button[data-k="{ch}"]')
        ext = "(()=>{const g=RK.wallGeom(RK.P.walls[0]); const xs=g.Q.map(q=>q[0]), ys=g.Q.map(q=>q[1]); return [+(Math.max(...xs)-Math.min(...xs)).toFixed(3), +(Math.max(...ys)-Math.min(...ys)).toFixed(3)]})()"
        # açık duvar: 3 kenar, kapatmayı unut
        await btn('#tools button[data-tool=duvar]'); await btn('#sheet button[data-a=wt][data-v="0.2"]')
        await ctap(70,120); await typ(400); await btn('#sheet button[data-a=ar][data-v="0"]'); await typ(300); await btn('#sheet button[data-a=ar][data-v="3"]'); await typ(400); await btn('#sheet button[data-a=ar][data-v="2"]'); await btn('#sheet button[data-a=end]')
        e0 = await ev(ext); ck('açık duvar çizildi (oda yok)', await ev("[RK.P.walls.length, RK.P.walls[0].closed, RK.P.rooms.length]")==[1,False,0])
        await btn('#fFit'); await btn('#cats button[data-cat=duz]'); await btn('#tools button[data-tool=sec]')
        q = await ev("(()=>{const g=RK.wallGeom(RK.P.walls[0]); const qd=g.quads[1].poly; return RK.w2s((qd[0][0]+qd[1][0]+qd[2][0]+qd[3][0])/4,(qd[0][1]+qd[1][1]+qd[2][1]+qd[3][1])/4)})()")
        await ctap(*q); has = await ev("!!document.querySelector('#sheet button[data-a=closeSel]')")
        ck('duvar seçilince "Kapat" tuşu var', has, await ev("RK.S.sel"))
        await btn('#sheet button[data-a=closeSel]')
        r = await ev("[RK.P.walls[0].closed, RK.P.rooms.map(r=>+r._f.net.toFixed(2)), RK.wallGeom(RK.P.walls[0]).quads.length]")
        e1 = await ev(ext)
        ck('Kapat: duvar kapandı, oda 12 m², kalınlık aynı tarafta', r==[True,[12.0],4] and e1==[4.4,3.4], [r, e0, e1])
        # düz çizgi zinciri (duvarsız) için Kapat
        await ev("(()=>{RK.P={v:8,name:'C'+Math.random(),nodes:[],lines:[],rooms:[],walls:[],roomSeq:0}; RK.commit(); RK.view.s=50; RK.view.ox=40; RK.view.oy=200; RK.S.np=false; RK.commit();})()")
        await btn('#cats button[data-cat=ciz]'); await btn('#tools button[data-tool=cizgi]')
        await ctap(50,200); await typ(300); await btn('#sheet button[data-a=ar][data-v="0"]'); await typ(200); await btn('#sheet button[data-a=ar][data-v="1"]'); await typ(300); await btn('#sheet button[data-a=ar][data-v="2"]'); await btn('#sheet button[data-a=end]')
        await btn('#cats button[data-cat=duz]'); await btn('#tools button[data-tool=sec]')
        q = await ev("(()=>{const l=RK.P.lines[1]; const a=RK.ns(l.a), b=RK.ns(l.b); return [(a[0]+b[0])/2,(a[1]+b[1])/2]})()"); await ctap(*q)
        ok = await btn('#sheet button[data-a=closeSel]')
        ck('çizgi zinciri seçilince Kapat → oda', ok and await ev("RK.P.rooms.map(r=>+r._f.net.toFixed(2))")==[6.0], await ev("RK.P.rooms.length"))
        ck('JS hatası yok', not errs, errs[:3]); await b.close()
    print('TOPLAM', sum(R), '/', len(R)); sys.exit(0 if all(R) else 1)
asyncio.run(main())
