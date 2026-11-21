"""Compare all triangles of the established Bund street scene with the verified bridge deck."""
import argparse, hashlib, json, math, runpy
from pathlib import Path
import numpy as np
import shapely
from shapely.geometry import Polygon

def run(project,decoded,dest):
    def read(path):
        return json.loads(path.read_bytes())
    def sha(p):
        return hashlib.sha256(p.read_bytes()).hexdigest()
    scope=project/'source/precise/huangpu-waibaidu-bridge'
    way=next(w for w in read(scope/'placement-research.json')['ways'] if w['id']=='815631996')
    street=project/'data/bund/street-interaction-v5.json'
    scene=project/'data/scene-props.json'
    geometry=project/'assets/models/bund/web/bund-streets.glb'
    item=next(m for m in read(scene)if m['id']=='bund-streets')
    assert sha(geometry)==item['web_sha256']==read(street)['web_model_sha256']
    x,y=read(street)['origin']
    assert [x,y]==[item['lng'],item['lat']] and all(item.get(k,v)==v for k,v in [('scale',1),('heading',0),('altitude',0)])
    scale=6371008.8*math.cos(math.radians(y))
    def north(a):
        return math.asinh(math.tan(math.radians(a)))
    footprint=Polygon([(scale*math.radians(lon-x),scale*(north(lat)-north(y)))for lon,lat in way['nodes']])
    reader=project/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
    triangles,ids,names,_=runpy.run_path(str(reader))['load_triangles'](decoded)
    projections=shapely.convex_hull(shapely.multipoints(triangles[:,:,:2]))
    distances=shapely.distance(projections,footprint)
    rows=[]
    for i in np.unique(ids):
        select=ids==i
        overlap=np.logical_and(select,distances<1e-8)
        nearest=np.flatnonzero(select)[np.argmin(distances[select])]
        rows.append(dict(material=names[i],triangles=int(select.sum()),intersecting=int(overlap.sum()),
                         minimum_clearance_m=float(distances[nearest]),nearest_heights_m=triangles[nearest,:,2].tolist()))
    assert len(rows)==16 and len(triangles)==138930
    dest.write_text(json.dumps(dict(reference='OpenStreetMap way 815631996, version 7',method='Compare each triangle footprint at the actual street-model Mercator origin to the registered bridge boundary.',footprint_source_sha256=sha(scope/'placement-research.json'),street_mesh_sha256=sha(geometry),decoded_sha256=sha(decoded),interaction_sha256=sha(street),scene_sha256=sha(scene),reader_sha256=sha(reader),triangles=len(triangles),origin=[x,y],intersecting=int((distances<1e-8).sum()),minimum_clearance_m=float(distances.min()),materials=sorted(rows,key=lambda r:r['minimum_clearance_m'])),indent=2,ensure_ascii=False)+'\n')
    print(dest, int((distances<1e-8).sum()),float(distances.min()))
if __name__=='__main__':
    arg=argparse.ArgumentParser(description=__doc__)
    arg.add_argument('--project',type=Path,required=True);arg.add_argument('--decoded',type=Path,required=True)
    arg.add_argument('--out',type=Path,required=True);args=arg.parse_args()
    run(args.project,args.decoded,args.out)
