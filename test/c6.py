# YENİ CAD: ayarlarda kapı/pencere kalınlık sınırı (varsayılan 60), kalınlık düğmesi (en yakın → tek çizgi → sonraki), seçimin hatırlanması
import os, pathlib, sys, asyncio
ROOT = pathlib.Path(__file__).resolve().parent.parent
URL = (ROOT / 'cad.html').as_uri()
CHROME = os.environ.get('CHROME', '/usr/bin/google-chrome' if os.path.exists('/usr/bin/google-chrome') else None)
from playwright.async_api import async_playwright
R=[]
def ck(n,ok,i=''): R.append(bool(ok)); print(('PASS ' if ok else 'FAIL ')+n, '' if ok else i)
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path=CHROME, args=['--no-sandbox'])
        ctx=await b.new_context(**p.devices['iPhone 13']); pg=await ctx.new_page(); errs=[]
        pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto(URL); await pg.evaluate("localStorage.clear()"); await pg.reload(); await pg.wait_for_timeout(300); ev=pg.evaluate
        cdp=await ctx.new_cdp_session(pg)
        async def btn(a):
            r = await ev(f"(()=>{{const e=document.querySelector('button[data-a=\"{a}\"]'); if(!e) return null; const r=e.getBoundingClientRect(); return [r.left+r.width/2, r.top+r.height/2]}})()")
            if not r: return False
            await pg.touchscreen.tap(r[0], r[1]); await pg.wait_for_timeout(60); return True
        async def S(x,y): return await ev(f"CAD.w2s({x},{y})")
        async def wtap(x,y): s=await S(x,y); await pg.touchscreen.tap(s[0],s[1]); await pg.wait_for_timeout(60)
        async def drag(p0,p1,n=12):
            a=await S(*p0); c=await S(*p1)
            await cdp.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':a[0],'y':a[1]}]})
            for k in range(1,n+1): await cdp.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{'x':a[0]+(c[0]-a[0])*k/n,'y':a[1]+(c[1]-a[1])*k/n}]})
            await cdp.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]}); await pg.wait_for_timeout(80)
        TH=lambda: ev("opTh(CAD.D.ops[0])")
        E=lambda: ev("Object.fromEntries(CAD.D.ents.map(e=>[e.id,e.p?e.p.length:0]))")
        # 1 m kalın taş duvar
        await ev("""CAD.D={nid:10,ents:[{id:'in',t:'pl',p:[[0,0],[4,0],[4,3],[0,3]],c:true},{id:'out',t:'pl',p:[[-1,-1],[5,-1],[5,4],[-1,4]],c:true}],ops:[]};
          Object.assign(CAD.view,{s:40,ox:70,oy:330}); CAD.commit()""")
        await btn('fly:open'); await wtap(1,0); await wtap(2,0)
        ck('varsayılan 60 cm: 1 m duvarda kapı tek çizgide', abs(await TH())<1e-9)
        await btn('fly:set')
        ck('ayarlarda sınır 60 görünüyor', (await ev("document.querySelector('#fly .sum').textContent"))=='60')
        await btn('sk:1'); await btn('sk:2'); await btn('sk:0'); await btn('skok')
        ck('  sınır 120 yapıldı ve kaydedildi', abs(await ev("CAD.S.thMax")-1.2)<1e-9 and abs(await ev("JSON.parse(localStorage.getItem('rcad1_doc')).thMax")-1.2)<1e-9)
        await btn('fly:edit'); await btn('t:erase'); await wtap(1.5,0)
        await btn('fly:open'); await btn('t:door'); await wtap(1,0); await wtap(2,0)
        e=await E()
        ck('  1 m duvarda kapı iki yüze yayıldı, dış pline\'a kırık noktası', abs(await TH()+1)<1e-9 and e['out']==6, [await TH(), e])
        # koridor: tek çizgili bölme + 1 m ötede karşı duvar
        await ev("""CAD.D={nid:10,ents:[{id:'w1',t:'pl',p:[[0,0],[6,0]],c:false},{id:'w2',t:'pl',p:[[0,1],[6,1]],c:false},{id:'w3',t:'pl',p:[[0,1.2],[6,1.2]],c:false}],ops:[]}; CAD.S.sel.clear(); CAD.commit()""")
        await wtap(1,1); await wtap(2,1)
        ck('koridor: en yakın paralel (20 cm) seçildi', abs(await TH()-0.2)<1e-9 and (await E())['w3']==4)
        await btn('sec'); await wtap(1.5,1)
        await btn('opw')
        ck('  kalınlık düğmesi: sıradaki (koridor karşısı -1 m), eski kırıklar kalktı', abs(await TH()+1)<1e-9 and (await E())['w3']==2 and (await E())['w1']==4, [await TH(), await E()])
        await btn('opw')
        ck('  sonra tek çizgi, kırıklar kalktı', abs(await TH())<1e-9 and (await E())['w1']==2)
        await btn('opw')
        ck('  sonra yine en yakın', abs(await TH()-0.2)<1e-9)
        await btn('opw')
        # seçim hatırlanır: karşı duvar (w1) kayınca kapı ona bağlı kalır, w3'e atlamaz
        await wtap(4.5,0); await drag((3,0),(3,0.5))
        ck('hatırlama: karşı duvar yaklaştı (-0.5), kapı yine onu tuttu', abs(await TH()+0.5)<1e-9, await TH())
        ck('JS hatası yok', not errs, errs[:3]); await b.close()
    print('TOPLAM', sum(R), '/', len(R)); sys.exit(0 if all(R) else 1)
asyncio.run(main())
