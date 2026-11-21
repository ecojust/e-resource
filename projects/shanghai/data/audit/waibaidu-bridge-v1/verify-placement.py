"""Compare the actual delivery and frozen city meshes around Waibaidu Bridge."""
import argparse
import gzip
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import shapely as geo
from shapely.geometry import box

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
sys.path.insert(0, str(PROJECT/'tools'))
from candidate_placement_meshes import PlacementMeshes, read, write


def clearance(triangles, bridge):
    xy = triangles[:, :, :2]
    # The source groups cover a wider area than the river. Keep all triangles that
    # could contain points within 80 m of the bridge's projected bounding box.
    x0,y0,x1,y1 = bridge.bounds
    mask = ((xy.max(axis=1) >= [x0-80,y0-80]).all(axis=1)
            & (xy.min(axis=1) <= [x1+80,y1+80]).all(axis=1))
    parts = xy[mask]
    polygons = geo.polygons(parts)
    flat = geo.area(polygons) <= 1e-10
    distances = []
    if np.any(flat):
        distances.extend(geo.distance(geo.linestrings(parts[flat]), bridge))
    if np.any(~flat):
        distances.extend(geo.distance(polygons[~flat], bridge))
    assert distances and min(distances) > .25
    return dict(source_triangles=len(triangles), inspected=len(parts),
                minimum_plan_clearance_m=float(min(distances)))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work',required=True,type=Path)
    parser.add_argument('--out',type=Path,default=HERE)
    args=parser.parse_args()
    ident='huangpu-waibaidu-bridge'
    source=PROJECT/'source/precise'/ident
    review=read(source/'footprint-review.json')
    ctx=PlacementMeshes(PROJECT,args.work,review)
    manifest=PROJECT/'assets/models/candidates'/ident/'manifest.json'
    models,bounds,projection,_=ctx.decode_model(manifest)
    assert box(-10,-52.5,10,52.5).covers(projection)
    nearest=sorted((poly.distance(projection),owner)for owner,poly in ctx.footprints.items())[:5]
    assert nearest[0][0]>12 and nearest[0][1]==935
    table=json.loads(gzip.decompress(ctx.files['feature-table.json.gz'].read_bytes()))
    write(ctx.work/'context-features.json',[{'localId':r['localId']}for r in table['features']])
    ctx.link('baseline-far.glb',ctx.files['far.glb'])
    ctx.link('macro-READY.json',ctx.files['READY.json'])
    checks={}
    for group in review['near_tiles']:
        ctx.link('baseline-near.glb.gz',ctx.files[Path(group['file']).name])
        subprocess.run(['node',ctx.decoders/'map-decode-source.mjs'],env=ctx.env,
                       stdout=subprocess.DEVNULL,check=True)
        for name,role in [(group['id'],'near'),('macro_far','far')]:
            if name in checks:continue
            tris=np.fromfile(ctx.work/f'baseline-{role}-triangles.f64').reshape(-1,3,3)
            tris[:,:,:2] = tris[:,:,:2] @ ctx.axes.T
            checks[name]=clearance(tris,projection)
    frozen=read(source/'frozen-bridge-layer.json')
    assert frozen['osm_frozen_deck_iou']>.98 and len(frozen['checks'])==63
    # The existing vector bridge connects both banks and exempts the sidewalks
    # from water collision. Inspect real frozen features independently of model geometry.
    for sample in frozen['checks']:
        if abs(sample['x'])<9:assert sample['native_collision'] is None
        if abs(sample['x'])==14 and abs(sample['y'])<=30:assert sample['native_collision']=='water'
    walk=read(HERE/'bridge-walk.json')
    verified_roads = [274981172, 4317222840]
    assert walk['transportation_feature_ids'] == verified_roads
    assert set(verified_roads).issubset({feature['id'] for feature in frozen['features']})
    assert walk['stations_m']==[[-52.12,-.01],[52.12,-.01]]
    assert walk['half_deck_m']==9.2 and walk['sidewalk_rise_m']==.16
    lng,lat=frozen['center']
    contract=dict(id=ident,lng=lng,lat=lat,heading=frozen['heading'],altitude=.085,scale=1,
        replacement_geometry=None,source_feature_ids={'building':[],'building_part':[]},collision_geometry=None,
        bridge_walk=walk,bounds_glb=bounds,model_geometry_sha256={k:v['sha256']for k,v in models.items()},
        overviewBearing=282,overviewPitch=58,overviewZoom=17.9,maxDistance=950,lod_switch_in_m=320,lod_switch_out_m=470,
        navigation=dict(listed=True, walkStart=[121.48567124230846,31.244858244692885],
                        bearing=frozen['heading'],status='从南端东侧人行道向北过桥'),
        placement={'status':'estimated','note':'1907年两跨桥身沿现有具名道路布置。车行面与项目平面街道的角色脚底对齐，两边人行道高0.16米。'},
        partial_model=True,model_scope=read(manifest)['model_scope_zh'])
    write(args.out/'placement-geometry.json',dict(id=ident,models=models,bounds=bounds,
          projected_area_m2=projection.area,native_groups=checks,nearest_buildings=nearest,
          existing_bridge_and_water_probes=frozen['checks'],frozen_deck_iou=frozen['osm_frozen_deck_iou']))
    write(args.out/'final-placement-contract.json',contract)
    print('Verified',len(checks),'native meshes and',len(frozen['checks']),'existing bridge and water positions.')


if __name__=='__main__':
    main()
