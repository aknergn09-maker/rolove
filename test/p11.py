# ÖNİZLEME: lazerle duvar kalınlığı — bir duvarın hem çizgisi hem diğer yüzü ölçülünce köşedeki komşu duvarların kalınlığı hesaplanır
import os, pathlib
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
            await pg.touchscreen.tap(r[0], r[1]); await pg.wait_for_timeout(80); return True
        async def ctap(x,y):
            r = await ev("(()=>{const r=document.querySelector('#cv').getBoundingClientRect(); return [r.left,r.top]})()"); await pg.touchscreen.tap(r[0]+x, r[1]+y); await pg.wait_for_timeout(100)
        async def W(x,y): return await ev(f"RK.w2s({x},{y})")
        async def typ(v):
            if not await ev("!!document.querySelector('#sheet button[data-k=C]')"): await btn('#sheet button[data-a=np]')
            await btn('#sheet button[data-k="C"]')
            for ch in str(v): await btn(f'#sheet button[data-k="{ch}"]')
        async def meas(x, y, cm):
            q = await W(x, y); await ctap(*q); await typ(cm); await btn('#sheet button[data-a=msok]'); return await ev("document.querySelector('#toast').textContent")
        await ev("""(()=>{const P=RK.P; P.nodes=[];P.lines=[];P.walls=[];P.rooms=[];P.openings=[]; const C=[[0,0],[4,0],[4,3],[0,3]]; const ids=C.map(([x,y],i)=>{const id='a'+i; P.nodes.push({id,x,y}); return id}); for(let i=0;i<4;i++) P.lines.push({id:'A'+i,a:ids[i],b:ids[(i+1)%4],kind:'sketch'}); P.walls.push({id:'WA',nodes:ids,closed:true,t:0.2,side:1}); P.rooms.push({id:'rA',name:'A',ax:2,ay:1.5}); RK.commit(); if(!RK.wallGeom(P.walls[0]).Q.some(q=>q[1]<-0.1)) P.walls[0].side=-1; RK.view.s=55; RK.view.ox=70; RK.view.oy=260; RK.commit();})()""")
        TH = "['A0','A1','A2','A3'].map(id=>{const l=RK.P.lines.find(q=>q.id===id); return l.wt==null?0.2:l.wt})"
        await btn('#tabs button[data-tab=olcum]'); await btn('#tools button[data-tool=olc]')
        t1 = await meas(2, 0, 400); t2 = await meas(2, -0.2, 450)
        th = await ev(TH)
        ck('alt duvar: çizgi 4.00 + dış yüz 4.50 → köşedeki sol ve sağ duvar 25 cm (eşit pay), alt ve üst 20 cm', th==[0.2,0.25,0.2,0.25], [th, t2])
        ck('  alt çizgi 4.00 kaldı, dış yüz 4.50 oldu', await ev("[+RK.lineLen(RK.P.lines.find(l=>l.id==='A0')).toFixed(3), +RK.faceLenOf(RK.P.lines.find(l=>l.id==='A0')).toFixed(3)]")==[4,4.5], await ev("[RK.lineLen(RK.P.lines.find(l=>l.id==='A0')), RK.faceLenOf(RK.P.lines.find(l=>l.id==='A0'))]"))
        t3 = await meas(4, 1.5, 300); t4 = await meas(4.25, 1.5, 370)
        th = await ev(TH)
        ck('sağ duvar: çizgi 3.00 + dış yüz 3.70 → alt ve üst 35 cm; sol/sağ 25 cm yerinde', th==[0.35,0.25,0.35,0.25], [th, t4])
        ck('  iki yüz ölçüsü de tutuyor (4.50, 3.70)', await ev("['A0','A1'].map(id=>+RK.faceLenOf(RK.P.lines.find(l=>l.id===id)).toFixed(3))")==[4.5,3.7])
        # dış yüzü yeniden ölç: 4.60 → sol+sağ 0.6
        await meas(2, -0.35, 460); th = await ev(TH)
        ck('alt dış yüz yeniden 4.60 ölçüldü → sol ve sağ 30 cm (değişebilir)', th==[0.35,0.3,0.35,0.3], th)
        await pg.screenshot(path='p11.png')
        # elle kalınlık seçilince hesaplanan kalınlıklar silinir
        ck('JS hatası yok', not errs, errs[:3]); await b.close()
    print('TOPLAM', sum(R), '/', len(R)); sys.exit(0 if all(R) else 1)
asyncio.run(main())
