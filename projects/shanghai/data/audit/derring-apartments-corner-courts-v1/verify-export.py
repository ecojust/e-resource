"""Test the actual twin windows, cut entrance, upper loggia, covered courts and roof houses."""
import argparse,json,math,runpy
from pathlib import Path
import numpy as np
from shapely.geometry import Point,Polygon

HERE=Path(__file__).resolve().parent
S=HERE.parents[2]/'source/precise/hongkou-derring-apartments-corner-courts/source'
inspect=runpy.run_path(HERE.parent/'central-reserve-bank-changshu-front-v1/verify-export.py')['inspect']
plan=json.loads((S/'plan.json').read_bytes());vertices=np.asarray(plan['outline_m'])
BASE='Pale cut-stone base'
CAP='Warm buff mouldings'
BRICK='Taishan brown facing brick'
ROUGH='Ochre roughcast upper walls'
PANEL='Ivory spandrel'
FRAME='Painted dark steel'
GLASS='Grey-blue glazing'
METAL='Muted grey sheet metal'

def cases():
    records=[]
    def probe(name,orig,dire,mat,interval,length=2.2):
        materials=None if mat is None else [mat] if isinstance(mat,str) else mat
        records.append(dict(name=name,origin=list(map(float,orig)),direction=list(map(float,dire)),allowed=materials,range_m=interval,length=length))
    def front(a,b,x,z,mat,iv,label,offset=.75):
        u=(vertices[b]-vertices[a]);u=u/np.linalg.norm(u);n=np.array([u[1],-u[0]])
        m=(vertices[a]+vertices[b])/2+u*x+n*offset
        probe(label,[*m,z],[-n[0],-n[1],0.],mat,iv)
    for a,b,count,label in [(9,10,19,'Jiangxi'),(0,1,18,'Chongming'),(1,2,2,'Southeast'),
                             (8,9,3,'Northwest'),(10,0,2,'Southwest')]:
        length=np.linalg.norm(vertices[b]-vertices[a]);half=length/2
        xs=np.linspace(-half+1.64,half-1.64,count) if count>3 else [-.84,.84] if count==2 else [-2.24,0.,2.24]
        for j,x in enumerate(xs):
            for k,(s,h) in enumerate([(4.95,6.48),(7.74,9.18),(10.74,12.27),(13.69,15.33)]):
                # .16 m avoids both the full third-width and distant half-width bars.
                front(a,b,x+.16,s+.27,GLASS,[1.007,1.025],f'{label} bay {j+1} level {k+2} glazing')
                if j in (0,count-1) and k<3:front(a,b,x+.19,(h+[7.74,10.74,13.69][k])/2,PANEL,[.613,.631],f'{label} edge {j+1} spandrel {k+1}')
            if a==10:continue
            front(a,b,x+.16,18.42,GLASS,[1.007,1.025],f'{label} sixth-storey glass {j+1}')
        if a==10:
            for x in [-.785,.785]:
                front(a,b,x,.98,GLASS,[1.047,1.063],f'Main door {x}')
                front(a,b,x,3.41,BASE,[.708,.724],f'Blind door tympanum {x}')
        if count<4:
            for x in [-half+.22,half-.22]:
                front(a,b,x,10.12,[BRICK,ROUGH],[.52,.77],f'{label} outer brick pier {x:.2f}')
    for x in (-.72,.72):
        front(10,0,x,17.94,GLASS,[1.592,1.615],f'Loggia arch deep glazing {x}')
    for x in (-1.43,0,1.43):
        front(10,0,x,16.81,PANEL,[.34,.36],f'Projecting balustrade pier {x}',1.4)
    for hole,poly in enumerate(plan['covered_courts_m']):
        shape=Polygon(poly);centre=shape.centroid
        for dx,dy in [(0,0),(.37,.22),(-.41,-.48)]:
            pt=[centre.x+dx,centre.y+dy];assert shape.covers(Point(pt))
            probe(f'Court {hole+1} opaque cover ({dx},{dy})',[*pt,23.0],[0,0,-1],['Pale green courtyard cover',METAL],[4.70,4.78],6.0)
    for entry in json.loads((S/'roof-houses.json').read_bytes()):
        visible=Polygon(entry['outline_m']).intersection(Polygon(plan['outline_m']).buffer(-.30,join_style=2))
        point=visible.buffer(-.12,join_style=2).representative_point();h=21.41+entry['height_estimate_m']+.073
        probe(entry['name']+' upper face',[point.x,point.y,h+.58],[0,0,-1],['Weathered roof slab',METAL],[.575,.587],1.0)
    for x,y in ((45,10),(-36,0),(0,38)):
        probe('Outside historic footprint '+str((x,y)),[x,y,26.],[0,0,-1],None,None,27.0)
    return records

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for k in ('raw','full','lod','output'):p.add_argument(k,type=Path)
    o=p.parse_args();rows={r:inspect(getattr(o,r),cases()) for r in ('raw','full','lod')}
    o.output.write_text(json.dumps(rows,ensure_ascii=False,indent=1)+'\n')
    for r,s in rows.items():print(r,len(s['cases']),[(v['name'],v['first_hit'])for v in s['cases']if not v['passed']])
    raise SystemExit(int(not all(s['passed'] for s in rows.values())))
