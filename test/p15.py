# ÖNİZLEME: Kırıkları düzelt — eğik çizilmiş 5 cm kırık yanındaki duvara dik olur, iki yan duvar paralel kalır, ölçüler korunur; sınır ayarlanabilir
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
        # alt duvarda 5 cm kırık, parmakla eğik çizilmiş (30°); duvar hafif eğik (gönyesiz)
        await ev("""(()=>{const P=RK.P; P.nodes=[];P.lines=[];P.walls=[];P.rooms=[];P.diags=[];
          const C={A:[0,0],J1:[2,0.03],J2:[2.05,0.06],B:[4,0.11],C:[4,3],D:[0,3]}; Object.entries(C).forEach(([id,[x,y]])=>P.nodes.push({id,x,y}));
          [['A','J1',2],['J1','J2',0.05],['J2','B',2],['B','C',2.9],['C','D',4],['D','A',3]].forEach(([a,b,m],i)=>P.lines.push({id:'L'+i,a,b,kind:'laser',m}));
          P.rooms.push({id:'r1',name:'Salon',ax:2,ay:1.5}); RK.commit(); RK.view.s=60; RK.view.ox=40; RK.view.oy=330; RK.commit()})()""")
        await btn('#tabs button[data-tab=olcum]'); await btn('#tools button[data-tool=kontrol]')
        ck('Gönye aracında kırık sınırı ayarı (30 cm seçili) ve "Kırıkları düzelt: Salon (1)" düğmesi', await ev("!!document.querySelector('#sheet button[data-a=jogl][data-v=\"30\"].on')") and 'Kırıkları düzelt: Salon (1)' in await ev("document.querySelector('#sheet').textContent"))
        await btn('#sheet button[data-a=jogl][data-v="10"]')
        ck('  sınır 10 cm yapılabiliyor (kayıtlı)', await ev("RK.SET.jog")==10 and await ev("JSON.parse(localStorage.getItem('rk4p_settings')).jog")==10)
        await btn('#sheet button[data-a=jogf][data-v=r1]'); await btn('#sheet button[data-a=cok]')
        P = dict((i,(x,y)) for i,x,y in await ev("RK.P.nodes.map(n=>[n.id,n.x,n.y])"))
        sub=lambda a,b:(P[b][0]-P[a][0],P[b][1]-P[a][1]); ang=lambda u,v: math.degrees(math.atan2(u[0]*v[1]-u[1]*v[0], u[0]*v[0]+u[1]*v[1]))
        a1 = ang(sub('A','J1'), sub('J1','J2')); a2 = ang(sub('J1','J2'), sub('J2','B'))
        ck('kırık yanındaki duvara dik (90°, −90°)', abs(abs(a1)-90)<0.2 and abs(abs(a2)-90)<0.2, [a1,a2])
        ck('  iki yan duvar paralel', abs(ang(sub('A','J1'), sub('J2','B')))<0.2, ang(sub('A','J1'), sub('J2','B')))
        d=lambda a,b: math.dist(P[a],P[b])
        ck('  ölçüler korundu (±3 mm)', all(abs(d(a,b)-m)<3e-3 for a,b,m in [('A','J1',2),('J1','J2',0.05),('J2','B',2),('B','C',2.9),('C','D',4),('D','A',3)]), [round(d(a,b),4) for a,b in [('A','J1'),('J1','J2'),('J2','B'),('B','C'),('C','D'),('D','A')]])
        ck('  artık düzeltilecek kırık yok', 'Kırıkları düzelt' not in await ev("document.querySelector('#sheet').textContent"))
        ck('JS hatası yok', not errs, errs[:3]); await b.close()
    print('TOPLAM', sum(R), '/', len(R)); sys.exit(0 if all(R) else 1)
asyncio.run(main())
