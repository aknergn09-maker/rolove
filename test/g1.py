# PC GÖNYE: telefon DXF + total NCN → hesapla → rapor, dengelenmiş DXF (ezdxf ile doğrulanır), koordinat listesi
import os, pathlib, sys, asyncio, json, math, subprocess
ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / 'test' / 'out'; OUT.mkdir(exist_ok=True)
CHROME = os.environ.get('CHROME', '/usr/bin/google-chrome' if os.path.exists('/usr/bin/google-chrome') else None)
from playwright.async_api import async_playwright
R=[]
def ck(n,ok,i=''): R.append(bool(ok)); print(('PASS ' if ok else 'FAIL ')+n, '' if ok else i)
async def main():
    subprocess.run([sys.executable, str(ROOT/'test'/'g_make.py')], check=True)
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path=CHROME, args=['--no-sandbox'])
        ctx=await b.new_context(viewport={'width':1300,'height':800}, accept_downloads=True); pg=await ctx.new_page(); errs=[]
        pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto((ROOT/'gonye.html').as_uri()); await pg.wait_for_timeout(200); ev=pg.evaluate
        await pg.set_input_files('#pick', [str(OUT/'g_kroki.dxf'), str(OUT/'g_total.ncn')]); await pg.wait_for_timeout(300)
        info=await ev("document.querySelector('#info').innerText")
        ck('dosyalar okundu: 2 total eşleşti, 7 ölçü', 'Total ile eşleşen: 2 nokta (101, 102)' in info and '7 ölçü' in info, info)
        await pg.click('#run'); await pg.wait_for_timeout(300)
        out=await ev("document.querySelector('#out').innerText")
        ck('rapor çıktı, kötü ölçü yok', 'Sonuç' in out and 'kontrol et' not in out, out[:400])
        tr=json.load(open(OUT/'g_true.json')); co=await ev("GN.ST.R.coords")
        sk=json.load(open(OUT/'g_skmap.json'))
        errs_mm={k:math.dist(co[n],tr[k])*1000 for k,n in sk.items() if k not in ('G','H')}
        ck('ölçülen tüm noktalar gerçeğe 2 mm içinde (kapı noktaları ölçülmedi, oranla yerleşir)', max(errs_mm.values())<2, errs_mm)
        async with pg.expect_download() as dl: await pg.click('#dxf')
        d=await dl.value; fn=OUT/'g_sonuc.dxf'; await d.save_as(fn)
        import ezdxf
        doc=ezdxf.readfile(fn); msp=doc.modelspace(); from collections import Counter; C=Counter(e.dxf.layer for e in msp)
        ck('dengelenmiş DXF geçerli, katmanlar: CIZIM, KAPI, NOKTA_TOTAL, OLCU, GONYE, DIKAYAK', len(doc.audit().errors)==0 and all(C[l] for l in ['CIZIM','KAPI','NOKTA_TOTAL','OLCU','GONYE','DIKAYAK']), C)
        ins=[e for e in msp if e.dxftype()=='INSERT'][0]
        ck('  kapı bloğu gerçek koordinata döndürülüp oturdu', abs(ins.dxf.insert[0]-co[sk['G']][0])<0.001 and abs(ins.dxf.insert[1]-co[sk['G']][1])<0.001 and abs(ins.dxf.rotation-16)<0.5, (tuple(ins.dxf.insert), co[sk['G']], ins.dxf.rotation))
        async with pg.expect_download() as dl: await pg.click('#csv')
        c=open(await (await dl.value).path(), encoding='utf-8').read()
        ck('koordinat listesi: AD;Y;X', c.startswith('AD;Y;X') and '101;' in c)
        await pg.screenshot(path=str(OUT/'g1.png'))
        ck('JS hatası yok', not errs, errs[:3]); await b.close()
    print('TOPLAM', sum(R), '/', len(R)); sys.exit(0 if all(R) else 1)
asyncio.run(main())
