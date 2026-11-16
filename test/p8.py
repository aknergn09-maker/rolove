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
        RAx = "Object.fromEntries(RK.P.rooms.map(r=>[r.name, RK.rA(r)==null?null:+RK.rA(r).toFixed(3)]))"
        # açık U bina (Duvar ile çizilmiş gibi, açık duvar zinciri): (0,0)→(0,8)→(5,8)→(5,0); alt açık
        await ev("""(()=>{const P=RK.P; P.nodes=[];P.lines=[];P.rooms=[];P.walls=[];P.arcs=[]; const C=[[0,0],[0,8],[5,8],[5,0]]; const ids=C.map(([x,y],i)=>{const id='u'+i; P.nodes.push({id,x,y}); return id}); for(let i=0;i<3;i++) P.lines.push({id:'U'+i,a:ids[i],b:ids[i+1],kind:'sketch'}); P.walls.push({id:'WU',nodes:ids,closed:false,t:0.2,side:1}); RK.commit();
          const g=RK.wallGeom(P.walls[0]); const q=g.Q[1]; if (q[0]>0 || q[1]<8) { P.walls[0].side=-1; } RK.commit(); RK.view.s=30; RK.view.ox=110; RK.view.oy=325; RK.commit();})()""")
        ck('kurulum: açık bina, oda yok, duvar dışa', await ev("RK.P.rooms.length")==0)
        await btn('#tabs button[data-tab=cizim]'); await btn('#cats button[data-cat=ciz]'); await btn('#tools button[data-tool=daire]'); await btn('#sheet button[data-a=drm][data-v="2n"]')
        q = await W(0,0); await ctap(*q); q = await W(5,0); r0 = await ev("(()=>{const r=document.querySelector('#cv').getBoundingClientRect(); return [r.left,r.top]})()")
        cdp = await ctx.new_cdp_session(pg); await cdp.send('Input.dispatchTouchEvent', {'type':'touchStart','touchPoints':[{'x':r0[0]+q[0],'y':r0[1]+q[1]}]}); await pg.wait_for_timeout(120)
        await pg.screenshot(path='p8a.png')
        await cdp.send('Input.dispatchTouchEvent', {'type':'touchEnd','touchPoints':[]}); await pg.wait_for_timeout(200)
        a = await ev(RAx); exp = 40 + math.pi*2.5*2.5/2
        ck('daire açık binayı kapattı: alttaki yarım daire katıldı, üstteki atıldı, tek oda %.2f' % exp, len(a)==1 and abs(list(a.values())[0]-exp)<0.01, a)
        w = await ev("RK.P.walls.map(w=>[w.closed, w.nodes.length, RK.wallGeom(w).quads.length])")
        ck('  duvar zinciri yay boyunca devam edip kapandı', len(w)==1 and w[0][0] and w[0][2]>10, w)
        out = await ev("(()=>{const g=RK.wallGeom(RK.P.walls[0]); return Math.max(...g.Q.filter(q=>q[1]<-0.01).map(q=>Math.hypot(q[0]-2.5,q[1]-0)))})()")
        ck('  duvar bandı yayın dışında (r 2.5 → 2.7)', abs(out-2.7)<0.02, out)
        await pg.screenshot(path='p8b.png')
        # iç detay: yaya DOKUNAN U çizgisi (kesmeden): (1.5,yA) ↑ (1.5,-1) → (3.5,-1) ↓ (3.5,yB)
        y15 = -math.sqrt(2.5**2-1**2)
        await ev('RK.view.s=40; RK.view.ox=95; RK.view.oy=215; RK.commit()')
        await btn('#tools button[data-tool=cizgi]'); q = await W(1.5,y15); await ctap(*q)
        for x,y in [(1.5,-1),(3.5,-1),(3.5,y15)]: q = await W(x,y); await ctap(*q)
        await btn('#sheet button[data-a=end]')
        touch = await ev("RK.P.nodes.filter(n=>Math.abs(Math.hypot(n.x-2.5,n.y)-2.5)<1e-6 && RK.P.lines.filter(l=>!l.step&&(l.a===n.id||l.b===n.id)).length>2).length")
        ck('detay çizgisi yaya iki noktadan dokunuyor', touch==2, touch)
        # Buda: yayın detay arasındaki parçasına (alt orta) dokun
        await btn('#cats button[data-cat=duz]'); await btn('#tools button[data-tool=buda]'); await btn('#sheet button[data-a=bum][data-v=buda]')
        q = await W(2.5,-2.5); await ctap(q[0], q[1]-1)
        rem = await ev("RK.P.lines.filter(l=>{const a=RK.P.nodes.find(n=>n.id===l.a), b=RK.P.nodes.find(n=>n.id===l.b); return (a.y+b.y)/2<-2.3 && Math.abs((a.x+b.x)/2-2.5)<0.9}).length")
        ck('Buda: dokunan çizgiler arasındaki yay parçası silindi (kesmeden dokunan çizgiler de kesme noktası)', rem==0 and 'budandı' in await ev("document.querySelector('#toast').textContent"), [rem, await ev("document.querySelector('#toast').textContent")])
        lft = await ev("RK.P.lines.filter(l=>{const a=RK.P.nodes.find(n=>n.id===l.a), b=RK.P.nodes.find(n=>n.id===l.b); return Math.abs(Math.hypot((a.x+b.x)/2-2.5,(a.y+b.y)/2)-2.5)<0.05 && (a.x+b.x)/2<1.4}).length")
        ck('  yayın kalan kısmı (sol) yerinde', lft>3, lft)
        a2 = await ev(RAx); ck('  oda yeni sınırla (detay çizgisi üzerinden) hesaplandı', len(a2)>=1 and all(v for v in a2.values()), a2)
        await btn('#fFit'); await pg.screenshot(path='p8c.png')
        # Gerçek kullanım: 3 noktalı yay yarım daireden küçük (daire yan duvarları ikinci kez keser) ve merkez+yarıçap ile uçları aşan daire
        U = """(()=>{const P=RK.P; P.nodes=[];P.lines=[];P.rooms=[];P.walls=[];P.arcs=[];P.openings=[]; const C=[[0,0],[0,8],[5,8],[5,0]]; const ids=C.map(([x,y],i)=>{const id='u'+i; P.nodes.push({id,x,y}); return id}); for(let i=0;i<3;i++) P.lines.push({id:'U'+i,a:ids[i],b:ids[i+1],kind:'sketch'}); P.walls.push({id:'WU',nodes:ids,closed:false,t:0.2,side:1}); RK.commit(); const g=RK.wallGeom(P.walls[0]); if (g.Q[1][0]>0||g.Q[1][1]<8) P.walls[0].side=-1; RK.view.s=30; RK.view.ox=110; RK.view.oy=325; RK.commit();})()"""
        BAND = "(c,r)=>{const g=RK.wallGeom(RK.P.walls[0]); const d=g.Q.filter(q=>q[1]<-0.05).map(q=>Math.hypot(q[0]-c[0],q[1]-c[1])-r); return d.length?[Math.min(...d),Math.max(...d)]:null}"
        await ev(U); await btn('#cats button[data-cat=ciz]'); await btn('#tools button[data-tool=daire]'); await btn('#sheet button[data-a=drm][data-v="3n"]')
        for x,y in [(0,0),(2.5,-1.5)]: q = await W(x,y); await ctap(*q)
        q = await W(5,0); await cdp.send('Input.dispatchTouchEvent', {'type':'touchStart','touchPoints':[{'x':r0[0]+q[0],'y':r0[1]+q[1]}]}); await pg.wait_for_timeout(120); await pg.screenshot(path='p8d.png')
        await cdp.send('Input.dispatchTouchEvent', {'type':'touchEnd','touchPoints':[]}); await pg.wait_for_timeout(200)
        a = await ev(RAx); rr = 17/6; seg = rr*rr*math.acos((rr-1.5)/rr) - (rr-1.5)*math.sqrt(rr*rr-(rr-1.5)**2); exp = 40+seg
        ck('3 noktalı basık yay (daire yan duvarları tekrar keser): tek oda %.3f' % exp, len(a)==1 and abs(list(a.values())[0]-exp)<0.01, a)
        w = await ev("RK.P.walls.map(w=>w.closed)"); bd = await ev(f"({BAND})([2.5,{rr-1.5}],{rr})")
        ck('  duvar kapandı, bant yayın dışında, yan çıkıntı yok', w==[True] and bd and abs(bd[1]-0.2)<0.02 and bd[0]>-0.01 and await ev("RK.P.nodes.every(n=>n.x>-0.01&&n.x<5.01)"), [w,bd])
        await pg.screenshot(path='p8e.png')
        await ev(U); await btn('#tools button[data-tool=cizgi]'); await btn('#tools button[data-tool=daire]'); await pg.wait_for_timeout(300); await btn('#sheet button[data-a=drm][data-v=mr]'); await ev('RK.view.s=25; RK.view.oy=290; RK.commit()')
        for x,y in [(2.5,1),(2.5,-2)]: q = await W(x,y); await ctap(*q)
        a = await ev(RAx); h = 1+math.sqrt(9-2.5**2); exp = 5*(8-h) + (9*math.pi - (9*math.acos((h-1)/3) - (h-1)*math.sqrt(9-(h-1)**2)))
        ck('merkez+yarıçap, daire yan duvarları keser: daire içindeki uçlar budandı, tek oda %.3f' % exp, len(a)==1 and abs(list(a.values())[0]-exp)<0.01, a)
        w = await ev("RK.P.walls.map(w=>w.closed)"); ck('  duvar kapandı, uç yok', w==[True] and await ev("RK.P.nodes.every(n=>n.y>=-2.01)") and await ev("!RK.P.nodes.some(n=>Math.abs(n.y)<1e-6&&(n.x===0||n.x===5))"), w)
        await btn('#fFit'); await pg.screenshot(path='p8f.png')
        # tamamen elle: Duvar aracıyla açık U çiz, sonra 3 nokta ile yay
        await ev("(()=>{const P=RK.P; P.nodes=[];P.lines=[];P.rooms=[];P.walls=[];P.arcs=[];P.openings=[]; RK.view.s=22; RK.view.ox=130; RK.view.oy=270; RK.commit();})()")
        await btn('#tools button[data-tool=duvar]')
        for x,y in [(0,0),(0,8),(5,8),(5,0)]: q = await W(x,y); await ctap(*q); await pg.wait_for_timeout(300)
        await btn('#sheet button[data-a=end]')
        st = await ev("[RK.P.walls.length, RK.P.walls.map(w=>w.closed), RK.P.rooms.length, RK.P.nodes.map(n=>[+n.x.toFixed(2),+n.y.toFixed(2)])]"); await pg.screenshot(path='p8g0.png')
        await btn('#tools button[data-tool=daire]'); await btn('#sheet button[data-a=drm][data-v="3n"]')
        for x,y in [(0,0),(2.5,-1.5),(5,0)]: q = await W(x,y); await ctap(*q)
        a = await ev(RAx); w = await ev("RK.P.walls.map(w=>w.closed)")
        ck('Duvar aracıyla çizilen açık bina + 3 nokta yay: duvar kapandı, tek oda %.3f' % (40+seg), len(a)==1 and abs(list(a.values())[0]-40-seg)<0.02 and w==[True], [st, a, w])
        await pg.screenshot(path='p8g.png')
        ck('JS hatası yok', not errs, errs[:3]); await b.close()
    print('TOPLAM', sum(R), '/', len(R)); sys.exit(0 if all(R) else 1)
asyncio.run(main())
