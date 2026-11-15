import os, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
URL = (ROOT / 'index.html').as_uri()
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
        await ev("""(()=>{const P=RK.P; const C=[[0,0],[4,0],[4,3],[0,3]]; const ids=C.map(([x,y],i)=>{const id='a'+i; P.nodes.push({id,x,y}); return id}); for(let i=0;i<4;i++) P.lines.push({id:'A'+i,a:ids[i],b:ids[(i+1)%4],kind:'typed'}); P.walls.push({id:'WA',nodes:ids,closed:true,t:0.2,side:1}); P.rooms.push({id:'rA',name:'A',ax:2,ay:1.5}); RK.commit(); RK.view.s=62; RK.view.ox=50; RK.view.oy=360; RK.commit();})()""")
        AREA = "+RK.rA(RK.P.rooms[0]).toFixed(3)"
        a0 = await ev(AREA)
        await btn('#cats button[data-cat=ekle]'); await btn('#tools button[data-tool=aciklik]')
        ck('Ekle sekmesinde Kapı/Pencere aracı', await ev("RK.S.tool")=='aciklik')
        # kapı: alt duvarda sol köşeye yakın dokun → köşeye oturur; köşeden 50, genişlik 90, → ok
        q = await W(0.08,0); await ctap(*q)
        ck('  köşeye yakın dokunuş köşeye oturdu', await ev("RK.S.op.step==2 && Math.abs(RK.S.op.p[0])<1e-9"), await ev("RK.S.op"))
        await btn('#sheet button[data-a=opf][data-v=d]'); await btn('#sheet button[data-k="5"]'); await btn('#sheet button[data-k="0"]')
        await btn('#sheet button[data-a=opf][data-v=w]'); await btn('#sheet button[data-k="9"]'); await btn('#sheet button[data-k="0"]')
        dirs = await ev("[...document.querySelectorAll('#sheet button[data-a=opar]')].map(b=>[b.dataset.v,b.textContent])"); v=[x for x,t in dirs if t=='→'][0]
        await btn(f'#sheet button[data-a=opar][data-v="{v}"]')
        d = await ev("(()=>{const o=RK.P.openings[0]; const g=RK.opGeom(o); return [o.type, +g.P0[0].toFixed(3), +g.P1[0].toFixed(3), o.sw, g.wall, +g.t.toFixed(3)]})()")
        ck('kapı: x 0.50–1.40, duvar içinde (20 cm), oda tarafına açılır', d==['kapi',0.5,1.4,-1,True,0.2], d)
        # pencere: üst duvarın DIŞ yüzüne dokun (x≈1.5) → genişlik 120 → ok
        await btn('#sheet button[data-a=opt][data-v=pencere]'); q = await W(1.5,3.2); await ctap(*q); ck('  2. adımda tuş takımı kapalı (bitiş noktası görünür)', not await ev("RK.S.np"))
        await btn('#sheet button[data-a=opf][data-v=w]'); await btn('#sheet button[data-k="C"]'); [await btn(f'#sheet button[data-k="{c}"]') for c in "120"]
        dirs = await ev("[...document.querySelectorAll('#sheet button[data-a=opar]')].map(b=>[b.dataset.v,b.textContent])"); v=[x for x,t in dirs if t=='→'][0]
        await btn(f'#sheet button[data-a=opar][data-v="{v}"]')
        w = await ev("(()=>{const o=RK.P.openings[1]; const g=RK.opGeom(o); const xs=[g.P0[0],g.P1[0]].sort((a,b)=>a-b); return [o.type, +xs[0].toFixed(3), +xs[1].toFixed(3), +g.P0[1].toFixed(3)]})()")
        ck('pencere: dış yüze dokunuş referans çizgiye taşındı, x 1.50–2.70, y=3', w==['pencere',1.5,2.7,3], w)
        # bitişe dokunarak: sağ duvar y 0.5→1.5
        q = await W(4,0.5); await ctap(*q); q = await W(4,1.5); await ctap(*q)
        w2 = await ev("(()=>{const o=RK.P.openings[2]; const g=RK.opGeom(o); return [+o.w.toFixed(3), +g.P0[1].toFixed(3)]})()")
        ck('başlangıç + bitişe dokunarak pencere (1.00 m)', w2==[1.0,0.5], w2)
        ck('oda alanı değişmedi', await ev(AREA)==a0, [a0, await ev(AREA)])
        await pg.screenshot(path='o10.png')
        # Seç: kapıya dokun → menteşe, açılış, genişlik
        await btn('#cats button[data-cat=duz]'); await btn('#tools button[data-tool=sec]'); q = await W(0.95,0.1); await ctap(*q); await pg.screenshot(path='o11.png')
        ck('Seç: kapı seçildi, panel açıldı', await ev("RK.S.sel && !!RK.S.sel.open") and await ev("!!document.querySelector('#sheet button[data-a=ophand]')"))
        h0 = await ev("RK.doorHand(RK.P.openings[0])"); sd0 = await ev("RK.doorSide(RK.P.openings[0])")
        ck('  kapı A tarafına açılıyor, el Sağ ya da Sol yazıyor', sd0=='A' and h0 in ('sag','sol') and await ev("!!document.querySelector('#sheet button[data-a=ophand][data-v=sag]')"), [h0, sd0])
        other = 'sol' if h0=='sag' else 'sag'; await btn(f'#sheet button[data-a=ophand][data-v={other}]')
        ck('  Sağ/Sol değişti (menteşe öbür uca geçti)', await ev("RK.doorHand(RK.P.openings[0])")==other and await ev("RK.P.openings[0].hinge")==1)
        await btn('#sheet button[data-a=opsw]')
        ck('  ⇅ dışarı açılır yaptı, el aynı kaldı', await ev("RK.doorSide(RK.P.openings[0])")=='dışarı' and await ev("RK.doorHand(RK.P.openings[0])")==other, [await ev("RK.doorSide(RK.P.openings[0])"), await ev("RK.doorHand(RK.P.openings[0])")])
        
        await btn('#sheet button[data-a=opsw]'); await ev("(()=>{const o=RK.P.openings[0]; o.hinge=0; RK.commit()})()")
        ck('  tanım: A içinden güneye bakan kişinin sağı batı; menteşe x=0.5 (batı) → Sağ', await ev("RK.doorHand(RK.P.openings[0])")=='sag')
        await ev("(()=>{const o=RK.P.openings[0]; o.hinge=1; o.sw=1; RK.commit()})()")
        ck('  düğmelere bastıktan sonra tuş takımı kendiliğinden açılmadı', not await ev('RK.S.np')); await btn('#sheet button[data-a=np]'); [await btn(f'#sheet button[data-k="{c}"]') for c in "100"]; await btn('#sheet button[data-a=opw]')
        ck('  genişlik 100 cm oldu', abs(await ev("RK.P.openings[0].w")-1.0)<1e-9)
        # Ötele: alt duvar 30 cm aşağı → kapı izler
        await btn('#sheet button[data-a=unsel]'); await ev("RK.offsetWall('A0', -1, 0.3)")
        y = await ev("+RK.opGeom(RK.P.openings[0]).P0[1].toFixed(3)"); ck('alt duvar ötelenince üstündeki kapı da kaydı (y=-0.3)', y==-0.3, y)
        yw = await ev("(()=>{const g=RK.opGeom(RK.P.openings[2]); return [+g.P0[1].toFixed(3), +g.P1[1].toFixed(3)]})()"); ck('uzayan sağ duvardaki pencere yerinde kaldı (y 0.5–1.5)', sorted(yw)==[0.5,1.5], yw)
        # duvar çizerken: 300 → , sonraki parça kapı 90 → , 200 →
        await ev("RK.view.s=40; RK.view.ox=40; RK.view.oy=440; RK.commit()")
        await btn('#cats button[data-cat=ciz]'); await btn('#tools button[data-tool=duvar]'); q = await W(0,5); await ctap(*q)
        ck('duvar başlangıcı alındı (panel çizim alanını kapatmıyor)', await ev('!!RK.S.chain'))
        await typ(300); await btn('#sheet button[data-a=ar][data-v="0"]'); await btn('#sheet button[data-a=pend][data-v=kapi]'); await typ(90); await btn('#sheet button[data-a=ar][data-v="0"]'); await typ(200); await btn('#sheet button[data-a=ar][data-v="0"]'); await btn('#sheet button[data-a=end]')
        k = await ev("(()=>{const o=RK.P.openings.find(o=>RK.opGeom(o).P0[1]>4); if(!o) return null; const g=RK.opGeom(o); return [o.type, +g.P0[0].toFixed(3), +g.P1[0].toFixed(3), g.wall]})()")
        ck('duvar çizerken "Sonraki parça kapı": x 3.00–3.90 kapı, duvar içinde', k==['kapi',3,3.9,True], k)
        # Sil aracı: kapıya dokun
        n0 = await ev("RK.P.openings.length"); await btn('#cats button[data-cat=duz]'); await btn('#tools button[data-tool=sil]'); q = await W(3.45,5.1); await ctap(*q)
        ck('Sil: kapı silindi', await ev("RK.P.openings.length")==n0-1)
        # ev sahibi çizgi silinince açıklık gider
        await ev("(()=>{RK.P.lines=RK.P.lines.filter(l=>l.id!=='A1'); RK.commit();})()")
        ck('duvar çizgisi silinince üstündeki pencere de gitti', await ev("RK.P.openings.filter(o=>{const g=RK.opGeom(o); return g && g.P0[0]>3.9}).length")==0)
        await ev("RK.undo()"); ck('geri al: pencere geri', await ev("RK.P.openings.filter(o=>{const g=RK.opGeom(o); return g && g.P0[0]>3.9}).length")==1)
        ck('JS hatası yok', not errs, errs[:3]); await b.close()
    print('TOPLAM', sum(R), '/', len(R)); sys.exit(0 if all(R) else 1)
asyncio.run(main())
