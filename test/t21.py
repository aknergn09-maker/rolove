# Çıkıntı: duvarın diğer yüzüne dokunarak başla/bitir (yakın zoomda yüz çizgiden uzak)
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
        async def btn(sel):
            r = await ev(f"(()=>{{const e=document.querySelector('{sel}'); if(!e||e.disabled) return null; const r=e.getBoundingClientRect(); return [r.left+r.width/2, r.top+r.height/2]}})()")
            if not r: return False
            await pg.touchscreen.tap(r[0], r[1]); await pg.wait_for_timeout(80); return True
        async def ctap(x,y):
            r = await ev("(()=>{const r=document.querySelector('#cv').getBoundingClientRect(); return [r.left,r.top]})()"); await pg.touchscreen.tap(r[0]+x, r[1]+y); await pg.wait_for_timeout(120)
        async def W(x,y): return await ev(f"RK.w2s({x},{y})")
        async def typ(v):
            if not await ev("!!document.querySelector('#sheet button[data-k=C]')"): await btn('#sheet button[data-a=np]')
            await btn('#sheet button[data-k="C"]')
            for ch in str(v): await btn(f'#sheet button[data-k="{ch}"]')
            await ev("RK.S.np=false; RK.commit()")
        SETUP = """((side)=>{const P=RK.P; P.nodes=[];P.lines=[];P.walls=[];P.rooms=[];P.openings=[]; const C=[[0,0],[4,0],[4,3],[0,3]]; const ids=C.map(([x,y],i)=>{const id='a'+i; P.nodes.push({id,x,y}); return id}); for(let i=0;i<4;i++) P.lines.push({id:'A'+i,a:ids[i],b:ids[(i+1)%4],kind:'sketch'}); P.walls.push({id:'WA',nodes:ids,closed:true,t:0.2,side}); P.rooms.push({id:'rA',name:'A',ax:2,ay:1.5}); RK.commit(); RK.view.s=150; RK.view.ox=20; RK.view.oy=240; RK.commit(); return RK.wallGeom(P.walls[0]).Q.some(q=>q[1]<-0.1)})"""
        AR = "+RK.rA(RK.P.rooms[0]).toFixed(3)"
        if await ev("!!document.querySelector('#tabs')"): await btn('#tabs button[data-tab=cizim]')
        await btn('#cats button[data-cat=duz]'); await btn('#tools button[data-tool=cikinti]'); await btn('#sheet button[data-a=cikm][data-v=el]')
        for side in (1, -1):
            out = await ev(SETUP + f"({side})"); fy = -0.2 if out else 0.2; a0 = await ev(AR)
            # dış bantta dışa çıkıntı (aşağı), iç bantta girinti (yukarı = içeri)
            q = await W(0.8, fy); await ctap(*q)
            st = await ev("[!!RK.S.chain, RK.S.chain && RK.P.nodes.find(n=>n.id===RK.S.chain.first) && [RK.P.nodes.find(n=>n.id===RK.S.chain.first).x, RK.P.nodes.find(n=>n.id===RK.S.chain.first).y]]")
            ck(f'[{"dış" if out else "iç"} bant] beyaz çizgiye (diğer yüz) dokununca çıkıntı oradan başladı (0.8, {fy})', st[0] and st[1] and abs(st[1][0]-0.8)<0.02 and abs(st[1][1]-fy)<1e-6, [st, await ev("document.querySelector('#toast').textContent")])
            await typ(50); await btn('#sheet button[data-a=ar][data-v="%s"]' % ('3' if out else '1')); await typ(100); await btn('#sheet button[data-a=ar][data-v="0"]')
            q = await W(1.8, fy); await ctap(*q)
            if await ev("!!document.querySelector('#sheet button[data-a=askN]')"): await btn('#sheet button[data-a=askN]')
            a1 = await ev(AR); exp = a0 + (0.3 if out else -0.5)  # çizilen yol yeni yüz: dışta referans 0.6×0.5 büyür; içte oda tam çizilen 1.0×0.5 kadar küçülür
            ck(f'  diğer yüze dokunarak bitti: alan {a0} → {exp:.3f}', abs(a1-exp)<1e-3, [a1, await ev("document.querySelector('#toast').textContent")])
            yy = fy + (-0.5 if out else 0.5)
            ck(f'  yeni yüz tam çizilen yerde: köşeler (0.8,{yy:.1f}) ve (1.8,{yy:.1f})', await ev(f"RK.P.walls.length===1 && RK.P.walls[0].closed && [[0.8,{yy}],[1.8,{yy}]].every(p=>RK.wallGeom(RK.P.walls[0]).Q.some(q=>Math.hypot(q[0]-p[0],q[1]-p[1])<1e-6))"), await ev("RK.wallGeom(RK.P.walls[0]).Q.map(q=>q.map(v=>+v.toFixed(2)))"))
            await pg.screenshot(path=f't21_{"dis" if out else "ic"}.png')
        # normal zoom (yüz çizgiye 12 px), sadece dokunarak: beyaz → dışarı → beyaz; ve karışık: turuncu → dışarı → beyaz
        for nm, start, sl, zs in (('beyaz→beyaz', -0.2, 0, 60), ('turuncu→beyaz', 0.0, 0, 60), ('özensiz dokunuş', -0.2, 0.1, 60), ('zoom 66', -0.2, 0, 66), ('zoom 90', -0.2, 0, 90)):
            await ev(SETUP + "(1)"); await ev(f"RK.view.s={zs}; RK.view.ox=60; RK.view.oy=250; RK.commit()"); await btn('#sheet button[data-a=cikm][data-v=el]')
            for x,y in [(0.8+sl*0.5,start-sl),(0.8+sl,-0.8-sl*0.6),(1.8-sl*0.7,-0.8+sl*0.5),(1.8+sl*0.6,-0.2-sl*0.9)]: q = await W(x,y); await ctap(*q); await pg.wait_for_timeout(150)
            if await ev("!!document.querySelector('#sheet button[data-a=askN]')"): await btn('#sheet button[data-a=askN]')
            a1 = await ev(AR); ok = (abs(a1-12.36)<1e-3 or (sl and 12.2<a1<12.45 and 'diğer yüz' in await ev("document.querySelector('#toast').textContent"))) and (sl or await ev("[[0.8,-0.8],[1.8,-0.8]].every(p=>RK.wallGeom(RK.P.walls[0]).Q.some(q=>Math.hypot(q[0]-p[0],q[1]-p[1])<1e-6))"))
            ck(f'normal zoom, dokunarak {nm}: çıkıntı oldu, yeni beyaz çizgi çizilen yerde, alan 12.36', ok, [a1, await ev("document.querySelector('#toast').textContent"), not await ev("!!RK.S.chain")])
            await pg.screenshot(path=f't21_{nm[0]}.png')
        # köşe kolonu (kullanıcının ekranı): iç bant, iki duvarın beyaz çizgileri köşede birleşiyor; bir yüzden başla, köşeyi dolaşıp diğer yüzde bitir
        for nm, pts, exp in (('sağ alt köşe', [(3.39,0.2),(3.39,0.38),(3.8,0.38)], 9.36-0.41*0.18), ('sol alt köşe (kapalı duvarın başı/sonu)', [(0.2,0.5),(0.5,0.5),(0.5,0.2)], 9.36-0.3*0.3), ('ters yönde çizim', [(3.8,0.38),(3.39,0.38),(3.39,0.2)], 9.36-0.41*0.18)):
            await ev("RK.S.faceAsk=null; RK.S.chain=null"); await ev(SETUP + "(-1)"); await ev("RK.view.s=140; RK.view.ox=(%s<1? 20 : -300); RK.view.oy=230; RK.commit()" % pts[0][0]); await btn('#sheet button[data-a=cikm][data-v=el]')
            for x,y in pts: q = await W(x,y); await ctap(*q); await pg.wait_for_timeout(150)
            if await ev("!!document.querySelector('#sheet button[data-a=askN]')"): await btn('#sheet button[data-a=askN]')
            a1 = await ev(AR); cor = await ev("[%s].every(p=>RK.wallGeom(RK.P.walls[0]).Q.some(q=>Math.hypot(q[0]-p[0],q[1]-p[1])<1e-6))" % ','.join('[%s,%s]' % p for p in pts[1:2]))
            ck(f'köşe kolonu, {nm}: alan {exp:.4f}, kolon köşesi beyaz çizgide', abs(a1-exp)<1e-3 and cor, [a1, cor, await ev("document.querySelector('#toast').textContent")])
            await pg.screenshot(path=f't21_k{nm[0:3]}.png')
        # "Sabit kalsın": turuncu çizgi yerinde kalır, beyaz çizgi çizilen yolu izler
        await ev(SETUP + "(-1)"); await ev("RK.view.s=140; RK.view.ox=-300; RK.view.oy=230; RK.commit()"); await btn('#sheet button[data-a=cikm][data-v=el]')
        for x,y in [(3.39,0.2),(3.39,0.38),(3.8,0.38)]: q = await W(x,y); await ctap(*q); await pg.wait_for_timeout(150)
        ck('köşe kolonu sonrası soru: turuncu çizgi ne olsun?', await ev("!!document.querySelector('#sheet button[data-a=faN]')"))
        await btn('#sheet button[data-a=faN]')
        ref = await ev("RK.P.walls[0].nodes.map(id=>{const n=RK.P.nodes.find(n=>n.id===id); return [+n.x.toFixed(3),+n.y.toFixed(3)]})"); a1 = await ev(AR)
        ck('  Sabit kalsın: turuncu çizgi (duvar) aynen, oda kolon kadar küçüldü %.4f' % (9.36-0.41*0.18), ref==[[0,0],[4,0],[4,3],[0,3]] and abs(a1-(9.36-0.41*0.18))<1e-3, [ref, a1])
        await pg.screenshot(path='t21_sabit.png')
        await ev("RK.undo()"); ck('  geri al: kalınlık korunan hal', abs(await ev(AR)-(9.36-0.41*0.18))<1e-3 and await ev("RK.P.walls[0].nodes.length")>4, [await ev(AR), await ev("RK.P.walls[0].nodes.length")])
        # Ölçü yazarak: başlangıç/bitiş yüzden
        out = await ev(SETUP + "(1)"); await btn('#sheet button[data-a=cikm][data-v=olcu]')
        q = await W(0.8, -0.2); await ctap(*q); s1 = await ev("JSON.stringify(RK.S.cik)")
        q = await W(1.8, -0.2); await ctap(*q); s2 = await ev("RK.S.cik.step")
        ck('Ölçü yazarak: diğer yüze dokunuşlar kabul edildi (başlangıç 0.80 çizgide)', '"step":2' in s1 and '[0.8,0]' in s1.replace('0.8000000000000002','0.8') and s2==3, [s1, s2])
        ck('JS hatası yok', not errs, errs[:3]); await b.close()
    print('TOPLAM', sum(R), '/', len(R)); sys.exit(0 if all(R) else 1)
asyncio.run(main())
