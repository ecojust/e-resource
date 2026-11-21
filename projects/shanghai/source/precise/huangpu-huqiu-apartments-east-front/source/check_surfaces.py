"""Measure the real materials of the two projecting wings and the recessed entrance."""
from pathlib import Path
import json
import sys
import numpy as np

SOURCE = Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE))
import build_model
from photo_architecture import Builder, Facade
from street_front import EDGES, PALETTE, add_building, GLASS, FRAME, BRICK, STONE, PLASTER, COPING, UPPER_SILLS



def first(triangles, materials, origin, direction):
    edge1 = triangles[:,1]-triangles[:,0]
    edge2 = triangles[:,2]-triangles[:,0]
    p = np.cross(np.broadcast_to(direction,edge2.shape),edge2)
    det = np.einsum('ij,ij->i',edge1,p)
    inverse = np.zeros_like(det)
    good = abs(det)>1e-9
    inverse[good] = 1/det[good]
    t = origin-triangles[:,0]
    u = np.einsum('ij,ij->i',t,p)*inverse
    q = np.cross(t,edge1)
    v = (q@direction)*inverse
    distance=np.einsum('ij,ij->i',edge2,q)*inverse
    hits=np.where(good&(u>=-1e-10)&(v>=-1e-10)&(u+v<=1+1e-10)&(distance>0))[0]
    if not len(hits):return None,None
    at=hits[np.argmin(distance[hits])]
    return materials[at],float(distance[at])


def run(distant):
    builder=Builder(PALETTE)
    add_building(builder,distant)
    arrays=[];materials=[]
    for part in builder.parts:
        indices=np.array(part['triangles'])
        arrays.append(np.array(part['vertices'])[indices])
        materials.extend([part['material']]*len(indices))
    return check_triangles(np.concatenate(arrays), materials, distant)


def check_triangles(triangles, materials, distant):
    results=[]
    for i,(a,b) in enumerate(zip(EDGES,EDGES[1:])):
        f=Facade(None,a,b)
        count=3 if i in (0,2,5) else 1
        inset=.66 if count==3 else (.20 if f.length>2.15 else .15)
        step=(f.length-2*inset)/count
        centers=[-f.length/2+inset+(j+.5)*step for j in range(count)]
        probes=[]
        for floor,z in enumerate(UPPER_SILLS):
            h=2.08 if floor<3 else 1.75
            for x in centers:
                probes.append((f'第{floor+2}层钢窗玻璃 {x:.2f}',x+.17,z+.51,GLASS))
                probes.append((f'第{floor+2}层窗横料 {x:.2f}',x+.17,z+.74*h,FRAME))
                if floor<3:probes.append((f'第{floor+2}层窗台下红砖 {x:.2f}',x+.09,z-.41,BRICK))
        probes += [('窗顶的浅色檐带',0,17.40,PLASTER),('顶端深色压边',0,18.47,COPING)]
        if i==2:
            probes += [
                ('south shaft', -2.045, 1.66, 'Huqiu pale worn stone mouldings'),
                ('north shaft', 2.045, 1.66, 'Huqiu pale worn stone mouldings'),
                ('south square foot', -2.285, 0.082, 'Huqiu grey threshold'),
                ('north abacus', 2.34, 3.925, 'Huqiu pale worn stone mouldings'),
                ('three glazing sections, southern', -1.204, 2.62, 'Huqiu smoky blue entrance glass'),
                ('middle overhead glazing', 0.235, 2.62, 'Huqiu smoky blue entrance glass'),
                ('three glazing sections, northern', 1.204, 2.62, 'Huqiu smoky blue entrance glass'),
                ('upper glazing mullion', 0.144, 2.65, 'Huqiu dark umber joinery'),
                ('south side light', -3.14, 1.12, 'Huqiu smoky blue entrance glass'),
                ('north side light', 3.13, 1.14, 'Huqiu smoky blue entrance glass'),
                ('south brown upper sash', -3.12, 2.56, 'Huqiu brown upper side light'),
                ('doorway shadow', -0.391, 1.2, 'Huqiu unlit door reveal'),
                ('right-hand open leaf glass', 0.35, 1.43, 'Huqiu smoky blue entrance glass'),
                ('timber transom', 0.0, 1.85, 'Huqiu dark umber joinery'),
                ('central crest', 0.02, 4.63, 'Huqiu recessed inscription stone'),
                ('cornice cap', -2.53, 4.286, 'Huqiu pale worn stone mouldings'),
                ('threshold', -0.31, 0.03, 'Huqiu grey threshold'),
                ('门额外侧南端上部砖墙', -3.80, 4.56, BRICK),
                ('门额与南窗间的背衬', -1.35, 4.56, BRICK),
                ('门额与北窗间的背衬', 1.35, 4.56, BRICK),
                ('门额外侧北端上部砖墙', 3.80, 4.56, BRICK),
                ('green street number plate', -1.09, 1.9, 'Huqiu green street number enamel'),
                ('first digit in 131', -1.02585, 1.8729, 'Huqiu ivory street number strokes'),
                ('虎', -1.1936821100325123, 3.2242362, 'Huqiu burnished inscription'),
                ('丘', -0.38388419695380877, 3.23121348, 'Huqiu burnished inscription'),
                ('公', 0.4236236823253633, 3.18105876, 'Huqiu burnished inscription'),
                ('寓', 1.1169876717791412, 3.18644628, 'Huqiu burnished inscription'),
            ]
        else:
            probes += [('底层窗与腰线之间的抹灰',.08,3.72,PLASTER),('底层水泥窗间墙',f.length*.47,2.40,PLASTER)]
        if i==5:probes.append(('露出的第六层北翼窗玻璃',-.13,19.50,GLASS))
        for name,x,z,expected in probes:
            hit,depth=first(triangles,materials,f.point(x,z,1.05),-f.n)
            results.append({'face':i,'detail':name,'expected':expected,'hit':hit,'distance_m':depth})
    if any(row['hit']!=row['expected'] for row in results):
        raise RuntimeError([r for r in results if r['hit']!=r['expected']])
    return {'distant':distant,'triangles':len(triangles),'rays':results}


if __name__=='__main__':
    report=[run(False),run(True)]
    print(json.dumps(report,ensure_ascii=False,indent=2))
