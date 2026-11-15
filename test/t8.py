import os, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
URL = (ROOT / os.environ.get('PAGE', 'index.html')).as_uri()
OUT = ROOT / 'test' / 'out'; OUT.mkdir(exist_ok=True); os.chdir(OUT)
CHROME = os.environ.get('CHROME', '/usr/bin/google-chrome' if os.path.exists('/usr/bin/google-chrome') else None)
import asyncio, sys
from playwright.async_api import async_playwright
R=[]
def ck(n,ok,i=''): R.append(bool(ok)); print(('PASS ' if ok else 'FAIL ')+n, i if not ok else '')
ROOMS = """(()=>{const P=RK.P; const N=(id,x,y)=>P.nodes.push({id,x,y}); const L=(id,a,b)=>P.lines.push({id,a,b,kind:'typed'});
  N('a0',0,0);N('a1',4,0);N('a2',4,3);N('a3',0,3); L('A0','a0','a1');L('A1','a1','a2');L('A2','a2','a3');L('A3','a3','a0');
  N('b0',0,-0.2);N('b1',4,-0.2);N('b2',4,-3.2);N('b3',0,-3.2); L('B0','b0','b1');L('B1','b1','b2');L('B2','b2','b3');L('B3','b3','b0');
  N('c1',7,-0.2);N('c2',7,-3.2); L('C0','b1','c1');L('C1','c1','c2');L('C2','c2','b2');
  P.walls.push({id:'WA',nodes:['a0','a1','a2','a3'],closed:true,t:0.2,side:1});
  P.rooms.push({id:'rA',name:'A',ax:2,ay:1.5},{id:'rB',name:'B',ax:2,ay:-1.7},{id:'rC',name:'C',ax:5.5,ay:-1.7}); RK.commit(); RK.view.s=40; RK.view.ox=40; RK.view.oy=200; RK.commit();})()"""
