# Ölçü komşu odaların şeklini bozarsa sorar: "Bağlantı korunsun" (komşular uyar) / "Komşular yerinde kalsın" (sadece ölçülen oda); bütün halinde ölçeklenmede sormaz
import os, pathlib, sys, asyncio
ROOT = pathlib.Path(__file__).resolve().parent.parent
URL = (ROOT / os.environ.get('PAGE', 'index.html')).as_uri()
OUT = ROOT / 'test' / 'out'; OUT.mkdir(exist_ok=True); os.chdir(OUT)
CHROME = os.environ.get('CHROME', '/usr/bin/google-chrome' if os.path.exists('/usr/bin/google-chrome') else None)
from playwright.async_api import async_playwright
R=[]
def ck(n,ok,i=''): R.append(bool(ok)); print(('PASS ' if ok else 'FAIL ')+n, i if not ok else '')
SET = """((meas)=>{const P=RK.P; P.nodes=[];P.lines=[];P.walls=[];P.rooms=[];P.fills=[]; RK.S.measAsk=null; const N=(id,x,y)=>P.nodes.push({id,x,y}); const L=(id,a,b,m)=>P.lines.push(m&&meas?{id,a,b,kind:'laser',m}:{id,a,b,kind:'sketch'});
  N('p0',0,0);N('p1',4,0);N('p2',7,0);N('p3',7,3);N('p4',4,3);N('p5',0,3);N('p6',7,5);N('p7',4,5);
  L('a0','p0','p1',4);L('a1','p1','p4',3);L('a2','p4','p5',4);L('a3','p5','p0',3);L('b0','p1','p2',3);L('b1','p2','p3');L('b2','p3','p4');L('c1','p3','p6');L('c2','p6','p7');L('c3','p7','p4');
  P.rooms.push({id:'rA',name:'A',ax:2,ay:1.5},{id:'rB',name:'B',ax:5.5,ay:1.5},{id:'rC',name:'C',ax:5.5,ay:4}); RK.commit(); RK.view.s=40; RK.view.ox=40; RK.view.oy=300; RK.commit()})"""
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
        LEN = "Object.fromEntries(RK.P.lines.map(l=>[l.id, +RK.lineLen(l).toFixed(3)]))"
        if await ev("!!document.querySelector('#tabs')"): await btn('#tabs button[data-tab=olcum]')
        else: await btn('#cats button[data-cat=olc]')
        await btn('#tools button[data-tool=olc]')
        # 1) hiç ölçü yok: ilk ölçü her şeyi aynı oranla ölçekler → soru yok
        await ev(SET + "(false)"); await ev("RK.applyMeasure(RK.P.lines.find(l=>l.id==='a0'), 4.4)")
        L = await ev(LEN)
        ck('ilk ölçü: bütün odalar aynı oranla (×1.1) büyüdü, soru sorulmadı', abs(L['b0']-3.3)<1e-3 and abs(L['c1']-2.2)<1e-3 and not await ev("!!RK.S.measAsk"), [L, await ev("RK.S.measAsk")])
        # 2) A ve B'nin altı ölçülü; C'nin üstü çizimden 30 cm kısa → B'nin ortak duvarı yamulur → soru
        await ev(SET + "(true)"); await ev("RK.applyMeasure(RK.P.lines.find(l=>l.id==='c2'), 2.7)")
        ck('C üstü 2.70: komşu B yamulacağı için soru çıktı', await ev("!!RK.S.measAsk") and 'B' in await ev("RK.S.measAsk.names.join(',')") and await ev("!!document.querySelector('#sheet button[data-a=mqD]')"), await ev("RK.S.measAsk"))
        await btn('#sheet button[data-a=mqD]'); L = await ev(LEN)
        ck('  "Komşular yerinde kalsın": A ve B aynen (B üstü 3.000), C üstü ~2.70', L['b2']==3 and L['b0']==3 and L['a0']==4 and abs(L['c2']-2.7)<6e-3, L)
        await btn('#sheet button[data-a=mqK]'); L = await ev(LEN)
        ck('  "Bağlantı korunsun": B\'nin üstü de C\'ye uydu (< 3.000)', L['b2']<2.99 and abs(L['c2']-2.7)<6e-3, L)
        ck('JS hatası yok', not errs, errs[:3]); await b.close()
    print('TOPLAM', sum(R), '/', len(R)); sys.exit(0 if all(R) else 1)
asyncio.run(main())
