# ÖNİZLEME (v11.5 tabanı + aşamalar) uçtan uca: duvarlı oda, kapı, köşe kolonu (kalınlaşsın), lazer ölçü, köşegen + geometriyi hesapla, yükseklik, kroki nokta adı, DXF (kolon altındaki eski çizgi ve kapı boşluğu yok)
import os, pathlib, sys, asyncio
ROOT = pathlib.Path(__file__).resolve().parent.parent
URL = (ROOT / os.environ.get('PAGE', 'onizleme.html')).as_uri()
if 'onizleme' not in URL: URL = (ROOT / 'onizleme.html').as_uri()
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
            await pg.touchscreen.tap(r[0], r[1]); await pg.wait_for_timeout(90); return True
        async def ctap(x,y):
            r = await ev("(()=>{const r=document.querySelector('#cv').getBoundingClientRect(); return [r.left,r.top]})()"); q = await ev(f"RK.w2s({x},{y})"); await pg.touchscreen.tap(r[0]+q[0], r[1]+q[1]); await pg.wait_for_timeout(200)
        async def typ(v):
            await btn('#sheet button[data-a=np]')
            for c in str(v): await btn(f'#sheet button[data-k="{c}"]')
        AR = "RK.P.rooms.filter(r=>!r.kind).map(r=>r._f?+RK.rA(r).toFixed(3):null)"; TOAST="document.querySelector('#toast').textContent"
        ck('üstte Çizim / Ölçüm / Kroki sekmeleri, ▾ tuşu', await ev("document.querySelectorAll('#tabs button').length")>=3 and await ev("!!document.querySelector('#fBar')"))
        # duvarlı oda 5×4 (duvar aracı)
        await btn('#tabs button[data-tab=cizim]'); await ev("RK.view.s=45; RK.view.ox=50; RK.view.oy=290; RK.commit()"); await btn('#cats button[data-cat=ciz]'); await btn('#tools button[data-tool=duvar]')
        for x,y in [(0,0),(5,0),(5,4),(0,4),(0,0)]: await ctap(x,y)
        ck('duvarlı oda 5×4 = 20', await ev(AR)==[20.0], [await ev(AR), await ev(TOAST)])
        # kapı (alt duvar, 1–1.9)
        n = await ev("(()=>{const a=RK.nodeAt([1,0]), b=RK.nodeAt([1.9,0]); RK.addOpening('kapi', a, b, 0, 0.9); RK.commit(); return RK.P.openings.length})()")
        # köşe kolonu: sağ üst köşe, turuncudan içeri 30×40
        await btn('#cats button[data-cat=duz]'); await btn('#tools button[data-tool=cikinti]'); await btn('#sheet button[data-a=cikm][data-v=el]')
        await ev("RK.view.s=110; RK.view.ox=-300; RK.view.oy=560; RK.commit()")
        for x,y in [(4.6,4),(4.6,3.7),(5,3.7)]: await ctap(x,y)
        ck('köşe kolonu: varsayılan "Duvar kalınlaşsın", oda 20 − 0.4×0.3 = 19.88', await ev("RK.S.faceAsk&&RK.S.faceAsk.cur")=='sabit' and await ev(AR)==[19.88] and await ev("RK.P.fills.length")==1, [await ev(AR), await ev(TOAST)])
        await pg.screenshot(path='p12_kolon.png')
        # lazer: alt çizgi 5.20 (kapının sağındaki parça değil, tüm alt duvar parçaları; sol alt parçayı ölç)
        await btn('#tabs button[data-tab=olcum]'); await ev("RK.view.s=45; RK.view.ox=50; RK.view.oy=290; RK.commit()")
        await btn('#tools button[data-tool=olc]'); await ctap(0.1, 2); await typ(410); await btn('#sheet button[data-a=msok]')
        L = await ev("(()=>{const l=RK.P.lines.find(l=>{const a=RK.P.nodes.find(n=>n.id===l.a),b=RK.P.nodes.find(n=>n.id===l.b); return Math.abs(a.x-b.x)<1e-3 && Math.min(a.x,b.x)<0.5}); return l&&[l.kind, +RK.lineLen(l).toFixed(3)]})()")
        ck('Ölç: sol duvar 4.10 yazıldı ve oturdu', L==['laser',4.1], [L, await ev(TOAST)])
        ck('  kolon köşede kaldı (sağ üst köşeye bitişik)', await ev("(()=>{const f=RK.P.fills[0]; const ps=f.nodes.map(id=>RK.P.nodes.find(n=>n.id===id)); const mx=Math.max(...RK.P.walls[0].nodes.map(id=>RK.P.nodes.find(n=>n.id===id).x)), my=Math.max(...RK.P.walls[0].nodes.map(id=>RK.P.nodes.find(n=>n.id===id).y)); return ps.some(n=>Math.abs(n.x-mx)<1e-3) && ps.some(n=>Math.abs(n.y-my)<1e-3)})()"))
        # kontrol: köşegen (sol alt → sağ alt kapının... oda içinden: (0,0) → (4.6, 3.7) kolon köşesi değil; (0,0)→(0,4) değil; sol alt → kolon köşesi)
        await btn('#tools button[data-tool=kontrol]')
        c = await ev("(()=>{const ns=RK.P.nodes; const a=ns.reduce((m,n)=>(n.x+n.y<m.x+m.y?n:m)); return [a.x,a.y]})()")
        k = await ev("(()=>{const f=RK.P.fills[0]; const ps=f.nodes.map(id=>RK.P.nodes.find(n=>n.id===id)); const q=ps.reduce((m,n)=>(n.x+n.y>m.x+m.y?m:n)); return [q.x,q.y]})()")
        k2 = await ev("(()=>{const f=RK.P.fills[0]; const ps=f.nodes.map(id=>RK.P.nodes.find(n=>n.id===id)); const q=ps.find(n=>ps.every(m=>m.x>=n.x-1e-6)&&ps.every(m=>m.y>=n.y-1e-6)); return q?[q.x,q.y]:null})()")
        await ctap(*c); await ctap(*k2)
        ck('Kontrol: oda içinden köşegen (sol alt → kolon iç köşesi) seçildi', await ev("!!RK.S.kt.b"), [c, k2, await ev(TOAST)])
        await typ(600); await btn('#sheet button[data-a=dgok]'); await btn('#sheet button[data-a=calc]'); await btn('#sheet button[data-a=cok]')
        d = await ev("(()=>{const g=RK.P.diags[0]; const a=RK.P.nodes.find(n=>n.id===g.a), b=RK.P.nodes.find(n=>n.id===g.b); return +Math.hypot(a.x-b.x,a.y-b.y).toFixed(3)})()")
        ck('  Geometriyi hesapla → Onayla: köşegen 6.00', abs(d-6.0)<2e-3, d)
        ck('  kolon dolgusu hâlâ köşede, tek parça', await ev("RK.P.fills.length")==1)
        # yükseklik
        await btn('#tools button[data-tool=yukseklik]'); await ctap(2,2); await typ(280); await btn('#sheet button[data-a=hsok]')
        ck('Yükseklik: oda 2.80', await ev("RK.P.rooms.find(r=>!r.kind).h")==2.8)
        # kroki nokta adı
        await btn('#tabs button[data-tab=kroki]')
        if not await ev("RK.S.tool==='nokta'"): await btn('#tools button[data-tool=nokta]')
        pg.once('dialog', lambda d: asyncio.ensure_future(d.accept('101')))
        await ctap(*c); await pg.wait_for_timeout(300); first = await ev("(RK.P.pts||[]).length")
        ck('Kroki: köşeye dokununca nokta adı verildi', first==1, [first, await ev(TOAST)])
        dxf = await ev("RK.makeDXF()")
        segs=[]; ls=dxf.split('\n')
        for i in range(len(ls)-1):
            if ls[i].strip()=='LINE' and ls[i-1].strip()=='0':
                g={}; j=i+1
                while j<len(ls)-1 and ls[j].strip()!='0': g[ls[j].strip()]=ls[j+1].strip(); j+=2
                segs.append((g.get('8'), float(g['10']),float(g['20']),float(g['11']),float(g['21'])))
        gap = await ev("(()=>{const g=RK.opGeom(RK.P.openings[0]); return [g.mid[0], g.mid[1]]})()")
        cross = [s for s in segs if s[0].startswith('CIZGI') and abs((s[3]-s[1])*(gap[1]-s[2])-(s[4]-s[2])*(gap[0]-s[1]))<1e-6 and min(s[1],s[3])-1e-6<=gap[0]<=max(s[1],s[3])+1e-6 and min(s[2],s[4])-1e-6<=gap[1]<=max(s[2],s[4])+1e-6]
        ck('DXF: kapı boşluğunda oda çizgisi yok', not cross, cross)
        hm = await ev("(()=>{const U=RK.underFillSet(); return RK.P.lines.filter(l=>U.has(l.id)).map(l=>{const a=RK.P.nodes.find(n=>n.id===l.a),b=RK.P.nodes.find(n=>n.id===l.b); return [(a.x+b.x)/2,(a.y+b.y)/2]})})()")
        on = lambda s,p: abs((s[3]-s[1])*(p[1]-s[2])-(s[4]-s[2])*(p[0]-s[1]))<1e-6 and min(s[1],s[3])-1e-6<=p[0]<=max(s[1],s[3])+1e-6 and min(s[2],s[4])-1e-6<=p[1]<=max(s[2],s[4])+1e-6
        bad = [p for p in hm if any(on(s,p) for s in segs if s[0].startswith('CIZGI'))]
        ck('DXF: kolon altındaki eski çizgiler yazılmadı', len(hm)==2 and not bad, [hm, bad])
        await btn('#tabs button[data-tab=cizim]'); await ev("RK.fit()"); await pg.screenshot(path='p12.png')
        ck('JS hatası yok', not errs, errs[:3]); await b.close()
    print('TOPLAM', sum(R), '/', len(R)); sys.exit(0 if all(R) else 1)
asyncio.run(main())
