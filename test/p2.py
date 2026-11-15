# ÖNİZLEME testi: sekmeler, kroki nokta adları, DXF
import os, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
URL = (ROOT / os.environ.get('PAGE', 'onizleme.html')).as_uri()
OUT = ROOT / 'test' / 'out'; OUT.mkdir(exist_ok=True); os.chdir(OUT)
CHROME = os.environ.get('CHROME', '/usr/bin/google-chrome' if os.path.exists('/usr/bin/google-chrome') else None)
import asyncio, sys, io
from playwright.async_api import async_playwright
R=[]
def ck(n,ok,i=''): R.append(bool(ok)); print(('PASS ' if ok else 'FAIL ')+n, i if not ok else '')
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path=CHROME, args=['--no-sandbox'])
        ctx=await b.new_context(**p.devices['iPhone 13']); pg=await ctx.new_page(); errs=[]; dlg=[]
        pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto(URL); await pg.evaluate("localStorage.clear()"); await pg.reload(); await pg.wait_for_timeout(300); ev=pg.evaluate
        async def btn(sel):
            r = await ev(f"(()=>{{const e=document.querySelector('{sel}'); if(!e||e.disabled) return null; const r=e.getBoundingClientRect(); return [r.left+r.width/2, r.top+r.height/2]}})()")
            if not r: return False
            await pg.touchscreen.tap(r[0], r[1]); await pg.wait_for_timeout(80); return True
        async def ctap(x,y):
            r = await ev("(()=>{const r=document.querySelector('#cv').getBoundingClientRect(); return [r.left,r.top]})()"); await pg.touchscreen.tap(r[0]+x, r[1]+y); await pg.wait_for_timeout(90)
        async def W(x,y): return await ev(f"RK.w2s({x},{y})")
        LEN = "Object.fromEntries(RK.P.lines.map(l=>[l.id, +RK.lineLen(l).toFixed(4)]))"
        # L biçimli oda (köşegen bir yerde dışarı çıkar) + yanında B
        await ev("""(()=>{const P=RK.P; const N=(id,x,y)=>P.nodes.push({id,x,y}); const L=(id,a,b)=>P.lines.push({id,a,b,kind:'sketch'});
          N('a',0,0);N('b',4,0);N('c',4,3);N('d',0,3); L('AB','a','b');L('BC','b','c');L('CD','c','d');L('DA','d','a'); P.rooms.push({id:'r1',name:'A',ax:2,ay:1.5});
          N('e',7,0);N('f',7,3); L('BE','b','e');L('EF','e','f');L('FC','f','c'); P.rooms.push({id:'r2',name:'B',ax:5.5,ay:1.5});
          RK.commit(); const w0=RK.nodeAt([4,1]), w1=RK.nodeAt([4,2]); RK.addOpening('pencere', w0, w1, 0, 1); RK.commit(); RK.view.s=40; RK.view.ox=20; RK.view.oy=300; RK.commit();})()""")
        await btn('#tabs button[data-tab=olcum]'); await btn('#tools button[data-tool=kontrol]')
        ck('Ölçüm sekmesinde Kontrol ve Yükseklik araçları', await ev("RK.S.tool")=='kontrol' and await ev("!!document.querySelector('#tools button[data-tool=yukseklik]')"))
        # geçersiz köşegen: a → e (B'yi ve duvarı keser)
        q = await W(0,0); await ctap(*q); q = await W(7,3); await ctap(*q)
        ck('oda dışından geçen köşegen reddedilir', await ev("RK.S.kt.b")==None and 'geçmiyor' in await ev("document.querySelector('#toast').textContent"))
        # A köşegeni a–c: çizim 5.000, ölç 5.050
        q = await W(0,0); await ctap(*q); q = await W(4,3); await ctap(*q)
        ck('A köşegeni seçildi', await ev("!!RK.S.kt.b"))
        await btn('#sheet button[data-a=np]'); [await btn(f'#sheet button[data-k="{c}"]') for c in ['5','0','5']]; await btn('#sheet button[data-a=dgok]')
        ck('köşegen 5.050 kaydedildi, uyumsuz gösterilir, geometri henüz değişmedi', await ev("RK.P.diags.length")==1 and await ev("RK.P.diags[0].m")==5.05 and (await ev(LEN))['AB']==4 and 'uyumsuz' in await ev("document.querySelector('#sheet').textContent"))
        await btn('#sheet button[data-a=calc]')
        ck('Geometriyi hesapla: önizleme gösterilir, çizim değişmez', await ev("!!RK.S.calc") and (await ev(LEN))['AB']==4 and await ev("!!document.querySelector('#sheet button[data-a=cok]')"))
        await pg.screenshot(path='p2.png')
        await btn('#sheet button[data-a=cx]'); ck('Vazgeç: önizleme kalkar', not await ev("!!RK.S.calc"))
        await btn('#sheet button[data-a=calc]'); await btn('#sheet button[data-a=cok]')
        d = await ev("+Math.hypot(RK.P.nodes.find(n=>n.id==='a').x-RK.P.nodes.find(n=>n.id==='c').x, RK.P.nodes.find(n=>n.id==='a').y-RK.P.nodes.find(n=>n.id==='c').y).toFixed(4)")
        ck('Onayla: köşegen 5.050 oldu', abs(d-5.05)<5e-4, d)
        ck('  dik açılar yaklaşık korundu (eskiz çizgiler yön tutar)', await ev("(()=>{const n=id=>RK.P.nodes.find(x=>x.id===id); return Math.abs(n('a').y-n('b').y)<0.02 && Math.abs(n('b').x-n('c').x)<0.02})()"))
        # Yükseklik
        await btn('#tools button[data-tool=yukseklik]'); q = await W(1.5,1.5); await ctap(*q)
        ck('odaya dokun → taban–tavan', await ev("RK.S.hs.kind")=='room')
        await btn('#sheet button[data-a=np]'); [await btn(f'#sheet button[data-k="{c}"]') for c in ['2','7','5']]; await btn('#sheet button[data-a=hsok]')
        ck('  A yüksekliği 2.75', await ev("RK.P.rooms.find(r=>r.name==='A').h")==2.75)
        g = await ev("(()=>{const o=RK.P.openings[0]; const g=RK.opGeom(o); const m=g.mid; return RK.w2s(m[0]+g.nB[0]*0.1, m[1]+g.nB[1]*0.1)})()"); await ctap(*g)
        ck('pencereye dokun → denizlik alanı', await ev("RK.S.hs.kind")=='op' and await ev("RK.S.hs.f")=='sill', await ev("RK.S.hs"))
        await btn('#sheet button[data-a=np]'); await btn('#sheet button[data-k="0"]'); await btn('#sheet button[data-a=hsok]')
        ck('  denizlik 0 kabul edilir, yükseklik alanına geçer', await ev("RK.P.openings[0].sill")==0 and await ev("RK.S.hs.f")=='oh')
        await btn('#sheet button[data-a=np]'); [await btn(f'#sheet button[data-k="{c}"]') for c in ['2','1','0']]; await btn('#sheet button[data-a=hsok]')
        ck('  pencere yüksekliği 2.10 → üstten tavana 65 cm', '65 cm' in await ev("document.querySelector('#sheet').textContent"), await ev("document.querySelector('#sheet').textContent"))
        # lazerle yükseklik (sahte değer)
        await ev("RK.laserValue(2.8)"); ck('lazer ölçüsü seçili alana yazılır (yükseklik 2.80)', await ev("RK.P.openings[0].oh")==2.8)
        # rapor
        await btn('#tools button[data-tool=kontrol]'); await btn('#sheet button[data-a=rep]')
        rp = await ev("window._lastRep || ''")
        ck('rapor: oda, alan, köşegen, pencere, üstten tavana', all(k in rp for k in ['A · alan', 'köşegen 5.050', 'Pencere 10', 'yükseklik 2.750', 'üstten tavana -5 cm']), rp)
        ck('  rapor penceresi açık', not await ev("document.querySelector('#modal').classList.contains('hid')"))
        ck('JS hatası yok', not errs, errs[:3]); await b.close()
    print('TOPLAM', sum(R), '/', len(R)); sys.exit(0 if all(R) else 1)
asyncio.run(main())
