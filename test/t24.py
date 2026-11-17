# Lazer bağlantısı sağlamlık: yazma yöntemi yedekleri, kopunca yeniden bağlanma, gelen veri tanısı, Bluetooth'suz tarayıcı uyarısı
import os, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
URL = (ROOT / os.environ.get('PAGE', 'index.html')).as_uri()
OUT = ROOT / 'test' / 'out'; OUT.mkdir(exist_ok=True); os.chdir(OUT)
CHROME = os.environ.get('CHROME', '/usr/bin/google-chrome' if os.path.exists('/usr/bin/google-chrome') else None)
import asyncio, sys
from playwright.async_api import async_playwright
R=[]
def ck(n,ok,i=''): R.append(bool(ok)); print(('PASS ' if ok else 'FAIL ')+n, i if not ok else '')
FAKE = """(()=>{ const listeners=[]; const dl=[]; window._glmWrites=[]; window._conn=0;
  const chr={ addEventListener:(t,f)=>listeners.push(f), startNotifications:async()=>chr, writeValueWithoutResponse:async(v)=>{ throw new Error('desteklenmiyor'); }, writeValue:async(v)=>{window._glmWrites.push([...v])} };
  const dev={ name:'GLM 50 C', addEventListener:(t,f)=>dl.push(f), gatt:{ connect:async()=>{ window._conn++; return { getPrimaryService:async(u)=>({ getCharacteristic:async(c)=>chr }) }; } } };
  Object.defineProperty(navigator,'bluetooth',{value:{ requestDevice:async(o)=>dev }});
  window._drop=()=>dl.forEach(f=>f());
  window._glmRaw=(bytes)=>{ const dv=new DataView(new Uint8Array(bytes).buffer); listeners.forEach(f=>f({target:{value:dv}})); };
})()"""
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path=CHROME, args=['--no-sandbox'])
        ctx=await b.new_context(**p.devices['iPhone 13']); pg=await ctx.new_page(); errs=[]; dlg=[]
        pg.on('pageerror', lambda e: errs.append(str(e))); pg.on('dialog', lambda d: (dlg.append(d.message), asyncio.ensure_future(d.dismiss())))
        await pg.goto(URL); await pg.evaluate("localStorage.clear()"); await pg.reload(); await pg.wait_for_timeout(300); ev=pg.evaluate
        async def btn(sel):
            r = await ev(f"(()=>{{const e=document.querySelector('{sel}'); if(!e||e.disabled) return null; const r=e.getBoundingClientRect(); return [r.left+r.width/2, r.top+r.height/2]}})()")
            if not r: return False
            await pg.touchscreen.tap(r[0], r[1]); await pg.wait_for_timeout(120); return True
        if await ev("!!document.querySelector('#tabs')"): await btn('#tabs button[data-tab=olcum]')
        else: await btn('#cats button[data-cat=olc]')
        await btn('#tools button[data-tool=olc]')
        ck('Bluetooth olmayan tarayıcı: panelde Bluefy uyarısı', 'Bluefy' in await ev("document.querySelector('#sheet').textContent"))
        await btn('#sheet button[data-a=lzc]'); await pg.wait_for_timeout(200)
        ck('  bağlan denenince açıklayıcı uyarı (iPhone Safari → Bluefy)', any('Bluefy' in m for m in dlg), dlg)
        await ev(FAKE); await btn('#sheet button[data-a=lzc]'); await pg.wait_for_timeout(300)
        ck('yanıtsız yazma desteklenmese de otomatik gönderme komutu yazıldı, bağlandı', await ev("RK.LZ.state")=='bağlı' and await ev("window._glmWrites[0]")==[0xC0,0x55,0x02,0x01,0x00,0x1A], [await ev("RK.LZ.state"), await ev("window._glmWrites")])
        await ev("window._glmRaw([0xC0,0x55,0x10,0x06,0x08,0x02,0x08,0xE0,0x9C,0xE9,0x3F,0,0,0,0,0,0,0,0,0x06])"); await pg.wait_for_timeout(150)
        ck('gerçek GLM paketi (1.825 m) alındı', abs((await ev("RK.LZ.last") or 0)-1.825)<1e-4, await ev("RK.LZ.last"))
        await ev("window._glmRaw([0xC0,0x55,0x10,0x07,0x08,0x02,0x08,0x00,0x00,0x20,0x40,0,0,0,0,0,0,0,0,0])"); await pg.wait_for_timeout(150)
        ck('  4. baytı 06 olmayan durum paketi (ölçüm yeri değişimi vb.) ölçü sayılmadı', abs((await ev("RK.LZ.last") or 0)-1.825)<1e-4, await ev("RK.LZ.last"))
        txt = await ev("document.querySelector('#sheet').textContent")
        ck('  panelde gelen veri sayısı ve son paket görünüyor', '2 paket' in txt and 'C0 55 10' in txt, txt[-160:])
        for _ in range(3): await ev("window._glmRaw([0xC0,0x11,0x00,0x3A])")
        await ev("RK.commit()"); txt = await ev("document.querySelector('#sheet').textContent")
        ck('GLM 50-27 CG canlılık sinyali (C0 11 00 3A) ölçüm sayılmıyor, ayrı gösteriliyor; son paket ölçüm paketi kalıyor', '2 paket (+3 canlılık)' in txt and 'C0 55 10' in txt, txt[-200:])
        n0 = await ev("window._glmWrites.length"); await btn('#sheet button[data-a=lztr]'); await pg.wait_for_timeout(1000)
        w = await ev("window._glmWrites.slice(-2)")
        ck('📏 Uzaktan ölç: lazere iki kez ölç komutu (C0 56 01 00 1E) gitti', w==[[0xC0,0x56,0x01,0x00,0x1E]]*2, w)
        await ev("window._drop()"); await pg.wait_for_timeout(1800)
        ck('bağlantı kopunca kendiliğinden yeniden bağlandı', await ev("RK.LZ.state")=='bağlı' and await ev("window._conn")==2, [await ev("RK.LZ.state"), await ev("window._conn")])
        # onay gelmezse (sadece canlılık sinyali) komut yinelenir
        await ev("window._glmWrites=[]; RK.LZ.armed=false"); await ev("window._drop()"); await pg.wait_for_timeout(1500); await pg.wait_for_timeout(5600)
        w = await ev("window._glmWrites.filter(x=>x[1]===0x55).length")
        ck('lazer onay vermezse ölçüm gönderme komutu birkaç kez yinelendi', w>=3, w)
        ck('JS hatası yok', not errs, errs[:3]); await b.close()
    print('TOPLAM', sum(R), '/', len(R)); sys.exit(0 if all(R) else 1)
asyncio.run(main())
