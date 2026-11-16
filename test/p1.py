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
        await pg.goto(URL); await pg.evaluate("localStorage.clear(); localStorage.setItem('rk3_projects', JSON.stringify({'Ana proje':{v:8,name:'Ana proje',nodes:[],lines:[],rooms:[],walls:[],roomSeq:0}})); localStorage.setItem('rk3_current','Ana proje')"); await pg.reload(); await pg.wait_for_timeout(300); ev=pg.evaluate
        ck('önizleme ana projeleri kopyaladı, kendi alanında çalışıyor', await ev("RK.P.name")=='Ana proje' and await ev("!!localStorage.getItem('rk3p_projects')"))
        main0 = await ev("localStorage.getItem('rk3_projects')")
        async def btn(sel):
            r = await ev(f"(()=>{{const e=document.querySelector('{sel}'); if(!e||e.disabled) return null; const r=e.getBoundingClientRect(); return [r.left+r.width/2, r.top+r.height/2]}})()")
            if not r: return False
            await pg.touchscreen.tap(r[0], r[1]); await pg.wait_for_timeout(80); return True
        async def ctap(x,y):
            r = await ev("(()=>{const r=document.querySelector('#cv').getBoundingClientRect(); return [r.left,r.top]})()"); await pg.touchscreen.tap(r[0]+x, r[1]+y); await pg.wait_for_timeout(90)
        async def W(x,y): return await ev(f"RK.w2s({x},{y})")
        await ev("""(()=>{const P=RK.P; const C=[[0,0],[4,0],[4,3],[0,3]]; const ids=C.map(([x,y],i)=>{const id='a'+i; P.nodes.push({id,x,y}); return id}); for(let i=0;i<4;i++) P.lines.push({id:'A'+i,a:ids[i],b:ids[(i+1)%4],kind:'sketch'}); P.walls.push({id:'WA',nodes:ids,closed:true,t:0.2,side:1}); P.rooms.push({id:'rA',name:'Salon',ax:2,ay:1.5}); RK.commit();
          const n0=RK.nodeAt([1,0]), n1=RK.nodeAt([1.9,0]); RK.addOpening('kapi', n0, n1, 0, 0.9); const w0=RK.nodeAt([4,1]), w1=RK.nodeAt([4,2.2]); RK.addOpening('pencere', w0, w1, 0, 1.2); RK.commit(); RK.view.s=60; RK.view.ox=60; RK.view.oy=330; RK.commit();})()""")
        tabs = await ev("[...document.querySelectorAll('#tabs button')].map(b=>b.textContent)")
        ck('üstte 3 sekme: Çizim / Ölçüm / Kroki', tabs==['Çizim','Ölçüm','Kroki'], tabs)
        ck('  Çizim sekmesinde Çiz/Düzenle/Ekle', await ev("[...document.querySelectorAll('#cats button')].map(b=>b.textContent)")==['Çiz','Düzenle','Ekle'])
        await btn('#tabs button[data-tab=olcum]'); ck('Ölçüm sekmesi: lazer/elle ölçü aracı', await ev("RK.S.tool")=='olc')
        await btn('#tabs button[data-tab=kroki]'); ck('Kroki sekmesi: nokta adı aracı', await ev("RK.S.tool")=='nokta')
        # başlangıç adı: ilk dokunuşta sorar
        pg.once('dialog', lambda d: asyncio.ensure_future(d.accept('101')))
        q = await W(0,0); await ctap(*q); await pg.wait_for_timeout(150)
        ck('ilk dokunuşta başlangıç sorulur, köşe 101 oldu', await ev("RK.P.pts.map(t=>t.name)")==['101'], await ev("RK.P.pts"))
        for x,y in [(4,0),(4,3)]: q = await W(x,y); await ctap(*q)
        # duvar dış köşesi (4.2, 3.2)
        q = await W(4.2,3.2); await ctap(*q)
        pts = await ev("RK.P.pts.map(t=>[t.name, ...RK.ptPos(t).map(v=>+v.toFixed(3))])")
        ck('sırayla 102, 103 ve dış köşe 104 (4.20, 3.20)', [t[0] for t in pts]==['101','102','103','104'] and pts[3][1:]==[4.2,3.2], pts)
        ck('  sıradaki ad 105 gösteriliyor', '105' in await ev("document.querySelector('#sheet').textContent"))
        # kapı kenarı da köşe
        q = await W(1,0); await ctap(*q); ck('kapı kenarı noktası 105', await ev("RK.P.pts.length")==5)
        # seç → adını değiştir, buradan devam
        q = await W(4,0); await ctap(*q); ck('var olan noktaya dokununca seçilir', await ev("RK.S.ptSel")!=None)
        pg.once('dialog', lambda d: asyncio.ensure_future(d.accept('K-7')))
        await btn('#sheet button[data-a=ptr]'); await pg.wait_for_timeout(100)
        ck('  ad değişti: K-7', 'K-7' in await ev("RK.P.pts.map(t=>t.name)"))
        q = await W(4,0); await ctap(*q); await btn('#sheet button[data-a=ptc]'); ck('  buradan devam: sıradaki K-8', await ev("RK.P.ptNext")=='K-8')
        ck('ad artırma: P009→P010, A→A1, 99→100', await ev("[RK.nextName('P009'),RK.nextName('A'),RK.nextName('99')]")==['P010','A1','100'])
        # ölçekleme noktaları taşır: Ölçüm'de alt duvarı 4.4 yap
        await btn('#tabs button[data-tab=olcum]'); q = await W(3,0); await ctap(q[0], q[1]-2)
        await btn('#sheet button[data-a=np]'); [await btn(f'#sheet button[data-k="{c}"]') for c in '220']; await btn('#sheet button[data-a=msok]')
        pts2 = await ev("RK.P.pts.map(t=>[t.name, ...RK.ptPos(t).map(v=>+v.toFixed(3))])")
        ck('ölçekleme sonrası noktalar köşeleriyle gitti, dış köşe kalınlığı korudu', abs([r for r in pts2 if r[0]=='104'][0][1]-[r for r in pts2 if r[0]=='103'][0][1]-0.2)<1e-6, pts2)
        await btn('#tabs button[data-tab=kroki]'); await pg.screenshot(path='p1.png')
        ov = await ev("(()=>{let n=0; for(let i=0;i<RK.LB.length;i++) for(let j=i+1;j<RK.LB.length;j++) if(RK.polyHit(RK.LB[i],RK.LB[j])) n++; return [RK.LB.length, n]})()")
        ck('Kroki: yakın nokta adları (103/104) ve ölçüler üst üste binmiyor', ov[1]==0, ov)
        # DXF
        await btn('#tools button[data-tool=disa]'); ck('DXF / Dışa aracı', await ev("!!document.querySelector('#sheet button[data-a=dxf]')"))
        dx = await ev("RK.makeDXF()")
        open('test.dxf','w',newline='').write(dx)
        import ezdxf
        doc = ezdxf.readfile('test.dxf'); msp = doc.modelspace()
        lay = {}
        for e in msp: lay.setdefault(e.dxf.layer, []).append(e.dxftype())
        ck('DXF okunuyor (ezdxf), katmanlar var', all(k in lay for k in ['CIZGI_ESKIZ','CIZGI_LAZER','DUVAR','KAPI','PENCERE','ODA','NOKTA','OLCU']), sorted(lay))
        ck('  kapıda yay (ARC), pencerede 3+2 çizgi', 'ARC' in lay['KAPI'] and lay['PENCERE'].count('LINE')==5, [lay.get('KAPI'), lay.get('PENCERE')])
        tx = [e.dxf.text for e in msp if e.dxftype()=='TEXT' and e.dxf.layer=='NOKTA']
        ck('  nokta adları ve noktalar', sorted(tx)==sorted(await ev("RK.P.pts.map(t=>t.name)")) and lay['NOKTA'].count('POINT')==len(tx), tx)
        rm = [e.dxf.text for e in msp if e.dxftype()=='TEXT' and e.dxf.layer=='ODA']
        ck('  oda adı ve alanı (Türkçe karakter kodlu)', any('Salon' in t for t in rm) and any('m2' in t for t in rm), rm)
        ln = [e for e in msp if e.dxftype()=='LINE' and e.dxf.layer=='CIZGI_LAZER']; L = [round(((e.dxf.end[0]-e.dxf.start[0])**2+(e.dxf.end[1]-e.dxf.start[1])**2)**.5,3) for e in ln]
        ck('  lazer ölçülü parça metre cinsinden (2.200)', abs(sum(L)-2.2)<1e-3, L)
        await btn('#sheet button[data-a=dxf]'); await pg.wait_for_timeout(300)
        ck('DXF düğmesi dosyayı üretir', await ev("!!window._lastDXF && window._lastDXF.includes('EOF')"))
        ck('ana uygulamanın kayıtları değişmedi', await ev("localStorage.getItem('rk3_projects')")==main0)
        ck('JS hatası yok', not errs, errs[:3]); await b.close()
    print('TOPLAM', sum(R), '/', len(R)); sys.exit(0 if all(R) else 1)
asyncio.run(main())
