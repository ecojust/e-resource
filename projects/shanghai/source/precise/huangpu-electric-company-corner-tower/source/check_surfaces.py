"""Cast rays from both streets and the junction through the Art Deco tower surfaces."""
from pathlib import Path
import json
import sys
import numpy as np

SOURCE = Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE))
import build_model
from photo_architecture import Builder, Facade
from tower import EDGES, PALETTE, add_building, GLASS, STONE, IRON, BRICK, GRANITE, MARBLE, BRONZE, HIGHLIGHT, LAMP, BASE, SPACING


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
        points = []
        columns = [0] if i == 1 else [-1.19,0,1.19]
        for floor in range(5):
            z = BASE + .14 + floor*SPACING
            for x in columns:
                points.append((f'floor {floor+2} glass {x:+.2f}', x+.17, z+.79, GLASS))
                points.append((f'floor {floor+2} transom {x:+.2f}', x+.17, z+1.91*.73, IRON))
                if floor<4:
                    points.append((f'floor {floor+2} spandrel {x:+.2f}', x+.12, z+2.55, IRON))
        if i==1:
            points += [('central tower bricks',1.52,12.2,BRICK),('granite at street',2.85,1.86,GRANITE),
                       ('polished portal reveal',1.55,2.90,MARBLE),('left lantern',-2.30,2.71,LAMP),
                       ('right lantern',2.30,2.76,LAMP),('shield on gate',.04,3.73,HIGHLIGHT),
                       ('transom iron grille',.352,3.68,BRONZE),('bronze leaf meeting stile',.028,1.67,BRONZE),
                       ('crown stone drop',.04,22.08,STONE),('attic brick pilaster',.68,25.18,BRICK),
                       ('attic central plaque',.14,25.21,STONE),('flag mast',.004,28.40,BRONZE)]
            # Compare the open areas and the cast motifs to the two separate door photos.
            for leaf, label, u, v, material in [
                    (-.685,'hammer head',12,40,BRONZE),(-.685,'raised hammer arm',73.1,15.1,BRONZE),
                    (-.685,'open space below hammer',25,40,GLASS),(-.685,'open space left of leg',14,58,GLASS),
                    (.685,'bent knee',39,66,BRONZE),(.685,'arm turned to sun',47,39,BRONZE),
                    (.685,'solar disk',9,12,BRONZE),(.685,'open space beside bent leg',84,65,GLASS)]:
                points.append((label, leaf+(u-50)*.0066, 2.32+(50-v)*.0081, material))
        else:
            points += [('stone ground facade',f.length*.44,2.85,GRANITE),('ground-floor glazing',.30,2.10,GLASS),
                       ('left brick pilaster',-2.35,12.50,BRICK),('side crown middle stone',.12,22.29,STONE)]
        for label,x,z,expected in points:
            hit,depth=first(triangles,materials,f.point(x,z,4.0),-f.n)
            results.append({'face':i,'detail':label,'hit':hit,'expected':expected,'distance_m':depth})
    if any(row['hit']!=row['expected'] for row in results):
        raise RuntimeError([r for r in results if r['hit']!=r['expected']])
    return {'distant':distant,'triangles':len(triangles),'rays':results}


if __name__=='__main__':
    report=[run(False),run(True)]
    print(json.dumps(report,ensure_ascii=False,indent=2))
