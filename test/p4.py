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
        LEN = "Object.fromEntries(RK.P.lines.filter(l=>!l.step).map(l=>[l.id, +RK.lineLen(l).toFixed(4)]))"
        await ev("RK.view.s=40; RK.view.ox=40; RK.view.oy=420; RK.commit()")
        # 3 noktalı daire: (2,2) merkezli r=1 → (1,2),(3,2),(2,3)
        await btn('#tools button[data-tool=daire]'); await btn('#sheet button[data-a=drm][data-v="3n"]')
        for x,y in [(1,2),(3,2),(2,3)]: q = await W(x,y); await ctap(*q)
        r = await ev("(()=>{const ns=RK.P.nodes; const d=ns.map(n=>Math.hypot(n.x-2,n.y-2)); return [ns.length, Math.min(...d), Math.max(...d)]})()")
        ck('3 noktadan daire: düğümler r=1 üstünde', r[0]>=12 and abs(r[1]-1)<1e-6 and abs(r[2]-1)<1e-6, r)
        a = await ev("RK.P.rooms.map(r=>+RK.rA(r).toFixed(2))"); ck('  kapalı → alan ≈ π (3.14)', any(abs(v-3.14)<0.02 for v in a), a)
        # merkez + yazılan r
        await btn('#sheet button[data-a=drm][data-v=mr]'); q = await W(6,2); await ctap(*q); await btn('#sheet button[data-a=np]'); [await btn(f'#sheet button[data-k="{c}"]') for c in '50']; await btn('#sheet button[data-a=drok]')
        r2 = await ev("(()=>{const ns=RK.P.nodes.filter(n=>n.x>4); const cx=ns.reduce((s,n)=>s+n.x,0)/ns.length, cy=ns.reduce((s,n)=>s+n.y,0)/ns.length; const d=ns.map(n=>Math.hypot(n.x-cx,n.y-cy)); return [Math.min(...d), Math.max(...d)]})()")
        ck('merkez + 50 cm yarıçap', abs(r2[0]-0.5)<1e-6 and abs(r2[1]-0.5)<1e-6, r2)
        # Buda / Uzat / Birleştir
        await ev("""(()=>{const P=RK.P; P.nodes=[];P.lines=[];P.rooms=[];P.walls=[]; const N=(id,x,y)=>P.nodes.push({id,x,y}); const L=(id,a,b)=>P.lines.push({id,a,b,kind:'sketch'});
          N('a',0,0);N('b',4,0); L('H','a','b'); N('c',2,-1);N('d',2,1); L('V','c','d'); N('e',6,-1);N('f',6,4); L('V2','e','f'); N('g',0,3);N('h',3,3); L('T','g','h'); N('i',4.5,4);N('j',4.5,5.5); L('S','i','j'); RK.commit(); RK.view.s=40; RK.view.ox=40; RK.view.oy=330; RK.commit();})()""")
        await btn('#cats button[data-cat=duz]'); await btn('#tools button[data-tool=buda]')
        q = await W(3,0); await ctap(q[0], q[1]-2)
        Lb = await ev(LEN); ck('Buda: H çizgisinin V ile kesişiminden sağ parçası silindi (kalan 2.00)', 2.0 in Lb.values() and 4.0 not in Lb.values(), Lb)
        await btn('#sheet button[data-a=bum][data-v=uzat]')
        q = await W(2.9,3); await ctap(q[0], q[1]-2)
        tx = await ev("(()=>{const n=RK.P.nodes.find(n=>n.id==='h'); return [n.x,n.y]})()")
        ck('Uzat: T çizgisi sağ ucundan V2\'ye kadar uzadı (x=6)', abs(tx[0]-6)<1e-6 and abs(tx[1]-3)<1e-6, tx)
        await btn('#sheet button[data-a=bum][data-v=birles]'); q = await W(4,3); await ctap(q[0], q[1]-2); q = await W(4.5,5); await ctap(q[0]+2, q[1])
        cn = await ev("(()=>{const n=id=>RK.P.nodes.find(x=>x.id===id); return RK.P.lines.filter(l=>!l.step).map(l=>[l.a,l.b].map(id=>{const p=RK.P.nodes.find(x=>x.id===id); return [+p.x.toFixed(3),+p.y.toFixed(3)]}))})()")
        ck('Birleştir: T ve S kesişim (4.5,3) noktasında köşe oldu', any(([4.5,3.0] in seg) for seg in cn) and await ev("RK.P.lines.some(l=>{const a=RK.P.nodes.find(n=>n.id===l.a), b=RK.P.nodes.find(n=>n.id===l.b); return Math.abs(a.x-4.5)<1e-6&&Math.abs(b.x-4.5)<1e-6&&Math.abs(Math.min(a.y,b.y)-3)<1e-6&&Math.abs(Math.max(a.y,b.y)-5.5)<1e-6})"), cn)
        # dairesel merdiven: merkez (3,3) r=1.5 yarım daire (üst), dışa 100 cm, 12 rıh
        await ev("(()=>{const P=RK.P; P.nodes=[];P.lines=[];P.rooms=[];P.walls=[]; P.stepSets=[]; RK.commit(); RK.view.s=40; RK.view.ox=40; RK.view.oy=420; RK.commit();})()")
        await btn('#tabs button[data-tab=cizim]'); await btn('#cats button[data-cat=ekle]'); await btn('#tools button[data-tool=merdiven]'); await btn('#sheet button[data-a=mkm][data-v=yuv]')
        for x,y in [(1.5,3),(3,4.5),(4.5,3)]: q = await W(x,y); await ctap(*q)
        ck('dairesel: 3 nokta alındı → genişlik/rıh', await ev("RK.S.yv.step")==1)
        await btn('#sheet button[data-a=yvf][data-v=w]'); [await btn(f'#sheet button[data-k="{c}"]') for c in '100']
        await btn('#sheet button[data-a=yvf][data-v=n]'); [await btn(f'#sheet button[data-k="{c}"]') for c in '12']
        await btn('#sheet button[data-a=yvok][data-v="1"]')
        st = await ev("RK.P.lines.filter(l=>l.step).map(l=>{const a=RK.P.nodes.find(n=>n.id===l.a), b=RK.P.nodes.find(n=>n.id===l.b); return [+Math.hypot(a.x-3,a.y-3).toFixed(3), +Math.hypot(b.x-3,b.y-3).toFixed(3)]})")
        ck('12 rıh: uçlar çerçevede, 10 ışınsal basamak, r 1.5 → 2.5', len(st)==10 and all(sorted(x)==[1.5,2.5] for x in st), st)
        mr = await ev("RK.P.rooms.filter(r=>r.kind==='merdiven').map(r=>+RK.rA(r).toFixed(2))")
        ck('  Merdiven alanı = π(2.5²−1.5²)/2 ≈ 6.28', len(mr)==1 and abs(mr[0]-6.28)<0.03, mr)
        ck('komut satırında undefined yok', 'undefined' not in await ev("document.querySelector('#cmd').textContent"))
        await btn('#fFit'); await pg.screenshot(path='p4.png')
        ck('JS hatası yok', not errs, errs[:3]); await b.close()
    print('TOPLAM', sum(R), '/', len(R)); sys.exit(0 if all(R) else 1)
asyncio.run(main())
