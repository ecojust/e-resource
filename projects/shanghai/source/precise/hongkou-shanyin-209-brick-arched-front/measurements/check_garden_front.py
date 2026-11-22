"""Measure the exported garden-front section, tile surfaces, recesses and exposed masonry."""
import json,sys
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(HERE.parents[1]/'xuhui-pathe-records-office/measurements/city-contact'),str(HERE.parent/'source')]
from glb_triangles import SerialScene
from frontage import PLASTER,RED,SOFFIT,STONE,TRIM,SILL,PLANK,DARK,point
from garden_fittings import IRON
from ground_arcade import RED as ARCADE_BRICK
from tiled_roof import BED,CLAYS,RIDGE,ROLL

def check(mesh):
    layout=json.loads((HERE/'garden-front-layout.json').read_bytes())
    scene=SerialScene(mesh);hits=[]
    def probe(label,origin,direction,length,allowed,depth=None):
        allowed=[allowed] if isinstance(allowed,str) else allowed
        observed=scene.ray(origin,direction,length)
        material=observed['material'] if observed else None
        dist=observed['distance_m'] if observed else None
        ok=material in allowed and (depth is None or dist is not None and depth[0]<=dist<=depth[1])
        hits.append(dict(feature=label,origin=np.asarray(origin).tolist(),direction=direction,first_material=material,
                         expected=allowed,distance=dist,expected_distance=depth,passed=ok))
    e=layout['eave_y'];ze=layout['eave_z'];hx,hy,hz=layout['hip_end'];slope=(hz-ze)/(hy-e)
    for x in [-4.11,-3.36,-2.53,-1.81,-1.27,-.50,.27,.89,1.46,2.46,3.14,3.83,4.49]:
        for y in [-.71,-.27]:
            z=ze+slope*(y-e)
            probe('Sloping tile face above the eaves',[x,y,z+1],[0,0,-1],1.2,[*CLAYS,ROLL,BED],[.84,1.001])
        probe('Painted fascia at eaves',[x,e-.60,ze-.07],[0,1,0],.85,TRIM,[.569,.571])
        probe('Underside of projecting eave',[x,-.55,ze-.65],[0,0,1],.75,SOFFIT,[.459,.461])
    for v,mat in [(462,RED),(773,RED),(764,STONE)]:
        for u in [315,430,563,689,800,927]:
            x,_,z=point(layout,u,v)
            probe('Front masonry and sill material',[x,-.7,z],[0,1,0],1.,mat)
    for u in [315,563,800]:
        x,_,z=point(layout,u,835)
        probe('Arcade brick in front of lower belt',[x,-.7,z],[0,1,0],1.,ARCADE_BRICK)
    for u in [502,510,736,744]:
        x,_,z=point(layout,u,839)
        probe('Red belt between adjoining arch extrados',[x,-.7,z],[0,1,0],1.,RED)
    for r in layout['upper_openings']:
        mid=(r['x0']+r['x1'])/2;z=r['z_sill']
        probe('Flower shelf edge outside sash',[mid,-.8,z-.046],[0,1,0],.8,IRON)
        probe('Light spandrel below sill',[mid,-.7,z-.28],[0,1,0],1.,SILL)
    for x in [2.18,3.07,3.91]:
        for i,y in enumerate([-.2,-.6,-1.0]):
            probe('Garden stair tread',[x,y,.55],[0,0,-1],1.5,STONE,[.55+.16*(i+1)-.001,.55+.16*(i+1)+.001])
        probe('Top landing in covered gallery',[x,.48,.55],[0,0,-1],.8,STONE,[.549,.551])
    for u,v,mat in [(787,954,PLASTER),(838,996,RED),(848,966,PLANK),(825,882,PLANK),(884,855,PLANK),(899,933,DARK)]:
        x,_,z=point(layout,u,v,1.83)
        probe('Rear of garden gallery',[x,.8,z],[0,1,0],1.25,mat)
    for x in [-4.4,-3.91,-3.15]:
        xmin=point(layout,251,800)[0]-.20
        y=5.35;z=ze+(x-xmin)*(hz-ze)/(hx-xmin)
        probe('West hipped roof surface',[x,y,z+.55],[0,0,-1],.8,[*CLAYS,BED],[.47,.55])
    for f in [.24,.46,.64,.84]:
        xmin=point(layout,251,800)[0]-.20
        xx=xmin+(hx-xmin)*f;yy=e+(hy-e)*f;zz=ze+(hz-ze)*f
        probe('Rounded hip capping above lower cut',[xx,yy,zz+.45],[0,0,-1],.65,RIDGE,[.30,.42])
    hi=layout['back_roof']['back_left'];lo=layout['back_roof']['front_left']
    for x in [1.15,1.96,3.15,4.52]:
        for y in [8.1,9.3]:
            z=lo[2]+(y-lo[1])*(hi[2]-lo[2])/(hi[1]-lo[1])
            probe('Higher rear tile plane',[x,y,z+.60],[0,0,-1],.85,[*CLAYS,BED],[.52,.601])
    return dict(passed=all(r['passed']for r in hits),asset=scene.asset,triangles=len(scene.tri),hits=hits,
                units='Local model metres, set by the assumed nominal brick course. Ranges check exported geometry.')
