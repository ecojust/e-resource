"""Four historic inscription fields, the narrow pale tablet and adjacent bonded brick."""
from pathlib import Path
import json
import numpy as np
from shapely.geometry import box, Polygon
from profile_tools import BRICK,cb,slab,bricks_uv
BASE='Mortar of the historic brickwork';BOARD='Pale name tablet';INK='Brush lettering';FADED='Lighter ink of the third character';EDGE='Narrow edge shadow'
colors={BRICK:(255,255,255),BASE:(123,111,99),BOARD:(224,217,199),INK:(61,55,49),FADED:(99,93,84),EDGE:(131,122,108)}
PALETTE={k:{'color':[(v/255)**2.2 for v in col],'roughness':.91} for k,col in colors.items()}
PALETTE[BRICK]['texture']=str(Path(__file__).with_name('finish.png'))
OUTLINES=json.loads(Path(__file__).with_name('inscription-outlines.json').read_bytes())['ink_fields']
BOTTOM=.154;TOP=BOTTOM+.48
def fields(lod=False):
    def ring(a):return [(-1+2*x,TOP-.48*y) for x,y in a]
    for item in OUTLINES:
        geom=[]
        for row in item['contours']:
            q=Polygon(ring(row['outer']),[ring(v) for v in row['holes']]).buffer(0)
            if lod:q=q.simplify(.0038,preserve_topology=True)
            geom.extend(p for p in getattr(q,'geoms',[q]) if p.geom_type=='Polygon' and p.area>.000005)
        yield item['label'],geom
def model(b,lod=False):
    wall=box(-1.21,0,1.21,.80);panel=box(-1,BOTTOM,1,TOP)
    cb(b,-1.21,1.21,.048,.15,0,.80,BASE,'Mortar backing behind the narrow sample')
    step=.237;joint=.007
    for row in range(11):
        z=row*.075
        for j in range(12):
            x=-1.43+(row%2)*step/2+j*step
            brick=box(x+joint/2,z+joint/2,x+step-joint/2,z+.075-joint/2).intersection(wall).difference(panel)
            slab(b,brick,.025,.055,BRICK,'Staggered facing brick')
    cb(b,-1.009,1.009,.009,.075,BOTTOM-.006,TOP+.006,EDGE,'Thin shadow at the junction with the wall')
    cb(b,-1,1,-.012,.028,BOTTOM,TOP,BOARD,'Pale tablet carrying four historic characters')
    for label,polys in fields(lod):
        for poly in polys:slab(b,poly,-.0135,-.0119,FADED if label=='童' else INK,'Archival lettering '+label)
    if lod:
        for part in b.parts:
            if part['material']!=BRICK:continue
            vertices=np.asarray(part['vertices'],dtype=float)
            def visible_face(triangle):
                a,c,d=vertices[np.asarray(triangle)]
                return np.cross(c-a,d-a)[1]<-1.e-9
            part['triangles']=[tri for tri in part['triangles'] if visible_face(tri)]
    bricks_uv(b)
