import os, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
URL = (ROOT / os.environ.get('PAGE', 'index.html')).as_uri()
OUT = ROOT / 'test' / 'out'; OUT.mkdir(exist_ok=True); os.chdir(OUT)
CHROME = os.environ.get('CHROME', '/usr/bin/google-chrome' if os.path.exists('/usr/bin/google-chrome') else None)
import asyncio, sys, json
from playwright.async_api import async_playwright
R=[]
def ck(n,ok,i=''): R.append(bool(ok)); print(('PASS ' if ok else 'FAIL ')+n, i if not ok else '')
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path=CHROME, args=['--no-sandbox'])
        pg=await b.new_page(viewport={'width':390,'height':800}, device_scale_factor=2, has_touch=True); errs=[]
        pg.on('pageerror', lambda e: errs.append(str(e))); pg.on('console', lambda m: errs.append(m.text) if m.type=='error' else None)
        await pg.goto(URL); await pg.evaluate("localStorage.clear()"); await pg.reload(); await pg.wait_for_timeout(250); ev=pg.evaluate
        async def box(): return await ev("(()=>{const r=document.querySelector('#cv').getBoundingClientRect(); return [r.left,r.top,r.width,r.height]})()")
        async def tap(x,y): bx=await box(); await pg.mouse.click(bx[0]+x,bx[1]+y); await pg.wait_for_timeout(40)
        async def path(pts):
            bx=await box(); await pg.mouse.move(bx[0]+pts[0][0],bx[1]+pts[0][1]); await pg.mouse.down()
            for i in range(1,len(pts)):
                await pg.mouse.move(bx[0]+pts[i][0],bx[1]+pts[i][1],steps=max(2,int(((pts[i][0]-pts[i-1][0])**2+(pts[i][1]-pts[i-1][1])**2)**.5/6)))
            await pg.mouse.up(); await pg.wait_for_timeout(60)
        async def drag(x0,y0,x1,y1): await path([(x0,y0),(x1,y1)])
        async def typ(v):
            if not await ev("!!document.querySelector('#sheet button[data-k=C]')"): await pg.click('#sheet button[data-a=np]')
            await pg.click('#sheet button[data-k="C"]')
            for ch in str(v): await pg.click(f'#sheet button[data-k="{ch}"]')
        async def arrow(k): await pg.click(f'#sheet button[data-a=ar][data-v="{k}"]')
        async def tool(cat, t): await pg.click(f'#cats button[data-cat={cat}]'); await pg.click(f'#tools button[data-tool={t}]'); await pg.wait_for_timeout(40)
        ext = "(()=>{const w=RK.P.walls[RK.P.walls.length-1]; const g=RK.wallGeom(w); const xs=g.Q.map(q=>q[0]), ys=g.Q.map(q=>q[1]); return [+(Math.max(...xs)-Math.min(...xs)).toFixed(3), +(Math.max(...ys)-Math.min(...ys)).toFixed(3), g.quads.length, w.closed]})()"
        rooms = "RK.P.rooms.map(r=>[r.name, r._f? +r._f.net.toFixed(3):null])"
        # 1 duvar aracı: 4x3 kapalı
        await tool('ciz','duvar'); await pg.click('#sheet button[data-a=wt][data-v="0.2"]')
        await tap(80,250); await typ(400); await arrow(0); await typ(300); await arrow(1); await typ(400); await arrow(2); await pg.click('#sheet button[data-a=close]')
        e1 = await ev(ext); ck('1 duvar aracı: kapalı oda, 20 cm kalınlık dışa', e1==[4.4,3.4,4,True] and await ev(rooms)==[['Oda 1',12.0]], [e1, await ev(rooms)])
        await pg.click('#fFit'); await pg.wait_for_timeout(60); await pg.screenshot(path='w1.png')
        # 2 seç → duvar bandına dokun → yön değiştir
        await tool('duz','sec'); o = await ev("[RK.P.nodes[0].x, RK.P.nodes[0].y]")
        q = await ev(f"RK.w2s({o[0]+2},{o[1]-0.1})"); await tap(q[0], q[1])
        ck('2 duvar bandına dokununca duvar seçilir', await ev("RK.S.sel && RK.S.sel.wall")==await ev("RK.P.walls[0].id"), await ev("RK.S.sel"))
        await pg.click('#sheet button[data-a=sside]'); e2 = await ev(ext)
        ck('  ⇄ Yön: kalınlık içe geçer', e2[:2]==[3.6,2.6], e2)
        await pg.click('#sheet button[data-a=sside]'); await pg.click('#sheet button[data-a=swt][data-v="0.3"]'); e3 = await ev(ext)
        ck('  kalınlık 30 cm', e3[:2]==[4.6,3.6], e3)
        # 3 köşe taşınınca duvar izler
        await tool('duz','sec'); n0 = await ev(f"RK.w2s({o[0]},{o[1]})"); await tap(n0[0], n0[1]); await drag(n0[0], n0[1], n0[0]-20, n0[1])
        e4 = await ev(ext); ck('3 köşe taşınınca duvar kendiliğinden uyar', e4[0] > 4.6 and e4[2]==4, e4)
        await ev("RK.undo()")
        # 4 açık duvar
        await ev("(()=>{RK.P={v:8,name:'W'+Math.random(),nodes:[],lines:[],rooms:[],walls:[],roomSeq:0}; RK.commit(); RK.fit();})()")
        await tool('ciz','duvar'); await tap(80, 250); await typ(200); await arrow(0); await typ(150); await arrow(1); await pg.click('#sheet button[data-a=end]')
        e5 = await ev(ext); ck('4 açık duvar (2 parça, uçlar kapalı)', e5[2]==2 and e5[3]==False, e5)
        # 5 serbest: kaba dikdörtgen
        await ev("(()=>{RK.P={v:8,name:'S'+Math.random(),nodes:[],lines:[],rooms:[],walls:[],roomSeq:0}; RK.commit(); RK.view.s=40;})()")
        await tool('ciz','serbest')
        await path([(60,120),(250,124),(254,300),(62,296),(61,126)])
        r5 = await ev("[RK.P.lines.length, RK.P.rooms.length, RK.P.lines.map(l=>{const a=RK.P.nodes.find(n=>n.id===l.a), b=RK.P.nodes.find(n=>n.id===l.b); const h=Math.atan2(b.y-a.y,b.x-a.x)*180/Math.PI; return +(((h%90)+90)%90).toFixed(2)})]")
        ck('5 serbest el: kaba dikdörtgen → 4 düz çizgi, 90° köşe, oda', r5[0]==4 and r5[1]==1 and all(a in (0,90) or abs(a)<1e-6 for a in r5[2]), r5)
        # 6 kısa çıkıntı (25 cm ≈ 10 px) üst üste binmez
        await path([(60,360),(220,360),(220,371),(330,371)])
        r6 = await ev("RK.P.lines.slice(4).map(l=>{const a=RK.P.nodes.find(n=>n.id===l.a), b=RK.P.nodes.find(n=>n.id===l.b); return +Math.hypot(a.x-b.x,a.y-b.y).toFixed(2)})")
        print('   ', await ev("RK.P.lines.slice(4).map(l=>[l.a,l.b].map(id=>{const n=RK.P.nodes.find(q=>q.id===id); return RK.w2s(n.x,n.y).map(v=>+v.toFixed(1))}))"))
        ck('6 uzun çizgide 25 cm kırık tanınır (3 parça, üst üste değil)', len(r6)==3 and 0.2<=r6[1]<=0.35, r6)
        # 7 köşeden köşeye serbest çizgi → bağlanır, yeni oda
        nb = await ev("RK.P.nodes.length"); a = await ev("RK.ns(RK.P.lines[0].a)"); c = await ev("RK.ns(RK.P.lines[0].b)")
        await path([(a[0]+3,a[1]+2),(a[0],a[1]-60),(c[0],c[1]-62),(c[0]-2,c[1]+3)])
        r7 = await ev("[RK.P.nodes.length, RK.P.rooms.length]"); ck('7 serbest çizgi köşelere bağlanır, yeni oda oluşur', r7[0]==nb+2 and r7[1]==2, [nb, r7])
        await pg.click('#fFit'); await pg.wait_for_timeout(60); await pg.screenshot(path='w2.png')
        # 8 titrek el: gürültülü çizim
        import random; random.seed(3)
        def noisy(pts, n=4):
            out=[]
            for (x0,y0),(x1,y1) in zip(pts, pts[1:]):
                L=max(1,int(((x1-x0)**2+(y1-y0)**2)**.5/5))
                for k in range(L): out.append((x0+(x1-x0)*k/L+random.uniform(-n,n)*0.5, y0+(y1-y0)*k/L+random.uniform(-n,n)*0.5))
            out.append(pts[-1]); return out
        await ev("(()=>{RK.P={v:8,name:'N'+Math.random(),nodes:[],lines:[],rooms:[],walls:[],roomSeq:0}; RK.commit(); RK.view.s=40;})()")
        bx=await box(); pts=noisy([(50,120),(300,126),(305,140),(345,141),(342,320),(55,315),(52,124)])
        await pg.mouse.move(bx[0]+pts[0][0],bx[1]+pts[0][1]); await pg.mouse.down()
        for q in pts[1:]: await pg.mouse.move(bx[0]+q[0],bx[1]+q[1])
        await pg.mouse.up(); await pg.wait_for_timeout(80)
        r8 = await ev("[RK.P.lines.length, RK.P.rooms.length, RK.P.lines.map(l=>{const a=RK.P.nodes.find(n=>n.id===l.a), b=RK.P.nodes.find(n=>n.id===l.b); return +Math.hypot(a.x-b.x,a.y-b.y).toFixed(2)})]")
        ck('8 titrek elle çizilen kademeli oda: 6 çizgi, oda, kademe korunur', r8[0]==6 and r8[1]==1 and min(r8[2])>0.25, r8)
        await pg.screenshot(path='w3.png')
        ck('JS hatası yok', not errs, errs[:4]); await b.close()
    print('TOPLAM', sum(R), '/', len(R)); sys.exit(0 if all(R) else 1)
asyncio.run(main())
