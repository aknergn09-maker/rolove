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
        pg.on('pageerror', lambda e: errs.append(str(e)))
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
        async def stroke(wpts):
            r = await org(); cdp = await ctx.new_cdp_session(pg); sp = [await ev(f"RK.w2s({x},{y})") for x,y in wpts]
            tp = lambda x,y: [{'x':r[0]+x,'y':r[1]+y}]
            await cdp.send('Input.dispatchTouchEvent', {'type':'touchStart','touchPoints':tp(*sp[0])})
            for (x0,y0),(x1,y1) in zip(sp,sp[1:]):
                n=max(2,int(((x1-x0)**2+(y1-y0)**2)**.5/5))
                for k in range(1,n+1): await cdp.send('Input.dispatchTouchEvent', {'type':'touchMove','touchPoints':tp(x0+(x1-x0)*k/n, y0+(y1-y0)*k/n)})
            await cdp.send('Input.dispatchTouchEvent', {'type':'touchEnd','touchPoints':[]}); await pg.wait_for_timeout(120)
        async def W(x,y): return await ev(f"RK.w2s({x},{y})")
        await ev("""(()=>{const P=RK.P; const C=[[0,0],[4,0],[4,3],[0,3]]; const ids=C.map(([x,y],i)=>{const id='a'+i; P.nodes.push({id,x,y}); return id}); for(let i=0;i<4;i++) P.lines.push({id:'A'+i,a:ids[i],b:ids[(i+1)%4],kind:'typed'}); P.walls.push({id:'WA',nodes:ids,closed:true,t:0.2,side:1}); P.rooms.push({id:'rA',name:'A',ax:2,ay:1.5}); RK.commit(); RK.view.s=45; RK.view.ox=20; RK.view.oy=230; RK.commit();})()""")
        # B odası: A'nın dış yüzünden (4.2,0) başla, sağa 3, yukarı 3, A'nın dış yüzüne dokun
        await btn('#tools button[data-tool=cizgi]')
        q = await W(4.2,0.0); await ctap(q[0], q[1]-1); st = await ev("(()=>{const n=RK.P.nodes.find(x=>x.id===RK.S.chain.first); return [+n.x.toFixed(4),+n.y.toFixed(4)]})()")
        ck('B başlangıcı A duvarının dış yüzünde', abs(st[0]-4.2)<1e-4, st)
        await typ(300); await btn('#sheet button[data-a=ar][data-v="0"]'); await typ(300); await btn('#sheet button[data-a=ar][data-v="1"]')
        q = await W(4.2,3.0); await ctap(q[0]+1, q[1]+1)
        a1 = await ev(AREAS); fl = await ev("RK.P.lines.filter(l=>l.face).length")
        ck('A\'nın dış yüzüne dokununca B ortak duvardan kapandı (9 m²), beyaz çizginin üstüne ayrıca çizgi eklenmedi', len(a1)==2 and abs(list(a1.values())[1]-9.0)<1e-6 and fl==0 and await ev("RK.S.chain")==None, [a1, fl])
        bname = [k for k in a1 if k!='A'][0]
        # Çıkıntı (çizerek): A'nın sağ duvarında (x=4) y=1'den dışa 0.5, y=2'ye
        await btn('#cats button[data-cat=duz]'); await btn('#tools button[data-tool=cikinti]')
        ck('Çıkıntı varsayılan çizerek', await ev("RK.S.cik.mode")=='el')
        await ev("window._E=[]; document.querySelector('#cv').addEventListener('pointerdown',e=>_E.push('d:'+RK.S.tool+':'+RK.S.cik.mode)); document.querySelector('#cv').addEventListener('pointerup',e=>_E.push('u'))")
        SAVED = await ev("JSON.stringify(RK.P)")
        q = await W(4,1.0); await ctap(q[0]-1, q[1]); await typ(50); await btn('#sheet button[data-a=ar][data-v="0"]'); await typ(100); await btn('#sheet button[data-a=ar][data-v="1"]')
        q = await W(4.02,2.0); await ctap(q[0], q[1])
        a2 = await ev(AREAS); ask = await ev("!!RK.S.cikAsk")
        ck('çizgi gibi çizilen çıkıntı hesaplandı, komşu B kendiliğinden izledi (A 12.5, B 8.3), soru soruldu', abs(a2['A']-12.5)<1e-6 and abs(a2[bname]-8.3)<1e-6 and ask, [a2, ask, await ev("document.querySelector('#toast').textContent")])
        ck('  "dış yüz değişsin mi" düğmeleri panelde', await ev("!!document.querySelector('#sheet button[data-a=askY]') && !!document.querySelector('#sheet button[data-a=askN]')"))
        await btn('#sheet button[data-a=askY]')
        a3 = await ev(AREAS); ck('Evet: komşunun dış yüzü aynı kalınlıkla kaydı (B 9 → 8.3)', abs(a3[bname]-8.3)<1e-6 and abs(a3['A']-12.5)<1e-6, a3)
        # geri al → Hayır
        await ev("RK.undo()"); a4 = await ev(AREAS); ck('geri al: çıkıntı öncesine döner (A 12, B 9)', abs(a4[bname]-9)<1e-6 and abs(a4['A']-12)<1e-6, a4)
        await ev(f"RK.P = JSON.parse({SAVED!r}); RK.commit()"); await btn('#cats button[data-cat=ciz]'); await btn('#tools button[data-tool=serbest]'); await stroke([(4,1.0),(4.5,1.0),(4.5,2.0),(4,2.0)])
        ck('serbest çizim: "Çıkıntı mı?" sorusu çıkar', await ev("!!document.querySelector('#sheet button[data-a=skY]')"))
        await btn('#sheet button[data-a=skY]')
        ck('serbest çizimle de çıkıntı + dış yüz sorusu', await ev("!!RK.S.cikAsk") and abs((await ev(AREAS))['A']-12.5)<1e-6, await ev(AREAS))
        await btn('#sheet button[data-a=askN]')
        a5 = await ev(AREAS); ck('Hayır: komşu duvar sabit kaldı (B 8.3, A 12.2)', abs(a5[bname]-8.3)<1e-6 and abs(a5['A']-12.2)<1e-6 and await ev("RK.S.cikAsk")==None, a5)
        # ölçüyle de sorsun: A alt duvarı (komşu yok) → soru gelmemeli
        await btn('#cats button[data-cat=duz]'); await btn('#tools button[data-tool=cikinti]'); await btn('#sheet button[data-a=cikm][data-v=olcu]'); q = await W(1,0); await ctap(q[0], q[1]); await typ(50)
        lbl = await ev("[...document.querySelectorAll('#sheet button[data-a=cikw]')].map(b=>[b.dataset.v,b.textContent])"); v=[x for x,t in lbl if t=='→'][0]; await btn(f'#sheet button[data-a=cikw][data-v="{v}"]')
        await typ(20); lbl = await ev("[...document.querySelectorAll('#sheet button[data-a=cikd]')].map(b=>[b.dataset.v,b.textContent])"); v=[x for x,t in lbl if t=='↓'][0]; await btn(f'#sheet button[data-a=cikd][data-v="{v}"]')
        ck('komşusu olmayan duvarda çıkıntı: soru sorulmaz (kendi çizgileri karşı yüz sayılmaz)', await ev("RK.S.cikAsk")==None and abs((await ev(AREAS))['A']-12.3)<1e-6, await ev(AREAS))
        await btn('#fFit'); await pg.screenshot(path='o2.png')
        ck('JS hatası yok', not errs, errs[:3]); await b.close()
    print('TOPLAM', sum(R), '/', len(R)); sys.exit(0 if all(R) else 1)
asyncio.run(main())
