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
        async def free():  # tuvalin panelle örtülmeyen yüksekliği
            return await ev("(()=>{const c=document.querySelector('#cv').getBoundingClientRect(); const s=document.querySelector('#sheet'); const t=s.innerHTML? s.getBoundingClientRect().top : c.bottom; return t-c.top})()")
        async def ctap(x,y):
            r = await ev("(()=>{const r=document.querySelector('#cv').getBoundingClientRect(); return [r.left,r.top]})()"); el = await ev(f"(()=>{{const e=document.elementFromPoint({r[0]+x},{r[1]+y}); return e.id}})()")
            await pg.touchscreen.tap(r[0]+x, r[1]+y); await pg.wait_for_timeout(80); return el
        async def typ(v):
            if not await ev("!!document.querySelector('#sheet button[data-k=C]')"): await btn('#sheet button[data-a=np]')
            await btn('#sheet button[data-k="C"]')
            for ch in str(v): await btn(f'#sheet button[data-k="{ch}"]')
        async def stroke(pts):
            r = await ev("(()=>{const r=document.querySelector('#cv').getBoundingClientRect(); return [r.left,r.top]})()")
            cdp = await ctx.new_cdp_session(pg)
            def tp(x,y): return [{'x':r[0]+x,'y':r[1]+y}]
            await cdp.send('Input.dispatchTouchEvent', {'type':'touchStart','touchPoints':tp(*pts[0])})
            for (x0,y0),(x1,y1) in zip(pts,pts[1:]):
                n=max(2,int(((x1-x0)**2+(y1-y0)**2)**.5/6))
                for k in range(1,n+1): await cdp.send('Input.dispatchTouchEvent', {'type':'touchMove','touchPoints':tp(x0+(x1-x0)*k/n, y0+(y1-y0)*k/n)})
            await cdp.send('Input.dispatchTouchEvent', {'type':'touchEnd','touchPoints':[]}); await pg.wait_for_timeout(100)
        await btn('#tools button[data-tool=duvar]')
        fh = await free(); ck('panel kompakt: tuvalin en az %55\'i açık', fh > 0.55*(await ev("document.querySelector('#cv').getBoundingClientRect().height")), fh)
        s0 = await ev("RK.SET.wallSide"); await btn('#sheet button[data-a=wside]'); ck('⇄ Yön (çizim sırasında)', await ev("RK.SET.wallSide")==-s0); await btn('#sheet button[data-a=wside]')
        await btn('#sheet button[data-a=wt][data-v="0.3"]'); ck('kalınlık 30 düğmesi', await ev("RK.SET.wallT")==0.3)
        el = await ctap(70,120); ck('tuvale dokunma panele gitmiyor', el=='cv', el)
        await typ(400); await btn('#sheet button[data-a=ar][data-v="0"]'); await typ(300); await btn('#sheet button[data-a=ar][data-v="1"]'); await typ(400); await btn('#sheet button[data-a=ar][data-v="2"]'); await btn('#sheet button[data-a=close]')
        sdw = await ev("RK.P.walls[0] && RK.P.walls[0].side"); await btn('#sheet button[data-a=wside]'); ck('çizim bitince ⇄ Yön az önce çizilen duvarı çevirir', await ev("RK.P.walls[0].side")==-sdw); await btn('#sheet button[data-a=wside]')
        await btn('#sheet button[data-a=wt][data-v="0.25"]'); ck('çizim bitince kalınlık düğmesi son duvara uygulanır', await ev("RK.P.walls[0].t")==0.25); await btn('#sheet button[data-a=wt][data-v="0.3"]')
        ck('dokunmayla duvarlı oda', await ev("[RK.P.walls.length, RK.P.rooms.length]")==[1,1], await ev("[RK.P.walls.length, RK.P.rooms.length, RK.P.lines.length]"))
        await btn('#cats button[data-cat=duz]'); await btn('#tools button[data-tool=sec]'); await btn('#fFit'); print('   view.s', await ev("RK.view.s"), await ev("RK.P.nodes.map(n=>[+n.x.toFixed(2),+n.y.toFixed(2)])"))
        q = await ev("(()=>{const g=RK.wallGeom(RK.P.walls[0]); const qd=g.quads[1].poly; return RK.w2s((qd[0][0]+qd[1][0]+qd[2][0]+qd[3][0])/4,(qd[0][1]+qd[1][1]+qd[2][1]+qd[3][1])/4)})()")
        await ctap(*q); ck('duvar bandına dokununca seçilir', await ev("!!(RK.S.sel&&RK.S.sel.wall)"), await ev("RK.S.sel"))
        sd = await ev("RK.P.walls[0].side"); await btn('#sheet button[data-a=sside]'); ck('seçili duvarda ⇄ Yön', await ev("RK.P.walls[0].side")==-sd)
        await btn('#sheet button[data-a=swt][data-v="0.15"]'); ck('seçili duvarda kalınlık 15', await ev("RK.P.walls[0].t")==0.15)
        # duvarın diğer (dış) yüzü seçilir
        q = await ev("(()=>{const g=RK.wallGeom(RK.P.walls[0]); const qd=g.quads[2].poly; return RK.w2s((qd[2][0]*0.6+qd[3][0]*0.4),(qd[2][1]*0.6+qd[3][1]*0.4))})()")
        await ctap(*q); fs = await ev("RK.S.sel && RK.S.sel.face ? RK.S.sel.face.k : null"); txt = await ev("document.querySelector('#sheet').textContent")
        ck('duvarın diğer yüzüne dokununca seçilir', fs=='out' and 'dış yüzü' in txt, [fs, await ev("RK.S.sel")])
        sd3 = await ev("RK.P.walls[0].side"); await btn('#sheet button[data-a=sside]'); ck('  dış yüz seçiliyken ⇄ Yön', await ev("RK.P.walls[0].side")==-sd3); await btn('#sheet button[data-a=sside]')
        # çizgi aracında dış köşe yakalanır
        await btn('#cats button[data-cat=ciz]'); await btn('#tools button[data-tool=cizgi]')
        qc = await ev("(()=>{const g=RK.wallGeom(RK.P.walls[0]); return RK.w2s(...g.Q[0])})()"); c = await ev(f"RK.candidate({qc[0]+4},{qc[1]+3},{{}})")
        ck('  çizgi aracında duvar dış köşesi yakalanır', c['type']=='end' and abs(c['X']-qc[0])<0.5, c)
        await btn('#cats button[data-cat=duz]'); await btn('#tools button[data-tool=sec]')
        q = await ev("(()=>{const l=RK.P.lines[0]; const a=RK.ns(l.a), b=RK.ns(l.b); return [(a[0]*0.4+b[0]*0.6),(a[1]*0.4+b[1]*0.6)]})()")
        await ctap(*q); ck('çizgiye dokununca seçilir', await ev("!!(RK.S.sel&&RK.S.sel.lines)"), await ev("RK.S.sel"))
        sd2 = await ev("RK.P.walls[0].side"); await btn('#sheet button[data-a=sside]'); ck('çizgi seçiliyken de duvar ⇄ Yön görünür ve çalışır', await ev("RK.P.walls[0].side")==-sd2)
        await btn('#sheet button[data-a=len]'); await typ(450); await btn('#sheet button[data-a=fix][data-v=B]'); await btn('#sheet button[data-a=lenok]')
        L = await ev("(()=>{const l=RK.P.lines[0]; const a=RK.P.nodes.find(n=>n.id===l.a), b=RK.P.nodes.find(n=>n.id===l.b); return +Math.hypot(a.x-b.x,a.y-b.y).toFixed(3)})()")
        ck('Uzunluk → ✓ Uygula', L==4.5, L)
        # serbest çizim + duvar ekle
        await ev("(()=>{RK.P={v:8,name:'F'+Math.random(),nodes:[],lines:[],rooms:[],walls:[],roomSeq:0}; RK.commit(); RK.view.s=45;})()")
        await btn('#cats button[data-cat=ciz]'); await btn('#tools button[data-tool=serbest]')
        await stroke([(50,60),(300,64),(304,260),(54,256),(52,62)])
        ck('serbest çizim (dokunmayla) → oda', await ev("[RK.P.lines.length, RK.P.rooms.length]")==[4,1], await ev("[RK.P.lines.length, RK.P.rooms.length]"))
        ok = await btn('#sheet button[data-a=wstroke]'); w = await ev("RK.P.walls.map(w=>[w.nodes.length,w.closed,w.t])")
        sdf = await ev("RK.P.walls[0].side"); await btn('#sheet button[data-a=wside]'); ck('serbest: duvar ekledikten sonra ⇄ Yön o duvarı çevirir', await ev("RK.P.walls[0].side")==-sdf)
        ck('serbest çizimden sonra "Duvar ekle"', ok and w==[[4,True,0.15]], [ok,w, await ev("document.querySelector('#toast').textContent"), await ev("RK.S.lastStroke"), await ev("RK.P.lines.map(l=>l.id)")])
        await stroke([(50,300),(200,300),(200,330)])
        await btn('#cats button[data-cat=duz]'); await btn('#tools button[data-tool=sec]')
        q = await ev("(()=>{const l=RK.P.lines[RK.P.lines.length-2]; const a=RK.ns(l.a), b=RK.ns(l.b); return [(a[0]+b[0])/2,(a[1]+b[1])/2]})()"); await ctap(*q)
        ok = await btn('#sheet button[data-a=mkwall]'); w = await ev("RK.P.walls.map(w=>[w.nodes.length,w.closed])")
        ck('Seç → çizgi → ▥ Duvar (bağlı zincir)', ok and w[-1]==[3,False], [ok,w])
        sd = await ev("RK.P.walls[RK.P.walls.length-1].side"); await btn('#sheet button[data-a=sside]'); ck('  yeni duvarda ⇄ Yön', await ev("RK.P.walls[RK.P.walls.length-1].side")==-sd)
        # açık duvarın ucu (kapak) seçilir, sonra çizgilere çevir
        q = await ev("(()=>{const w=RK.P.walls[RK.P.walls.length-1]; const g=RK.wallGeom(w); const qd=g.quads[0].poly; const c=[(qd[0][0]+qd[3][0])/2,(qd[0][1]+qd[3][1])/2]; const v=RK.view; v.s=400; v.ox=195-c[0]*v.s; v.oy=200+c[1]*v.s; RK.commit(); return RK.w2s(...c)})()")
        await ctap(*q); ck('açık duvarın ucu (kapak) yakınlaştırınca seçilir', (await ev("RK.S.sel && RK.S.sel.face ? RK.S.sel.face.k : null")) in ('capA','capB'), await ev("RK.S.sel"))
        nl = await ev("RK.P.lines.length"); nw_ = await ev("RK.P.walls.length"); await btn('#sheet button[data-a=wsplit]')
        ck('  "Çizgilere çevir": diğer yüz gerçek çizgi olur', await ev("RK.P.lines.length")==nl+4 and await ev("RK.P.walls.length")==nw_-1, [nl, await ev("RK.P.lines.length")])
        # hızlı dokunuş: çizimden hemen sonra düğme (bekleme yok), 5 kez
        await btn('#cats button[data-cat=ciz]'); await btn('#tools button[data-tool=serbest]'); okc = 0
        for k in range(5):
            nw0 = await ev("RK.P.walls.length"); await stroke([(40,330+k*4),(120,330+k*4)])
            r = await ev("(()=>{const e=document.querySelector('#sheet button[data-a=wstroke]'); const r=e.getBoundingClientRect(); return [r.left+r.width/2, r.top+r.height/2]})()")
            await pg.touchscreen.tap(r[0], r[1]); await pg.wait_for_timeout(30)
            if await ev("RK.P.walls.length")==nw0+1: okc += 1
        ck('çizimden hemen sonra düğmeye basınca kaybolmuyor (5/5, tek sefer)', okc==5, okc)
        await btn('#fFit'); await pg.screenshot(path='m1.png')
        ck('JS hatası yok', not errs, errs[:3]); await b.close()
    print('TOPLAM', sum(R), '/', len(R)); sys.exit(0 if all(R) else 1)
asyncio.run(main())
