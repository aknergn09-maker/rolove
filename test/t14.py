import os, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
URL = (ROOT / os.environ.get('PAGE', 'index.html')).as_uri()
OUT = ROOT / 'test' / 'out'; OUT.mkdir(exist_ok=True); os.chdir(OUT)
CHROME = os.environ.get('CHROME', '/usr/bin/google-chrome' if os.path.exists('/usr/bin/google-chrome') else None)
import asyncio, sys
from playwright.async_api import async_playwright
R=[]
def ck(n,ok,i=''): R.append(bool(ok)); print(('PASS ' if ok else 'FAIL ')+n, i if not ok else '')
AREAS = "Object.fromEntries(RK.P.rooms.map(r=>[r.name, r._f? +r._f.net.toFixed(3):null]))"
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path=CHROME, args=['--no-sandbox'])
        ctx=await b.new_context(**p.devices['iPhone 13']); pg=await ctx.new_page(); errs=[]
        pg.on('pageerror', lambda e: errs.append(e.stack[:300]))
        await pg.goto(URL); await pg.evaluate("localStorage.clear()"); await pg.reload(); await pg.wait_for_timeout(300); ev=pg.evaluate
        async def btn(sel):
            r = await ev(f"(()=>{{const e=document.querySelector('{sel}'); if(!e||e.disabled) return null; const r=e.getBoundingClientRect(); return [r.left+r.width/2, r.top+r.height/2]}})()")
            if not r: return False
            await pg.touchscreen.tap(r[0], r[1]); await pg.wait_for_timeout(70); return True
        async def org(): return await ev("(()=>{const r=document.querySelector('#cv').getBoundingClientRect(); return [r.left,r.top]})()")
        async def ctap(x,y): r=await org(); await pg.touchscreen.tap(r[0]+x, r[1]+y); await pg.wait_for_timeout(80)
        async def typ(v):
            if not await ev("!!document.querySelector('#sheet button[data-k=C]')"): await btn('#sheet button[data-a=np]')
            await btn('#sheet button[data-k="C"]')
            for ch in str(v): await btn(f'#sheet button[data-k="{ch}"]')
            await ev("RK.S.np=false; RK.commit()")
        async def W(x,y): return await ev(f"RK.w2s({x},{y})")
        async def stroke(wpts):
            r = await org(); cdp = await ctx.new_cdp_session(pg); sp = [await ev(f"RK.w2s({x},{y})") for x,y in wpts]
            tp = lambda x,y: [{'x':r[0]+x,'y':r[1]+y}]
            await cdp.send('Input.dispatchTouchEvent', {'type':'touchStart','touchPoints':tp(*sp[0])})
            for (x0,y0),(x1,y1) in zip(sp,sp[1:]):
                n=max(2,int(((x1-x0)**2+(y1-y0)**2)**.5/5))
                for k in range(1,n+1): await cdp.send('Input.dispatchTouchEvent', {'type':'touchMove','touchPoints':tp(x0+(x1-x0)*k/n, y0+(y1-y0)*k/n)})
            await cdp.send('Input.dispatchTouchEvent', {'type':'touchEnd','touchPoints':[]}); await pg.wait_for_timeout(120)
        RA = "Object.fromEntries(RK.P.rooms.map(r=>[r.name, RK.rA(r)==null?null:+RK.rA(r).toFixed(3)]))"
        await ev("""(()=>{const P=RK.P; const C=[[0,0],[6,0],[6,5],[0,5]]; const ids=C.map(([x,y],i)=>{const id='a'+i; P.nodes.push({id,x,y}); return id}); for(let i=0;i<4;i++) P.lines.push({id:'A'+i,a:ids[i],b:ids[(i+1)%4],kind:'typed'}); P.rooms.push({id:'rA',name:'A',ax:3,ay:2.5}); RK.commit(); RK.view.s=48; RK.view.ox=20; RK.view.oy=330; RK.commit();})()""")
        await btn('#cats button[data-cat=ekle]'); await btn('#tools button[data-tool=eleman]')
        ck('Ekle sekmesinde Eleman ve Merdiven var', await ev("!!document.querySelector('#tools button[data-tool=merdiven]')"))
        # 1) kolon (ada)
        q = await W(1,1); await ctap(*q); await typ(40); await btn('#sheet button[data-a=ar][data-v="0"]'); await typ(40); await btn('#sheet button[data-a=ar][data-v="1"]'); await typ(40); await btn('#sheet button[data-a=ar][data-v="2"]'); await btn('#sheet button[data-a=close]')
        a = await ev(RA); ck('kolon (oda içinde ada): alanı 0.16 yazar, A 30 (düşülmez)', a.get('Kolon')==0.16 and a['A']==30, a)
        # 2) şömine duvara bitişik
        await btn('#sheet button[data-a=eln][data-v="Şömine"]'); q = await W(0,3); await ctap(*q); await typ(60); await btn('#sheet button[data-a=ar][data-v="0"]'); await typ(100); await btn('#sheet button[data-a=ar][data-v="1"]'); q = await W(0,4); await ctap(*q)
        a = await ev(RA); ck('şömine (duvara bitişik): 0.6, A yine 30', a.get('Şömine')==0.6 and a['A']==30 and await ev("RK.S.chain")==None, a)
        # 3) merdiven çerçevesi (duvara bitişik)
        await btn('#tools button[data-tool=merdiven]'); q = await W(6,1); await ctap(*q); await typ(100); await btn('#sheet button[data-a=ar][data-v="2"]'); await typ(300); await btn('#sheet button[data-a=ar][data-v="1"]'); q = await W(6,4); await ctap(*q)
        a = await ev(RA); ck('merdiven 1×3: "Merdiven 3.00 m²", A 30-3=27 (düşülür)', a.get('Merdiven')==3 and a['A']==27, a)
        # 4) basamak: karşılıklı iki kenar + 4 rıh
        await btn('#sheet button[data-a=mkm][data-v=bas]'); q = await W(5,2.5); await ctap(*q); q = await W(6,2.5); await ctap(*q)
        ck('  iki kenar seçildi', await ev("RK.S.mk.l1 && RK.S.mk.l2 && RK.S.mk.l1!==RK.S.mk.l2"))
        await typ(4); await btn('#sheet button[data-a=stp]')
        st = await ev("RK.P.lines.filter(l=>l.step).map(l=>[RK.P.nodes.find(n=>n.id===l.a).y, RK.P.nodes.find(n=>n.id===l.b).y].map(v=>+v.toFixed(3)))")
        a = await ev(RA); ck('4 rıh: başlangıç+2+bitiş, kenarlar zaten var → 2 yeni çizgi (y=2, y=3); alanlar değişmez', sorted(x[0] for x in st)==[2,3] and a['Merdiven']==3 and a['A']==27, [st, a])
        # 4b) uzun ve kısa kenar: kısa esas, dik çıkar
        await ev("(()=>{const P=RK.P; [['k1',7.2,1],['k2',7.2,4],['u1',8.2,-0.5],['u2',8.2,6]].forEach(([id,x,y])=>P.nodes.push({id,x,y})); P.lines.push({id:'KS',a:'k1',b:'k2',kind:'sketch'},{id:'UZ',a:'u1',b:'u2',kind:'sketch'}); RK.view.s=48; RK.view.ox=-80; RK.commit();})()")
        await btn('#sheet button[data-a=mkr]'); q = await W(8.2,3.2); await ctap(*q); q = await W(7.2,2.5); await ctap(*q); await typ(4); await btn('#sheet button[data-a=stp]')
        st2 = await ev("RK.P.lines.filter(l=>l.step).map(l=>[l.a,l.b].map(id=>{const n=RK.P.nodes.find(x=>x.id===id); return [+n.x.toFixed(3),+n.y.toFixed(3)]})).filter(s=>s[0][0]>7 || s[1][0]>7)")
        ck('kısa kenar (3 m) esas: 4 çizgi y=1,2,3,4, kısa kenardan dik, uzun kenarda biter', sorted(round(x[0][1],3) for x in st2)==[1,2,3,4] and all(abs(x[0][1]-x[1][1])<1e-6 for x in st2), st2)
        await ev("RK.view.s=48; RK.view.ox=20; RK.commit()")
        # 5) yön
        await btn('#sheet button[data-a=mkm][data-v=yon]'); q = await W(5.5,1.2); await ctap(*q); q = await W(5.5,3.8); await ctap(*q); await btn('#sheet button[data-a=yonok]')
        ck('çıkış yönü oku çizildi', await ev("RK.P.arrows.length")==1)
        # 6) var olan alanı eleman yap
        await btn('#cats button[data-cat=ciz]'); await btn('#tools button[data-tool=cizgi]'); q = await W(2,3); await ctap(*q); await typ(100); await btn('#sheet button[data-a=ar][data-v="0"]'); await typ(100); await btn('#sheet button[data-a=ar][data-v="1"]'); await typ(100); await btn('#sheet button[data-a=ar][data-v="2"]'); await btn('#sheet button[data-a=close]')
        await btn('#cats button[data-cat=ekle]'); await btn('#tools button[data-tool=eleman]'); await btn('#sheet button[data-a=eln][data-v="Baca"]'); await btn('#sheet button[data-a=mkm][data-v=alan]'); q = await W(2.5,3.5); await ctap(*q)
        a = await ev(RA); ck('çizgiyle çizilen kare "Alana dokun" ile Baca oldu (1.00), A 27', a.get('Baca')==1 and a['A']==27, a)
        await btn('#fFit'); await pg.screenshot(path='o8.png')
        # 7) sil: ok ve merdiven işareti
        await btn('#cats button[data-cat=duz]'); await btn('#tools button[data-tool=sil]'); q = await W(5.5,2.5); await ctap(q[0], q[1]+0.5)
        ck('Sil: yön oku silinir', await ev("RK.P.arrows.length")==0)
        await ev("RK.undo()"); ck('geri al: ok geri gelir', await ev("RK.P.arrows.length")==1)
        ck('JS hatası yok', not errs, errs[:3]); await b.close()
    print('TOPLAM', sum(R), '/', len(R)); sys.exit(0 if all(R) else 1)
asyncio.run(main())
