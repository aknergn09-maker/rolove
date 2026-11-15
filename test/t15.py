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
        RA = "Object.fromEntries(RK.P.rooms.map(r=>[r.name, RK.rA(r)==null?null:+RK.rA(r).toFixed(3)]))"
        STEPS = "RK.P.lines.filter(l=>l.step).map(l=>[l.a,l.b].map(id=>{const n=RK.P.nodes.find(x=>x.id===id); return [+n.x.toFixed(3),+n.y.toFixed(3)]})).sort((p,q)=>p[0][1]-q[0][1])"
        await ev("""(()=>{const P=RK.P; const C=[[0,0],[6,0],[6,5],[0,5]]; const ids=C.map(([x,y],i)=>{const id='a'+i; P.nodes.push({id,x,y}); return id}); for(let i=0;i<4;i++) P.lines.push({id:'A'+i,a:ids[i],b:ids[(i+1)%4],kind:'typed'}); P.rooms.push({id:'rA',name:'A',ax:3,ay:2.5}); RK.commit(); RK.view.s=48; RK.view.ox=20; RK.view.oy=330; RK.commit();})()""")
        ck('sürüm görünür', (await ev("RK.VER")).startswith('v'))
        await btn('#cats button[data-cat=ekle]'); await btn('#tools button[data-tool=merdiven]')
        q = await W(6,1); await ctap(*q); await typ(100); await btn('#sheet button[data-a=ar][data-v="2"]'); await typ(300); await btn('#sheet button[data-a=ar][data-v="1"]'); q = await W(6,4); await ctap(*q)
        await btn('#sheet button[data-a=mkm][data-v=bas]')
        # köşeye yakın dokunuş da kenarı seçer (6. madde)
        q = await W(5,1.15); await ctap(*q); q = await W(6,1.15); await ctap(*q)
        ck('köşeye yakın dokunuşla iki kenar seçildi', await ev("!!(RK.S.mk.l1 && RK.S.mk.l2 && RK.S.mk.l1!==RK.S.mk.l2)"), await ev("RK.S.mk"))
        await typ(4); await btn('#sheet button[data-a=stp]')
        s0 = await ev(STEPS); ck('basamaklar atıldı (y=2,3) ve merdivene bağlı', [x[0][1] for x in s0]==[2,3] and await ev("RK.P.stepSets.length==1 && !!RK.P.stepSets[0].stair"), [s0, await ev("JSON.stringify(RK.P.stepSets)")])
        await btn('#sheet button[data-a=mkm][data-v=yon]'); q = await W(5.5,1.2); await ctap(*q); q = await W(5.5,3.8); await ctap(*q); await btn('#sheet button[data-a=yonok]')
        ck('yön oku merdivene bağlı', await ev("RK.P.arrows.length==1 && !!RK.P.arrows[0].stair && !!RK.P.arrows[0].ref"))
        # merdiven çerçevesini taşı (frame düğümleri) → basamak ve ok izler
        fr = await ev("RK.P.rooms.find(r=>r.kind==='merdiven')._f.poly.map(p=>RK.P.nodes.find(n=>Math.hypot(n.x-p[0],n.y-p[1])<1e-6)).filter(Boolean).map(n=>n.id)")
        await ev(f"(()=>{{RK.snap&&0; const ids={fr}; ids.forEach(id=>{{const n=RK.P.nodes.find(x=>x.id===id); n.x-=2;}}); RK.commit();}})()")
        s1 = await ev(STEPS); ar = await ev("RK.P.arrows[0].pts")
        ck('çerçeve 2 m sola taşınınca basamaklar izledi', len(s1)==2 and all(abs(x[0][0]-3)<1e-6 or abs(x[1][0]-3)<1e-6 for x in s1), s1)
        ck('ok da izledi', abs(ar[0][0]-3.5)<1e-6, ar)
        # Ötele: kısa kenar uzarsa basamaklar yeniden dağılır
        await ev(f"(()=>{{const ids={fr}; ids.forEach(id=>{{const n=RK.P.nodes.find(x=>x.id===id); if (n.y>3.5) n.y+=1;}}); RK.commit();}})()")
        s2 = await ev(STEPS); ck('çerçeve 1 m uzayınca 4 rıh yeniden eşit dağıldı (y=2.333, 3.667)', [x[0][1] for x in s2]==[2.333,3.667], s2)
        # basamak çizgisini Sil → set gider, geri gelmez
        await btn('#cats button[data-cat=duz]'); await btn('#tools button[data-tool=sil]')
        q = await W(3.2,2.333); await ctap(*q)
        ck('bir basamak çizgisi silinince o set silindi, geri gelmedi', await ev("RK.P.lines.filter(l=>l.step).length")==0 and await ev("RK.P.stepSets.length")==0)
        await ev("RK.undo()"); ck('geri al: basamaklar geri', await ev("RK.P.lines.filter(l=>l.step).length")==2)
        # merdiven işaretini kaldır → basamak ve ok gider
        await ev("(()=>{RK.P.rooms=RK.P.rooms.filter(r=>r.kind!=='merdiven'); RK.commit();})()")
        ck('merdiven kaldırılınca basamaklar ve ok da gitti', await ev("RK.P.lines.filter(l=>l.step).length")==0 and await ev("RK.P.arrows.length")==0)
        # aynı adlı proje
        n1 = await ev("RK.P.name"); n2 = await ev("RK.uniqName(RK.P.name)")
        ck('aynı adlı yeni proje üstüne yazmaz: ' + n2, n2 != n1 and n2.startswith(n1))
        # yedek uyarısı
        await ev("RK.P.backupAt=0; RK.P.saved=Date.now(); RK.commit()")
        ck('yedeği olmayan projede ☰ kırmızı nokta', await ev("document.getElementById('bMenu').classList.contains('warn')"))
        await btn('#bMenu'); await pg.wait_for_timeout(300); ck('☰ dokunuşla menü AÇIK kalır', not await ev("document.querySelector('#modal').classList.contains('hid')"))
        ck('menüde sürüm ve yedek bilgisi', await ev("document.querySelector('#mbox').textContent.includes(RK.VER) && document.querySelector('#mbox').textContent.includes('yedeği yok')"))
        r = await ev("(()=>{const r=document.querySelector('#modal').getBoundingClientRect(); return [r.left+8, r.top+8]})()"); await pg.wait_for_timeout(700); await pg.touchscreen.tap(*r); await pg.wait_for_timeout(200)
        ck('boşluğa dokununca menü kapanır', await ev("document.querySelector('#modal').classList.contains('hid')"))
        await ev("document.querySelector('#modal').classList.add('hid')")
        # kayıt hatası uyarısı
        msgs=[]; pg.on('dialog', lambda d: (msgs.append(d.message), asyncio.ensure_future(d.dismiss())))
        await ev("(()=>{const o=Storage.prototype.setItem; Storage.prototype.setItem=function(){throw new DOMException('dolu','QuotaExceededError')}; RK.commit(); Storage.prototype.setItem=o;})()"); await pg.wait_for_timeout(200)
        ck('hafıza dolunca KAYDEDİLEMEDİ uyarısı çıkar', any('KAYDEDİLEMEDİ' in m for m in msgs), msgs)
        ck('JS hatası yok', not errs, errs[:3]); await b.close()
    print('TOPLAM', sum(R), '/', len(R)); sys.exit(0 if all(R) else 1)
asyncio.run(main())