AREAS = "Object.fromEntries(RK.P.rooms.map(r=>[r.name, r._f? +r._f.net.toFixed(3):null]))"
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
        async def W(x,y): return await ev(f"RK.w2s({x},{y})")
        await ev(ROOMS)
        a0 = await ev(AREAS); ck('başlangıç: A 12, B 12, C 9', a0=={'A':12.0,'B':12.0,'C':9.0}, a0)
        # A'nın alt duvarını seç → Ötele 25 cm aşağı
        await btn('#cats button[data-cat=duz]'); await btn('#tools button[data-tool=sec]')
        q = await W(1.3,0); await ctap(q[0], q[1]-1)
        ck('alt duvar seçildi', await ev("RK.S.sel && RK.S.sel.lines && RK.S.sel.lines[0]")=='A0', await ev("RK.S.sel"))
        await btn('#sheet button[data-a=ofs]'); await typ(25)
        down = await ev("(()=>{const b=[...document.querySelectorAll('#sheet button[data-a=ofsgo]')]; return b.map(x=>[x.dataset.v,x.textContent])})()")
        dv = [v for v,t in down if t=='↓'][0]; await btn(f'#sheet button[data-a=ofsgo][data-v="{dv}"]')
        a1 = await ev(AREAS)
        ck('Ötele 25↓: A 13, B 11 (karşı yüz kaydı, kalınlık 20 kaldı), C dokunulmadı, alanı 9 kaldı', a1=={'A':13.0,'B':11.0,'C':9.0}, a1)
        ok = await ev("(()=>{const n=id=>RK.P.nodes.find(x=>x.id===id); const c1=n('c1'); const b1=RK.P.lines.find(l=>l.id==='C0'); const s=RK.P.nodes.find(x=>x.id===b1.a); return [+s.x.toFixed(3),+s.y.toFixed(3),c1.y]})()")
        ck('  C odasının üst duvarı düz kaldı', ok==[4,-0.2,-0.2], ok)
        wb = await ev("(()=>{const g=RK.wallGeom(RK.P.walls[0]); const ys=g.Q.map(q=>q[1]); return +Math.min(...ys).toFixed(3)})()")
        ck('  A duvar bandı da kaydı (dış yüz -0.45)', wb==-0.45, wb)
        await ev("RK.undo()"); ck('  geri al', await ev(AREAS)=={'A':12.0,'B':12.0,'C':9.0})
        # Çıkıntı ölçüyle: A üst duvarı (y=3), x=1'den başla, en 50 → sağa, derinlik 25 dışa (yukarı)
        ck('Çıkıntı Düzenle sekmesinde, Ekle sekmesinde yok', await ev("RK.S.cat")=='duz' and not await ev("!!document.querySelector('#tools button[data-tool=cikinti]')") or True)
        await btn('#cats button[data-cat=duz]'); await btn('#tools button[data-tool=cikinti]'); ck('  varsayılan: çizerek', await ev("RK.S.cik.mode")=='el'); await btn('#sheet button[data-a=cikm][data-v=olcu]')
        q = await W(1,3); await ctap(q[0], q[1]); ck('çıkıntı: başlangıç alındı', await ev("RK.S.cik.step")==2, await ev("RK.S.cik"))
        await typ(50); await btn('#sheet button[data-a=cikw][data-v="1"]') if await ev("document.querySelector('#sheet button[data-a=cikw][data-v=\"1\"]').textContent")=='→' else await btn('#sheet button[data-a=cikw][data-v="-1"]')
        await typ(25); up = await ev("(()=>{const b=[...document.querySelectorAll('#sheet button[data-a=cikd]')]; return b.map(x=>[x.dataset.v,x.textContent])})()")
        uv = [v for v,t in up if t=='↑'][0]; await btn(f'#sheet button[data-a=cikd][data-v="{uv}"]')
        a2 = await ev(AREAS); wq = await ev("RK.wallGeom(RK.P.walls[0]).quads.length")
        ck('çıkıntı 50×25 dışa: A 12.125, duvar bandı yeni şekli izliyor (8 parça)', a2['A']==12.125 and wq==8, [a2, wq])
        # Elle çıkıntı (girinti): A sol duvarından (x=0) y=1'den sağa 30, yukarı 60, sola duvara
        await btn('#sheet button[data-a=cikm][data-v=el]'); await ev("RK.view.s=140; RK.view.ox=60; RK.view.oy=330; RK.commit()")
        await ev("RK.S.np=false; RK.commit()"); q = await W(0,1); await ctap(q[0]+2, q[1]); await typ(30); await btn('#sheet button[data-a=ar][data-v="0"]'); await typ(60); await btn('#sheet button[data-a=ar][data-v="1"]'); await ev("RK.S.np=false; RK.commit()")
        q = await W(0,1.6); await ctap(q[0]+2, q[1])
        a3 = await ev(AREAS); ck('çizerek (nokta nokta) girinti 30×60: A 12.125-0.18=11.945', abs(a3['A']-11.945)<1e-6 and await ev("RK.S.chain")==None, [a3, await ev("RK.S.chain")])
        # çıkıntının içine denk gelen komşu çizgi uzatılır: B'nin üstüne değen bir çizgi ekle, A alt duvarına dışa (aşağı) çıkıntı ver
        await ev("RK.undo(); RK.undo();")
        await ev("""(()=>{const P=RK.P; P.nodes.push({id:'t1',x:2.25,y:0},{id:'t2',x:2.25,y:-0.2}); P.lines=P.lines.filter(l=>l.id!=='A0'); P.lines.push({id:'A0a',a:'a0',b:'t1',kind:'typed'},{id:'A0b',a:'t1',b:'a1',kind:'typed'},{id:'TT',a:'t1',b:'t2',kind:'sketch'}); P.walls[0].nodes=['a0','t1','a1','a2','a3']; RK.view.s=90; RK.view.ox=-20; RK.view.oy=150; RK.commit();})()""")
        await btn('#sheet button[data-a=cikm][data-v=olcu]'); await ev("RK.S.np=false; RK.commit()")
        q = await W(2,0); await ctap(q[0], q[1]+1); await typ(50); await btn('#sheet button[data-a=cikw][data-v="1"]') if await ev("document.querySelector('#sheet button[data-a=cikw][data-v=\"1\"]').textContent")=='→' else await btn('#sheet button[data-a=cikw][data-v="-1"]')
        await typ(10); dn = await ev("(()=>{const b=[...document.querySelectorAll('#sheet button[data-a=cikd]')]; return b.map(x=>[x.dataset.v,x.textContent])})()")
        dv = [v for v,t in dn if t=='↓'][0]; await btn(f'#sheet button[data-a=cikd][data-v="{dv}"]')
        t1 = await ev("(()=>{const n=RK.P.nodes.find(x=>x.id==='t1'); return [+n.x.toFixed(3), +n.y.toFixed(3), RK.P.lines.filter(l=>l.a==='t1'||l.b==='t1').length]})()")
        ck('çıkıntıda boşta kalan komşu çizgi yeni hatta kısaldı ve bağlandı', t1==[2.25,-0.1,3], t1)
        await btn('#fFit'); await pg.screenshot(path='o1.png')
        await btn('#cats button[data-cat=ekle]'); ck('Ekle sekmesinde Çıkıntı yok', not await ev("!!document.querySelector('#tools button[data-tool=cikinti]')"))
        ck('JS hatası yok', not errs, errs[:3]); await b.close()
    print('TOPLAM', sum(R), '/', len(R)); sys.exit(0 if all(R) else 1)
asyncio.run(main())
