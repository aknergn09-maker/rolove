# YENİ CAD aşama 3–4: kapı/pencere (2 dokunuş, kırık noktası, offset ikizi, yön, seçim paneli, kenarla gelme, silme) + DXF dışa/içe + yeni çizim
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
        ctx=await b.new_context(**p.devices['iPhone 13'], accept_downloads=True); pg=await ctx.new_page(); errs=[]
        pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto(URL); await pg.evaluate("localStorage.clear()"); await pg.reload(); await pg.wait_for_timeout(300); ev=pg.evaluate
        cdp=await ctx.new_cdp_session(pg)
        async def btn(a):
            r = await ev(f"(()=>{{const e=document.querySelector('button[data-a=\"{a}\"]'); if(!e) return null; const r=e.getBoundingClientRect(); return [r.left+r.width/2, r.top+r.height/2]}})()")
            if not r: return False
            await pg.touchscreen.tap(r[0], r[1]); await pg.wait_for_timeout(60); return True
        async def S(x,y): return await ev(f"CAD.w2s({x},{y})")
        async def wtap(x,y): s=await S(x,y); await pg.touchscreen.tap(s[0],s[1]); await pg.wait_for_timeout(60)
        async def drag(p0,p1,n=12):
            a=await S(*p0); c=await S(*p1)
            await cdp.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':a[0],'y':a[1]}]})
            for k in range(1,n+1): await cdp.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{'x':a[0]+(c[0]-a[0])*k/n,'y':a[1]+(c[1]-a[1])*k/n}]})
            await cdp.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]}); await pg.wait_for_timeout(80)
        E=lambda: ev("Object.fromEntries(CAD.D.ents.map(e=>[e.id,e]))")
        OPS=lambda: ev("JSON.parse(JSON.stringify(CAD.D.ops))")
        await ev("""CAD.D={nid:10,ents:[{id:'in',t:'pl',p:[[0,0],[4,0],[4,3],[0,3]],c:true},{id:'out',t:'pl',p:[[-0.2,-0.2],[4.2,-0.2],[4.2,3.2],[-0.2,3.2]],c:true}],ops:[]};
          Object.assign(CAD.view,{s:50,ox:40,oy:420}); CAD.commit()""")
        await btn('fly:open')
        ck('Kapı grubu: son araç (kapı) direkt aktif', await ev("CAD.S.tool")=='door')
        await wtap(0.5,0); await wtap(1.4,0)
        O=await OPS(); e=await E()
        ck('kapı 2 dokunuşla kondu (0.90 m)', len(O)==1 and O[0]['t']=='door' and abs(O[0]['b'][0]-O[0]['a'][0]-0.9)<1e-6, O)
        ck('  iç pline\'a aynı doğrultuda 2 kırık noktası', len(e['in']['p'])==6 and near(e['in']['p'][1],(0.5,0)) and near(e['in']['p'][2],(1.4,0)), e['in']['p'])
        ck('  offset ikizine de kırık noktası (dış pline 6 köşe)', len(e['out']['p'])==6 and near(e['out']['p'][1],(0.5,-0.2)), e['out']['p'])
        ck('  kalınlık bulundu (-0.20), kapı odaya açılıyor', abs(await ev("opTh(CAD.D.ops[0])")+0.2)<1e-6 and O[0]['sw']==1)
        ck('  alan bozulmadı (2 kapalı alan)', await ev("faces(CAD.D.ents).length")==2)
        await wtap(0.95,-0.1)
        ck('  kapıya tekrar dokununca yön değişti', (await OPS())[0]['hinge']==1)
        await btn('fly:open'); await btn('t:win'); await wtap(2.5,3); await wtap(3.5,3)
        O=await OPS()
        ck('pencere üst kenara kondu', len(O)==2 and O[1]['t']=='win' and abs(O[1]['a'][1]-3)<1e-9)
        await btn('sec'); await wtap(0.95,0)
        ck('Seç: kapı seçildi, simgeli panel (5 düğme)', await ev("CAD.S.selOp")==O[0]['id'] and await ev("document.querySelectorAll('#opp button').length")==5)
        sw0=(await OPS())[0]['sw']; await btn('ops')
        ck('  panelden açılış tarafı değişti', (await OPS())[0]['sw']==-sw0)
        await drag((1.4,0),(1.6,0))
        O=await OPS(); e=await E()
        ck('  kapı ucu tutamakla çizgi boyunca uzadı, pline köşesi de geldi', near(O[0]['b'],(1.6,0)) and near(e['in']['p'][2],(1.6,0)), [O[0], e['in']['p']])
        await wtap(4,1.5)
        await drag((2,3),(2,3.8))
        O=await OPS()
        ck('üst kenar orta tutamakla kaydı, pencere de geldi', abs(O[1]['a'][1]-3.8)<1e-9 and abs(O[1]['b'][1]-3.8)<1e-9, O[1])
        await btn('fly:edit'); await btn('t:erase'); await wtap(1.05,0)
        O=await OPS(); e=await E()
        ck('Sil: kapı silindi, kırık noktaları kalktı', len(O)==1 and len(e['in']['p'])==6 and len(e['out']['p'])==6 and not any(abs(q[1])<1e-9 and 0<q[0]<4 for q in e['in']['p']), [len(O), e['in']['p'], e['out']['p']])
        await pg.screenshot(path=str(OUT/'c5.png'))
        # DXF
        dx=await ev("CAD.makeDXF()")
        ck('DXF: kapalı POLYLINE, PENCERE ve NOKTA katmanı, X1 adı', 'POLYLINE' in dx and '\r\n70\r\n1\r\n' in dx and '\r\nPENCERE\r\n' in dx and '\r\nX1\r\n' in dx and '\r\nINSERT\r\n' in dx and 'arial.ttf' in dx and dx.rstrip().endswith('EOF'))
        n0=await ev("CAD.D.ents.length")
        async with pg.expect_download() as dl: await btn('fly:file'); await btn('exp')
        d=await dl.value
        ck('  dışa aktar düğmesi dosya verdi', d.suggested_filename.startswith('cizim_') and d.suggested_filename.endswith('.dxf'), d.suggested_filename)
        await btn('fly:file'); await btn('new')
        ck('yeni çizim tek dokunuşta silmedi (onay bekliyor)', await ev("CAD.D.ents.length")==n0 and await ev("!!document.querySelector('button[data-a=new].dng')"))
        await btn('new')
        ck('  ikinci dokunuşta temizlendi', await ev("CAD.D.ents.length")==0 and await ev("CAD.D.ops.length")==0)
        await pg.set_input_files('#fileIn', files=[{'name':'a.dxf','mimeType':'application/dxf','buffer':dx.encode()}]); await pg.wait_for_timeout(300)
        im=await ev("CAD.D.ents.map(e=>e.t+(e.imp?'*':''))")
        ck('DXF içe aktarıldı: polyline, çizgi, nokta; hepsi altlık', 'pl*' in im and 'line*' in im and 'pt*' in im and all(x.endswith('*') for x in im), im)
        await btn('sec'); await wtap(4,1.5)
        ck('  altlık seçilemiyor (kilitli)', await ev("CAD.S.sel.size")==0)
        ck('  altlık kapalı alan dolgusu yapmıyor', await ev("CAD.D.ents.filter(e=>!e.imp).length")==0)
        await ev("Object.assign(CAD.view,{s:50,ox:40,oy:420}); CAD.render()"); await btn('fly:draw'); await btn('t:line')
        await wtap(4,0.05); 
        ck('  altlığın köşesine yakalanıyor', near(await ev("CAD.S.chain.pts[0]"),(4,0)), await ev("CAD.S.chain.pts[0]"))
        dx2=await ev("CAD.makeDXF()")
        ck('  dışa aktarmada IMPORT katmanında', '\r\nIMPORT\r\n' in dx2)
        ck('JS hatası yok', not errs, errs[:3]); await b.close()
    print('TOPLAM', sum(R), '/', len(R)); sys.exit(0 if all(R) else 1)
asyncio.run(main())
