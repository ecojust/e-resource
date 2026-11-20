"""Measure all three meshes and the real near/far owners around the former Chung Wei Bank."""
import argparse
from pathlib import Path
import sys
import tempfile

import numpy as np
import shapely as geo
from shapely.geometry import Point,shape

audit=Path(__file__).resolve().parent
project=audit.parents[2]
sys.path.insert(0,str(project/'tools'))
from candidate_placement_meshes import PlacementMeshes,read,write,sha
from build_candidate_city_integrations import checked_geometry

ident='huangpu-chung-wei-bank-building'
cli=argparse.ArgumentParser(description=__doc__)
cli.add_argument('--macro',required=True,type=Path)
cli.add_argument('--vector',required=True,type=Path)
cli.add_argument('--manifest',type=Path,default=project/'assets/models/candidates'/ident/'manifest.json')
cli.add_argument('--out',type=Path,default=audit)
args=cli.parse_args()
review_file=project/'source/precise'/ident/'footprint-review.json'
src=read(review_file)
manifest=read(args.manifest)
vec=read(args.vector)
assert vec['sha256']==src['fallback_vector']['tile_sha256'] and manifest['id']==ident
group=src['near_tiles'][0]
assert set(group['feature_local_ids'])=={830,1445}
with tempfile.TemporaryDirectory() as temp:
    work=Path(temp)
    for receipt in src['frozen_bindings']:
        suffix=receipt['repository_path'].split(src['owner']['macro_id']+'/')[1]
        (work/Path(suffix).name).symlink_to((args.macro/suffix).resolve())
    mesh=PlacementMeshes(project,work,src)
    assets,bounds,profile,ground=mesh.decode_model(args.manifest)
    decoded=mesh.decode_group(group,830)
    source={k:mesh.project_faces(tris) for k,(tris,_,_) in decoded.items()}
    retained={k:mesh.project_faces(tris) for k,(_,tris,_) in decoded.items()}
    original=mesh.footprints[830]
    aggregate=next(f for f in vec['features'] if f['id']==23763660)
    assert aggregate['properties']['render_height']==41
    agg=geo.transform(shape(aggregate['geometry']),mesh.to_xy)
    assert len(agg.geoms)==2
    target,remote=sorted(agg.geoms,key=lambda p:-p.intersection(original).area)
    assert target.intersection(original).area>2000 and remote.distance(original)>700
    surrounding=next(f for f in vec['features'] if f['id']==106284410)
    low=geo.transform(shape(surrounding['geometry']),mesh.to_xy)
    contained=[profile,original,target,*source.values()]
    mask=geo.union_all(contained).buffer(.045,join_style='mitre').simplify(.018,preserve_topology=True)
    collision=ground.buffer(.06,join_style='mitre').simplify(.05,preserve_topology=True)
    assert max(p.difference(mask).area for p in contained)<.0001
    assert ground.difference(collision).area<.001
    assert all(p.distance(mask)>3 for p in retained.values())
    assert not low.intersects(mask) and not remote.intersects(mask)
    other={i:{'gap_m':p.distance(mask),'overlap_m2':p.intersection(mask).area} for i,p in mesh.footprints.items() if i!=830 and p.distance(mask)<12}
    assert all(v['overlap_m2']<.001 for v in other.values()),other
    ow=src['owner']
    contract={'id':ident,**src['author_frame']['anchor'],'heading':src['author_frame']['runtime_heading_deg'],'scale':1,'altitude':0,
        'owner':{'macro_id':ow['macro_id'],'feature_local_id':830},'source_feature_ids':{'building':[ow['source_key'].split(':')[1]],'building_part':[]},
        'model_geometry_sha256':{k:v['sha256']for k,v in assets.items()},'bounds_glb':bounds,
        'replacement_geometry':mesh.wgs(mask),'collision_geometry':mesh.wgs(collision),'overviewBearing':-105,'overviewPitch':55,'overviewZoom':18.69,
        'maxDistance':600,'lod_switch_in_m':600,'lod_switch_out_m':780,
        'navigation':{'listed':False,'status':'可从河南南路看北端退台塔、东侧窗带和金陵东路的转角。'},
        'placement':{'status':'estimated','note':'按延安东路143号具名原生记录830定位。保留近景同组1445和西侧紧邻地块96。层高、后侧和设备参考外部照片与地方志估算。'},
        'partial_model':False,'model_scope':manifest['model_scope_zh']}
    for name in ('replacement_geometry','collision_geometry'):
        checked_geometry(contract[name],name,collision=name=='collision_geometry')
    points=[]
    for label,x,y,expected in [('east facade body',15,0,True),('north entrance end',2,32,True),('south street return',3,-30,True),('Henan South Road',23,0,False),('Jinling East Road',2,-42,False),('Yanan East Road',1,44,False)]:
        pt=Point(x,y);assert collision.covers(pt)==expected,(label,collision.distance(pt))
        points.append({'label':label,'point':mesh.to_wgs(np.array([[x,y]]))[0].tolist(),'model_collision':expected,'under_mask':mask.covers(pt)})
    args.out.mkdir(exist_ok=True,parents=True)
    write(args.out/'final-placement-contract.json',contract)
    report={'id':ident,'manifest_sha256':sha(args.manifest),'source_sha256':sha(review_file),'script_sha256':sha(Path(__file__)),
        'decoder_sha256':sha(project/'tools/candidate_placement_meshes.py'),'contract_sha256':sha(args.out/'final-placement-contract.json'),
        'model_area_m2':profile.area,'ground_area_m2':ground.area,'collision_area_m2':collision.area,'replacement_area_m2':mask.area,'assets':assets,
        'source_group':group,'source_native':{k:{'area_m2':p.area,'remaining_m2':p.difference(mask).area,'all_other_buildings_gap_m':retained[k].distance(mask),'model_to_other_m':retained[k].distance(profile),'assignment':decoded[k][2]}for k,p in source.items()},
        'ground_points':points,'nearby_owners':other,'osm_source':{'id':aggregate['id'],'target_remaining_m2':target.difference(mask).area,
            'remote_original_area_m2':remote.area,'remote_after_m2':remote.difference(mask).area,'remote_gap_m':remote.distance(mask),
            'retained_low_source_id':surrounding['id'],'retained_low_gap_m':low.distance(mask),'retained_low_intersection_m2':low.intersection(mask).area}}
    write(args.out/'placement-geometry.json',report)
    print(ident,[(k,round(v['all_other_buildings_gap_m'],3))for k,v in report['source_native'].items()],other)
