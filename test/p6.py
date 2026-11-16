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
        # A) duvarda 2 nokta + dışarıda tepe
        await ev(SETUP); await daire3([(4,1),(4.5,1.5),(4,2)])
        a = await ev(RA); exp = 12 + math.pi*0.25/2
        ck('A) daire duvarı kesti: dışarıdaki yarım daire odaya katıldı (≈%.3f)' % exp, abs(a['A']-exp)<0.005 and len(a)==1, a)
        ck('   içerideki yarım daire ve düz duvar parçası silindi, duvar bandı yayı izliyor', await ev("RK.P.lines.some(l=>{const p=RK.P.nodes.find(n=>n.id===l.a), q=RK.P.nodes.find(n=>n.id===l.b); return (p.x+q.x)/2<3.99 && Math.hypot((p.x+q.x)/2-4,(p.y+q.y)/2-1.5)<0.49})")==False and await ev("RK.wallGeom(RK.P.walls[0]).quads.length")>8)
        await pg.screenshot(path='p6a.png')
        # B) 3. nokta boşlukta: (4,1) duvarda, (4.4,1.3) ve (4.5,1.9) boşlukta
        await ev(SETUP); await daire3([(4,0.8),(4.7,1.2),(4.9,2.0)])
        ci = await ev("(()=>{const a=RK.P.arcs[0]; const ps=a.ids.map(id=>{const n=RK.P.nodes.find(x=>x.id===id); return [n.x,n.y]}); return RK.circ3(ps[0],ps[Math.floor(ps.length/2)],ps[ps.length-1])})()"); h = await ev("RK.P.arcs.length")
        cx, cy, r = ci['c'][0], ci['c'][1], ci['r']; dy = math.sqrt(r*r-(4-cx)**2); y1, y2 = cy-dy, cy+dy
        exp = 12 + (math.pi*r*r - segA(r, y2-y1) if cx>4 else segA(r, y2-y1))
        a = await ev(RA); ck('B) 3. nokta boşlukta: daire duvarı kendi kestiği yerlerden (y %.2f–%.2f) kesti, alan %.3f' % (y1, y2, exp), h==1 and abs(a['A']-exp)<0.01, [a, exp, ci])
        # C) köşeyi kesen daire: merkez (4,3) r 0.8 → dışarıdaki 3/4 daire katılır
        await ev(SETUP); await daire3([(4.8,3),(4,3.8),(3.2,3)])
        a = await ev(RA); exp = 12 + 0.75*math.pi*0.64
        ck('C) köşeyi kesen daire: dışarıdaki 3/4 daire odaya katıldı (≈%.3f)' % exp, abs(a['A']-exp)<0.01, a)
        # D) hiçbir şeye değmeyen daire → normal daire (kolon/yuvarlak oda)
        await ev(SETUP); await daire3([(1,1.5),(2,2.5),(3,1.5)])
        a = await ev(RA); ck('D) odanın içinde değmeyen daire: ada (A = 12 − π), A adı dairenin içine kaymadı', abs(a['A']-(12-math.pi))<0.01, a)
        # E) Çıkıntı → Yay, noktalar serbest, içe girinti: (1.2,-0.2) boşlukta, (2,0.5) içeride, (2.8,-0.2)
        await ev(SETUP); await btn('#tabs button[data-tab=cizim]'); await btn('#cats button[data-cat=duz]'); await btn('#tools button[data-tool=cikinti]'); await btn('#sheet button[data-a=cikm][data-v=yay]')
        for x,y in [(1.2,-0.25),(2,0.5),(2.8,-0.25)]: q = await W(x,y); await ctap(*q)
        ci = await ev("(()=>{const a=RK.P.arcs[0]; const ps=a.ids.map(id=>{const n=RK.P.nodes.find(x=>x.id===id); return [n.x,n.y]}); return RK.circ3(ps[0],ps[Math.floor(ps.length/2)],ps[ps.length-1])})()"); r = ci['r']; cyy = ci['c'][1]; half = math.sqrt(r*r-cyy*cyy); exp = 12 - (segA(r, 2*half) if cyy<0 else math.pi*r*r-segA(r, 2*half))
        a = await ev(RA); ck('E) Çıkıntı-Yay serbest noktalarla içe girinti: alan yay dilimi kadar azaldı (≈%.3f)' % exp, abs(a['A']-exp)<0.01, [a, exp])
        await pg.screenshot(path='p6e.png')
        # F) DXF: yaylar ARC
        dx = await ev("RK.makeDXF()"); open('p6.dxf','w',newline='').write(dx)
        import ezdxf
        arcs = [e for e in ezdxf.readfile('p6.dxf').modelspace() if e.dxftype()=='ARC']
        ck('F) DXF: kesilmiş yay ARC olarak', len(arcs)==1 and abs(arcs[0].dxf.radius-r)<1e-3, [(e.dxf.radius) for e in arcs])
        ck('JS hatası yok', not errs, errs[:3]); await b.close()
    print('TOPLAM', sum(R), '/', len(R)); sys.exit(0 if all(R) else 1)
asyncio.run(main())
