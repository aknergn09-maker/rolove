import os, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
URL = (ROOT / os.environ.get('PAGE', 'index.html')).as_uri()
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
            await pg.touchscreen.tap(r[0], r[1]); await pg.wait_for_timeout(80); return True
        # küçük oda: oda adı ve ölçüler çakışmasın
        await ev("""(()=>{const P=RK.P; const C=[[0,0],[1.2,0],[1.2,0.8],[0,0.8]]; const ids=C.map(([x,y],i)=>{const id='a'+i; P.nodes.push({id,x,y}); return id}); for(let i=0;i<4;i++) P.lines.push({id:'A'+i,a:ids[i],b:ids[(i+1)%4],kind:'sketch'}); P.rooms.push({id:'r',name:'Uzun oda adı WC',ax:0.6,ay:0.4}); RK.commit(); RK.view.s=70; RK.view.ox=80; RK.view.oy=300; RK.commit();})()""")
        ov = await ev("(()=>{let n=0; for(let i=0;i<RK.LB.length;i++) for(let j=i+1;j<RK.LB.length;j++) if(RK.polyHit(RK.LB[i],RK.LB[j])) n++; return [RK.LB.length, n]})()")
        ck('dar odada yazılar çakışmıyor (ölçüler + oda adı)', ov[0]>=5 and ov[1]==0, ov)
        await pg.screenshot(path='t19.png')
        await btn('#bMenu'); await pg.wait_for_timeout(250)
        has = await ev("[...document.querySelectorAll('#mbox button[data-m=go]')].map(b=>b.dataset.v)")
        ck('menüde önizleme/ana uygulama ve eski sürüm düğmeleri', ('onizleme.html' in has or 'index.html' in has) and 'eski.html' in has, has)
        tgt = 'onizleme.html' if 'onizleme.html' in has else 'index.html'
        await btn(f'#mbox button[data-v="{tgt}"]'); await pg.wait_for_timeout(600)
        ck('düğmeye dokununca ' + tgt + ' açılır', pg.url.endswith(tgt), pg.url)
        ck('JS hatası yok', not errs, errs[:3]); await b.close()
    print('TOPLAM', sum(R), '/', len(R)); sys.exit(0 if all(R) else 1)
asyncio.run(main())
