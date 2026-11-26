# YENİ CAD: başlangıç noktası hizası, yayla kapanan alan, explode/join geri bildirimi + iki adımlı join, son aracı direkt açma
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
        async def btn(a):
            r = await ev(f"(()=>{{const e=document.querySelector('button[data-a=\"{a}\"]'); if(!e) return null; const r=e.getBoundingClientRect(); return [r.left+r.width/2, r.top+r.height/2]}})()")
            if not r: return False
            await pg.touchscreen.tap(r[0], r[1]); await pg.wait_for_timeout(60); return True
        async def S(x,y): return await ev(f"CAD.w2s({x},{y})")
        async def wtap(x,y): s=await S(x,y); await pg.touchscreen.tap(s[0],s[1]); await pg.wait_for_timeout(60)
        E=lambda: ev("JSON.parse(JSON.stringify(CAD.D.ents))")
        await ev("Object.assign(CAD.view,{s:40,ox:40,oy:330}); CAD.render()")
        # 1) başlangıç noktası hizası
        await btn('fly:draw'); await btn('t:pl')
        await wtap(0,0); await wtap(4,0); await wtap(4,3)
        sn = await ev("(()=>{const s=CAD.w2s(0.15,3.06); return [s[0],s[1]]})()")
        await pg.touchscreen.tap(*sn); await pg.wait_for_timeout(60)
        e=(await E())[0]
        ck('dördüncü köşe başlangıç hizasına oturdu (0,3)', near(e['p'][3],(0,3)), e['p'])
        await wtap(0,0); e=(await E())[0]
        ck('  kapandı, tam dikdörtgen', e['c'] and len(e['p'])==4, e)
        # 2) yayla kapanan alan
        await ev("""CAD.D={nid:20,ents:[{id:'a',t:'line',a:[0,0],b:[4,0]},{id:'b',t:'line',a:[4,0],b:[4,3]},{id:'c',t:'line',a:[0,3],b:[0,0]},Object.assign(arc3([4,3],[2,4],[0,3]),{id:'d'})]}; CAD.commit()""")
        ck('yayla kapanan alan dolgulu (1 alan)', await ev("faces(CAD.D.ents).length")==1)
        await ev("CAD.D={nid:20,ents:[{id:'k',t:'cir',c:[2,2],r:1}]}; CAD.commit()")
        ck('  daire de kapalı alan', await ev("faces(CAD.D.ents).length")==1)
        # 3) explode geri bildirimi
        await ev("CAD.D={nid:30,ents:[{id:'q',t:'pl',p:[[0,0],[4,0],[4,3],[0,3]],c:true},{id:'t1',t:'line',a:[6,0],b:[6,3]},{id:'t2',t:'line',a:[6,3],b:[8,3]},{id:'t3',t:'line',a:[6,3],b:[6,5]}]}; CAD.S.sel.clear(); CAD.commit()")
        await btn('fly:edit'); await btn('t:explode'); await wtap(2,0);
        ck('explode: 4 çizgi ve parçalar yanıp sönüyor', len(await E())==7 and await ev("CAD.S.flash && CAD.S.flash.ids.size")==4)
        await pg.wait_for_timeout(1150)
        ck('  yanıp sönme bitti', await ev("CAD.S.flash")==None)
        # 4) join: üçlü düğümde otomatik olmaz → ilk dokunuş seçer, ikinci ekler
        await btn('fly:edit'); await btn('t:join'); await wtap(6,1.5)
        ck('join: üçlü düğümde ilk obje seçili kaldı', await ev("[...CAD.S.sel].join()")=='t1')
        await wtap(7,3)
        J=[x for x in await E() if x['t']=='pl' and not x['c']]
        ck('  ikinci dokunuşla birleşti (3 nokta) ve yanıp söndü', len(J)==1 and len(J[0]['p'])==3 and await ev("!!CAD.S.flash"), J)
        # 5) sütundaki Çiz düğmesi son aracı direkt açar
        await btn('fly:edit'); await btn('t:trim')
        await btn('fly:draw')
        ck('Çiz düğmesi: son araç (pline) direkt aktif, pencere açık', await ev("CAD.S.tool")=='pl' and await ev("CAD.S.fly")=='draw')
        await wtap(1,6)
        ck('  pencereye basmadan çizime geçince pencere kapandı, nokta konuldu', await ev("CAD.S.fly")==None and await ev("CAD.S.chain && CAD.S.chain.pts.length")==1)
        await btn('fly:draw'); await btn('t:line')
        ck('  pencereden başka araç seçilebiliyor', await ev("CAD.S.tool")=='line')
        await btn('fly:edit')
        ck('Düzenle düğmesi: son araç (trim) direkt aktif', await ev("CAD.S.tool")=='trim')
        ck('JS hatası yok', not errs, errs[:3]); await b.close()
    print('TOPLAM', sum(R), '/', len(R)); sys.exit(0 if all(R) else 1)
asyncio.run(main())
