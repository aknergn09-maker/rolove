# Ölç: beyaz çizgi değen iç duvarda kırılır, parça ölçülür; kolon iki ayrı duvar arasında (T), kolon altındaki eski beyaz çizgi silinir
import os, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
URL = (ROOT / os.environ.get('PAGE', 'index.html')).as_uri()
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
            await pg.touchscreen.tap(r[0], r[1]); await pg.wait_for_timeout(80); return True
        async def ctap(x,y):
            r = await ev("(()=>{const r=document.querySelector('#cv').getBoundingClientRect(); return [r.left,r.top]})()"); await pg.touchscreen.tap(r[0]+x, r[1]+y); await pg.wait_for_timeout(120)
        async def W(x,y): return await ev(f"RK.w2s({x},{y})")
        async def typ(v):
            if not await ev("!!document.querySelector('#sheet button[data-k=C]')"): await btn('#sheet button[data-a=np]')
            await btn('#sheet button[data-k="C"]')
            for ch in str(v): await btn(f'#sheet button[data-k="{ch}"]')
        TABS = await ev("!!document.querySelector('#tabs')")
        async def go(cat, tool):
            if TABS: await btn('#tabs button[data-tab=%s]' % ('olcum' if cat=='olc' else 'cizim'))
            if not (TABS and cat=='olc'): await btn(f'#cats button[data-cat={cat}]')
            await btn(f'#tools button[data-tool={tool}]')
        # 6×3 oda, bant içte; ortada iç duvar (x=3, bandı solda: yüzü x=2.8), iki ucu dış duvarın beyaz çizgisinde
        await ev("""(()=>{const P=RK.P; P.nodes=[];P.lines=[];P.walls=[];P.rooms=[];P.openings=[]; const C=[[0,0],[6,0],[6,3],[0,3]]; const ids=C.map(([x,y],i)=>{const id='a'+i; P.nodes.push({id,x,y}); return id}); for(let i=0;i<4;i++) P.lines.push({id:'A'+i,a:ids[i],b:ids[(i+1)%4],kind:'sketch'}); P.walls.push({id:'WA',nodes:ids,closed:true,t:0.2,side:1}); RK.commit(); if(RK.wallGeom(P.walls[0]).Q.some(q=>q[1]<-0.1)) P.walls[0].side=-1;
          P.nodes.push({id:'b0',x:3,y:0.2},{id:'b1',x:3,y:2.8}); P.lines.push({id:'B0',a:'b0',b:'b1',kind:'sketch'}); P.walls.push({id:'WB',nodes:['b0','b1'],closed:false,t:0.2,side:1}); RK.commit(); if(!RK.wallGeom(P.walls[1]).Q.some(q=>q[0]<2.9)) P.walls[1].side=-1;
          P.nodes.push({id:'f0',x:0.2,y:0.2}); P.lines.push({id:'FL',a:'f0',b:'b0',kind:'sketch',face:true}); P.rooms.push({id:'rL',name:'Sol',ax:1.5,ay:1.5},{id:'rR',name:'Sağ',ax:4.5,ay:1.5}); RK.commit(); RK.view.s=80; RK.view.ox=10; RK.view.oy=300; RK.commit();})()""")
        AR = "RK.P.rooms.map(r=>r._f? +RK.rA(r).toFixed(4):null)"
        ck('kurulum: iç duvar iki odayı ayırıyor (sol 2.6×2.6=6.76, sağ 2.8×2.6=7.28)', await ev(AR)==[6.76,7.28], await ev(AR))
        # Ölç: sol odada alt beyaz çizgiye dokun → köşeden iç duvarın yüzüne kadar olan parça
        await go('olc','olc'); q = await W(1.5, 0.2); await ctap(*q)
        st = await ev("[!!RK.S.ms.dim, RK.S.ms.fs && +Math.hypot(RK.S.ms.fs[1][0]-RK.S.ms.fs[0][0],RK.S.ms.fs[1][1]-RK.S.ms.fs[0][1]).toFixed(3), document.querySelector('#sheet').textContent.includes('parça')]")
        ck('beyaz çizgi iç duvarda kırıldı: seçilen parça köşeden iç duvara 2.60', st==[True,2.6,True], st)
        await typ(270); await btn('#sheet button[data-a=msok]')
        b0 = await ev("(()=>{const n=RK.P.nodes.find(q=>q.id==='b0'), m=RK.P.nodes.find(q=>q.id==='b1'), a=RK.P.nodes.find(q=>q.id==='a0'); return [+(n.x-0.2-(a.x+0.2)).toFixed(4),+(n.y-a.y).toFixed(4),+(m.x-n.x).toFixed(4)]})()")
        ck('  2.70 ölçüldü: köşe yüzü → iç duvar yüzü tam 2.70, iç duvar ucu beyaz çizgide kaldı, iç duvar düz', b0==[2.7,0.2,0], [b0, await ev("document.querySelector('#toast').textContent")])
        ck('  sol oda genişliği 2.70 ile hesaplandı', abs((await ev(AR))[0] - 2.7*(await ev("(()=>{const a=RK.P.nodes.find(q=>q.id==='a0'), d=RK.P.nodes.find(q=>q.id==='a3'); return d.y-a.y-0.4})()")))<1e-3, await ev(AR))
        q = await W(4.5, 0.2); await ctap(*q); st2 = await ev("RK.S.ms.fs && +Math.hypot(RK.S.ms.fs[1][0]-RK.S.ms.fs[0][0],RK.S.ms.fs[1][1]-RK.S.ms.fs[0][1]).toFixed(3)"); exp2 = await ev("(()=>{const n=RK.P.nodes.find(q=>q.id==='b0'), a=RK.P.nodes.find(q=>q.id==='a1'); return +((a.x-0.2)-n.x).toFixed(3)})()")
        ck('  sağ odada dokununca iç duvardan sağ köşeye parça seçilir', st2==exp2, [st2, exp2])
        await ev("RK.S.ms.sel=null; RK.commit()")
        await pg.screenshot(path='t22a.png')
        # kolon: alt beyaz çizgi ile iç duvarın beyaz çizgisi arasında (iki ayrı duvar)
        await go('duz','cikinti'); await btn('#sheet button[data-a=cikm][data-v=el]')
        fx, fy0 = await ev("(()=>{const n=RK.P.nodes.find(q=>q.id==='b0'); return [n.x-0.2, n.y]})()"); a0 = await ev(AR); await ev(f"RK.view.s=220; RK.view.ox={200-fx*220}; RK.view.oy={330+fy0*220}; RK.commit()")
        for x,y in [(fx-0.5,fy0),(fx-0.5,fy0+0.16),(fx,fy0+0.16)]: q = await W(x,y); await ctap(*q); await pg.wait_for_timeout(150)
        a = await ev(AR); fl = await ev("(RK.P.fills||[]).length")
        ck('kolon iki ayrı duvar arasında: duvar dolgusu, sol oda 0.5×0.16 küçüldü, sağ oda aynı', fl==1 and a[0] is not None and abs(a[0]-(a0[0]-0.08))<1e-3 and a[1]==a0[1], [fl, a0, a, await ev("document.querySelector('#toast').textContent")])
        vis = await ev("(()=>{const g=RK.wallGeom(RK.P.walls[0]); const q=g.quads.find(q=>Math.abs(q.poly[3][1]-q.poly[2][1])<1e-3 && q.poly[3][1]>q.poly[0][1]+0.1 && q.poly[3][1]<1); return RK.faceVisible(q.poly[3],q.poly[2]).map(s=>s.map(p=>+p[0].toFixed(3)))})()")
        lf = await ev("RK.P.lines.filter(l=>{const a=RK.P.nodes.find(n=>n.id===l.a), b=RK.P.nodes.find(n=>n.id===l.b); return Math.abs(a.y-b.y)<1e-4 && Math.abs(a.y-%s)<1e-3 && !l.step}).map(l=>{const a=RK.P.nodes.find(n=>n.id===l.a), b=RK.P.nodes.find(n=>n.id===l.b); return [+Math.min(a.x,b.x).toFixed(3), +Math.max(a.x,b.x).toFixed(3)]})" % fy0)
        ck('  yüz boyunca çizilmiş gerçek oda çizgisi kolonun altında silindi', not any(fx-0.5+1e-3 < (a+b)/2 < fx-1e-3 for a,b in lf) and any(abs(b-(fx-0.5))<1e-3 for a,b in lf), [lf, fx])
        ck('  kolonun altındaki eski beyaz çizgi silindi (kolon aralığı görünmüyor)', len(vis)==2 and abs(vis[0][1]-(fx-0.5))<1e-3 and abs(vis[1][0]-fx)<1e-3, [vis, fx])
        await pg.screenshot(path='t22b.png')
        # kolondan sonra ölçü: kolondan sola
        await ev('RK.view.s=80; RK.view.ox=10; RK.view.oy=300; RK.commit()'); await go('olc','olc'); q = await W(1.2, fy0); await ctap(*q); st3 = await ev("RK.S.ms.fs && +Math.hypot(RK.S.ms.fs[1][0]-RK.S.ms.fs[0][0],RK.S.ms.fs[1][1]-RK.S.ms.fs[0][1]).toFixed(3)")
        ck('ölçü artık kolondan çekilir: köşe → kolon', abs(st3-(fx-0.5-0.2-(await ev("RK.P.nodes.find(q=>q.id==='a0').x"))))<1e-3, st3)
        await typ(225); await btn('#sheet button[data-a=msok]'); k0 = await ev("(()=>{const f=RK.P.fills[0]; const n=RK.P.nodes.find(q=>q.id===f.nodes[0]), a=RK.P.nodes.find(q=>q.id==='a0'); return +(n.x-(a.x+0.2)).toFixed(4)})()")
        ck('  2.25 ölçüldü: kolon köşesi tam 2.25 te', k0==2.25, [k0, await ev("document.querySelector('#toast').textContent"), await ev('(()=>{const d=RK.P.dims[1]; const a=RK.P.nodes.find(n=>n.id===d.a), b=RK.P.nodes.find(n=>n.id===d.b); return [b.x-a.x, b.y-a.y, RK.P.fills[0].nodes.map(id=>{const n=RK.P.nodes.find(q=>q.id===id); return id===d.b?"B":[+(n.x-a.x).toFixed(3),+(n.y-a.y).toFixed(3)]})]})()')])
        await pg.screenshot(path='t22c.png')
        ck('JS hatası yok', not errs, errs[:3]); await b.close()
    print('TOPLAM', sum(R), '/', len(R)); sys.exit(0 if all(R) else 1)
asyncio.run(main())
