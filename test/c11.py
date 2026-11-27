# YENİ CAD: krokiler ve yedek — eski kaydın taşınması, yeni/çoğalt/adlandır/aç/sil, önceki haline dönme, yedek al (dosya), yedekten yükle, yedek uyarısı
import os, pathlib, sys, asyncio, json
ROOT = pathlib.Path(__file__).resolve().parent.parent
URL = (ROOT / 'cad.html').as_uri()
OUT = ROOT / 'test' / 'out'; OUT.mkdir(exist_ok=True)
CHROME = os.environ.get('CHROME', '/usr/bin/google-chrome' if os.path.exists('/usr/bin/google-chrome') else None)
from playwright.async_api import async_playwright
R=[]
def ck(n,ok,i=''): R.append(bool(ok)); print(('PASS ' if ok else 'FAIL ')+n, '' if ok else i)
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path=CHROME, args=['--no-sandbox'])
        ctx=await b.new_context(**p.devices['iPhone 13'], accept_downloads=True); pg=await ctx.new_page(); errs=[]
        pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto(URL); ev=pg.evaluate
        # eski sürümün tek çizimli kaydı
        await ev("""localStorage.clear(); localStorage.setItem('rcad1_doc', JSON.stringify({D:{nid:5,ents:[{id:'e1',t:'line',a:[0,0],b:[3,0]}]},view:{s:50,ox:60,oy:300},snaps:{end:1,mid:1,near:1,orth:1,xy:0,trk:1}}))""")
        await pg.reload(); await pg.wait_for_timeout(300)
        async def btn(a):
            r = await ev(f"(()=>{{const e=document.querySelector('button[data-a=\"{a}\"]'); if(!e) return null; const r=e.getBoundingClientRect(); return [r.left+r.width/2, r.top+r.height/2]}})()")
            if not r: return False
            await pg.touchscreen.tap(r[0], r[1]); await pg.wait_for_timeout(80); return True
        ck('eski kayıt "Kroki 1" olarak taşındı', await ev("CAD.D.ents.length")==1 and await ev("CAD.IDX.list.map(p=>p.name).join()")=='Kroki 1')
        ck('hiç yedek yok: klasörde kırmızı nokta', await ev("!!document.querySelector('button[data-a=\"fly:file\"].dot')"))
        await btn('fly:file'); await btn('proj')
        ck('Krokiler paneli açıldı, 1 kroki', await ev("getComputedStyle(document.querySelector('#pp')).display")=='flex' and await ev("document.querySelectorAll('.ppi').length")==1)
        ck('  ilk çizimde önceki hal kaydı alındı', await ev("document.querySelectorAll('[data-a^=psnap]').length")==1)
        await btn('pnew')
        ck('yeni kroki: boş, listede 2', await ev("CAD.D.ents.length")==0 and await ev("document.querySelectorAll('.ppi').length")==2)
        await pg.fill('#ppName','Ahmet Bey dükkan'); await ev("document.querySelector('#ppName').dispatchEvent(new Event('change'))")
        ck('  yeniden adlandırıldı', 'Ahmet Bey dükkan' in await ev("CAD.IDX.list.map(p=>p.name).join()"))
        await ev("CAD.D.ents.push({id:'x1',t:'line',a:[0,0],b:[0,2]},{id:'x2',t:'line',a:[0,2],b:[2,2]}); CAD.commit()")
        k1=await ev("CAD.IDX.list.find(p=>p.name==='Kroki 1').id")
        await btn('popen:'+k1)
        ck('Kroki 1 açıldı, çizimi geldi', await ev("CAD.D.ents.length")==1 and await ev("CAD.D.ents[0].b[0]")==3)
        # önceki haline dön
        await ev("CAD.D.ents.length=0; CAD.commit()")
        await btn('fly:file'); await btn('proj'); await btn('psnap:0')
        ck('önceki haline döndü', await ev("CAD.D.ents.length")==1)
        await btn('undo')
        ck('  geri al ile dönüş geri alınabiliyor', await ev("CAD.D.ents.length")==0)
        await btn('redo')
        # yedek al
        await btn('fly:file'); await btn('proj')
        async with pg.expect_download() as dl: await btn('bkout')
        d=await dl.value; bk=json.load(open(await d.path(), encoding='utf-8'))
        ck('yedek dosyası: 2 kroki, adlarıyla', d.suggested_filename.startswith('kroki_yedek_') and len(bk['projects'])==2 and {'Kroki 1','Ahmet Bey dükkan'}=={p['name'] for p in bk['projects']}, d.suggested_filename)
        ck('  yedek alınınca kırmızı nokta kalktı', not await ev("!!document.querySelector('button[data-a=\"fly:file\"].dot')"))
        # sil (iki dokunuş) ve yedekten geri yükle
        ah=await ev("CAD.IDX.list.find(p=>p.name==='Ahmet Bey dükkan').id")
        await btn('pdel:'+ah)
        ck('sil: ilk dokunuşta silmedi', await ev("CAD.IDX.list.length")==2)
        await btn('pdel:'+ah)
        ck('  ikinci dokunuşta silindi', await ev("CAD.IDX.list.length")==1)
        await pg.set_input_files('#bkIn', files=[{'name':'y.json','mimeType':'application/json','buffer':json.dumps(bk).encode()}]); await pg.wait_for_timeout(300)
        ck('yedekten yükle: silinen geri geldi, aynısı çoğalmadı', await ev("CAD.IDX.list.length")==2 and 'Ahmet Bey dükkan' in await ev("CAD.IDX.list.map(p=>p.name).join()"))
        await pg.reload(); await pg.wait_for_timeout(300)
        ck('yeniden açınca son kroki ve liste duruyor', await ev("CAD.IDX.list.length")==2 and await ev("CAD.D.ents.length")==1)
        await btn('fly:file'); await btn('proj'); await pg.screenshot(path=str(OUT/'c11.png'))
        ck('JS hatası yok', not errs, errs[:3]); await b.close()
    print('TOPLAM', sum(R), '/', len(R)); sys.exit(0 if all(R) else 1)
asyncio.run(main())
