# ÖNİZLEME v12: yay çıkıntısı, ölçü yazarak çıkıntı, serbest çizim çıkıntısı duvarlı çizgide; tarama tüm duvar; duvarsız çizgide klasik çıkıntı
import os, pathlib, math
ROOT = pathlib.Path(__file__).resolve().parent.parent
URL = (ROOT / os.environ.get('PAGE', 'onizleme.html')).as_uri()
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
            await pg.touchscreen.tap(r[0], r[1]); await pg.wait_for_timeout(90); return True
        async def org(): return await ev("(()=>{const r=document.querySelector('#cv').getBoundingClientRect(); return [r.left,r.top]})()")
        async def ctap(x,y): o = await org(); q = await ev(f"RK.w2s({x},{y})"); await pg.touchscreen.tap(o[0]+q[0], o[1]+q[1]); await pg.wait_for_timeout(200)
        async def typ(v):
            if not await ev("!!document.querySelector('#sheet button[data-k=C]')"): await btn('#sheet button[data-a=np]')
            await btn('#sheet button[data-k="C"]')
            for ch in str(v): await btn(f'#sheet button[data-k="{ch}"]')
            await ev("RK.S.np=false; RK.commit()")
        async def stroke(wpts):
            o = await org(); cdp = await ctx.new_cdp_session(pg); sp = [await ev(f"RK.w2s({x},{y})") for x,y in wpts]; tp = lambda x,y: [{'x':o[0]+x,'y':o[1]+y}]
            await cdp.send('Input.dispatchTouchEvent', {'type':'touchStart','touchPoints':tp(*sp[0])})
            for (x0,y0),(x1,y1) in zip(sp,sp[1:]):
                n=max(2,int(((x1-x0)**2+(y1-y0)**2)**.5/5))
                for k in range(1,n+1): await cdp.send('Input.dispatchTouchEvent', {'type':'touchMove','touchPoints':tp(x0+(x1-x0)*k/n, y0+(y1-y0)*k/n)})
            await cdp.send('Input.dispatchTouchEvent', {'type':'touchEnd','touchPoints':[]}); await pg.wait_for_timeout(150)
        RM = "RK.P.rooms.filter(r=>!r.kind).map(r=>r._f? +RK.rA(r).toFixed(3):null)"
        INIT = """(()=>{RK.S.faceAsk=null; RK.S.cikAsk=null; const P=RK.P; P.nodes=[];P.lines=[];P.walls=[];P.rooms=[];P.openings=[];P.wq=[];P.offs=[];P.fills=[];P.arcs=[]; const C=[[0,0],[4,0],[4,3],[0,3]]; const ids=C.map(([x,y],i)=>{const id='a'+i; P.nodes.push({id,x,y}); return id}); for(let i=0;i<4;i++) P.lines.push({id:'A'+i,a:ids[i],b:ids[(i+1)%%4],kind:'sketch'}); %s P.rooms.push({id:'r',name:'A',ax:2,ay:1.5}); RK.commit(); RK.view.s=70; RK.view.ox=50; RK.view.oy=250; RK.commit();})()"""
        WALL = "P.walls.push({id:'W',nodes:ids,closed:true,t:0.2,side:1});"
        await btn('#tabs button[data-tab=cizim]')
        # 1) yay çıkıntısı (dış çizgide 3 nokta)
        await ev(INIT % WALL); await btn('#cats button[data-cat=duz]'); await btn('#tools button[data-tool=cikinti]'); await btn('#sheet button[data-a=cikm][data-v=yay]')
        for x,y in [(1,-0.2),(2,-1.2),(3,-0.2)]: await ctap(x,y)
        a = await ev(RM); ck('yay çıkıntısı duvarlı çizgide: soru, varsayılan ofset korunsun, iç çizgi de yay (oda büyüdü)', await ev("RK.S.faceAsk&&RK.S.faceAsk.cur")=='kayar' and a[0]>13 and await ev("RK.P.arcs.length")==2, [a, await ev("RK.P.arcs.length")])
        await btn('#sheet button[data-a=faN]'); ck('  "Duvar kalınlaşsın": oda 12, yay ile duvar arası taralı', await ev(RM)==[12] and await ev("RK.P.fills.length")==1, await ev(RM))
        await pg.screenshot(path='q2a.png')
        # 2) ölçü yazarak (dış çizgi: başlangıç 1, genişlik 100 →, derinlik 50 ↓)
        await ev(INIT % WALL); await btn('#sheet button[data-a=cikm][data-v=olcu]')
        await ctap(1,-0.2); await typ(100); lbl = await ev("[...document.querySelectorAll('#sheet button[data-a=cikw]')].map(b=>[b.dataset.v,b.textContent])"); v=[x for x,t in lbl if t=='→'][0]; await btn(f'#sheet button[data-a=cikw][data-v="{v}"]')
        await typ(50); lbl = await ev("[...document.querySelectorAll('#sheet button[data-a=cikd]')].map(b=>[b.dataset.v,b.textContent])"); v=[x for x,t in lbl if t=='↓'][0]; await btn(f'#sheet button[data-a=cikd][data-v="{v}"]')
        a = await ev(RM); ck('ölçü yazarak (dış çizgiden 100×50 dışa): soru çıktı, ofset korunsun → oda 12 + 0.6×0.5 = 12.3', await ev("RK.S.faceAsk&&RK.S.faceAsk.cur")=='kayar' and a==[12.3], [a, await ev("document.querySelector('#toast').textContent")])
        await btn('#sheet button[data-a=faN]'); ck('  kalınlaşsın → 12', await ev(RM)==[12], await ev(RM))
        # 3) serbest çizim (iç çizgiden içeri: kolon gibi)
        await ev(INIT % WALL); await btn('#cats button[data-cat=ciz]'); await btn('#tools button[data-tool=serbest]')
        await stroke([(1.5,0),(1.5,0.4),(2.5,0.4),(2.5,0)])
        if await ev("!!document.querySelector('#sheet button[data-a=skY]')"): await btn('#sheet button[data-a=skY]')
        a = await ev(RM); ck('serbest çizimle iç çizgiden içeri: soru, varsayılan kalınlaşsın → oda 12 − 1×0.4 = 11.6', await ev("RK.S.faceAsk&&RK.S.faceAsk.cur")=='sabit' and a==[11.6], [a, await ev("document.querySelector('#toast').textContent")])
        # 4) duvarsız çizgi odada çıkıntı: klasik (soru yok, oda büyür)
        await ev(INIT % ''); await btn('#cats button[data-cat=duz]'); await btn('#tools button[data-tool=cikinti]'); await btn('#sheet button[data-a=cikm][data-v=el]')
        for x,y in [(1,0),(1,-0.5),(2,-0.5),(2,0)]: await ctap(x,y)
        ck('duvarsız odada çıkıntı: klasik, oda 12.5, soru yok', await ev(RM)==[12.5] and not await ev("!!RK.S.faceAsk"), [await ev(RM), await ev("RK.S.faceAsk")])
        # 5) tarama: bir yerine dokununca o duvarın tamamı
        await ev(INIT % WALL); await btn('#cats button[data-cat=ekle]'); await btn('#tools button[data-tool=tarama]')
        await ctap(2,-0.1); ck('Duvar alanı: duvarın bir yerine dokununca taramanın tamamı kalktı', await ev("RK.P.wq.length")==0 and await ev("RK.P.wqOff.length")==4, [await ev("RK.P.wq.length")])
        await ctap(-0.1,1.5); ck('  başka yerine dokununca tamamı geri geldi', await ev("RK.P.wq.length")==4, await ev("RK.P.wq.length"))
        # 6) açık U duvarı 3 noktalı daireyle kapatma: tek oda, iki eş merkezli yay
        await ev("localStorage.clear()"); await pg.reload(); await pg.wait_for_timeout(300)
        r = await ev("""(()=>{const P=RK.P; const C=[[0,0],[0,8],[5,8],[5,0]]; const ids=C.map(([x,y],i)=>{const id='u'+i; P.nodes.push({id,x,y}); return id}); for(let i=0;i<3;i++) P.lines.push({id:'U'+i,a:ids[i],b:ids[i+1],kind:'sketch'}); P.walls.push({id:'WU',nodes:ids,closed:false,t:0.2,side:1}); RK.commit();
           RK.setTool('daire'); RK.S.dr.mode='3n'; RK.S.dr.pts=[[0,0],[2.5,-1.5],[5,0]]; RK.daireMake(); RK.commit();
           return [RK.P.rooms.map(r=>+RK.rA(r).toFixed(3)), (RK.P.arcs||[]).length]})()""")
        ck('açık U + daire: tek oda 45.343, 2 yay (iç+dış duvar)', r==[[45.343],2], r)
        ck('JS hatası yok', not errs, errs[:3]); await b.close()
    print('TOPLAM', sum(R), '/', len(R)); sys.exit(0 if all(R) else 1)
asyncio.run(main())
