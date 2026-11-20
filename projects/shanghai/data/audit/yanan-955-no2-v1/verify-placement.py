"""Verify the source strip, surveyed north return and surviving courtyard and neighboring roofs."""
import argparse
from pathlib import Path
import sys
import tempfile

import numpy as np
import shapely as geo
from shapely.geometry import Point, shape, LineString

audit=Path(__file__).resolve().parent
project=audit.parents[2]
sys.path.insert(0,str(project/'tools'))
from build_candidate_city_integrations import checked_geometry
from candidate_placement_meshes import PlacementMeshes, read, sha, write

model='jingan-yanan-955-no2'
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--macro',type=Path,required=True)
parser.add_argument('--vector',type=Path,required=True)
parser.add_argument('--manifest',type=Path,default=project/'assets/models/candidates'/model/'manifest.json')
parser.add_argument('--out',type=Path,default=audit)
args=parser.parse_args()
source_path=project/'source/precise'/model/'footprint-review.json'
source,vector,manifest=read(source_path),read(args.vector),read(args.manifest)
assert manifest['id']==model and vector['sha256']=='21ae0cc5b91bfb8c85d320d3d0295804e5af8d04fcca02fb316f3e5ef80449e2'
owner=source['owner']
group,=source['near_tiles']
assert owner['feature_local_id']==2661 and len(group['feature_local_ids'])==14
with tempfile.TemporaryDirectory()as folder:
    scratch=Path(folder)
    for binding in source['frozen_bindings']:
        name=binding['repository_path'].split(owner['macro_id']+'/')[1]
        (scratch/Path(name).name).symlink_to((args.macro/name).resolve())
    site=PlacementMeshes(project,scratch,source)
    assets,bounds,profile,ground=site.decode_model(args.manifest)
    collision=ground.buffer(.03,join_style='mitre').simplify(.035,preserve_topology=True)
    assert ground.difference(collision).area<.025
    original=site.footprints[2661]
    decoded=site.decode_group(group,2661)
    originals={role:site.project_faces(v[0])for role,v in decoded.items()}
    peers={role:site.project_faces(v[1])for role,v in decoded.items()}
    mask=geo.union_all([profile,original,*originals.values()]).buffer(.06,join_style='mitre').simplify(.025,preserve_topology=True)
    assert all(g.difference(mask).area<.00001 for g in [profile,original,*originals.values()])
    gaps={i:dict(removed_m2=g.intersection(mask).area,gap_m=g.distance(mask)) for i,g in site.footprints.items()if i!=2661}
    assert all(g['removed_m2']==0 and g['gap_m']>.5 for g in gaps.values())
    assert all(g.distance(mask)>.6 for g in peers.values())
    vector_distances={str(f['id']):geo.transform(shape(f['geometry']),site.to_xy).distance(mask)for f in vector['nearby_features']}
    assert vector['total_tile_buildings']==26 and len(vector_distances)==1 and min(vector_distances.values())>10
    # Projection of the public lane and two observation station coordinates.
    lane=LineString(site.to_xy(np.array(source['lane_way']['geometry'])))
    assert lane.distance(mask)>1. and lane.distance(collision)>1.
    probes=[]
    tests=[('main enclosed rooms',0,0,True),('under west dormer',1.90,8.02,True),
           ('enclosed north return',8.26,12.81,True),('outside lower return wall',11.75,12.1,False),
           ('open northerly forecourt',1.5,12.7,False),('north approach',8.25,17.2,False),
           ('west walkway',-11.4,.1,False),('south walkway',0,-6.1,False)]
    for name,x,y,blocked in tests:
        point=Point(x,y);assert collision.covers(point)==blocked,(name,collision.covers(point))
        probes.append(dict(label=name,xy=[x,y],point=site.to_wgs(np.array([[x,y]]))[0].tolist(),model_collision=blocked,under_mask=mask.covers(point)))
    contract={'id':model,**source['author_frame']['anchor'],'heading':source['author_frame']['runtime_heading_deg'],
              'scale':1,'altitude':0,'owner':{'macro_id':owner['macro_id'],'feature_local_id':2661},
              'source_feature_ids':{'building':[owner['source_key'].split(':')[1]],'building_part':[]},
              'model_geometry_sha256':{k:v['sha256']for k,v in assets.items()},'bounds_glb':bounds,
              'replacement_geometry':site.wgs(mask),'collision_geometry':site.wgs(collision),
              'overviewBearing':165,'overviewPitch':55,'overviewZoom':20.12,'maxDistance':670,'lod_switch_in_m':620,'lod_switch_out_m':820,
              'placement':{'status':'estimated','note':'2号北侧凸廊及主瓦坡按三个街面机位与航片对齐。原地块2661的南段轮廓在近远景均作整体替换，旁侧院地及弄道保留。'},
              'navigation':{'listed':False,'status':'从延安中路南侧沿街看北向老虎窗、主瓦坡和低屋面。'},
              'partial_model':True,'model_scope':manifest['model_scope_zh']}
    for key in ['replacement_geometry','collision_geometry']:checked_geometry(contract[key],key,collision=key=='collision_geometry')
    args.out.mkdir(parents=True,exist_ok=True)
    write(args.out/'final-placement-contract.json',contract)
    states={role:{'old_area_m2':originals[role].area,'remaining_m2':originals[role].difference(mask).area,
                  'old_top_m':float(decoded[role][0][:,:,2].max()),'other_triangles_gap_m':peers[role].distance(mask),'assignment':decoded[role][2]}for role in decoded}
    result=dict(id=model,script_sha256=sha(Path(__file__)),manifest_sha256=sha(args.manifest),source_sha256=sha(source_path),
                contract_sha256=sha(args.out/'final-placement-contract.json'),assets=assets,group=group,source_records=states,
                source_outline_m2=original.area,display_m2=profile.area,display_outside_source_m2=profile.difference(original).area,
                collision_m2=collision.area,mask_m2=mask.area,ground_points=probes,
                other_group_owners={i:gaps[i] for i in group['feature_local_ids'] if i!=2661},
                adjacent_sources={i:gaps[int(i)] for i in source['neighboring_buildings']},nearest_source=min(gaps,key=lambda i:gaps[i]['gap_m']),
                surveyed_lane={'osm_way':source['lane_way']['id'],'distance_to_mask_m':lane.distance(mask),'distance_to_ground_collision_m':lane.distance(collision)},
                osm_fallback={'sha256':vector['sha256'],'features':26,'nearby_distances_m':vector_distances,'overlapping_parts':0})
    write(args.out/'placement-geometry.json',result)
    print('No.2',states,result['surveyed_lane'],result['osm_fallback'])
