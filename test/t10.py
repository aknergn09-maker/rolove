import os, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
URL = (ROOT / os.environ.get('PAGE', 'index.html')).as_uri()
OUT = ROOT / 'test' / 'out'; OUT.mkdir(exist_ok=True); os.chdir(OUT)
CHROME = os.environ.get('CHROME', '/usr/bin/google-chrome' if os.path.exists('/usr/bin/google-chrome') else None)
import asyncio, sys
from playwright.async_api import async_playwright
R=[]
def ck(n,ok,i=''): R.append(bool(ok)); print(('PASS ' if ok else 'FAIL ')+n, i if not ok else '')
AREAS = "Object.fromEntries(RK.P.rooms.map(r=>[r.name, r._f? +r._f.net.toFixed(3):null]))"
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path=CHROME, args=['--no-sandbox'])
        ctx=await b.new_context(**p.devices['iPhone 13']); pg=await ctx.new_page(); errs=[]
        pg.on('pageerror', lambda e: errs.append(e.stack[:300]))
        await pg.goto(URL); await pg.evaluate("localStorage.clear()"); await pg.reload(); await pg.wait_for_timeout(300); ev=pg.evaluate
        async def btn(sel):
            r = await ev(f"(()=>{{const e=document.querySelector('{sel}'); if(!e||e.disabled) return null; const r=e.getBoundingClientRect(); return [r.left+r.width/2, r.top+r.height/2]}})()")
            if not r: return False
            await pg.touchscreen.tap(r[0], r[1]); await pg.wait_for_timeout(70); return True
        async def org(): return await ev("(()=>{const r=document.querySelector('#cv').getBoundingClientRect(); return [r.left,r.top]})()")
        async def ctap(x,y): r=await org(); await pg.touchscreen.tap(r[0]+x, r[1]+y); await pg.wait_for_timeout(80)
        async def typ(v):
            if not await ev("!!document.querySelector('#sheet button[data-k=C]')"): await btn('#sheet button[data-a=np]')
            await btn('#sheet button[data-k="C"]')
            for ch in str(v): await btn(f'#sheet button[data-k="{ch}"]')
            await ev("RK.S.np=false; RK.commit()")
        async def W(x,y): return await ev(f"RK.w2s({x},{y})")
        async def stroke(wpts):
            r = await org(); cdp = await ctx.new_cdp_session(pg); sp = [await ev(f"RK.w2s({x},{y})") for x,y in wpts]
            tp = lambda x,y: [{'x':r[0]+x,'y':r[1]+y}]
            await cdp.send('Input.dispatchTouchEvent', {'type':'touchStart','touchPoints':tp(*sp[0])})
            for (x0,y0),(x1,y1) in zip(sp,sp[1:]):
                n=max(2,int(((x1-x0)**2+(y1-y0)**2)**.5/5))
                for k in range(1,n+1): await cdp.send('Input.dispatchTouchEvent', {'type':'touchMove','touchPoints':tp(x0+(x1-x0)*k/n, y0+(y1-y0)*k/n)})
            await cdp.send('Input.dispatchTouchEvent', {'type':'touchEnd','touchPoints':[]}); await pg.wait_for_timeout(120)
        INIT = """(()=>{RK.S.cikAsk=null; const P=RK.P; P.nodes=[];P.lines=[];P.walls=[];P.rooms=[]; const mk=(pre,C,name,ax,ay)=>{const ids=C.map(([x,y],i)=>{const id=pre+i; P.nodes.push({id,x,y}); return id}); for(let i=0;i<C.length;i++) P.lines.push({id:pre+'L'+i,a:ids[i],b:ids[(i+1)%C.length],kind:'sketch'}); P.walls.push({id:'W'+pre,nodes:ids,closed:true,t:0.2,side:1}); P.rooms.push({id:'r'+pre,name,ax,ay});};
          mk('a',[[0,0],[6,0],[6,9],[0,9]],'A',2,4); mk('b',[[6.1,0],[10,0],[10,5],[6.1,5]],'B',8,2); RK.commit(); RK.commit();})()"""
        await ev(INIT); await btn('#fFit')
        await btn('#cats button[data-cat=duz]'); await btn('#tools button[data-tool=cikinti]')
        # içe köşe girintisi (ekteki gibi): alt cepheden başla, yukarı 4 m, sağ cepheye dokun
        q = await W(4.75,0); await ctap(q[0], q[1]); await typ(400); await btn('#sheet button[data-a=ar][data-v="1"]')
        q = await W(6,4); await ctap(q[0]-1, q[1]);
        a = await ev(AREAS); nr = len(a)
        ck('alt cepheden başlayıp sağ cepheye dokununca köşe girintisi: A 54-5=49, yeni oda yok, B aynı', abs(a['A']-49)<1e-6 and nr==2 and abs(a['B']-19.5)<1e-6 and await ev("RK.S.chain")==None, a)
        ck('  duvar bandı yeni köşeyi izliyor (6 köşe)', await ev("RK.P.walls.find(w=>w.id==='Wa').nodes.filter(id=>RK.P.lines.some(l=>l.a===id||l.b===id)).length")>=6 and await ev("RK.wallGeom(RK.P.walls.find(w=>w.id==='Wa')).quads.length")==6, await ev("RK.wallGeom(RK.P.walls.find(w=>w.id==='Wa')).quads.length"))
        ck('köşe girintisinde de "dış yüz değişsin mi?" sorusu çıkar (komşu B var)', await ev("!!document.querySelector('#sheet button[data-a=askY]')"))
        await btn('#sheet button[data-a=askY]'); a = await ev(AREAS);
        ck('  Evet: B\'nin yüzü girintiyi 10 cm kalınlıkla izledi (B 19.5 + 1.25×3.9 = 24.375), A 49', abs(a['B']-24.375)<1e-6 and abs(a['A']-49)<1e-6 and len(a)==2, a)
        await pg.screenshot(path='o4.png')
        await ev("RK.undo()"); a = await ev(AREAS); ck('  geri al → B 19.5', abs(a['B']-19.5)<1e-6 and abs(a['A']-49)<1e-6, a)
        # dışa köşe çıkıntısı: sağ cepheden başla → 1, ↑ 4, ← 2, üst cepheye dokun
        q = await W(6,6); await ctap(q[0]-1, q[1]); await typ(100); await btn('#sheet button[data-a=ar][data-v="0"]'); await typ(400); await btn('#sheet button[data-a=ar][data-v="1"]'); await typ(200); await btn('#sheet button[data-a=ar][data-v="2"]')
        q = await W(5,9); await ctap(q[0], q[1]+1)
        a = await ev(AREAS); ck('sağ cepheden çıkıp üst cepheye dönünce köşe çıkıntısı: A 49+5=54', abs(a['A']-54)<1e-6 and len(a)==2, a)
        await ev("RK.undo()"); a = await ev(AREAS); ck('geri al', abs(a['A']-49)<1e-6, a)
        # iki odayı ayıran çizgiyi silmez
        await ev(INIT.replace("[[6.1,0],[10,0],[10,5],[6.1,5]]","[[6,0],[10,0],[10,5],[6,5]]").replace("RK.commit(); RK.view","RK.view"))
        await ev("(()=>{const P=RK.P; P.lines=P.lines.filter(l=>l.id!=='bL3'); P.nodes.find(n=>n.id==='b0').x=6.0001; RK.commit()})()")
        await ev("""(()=>{const P=RK.P; P.nodes=[];P.lines=[];P.walls=[];P.rooms=[]; const N=[[0,0],[6,0],[10,0],[10,5],[6,5],[6,9],[0,9]]; N.forEach(([x,y],i)=>P.nodes.push({id:'n'+i,x,y})); const L=[[0,1],[1,2],[2,3],[3,4],[4,5],[5,6],[6,0],[1,4]]; L.forEach(([u,v],i)=>P.lines.push({id:'L'+i,a:'n'+u,b:'n'+v,kind:'sketch'})); P.rooms.push({id:'rA',name:'A',ax:2,ay:4},{id:'rB',name:'B',ax:8,ay:2}); RK.commit()})()"""); await btn('#fFit')
        q = await W(4.75,0); await ctap(q[0], q[1]); await typ(400); await btn('#sheet button[data-a=ar][data-v="1"]'); q = await W(6,4); await ctap(q[0]-1, q[1])
        a = await ev(AREAS); ck('aradaki çizgi iki odanın ortak sınırıysa silinmez (B bozulmaz), A korunur', abs(a['B']-20)<1e-6 and abs(a['A']-49)<1e-6, a)
        # serbest çizimde de köşe
        await ev(INIT); await btn('#fFit'); await btn('#cats button[data-cat=ciz]'); await btn('#tools button[data-tool=serbest]')
        await stroke([(4.75,0),(4.75,4),(6,4)])
        ck('serbest: köşe için de "Çıkıntı / girinti mi?" sorar', await ev("!!document.querySelector('#sheet button[data-a=skY]')"))
        await btn('#sheet button[data-a=skY]'); a = await ev(AREAS); ck('  Evet → A 49', abs(a['A']-49)<1e-6 and len(a)==2, a)
        ck('  serbestte de dış yüz sorusu', await ev("!!document.querySelector('#sheet button[data-a=askN]')")); await btn('#sheet button[data-a=askN]'); a = await ev(AREAS); ck('  Hayır → B sabit 19.5', abs(a['B']-19.5)<1e-6 and await ev("RK.S.cikAsk")==None, a)
        await btn('#fFit'); await pg.screenshot(path='o3.png')
        ck('JS hatası yok', not errs, errs[:3]); await b.close()
    print('TOPLAM', sum(R), '/', len(R)); sys.exit(0 if all(R) else 1)
asyncio.run(main())
