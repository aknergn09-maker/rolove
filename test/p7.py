# ÖNİZLEME testi: sekmeler, kroki nokta adları, DXF
import os, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
URL = (ROOT / os.environ.get('PAGE', 'onizleme.html')).as_uri()
OUT = ROOT / 'test' / 'out'; OUT.mkdir(exist_ok=True); os.chdir(OUT)
CHROME = os.environ.get('CHROME', '/usr/bin/google-chrome' if os.path.exists('/usr/bin/google-chrome') else None)
import asyncio, sys, io
from playwright.async_api import async_playwright
R=[]
def ck(n,ok,i=''): R.append(bool(ok)); print(('PASS ' if ok else 'FAIL ')+n, i if not ok else '')
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path=CHROME, args=['--no-sandbox'])
        ctx=await b.new_context(**p.devices['iPhone 13']); pg=await ctx.new_page(); errs=[]; dlg=[]
        pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto(URL); await pg.evaluate("localStorage.clear()"); await pg.reload(); await pg.wait_for_timeout(300); ev=pg.evaluate
        async def btn(sel):
            r = await ev(f"(()=>{{const e=document.querySelector('{sel}'); if(!e||e.disabled) return null; const r=e.getBoundingClientRect(); return [r.left+r.width/2, r.top+r.height/2]}})()")
            if not r: return False
            await pg.touchscreen.tap(r[0], r[1]); await pg.wait_for_timeout(80); return True
        async def ctap(x,y):
            r = await ev("(()=>{const r=document.querySelector('#cv').getBoundingClientRect(); return [r.left,r.top]})()"); await pg.touchscreen.tap(r[0]+x, r[1]+y); await pg.wait_for_timeout(90)
        async def W(x,y): return await ev(f"RK.w2s({x},{y})")
        RA = "Object.fromEntries(RK.P.rooms.map(r=>[r.name, RK.rA(r)==null?null:+RK.rA(r).toFixed(2)]))"
        async def typ(v):
            if not await ev("!!document.querySelector('#sheet button[data-k=C]')"): await btn('#sheet button[data-a=np]')
            await btn('#sheet button[data-k="C"]')
            for ch in str(v): await btn(f'#sheet button[data-k="{ch}"]')
            await ev("RK.S.np=false; RK.commit()")
        import math
        SETUP = """(()=>{const P=RK.P; P.nodes=[];P.lines=[];P.rooms=[];P.walls=[];P.arcs=[];P.openings=[]; const C=[[0,0],[4,0],[4,3],[0,3]]; const ids=C.map(([x,y],i)=>{const id='a'+i; P.nodes.push({id,x,y}); return id}); for(let i=0;i<4;i++) P.lines.push({id:'A'+i,a:ids[i],b:ids[(i+1)%4],kind:'sketch'}); P.walls.push({id:'WA',nodes:ids,closed:true,t:0.2,side:1}); P.rooms.push({id:'rA',name:'A',ax:2,ay:1.5}); RK.commit(); RK.view.s=55; RK.view.ox=40; RK.view.oy=330; RK.commit();})()"""
        async def daire3(pts):
            await btn('#tabs button[data-tab=cizim]'); await btn('#cats button[data-cat=ciz]'); await btn('#tools button[data-tool=daire]'); await btn('#sheet button[data-a=drm][data-v="3n"]')
            for x,y in pts: q = await W(x,y); await ctap(*q)
        def segA(r, c): th = 2*math.asin(c/(2*r)); return r*r/2*(th-math.sin(th))
        async def px(wx, wy):
            return await ev(f"(()=>{{const c=document.querySelector('#cv'); const g=c.getContext('2d'); const [X,Y]=RK.w2s({wx},{wy}); const d=window.devicePixelRatio||1; const v=g.getImageData(Math.round(X*d),Math.round(Y*d),1,1).data; return [v[0],v[1],v[2]]}})()")
        green = lambda c: c[1]>150 and c[0]<120 and c[2]<150
        # 1) Daire: 2 nokta koy, 3. noktayı parmak ekrandayken (bırakmadan) önizle
        await ev(SETUP); await btn('#tabs button[data-tab=cizim]'); await btn('#cats button[data-cat=ciz]'); await btn('#tools button[data-tool=daire]'); await btn('#sheet button[data-a=drm][data-v="3n"]')
        for x,y in [(4,1),(4.5,1.5)]: q = await W(x,y); await ctap(*q)
        r0 = await ev("(()=>{const r=document.querySelector('#cv').getBoundingClientRect(); return [r.left,r.top]})()"); q = await W(4,2)
        cdp = await ctx.new_cdp_session(pg); await cdp.send('Input.dispatchTouchEvent', {'type':'touchStart','touchPoints':[{'x':r0[0]+q[0],'y':r0[1]+q[1]}]}); await pg.wait_for_timeout(120)
        outer, inner = await px(4.5,1.5), await px(3.5,1.5)
        await pg.screenshot(path='p7a.png')
        ck('önizleme: kalacak dış yay kalın yeşil, atılacak iç yay yeşil değil', green(outer) and not green(inner), [outer, inner])
        redp = await px(4,1.5); ck('  silinecek duvar parçası kırmızı', redp[0]>200 and redp[1]<150, redp)
        plan = await ev("(()=>{const g=RK.circ3(...RK.S.dr.pts, RK.s2w(...RK.w2s(4,2))); const p=RK.circlePlan(g,null); return p.pieces.map(x=>[x.p0,x.p1].map(q=>q.map(v=>+v.toFixed(3))))})()")
        await cdp.send('Input.dispatchTouchEvent', {'type':'touchEnd','touchPoints':[]}); await pg.wait_for_timeout(150)
        res = await ev("RK.P.arcs.map(a=>{const ps=a.ids.map(id=>RK.P.nodes.find(n=>n.id===id)); return [ps[0],ps[ps.length-1]].map(n=>[+n.x.toFixed(3),+n.y.toFixed(3)])})")
        ck('sonuç önizlemeyle birebir aynı (aynı yay, aynı uçlar)', sorted(map(sorted, res))==sorted(map(sorted, plan)), [plan, res])
        a = await ev(RA); ck('  alan 12 + yarım daire', abs(a['A']-(12+math.pi*0.125))<0.005, a)
        # 2) Çıkıntı-Yay önizleme = sonuç (içe)
        await ev(SETUP); await btn('#cats button[data-cat=duz]'); await btn('#tools button[data-tool=cikinti]'); await btn('#sheet button[data-a=cikm][data-v=yay]')
        for x,y in [(1.2,-0.25),(2,0.5)]: q = await W(x,y); await ctap(*q)
        q = await W(2.8,-0.25); await cdp.send('Input.dispatchTouchEvent', {'type':'touchStart','touchPoints':[{'x':r0[0]+q[0],'y':r0[1]+q[1]}]}); await pg.wait_for_timeout(120)
        ci = await ev("RK.circ3(...RK.S.cik.pts, RK.s2w(...RK.w2s(2.8,-0.25)))"); top = [ci['c'][0], ci['c'][1]+ci['r']]; bot = [ci['c'][0], ci['c'][1]-ci['r']]
        pt, pb = await px(*top), await px(*bot)
        ck('Çıkıntı-Yay önizleme: içerideki yay yeşil, dışarıdaki değil', green(pt) and not green(pb), [pt, pb, ci])
        await cdp.send('Input.dispatchTouchEvent', {'type':'touchEnd','touchPoints':[]}); await pg.wait_for_timeout(150)
        a = await ev(RA); ck('  sonuç: içe girinti oldu', a['A']<12, a)
        # 3) Köşe yuvarla (fillet) R=100 sağ üst köşe
        await ev(SETUP); await btn('#cats button[data-cat=duz]'); await btn('#tools button[data-tool=buda]'); await btn('#sheet button[data-a=bum][data-v=yuvarla]')
        ck('Düzenle → Buda/Yuvarla → ◜ Yuvarla', await ev("RK.S.bu.mode")=='yuvarla')
        await btn('#sheet button[data-a=np]'); [await btn(f'#sheet button[data-k="{c}"]') for c in '100']; await btn('#sheet button[data-a=np]')
        q = await W(4,3); await ctap(q[0]-2, q[1]+2)
        ck('  köşe seçildi, önizleme hazır', await ev("RK.S.bu.fc")=='a2' and 'Yeşil yay' in await ev("document.querySelector('#sheet').textContent"))
        mid = [3+math.cos(math.pi/4), 2+math.sin(math.pi/4)]; pm = await px(*mid); await pg.screenshot(path='p7c.png')
        ck('  önizlemede yay yeşil çiziliyor', green(pm), pm)
        await btn('#sheet button[data-a=filok]')
        a = await ev("RK.rA(RK.P.rooms[0])"); exp = 12 - (1 - math.pi/4)
        ck('Yuvarla: köşe R 1.00 ile kesildi, alan 12 − (1 − π/4) = %.4f' % exp, abs(a-exp)<1e-4, a)
        ar = await ev("(()=>{const a=RK.P.arcs[0]; const ps=a.ids.map(id=>RK.P.nodes.find(n=>n.id===id)); return ps.map(n=>+Math.hypot(n.x-3,n.y-2).toFixed(4))})()")
        ck('  yay iki duvara teğet (merkez 3,2; tüm noktalar r=1)', all(abs(v-1)<1e-6 for v in ar), ar)
        ck('  duvar bandı yayı izliyor', await ev("RK.wallGeom(RK.P.walls[0]).quads.length")>8)
        # büyük yarıçap uyarısı
        await btn('#sheet button[data-a=np]'); await btn('#sheet button[data-k="C"]'); [await btn(f'#sheet button[data-k="{c}"]') for c in '400']; await btn('#sheet button[data-a=np]'); q = await W(0,0); await ctap(q[0]+2, q[1]-2)
        ck('  sığmayan yarıçapta uyarı (en çok … cm)', 'en çok' in await ev("document.querySelector('#sheet').textContent"))
        ck('JS hatası yok', not errs, errs[:3]); await b.close()
    print('TOPLAM', sum(R), '/', len(R)); sys.exit(0 if all(R) else 1)
asyncio.run(main())
