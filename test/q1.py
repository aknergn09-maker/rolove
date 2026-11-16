# ÖNİZLEME v12: duvar = iki bağımsız çizgi + taralı alan. Duvar çizme, T bağlantı, çıkıntı/kolon (kalınlaşsın / ofset korunsun), kapı, lazer, eski proje çevirme, Yön/kalınlık
import os, pathlib, json
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
        async def ctap(x,y):
            r = await ev("(()=>{const r=document.querySelector('#cv').getBoundingClientRect(); return [r.left,r.top]})()"); q = await ev(f"RK.w2s({x},{y})"); await pg.touchscreen.tap(r[0]+q[0], r[1]+q[1]); await pg.wait_for_timeout(200)
        async def typ(v):
            if not await ev("!!document.querySelector('#sheet button[data-k=C]')"): await btn('#sheet button[data-a=np]')
            await btn('#sheet button[data-k="C"]')
            for ch in str(v): await btn(f'#sheet button[data-k="{ch}"]')
        RM = "RK.P.rooms.filter(r=>!r.kind).map(r=>r._f? +RK.rA(r).toFixed(3):null)"
        TOAST = "document.querySelector('#toast').textContent"
        # 1) Duvar aracıyla 6×4 oda
        await ev("RK.view.s=40; RK.view.ox=60; RK.view.oy=290; RK.commit()")
        await btn('#tabs button[data-tab=cizim]'); await btn('#cats button[data-cat=ciz]'); await btn('#tools button[data-tool=duvar]')
        for x,y in [(0,0),(6,0),(6,4),(0,4),(0,0)]: await ctap(x,y)
        st = await ev("[RK.P.walls.length, RK.P.wq.length, RK.P.lines.length]")
        ck('duvar çizildi: karşı yüz gerçek çizgi (8 çizgi), 4 taralı dörtgen, eski tip duvar kalmadı', st==[0,4,8], st)
        ck('  oda 6×4=24 (bant dışta)', await ev(RM)==[24], await ev(RM))
        # 2) Yön: son duvar ters yüze
        await btn('#sheet button[data-a=wside]'); ck('⇄ Yön: bant içe döndü (oda 5.6×3.6=20.16), yine iki çizgi', await ev(RM)==[20.16] and await ev("RK.P.wq.length")==4, await ev(RM))
        await btn('#sheet button[data-a=wside]'); ck('  tekrar ⇄: 24', await ev(RM)==[24], await ev(RM))
        await btn('#sheet button[data-a=wt][data-v="0.3"]'); ck('  kalınlık 30 cm: dış çizgi 30 cm ötede', await ev("Math.min(...RK.P.nodes.map(n=>n.y))")==-0.3 and await ev(RM)==[24], await ev("Math.min(...RK.P.nodes.map(n=>n.y))"))
        await btn('#sheet button[data-a=wt][data-v="0.2"]')
        # 3) iç duvar (T): bağlandığı yerdeki çizgi silinir, iki oda
        await btn('#tools button[data-tool=duvar]'); await ctap(3,0); await ctap(3,4); await btn('#sheet button[data-a=end]')
        ck('iç duvar: iki oda (11.2 ve 12), bağlandığı yerlerde iç çizgi kesildi', sorted(await ev(RM))==[11.2,12] and await ev("!RK.P.lines.some(l=>{const a=RK.P.nodes.find(n=>n.id===l.a),b=RK.P.nodes.find(n=>n.id===l.b); return Math.abs(a.y-b.y)<1e-9 && Math.abs(a.y)<1e-9 && Math.min(a.x,b.x)<2.9 && Math.max(a.x,b.x)>3.1})"), await ev(RM))
        await pg.screenshot(path='q1a.png'); SAVED = await ev("JSON.stringify(RK.P)")
        # 4) dışa çıkıntı (dış çizgiden): varsayılan ofset korunsun
        await btn('#cats button[data-cat=duz]'); await btn('#tools button[data-tool=cikinti]'); await btn('#sheet button[data-a=cikm][data-v=el]')
        await ev("RK.view.s=60; RK.view.ox=-150; RK.view.oy=230; RK.commit()")
        for x,y in [(4,-0.2),(4,-0.7),(5,-0.7),(5,-0.2)]: await ctap(x,y)
        a = await ev(RM); ck('dışa çıkıntı: soru çıktı, varsayılan "Ofset korunsun": iç çizgi de kaydı (12 + 0.6×0.5 = 12.3)', await ev("RK.S.faceAsk&&RK.S.faceAsk.cur")=='kayar' and 12.3 in a, [a, await ev(TOAST)])
        await btn('#sheet button[data-a=faN]'); a = await ev(RM); ck('  "Duvar kalınlaşsın": iç çizgi yerinde (12), çıkıntı taralı duvar', 12 in a and 12.3 not in a and await ev("RK.P.fills.length")==1, a)
        await btn('#sheet button[data-a=faY]'); ck('  tekrar "Ofset korunsun": 12.3', 12.3 in await ev(RM))
        await pg.screenshot(path='q1b.png')
        # 5) köşe kolonu (iki çizgi): varsayılan kalınlaşsın
        await ev(f"RK.P=JSON.parse({SAVED!r}); RK.S.faceAsk=null; RK.commit(); RK.view.s=90; RK.view.ox=-250; RK.view.oy=560; RK.commit()")
        for x,y in [(5.5,4),(5.5,3.7),(6,3.7)]: await ctap(x,y)
        a = await ev(RM); ck('köşe kolonu: varsayılan "Duvar kalınlaşsın": oda 12 − 0.5×0.3 = 11.85, köşedeki iç çizgiler silindi', await ev("RK.S.faceAsk&&RK.S.faceAsk.cur")=='sabit' and 11.85 in a and not await ev("RK.P.lines.some(l=>{const A=RK.P.nodes.find(n=>n.id===l.a),B=RK.P.nodes.find(n=>n.id===l.b); return Math.abs(A.y-4)<1e-9&&Math.abs(B.y-4)<1e-9&&Math.max(A.x,B.x)>5.6})"), [a, await ev(TOAST)])
        await btn('#sheet button[data-a=faY]'); a = await ev(RM); ck('  köşede de "Ofset korunsun" seçilebilir: dış köşe de girdi, oda 11.85', 11.85 in a and await ev("RK.P.nodes.some(n=>Math.abs(n.x-5.7)<1e-6&&Math.abs(n.y-3.9)<1e-6)"), a)
        await pg.screenshot(path='q1c.png')
        # 6) kapı: iç çizgiye iki dokunuş → iki yüzde de boşluk, oda kapalı
        await ev(f"RK.P=JSON.parse({SAVED!r}); RK.S.faceAsk=null; RK.commit(); RK.view.s=70; RK.view.ox=-20; RK.view.oy=260; RK.commit()")
        await btn('#cats button[data-cat=ekle]'); await btn('#tools button[data-tool=aciklik]')
        await ctap(1,0); await ctap(1.9,0); await pg.wait_for_timeout(150)
        og = await ev("(()=>{const o=RK.P.openings[0]; if(!o) return null; const g=RK.opGeom(o); return [g.wall, +g.t.toFixed(3), +g.P0[0].toFixed(2), +g.P1[0].toFixed(2)]})()")
        ck('kapı: duvar kalınlığı 20 cm bulundu, 1.00–1.90', og==[True,0.2,1,1.9], [og, await ev(TOAST)])
        PX = """((x,y)=>{const cv=document.querySelector('#cv'); const r=window.devicePixelRatio||1; const q=RK.w2s(x,y); const d=cv.getContext('2d').getImageData(Math.round(q[0]*r),Math.round(q[1]*r),1,1).data; return d[0]>200&&d[1]>130&&d[1]<200&&d[2]<90})"""
        await ev("RK.SET.showLen=false; RK.commit()")
        ck('  kapı boşluğunda iki yüzde de çizgi yok, kapı dışında var', not await ev(PX+"(1.45,0)") and not await ev(PX+"(1.45,-0.2)") and await ev(PX+"(0.5,0)") and await ev(PX+"(0.5,-0.2)"))
        ck('  odalar kapalı kaldı', sorted(await ev(RM))==[11.2,12], await ev(RM))
        await ev("RK.SET.showLen=true; RK.commit()"); await pg.screenshot(path='q1d.png')
        sp = await ev("RK.P.nodes.filter(n=>Math.abs(n.y+0.2)<1e-6 && (Math.abs(n.x-1)<1e-6 || Math.abs(n.x-1.9)<1e-6)).length")
        ck('  karşı çizgi de kapı kenarlarından bölündü (1.00 ve 1.90)', sp==2, sp)
        # duvar alanı (tarama): iç duvar bandı → tarama kalkar; tekrar → taralı
        await ev(f"RK.P=JSON.parse({SAVED!r}); RK.commit(); RK.view.s=70; RK.view.ox=-20; RK.view.oy=320; RK.commit()")
        await btn('#tools button[data-tool=tarama]'); q0 = await ev("RK.P.wq.length")
        await ctap(2.9, 2); q1 = await ev("RK.P.wq.length"); ck('Duvar alanı aracı: iç duvar bandına dokununca o duvarın taraması kalktı', q1 == q0-1, [q0, q1, await ev(TOAST)])
        await ctap(2.9, 2); ck('  tekrar dokununca tarama geri geldi, odalar aynı', await ev("RK.P.wq.length")==q0 and sorted(await ev(RM))==[11.2,12], [await ev("RK.P.wq.length"), await ev(RM)])
        await ctap(4.5, 2); ck('  oda alanına dokununca taralı duvar alanı oldu, oda sayılmadı', await ev("RK.P.fills.length")==1 and await ev(RM)==[11.2], [await ev("RK.P.fills.length"), await ev(RM)])
        await ctap(4.5, 2); ck('  tekrar dokununca tarama kalktı, alan yine oda', await ev("RK.P.fills.length")==0 and sorted(await ev(RM))==[11.2,12], [await ev("RK.P.fills.length"), await ev(RM)])
        # alttaki düğmeleri gizle/aç
        h0 = await ev("document.querySelector('#cv').getBoundingClientRect().height"); await btn('#fBar')
        h1 = await ev("document.querySelector('#cv').getBoundingClientRect().height"); hid = await ev("getComputedStyle(document.querySelector('#bar')).display")
        ck('▾ düğmesi alttaki araç düğmelerini gizledi, çizim alanı büyüdü', hid=='none' and h1 > h0 + 40, [hid, h0, h1])
        await btn('#fBar'); ck('  ▴ ile geri geldi', await ev("getComputedStyle(document.querySelector('#bar')).display")!='none' and abs(await ev("document.querySelector('#cv').getBoundingClientRect().height")-h0)<1)
        await pg.screenshot(path='q1e.png')
        # 7) lazer: iç çizgi ölçülür, kalınlık korunur
        await ev(f"RK.P=JSON.parse({SAVED!r}); RK.commit(); RK.view.s=40; RK.view.ox=60; RK.view.oy=290; RK.commit()")
        await btn('#tabs button[data-tab=olcum]'); await btn('#tools button[data-tool=olc]'); await ctap(1.4,0); await typ(300); await btn('#sheet button[data-a=msok]')
        th = await ev("(()=>{const U=v=>[...new Set(v.map(z=>+z.toFixed(6)))].sort((a,b)=>a-b); const ys=U(RK.P.nodes.map(n=>n.y)); const xs=U(RK.P.nodes.map(n=>n.x)); return [+(ys[1]-ys[0]).toFixed(3), +(xs[1]-xs[0]).toFixed(3)]})()")
        ln = await ev("(()=>{const l=RK.P.lines.find(l=>l.kind==='laser'); return +RK.lineLen(l).toFixed(3)})()")
        ck('lazer 3.00: ölçülen çizgi oturdu, dış duvar kalınlığı 20 cm kaldı', ln==3 and th==[0.2,0.2], [ln, th])
        ck('  odalar ölçeklendi, iki oda var', len(await ev(RM))==2 and all(v for v in await ev(RM)), await ev(RM))
        # 8) eski proje: açılışta yedek + çevirme
        old = {"v":8,"name":"Eski","nodes":[{"id":"a0","x":0,"y":0},{"id":"a1","x":4,"y":0},{"id":"a2","x":4,"y":3},{"id":"a3","x":0,"y":3}],"lines":[{"id":"L0","a":"a0","b":"a1","kind":"sketch"},{"id":"L1","a":"a1","b":"a2","kind":"sketch"},{"id":"L2","a":"a2","b":"a3","kind":"sketch"},{"id":"L3","a":"a3","b":"a0","kind":"sketch"}],"walls":[{"id":"W","nodes":["a0","a1","a2","a3"],"closed":True,"t":0.2,"side":1}],"rooms":[{"id":"r","name":"Eski oda","ax":2,"ay":1.5}],"openings":[]}
        pg2 = await ctx.new_page(); pg2.on('pageerror', lambda e: errs.append(str(e)))
        await pg2.add_init_script(f"if (!sessionStorage.getItem('q1')) {{ sessionStorage.setItem('q1','1'); localStorage.clear(); localStorage.setItem('rk3p_projects', JSON.stringify({{'Eski': {json.dumps(old)}}})); localStorage.setItem('rk3p_current','Eski'); }}")
        await pg2.goto(URL); await pg2.wait_for_timeout(400); ev = pg2.evaluate
        st = await ev("[RK.P.name, RK.P.walls.length, (RK.P.wq||[]).length, RK.P.lines.length, Object.keys(JSON.parse(localStorage.getItem('rk3p_projects'))), RK.P.rooms.map(r=>r._f? +RK.rA(r).toFixed(3):null)]")
        ck('eski proje: yedeği alındı, duvar iki çizgiye çevrildi, oda aynı', st[0]=='Eski' and st[1]==0 and st[2]==4 and st[3]==8 and any('yedek' in k for k in st[4]) and st[5] in ([12],[10.64]), st)
        ck('JS hatası yok', not errs, errs[:3]); await b.close()
    print('TOPLAM', sum(R), '/', len(R)); sys.exit(0 if all(R) else 1)
asyncio.run(main())
