import os, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
URL = (ROOT / 'index.html').as_uri()
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
        async def drag(x0,y0,x1,y1,steps=8):
            bx=await box(); await pg.mouse.move(bx[0]+x0,bx[1]+y0); await pg.mouse.down(); await pg.mouse.move(bx[0]+x1,bx[1]+y1,steps=steps); await pg.mouse.up(); await pg.wait_for_timeout(40)
        O=[0,0]
        async def W(x,y): return await ev(f"RK.w2s({x+O[0]},{y+O[1]})")
        async def typ(v):
            if not await ev("!!document.querySelector('#sheet button[data-k=C]')"): await pg.click('#sheet button[data-a=np]')
            await pg.click('#sheet button[data-k="C"]')
            for ch in str(v): await pg.click(f'#sheet button[data-k="{ch}"]')
        async def arrow(k): await pg.click(f'#sheet button[data-a=ar][data-v="{k}"]')
        async def tool(cat, t): await pg.click(f'#cats button[data-cat={cat}]'); await pg.click(f'#tools button[data-tool={t}]'); await pg.wait_for_timeout(40)
        rooms = "RK.P.rooms.map(r=>[r.name, r._f? +r._f.net.toFixed(3):null])"
        ck('açılış: çizgi aracı, siyah tema', await ev("RK.S.tool")=='cizgi' and await ev("getComputedStyle(document.body).backgroundColor")=='rgb(11, 13, 16)')
        # 1. oda: 4x3 yazarak
        await tap(80, 250); await typ(400); await arrow(0); await typ(300); await arrow(1); await typ(400); await arrow(2)
        await pg.click('#sheet button[data-a=close]')
        o = await ev("[RK.P.nodes[0].x, RK.P.nodes[0].y]"); O[0]=o[0]; O[1]=o[1]
        r1 = await ev(rooms); ck('1 tuşla oda çizildi, kapanınca oda oluştu (12 m²)', r1==[['Oda 1',12.0]], r1)
        ck('  yazılan çizgiler "yazılan" türünde', await ev("RK.P.lines.filter(l=>l.kind==='typed').length")>=3)
        await pg.click('#fFit'); await pg.wait_for_timeout(50)
        # 2. oda: sağ alt köşeden başla (4,0), 300 →, 300 ↑, (4,3) köşesine dokun
        q = await W(4,0); await tap(q[0]+3, q[1]-3); await typ(300); await arrow(0); await typ(300); await arrow(1)
        q = await W(4,3); await tap(q[0]+2, q[1]+2)
        r2 = await ev(rooms); ck('2 bitişik oda: köşeden köşeye çizince oda oluştu, ortak duvar', r2==[['Oda 1',12.0],['Oda 2',9.0]] and await ev("RK.P.lines.length")==7, [r2, await ev("RK.P.lines.length")])
        await pg.click('#fFit'); await pg.wait_for_timeout(50)
        # 3. oda: alt duvarın ortasından (2,0) aşağı 200, sağa 200, (4,0)'a dokun
        q = await W(2,0); await tap(q[0], q[1]); n_after_start = await ev("RK.P.nodes.length")
        await typ(200); await arrow(3); await typ(200); await arrow(0); q = await W(4,0); await tap(q[0]+2,q[1]-2)
        r3 = await ev(rooms); ck('3 duvar ortasından başlayan oda (T bağlantı)', len(r3)==3 and r3[2][1]==4.0 and r3[0][1]==12.0, r3)
        await pg.click('#fFit'); await pg.wait_for_timeout(50); await pg.screenshot(path='s1.png')
        # 4. seç: üst duvar uzunluğu 4.50 (A sabit)
        await tool('duz','sec'); q1 = await W(0,3); q2 = await W(4,3); await tap((q1[0]+q2[0])/2+20, q1[1])
        sel = await ev("RK.S.sel"); ck('4 çizgiye dokununca seçilir', sel and sel.get('lines') and len(sel['lines'])==1, sel)
        await pg.click('#sheet button[data-a=len]'); await typ(450)
        lid = sel['lines'][0]; ends = await ev(f"(()=>{{const l=RK.P.lines.find(x=>x.id==='{lid}'); const a=RK.P.nodes.find(n=>n.id===l.a); return [a.x,a.y]}})()")
        await pg.click('#sheet button[data-a=fix][data-v=A]'); await pg.click('#sheet button[data-a=lenok]')
        L = await ev(f"(()=>{{const l=RK.P.lines.find(x=>x.id==='{lid}'); const a=RK.P.nodes.find(n=>n.id===l.a), b=RK.P.nodes.find(n=>n.id===l.b); return [Math.hypot(a.x-b.x,a.y-b.y), l.kind, a.x, a.y]}})()")
        ck('  uzunluk 4.50, A ucu yerinde', abs(L[0]-4.5)<1e-9 and L[1]=='typed' and abs(L[2]-ends[0])<1e-9, L)
        await ev("RK.undo()"); ck('  geri al', abs(await ev(f"(()=>{{const l=RK.P.lines.find(x=>x.id==='{lid}'); const a=RK.P.nodes.find(n=>n.id===l.a), b=RK.P.nodes.find(n=>n.id===l.b); return Math.hypot(a.x-b.x,a.y-b.y)}})()")-4.0)<1e-9)
        # 5. kırık: sol duvarın ortasına kırık koy (çizgi aracında orta noktaya dokunup bitir), sonra Sil ile kırığı kaldır
        await tool('ciz','cizgi'); q = await W(0,1.5); await tap(q[0], q[1]); await pg.click('#sheet button[data-a=end]')
        nl0 = await ev("RK.P.lines.length")
        await tool('duz','sil'); await tap(q[0], q[1])
        nl1 = await ev("RK.P.lines.length"); ck('5 kırık (orta nokta) Sil ile kaldırılır, çizgiler birleşir', nl1==nl0-1 and await ev(rooms)==r3, [nl0,nl1])
        # 6. köşeyi köşeye oturt: serbest iki çizgi
        await tool('ciz','cizgi'); await tap(60,120); await tap(150,120); await pg.click('#sheet button[data-a=end]')
        await tap(60,170); await tap(160,175); await pg.click('#sheet button[data-a=end]')
        nn0 = await ev("RK.P.nodes.length")
        await tool('duz','sec'); await tap(105,174)   # alt çizgiyi seç
        await drag(160,175,151,122)   # sağ uç grip -> üst çizginin sağ ucu
        nn1 = await ev("RK.P.nodes.length"); ck('6 grip sürükle: köşe diğer köşeye oturur (birleşir)', nn1==nn0-1, [nn0, nn1])
        # 7. kutu seçim + sil
        await ev("RK.S.sel=null; RK.commit()"); await drag(40,100,190,195)
        ks = await ev("RK.S.sel && RK.S.sel.lines.length"); await pg.click('#sheet button[data-a=del]')
        ck('7 kutu seçim (2 çizgi) ve sil', ks==2 and await ev("RK.P.lines.length")==nl1, [ks, await ev("RK.P.lines.length")])
        # 8. taşı: 3. odanın alt duvarını 50 cm aşağı (yazarak)
        q1 = await W(2,-2); q2 = await W(4,-2); await tap((q1[0]+q2[0])/2+15, q1[1])
        await pg.click('#sheet button[data-a=mv]'); await tap(q1[0], q1[1]); await typ(50)
        bx=await box(); await pg.mouse.move(bx[0]+q1[0], bx[1]+q1[1]); await pg.mouse.down(); await pg.mouse.move(bx[0]+q1[0], bx[1]+q1[1]+60, steps=5); await pg.mouse.up(); await pg.wait_for_timeout(50)
        r8 = await ev(rooms); ck('8 taşı (baz + yazılan mesafe): oda 3 alanı 4→5 m²', r8[2][1]==5.0, r8)
        # 9. dikdörtgen (yazılı ölçü) ve ada (kolon) çıkarma
        await tool('ciz','dikdortgen'); await pg.click('#sheet button[data-a=fld][data-v=w]'); await typ(50); await pg.click('#sheet button[data-a=fld][data-v=h]'); await typ(50)
        q = await W(1,1); await tap(q[0], q[1]); q = await W(2,2); await tap(q[0], q[1])
        r9 = await ev(rooms); ck('9 oda içine 50x50 kolon: oda alanından düşer, kolon oda sayılmaz', r9[0][1]==11.75 and len(r9)==3, r9)
        # 10. oda aracı: elle oda, ad
        await tool('ekle','oda'); q = await W(1.5,1.5); await tap(q[0], q[1])
        ck('10 oda aracı: var olan odaya dokununca seçilir', await ev("RK.S.sel && RK.S.sel.room")==await ev("RK.P.rooms[0].id"))
        # 11. orto X-Y ve kılavuz
        await pg.click('#fOrtX'); ck('11 X-Y kilidi', await ev("RK.SET.ortho")=='xy')
        q = await W(4,3); g = await ev(f"RK.candidate({q[0]+3},{q[1]-60},{{}})"); ck('  hiza kılavuzu', g['type'] in ('guide',) and abs(g['X']-q[0])<0.5, g)
        await pg.click('#fOrtO'); ck('  obje kilidi', await ev("RK.SET.ortho")=='obj')
        # 12. kayıt ve yeniden yükleme
        await pg.reload(); await pg.wait_for_timeout(250); ck('12 yeniden açınca proje geri gelir', await ev(rooms)==r9, await ev(rooms))
        await pg.click('#fFit'); await pg.wait_for_timeout(50); await pg.screenshot(path='s2.png')
        await tool('duz','sec'); q1 = await W(0,3); q2 = await W(4,3); await tap((q1[0]+q2[0])/2+20, q1[1]); await pg.screenshot(path='s3.png')
        ck('JS hatası yok', not errs, errs[:4]); await b.close()
    print('TOPLAM', sum(R), '/', len(R)); sys.exit(0 if all(R) else 1)
asyncio.run(main())
