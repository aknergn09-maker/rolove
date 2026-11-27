# YENİ CAD: obje üstünde hizalama — parmak bir duvarın üstündeyken, geçilen köşenin hizasının o duvara düştüğü nokta yakalanır (çizim, ölçü, tutamak)
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
        async def btn(a):
            r = await ev(f"(()=>{{const e=document.querySelector('button[data-a=\"{a}\"]'); if(!e) return null; const r=e.getBoundingClientRect(); return [r.left+r.width/2, r.top+r.height/2]}})()")
            if not r: return False
            await pg.touchscreen.tap(r[0], r[1]); await pg.wait_for_timeout(60); return True
        async def S(x,y): return await ev(f"CAD.w2s({x},{y})")
        async def path(pts,n=10):
            sp=[await S(*q) for q in pts]
            await cdp.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':sp[0][0],'y':sp[0][1]}]}); await pg.wait_for_timeout(40)
            for (x0,y0),(x1,y1) in zip(sp,sp[1:]):
                for k in range(1,n+1): await cdp.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{'x':x0+(x1-x0)*k/n,'y':y0+(y1-y0)*k/n}]}); await pg.wait_for_timeout(8)
            await cdp.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]}); await pg.wait_for_timeout(80)
        # oda + ortada kolon (köşesi 2.2,1.6) — eğik alt duvar ki XY hizası değil, köşe hizası ve uzantı kesişimi denensin
        await ev("""CAD.D={nid:10,ents:[{id:'r',t:'pl',p:[[0,0],[5,0],[5,4],[0,4]],c:true},{id:'k',t:'pl',p:[[2.2,1.6],[2.6,1.6],[2.6,2],[2.2,2]],c:true}],ops:[]};
          Object.assign(CAD.view,{s:50,ox:30,oy:330}); CAD.commit()""")
        await btn('fly:draw'); await btn('t:line')
        # parmak kolon köşesinden geçip alt duvarın üstüne (hizaya 6 cm uzak) iner
        await path([(2.2,1.6),(2.25,0.8),(2.26,0.03)])
        ck('çizgi: kolon köşesinin hizası alt duvarın üstünde yakalandı (2.2,0)', near(await ev("CAD.S.chain && CAD.S.chain.pts[0]"),(2.2,0)), await ev("CAD.S.chain && CAD.S.chain.pts"))
        await btn('qok')
        # ölçme: obje yakalayan, sol duvarın üstünde kolon köşesinin yatay hizası
        await btn('mode'); await btn('t:m_pp')
        await path([(2.2,1.6),(1.0,1.62),(0.02,1.66)])
        q=await ev("JSON.parse(JSON.stringify(CAD.S.mq))")
        ck('ölçü: sol duvar üstünde köşe hizası (0,1.6)', q and near(q['picks'][0]['p'],(0,1.6)), q)
        await btn('undo'); await btn('mode')
        # tutamak: kapı noktası gibi bir köşeyi sürüklerken de hiza
        await ev("CAD.D.ents.push({id:'L',t:'line',a:[4,4],b:[4,3]}); CAD.S.sel.clear(); CAD.commit()")
        await btn('sec'); s=await S(4,3.5); await pg.touchscreen.tap(*s); await pg.wait_for_timeout(80)
        await path([(4,4),(3,3.0),(2.6,2.0),(2.66,3.2),(2.63,3.96)])
        L=await ev("JSON.parse(JSON.stringify(CAD.D.ents.find(e=>e.id==='L')))")
        ck('tutamak: köşe üst duvarda kolon köşesinin hizasına oturdu (2.6,4)', near(L['a'],(2.6,4)), L)
        # kullanıcının resmi: yukarıdan aşağı pline çizerken alttaki çizginin ucu eksenin 7 px yanında → eksen üstündeki izdüşüm yakalanmalı
        await ev("""CAD.D={nid:10,ents:[{id:'u',t:'pl',p:[[4,4],[0,4]],c:false},{id:'b',t:'line',a:[0.14,0],b:[1.2,0]}],ops:[]}; Object.assign(CAD.view,{s:50,ox:60,oy:330}); CAD.S.sel.clear(); CAD.commit()""")
        await btn('fly:draw'); await btn('t:pl')
        s0=await S(0,4); await pg.touchscreen.tap(*s0); await pg.wait_for_timeout(80)
        await path([(0.02,3),(0.03,1),(0.08,0.08)])
        pts=await ev("CAD.S.chain && CAD.S.chain.pts")
        ck('alttaki çizginin ucu eksen yanındayken, eksen üstündeki hiza noktası (0,0) yakalandı, çizgi dik kaldı', pts and len(pts)==2 and near(pts[1],(0,0)), pts)
        await btn('qok')
        ck('JS hatası yok', not errs, errs[:3]); await b.close()
    print('TOPLAM', sum(R), '/', len(R)); sys.exit(0 if all(R) else 1)
asyncio.run(main())
