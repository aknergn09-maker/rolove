# YENİ CAD: çizim modu (B) — çizim sürerken sağda sadece ≡, geri, ileri, sığdır + altta 10/50/100; parmak ekrandayken soluk; ✓ ile normal sütun döner
import os, pathlib, sys, asyncio
ROOT = pathlib.Path(__file__).resolve().parent.parent
URL = (ROOT / 'cad.html').as_uri()
OUT = ROOT / 'test' / 'out'; OUT.mkdir(exist_ok=True)
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
        colA=lambda: ev("[...document.querySelectorAll('#col button')].map(b=>b.dataset.a).join(',')")
        await ev("Object.assign(CAD.view,{s:40,ox:40,oy:330}); CAD.render()")
        await btn('fly:draw'); await btn('t:pl')
        ck('araç seçildi, henüz çizim yok: normal sütun', 'fly:draw' in await colA())
        await wtap(0,0)
        ck('çizim başladı: sütunda sadece ≡ geri ileri sığdır', await colA()=='full,undo,redo,fit', await colA())
        ck('  10/50/100 paneli sağ altta, sütunla aynı kenarda', await ev("document.querySelector('#qp').className")=='mini' and await ev("Math.round(document.querySelector('#qp').getBoundingClientRect().right)")==390)
        s=await S(2,1)
        await cdp.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':s[0],'y':s[1]}]}); await pg.wait_for_timeout(250)
        ck('  parmak ekrandayken soluk', await ev("document.body.classList.contains('touching') && getComputedStyle(document.querySelector('#col')).opacity<0.5"))
        await cdp.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]}); await pg.wait_for_timeout(250)
        ck('  parmak kalkınca tekrar net', not await ev("document.body.classList.contains('touching')") and await ev("getComputedStyle(document.querySelector('#col')).opacity")=='1')
        await btn('fit')
        ck('  sığdır çizim sırasında çalışıyor, çizim sürüyor', await ev("CAD.S.chain && CAD.S.chain.pts.length")==2)
        await btn('full')
        ck('≡: normal sütun geri geldi, çizim bozulmadı', 'fly:draw' in await colA() and await ev("CAD.S.chain && CAD.S.chain.pts.length")==2)
        await ev("Object.assign(CAD.view,{s:40,ox:40,oy:330}); CAD.render()")
        await wtap(2,3)
        ck('  tuvale dokununca çizime devam, sütun yine küçük', await colA()=='full,undo,redo,fit' and await ev("CAD.S.chain.pts.length")==3)
        await btn('qok')
        ck('✓ ile çizim bitti, normal sütun döndü', 'fly:draw' in await colA() and not await ev("!!CAD.S.chain"))
        await btn('fly:draw'); await btn('t:cir'); await wtap(5,5)
        ck('daire çizerken de küçük sütun', await colA()=='full,undo,redo,fit')
        await btn('undo')
        ck('  geri al daireyi iptal etti, normal sütun', 'fly:draw' in await colA() and not await ev("!!CAD.S.cir"))
        await wtap(0,0); await pg.screenshot(path=str(OUT/'c4.png'))
        ck('JS hatası yok', not errs, errs[:3]); await b.close()
    print('TOPLAM', sum(R), '/', len(R)); sys.exit(0 if all(R) else 1)
asyncio.run(main())
