"""Cast rays from the original street and lane photographs at independently picked surfaces."""
import argparse
from pathlib import Path
import json,hashlib,runpy
import numpy as np
from register_house import Camera

HERE=Path(__file__).resolve().parent
SHARED=Path('data/audit/postal-office-v1/independent-glb-review-helpers.py')
PROJ=next(p for p in HERE.parents if (p/SHARED).is_file())
Scene=runpy.run_path(str(PROJ/SHARED))['SerialScene']
TYPES={
    'glass':{'dim garden reflection','pale sky reflection'},
    'steel':{'dark steel joinery'},'aluminium':{'silver grey replacement frame'},
    'masonry':{'pale ochre roughcast','grey lower render'},
    'air':{'chalk white condenser case','shaded condenser grille','galvanized fan guard'},
    'tile':{'reddish brown sill tiles','grey sill bedding'},'pipe':{'dark rainwater iron'}}
def check(asset):
    scene=Scene(asset);selection=json.loads((HERE/'wall-first-hit-controls.json').read_text());obs=[]
    for station,items in selection['controls'].items():
        c=Camera(station)
        for kind,points in items.items():
            for px in points:
                hits=[]
                nearest=None
                for radius in (0,1,2,4):
                    for vector in ((0,0),) if radius==0 else ((1,0),(-1,0),(0,1),(0,-1),(.71,.71),(.71,-.71),(-.71,.71),(-.71,-.71)):
                        hit=scene.ray(c.c,c.ray(np.array(px)+radius*np.array(vector)),85)
                        if not hits:hits.append(hit)
                        if hit and any(hit['material']=='280-2 | '+material for material in TYPES[kind]):
                            nearest=radius
                            break
                    if nearest is not None:break
                obs.append({'station':station,'pixel':px,'surface':kind,'first_hit':hits[0],'nearest_px':nearest})
    return {'mesh_sha256':hashlib.sha256(asset.read_bytes()).hexdigest(),'camera_sha256':hashlib.sha256((HERE/'house-cameras.json').read_bytes()).hexdigest(),
            'total':len(obs),'exact':sum(r['nearest_px']==0 for r in obs),'within_4_px':sum(r['nearest_px'] is not None for r in obs),'observations':obs}
if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('asset',type=Path);cli.add_argument('report',type=Path)
    a=cli.parse_args();r=check(a.asset);a.report.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
    print(r['exact'],r['within_4_px'],r['total'])
