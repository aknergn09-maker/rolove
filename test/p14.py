# ÖNİZLEME: başka odanın duvar yüzüne dayanan oda (kullanıcı JSON'u gibi). Ölç: yüz parçası komşu duvarın İÇ yüzünde biter (eğik yüzde de); Gönye: duvar yüzündeki oda köşelerine dokunulur, sadece bu odanın duvarı oynar, öbür oda aynen kalır
import os, pathlib, sys, asyncio, math
ROOT = pathlib.Path(__file__).resolve().parent.parent
URL = (ROOT / 'onizleme.html').as_uri()
OUT = ROOT / 'test' / 'out'; OUT.mkdir(exist_ok=True); os.chdir(OUT)
CHROME = os.environ.get('CHROME', '/usr/bin/google-chrome' if os.path.exists('/usr/bin/google-chrome') else None)
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
            await pg.touchscreen.tap(r[0], r[1]); await pg.wait_for_timeout(100); return True
        async def ctap(x,y):
            r = await ev("(()=>{const r=document.querySelector('#cv').getBoundingClientRect(); return [r.left,r.top]})()"); q = await ev(f"RK.w2s({x},{y})"); await pg.touchscreen.tap(r[0]+q[0], r[1]+q[1]); await pg.wait_for_timeout(250)
        # A: üst duvarı hafif eğik (sağa doğru 0.2 m yükselir); B: A'nın üst beyaz yüzüne dayanan açık duvar (bant B'nin içine)
        await ev("""(()=>{const P=RK.P; P.nodes=[];P.lines=[];P.walls=[];P.rooms=[];P.diags=[];
          const C=[[0,0],[6,0],[6,4.2],[0,4]]; const ids=C.map(([x,y],i)=>{const id='a'+i; P.nodes.push({id,x,y}); return id}); for(let i=0;i<4;i++) P.lines.push({id:'A'+i,a:ids[i],b:ids[(i+1)%4],kind:'sketch'}); P.walls.push({id:'WA',nodes:ids,closed:true,t:0.3,side:1});
          const fy=x=>4+0.2*x/6+0.3*Math.hypot(6,0.2)/6; const D=[[2,fy(2)],[2,7],[5,7],[5,fy(5)]]; const jd=D.map(([x,y],i)=>{const id='b'+i; P.nodes.push({id,x,y}); return id}); for(let i=0;i<3;i++) P.lines.push({id:'B'+i,a:jd[i],b:jd[i+1],kind:'sketch'}); P.walls.push({id:'WB',nodes:jd,closed:false,t:0.3,side:-1});
          P.rooms.push({id:'rA',name:'A',ax:3,ay:2},{id:'rB',name:'B',ax:3.5,ay:5.5}); RK.commit(); RK.view.s=70; RK.view.ox=-20; RK.view.oy=560; RK.commit()})()""")
        A0 = await ev("RK.P.nodes.filter(n=>n.id[0]==='a').map(n=>[n.x,n.y])")
        ck('kurulum: B odası A’nın eğik yüzüne dayanıyor', await ev("+RK.rA(RK.P.rooms[1]).toFixed(2)")>5, await ev("RK.P.rooms.map(r=>r._f&&RK.rA(r))"))
        await btn('#tabs button[data-tab=olcum]'); await btn('#tools button[data-tool=olc]')
        await ctap(3.5, 4.4)
        fs = await ev("RK.S.ms.fs")
        ck('Ölç: B içinde A’nın yüzüne dokununca parça B’nin iç yüzleri arasında (2.3–4.7), duvar kalınlığı girmiyor', fs and abs(min(fs[0][0],fs[1][0])-2.3)<1e-3 and abs(max(fs[0][0],fs[1][0])-4.7)<1e-3, fs)
        await btn('#tools button[data-tool=kontrol]')
        bp = await ev("RK.P.rooms.find(r=>r.id==='rB')._f.poly.map(p=>[+p[0].toFixed(4),+p[1].toFixed(4)])")
        c1 = min(bp, key=lambda p: p[0]+p[1]); c2 = max(bp, key=lambda p: p[0]+p[1])
        await ctap(*c1); await ctap(*c2)
        ck('Gönye: duvar yüzündeki oda köşelerine dokunulabiliyor (düğüm olmasa da)', await ev("!!(RK.S.kt.a&&RK.S.kt.b)") and await ev("RK.S.kt.room")=='B', [c1, c2, await ev("document.querySelector('#toast').textContent")])
        L0 = math.dist(c1, c2); await ev(f"RK.laserValue({round(L0+0.04,3)})"); await btn('#sheet button[data-a=dgok]')
        await btn('#sheet button[data-a=gny][data-v=rB]')
        ang = await ev("RK.S.calc.ang.map(o=>o.a)")
        ck('  önizleme: 4 köşe açısı, toplam 360°', len(ang)==4 and abs(sum(ang)-360)<0.3, ang)
        await btn('#sheet button[data-a=cok]')
        d = await ev("+RK.diagLen(RK.P.diags[0]).toFixed(4)")
        ck('  Onayla: çapraz %.3f oldu' % (L0+0.04), abs(d-round(L0+0.04,3))<2e-3, d)
        A1 = await ev("RK.P.nodes.filter(n=>n.id[0]==='a').map(n=>[n.x,n.y])")
        ck('  A odası hiç oynamadı', all(math.dist(p,q)<1e-6 for p,q in zip(A0,A1)), [A0,A1])
        ck('  B’nin duvar uçları A’nın yüzünde kaldı', await ev("(()=>{const g=RK.wallGeom(RK.P.walls[0]); const f=g.quads.find(q=>q.i===2); return ['b0','b3'].every(id=>{const n=RK.P.nodes.find(x=>x.id===id); const A=f.poly[3],B=f.poly[2]; return Math.abs((B[0]-A[0])*(n.y-A[1])-(B[1]-A[1])*(n.x-A[0]))/Math.hypot(B[0]-A[0],B[1]-A[1])<1e-3})})()"))
        await pg.screenshot(path='p14.png')
        ck('JS hatası yok', not errs, errs[:3]); await b.close()
    print('TOPLAM', sum(R), '/', len(R)); sys.exit(0 if all(R) else 1)
asyncio.run(main())
