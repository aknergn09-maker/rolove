# ÖNİZLEME: obje kaydırma — Seç ile objenin çizgisine dokun; ortadaki tutamaktan sürükle → tüm obje, köşeden → sadece köşe
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
        cdp = await ctx.new_cdp_session(pg)
        async def btn(sel):
            r = await ev(f"(()=>{{const e=document.querySelector('{sel}'); if(!e||e.disabled) return null; const r=e.getBoundingClientRect(); return [r.left+r.width/2, r.top+r.height/2]}})()")
            if not r: return False
            await pg.touchscreen.tap(r[0], r[1]); await pg.wait_for_timeout(80); return True
        async def org(): return await ev("(()=>{const r=document.querySelector('#cv').getBoundingClientRect(); return [r.left,r.top]})()")
        async def ctap(x,y): o = await org(); await pg.touchscreen.tap(o[0]+x, o[1]+y); await pg.wait_for_timeout(120)
        async def drag(a, bb):
            o = await org(); pts = [(a[0]+(bb[0]-a[0])*k/8, a[1]+(bb[1]-a[1])*k/8) for k in range(9)]
            await cdp.send('Input.dispatchTouchEvent', {'type':'touchStart','touchPoints':[{'x':o[0]+pts[0][0],'y':o[1]+pts[0][1]}]}); await pg.wait_for_timeout(60)
            for q in pts[1:]: await cdp.send('Input.dispatchTouchEvent', {'type':'touchMove','touchPoints':[{'x':o[0]+q[0],'y':o[1]+q[1]}]}); await pg.wait_for_timeout(30)
            await cdp.send('Input.dispatchTouchEvent', {'type':'touchEnd','touchPoints':[]}); await pg.wait_for_timeout(150)
        async def W(x,y): return await ev(f"RK.w2s({x},{y})")
        await ev("""(()=>{const P=RK.P; P.nodes=[];P.lines=[];P.walls=[];P.rooms=[];P.openings=[];
          const sq=(pre,C,closed)=>{const ids=C.map(([x,y],i)=>{const id=pre+i; P.nodes.push({id,x,y}); return id}); for(let i=0;i<(closed?C.length:C.length-1);i++) P.lines.push({id:'L'+pre+i,a:ids[i],b:ids[(i+1)%C.length],kind:'sketch'}); return ids};
          const A=sq('a',[[0,0],[4,0],[4,3],[0,3]],true); P.walls.push({id:'W',nodes:A,closed:true,t:0.2,side:1}); sq('e',[[3,2],[3.5,2],[3.5,2.5],[3,2.5]],true); sq('d',[[1,1],[2,1]],false);
          P.rooms.push({id:'rA',name:'Salon',ax:1.5,ay:2.2}); P.rooms.push({id:'rE',name:'Kolon',ax:3.25,ay:2.25,kind:'eleman'}); RK.commit(); RK.view.s=70; RK.view.ox=40; RK.view.oy=330; RK.commit();})()""")
        N = "(id=>{const n=RK.P.nodes.find(q=>q.id===id); return [+n.x.toFixed(3),+n.y.toFixed(3)]})"
        A0 = await ev("+RK.rA(RK.P.rooms[0]).toFixed(4)")
        if await ev("!!document.querySelector('#tabs')"): await btn('#tabs button[data-tab=cizim]')
        await btn('#cats button[data-cat=duz]'); await btn('#tools button[data-tool=sec]')
        q = await W(3.25, 2); await ctap(*q)
        ck('kolonun alt çizgisi seçildi', await ev("JSON.stringify(RK.S.sel)")=='{"lines":["Le0"]}', await ev("JSON.stringify(RK.S.sel)"))
        await drag(await W(3.25,2), await W(2.25,1.5))
        e = [await ev(N + f"('e{i}')") for i in range(4)]
        ck('ortadan sürükleme: kolonun 4 köşesi birlikte 1.00 sola, 0.50 aşağı kaydı', e==[[2,1.5],[2.5,1.5],[2.5,2],[2,2]], e)
        ck('  kolon adı ve alanı birlikte kaydı, salon alanı aynı', await ev("[RK.P.rooms[1].ax, RK.P.rooms[1].ay, +RK.rA(RK.P.rooms[1]).toFixed(3), +RK.rA(RK.P.rooms[0]).toFixed(4)]")==[2.25,1.75,0.25,A0], await ev("[RK.P.rooms[1].ax, RK.P.rooms[1].ay, RK.rA(RK.P.rooms[1]), RK.rA(RK.P.rooms[0])]"))
        await pg.screenshot(path='p10a.png')
        # köşeden: sadece o köşe
        await drag(await W(2.5,1.5), await W(2.8,1.3))
        e2 = [await ev(N + f"('e{i}')") for i in range(4)]
        ck('köşeden sürükleme: sadece o köşe kaydı', e2[1]!=[2.5,1.5] and e2[0]==[2,1.5] and e2[2]==[2.5,2] and e2[3]==[2,2], e2)
        await ev("RK.undo(); RK.commit()")
        # iç detay çizgisi (tek başına): ortadan → tamamı (zaten iki ucu)
        # bina duvarı: ortadan sürükleme tüm binayı taşımaz
        q = await W(2, 3); await ctap(*q); s3 = await ev("JSON.stringify(RK.S.sel)")
        await drag(await W(2,3), await W(2,3.4))
        a = await ev(N+"('a0')"); c = await ev(N+"('a2')")
        ck('bina duvarı ortadan sürüklenince bütün bina kaymaz (alt köşe yerinde)', a==[0,0] and c[1]!=3, [s3, a, c])
        await ev("RK.undo(); RK.commit()")
        ck('JS hatası yok', not errs, errs[:3]); await b.close()
    print('TOPLAM', sum(R), '/', len(R)); sys.exit(0 if all(R) else 1)
asyncio.run(main())
