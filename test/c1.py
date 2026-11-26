# YENİ CAD (cad.html): çizim, yakalama, hızlı uzunluk, offset, tutamaklar, trim/extend/fillet/join/explode, ileri-geri, iki parmak zoom — gerçek dokunma
import os, pathlib, sys, asyncio, math, json
ROOT = pathlib.Path(__file__).resolve().parent.parent
URL = (ROOT / 'cad.html').as_uri()
OUT = ROOT / 'test' / 'out'; OUT.mkdir(exist_ok=True); os.chdir(OUT)
CHROME = os.environ.get('CHROME', '/usr/bin/google-chrome' if os.path.exists('/usr/bin/google-chrome') else None)
from playwright.async_api import async_playwright
R=[]
def ck(n,ok,i=''): R.append(bool(ok)); print(('PASS ' if ok else 'FAIL ')+n, '' if ok else i)
def near(a,b,t=1e-3): return all(abs(x-y)<t for x,y in zip(a,b))
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path=CHROME, args=['--no-sandbox'])
        ctx=await b.new_context(**p.devices['iPhone 13']); pg=await ctx.new_page(); errs=[]
        pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto(URL); await pg.evaluate("localStorage.clear()"); await pg.reload(); await pg.wait_for_timeout(300); ev=pg.evaluate
        cdp=await ctx.new_cdp_session(pg)
        async def btn(a):
            r = await ev(f"(()=>{{const e=document.querySelector('button[data-a=\"{a}\"]'); if(!e) return null; const r=e.getBoundingClientRect(); return [r.left+r.width/2, r.top+r.height/2]}})()")
            if not r: return False
            await pg.touchscreen.tap(r[0], r[1]); await pg.wait_for_timeout(60); return True
        async def tool(grp, t):
            await btn('fly:'+grp); await btn('t:'+t)
        async def S(x,y): return await ev(f"CAD.w2s({x},{y})")
        async def wtap(x,y): s=await S(x,y); await pg.touchscreen.tap(s[0],s[1]); await pg.wait_for_timeout(60)
        async def drag(p0,p1,n=12):
            a=await S(*p0); c=await S(*p1); tp=lambda x,y:[{'x':x,'y':y}]
            await cdp.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':tp(*a)})
            for k in range(1,n+1): await cdp.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':tp(a[0]+(c[0]-a[0])*k/n,a[1]+(c[1]-a[1])*k/n)})
            await cdp.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]}); await pg.wait_for_timeout(80)
        ents=lambda: ev("JSON.parse(JSON.stringify(CAD.D.ents))")
        await ev("Object.assign(CAD.view,{s:25,ox:200,oy:330}); CAD.render()")
        ck('sağ sütunda sadece simge, yazı yok', (await ev("[...document.querySelectorAll('#col button')].map(b=>b.innerText).join('').trim()"))=='')
        # 1) Pline dikdörtgen, ilk noktaya dokununca kapanır
        await tool('draw','pl')
        ck('Çiz penceresi seçince kapandı', await ev("getComputedStyle(document.querySelector('#fly')).display")=='none')
        for pt in [(0,0),(4,0),(4,3),(0,3),(0,0)]: await wtap(*pt)
        E=await ents()
        ck('pline kapalı 4 köşe', len(E)==1 and E[0]['t']=='pl' and E[0]['c'] and len(E[0]['p'])==4, E)
        ck('  kapalı alan dolgusu (1 alan)', await ev("faces(CAD.D.ents).length")==1)
        # 2) Line + hızlı uzunluk: 100+50 ↑, sonra 50 →
        await tool('draw','line'); await wtap(-2,4)
        ck('ilk noktada 4 ok', await ev("['up','down','left','right'].every(k=>document.querySelector('button[data-a=\"qa:'+k+'\"]'))"))
        await btn('q:100'); await btn('q:50')
        ck('  toplam 150', (await ev("document.querySelector('#qp .sum').textContent"))=='150')
        await btn('qa:up')
        ck('  yukarı giderken sadece sağ/sol', await ev("!!document.querySelector('button[data-a=\"qa:left\"]') && !document.querySelector('button[data-a=\"qa:up\"]')"))
        await btn('q:50'); await btn('qa:right'); await btn('qok')
        E=await ents(); L=[e for e in E if e['t']=='line']
        ck('  çizgiler (-2,4)-(-2,5.5)-(-1.5,5.5)', len(L)==2 and near(L[0]['a'],(-2,4)) and near(L[0]['b'],(-2,5.5)) and near(L[1]['b'],(-1.5,5.5)), L)
        # 3) Offset 15 cm içeri
        await tool('edit','offset'); await btn('k:1'); await btn('k:5')
        await wtap(2,0); await wtap(2,1)
        E=await ents(); O=E[-1]
        ck('offset 15 cm içeri kapalı pline', O['t']=='pl' and O['c'] and near(O['p'][0],(0.15,0.15)) and near(O['p'][2],(3.85,2.85)), O)
        # 4) Seç + orta tutamak: sağ kenarı 1 m dışarı
        await btn('sec'); await wtap(4,2.2)
        ck('seçim', await ev("CAD.S.sel.size")==1)
        await drag((4,1.5),(5,1.5))
        P=(await ents())[0]['p']
        ck('orta tutamak: sağ kenar x=5, alt/üst uzadı', near(P[1],(5,0)) and near(P[2],(5,3)) and near(P[0],(0,0)), P)
        # 5) köşe tutamağı
        await drag((0,3),(-1,3))
        P=(await ents())[0]['p']
        ck('köşe tutamağı ortho ile (0,3)→(-1,3)', near(P[3],(-1,3),1e-6), P)
        # 6) Trim
        await ev("const D=CAD.D; D.ents.push({id:'tL',t:'line',a:[2,-1],b:[2,4.5]},{id:'xL',t:'line',a:[-3,1],b:[-2,1]},{id:'f1',t:'line',a:[-7,-2],b:[-5,-2]},{id:'f2',t:'line',a:[-4,-1],b:[-4,1]}); CAD.commit()")
        await tool('edit','trim'); await wtap(2,-0.5)
        T=[e for e in await ents() if e['id'].startswith('e') and e['t']=='line' and abs(e['a'][0]-2)<1e-6]
        ck('trim: alt taşan parça silindi', T and near(T[0]['a'],(2,0)) and near(T[0]['b'],(2,4.5)), T)
        # 7) Extend
        await tool('edit','extend'); await wtap(-2.1,1)
        X=[e for e in await ents() if e['t']=='line' and abs(e['a'][1]-1)<1e-9 and abs(e['b'][1]-1)<1e-9 and e['a'][0]<-2.5]
        ck('extend: sınıra kadar uzadı', X and abs(X[0]['b'][0]-(-1/3))<1e-6, X)
        # 8) Fillet
        await tool('edit','fillet'); await wtap(-6,-2); await wtap(-4,0)
        F={e['id']:e for e in await ents()}
        ck('fillet: köşe (-4,-2)', near(F['f1']['b'],(-4,-2)) and near(F['f2']['a'],(-4,-2)), [F.get('f1'),F.get('f2')])
        # 9) Join (zincire dokun) + Explode
        await tool('edit','join'); await wtap(-2,4.7)
        J=[e for e in await ents() if e['t']=='pl' and not e['c']]
        ck('join: iki çizgi tek pline', len(J)==1 and len(J[0]['p'])==3, J)
        await tool('edit','explode'); await wtap(-2,4.7)
        ck('explode: tekrar 2 çizgi', len([e for e in await ents() if e['t']=='line' and e['a'][1]>=3.9 and e['a'][0]<=-1.4])==2)
        # 10) Circle + Arc
        await tool('draw','cir'); await wtap(-4,6); await wtap(-3,6)
        await tool('draw','arc'); await wtap(-7,4); await wtap(-6,5); await wtap(-5,4)
        E=await ents(); C=[e for e in E if e['t']=='cir']; A=[e for e in E if e['t']=='arc']
        ck('daire r=1 ve 3 noktalı yay', C and abs(C[0]['r']-1)<1e-6 and A and abs(A[0]['r']-1)<1e-6, [C,A])
        # 11) Yakalama: orta nokta + ortho
        await ev("Object.assign(CAD.view,{s:100,ox:-100,oy:450}); CAD.render()"); await tool('draw','line'); await wtap(1.8,1.2); 
        await ev("CAD.S.snaps.end=1")
        n0=len(await ents()); await wtap(2.5,0.05); await btn('qok')
        E=await ents(); Ln=E[-1]
        ck('orta noktaya yakaladı (2.5,0)', len(E)==n0+1 and near(Ln['b'],(2.5,0)), Ln)
        # 11b) Kopyala / Taşı (sürükle: temel nokta → hedef)
        await ev("Object.assign(CAD.view,{s:25,ox:200,oy:330}); CAD.render()")
        await tool('edit','copy'); nC=len(await ents()); await wtap(-4,5.2)
        ck('kopyala: dokununca seçildi', await ev("CAD.S.sel.size")==1)
        await drag((-4,6),(1,6))
        E=await ents(); C=[e for e in E if e['t']=='cir']
        ck('  daire kopyalandı (1,6)', len(E)==nC+1 and any(near(c['c'],(1,6)) for c in C) and any(near(c['c'],(-4,6)) for c in C), C)
        await tool('edit','move'); await wtap(3,7); await wtap(1,5.05); await drag((1,6),(1,7.5))
        C=[e for e in await ents() if e['t']=='cir']
        ck('  taşı: daire (1,7.5)', any(near(c['c'],(1,7.5)) for c in C) and not any(near(c['c'],(1,6)) for c in C), C)
        await btn('sec')
        # 12) İleri-geri
        n=len(await ents()); e0=await ents(); await btn('undo'); e1=await ents(); await btn('redo'); e2=await ents()
        ck('geri al / ileri al (taşımayı geri aldı, ileri aldı)', e1!=e0 and e2==e0 and any(near(c['c'],(1,6)) for c in e1 if c['t']=='cir'), [len(e0),len(e1)])
        # 13) Kayıt (yeniden yükle)
        await pg.reload(); await pg.wait_for_timeout(300)
        ck('kayıt korunur', len(await ents())==n)
        # 14) İki parmak zoom
        s0=await ev("CAD.view.s"); await ev("Object.assign(CAD.view,{s:40,ox:110,oy:520}); CAD.render()")
        await cdp.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':150,'y':400,'id':1},{'x':200,'y':400,'id':2}]})
        for k in range(1,8): await cdp.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{'x':150-k*10,'y':400,'id':1},{'x':200+k*10,'y':400,'id':2}]})
        await cdp.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]}); await pg.wait_for_timeout(80)
        ck('iki parmak zoom', await ev("CAD.view.s")>60 and len(await ents())==n)
        await btn('fit'); await pg.wait_for_timeout(100); await pg.screenshot(path='c1.png')
        ck('JS hatası yok', not errs, errs[:3]); await b.close()
    print('TOPLAM', sum(R), '/', len(R)); sys.exit(0 if all(R) else 1)
asyncio.run(main())
