# YENİ CAD: Düzleştir — offset'teki girinti tek dokunuşla düz geçer, kademe uzun duvarın hizasına çekilir, kapı noktaları korunur
import os, pathlib, sys, asyncio
ROOT = pathlib.Path(__file__).resolve().parent.parent
URL = (ROOT / 'cad.html').as_uri()
OUT = ROOT / 'test' / 'out'; OUT.mkdir(exist_ok=True)
CHROME = os.environ.get('CHROME', '/usr/bin/google-chrome' if os.path.exists('/usr/bin/google-chrome') else None)
from playwright.async_api import async_playwright
R=[]
def ck(n,ok,i=''): R.append(bool(ok)); print(('PASS ' if ok else 'FAIL ')+n, '' if ok else i)
def near(a,b,t=1e-6): return all(abs(x-y)<t for x,y in zip(a,b))
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path=CHROME, args=['--no-sandbox'])
        ctx=await b.new_context(**p.devices['iPhone 13']); pg=await ctx.new_page(); errs=[]
        pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto(URL); await pg.evaluate("localStorage.clear()"); await pg.reload(); await pg.wait_for_timeout(300); ev=pg.evaluate
        async def btn(a):
            r = await ev(f"(()=>{{const e=document.querySelector('button[data-a=\"{a}\"]'); if(!e) return null; const r=e.getBoundingClientRect(); return [r.left+r.width/2, r.top+r.height/2]}})()")
            if not r: return False
            await pg.touchscreen.tap(r[0], r[1]); await pg.wait_for_timeout(60); return True
        async def S(x,y): return await ev(f"CAD.w2s({x},{y})")
        async def wtap(x,y): s=await S(x,y); await pg.touchscreen.tap(s[0],s[1]); await pg.wait_for_timeout(60)
        E=lambda: ev("Object.fromEntries(CAD.D.ents.map(e=>[e.id,e.p]))")
        # kullanıcının resmi gibi: içeri girinti (sol) + sağ altta kademe; kapı üst duvarda
        await ev("""CAD.D={nid:10,ents:[{id:'in',t:'pl',p:[[0,0],[3,0],[3,1],[3.2,1],[3.2,6],[0,6],[0,4],[0.3,4],[0.3,3.5],[0,3.5]],c:true}],ops:[]};
          Object.assign(CAD.view,{s:45,ox:60,oy:400}); CAD.commit()""")
        await btn('fly:edit'); await btn('t:offset'); await wtap(1.5,0); await wtap(1.5,-1)
        out=[k for k in (await E()) if k!='in'][0]
        ck('offset dışarı: girinti ve kademe dışta da var (10 köşe)', len((await E())[out])==10)
        await ev(f"(()=>{{const e=CAD.D.ents.find(x=>x.id==='{out}'); e.p.splice(4,0,[3.4,4.5]); }})()")
        await ev(f"CAD.D.ops.push({{id:'o1',t:'door',a:[1,6],b:[2,6],hinge:0,sw:-1}}); CAD.D.ents[0].p.splice(5,0,[2,6],[1,6]); CAD.commit()")
        await btn('fly:edit'); await btn('t:flat')
        ck('Düzenle penceresinde Düzleştir aracı', await ev("CAD.S.tool")=='flat')
        await wtap(-0.2,3.25)
        P=(await E())[out]
        ck('dış çizgide girintiye dokununca sol duvar düz geçti', not any(abs(q[0]-0.1)<1e-6 for q in P) and len(P)==7, P)
        await wtap(0.3,3.75)
        P=(await E())['in']
        ck('iç çizgide de girinti silindi', not any(abs(q[0]-0.3)<1e-6 for q in P), P)
        await wtap(3.1,1)
        P=(await E())['in']
        ck('kademe: uzun duvar (sağ) esas, alt duvar uzadı', any(near(q,(3.2,0)) for q in P) and not any(near(q,(3,0)) for q in P), P)
        ck('  kapı noktaları duruyor', any(near(q,(2,6)) for q in P) and any(near(q,(1,6)) for q in P) and await ev("CAD.D.ops.length")==1)
        ck('  alan kapalı ve tek', await ev("CAD.D.ents.find(e=>e.id==='in').c") and await ev("faces(CAD.D.ents).length")==2)
        n=len(P); await wtap(1.5,0)
        ck('düz duvara dokununca bir şey yapmaz', len((await E())['in'])==n)
        await btn('undo')
        ck('geri al çalışıyor', any(near(q,(3,0)) for q in (await E())['in']))
        # offset'te dar girinti: genişlik < 2×offset → girinti dışarıda hiç oluşmaz (kendini kesen çizgi yok)
        await ev("""CAD.D={nid:10,ents:[{id:'n',t:'pl',p:[[0,0],[3,0],[3,6],[0,6],[0,4],[0.15,4],[0.15,3.7],[0,3.7]],c:true}],ops:[]}; CAD.S.sel.clear(); CAD.commit()""")
        await btn('fly:edit'); await btn('t:offset'); await wtap(1.5,0); await wtap(1.5,-1)
        o=[v for k,v in (await E()).items() if k!='n'][0]
        ck('dar girinti (30 cm) + 20 cm offset: dışta girinti yok, düz', len(o)==4, o)
        # 10 cm offset'te girinti dışta kalır; yan kenarına, ağzına, dibine dokununca tamamen silinir
        for q in [(-0.1,3.85),(0.0,3.85),(0.05,3.85)]:
            await ev("""CAD.D={nid:10,ents:[{id:'n',t:'pl',p:[[0,0],[3,0],[3,6],[0,6],[0,4],[0.15,4],[0.15,3.7],[0,3.7]],c:true}],ops:[]}; CAD.S.sel.clear(); CAD.S.offD=0.1; CAD.commit()""")
            await btn('fly:edit'); await btn('t:offset'); await wtap(1.5,0); await wtap(1.5,-1)
            await btn('fly:edit'); await btn('t:flat'); await wtap(*q)
            o=[v for k,v in (await E()).items() if k!='n'][0]
            ck(f'  offset girintisi {q} dokunuşuyla tamamen silindi', len(o)==4, o)
        await wtap(-0.1,1.5)
        ck('girintisiz uzun duvara dokununca şekil bozulmadı', len([v for k,v in (await E()).items() if k!='n'][0])==4)
        await pg.screenshot(path=str(OUT/'c7.png'))
        ck('JS hatası yok', not errs, errs[:3]); await b.close()
    print('TOPLAM', sum(R), '/', len(R)); sys.exit(0 if all(R) else 1)
asyncio.run(main())
