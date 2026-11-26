# Seç: duvar seçilince köşelerde tutamak çıkar, köşe sürüklenince duvar gelir; kırık çizgisi "Kırığı sil" ile silinir, duvar düz bağlanır
import os, pathlib, sys, asyncio, math
ROOT = pathlib.Path(__file__).resolve().parent.parent
URL = (ROOT / os.environ.get('PAGE', 'index.html')).as_uri()
OUT = ROOT / 'test' / 'out'; OUT.mkdir(exist_ok=True); os.chdir(OUT)
CHROME = os.environ.get('CHROME', '/usr/bin/google-chrome' if os.path.exists('/usr/bin/google-chrome') else None)
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
            await pg.touchscreen.tap(r[0], r[1]); await pg.wait_for_timeout(100); return True
        async def org(): return await ev("(()=>{const r=document.querySelector('#cv').getBoundingClientRect(); return [r.left,r.top]})()")
        async def wtap(x,y): r=await org(); s=await ev(f"RK.w2s({x},{y})"); await pg.touchscreen.tap(r[0]+s[0], r[1]+s[1]); await pg.wait_for_timeout(120)
        async def wdrag(p0,p1):
            r=await org(); cdp=await ctx.new_cdp_session(pg); a=await ev(f"RK.w2s({p0[0]},{p0[1]})"); c=await ev(f"RK.w2s({p1[0]},{p1[1]})")
            tp=lambda x,y:[{'x':r[0]+x,'y':r[1]+y}]
            await cdp.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':tp(*a)}); await pg.wait_for_timeout(60)
            for k in range(1,21): await cdp.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':tp(a[0]+(c[0]-a[0])*k/20,a[1]+(c[1]-a[1])*k/20)}); await pg.wait_for_timeout(10)
            await cdp.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]}); await pg.wait_for_timeout(150)
        INIT = """(()=>{const P=RK.P; P.nodes=[];P.lines=[];P.walls=[];P.rooms=[];
          const C={A:[0,0],J1:[2,0],J2:[2,0.06],B:[4,0.06],C:[4,3],D:[0,3]}; Object.entries(C).forEach(([id,[x,y]])=>P.nodes.push({id,x,y}));
          const ids=Object.keys(C); ids.forEach((a,i)=>P.lines.push({id:'L'+i,a,b:ids[(i+1)%ids.length],kind:'sketch'}));
          P.walls.push({id:'W1',nodes:ids,closed:true,t:0.2,side:1}); P.rooms.push({id:'r1',name:'Salon',ax:2,ay:1.5}); RK.commit(); RK.commit(); RK.setTool('sec'); RK.commit()})()"""
        await ev(INIT); await btn('#fFit')
        # duvara dokun (tarama içine; iki yönü dene)
        for off in (0.1,-0.1):
            await wtap(-off*0+(-0.1 if off>0 else 0.1), 1.5)
            if await ev("!!(RK.S.sel&&RK.S.sel.wall)"): break
        ck('duvara dokununca duvar seçili', await ev("!!(RK.S.sel&&RK.S.sel.wall)"), await ev("JSON.stringify(RK.S.sel)"))
        ck('  "Köşeden tutup sürükle" ipucu', 'Köşeden tutup sürükle' in await ev("document.querySelector('#sheet').textContent"))
        await wdrag((4,3),(4.5,3.4))
        c = await ev("(()=>{const n=RK.P.nodes.find(n=>!['A','J1','J2','B','D'].includes(n.id)); return n?[n.x,n.y,n.id]:[0,0,'']})()")
        ck('köşe C sürüklendi (≈4.5, 3.4)', abs(c[0]-4.5)<0.15 and abs(c[1]-3.4)<0.15, c)
        ck('  duvar köşeyle birlikte geldi', await ev(f"RK.P.walls[0].nodes.includes('{c[2]}') && RK.P.walls[0].nodes.length===6 && RK.P.rooms.length===1"))
        # kırık: J1-J2 çizgisine dokun
        await ev(INIT); await btn('#fFit')
        await wtap(2,0.03)
        if not await ev("!!(RK.S.sel&&RK.S.sel.lines)"): await ev("RK.S.sel={lines:['L1']}; RK.commit()")
        ck('kırık çizgisinde "Kırığı sil" düğmesi', await ev("!!document.querySelector('#sheet button[data-a=jogdel]')"), await ev("JSON.stringify(RK.S.sel)"))
        await ev("RK.S.sel={lines:['L0']}; RK.commit()")
        ck('  uzun duvarda "Kırığı sil" yok', not await ev("!!document.querySelector('#sheet button[data-a=jogdel]')"))
        await ev("RK.S.sel={lines:['L1']}; RK.commit()"); await btn('#sheet button[data-a=jogdel]')
        N = dict((i,(x,y)) for i,x,y in await ev("RK.P.nodes.map(n=>[n.id,n.x,n.y])"))
        ck('kırık silindi (5 köşe, 5 çizgi)', len(N)==5 and await ev("RK.P.lines.length")==5, [len(N), await ev("RK.P.lines.length")])
        k = 'J1' if 'J1' in N else 'J2'; a,x,bb = N['A'],N[k],N['B']
        cr = (x[0]-a[0])*(bb[1]-a[1])-(x[1]-a[1])*(bb[0]-a[0])
        ck('  A–kırık–B düz bir hat', abs(cr)<1e-6, cr)
        ck('  duvar ve oda duruyor', await ev("RK.P.walls.length===1 && RK.P.walls[0].nodes.length===5 && RK.P.rooms.length===1"))
        await ev("RK.undo ? RK.undo() : null")
        ck('JS hatası yok', not errs, errs[:3]); await b.close()
    print('TOPLAM', sum(R), '/', len(R)); sys.exit(0 if all(R) else 1)
asyncio.run(main())
