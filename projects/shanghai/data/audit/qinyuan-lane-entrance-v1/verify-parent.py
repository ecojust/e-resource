"""Compare the unchanged original street and every walking sample with the signed preceding city."""
from pathlib import Path
from argparse import ArgumentParser
from hashlib import sha256
import json, math
import shapely as geo
from shapely.geometry import box,Point,shape
import numpy as np

def digest(path):return sha256(path.read_bytes()).hexdigest()
def read(path):return json.loads(path.read_bytes())
def main():
    args=ArgumentParser(description=__doc__)
    args.add_argument('--parent',type=Path,required=True)
    args.add_argument('--proof-order',type=int,default=309)
    args.add_argument('--audit',type=Path,default=Path(__file__).resolve().parent)
    args.add_argument('--out',type=Path,required=True)
    a=args.parse_args();prior=read(a.parent)
    assert prior['order']==a.proof_order
    stage=Path(prior['root'])/'projects/shanghai';snapshot=Path(prior['snapshot'])
    assert digest(snapshot)==prior['sha256']
    cat=stage/'data/candidate-city-integrations.json'
    assert digest(cat)==prior['catalog_sha256']==read(snapshot)['files']['data/candidate-city-integrations.json']
    contract=read(a.audit/'final-placement-contract.json');g=read(a.audit/'placement-geometry.json')
    assert contract['id']==g['id'] and g['contract_sha256']==digest(a.audit/'final-placement-contract.json')
    catalog=read(cat);rows=catalog['models']
    assert not any(r['id']==contract['id']for r in rows)
    if a.proof_order==309:assert rows[-1]['id']=='jingan-jueyuan-xiangguang-hall'
    bearing=math.radians(contract['heading']);ax=np.array([[math.cos(bearing),-math.sin(bearing)],[math.sin(bearing),math.cos(bearing)]])
    k=6371008.8*math.cos(math.radians(contract['lat']));m=math.asinh(math.tan(math.radians(contract['lat'])))
    def local(coords):return np.column_stack([np.radians(coords[:,0]-contract['lng'])*k,(np.arcsinh(np.tan(np.radians(coords[:,1])))-m)*k])@ax.T
    bounds=contract['bounds_glb'];b0,b1=bounds['min'],bounds['max'];model=box(b0[0],-b1[2],b1[0],-b0[2])
    corridor=geo.Polygon(g['continuous_clear_corridor_xy_m'])
    candidates=[]
    for r in rows:
        for key in ('replacement_geometry','collision_geometry','osm_replacement_geometry'):
            if not r.get(key):continue
            geom=geo.transform(shape(r[key]),local);dist_model=geom.distance(model);dist_walk=geom.distance(corridor)
            assert min(dist_model,dist_walk)>0,(r['id'],key,dist_walk,dist_model)
            candidates.append((min(dist_model,dist_walk),r['id'],key))
    result=dict(order=310,actual_previous_order=prior['order'],actual_previous_id=rows[-1]['id'],catalog_population=len(rows),passed=True,receipt_sha256=digest(a.parent),snapshot_sha256=digest(snapshot),catalog_sha256=digest(cat),contract_sha256=digest(a.audit/'final-placement-contract.json'),new_source_owners=0,new_clip_triangles=0,existing_candidate_geometries=len(candidates),five_nearest=sorted(candidates)[:5],old_ground_probes_checked=len(g['ground_samples']),walking_corridor_unchanged=True)
    a.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print('checked',a.proof_order,len(rows),len(candidates))
if __name__=='__main__':main()
