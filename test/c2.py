# YENİ CAD: orta tutamak — ayrı çizgilerde komşular kendi doğrultusunda uzar, T bağlantısı kenarda kalır, aynı doğrultudaki pline parçaları tek kenar
import os, pathlib, sys, asyncio
ROOT = pathlib.Path(__file__).resolve().parent.parent
URL = (ROOT / 'cad.html').as_uri()
CHROME = os.environ.get('CHROME', '/usr/bin/google-chrome' if os.path.exists('/usr/bin/google-chrome') else None)
from playwright.async_api import async_playwright
R=[]
def ck(n,ok,i=''): R.append(bool(ok)); print(('PASS ' if ok else 'FAIL ')+n, '' if ok else i)
def near(a,b,t=1e-6): return all(abs(x-y)<t for x,y in zip(a,b))
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path=CHROME, args=['--no-sandbox'])
        ctx=await b.new_context(**p.devices['iPhone 13']); pg=await ctx.new_page(); errs=[]
        pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto(URL); await pg.evaluate("localStorage.clear()"); await pg.reload(); await pg.wait_for_timeout(300); ev=pg.evaluate
        cdp=await ctx.new_cdp_session(pg)
        async def S(x,y): return await ev(f"CAD.w2s({x},{y})")
        async def wtap(x,y): s=await S(x,y); await pg.touchscreen.tap(s[0],s[1]); await pg.wait_for_timeout(60)
        async def drag(p0,p1,n=12):
            a=await S(*p0); c=await S(*p1)
            await cdp.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':a[0],'y':a[1]}]})
            for k in range(1,n+1): await cdp.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{'x':a[0]+(c[0]-a[0])*k/n,'y':a[1]+(c[1]-a[1])*k/n}]})
            await cdp.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]}); await pg.wait_for_timeout(80)
        E=lambda: ev("Object.fromEntries(CAD.D.ents.map(e=>[e.id,e]))")
        # ayrı çizgiler: eğik sol duvar, dik sağ duvar, üst kenar; ortadaki bölme üst kenara T ile bağlı
        await ev("""CAD.D={nid:10,ents:[{id:'L',t:'line',a:[0,0],b:[-1,4]},{id:'T',t:'line',a:[-1,4],b:[4,4]},{id:'Rr',t:'line',a:[4,4],b:[4,0]},{id:'P',t:'line',a:[2,1],b:[2,4]}]};
          Object.assign(CAD.view,{s:40,ox:80,oy:420}); CAD.setTool('sec'); CAD.commit()""")
        await wtap(3,4)
        await drag((1.5,4),(1.5,5))
        e=await E()
        ck('üst kenar 1 m yukarı', near(e['T']['a'][1:],[5]) and near(e['T']['b'][1:],[5]), e['T'])
        ck('  eğik sol duvar kendi doğrultusunda uzadı (-1.25,5)', near(e['L']['b'],(-1.25,5)) and near(e['T']['a'],(-1.25,5)), [e['L'],e['T']])
        ck('  sağ duvar uzadı (4,5)', near(e['Rr']['a'],(4,5)), e['Rr'])
        ck('  T bağlı bölme kenarda kaldı (2,5)', near(e['P']['b'],(2,5)) and near(e['P']['a'],(2,1)), e['P'])
        # pline, alt kenarda aynı doğrultuda ara köşe (kapı noktası gibi): tek kenar sayılır
        await ev("""CAD.D={nid:10,ents:[{id:'Q',t:'pl',p:[[0,0],[1.5,0],[2.5,0],[4,0],[4,3],[0,3]],c:true}]}; CAD.S.sel.clear(); CAD.commit()""")
        await wtap(3.2,0)
        g=await ev("gripsOf(CAD.D.ents[0]).filter(g=>g.k==='m').length")
        ck('aynı doğrultudaki 3 parça tek orta tutamak (toplam 4 kenar)', g==4, g)
        await drag((2,0),(2,-0.5))
        q=(await E())['Q']['p']
        ck('  alt kenarın tüm noktaları birlikte kaydı (kapı noktaları dahil)', all(abs(p[1]+0.5)<1e-9 for p in q[:4]) and near(q[1],(1.5,-0.5)) and near(q[2],(2.5,-0.5)), q)
        ck('JS hatası yok', not errs, errs[:3]); await b.close()
    print('TOPLAM', sum(R), '/', len(R)); sys.exit(0 if all(R) else 1)
asyncio.run(main())
