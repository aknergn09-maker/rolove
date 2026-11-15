import os, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
URL = (ROOT / 'index.html').as_uri()
OUT = ROOT / 'test' / 'out'; OUT.mkdir(exist_ok=True); os.chdir(OUT)
CHROME = os.environ.get('CHROME', '/usr/bin/google-chrome' if os.path.exists('/usr/bin/google-chrome') else None)
import asyncio, sys
from playwright.async_api import async_playwright
R=[]
def ck(n,ok,i=''): R.append(bool(ok)); print(('PASS ' if ok else 'FAIL ')+n, i if not ok else '')
# Sahte Bosch GLM: Web Bluetooth taklidi; window._glmSend(m) cihazdan ölçüm bildirimi gönderir
FAKE = """(()=>{ const listeners=[]; window._glmWrites=[];
  const chr={ addEventListener:(t,f)=>listeners.push(f), startNotifications:async()=>chr, writeValueWithoutResponse:async(v)=>{window._glmWrites.push([...v])} };
  const dev={ name:'GLM50-27 CG', addEventListener:()=>{}, gatt:{ connect:async()=>({ getPrimaryService:async(u)=>{ if(u!=='02a6c0d0-0451-4000-b000-fb3210111989') throw new Error('svc'); return { getCharacteristic:async(c)=>{ if(c!=='02a6c0d1-0451-4000-b000-fb3210111989') throw new Error('chr'); return chr; } }; } }) } };
  Object.defineProperty(navigator,'bluetooth',{value:{ requestDevice:async(o)=>{ window._glmReq=o; return dev; } }});
  window._glmSend=(m)=>{ const b=new ArrayBuffer(20); const dv=new DataView(b); [0xC0,0x55,0x10,0x06].forEach((x,i)=>dv.setUint8(i,x)); dv.setFloat32(7,m,true); listeners.forEach(f=>f({target:{value:dv}})); };
})()"""
LEN = "Object.fromEntries(RK.P.lines.filter(l=>!l.step).map(l=>[l.id, +RK.lineLen(l).toFixed(4)]))"
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path=CHROME, args=['--no-sandbox'])
        ctx=await b.new_context(**p.devices['iPhone 13']); await ctx.add_init_script(FAKE); pg=await ctx.new_page(); errs=[]
        pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto(URL); await pg.evaluate("localStorage.clear()"); await pg.reload(); await pg.wait_for_timeout(300); ev=pg.evaluate
        async def btn(sel):
            r = await ev(f"(()=>{{const e=document.querySelector('{sel}'); if(!e||e.disabled) return null; const r=e.getBoundingClientRect(); return [r.left+r.width/2, r.top+r.height/2]}})()")
            if not r: return False
            await pg.touchscreen.tap(r[0], r[1]); await pg.wait_for_timeout(80); return True
        async def ctap(x,y):
            r = await ev("(()=>{const r=document.querySelector('#cv').getBoundingClientRect(); return [r.left,r.top]})()"); await pg.touchscreen.tap(r[0]+x, r[1]+y); await pg.wait_for_timeout(90)
        async def W(x,y): return await ev(f"RK.w2s({x},{y})")
        # A 4×3 ve sağında B 3×3 (ortak duvar), eskiz
        await ev("""(()=>{const P=RK.P; const N=(id,x,y)=>P.nodes.push({id,x,y}); const L=(id,a,b)=>P.lines.push({id,a,b,kind:'sketch'});
          N('a',0,0);N('b',4,0);N('c',4,3);N('d',0,3);N('e',7,0);N('f',7,3); L('AB','a','b');L('BC','b','c');L('CD','c','d');L('DA','d','a');L('BE','b','e');L('EF','e','f');L('FC','f','c');
          P.rooms.push({id:'r1',name:'A',ax:2,ay:1.5},{id:'r2',name:'B',ax:5.5,ay:1.5}); RK.commit(); RK.view.s=45; RK.view.ox=30; RK.view.oy=300; RK.commit();})()""")
        await btn('#cats button[data-cat=olc]')
        ck('Ölç sekmesi ve aracı', await ev("RK.S.tool")=='olc')
        await btn('#sheet button[data-a=lzc]'); await pg.wait_for_timeout(200)
        ck('lazer bağlandı (sahte GLM), cihaza C0 55 02 01 00 1A yazıldı', await ev("RK.LZ.state")=='bağlı' and await ev("window._glmWrites[0]")==[0xC0,0x55,0x02,0x01,0x00,0x1A], [await ev("RK.LZ.state"), await ev("window._glmWrites")])
        ck('  ayrıştırıcı: başlık yanlışsa yok sayar', await ev("(()=>{const dv=new DataView(new ArrayBuffer(12)); dv.setFloat32(7,2,true); return RK.laserParse(dv)})()") is None)
        # 1) çizgiye dokun, sonra lazer 4.100 → A'nın alt çizgisi
        q = await W(2,0); await ctap(*q)
        ck('çizgi seçildi', await ev("RK.S.ms.sel")=='AB')
        await ev("window._glmSend(4.1)"); await pg.wait_for_timeout(100)
        L1 = await ev(LEN)
        ck('lazer 4.100: AB tam 4.100', abs(L1['AB']-4.1)<1e-4, L1)
        ck('  ölçülmeyenler aynı oranla ölçeklendi (BC 3.075, BE 3.075)', abs(L1['BC']-3.075)<2e-3 and abs(L1['BE']-3.075)<2e-3, L1)
        ck('  dik açılar korundu', await ev("(()=>{const n=id=>RK.P.nodes.find(x=>x.id===id); return Math.abs(n('a').y-n('b').y)<1e-4 && Math.abs(n('b').x-n('c').x)<1e-4 && Math.abs(n('e').x-n('f').x)<1e-4})()"))
        # 2) önce lazer, sonra çizgi (BC = 2.950)
        await ev("window._glmSend(2.95)"); await pg.wait_for_timeout(100)
        ck('önce ölçüp sonra dokunma: bekleyen ölçü gösterildi', await ev("RK.S.ms.pend")!=None and await ev("!!document.querySelector('#sheet button[data-a=mspx]')"))
        q = await W(4.1,1.5); await ctap(*q)
        L2 = await ev(LEN)
        ck('BC 2.950 oturdu, AB 4.100 bozulmadı', abs(L2['BC']-2.95)<1e-4 and abs(L2['AB']-4.1)<1e-4, L2)
        ck('  karşı kenarlar uyum: DA ≈ 2.95, CD ≈ 4.10', abs(L2['DA']-2.95)<2e-3 and abs(L2['CD']-4.1)<2e-3, L2)
        # 3) elle yaz: BE = 302,5 cm
        q = await W(5.5,0); await ctap(*q); await btn('#sheet button[data-a=np]')
        for c in ['3','0','2',',','5']: await btn(f'#sheet button[data-k="{c}"]')
        await btn('#sheet button[data-a=msok]')
        L3 = await ev(LEN); ck('elle 302,5 cm: BE 3.025, öncekiler korundu', abs(L3['BE']-3.025)<1e-4 and abs(L3['BC']-2.95)<1e-4 and abs(L3['AB']-4.1)<1e-4, L3)
        ck('  ölçülen etiketler mm hassasiyetle (lazer rengi)', await ev("RK.P.lines.filter(l=>l.kind==='laser').length")==3)
        # 4) çelişki: kapalı zincirde imkânsız ölçü
        q = await W(5.5,3); await ctap(*q); await ev("window._glmSend(3.5)"); await pg.wait_for_timeout(100)
        ck('çelişen ölçü (FC 3.5, BE 3.025 iken) uyarı verir', 'çelişiyor' in await ev("document.querySelector('#toast').textContent"), await ev("document.querySelector('#toast').textContent"))
        await ev("RK.undo()")
        # 5) Ötele sonrası uyumsuzluk kırmızı + yeniden hesapla
        await ev("(()=>{const n=RK.P.nodes.find(x=>x.id==='e'); n.x+=0.2; const f=RK.P.nodes.find(x=>x.id==='f'); f.x+=0.2; RK.commit();})()")
        ck('ölçüden sonra elle bozulunca uyumsuz sayısı gösterilir', 'uyumsuz' in await ev("document.querySelector('#sheet').textContent"))
        await btn('#sheet button[data-a=msadj]'); L5 = await ev(LEN)
        ck('Yeniden hesapla: BE tekrar 3.025 (±0.5 mm)', abs(L5['BE']-3.025)<5e-4, L5)
        # 6) kapı bölünmesi: ölçülü çizgi bölünce parça toplamı korunur
        s0 = await ev("[RK.P.lines.filter(l=>l.kind==='laser').length, RK.P.lines.filter(l=>l.kind==='laser').reduce((s,l)=>s+l.m,0)]")
        await ev("(()=>{const l=RK.P.lines.find(l=>l.id==='AB'); const a=RK.P.nodes.find(n=>n.id===l.a), b=RK.P.nodes.find(n=>n.id===l.b); RK.nodeAt([(a.x*0.3+b.x*0.7),(a.y*0.3+b.y*0.7)]); RK.commit();})()")
        s1 = await ev("[RK.P.lines.filter(l=>l.kind==='laser').length, RK.P.lines.filter(l=>l.kind==='laser').reduce((s,l)=>s+l.m,0), RK.P.lines.filter(l=>l.kind==='laser').map(l=>l.m).sort()]")
        ck('ölçülü çizgi bölününce 2 parça olur, ölçü toplamı korunur (4.100 = 2.870 + 1.230)', s1[0]==s0[0]+1 and abs(s1[1]-s0[1])<1e-9 and 1.23 in [round(v,3) for v in s1[2]], [s0, s1])
        await btn('#fFit'); await pg.screenshot(path='o13.png')
        ck('JS hatası yok', not errs, errs[:3]); await b.close()
    print('TOPLAM', sum(R), '/', len(R)); sys.exit(0 if all(R) else 1)
asyncio.run(main())
