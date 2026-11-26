# YENİ CAD: ölçme modunda not — krokide yere dokun, telefon klavyesiyle yaz, iğne olarak görünür, duvarla gelir, DXF NOT katmanı, düzenle/sil
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
        async def wtap(x,y): s=await S(x,y); await pg.touchscreen.tap(s[0],s[1]); await pg.wait_for_timeout(80)
        await ev("""CAD.D={nid:10,ents:[{id:'r',t:'pl',p:[[0,0],[4,0],[4,3],[0,3]],c:true}],ops:[]}; Object.assign(CAD.view,{s:50,ox:30,oy:330}); CAD.commit()""")
        await btn('mode'); await btn('t:note')
        ck('Ölçme modunda not aracı', await ev("CAD.S.tool")=='note')
        await wtap(4,1.5)
        ck('dokununca yazı kutusu açıldı ve odaklandı (telefon klavyesi)', await ev("document.activeElement && document.activeElement.id")=='ntIn')
        await pg.keyboard.type('Pencere altı nemli\nsıva dökük')
        await btn('ntok'); N=await ev("JSON.parse(JSON.stringify(CAD.noteList()))")
        ck('not kaydedildi, sağ duvara iliştirildi', len(N)==1 and N[0]['s']=='Pencere altı nemli\nsıva dökük' and abs(N[0]['p'][0]-4)<1e-9, N)
        await wtap(1,1); await ev("document.querySelector('#ntIn').value=''"); await btn('ntok')
        ck('boş bırakılan yeni not kaydedilmez', len(await ev("CAD.noteList()"))==1)
        # duvarla birlikte gelme
        await btn('mode'); await btn('sec'); await wtap(4,2.5)
        sp=await S(4,1.5); tp=await S(4.6,1.5)
        await cdp.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':sp[0],'y':sp[1]}]})
        for k in range(1,11): await cdp.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{'x':sp[0]+(tp[0]-sp[0])*k/10,'y':sp[1]}]})
        await cdp.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]}); await pg.wait_for_timeout(80)
        ck('duvar kayınca not da geldi', abs(await ev("CAD.noteList()[0].p[0]")-4.6)<1e-6, await ev("CAD.noteList()[0].p"))
        dx=await ev("CAD.makeDXF()")
        ck('DXF NOT katmanında iki satır', '\r\nNOT\r\n' in dx and 'Pencere alt' in dx and 's\\U+0131va d\\U+00F6k\\U+00FCk' in dx)
        # düzenle ve sil
        await btn('mode'); await btn('t:note'); await wtap(4.6+0.18,1.5+0.18)
        ck('nota dokununca düzenleme açıldı', (await ev("document.querySelector('#ntIn') && document.querySelector('#ntIn').value"))=='Pencere altı nemli\nsıva dökük')
        await btn('ntdel')
        ck('not silindi', len(await ev("CAD.noteList()"))==0)
        await btn('undo')
        ck('geri al notu geri getirdi', len(await ev("CAD.noteList()"))==1)
        await pg.screenshot(path=str(OUT/'c10.png'))
        ck('JS hatası yok', not errs, errs[:3]); await b.close()
    print('TOPLAM', sum(R), '/', len(R)); sys.exit(0 if all(R) else 1)
asyncio.run(main())
