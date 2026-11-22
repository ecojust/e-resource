"""Cut-corner stone tablet and its stepped surround on the historic upper facade."""
import json
from pathlib import Path
import numpy as np
from shapely.geometry import Polygon
from shapely.geometry.polygon import orient

ROOT=Path(__file__).resolve().parent
MEASUREMENTS=ROOT.parent/'measurements'/'central-tablet-metric.json'
FACE='Tablet | exposed aggregate'
HOOD='Tablet | grey hood stone'
CAP='Tablet | light cap'
BED='Tablet | smooth mount'
PLINTH='Tablet | bottom stone'


def finish(rgb):
    a=np.asarray(rgb)/255.
    color=np.where(a<=.04045,a/12.92,((a+.055)/1.055)**2.4)
    return {'color':color.tolist(),'roughness':.86,'metallic':0.}


PALETTE={FACE:{'color':[1.,1.,1.],'roughness':.94,'metallic':0.,'texture':str(ROOT/'tablet-aggregate.jpg')},
         HOOD:{'color':[1.,1.,1.],'roughness':.90,'metallic':0.,'texture':str(ROOT/'tablet-hood.jpg')},
         CAP:finish([204,204,194]),BED:finish([148,149,136]),
         PLINTH:finish([172,169,153])}


def _mapping(x,z,outward):
    return x,-outward,z


def _tablet(b,profile,y_front,y_back,low):
    # XZ points run counterclockwise. The normal to the face is toward the viewer, -Y.
    face=orient(Polygon(profile),sign=1.)
    outward=face.buffer(.010,join_style=2)
    coords=np.asarray(face.exterior.coords[:-1]);exp=np.asarray(outward.exterior.coords[:-1])
    # Buffer may start at another corner or reverse order. Pair its eight offset corners explicitly.
    expanded=exp[np.argmin(np.linalg.norm(coords[:,None]-exp[None,:],axis=2),axis=1)]
    assert len(set(map(tuple,expanded)))==len(coords)==8
    rings=[(coords,y_front),(expanded,y_front+.022)]
    if not low:rings.append((expanded,y_back-.008))
    rings.append((expanded*.996+expanded.mean(axis=0)*.004,y_back))
    v=[(x,y,z) for p,y in rings for x,z in p];n=len(coords)
    f=[tuple(range(n)),tuple((len(rings)-1)*n+i for i in reversed(range(n)))]
    for i in range(len(rings)-1):
        for j in range(n):
            j1=(j+1)%n
            f.append((i*n+j1,i*n+j,(i+1)*n+j,(i+1)*n+j1))
    b.add(v,f,FACE,'Central tablet | eight cut corners and narrow stone bevel')
    uv=np.asarray([(x,-z) for x,y,z in v]);uv=(uv-uv.min(axis=0))/np.ptp(uv,axis=0)
    b.parts[-1]['texcoords']=uv.tolist()


def add_central_tablet(b,lod=False):
    m=json.loads(MEASUREMENTS.read_text());p=m['xz_m'];y=m['front_planes_m']
    def relief(key,rear,material,label):
        b.prism(Polygon(p[key]),-rear,-y[key],_mapping,material,label)
    relief('mount',.020,BED,'Central tablet | projecting plastered mount')
    relief('plinth',.018,PLINTH,'Central tablet | short base above the continuous cornice')
    relief('hood',.013,HOOD,'Central tablet | stone hood with two short downward ends')
    hood = b.parts[-1]
    coords=np.asarray([(x,-z) for x,y,z in hood['vertices']]);hood['texcoords']=((coords-coords.min(axis=0))/np.ptp(coords,axis=0)).tolist()
    relief('cap',.011,CAP,'Central tablet | narrow stepped head cap')
    _tablet(b,p['tablet'],y['tablet'],y['mount']+.004,lod is True or lod=='lod')
