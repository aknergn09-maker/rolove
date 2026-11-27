# YENİ CAD: nokta adı — hiza noktası çizgi üstündeyse ad verilebilir; geri al numarayı da geri alır (29 → geri al → yine 29), ileri al ilerletir; hiza kaynağı sadece köşeler
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
        async def btn(a):
            r = await ev(f"(()=>{{const e=document.querySelector('button[data-a=\"{a}\"]'); if(!e) return null; const r=e.getBoundingClientRect(); return [r.left+r.width/2, r.top+r.height/2]}})()")
            if not r: return False
            await pg.touchscreen.tap(r[0], r[1]); await pg.wait_for_timeout(60); return True
        async def S(x,y): return await ev(f"CAD.w2s({x},{y})")
        async def wtap(x,y): s=await S(x,y); await pg.touchscreen.tap(s[0],s[1]); await pg.wait_for_timeout(80)
        await ev("""CAD.D={nid:10,ents:[{id:'r',t:'pl',p:[[0,0],[5,0],[5,4],[0,4]],c:true},{id:'k',t:'pl',p:[[2.2,1.6],[2.6,1.6],[2.6,2],[2.2,2]],c:true}],ops:[]};
          Object.assign(CAD.view,{s:50,ox:30,oy:330}); CAD.commit()""")
        await btn('mode'); await btn('t:tag'); await pg.fill('#nmIn','28')
        await wtap(0,0)
        ck('28 köşeye verildi, sıradaki 29', await ev("CAD.nameList().map(n=>n.n).join()")=='28' and await ev("CAD.S.nameNext")=='29')
        await wtap(3.5,4)
        ck('29 verildi', await ev("CAD.nameList().map(n=>n.n).join()")=='28,29' and await ev("CAD.S.nameNext")=='30')
        await btn('undo')
        ck('geri al: 29 silindi, sıradaki yine 29, kutuda 29', await ev("CAD.nameList().map(n=>n.n).join()")=='28' and await ev("CAD.S.nameNext")=='29' and await ev("document.querySelector('#nmIn').value")=='29')
        await wtap(4,4)
        ck('  başka yere dokununca yine 29', await ev("CAD.nameList().map(n=>n.n).join()")=='28,29' and await ev("CAD.nameList()[1].p.join()")=='4,4')
        await btn('undo'); await btn('redo')
        ck('ileri al: 29 geri geldi, sıradaki 30', await ev("CAD.nameList().map(n=>n.n).join()")=='28,29' and await ev("CAD.S.nameNext")=='30')
        # kolon köşesinin hizası üst duvarın üstünde: hiza noktasına ad verilebilir
        await wtap(2.22,3.98)
        N=await ev("JSON.parse(JSON.stringify(CAD.nameList()))")
        ck('çizgi üstündeki hiza noktasına ad verilebildi', len(N)==3 and N[-1]['n']=='30', N)
        ck('hiza kaynakları sadece köşeler (nokta adları değil)', await ev("cornerPts().length")==8)
        ck('JS hatası yok', not errs, errs[:3]); await b.close()
    print('TOPLAM', sum(R), '/', len(R)); sys.exit(0 if all(R) else 1)
asyncio.run(main())
