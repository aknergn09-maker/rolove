# YENİ CAD aşama 4: ölçü notları (nokta-nokta, noktadan dik, çizgiden çizgiye, dik ayak/dik boy + hizalama), lazer değeri, nokta adı, DXF OLCU/NOKTA, geometriyle birlikte gelme
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
        cdp=await ctx.new_cdp_session(pg)
        async def btn(a):
            r = await ev(f"(()=>{{const e=document.querySelector('button[data-a=\"{a}\"]'); if(!e) return null; const r=e.getBoundingClientRect(); return [r.left+r.width/2, r.top+r.height/2]}})()")
            if not r: return False
            await pg.touchscreen.tap(r[0], r[1]); await pg.wait_for_timeout(60); return True
        async def S(x,y): return await ev(f"CAD.w2s({x},{y})")
        async def wtap(x,y): s=await S(x,y); await pg.touchscreen.tap(s[0],s[1]); await pg.wait_for_timeout(60)
        async def path(pts,n=10):
            sp=[await S(*q) for q in pts]
            await cdp.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':sp[0][0],'y':sp[0][1]}]}); await pg.wait_for_timeout(40)
            for (x0,y0),(x1,y1) in zip(sp,sp[1:]):
                for k in range(1,n+1): await cdp.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{'x':x0+(x1-x0)*k/n,'y':y0+(y1-y0)*k/n}]}); await pg.wait_for_timeout(8)
            await cdp.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]}); await pg.wait_for_timeout(80)
        M=lambda: ev("JSON.parse(JSON.stringify(CAD.measList()))")
        await ev("""CAD.D={nid:10,ents:[{id:'r',t:'pl',p:[[0,0],[4,0],[4,3],[0,3]],c:true},{id:'k',t:'pl',p:[[2,1.5],[2.4,1.5],[2.4,1.9],[2,1.9]],c:true}],ops:[]};
          Object.assign(CAD.view,{s:50,ox:30,oy:330}); CAD.commit()""")
        await btn('fly:meas')
        ck('Ölçü grubu: nokta-nokta aktif, pencerede 5 tür + ad göster', await ev("CAD.S.tool")=='m_pp')
        await btn('t:m_pp')
        await ev("CAD.laserValue(5)")
        ck('  uç seçmeden gelen lazer değeri panelde bekliyor', await ev("!!document.querySelector('#mp .mval.pend')"))
        await wtap(0,0); await wtap(4,3)
        ck('  iki uç seçilince değer kutuya düştü (5.000)', (await ev("document.querySelector('#mp .mval').textContent"))=='5.000')
        await btn('mok'); m=await M()
        ck('  kaydedildi: nokta-nokta 5.000, çizim değişmedi', len(m)==1 and m[0]['k']=='m_pp' and m[0]['v']==5 and await ev("CAD.D.ents[0].p.length")==4)
        # noktadan dik: kolon köşesi → alt duvar (pline'ın tek kenarı)
        await btn('fly:meas'); await btn('t:m_pl'); await wtap(2,1.5); await wtap(1,0)
        await btn('mv:0'); await btn('mk:1'); await btn('mk:.'); await btn('mk:5'); await btn('mok'); m=await M()
        ck('noktadan dik: kolon köşesi→alt kenar, elle 1.5', m[-1]['k']=='m_pl' and m[-1]['v']==1.5 and near(m[-1]['pts'][1],(0,0)) and near(m[-1]['pts'][2],(4,0)), m[-1])
        # çizgiden çizgiye
        await btn('fly:meas'); await btn('t:m_ll'); await wtap(0,2.2); await wtap(4,2.2)
        await ev("CAD.laserValue(4.012)"); await btn('mok'); m=await M()
        ck('çizgiden çizgiye: sol↔sağ duvar, lazer 4.012', m[-1]['k']=='m_ll' and abs(m[-1]['v']-4.012)<1e-9 and m[-1]['src']=='laser', m[-1])
        # dik ayak / dik boy: köşe O, ayak duvar boyunca (kolon köşesinin hizası yakalanır), boy kolon köşesine
        await btn('fly:meas'); await btn('t:m_ab'); await wtap(0,0)
        await path([(2,1.5),(2.06,0.6),(2.06,-0.03)])
        q=await ev("JSON.parse(JSON.stringify(CAD.S.mq))")
        ck('dik ayak: ayak ucu kolon köşesinin dik hizasına oturdu (2,0)', len(q['picks'])==2 and near(q['picks'][1]['p'],(2,0)), q)
        await wtap(2,1.5)
        await ev("CAD.laserValue(2)"); await ev("CAD.laserValue(1.5)")
        ck('  lazer önce ayağı sonra boyu doldurdu', [await ev("[...document.querySelectorAll('#mp .mval')].map(e=>e.textContent).join(',')")]==['2.000,1.500'])
        await btn('mok'); m=await M()
        ck('  kaydedildi: ayak 2, boy 1.5, üç nokta', m[-1]['k']=='m_ab' and m[-1]['v']==2 and m[-1]['v2']==1.5 and near(m[-1]['pts'][2],(2,1.5)))
        # geri al: seçilen uç geri alınır
        await btn('fly:meas'); await btn('t:m_pp'); await wtap(0,3); await btn('undo')
        ck('ölçü sırasında geri al son seçilen ucu siler', await ev("CAD.S.mq")==None)
        # nokta adı
        await btn('fly:meas'); await btn('t:tag')
        await pg.fill('#nmIn','101'); await wtap(0,3); await wtap(1.3,3)
        N=await ev("JSON.parse(JSON.stringify(CAD.nameList()))")
        ck('nokta adı: başlangıç 101, köşe ve çizgi üstü, sormadan arttı', [n['n'] for n in N]==['101','102'] and near(N[1]['p'],(1.3,3)) and await ev("CAD.S.nameNext")=='103', N)
        await wtap(1.3,3); await pg.fill('#nmIn','12'); await ev("document.querySelector('#nmIn').dispatchEvent(new Event('change'))")
        ck('  var olan ada dokununca değiştirilebildi (12)', (await ev("CAD.nameList()[1].n"))=='12')
        # geometriyle birlikte gelme
        await btn('sec'); await wtap(3,3)
        sp=await S(2,3); tp=await S(2,3.5)
        await cdp.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':sp[0],'y':sp[1]}]})
        for k in range(1,11): await cdp.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{'x':sp[0],'y':sp[1]+(tp[1]-sp[1])*k/10}]})
        await cdp.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]}); await pg.wait_for_timeout(80)
        N=await ev("JSON.parse(JSON.stringify(CAD.nameList()))"); m=await M()
        ck('üst kenar kayınca adlar ve ölçü ucu da geldi', near(N[0]['p'],(0,3.5)) and near(N[1]['p'],(1.3,3.5)) and near(m[0]['pts'][1],(4,3.5)), [N, m[0]])
        # DXF
        dx=await ev("CAD.makeDXF()")
        ck('DXF: OLCU katmanı, NN/ND/CC/DA satırları, adlar 101 ve 12', all(x in dx for x in ['\r\nOLCU\r\n','NN ','ND ','CC ','DA ','\r\n101\r\n','\r\n12\r\n',' 4.012 L']))
        da=[l for l in dx.split('\r\n') if l.startswith('DA ')]
        ck('  dik ayak satırı: köşe, ayak ucu, kolon köşesi adı + iki değer', da and da[0].endswith('2.000 1.500 L'), da)
        # Seç ile ölçü seçip silme
        await btn('sec')
        await ev("CAD.S.sel.clear(); CAD.render()")
        await wtap(3.2,2.8)
        ck('Seç: ölçüye dokununca seçildi, düzenleme paneli', await ev("!!CAD.S.selMeas") and await ev("!!document.querySelector('button[data-a=mdel]')"))
        n0=len(await M()); await btn('mdel')
        ck('  ölçü silindi', len(await M())==n0-1)
        await btn('fly:meas'); await btn('tgn')
        ck('nokta adları gizlenebiliyor', await ev("CAD.S.showNames")==False)
        await btn('tgn'); await btn('sec'); await pg.screenshot(path=str(OUT/'c9.png'))
        ck('JS hatası yok', not errs, errs[:3]); await b.close()
    print('TOPLAM', sum(R), '/', len(R)); sys.exit(0 if all(R) else 1)
asyncio.run(main())
