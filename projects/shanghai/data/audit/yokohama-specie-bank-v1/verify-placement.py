"""Compare the delivered model to the five real near/far source owners and the 28-component OSM aggregate."""
import argparse
from pathlib import Path
import os,sys,tempfile
import numpy as np
import shapely as geo
from shapely.geometry import shape,Point

audit=Path(__file__).resolve().parent
project=audit.parents[2]
sys.path.insert(0,str(project/'tools'))
from candidate_placement_meshes import PlacementMeshes,read,write,sha
from build_candidate_city_integrations import checked_geometry

ident='huangpu-yokohama-specie-bank'
cli=argparse.ArgumentParser(description=__doc__)
cli.add_argument('--macro',required=True,type=Path)
cli.add_argument('--vector',required=True,type=Path)
cli.add_argument('--manifest',type=Path,default=project/'assets/models/candidates'/ident/'manifest.json')
cli.add_argument('--out',type=Path,default=audit)
args=cli.parse_args()
footfile=project/'source/precise'/ident/'footprint-review.json'
src=read(footfile);manifest=read(args.manifest);vector=read(args.vector)
assert vector['sha256']==src['fallback_vector']['tile_sha256'] and manifest['id']==ident
group=src['near_tiles'][0];ids=group['feature_local_ids']
assert set(ids)=={1332,833,2903,2937,1571}
args.out.mkdir(parents=True,exist_ok=True)
with tempfile.TemporaryDirectory() as directory:
    work=Path(directory)
    for receipt in src['frozen_bindings']:
        suffix=receipt['repository_path'].split(src['owner']['macro_id']+'/')[1]
        (work/Path(suffix).name).symlink_to((args.macro/suffix).resolve())
    mesh=PlacementMeshes(project,work,src)
    assets,bounds,profile,ground=mesh.decode_model(args.manifest)
    source=mesh.decode_group(group,1571)
    native={k:mesh.project_faces(t) for k,(t,_,_) in source.items()}
    others={k:mesh.project_faces(n) for k,(_,n,_) in source.items()}
    native_outline=mesh.footprints[1571]
    bundle=next(f for f in vector['features'] if f['id']==116367860)
    raw_osm=geo.transform(shape(bundle['geometry']),mesh.to_xy)
    components=list(raw_osm.geoms)
    target=[g for g in components if g.intersection(native_outline).area>1.]
    assert len(components)==28 and len(target)==1
    pieces=[native_outline,profile,*native.values(),*target]
    mask=geo.union_all(pieces).buffer(.055,join_style='mitre').simplify(.018,preserve_topology=True)
    collision=ground.buffer(.07,join_style='mitre').simplify(.075,preserve_topology=True)
    assert ground.difference(collision).area<.001 and mask.is_valid and collision.is_valid
    assert max(m.difference(mask).area for m in pieces)<.00005
    assert profile.difference(mask).area<.0005,profile.difference(mask).area
    assert all(g.distance(mask)>1. for g in others.values())
    unchanged_components=[p for p in components if p!=target[0]]
    assert all(p.intersection(mask).area<.001 for p in unchanged_components)
    nearby={i:{'mask_gap_m':g.distance(mask),'model_gap_m':g.distance(profile),'mask_intersection_m2':g.intersection(mask).area} for i,g in mesh.footprints.items() if i!=1571 and g.distance(mask)<14}
    assert all(v['mask_intersection_m2']<.001 for v in nearby.values())
    for geo_name,geom in [('replacement_geometry',mask),('collision_geometry',collision)]:
        checked_geometry(mesh.wgs(geom),geo_name,collision=geo_name=='collision_geometry')
    anchor=src['author_frame']['anchor'];r=src['owner']
    contract={'id':ident,**anchor,'heading':src['author_frame']['runtime_heading_deg'],'scale':1,'altitude':0,
        'owner':{'macro_id':r['macro_id'],'feature_local_id':1571},
        'source_feature_ids':{'building':[r['source_key'].split(':')[1]],'building_part':[]},
        'model_geometry_sha256':{role:asset['sha256'] for role,asset in assets.items()},
        'bounds_glb':bounds,'replacement_geometry':mesh.wgs(mask),'collision_geometry':mesh.wgs(collision),
        'overviewBearing':-86,'overviewPitch':58,'overviewZoom':19.04,
        'overview_focus_bounds_glb':{'min':[26,.12,-7.3],'max':[39.85,35.52,18.5]},
        'maxDistance':550,'lod_switch_in_m':550,'lod_switch_out_m':700,
        'navigation':{'listed':False,'status':'黄浦江侧主立面、双巨柱、三开间铜门与有斜侧光的阳台。'},
        'placement':{'status':'estimated','note':'以外滩24号具名L形原址替换1571。原组包含27号怡和洋行、28号格林邮船大楼和26号扬子大楼。屋盖进深、后翼与高度按外部照片、地方志和航片估计。'},
        'partial_model':False,'model_scope':manifest['model_scope_zh']}
    focus=contract['overview_focus_bounds_glb']
    assert all(bounds['min'][i]<=focus['min'][i]<focus['max'][i]<=bounds['max'][i] for i in range(3))
    probes=[]
    for label,x,y,expected in [('three bronze doors',38.93,-5.405,True),('west wing',-17,12,True),('Bund sidewalk',43,-5,False),('south separation',23,-20.61,False),('Yangtze Insurance lot',23,13,False)]:
        point=Point(x,y)
        assert collision.covers(point)==expected,(label,collision.distance(point))
        probes.append({'label':label,'point':mesh.to_wgs(np.array([[x,y]]))[0].tolist(),'model_collision':expected,'under_mask':mask.covers(point)})
    outcome={'id':ident,'manifest_sha256':sha(args.manifest),'source_sha256':sha(footfile),'script_sha256':sha(Path(__file__)),'decoder_sha256':sha(project/'tools/candidate_placement_meshes.py'),
             'assets':assets,'model_area_m2':profile.area,'ground_area_m2':ground.area,'collision_area_m2':collision.area,'replacement_area_m2':mask.area,
             'source_group':group,'source_native':{k:{'area_m2':v.area,'remaining_m2':v.difference(mask).area,'all_other_buildings_gap_m':others[k].distance(mask),'model_to_all_other_buildings_m':profile.distance(others[k]),'assignment':source[k][2]}for k,v in native.items()},
             'osm_source':{'id':bundle['id'],'tile_sha256':vector['sha256'],'aggregate_parts':len(components),'area_target_m2':target[0].area,'target_missing_m2':target[0].difference(mask).area,'retained_component_count':len(unchanged_components),'next_component_gap_m':min(p.distance(mask)for p in unchanged_components)},
             'nearby_original_footprints':nearby,'ground_points':probes}
    write(args.out/'final-placement-contract.json',contract)
    outcome['contract_sha256']=sha(args.out/'final-placement-contract.json')
    write(args.out/'placement-geometry.json',outcome)
    print(ident,[(key,round(v['all_other_buildings_gap_m'],3))for key,v in outcome['source_native'].items()],len(unchanged_components))
