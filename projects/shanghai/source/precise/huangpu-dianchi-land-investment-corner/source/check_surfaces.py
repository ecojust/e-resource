"""Cast rays from both streets and the junction through the authored surfaces."""
from pathlib import Path
import json
import sys
import numpy as np

SOURCE = Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE))
import build_model
from photo_architecture import Builder, Facade
from corner import EDGES, PALETTE, add_building, GLASS, WOOD, STONE, IRON, BRICK, RED, ROOF


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
    hits=np.where(good&(u>=0)&(v>=0)&(u+v<=1)&(distance>0))[0]
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
        if i==1:
            points=[('corner attic pane',.26,15.14,GLASS),('corner attic pier',1.37,15.09,BRICK),
                    ('upper French window',.34,12.42,GLASS),('middle French window',.35,8.62,GLASS),
                    ('lower French window',.33,5.27,GLASS),('middle lintel',.61,9.92,STONE),
                    ('window keystone',.02,9.92,STONE),('attic coping',.25,16.26,STONE)]
        else:
            points=[('attic arch pane',.38,15.48,GLASS),('red attic wall',1.50,14.96,BRICK),
                    ('left middle sash',-1.10,8.46,GLASS),('right middle sash',1.10,8.46,GLASS),
                    ('stone middle mullion',.005,8.65,STONE),('curve above window',.13,10.57,STONE),
                    ('lower arched sash',-.63,5.40,GLASS),('upper sash',1.10,12.00,GLASS)]
        points += [('balcony rail',.04,4.28,IRON),('balcony stone slab',.3,3.44,STONE),
                   ('shop glass',.32,1.46,GLASS),('cornice',.41,13.95,STONE)]
        for label,x,z,expected in points:
            hit,depth=first(triangles,materials,f.point(x,z,4.0),-f.n)
            results.append({'face':i,'detail':label,'hit':hit,'expected':expected,'distance_m':depth})
    if any(row['hit']!=row['expected'] for row in results):
        raise RuntimeError([r for r in results if r['hit']!=r['expected']])
    return {'distant':distant,'triangles':len(triangles),'rays':results}


if __name__=='__main__':
    report=[run(False),run(True)]
    print(json.dumps(report,ensure_ascii=False,indent=2))
