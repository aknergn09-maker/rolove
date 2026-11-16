# Kapı/pencere boşluğunda çizgi çizilmez; kapı daralınca çizgi kendiliğinden uzar. Oda duvara bağlanınca beyaz çizgi üstüne çizgi eklenmez; eski projelerdeki bu çift çizgiler açılışta silinir
import os, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
URL = (ROOT / os.environ.get('PAGE', 'index.html')).as_uri()
OUT = ROOT / 'test' / 'out'; OUT.mkdir(exist_ok=True); os.chdir(OUT)
CHROME = os.environ.get('CHROME', '/usr/bin/google-chrome' if os.path.exists('/usr/bin/google-chrome') else None)
import asyncio, sys
from playwright.async_api import async_playwright
R=[]
def ck(n,ok,i=''): R.append(bool(ok)); print(('PASS ' if ok else 'FAIL ')+n, i if not ok else '')
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path=CHROME, args=['--no-sandbox'])
        ctx=await b.new_context(**p.devices['iPhone 13']); pg=await ctx.new_page(); errs=[]
        pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto(URL); await pg.evaluate("localStorage.clear()"); await pg.reload(); await pg.wait_for_timeout(300); ev=pg.evaluate
        await ev("""(()=>{const P=RK.P; P.nodes=[];P.lines=[];P.walls=[];P.rooms=[];P.openings=[]; const C=[[0,0],[4,0],[4,3],[0,3]]; const ids=C.map(([x,y],i)=>{const id='a'+i; P.nodes.push({id,x,y}); return id}); for(let i=0;i<4;i++) P.lines.push({id:'A'+i,a:ids[i],b:ids[(i+1)%4],kind:'sketch'}); P.walls.push({id:'WA',nodes:ids,closed:true,t:0.2,side:1}); P.rooms.push({id:'rA',name:'A',ax:2,ay:1.5}); RK.commit(); if(RK.wallGeom(P.walls[0]).Q.some(q=>q[1]>0.1&&q[1]<2.9&&q[0]>0.1&&q[0]<3.9)) P.walls[0].side=-1; RK.addOpening('kapi','a0','a1',1.5,0.9); RK.view.s=70; RK.view.ox=45; RK.view.oy=330; RK.commit();})()""")
        PX = """((x,y)=>{const cv=document.querySelector('#cv'); const r=window.devicePixelRatio||1; const q=RK.w2s(x,y); const d=cv.getContext('2d').getImageData(Math.round(q[0]*r),Math.round(q[1]*r),1,1).data; return d[0]>200&&d[1]>130&&d[1]<200&&d[2]<90})"""
        ck('kapısız yerde çizgi var (turuncu)', await ev(PX + "(0.7,0)"))
        ck('kapı boşluğunda çizgi çizilmiyor', not await ev(PX + "(1.95,0)") and not await ev(PX + "(2.3,0)"))
        ck('  oda alanı aynı (oda kapıdan açılmadı)', await ev("+RK.rA(RK.P.rooms[0]).toFixed(3)")==12, await ev("RK.rA(RK.P.rooms[0])"))
        await ev("RK.setTool('sec'); RK.S.sel={open:RK.P.openings[0].id}; RK.S.kbuf='40'; RK.commit()")
        r = await ev("(()=>{const e=document.querySelector('#sheet button[data-a=opw]'); if(!e) return null; const r=e.getBoundingClientRect(); return [r.left+r.width/2, r.top+r.height/2]})()")
        if r: await pg.touchscreen.tap(r[0], r[1]); await pg.wait_for_timeout(150)
        ck('kapı 0.90 → 0.40 daralınca çizgi kendiliğinden uzadı (x=2.2 artık çizgi)', await ev(PX + "(2.2,0)") and not await ev(PX + "(1.7,0)"))
        await pg.screenshot(path='t23.png')
        # oda duvarın beyaz çizgisinde kapanınca o çizginin üstüne çizgi eklenmez
        await ev("""(()=>{const P=RK.P; P.openings=[]; RK.commit(); RK.view.s=70; RK.view.ox=-234; RK.view.oy=295; RK.commit();})()""")
        side = await ev("RK.wallGeom(RK.P.walls[0]).Q.some(q=>q[0]>4.1)")
        fx = 4.2 if side else 4.0
        async def btn(sel):
            r = await ev(f"(()=>{{const e=document.querySelector('{sel}'); if(!e||e.disabled) return null; const r=e.getBoundingClientRect(); return [r.left+r.width/2, r.top+r.height/2]}})()")
            if not r: return False
            await pg.touchscreen.tap(r[0], r[1]); await pg.wait_for_timeout(80); return True
        async def ctap(x,y):
            r = await ev("(()=>{const r=document.querySelector('#cv').getBoundingClientRect(); return [r.left,r.top]})()"); q = await ev(f"RK.w2s({x},{y})"); await pg.touchscreen.tap(r[0]+q[0], r[1]+q[1]); await pg.wait_for_timeout(200)
        if await ev("!!document.querySelector('#tabs')"): await btn('#tabs button[data-tab=cizim]')
        await btn('#cats button[data-cat=ciz]'); await btn('#tools button[data-tool=cizgi]')
        for x,y in [(fx,0.5),(fx+2,0.5),(fx+2,2.5),(fx,2.5)]: await ctap(x,y)
        a = await ev("RK.P.rooms.map(r=>[r.name, r._f? +RK.rA(r).toFixed(3):null])"); n = await ev("RK.P.lines.filter(l=>{const A=RK.P.nodes.find(q=>q.id===l.a), B=RK.P.nodes.find(q=>q.id===l.b); return Math.abs(A.x-%s)<1e-3 && Math.abs(B.x-%s)<1e-3}).length" % (fx, fx))
        ck('beyaz çizgide kapanan oda: oda oluştu (2×2=4), beyaz çizginin üstüne çizgi eklenmedi', len(a)==2 and a[1][1]==4 and n==0, [a, n])
        # eski proje: beyaz çizgiyle üst üste yüz çizgisi açılışta silinir
        await ev("""(()=>{const P=RK.P; P.nodes.push({id:'z0',x:%s,y:0.5},{id:'z1',x:%s,y:2.5}); P.lines.push({id:'ZF',a:'z0',b:'z1',kind:'sketch',face:'WA'}); RK.commit(); })()""" % (fx, fx))
        await ev("RK.undo(); RK.redo()")
        ck('eski çift çizgi (beyaz çizgiyle üst üste) açılışta/geri almada silindi, oda aynı', not await ev("RK.P.lines.some(l=>l.id==='ZF')") and (await ev("RK.P.rooms.map(r=>r._f? +RK.rA(r).toFixed(3):null)"))[1]==4, await ev("RK.P.lines.some(l=>l.id==='ZF')"))
        ck('JS hatası yok', not errs, errs[:3]); await b.close()
    print('TOPLAM', sum(R), '/', len(R)); sys.exit(0 if all(R) else 1)
asyncio.run(main())
