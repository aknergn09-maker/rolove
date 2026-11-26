# YENİ CAD: offset otomatik kesme — yan yana iki oda (aralık = duvar), ikisine dış offset → tek dış hat, arada çizgi/çıkıntı yok; tek oda ve kolon kesilmez; ayardan kapatılır
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
        async def btn(a):
            r = await ev(f"(()=>{{const e=document.querySelector('button[data-a=\"{a}\"]'); if(!e) return null; const r=e.getBoundingClientRect(); return [r.left+r.width/2, r.top+r.height/2]}})()")
            if not r: return False
            await pg.touchscreen.tap(r[0], r[1]); await pg.wait_for_timeout(60); return True
        async def S(x,y): return await ev(f"CAD.w2s({x},{y})")
        async def wtap(x,y): s=await S(x,y); await pg.touchscreen.tap(s[0],s[1]); await pg.wait_for_timeout(60)
        await ev("""CAD.D={nid:10,ents:[{id:'r1',t:'pl',p:[[0,0],[4,0],[4,3],[0,3]],c:true},{id:'r2',t:'pl',p:[[4.2,0],[7,0],[7,3],[4.2,3]],c:true},{id:'k',t:'cir',c:[1.5,1.5],r:0.3}],ops:[]};
          Object.assign(CAD.view,{s:40,ox:25,oy:330}); CAD.commit()""")
        await btn('fly:edit'); await btn('t:offset')
        await wtap(2,0); await wtap(2,-1)
        await wtap(5.5,0); await wtap(5.5,-1)
        news=await ev("CAD.D.ents.filter(e=>!['r1','r2','k'].includes(e.id)).map(e=>JSON.parse(JSON.stringify(e)))")
        segs=[]
        for e in news:
            pts=e['p'] if e['t']=='pl' else [e['a'],e['b']]
            for i in range(len(pts)-1): segs.append((pts[i],pts[i+1]))
        mid=[s for s in segs if 3.9<(s[0][0]+s[1][0])/2<4.3 and -0.19<(s[0][1]+s[1][1])/2<3.19]
        ck('iki odanın arasında offset çizgisi ve çıkıntı kalmadı', not mid, mid)
        ck('  iki parça dış hat birleşince kapalı dikdörtgen', await ev("(()=>{const n=CAD.D.ents.filter(e=>!['r1','r2','k'].includes(e.id)); const j=joinEnts(n); return !!j && j.ent.c && j.used.length===n.length})()"), news)
        await wtap(1.5,1.8); await wtap(1.5,2.5)
        ck('oda içindeki kolonun offset\'i kesilmedi', await ev("CAD.D.ents.some(e=>e.t==='cir' && Math.abs(e.r-0.5)<1e-9)"))
        await btn('fly:set')
        ck('ayarlarda otomatik kesme düğmesi açık', await ev("!!document.querySelector('button[data-a=scut].on')"))
        await btn('scut'); await btn('skok')
        await btn('fly:edit'); await btn('t:offset'); n0=await ev("CAD.D.ents.length")
        await wtap(2,3); await wtap(2,5)
        ck('kapalıyken offset kesilmeden tam kapalı çıkar', await ev("CAD.D.ents.length")==n0+1 and await ev("CAD.D.ents[CAD.D.ents.length-1].c"))
        await pg.screenshot(path=str(OUT/'c8.png'))
        ck('JS hatası yok', not errs, errs[:3]); await b.close()
    print('TOPLAM', sum(R), '/', len(R)); sys.exit(0 if all(R) else 1)
asyncio.run(main())
