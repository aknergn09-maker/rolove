# Ana (v11): turuncu çizgiden içeri kolon → soru (Ofset korunsun / Duvar kalınlaşsın), varsayılan kalınlaşsın; büyük girinti ve pencereli duvarda varsayılan ofset; kolon altındaki eski çizgi görünmez; ▾ alt çubuğu gizler
import os, pathlib, sys, asyncio
ROOT = pathlib.Path(__file__).resolve().parent.parent
URL = (ROOT / os.environ.get('PAGE', 'index.html')).as_uri()
OUT = ROOT / 'test' / 'out'; OUT.mkdir(exist_ok=True); os.chdir(OUT)
CHROME = os.environ.get('CHROME', '/usr/bin/google-chrome' if os.path.exists('/usr/bin/google-chrome') else None)
from playwright.async_api import async_playwright
R=[]
def ck(n,ok,i=''): R.append(bool(ok)); print(('PASS ' if ok else 'FAIL ')+n, i if not ok else '')
SETUP = """((side, ox)=>{RK.S.faceAsk=null; RK.S.cikAsk=null; const P=RK.P; P.nodes=[];P.lines=[];P.walls=[];P.rooms=[];P.openings=[];P.fills=[]; const C=[[0,0],[4,0],[4,3],[0,3]]; const ids=C.map(([x,y],i)=>{const id='a'+i; P.nodes.push({id,x,y}); return id}); for(let i=0;i<4;i++) P.lines.push({id:'A'+i,a:ids[i],b:ids[(i+1)%4],kind:'sketch'}); P.walls.push({id:'WA',nodes:ids,closed:true,t:0.2,side}); P.rooms.push({id:'rA',name:'A',ax:2,ay:1.5}); RK.commit(); RK.view.s=140; RK.view.ox=ox; RK.view.oy=230; RK.commit()})"""
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
        AR = "RK.P.rooms.filter(r=>!r.kind).map(r=>r._f?+RK.rA(r).toFixed(4):null)"; CUR = "RK.S.faceAsk&&RK.S.faceAsk.cur"; FL = "(RK.P.fills||[]).length"
        if await ev("!!document.querySelector('#tabs')"): await btn('#tabs button[data-tab=cizim]')
        # ▾ alt çubuk
        await btn('#fBar'); h = await ev("getComputedStyle(document.querySelector('#bar')).display"); await btn('#fBar'); h2 = await ev("getComputedStyle(document.querySelector('#bar')).display")
        ck('▾ tuşu alttaki araç çubuğunu gizler / tekrar açar', h=='none' and h2!='none', [h,h2])
        await btn('#cats button[data-cat=duz]'); await btn('#tools button[data-tool=cikinti]')
        # 1) köşe kolonu (ekteki gibi): alt turuncudan içeri 30, sağa turuncuya
        await ev(SETUP + "(1,-250)"); await btn('#sheet button[data-a=cikm][data-v=el]')
        for x,y in [(3.5,0),(3.5,0.3),(4,0.3)]: await ctap(x,y)
        ck('köşe kolonu: soru çıktı, varsayılan "Duvar kalınlaşsın", oda 12−0.5×0.3=11.85, dolgu 1', await ev(CUR)=='sabit' and await ev(AR)==[11.85] and await ev(FL)==1 and await ev("!!document.querySelector('#sheet button[data-a=faY]')"), [await ev(CUR), await ev(AR), await ev(FL)])
        hid = await ev("(()=>{const U=RK.underFillSet(); return RK.P.lines.filter(l=>U.has(l.id)).map(l=>{const a=RK.P.nodes.find(n=>n.id===l.a),b=RK.P.nodes.find(n=>n.id===l.b);return [a.x,a.y,b.x,b.y].map(v=>+v.toFixed(2))})})()")
        ck('  kolonun altında kalan eski turuncu çizgiler görünmüyor (2 parça)', len(hid)==2, hid)
        STR = "(()=>{const g=RK.wallGeom(RK.P.walls[0]); return g.quads.every(q=>q.poly.every(p=>Math.abs(p[0]+0.2)<1e-6||Math.abs(p[0]-4.2)<1e-6||Math.abs(p[1]+0.2)<1e-6||Math.abs(p[1]-3.2)<1e-6||Math.abs(p[0])<1e-6||Math.abs(p[0]-4)<1e-6||Math.abs(p[1])<1e-6||Math.abs(p[1]-3)<1e-6))})()"
        ck('  duvar (beyaz dış yüz) düz kaldı', await ev(STR), await ev("RK.P.walls[0].nodes.map(id=>{const n=RK.P.nodes.find(q=>q.id===id); return [n.x,n.y]})"))
        await pg.screenshot(path='t25_kose.png')
        await btn('#sheet button[data-a=faY]'); ck('  "Ofset korunsun": dolgu yok, duvar kolonu izledi, oda aynı', await ev(FL)==0 and await ev("RK.P.walls[0].nodes.length")>4 and await ev(AR)==[11.85], [await ev(FL), await ev(AR)])
        await btn('#sheet button[data-a=faN]'); ck('  tekrar "Duvar kalınlaşsın"', await ev(FL)==1 and await ev(STR))
        # 2) düz duvarda kolon
        await ev(SETUP + "(1,-80)"); await btn('#sheet button[data-a=cikm][data-v=el]')
        for x,y in [(1,0),(1,0.3),(2,0.3),(2,0)]: await ctap(x,y)
        ck('düz duvarda kolon 1×0.3: varsayılan kalınlaşsın, oda 11.7', await ev(CUR)=='sabit' and await ev(AR)==[11.7] and await ev(FL)==1, [await ev(CUR), await ev(AR)])
        # 3) büyük girinti (1 m derin): varsayılan ofset korunsun
        await ev(SETUP + "(1,-80)"); await ev("RK.view.s=80; RK.commit()"); await btn('#sheet button[data-a=cikm][data-v=el]')
        for x,y in [(1,0),(1,1),(2,1),(2,0)]: await ctap(x,y)
        ck('büyük girinti (1 m): varsayılan ofset korunsun (duvar izler), oda 11', await ev(CUR)=='kayar' and await ev(AR)==[11.0] and await ev(FL)==0, [await ev(CUR), await ev(AR)])
        # 4) dışa çıkıntı: soru yok, oda büyür
        await ev(SETUP + "(1,-80)"); await btn('#sheet button[data-a=cikm][data-v=el]')
        for x,y in [(1,0),(1,-0.5),(2,-0.5),(2,0)]: await ctap(x,y)
        ck('dışa çıkıntı: eskisi gibi (soru yok), oda 12.5', not await ev("!!RK.S.faceAsk") and await ev(AR)==[12.5], [await ev(AR)])
        # 5) laser ölçü: kolonlu odada sağ duvar ölçülünce kolon birlikte kayar
        await ev(SETUP + "(1,-250)"); await btn('#sheet button[data-a=cikm][data-v=el]')
        for x,y in [(3.5,0),(3.5,0.3),(4,0.3)]: await ctap(x,y)
        r = await ev("(()=>{const l=RK.P.lines.find(l=>{const a=RK.P.nodes.find(n=>n.id===l.a),b=RK.P.nodes.find(n=>n.id===l.b); return Math.abs(a.y-3)<1e-6&&Math.abs(b.y-3)<1e-6}); RK.applyMeasure(l, 4.5); const f=RK.P.fills[0]; const w=RK.P.walls[0].nodes.map(id=>RK.P.nodes.find(q=>q.id===id)); return [RK.P.fills.length, f.nodes.map(id=>{const n=RK.P.nodes.find(q=>q.id===id); return [+n.x.toFixed(3),+n.y.toFixed(3)]}), Math.max(...w.map(n=>n.x)), Math.min(...w.map(n=>n.y)), +RK.lineLen(l).toFixed(3)]})()")
        ck('lazerle oda 4.50 ölçülünce kolon köşede kaldı (sağ duvara ve alt duvara bitişik)', r[0]==1 and r[4]==4.5 and abs(r[1][-1][0]-r[2])<1e-3 and abs(r[1][0][1]-r[3])<1e-3, r)
        ck('JS hatası yok', not errs, errs[:3]); await b.close()
    print('TOPLAM', sum(R), '/', len(R)); sys.exit(0 if all(R) else 1)
asyncio.run(main())
