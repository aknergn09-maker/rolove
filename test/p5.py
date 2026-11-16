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
        RA = "Object.fromEntries(RK.P.rooms.map(r=>[r.name, RK.rA(r)==null?null:+RK.rA(r).toFixed(2)]))"
        async def typ(v):
            if not await ev("!!document.querySelector('#sheet button[data-k=C]')"): await btn('#sheet button[data-a=np]')
            await btn('#sheet button[data-k="C"]')
            for ch in str(v): await btn(f'#sheet button[data-k="{ch}"]')
            await ev("RK.S.np=false; RK.commit()")
        await ev("RK.view.s=40; RK.view.ox=40; RK.view.oy=380; RK.commit()")
        # 1) duvar kalınlıklı daire (3 nokta, r=1, merkez 2,4)
        await btn('#tools button[data-tool=daire]'); await btn('#sheet button[data-a=drm][data-v="3n"]'); await btn('#sheet button[data-a=drw]')
        for x,y in [(1,4),(3,4),(2,5)]: q = await W(x,y); await ctap(*q)
        w = await ev("RK.P.walls.map(w=>{const g=RK.wallGeom(w); const d=g.Q.map(q=>Math.hypot(q[0]-2,q[1]-4)); return [w.nodes.length, +Math.min(...d).toFixed(3), +Math.max(...d).toFixed(3)]})")
        a = await ev(RA)
        ck('daireye duvar kalınlığı: dış yüz r≈1.20 (dışa 20 cm), oda alanı π', len(w)==1 and w[0][1]>1.19 and w[0][2]<1.21 and any(v and abs(v-3.14)<0.03 for v in a.values()), [w, a])
        # 2) duvar zincirinde yay ile kapatma: (5,2)→(9,2)→(9,5)→(5,5), sonra yay (4,3.5) üstünden başlangıca
        await ev("RK.view.s=40; RK.view.ox=-120; RK.view.oy=380; RK.commit()")
        await btn('#tools button[data-tool=duvar]'); q = await W(5,2); await ctap(*q)
        await typ(400); await btn('#sheet button[data-a=ar][data-v="0"]'); await typ(300); await btn('#sheet button[data-a=ar][data-v="1"]'); await typ(400); await btn('#sheet button[data-a=ar][data-v="2"]')
        await btn('#sheet button[data-a=charc]'); ck('zincirde ◠ Yay düğmesi', await ev("!!RK.S.chArc"))
        q = await W(3.5,3.5); await ctap(*q); q = await W(5,2); await ctap(*q)
        await pg.screenshot(path='p5a.png');
        a2 = await ev(RA); exp = 12 + 3.14159*1.5*1.5/2
        ck('yayla kapandı: oda alanı 4×3 + yarım daire (r 1.5) ≈ %.2f' % exp, any(v and abs(v-exp)<0.05 for v in a2.values()) and await ev("RK.S.chain")==None, a2)
        wb = await ev("RK.P.walls.length"); ck('  duvar bandı yayı da izliyor (ikinci duvar, çok köşeli)', wb==2 and await ev("RK.P.walls[1].nodes.length")>10, [wb, await ev("RK.P.walls.map(w=>w.nodes.length)")])
        # 3) Düzenle → Çıkıntı → Yay: 4×3 odanın sağ duvarına dışa yay (y 1..2, tepe x=4.5)
        await ev("""(()=>{const P=RK.P; P.nodes=[];P.lines=[];P.rooms=[];P.walls=[];P.arcs=[]; const C=[[0,0],[4,0],[4,3],[0,3]]; const ids=C.map(([x,y],i)=>{const id='a'+i; P.nodes.push({id,x,y}); return id}); for(let i=0;i<4;i++) P.lines.push({id:'A'+i,a:ids[i],b:ids[(i+1)%4],kind:'sketch'}); P.walls.push({id:'WA',nodes:ids,closed:true,t:0.2,side:1}); P.rooms.push({id:'rA',name:'A',ax:2,ay:1.5}); RK.commit(); RK.view.s=60; RK.view.ox=40; RK.view.oy=330; RK.commit();})()""")
        a0 = (await ev(RA))['A']
        await btn('#cats button[data-cat=duz]'); await btn('#tools button[data-tool=cikinti]'); await btn('#sheet button[data-a=cikm][data-v=yay]')
        for x,y in [(4,1),(4.5,1.5),(4,2)]: q = await W(x,y); await ctap(q[0]-1 if x==4 else q[0], q[1])
        a3 = await ev(RA); exp3 = a0 + 3.14159*0.5*0.5/2
        ck('Çıkıntı-Yay: düz duvar kesildi, oda yarım daire kadar büyüdü (≈%.2f)' % exp3, abs(a3['A']-exp3)<0.02, [a0, a3])
        wq = await ev("RK.wallGeom(RK.P.walls[0]).quads.length"); ck('  duvar bandı yayı izliyor', wq>8, wq)
        # içe yay
        for x,y in [(1,0),(2,0.6),(3,0)]: q = await W(x,y); await ctap(q[0], q[1]-1 if y==0 else q[1])
        a4 = await ev(RA); r4 = (1+0.36)/(2*0.6); import math
        seg = r4*r4*math.acos((r4-0.6)/r4) - (r4-0.6)*math.sqrt(2*r4*0.6-0.36)
        ck('Çıkıntı-Yay içe: alan yay parçası kadar azaldı', abs(a4['A']-(a3['A']-seg))<0.02, [a3['A'], a4['A'], seg])
        # 4) Ekle → Eleman → Daire → Kolon (merkez + r 25)
        await btn('#cats button[data-cat=ekle]'); await btn('#tools button[data-tool=eleman]'); await btn('#sheet button[data-a=els][data-v=daire]')
        ck('Eleman: şekil Çizgi/Daire seçimi', await ev("RK.S.elShape")=='daire' and await ev("!!document.querySelector('#sheet button[data-a=drm]')"))
        await btn('#sheet button[data-a=eln][data-v="Kolon"]'); await btn('#sheet button[data-a=drm][data-v=mr]')
        q = await W(1.5,1.5); await ctap(*q); await btn('#sheet button[data-a=np]'); [await btn(f'#sheet button[data-k="{c}"]') for c in '25']; await btn('#sheet button[data-a=drok]')
        a5 = await ev(RA); kol = [v for k,v in a5.items() if k=='Kolon']
        ck('daire kolon: alanı π·0.25² ≈ 0.20, oda alanı düşmedi', kol and abs(kol[0]-0.2)<0.01 and abs(a5['A']-a4['A'])<1e-6, a5)
        await btn('#sheet button[data-a=els][data-v=ciz]'); ck('  Çizgi seçilince çizgi ile çizer', await ev("RK.S.elShape")=='ciz' and await ev("RK.S.mk.mode")=='ciz')
        await btn('#fFit'); await pg.screenshot(path='p5.png')
        ck('JS hatası yok', not errs, errs[:3]); await b.close()
    print('TOPLAM', sum(R), '/', len(R)); sys.exit(0 if all(R) else 1)
asyncio.run(main())
