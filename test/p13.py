# ÖNİZLEME: Gönye — çapraz sadece kendi odasını düzeltir; ölçülü boylar ve 10 cm kırık korunur, komşu oda yalnız ortak duvarı izler; önizleme köşe açılarını gösterir
import os, pathlib, sys, asyncio, math
ROOT = pathlib.Path(__file__).resolve().parent.parent
URL = (ROOT / 'onizleme.html').as_uri()
OUT = ROOT / 'test' / 'out'; OUT.mkdir(exist_ok=True); os.chdir(OUT)
CHROME = os.environ.get('CHROME', '/usr/bin/google-chrome' if os.path.exists('/usr/bin/google-chrome') else None)
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
            await pg.touchscreen.tap(r[0], r[1]); await pg.wait_for_timeout(100); return True
        async def ctap(x,y):
            r = await ev("(()=>{const r=document.querySelector('#cv').getBoundingClientRect(); return [r.left,r.top]})()"); q = await ev(f"RK.w2s({x},{y})"); await pg.touchscreen.tap(r[0]+q[0], r[1]+q[1]); await pg.wait_for_timeout(200)
        await ev("""(()=>{const P=RK.P; P.nodes=[];P.lines=[];P.walls=[];P.rooms=[];P.diags=[];
          const C={A:[0,0],J1:[2,0],J2:[2,0.1],B:[4,0.1],C:[4,3],D:[0,3],E:[4,6],F:[0,6]}; Object.entries(C).forEach(([id,[x,y]])=>P.nodes.push({id,x,y}));
          [['A','J1',2],['J1','J2',null],['J2','B',2],['B','C',2.9],['C','D',4],['D','A',3],['C','E',null],['E','F',null],['F','D',null]].forEach(([a,b,m],i)=>P.lines.push(m?{id:'L'+i,a,b,kind:'laser',m}:{id:'L'+i,a,b,kind:'sketch'}));
          P.rooms.push({id:'r1',name:'Salon',ax:1,ay:1.5},{id:'r2',name:'Yatak',ax:2,ay:4.5}); RK.commit(); RK.view.s=55; RK.view.ox=60; RK.view.oy=330; RK.commit()})()""")
        await btn('#tabs button[data-tab=olcum]'); await btn('#tools button[data-tool=kontrol]')
        ck('Ölçüm sekmesinde Gönye aracı', await ev("RK.S.tool")=='kontrol' and 'Gönye' in await ev("document.querySelector('#tools').textContent"))
        await ctap(0,0); await ctap(4,3)
        ck('Salon köşeleri seçildi (çapraz oda içinden)', await ev("RK.S.kt.b.id")=='C' and await ev("RK.S.kt.room")=='Salon', await ev("document.querySelector('#toast').textContent"))
        await ev("RK.laserValue(5.05)")
        ck('lazer ölçüsü hemen kaydedilmedi, kutuya yazıldı (505 cm)', await ev("RK.S.ms.buf")=='505' and not await ev("(RK.P.diags||[]).length"), await ev("RK.S.ms.buf"))
        await btn('#sheet button[data-a=dgok]')
        ck('Kaydet: çapraz 5.050 Salon odasına kaydedildi, "Gönyele: Salon" düğmesi var', await ev("RK.P.diags[0].m")==5.05 and await ev("RK.P.diags[0].room")=='r1' and await ev("!!document.querySelector('#sheet button[data-a=gny][data-v=r1]')"))
        await btn('#sheet button[data-a=gny]')
        ck('önizleme: köşe açıları gösteriliyor, çizim henüz değişmedi', len(await ev("RK.S.calc.ang"))>=4 and await ev("RK.P.nodes.find(n=>n.id==='A').y")==0 and '°' in await ev("document.querySelector('#sheet').textContent"))
        await pg.screenshot(path='p13.png')
        await btn('#sheet button[data-a=cok]')
        P = dict((i,(x,y)) for i,x,y in await ev("RK.P.nodes.map(n=>[n.id,n.x,n.y])"))
        d = lambda a,b: math.dist(P[a],P[b])
        ck('Onayla: çapraz 5.050, ölçülü boylar aynen (2.000, 2.000, 2.900, 4.000, 3.000)', abs(d('A','C')-5.05)<1e-3 and all(abs(d(a,b)-m)<1e-3 for a,b,m in [('A','J1',2),('J2','B',2),('B','C',2.9),('C','D',4),('D','A',3)]), [d('A','C')])
        v1=[P['J2'][0]-P['J1'][0],P['J2'][1]-P['J1'][1]]; v2=[P['J1'][0]-P['A'][0],P['J1'][1]-P['A'][1]]; ja=abs(math.degrees(math.atan2(v1[0]*v2[1]-v1[1]*v2[0], v1[0]*v2[0]+v1[1]*v2[1])))
        ck('  10 cm kırık korundu (boy 0.100, duvara dik ±0.5°)', abs(d('J1','J2')-0.1)<1e-3 and abs(ja-90)<0.5, [d('J1','J2'), ja])
        ck('  komşu oda (Yatak) dış köşeleri yerinde, yalnız ortak duvarı izledi', [round(v,4) for v in P['E']+P['F']]==[4,6,0,6], [P['E'],P['F']])
        ck('JS hatası yok', not errs, errs[:3]); await b.close()
    print('TOPLAM', sum(R), '/', len(R)); sys.exit(0 if all(R) else 1)
asyncio.run(main())
