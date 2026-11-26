# sentetik iş: gerçek bina (UTM, 16° dönük, bir köşe 88.5°, kapı) → telefonda bozuk çizilmiş kroki + gerçek lazer ölçüleri → DXF + NCN
import asyncio, pathlib, math, json
from playwright.async_api import async_playwright
ROOT = pathlib.Path(__file__).resolve().parent.parent; OUT = ROOT/'test'/'out'; OUT.mkdir(exist_ok=True)
th=math.radians(16); O=(523062.0,4097380.0)
def T(p): x,y=p; return [O[0]+x*math.cos(th)-y*math.sin(th), O[1]+x*math.sin(th)+y*math.cos(th)]
true={'A':(0,0),'B':(5.0,0),'C':(5.08,3.9),'D':(0,4.0),'K':(2.2,1.6),'F':(2.2,0),'G':(3.0,0),'H':(3.9,0)}
d=lambda a,b: math.dist(true[a],true[b])
sk={'A':[0,0],'B':[4.6,0],'C':[4.6,3.7],'D':[0,3.7],'K':[2.0,1.5],'F':[2.0,0],'G':[2.8,0],'H':[3.6,0]}
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(args=['--no-sandbox']); pg=await b.new_page()
        await pg.goto((ROOT/'cad.html').as_uri()); await pg.evaluate("localStorage.clear()"); await pg.reload(); await pg.wait_for_timeout(300)
        m=lambda i,k,pts,v,v2=None: dict(id=i,k=k,pts=[sk[x] for x in pts],v=v,src='laser',**({'v2':v2} if v2 is not None else {}))
        D={'nid':10,'ents':[{'id':'r','t':'pl','p':[sk['A'],sk['F'],sk['G'],sk['H'],sk['B'],sk['C'],sk['D']],'c':True},{'id':'k','t':'pl','p':[sk['K'],[2.4,1.5],[2.4,1.9],[2.0,1.9]],'c':True}],
           'ops':[{'id':'o1','t':'door','a':sk['G'],'b':sk['H'],'hinge':0,'sw':1,'th':0}],
           'meas':[m('m1','m_obj',['A','B'],d('A','B')),m('m2','m_obj',['B','C'],d('B','C')),m('m3','m_obj',['C','D'],d('C','D')),m('m4','m_obj',['D','A'],d('D','A')),
                   m('m5','m_g',['A','C'],d('A','C')),m('m6','m_g',['B','D'],d('B','D')),m('m7','m_ab',['A','F','K'],d('A','F'),d('F','K'))],
           'names':[{'id':'n1','n':'101','p':sk['A']},{'id':'n2','n':'102','p':sk['B']}]}
        await pg.evaluate("d=>{CAD.D=d; CAD.commit()}", D)
        open(OUT/'g_kroki.dxf','w').write(await pg.evaluate("CAD.makeDXF()"))
        names=await pg.evaluate("Object.fromEntries(pointNames().map(t=>[t.p.join(','),t.name]))")
        await b.close()
    skmap={k:names[','.join(str(int(v)) if float(v).is_integer() else str(v) for v in sk[k])] for k in ['A','B','C','D','K','F','G','H']}
    a,bb=T(true['A']),T(true['B'])
    open(OUT/'g_total.ncn','w').write(f'101     {a[0]:.4f}    {a[1]:.4f}       0.00 0 "" "" ""\n102     {bb[0]:.4f}    {bb[1]:.4f}       0.00 0 "" "" ""\n103     {a[0]+20:.4f}    {a[1]+5:.4f}       0.00 0 "" "" ""\n')
    json.dump({k:T(v) for k,v in true.items()},open(OUT/'g_true.json','w')); json.dump(skmap,open(OUT/'g_skmap.json','w'))
asyncio.run(main())
