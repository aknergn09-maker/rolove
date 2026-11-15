import os, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
URL = (ROOT / 'index.html').as_uri()
OUT = ROOT / 'test' / 'out'; OUT.mkdir(exist_ok=True); os.chdir(OUT)
CHROME = os.environ.get('CHROME', '/usr/bin/google-chrome' if os.path.exists('/usr/bin/google-chrome') else None)
import asyncio, sys
from playwright.async_api import async_playwright
R=[]
def ck(n,ok,i=''): R.append(bool(ok)); print(('PASS ' if ok else 'FAIL ')+n, i if not ok else '')
OPS = "RK.P.openings.map(o=>{const g=RK.opGeom(o); return [o.type, ...[g.P0,g.P1].map(p=>[+p[0].toFixed(3),+p[1].toFixed(3)]).sort((a,b)=>a[0]-b[0]||a[1]-b[1])]})"
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
            await ev("RK.S.np=false; RK.commit()")
        async def W(x,y): return await ev(f"RK.w2s({x},{y})")
        SETUP = """(()=>{const P=RK.P; P.nodes=[];P.lines=[];P.walls=[];P.rooms=[];P.openings=[]; const C=[[0,0],[4,0],[4,3],[0,3]]; const ids=C.map(([x,y],i)=>{const id='a'+i; P.nodes.push({id,x,y}); return id}); for(let i=0;i<4;i++) P.lines.push({id:'A'+i,a:ids[i],b:ids[(i+1)%4],kind:'sketch'}); P.walls.push({id:'WA',nodes:ids,closed:true,t:0.2,side:1}); P.rooms.push({id:'rA',name:'A',ax:2,ay:1.5}); RK.commit();
          const sp=(x)=>{const id=RK.nodeAt([x,0]); return id}; const n0=sp(1.5), n1=sp(2.7); RK.addOpening('pencere', n0, n1, 0, 1.2); RK.commit(); RK.view.s=60; RK.view.ox=60; RK.view.oy=330; RK.commit();})()"""
        await ev(SETUP)
        ck('kurulum: alt duvarda pencere 1.50–2.70', await ev(OPS)==[['pencere',[1.5,0],[2.7,0]]], await ev(OPS))
        # çizerek çıkıntı: x=1'den aşağı 50, sağa 200, yukarı duvara
        await btn('#cats button[data-cat=duz]'); await btn('#tools button[data-tool=cikinti]')
        q = await W(1,0); await ctap(q[0], q[1]-2); await typ(50); await btn('#sheet button[data-a=ar][data-v="3"]'); await typ(200); await btn('#sheet button[data-a=ar][data-v="0"]')
        q = await W(3,0); await ctap(q[0], q[1]-2)
        if await ev("!!document.querySelector('#sheet button[data-a=askN]')"): await btn('#sheet button[data-a=askN]')
        ck('dışa çıkıntı: pencere yeni dış yüze taşındı (y=-0.5, x 1.50–2.70)', await ev(OPS)==[['pencere',[1.5,-0.5],[2.7,-0.5]]], [await ev(OPS), await ev("+RK.rA(RK.P.rooms[0]).toFixed(3)")])
        ck('  alan 12 + 2×0.5 = 13', await ev("+RK.rA(RK.P.rooms[0]).toFixed(3)")==13)
        await ev("RK.undo()"); ck('geri al: pencere eski yerinde', await ev(OPS)==[['pencere',[1.5,0],[2.7,0]]], await ev(OPS))
        # ölçüyle girinti içeri 30
        await ev(SETUP); await btn('#sheet button[data-a=cikm][data-v=olcu]')
        q = await W(1,0); await ctap(q[0], q[1]-2); await typ(200)
        lbl = await ev("[...document.querySelectorAll('#sheet button[data-a=cikw]')].map(b=>[b.dataset.v,b.textContent])"); v=[x for x,t in lbl if t=='→'][0]; await btn(f'#sheet button[data-a=cikw][data-v="{v}"]')
        await typ(30); lbl = await ev("[...document.querySelectorAll('#sheet button[data-a=cikd]')].map(b=>[b.dataset.v,b.textContent])"); v=[x for x,t in lbl if t=='↑'][0]; await btn(f'#sheet button[data-a=cikd][data-v="{v}"]')
        ck('ölçüyle girinti: pencere y=0.3 iç yüze taşındı', await ev(OPS)==[['pencere',[1.5,0.3],[2.7,0.3]]], await ev(OPS))
        # pencereye sığmayan çıkıntı: x 2..3 → pencere (1.5–2.7) taşan, kaldırılır
        await ev(SETUP); await btn('#sheet button[data-a=cikm][data-v=el]')
        q = await W(2,0); await ctap(q[0], q[1]-2); await typ(50); await btn('#sheet button[data-a=ar][data-v="3"]'); await typ(150); await btn('#sheet button[data-a=ar][data-v="0"]')
        q = await W(3.5,0); await ctap(q[0], q[1]-2)
        if await ev("!!document.querySelector('#sheet button[data-a=askN]')"): await btn('#sheet button[data-a=askN]')
        ck('çıkıntı pencerenin ortasından geçerse pencere kaldırılır, uyarı verir', await ev("RK.P.openings.length")==0)
        ck('JS hatası yok', not errs, errs[:3]); await b.close()
    print('TOPLAM', sum(R), '/', len(R)); sys.exit(0 if all(R) else 1)
asyncio.run(main())
