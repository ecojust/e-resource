"""Read the three serialized meshes and intersect rays with windows, guards, door bays, tiles and the open sky."""
from pathlib import Path
import json,runpy,sys
import numpy as np

HERE=Path(__file__).resolve().parent
inspect=runpy.run_path(HERE.parent/'central-reserve-bank-changshu-front-v1/verify-export.py')['inspect']
GLASS=['Grey garden window reflection','Green garden window reflection','Blue smoke garden window']
IRON='Oxblood balcony wood'; STUCCO='Warm ochre garden roughcast'; WOOD='Dark olive timber casement'
TILES=['Sienna clay roof tile','Smoke dark clay roof tile','Old russet roof tile','Warm fired clay roof tile','Dark clay bedding']
def cases():
    rows=[]
    def ray(name,org,direction,allowed,interval=None,maximum=7.):
        rows.append(dict(name=name,origin=org,direction=direction,length=maximum,allowed=allowed,range_m=interval))
    def front(name,u,v,materials,interval=None):
        ray(name,[(u-267)*.018,-1.5,(358-v)*.018],[0.,1.,0.],materials,interval)
    for name,cols,ys in [('west',(187,210),(108,119,136)),('east',(312,335),(96,111,125))]:
        for u in cols:
            for v in ys: front(f'{name} casement glass {u}/{v}',u,v,GLASS,[1.631,1.637])
    for n,u,v in [('west',199,106),('east',325,101)]:
        front(n+' vertical meeting stile',u,v,[WOOD],[1.572,1.582])
    for label,l,r,vt,vt2,vb,vb2 in [('west',153,239,147,142,168,163),('east',286,373,136,130,157,151)]:
        for i,a in enumerate((.12,.28,.43,.58,.74,.89)):
            u=l+(r-l)*a;v=(1-a)*vt+a*vt2;v2=(1-a)*vb+a*vb2
            front(f'{label} guard handrail {i+1}',u,v,[IRON],[1.072,1.091])
            front(f'{label} guard lower rail {i+1}',u,v2,[IRON],[1.082,1.095])
        for i,a in enumerate((.19,.35,.51,.67,.83)):
            u=l+(r-l)*a;v=(vt+vb)*(1-a)/2+(vt2+vb2)*a/2
            front(f'{label} upright {i+1}',u,v,[IRON],[1.095,1.124])
    for u,v in [(239,23),(272,47),(224,54),(268,107),(274,139),(255,197),(154,188),(386,173),(387,113)]:
        front(f'ochre roughcast {u}/{v}',u,v,[STUCCO],[1.49,1.509])
    for u,v,m in [(178.3,285,'Aomen narrow door glass'),(209,286,'Aomen entry worn oxblood panel'),(200,336,'Aomen entry worn oxblood panel'),(308,301,'Aomen entry painted oxblood timber'),(329,300,'Aomen open passage shadow'),(356,312,'Aomen entry worn oxblood panel')]:
        front(f'paired entry {u}/{v}',u,v,[m])
    for y in [.35,1.05,1.68]:
        for xx in [-2.19,-1.65,-1.22,-.87,-.43,.43,.9,1.45,1.90,2.48]:
            ray(f'tile plane {xx}/{y}',[xx,y,9.1],[0.,0.,-1.],TILES,maximum=7.5)
    for u,v in [(111,55),(125,56),(105,75),(405,25),(420,37),(423,51)]:
        front(f'open air at sloping roof edge {u}/{v}',u,v,None)
    return rows

if __name__=='__main__':
    args=list(map(Path,sys.argv[1:]));roles=['raw','full','lod'] if len(args)==4 else ['model']
    if len(args)!=len(roles)+1:raise SystemExit('Supply one or three meshes followed by the output JSON')
    results={k:inspect(f,cases()) for k,f in zip(roles,args)}
    args[-1].write_text(json.dumps(results,ensure_ascii=False,separators=(',',':'))+'\n')
    for key,q in results.items():
        print(key,len(q['cases']),[(r['name'],r['first_hit'] and (r['first_hit']['material'],r['first_hit'].get('distance')))for r in q['cases'] if not r['passed']])
    sys.exit(int(not all(r['passed'] for r in results.values())))
