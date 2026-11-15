# ÖNİZLEME: duvar birleşimleri (T ve artı) — görsel kontrol + kesişim pikselleri
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
        # dış kutu (duvar dışa) + ortada T bölme duvarı (merkezli) + artı kesişimi
        await ev("""(()=>{const P=RK.P; const N=(id,x,y)=>P.nodes.push({id,x,y}); const L=(id,a,b)=>P.lines.push({id,a,b,kind:'sketch'});
          N('a',0,0);N('b',6,0);N('c',6,4);N('d',0,4); L('1','a','b');L('2','b','c');L('3','c','d');L('4','d','a'); P.walls.push({id:'W1',nodes:['a','b','c','d'],closed:true,t:0.2,side:1});
          N('m',3,0);N('n',3,4); L('5','m','n'); N('p',0,2);N('q',6,2); L('6','p','q');
          RK.commit(); P.walls.push({id:'W2',nodes:['m','n'],closed:false,t:0.2,side:1}); P.walls.push({id:'W3',nodes:['p','q'],closed:false,t:0.2,side:1}); RK.commit(); RK.view.s=55; RK.view.ox=30; RK.view.oy=330; RK.commit();})()""")
        await pg.screenshot(path='p3.png')
        # artı kesişiminin ortasında (bantların üst üste geldiği yer) kenar çizgisi rengi (#cbd5e1) olmamalı
        px = await ev("""(()=>{const c=document.querySelector('#cv'); const g=c.getContext('2d'); const [X,Y]=RK.w2s(3.1,2.1); const d=window.devicePixelRatio||1; const v=g.getImageData(Math.round(X*d),Math.round(Y*d),1,1).data; return [v[0],v[1],v[2]]})()""")
        ck('artı birleşimin içinde kenar çizgisi yok (tarama/dolgu)', not (px[0]>180 and px[1]>190 and px[2]>200), px)
        n = await ev("RK.P.rooms.length")
        ck('4 oda oluşur (bölmeler ve iç yüzler sınır)', n==0 or n>=4, n)
        ck('JS hatası yok', not errs, errs[:3]); await b.close()
    print('TOPLAM', sum(R), '/', len(R)); sys.exit(0 if all(R) else 1)
asyncio.run(main())
