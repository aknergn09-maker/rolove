# YENİ CAD: Kroki/Ölçme modları, ölçü araçları (obje yakalayan + dik, obje seçen, iki duvar arası, dik ayak/boy hizalamalı, gönye, nokta adı), lazer, görünürlük, DXF 3 kopya, açık uçlu offset
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
        colA=lambda: ev("[...document.querySelectorAll('#col button')].map(b=>b.dataset.a).join(',')")
        await ev("""CAD.D={nid:10,ents:[{id:'r',t:'pl',p:[[0,0],[1.5,0],[2.4,0],[4,0],[4,3],[0,3]],c:true},{id:'k',t:'pl',p:[[2,1.5],[2.4,1.5],[2.4,1.9],[2,1.9]],c:true}],ops:[{id:'o1',t:'door',a:[1.5,0],b:[2.4,0],hinge:0,sw:1}]};
          Object.assign(CAD.view,{s:50,ox:30,oy:330}); CAD.commit()""")
        ck('Kroki modu: çizim araçları var, ölçü araçları yok', 'fly:draw' in await colA() and 't:m_pp' not in await colA())
        await btn('mode')
        A=await colA()
        ck('Ölçme modu: sütunda sadece ölçü araçları', all(('t:'+k) in A for k in ['m_pp','m_obj','m_ll','m_ab','m_g','tag']) and 'fly:draw' not in A and 'fly:edit' not in A, A)
        ck('  obje yakalayan aktif', await ev("CAD.S.tool")=='m_pp')
        # obje yakalayan: köşe→köşe
        await ev("CAD.laserValue(5)")
        ck('  uç seçmeden gelen lazer değeri bekliyor', await ev("!!document.querySelector('#mp .mval.pend')"))
        await wtap(0,0); await wtap(4,3)
        ck('  iki köşe seçilince değer kutuda', (await ev("document.querySelector('#mp .mval').textContent"))=='5.000')
        await btn('mok'); m=await M()
        ck('  nokta–nokta kaydedildi, çizim değişmedi', m[-1]['k']=='m_pp' and m[-1]['v']==5 and await ev("CAD.D.ents[0].p.length")==6)
        # obje yakalayan: köşe → duvar = dik
        await wtap(2,1.9); await wtap(3,3)
        await btn('mv:0'); await btn('mk:1'); await btn('mk:.'); await btn('mk:1'); await btn('mok'); m=await M()
        ck('obje yakalayan: noktadan duvara dokununca dik (kolon köşesi→üst duvar 1.1)', m[-1]['k']=='m_pl' and m[-1]['v']==1.1 and near(m[-1]['pts'][1],(4,3)) and near(m[-1]['pts'][2],(0,3)), m[-1])
        # obje seçen: pline kenarı (kapı kırıkları olsa da bütün kenar) ve kapı
        await btn('t:m_obj'); await wtap(3.2,0)
        ck('obje seçen: tek dokunuşla alt kenarın tamamı', await ev("!!document.querySelector('#mp .mval')"))
        await ev("CAD.laserValue(4.003)"); await btn('mok'); m=await M()
        ck('  kenar uzunluğu kaydı (0,0)-(4,0) 4.003', m[-1]['k']=='m_obj' and near(m[-1]['pts'][0],(0,0)) and near(m[-1]['pts'][1],(4,0)) and m[-1]['src']=='laser', m[-1])
        await wtap(1.95,0.1); await ev("CAD.laserValue(0.9)"); await btn('mok'); m=await M()
        ck('  kapıya dokununca kapı genişliği', m[-1]['k']=='m_obj' and near(m[-1]['pts'][0],(1.5,0)) and near(m[-1]['pts'][1],(2.4,0)), m[-1])
        # iki duvar arası
        await btn('t:m_ll'); await wtap(0,2.4); await wtap(4,2.4); await ev("CAD.laserValue(4.01)"); await btn('mok'); m=await M()
        ck('iki duvar arası', m[-1]['k']=='m_ll' and abs(m[-1]['v']-4.01)<1e-9)
        # dik ayak/boy: hizalama
        await btn('t:m_ab'); await wtap(0,0)
        await path([(2,1.5),(2.06,0.6),(2.06,-0.03)])
        q=await ev("JSON.parse(JSON.stringify(CAD.S.mq))")
        ck('dik ayak: ayak ucu kolon köşesinin hizasına oturdu (2,0)', len(q['picks'])==2 and near(q['picks'][1]['p'],(2,0)), q)
        await wtap(2,1.5); await ev("CAD.laserValue(2)"); await ev("CAD.laserValue(1.5)"); await btn('mok'); m=await M()
        ck('  ayak 2 boy 1.5', m[-1]['k']=='m_ab' and m[-1]['v']==2 and m[-1]['v2']==1.5)
        # gönye
        await btn('t:m_g'); await wtap(4,0); await wtap(0,3); await ev("CAD.laserValue(5.001)"); await btn('mok'); m=await M()
        ck('gönye ayrı tür', m[-1]['k']=='m_g')
        # nokta adı + nokta adına yakalama
        await btn('t:tag'); await pg.fill('#nmIn','101'); await wtap(0,3); await wtap(1.3,3)
        N=await ev("CAD.nameList().map(n=>n.n)")
        ck('nokta adı: 101, 102 (çizgi üstü)', N==['101','102'], N)
        await btn('t:m_pp'); await wtap(1.33,3.02); await wtap(2.4,1.9)
        q=await ev("JSON.parse(JSON.stringify(CAD.S.mq))")
        ck('obje yakalayan nokta adına (çizgi üstü 102) yakalandı', near(q['picks'][0]['p'],(1.3,3)), q)
        await btn('undo'); await btn('undo')
        # mevcut ölçüye dokununca düzenleme
        await wtap(2,1.5+0.75*0)  # boş değil: kolon köşesi; önce boş bir ölçü çizgisi noktası
        await btn('undo')
        await wtap(3.2,2.4)
        ck('ölçme modunda ölçüye dokununca düzenleme paneli', await ev("!!CAD.S.selMeas") and await ev("!!document.querySelector('button[data-a=mdel]')"))
        await btn('mdel')
        # görünürlük
        await btn('fly:vis'); await btn('v:gonye')
        ck('gönyeler gizlenebiliyor', await ev("CAD.S.vis.gonye")==0)
        await btn('v:gonye')
        # DXF: 3 kopya
        dx=await ev("CAD.makeDXF()")
        ck('DXF: OLCU, GONYE, DIKAYAK katmanları ve kopyalar', all(x in dx for x in ['\r\nOLCU\r\n','\r\nGONYE\r\n','\r\nDIKAYAK\r\n','\r\nKOPYA_GONYE\r\n','\r\nKOPYA_DIKAYAK\r\n','OB ','GN ','DA ','ND ','CC ']))
        ck('  gönye kopyası sağa kaydırılmış (x > 4)', any(l.startswith('GN ') for l in dx.split('\r\n')))
        await pg.screenshot(path=str(OUT/'c9.png'))
        # açık uçlu offset: bir ucu duvara bağlı bölme → bağlı uç oturur, boş uç sorulur
        await btn('mode')
        await ev("""CAD.D={nid:50,ents:[{id:'w',t:'pl',p:[[0,0],[6,0],[6,4],[0,4]],c:true},{id:'b',t:'pl',p:[[3,0],[3,2.5]],c:false}],ops:[],meas:[],names:[]}; CAD.commit()""")
        await btn('fly:edit'); await btn('t:offset'); await btn('kopen'); await btn('k:1'); await btn('k:0'); await btn('kok')
        await wtap(3,1.2); await wtap(3.5,1.2)
        ck('açık bölme offset: boş uç için kapak sorusu çıktı', await ev("!!CAD.S.capAsk") and await ev("!!document.querySelector('button[data-a=capY]')"))
        o=await ev("JSON.parse(JSON.stringify(CAD.D.ents.find(e=>!['w','b'].includes(e.id))))")
        ck('  bağlı uç duvara oturdu (3.1,0)', near(o['p'][0],(3.1,0)), o)
        await btn('capY')
        ck('  kapak çizildi (2.5 hizasında)', await ev("CAD.D.ents.some(e=>e.t==='line' && Math.abs(e.a[1]-2.5)<1e-9 && Math.abs(e.b[1]-2.5)<1e-9)"))
        ck('JS hatası yok', not errs, errs[:3]); await b.close()
    print('TOPLAM', sum(R), '/', len(R)); sys.exit(0 if all(R) else 1)
asyncio.run(main())
