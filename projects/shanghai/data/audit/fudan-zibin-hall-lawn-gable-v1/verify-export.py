"""Inspect actual pane depths, mouldings, open rail intervals, roof surface and crest."""
import argparse
import json
import math
from pathlib import Path
import runpy
import numpy as np
from shapely.geometry import Polygon

HERE=Path(__file__).absolute().parent
SOURCE=HERE.parents[2]/'source/precise/yangpu-fudan-zibin-hall-lawn-gable/source'
D=json.loads((SOURCE/'dimensions.json').read_bytes())
INSPECT=runpy.run_path(HERE.parent/'central-reserve-bank-changshu-front-v1/verify-export.py')['inspect']

def cases():
    result=[]
    def ray(name,origin,direction,length,allowed=None,limits=None):
        result.append(dict(name=name,origin=list(map(float,origin)),direction=list(map(float,direction)),length=length,
                           allowed=None if allowed is None else allowed if isinstance(allowed,list) else [allowed],range_m=limits))
    def front(name,x,z,mat,limits,y=-.26):
        ray(name,[x,y,z],[0,1,0],.7,mat,limits)
    for level in ('lower','attic'):
        for i,(x0,z0,x1,z1)in enumerate(D[level]):
            x=(x0+x1)/2;split=z0+(z1-z0)*(.36 if level=='attic'else .72)
            for col,along in enumerate([.27,.73]):
                for row,z in enumerate([(z0+split)/2,(split+z1)/2]):
                    front(f'{level} {i+1} pane {col+1} {row+1}',x0+(x1-x0)*along,z,['Deep green glazing','Reflected blue grey glass'],[.403,.418])
            front(f'{level} {i+1} meeting stile',x,(split+z1)/2,'Graphite sash paint',[.354,.370])
            front(f'{level} {i+1} transom',x0+(x1-x0)*.27,split,'Graphite sash paint',[.354,.370])
            front(f'{level} {i+1} jamb',x0+.036,z0+.86*(z1-z0),'Graphite sash paint',[.309,.325])
            front(f'{level} {i+1} sill',x,z0-.031,'Balcony warm grey coping',[.108,.123])
            # Aim behind the meeting stile from a lawn-side angle. At a seam this
            # may hit a pane, the stile or the continuous glazing bed behind it.
            z=z0+.81*(z1-z0)
            for dx in [-.038,.038]:
                ray(f'{level} {i+1} oblique seam {dx}',[x+dx-.163,-.24,z],[.48,1,0],.63,
                    ['Deep green glazing','Reflected blue grey glass','Graphite sash paint'],[.35,.51])
    for i,coords in enumerate(D['fields']):
        poly=Polygon(coords);sample=poly.representative_point()
        if i!=2:front('grey panel '+str(i+1),sample.x,sample.y,'Cool grey inset panel',[.238,.255])
    cx,peak=D['rake'][1]
    front('central two-tone pediment',cx,5.62,'Zibin Hall pale grey plaster',[.216,.239])
    for i,x in enumerate([D['rake'][0][0]+.35,-2.23,2.01,D['rake'][2][0]-.41]):
        front('tall pier '+str(i+1),x,1.71,'Whitened plaster band',[.120,.137])
    for i,x in enumerate([-4.,-.45,3.45]):
        front('projecting gable cornice '+str(i+1),x,3.0,'Whitened plaster band',[.036,.051])
    left,top,right=np.array(D['rake']);rail_y=-D['balcony_projection']+.1
    dies=[left[0]+.37,-2.16,2.02,right[0]-.37]
    for i,x in enumerate(dies):
        front('rail die '+str(i+1),x,.57,'Baluster limestone colour',[.084,.098],rail_y-.28)
    for i,(a,b)in enumerate(zip(dies,dies[1:])):
        clear=b-a-.43;count=round(clear/.28);pitch=clear/count
        for j in range(count):
            x=a+.215+(j+.5)*pitch
            ray(f'spindle {i+1}-{j+1}',[x,rail_y-.28,.59],[0,1,0],.55,'Baluster limestone colour',[.18,.23])
            if j<count-1:
                ray(f'open gap {i+1}-{j+1}',[x+pitch/2,rail_y-.26,.59],[0,1,0],.5)
        ray('handrail '+str(i+1),[(a+b)/2,rail_y,1.23],[0,0,-1],.6,'Balcony warm grey coping',[.238,.252])
    for i,(a,b)in enumerate([(left,top),(top,right)]):
        for j,k in enumerate([.15,.31,.56,.75,.91]):
            x,z=a*(1-k)+b*k
            ray(f'sloping tile {i+1}-{j+1}',[x,.73,z+.36],[0,0,-1],.6,['Old brown roof tile','Sunlit terracotta rib'],[.24,.31])
    ray('finial top',[cx,-.022,peak+.50],[0,0,-1],.60,'Balcony warm grey coping',[.125,.14])
    x0,z0,x1,z1=D['lower'][0]
    front('left casing projected in front of first jamb',x0+.036,(z0+z1)/2,'Grey enamel casing',[.10,.12],-.54)
    for i,row in enumerate(D['visible_grille_cases']):
        x0,z0,x1,z1=row['front_xz'];cx,cz=row['centre_xz']
        front('offset grille hub '+str(i+1),cx,cz,'Grey enamel casing',[.071,.078],-.54)
        front('pale casing '+str(i+1),x0+(x1-x0)*.17,cz,'Grey enamel casing',[.1,.12],-.54)
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for k in ('raw','full','lod','output'):p.add_argument(k,type=Path)
    q=p.parse_args();tests=cases()
    report={k:INSPECT(getattr(q,k),tests)for k in ('raw','full','lod')}
    q.output.write_text(json.dumps(report,ensure_ascii=False,separators=(',',':'))+'\n')
    assert all(v['passed']for v in report.values()),[(k,[c['name']for c in v['cases']if not c['passed']])for k,v in report.items()]
    print(len(tests),'physical checks per model')
