"""Verify the former Customs Club, its raised veranda and neighboring lane houses."""
import argparse
from pathlib import Path
import sys
import tempfile

import numpy as np
import shapely as geo
from shapely.geometry import Point, shape, LineString, box

audit=Path(__file__).resolve().parent
project=audit.parents[2]
sys.path.insert(0,str(project/'tools'))
from build_candidate_city_integrations import checked_geometry
from candidate_placement_meshes import PlacementMeshes, read, sha, write

model='xuhui-fenyang-customs-club'
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--macro',type=Path,required=True)
parser.add_argument('--vector',type=Path,required=True)
parser.add_argument('--manifest',type=Path,default=project/'assets/models/candidates'/model/'manifest.json')
parser.add_argument('--out',type=Path,default=audit)
args=parser.parse_args()
source_path=project/'source/precise'/model/'footprint-review.json'
source,vector,manifest=read(source_path),read(args.vector),read(args.manifest)
assert manifest['id']==model and vector['sha256']=='36448c327185ab13a8d07e723bda4d00dec0c1d36c6831a4c6aa50de13a07893'
owner=source['owner']
group,=source['near_tiles']
assert owner['feature_local_id']==784 and len(group['feature_local_ids'])==21
with tempfile.TemporaryDirectory()as folder:
    scratch=Path(folder)
    for binding in source['frozen_bindings']:
        name=binding['repository_path'].split(owner['macro_id']+'/')[1]
        (scratch/Path(name).name).symlink_to((args.macro/name).resolve())
    site=PlacementMeshes(project,scratch,source)
    assets,bounds,profile,ground=site.decode_model(args.manifest)
    collision=ground.buffer(.03,join_style='mitre').simplify(.035,preserve_topology=True)
    assert ground.difference(collision).area<.025
    original=site.footprints[784]
    decoded=site.decode_group(group,784)
    originals={role:site.project_faces(v[0])for role,v in decoded.items()}
    peers={role:site.project_faces(v[1])for role,v in decoded.items()}
    mask=geo.union_all([profile,original,*originals.values()]).buffer(.06,join_style='mitre').simplify(.025,preserve_topology=True)
    assert all(g.difference(mask).area<.00001 for g in [profile,original,*originals.values()])
    gaps={i:dict(removed_m2=g.intersection(mask).area,gap_m=g.distance(mask)) for i,g in site.footprints.items()if i!=784}
    assert all(g['removed_m2']==0 and g['gap_m']>.5 for g in gaps.values())
    assert all(g.distance(mask)>.6 for g in peers.values())
    affected=[]
    for item in vector['nearby_features']:
        geom=geo.transform(shape(item['geometry']),site.to_xy)
        components=list(geom.geoms) if hasattr(geom,'geoms') else [geom]
        intersects=[g for g in components if g.intersection(mask).area>.001]
        if intersects:
            union=geo.union_all([geo.make_valid(g) for g in intersects])
            affected.append({'id':item['id'],'original_components':len(components),'affected_components':len(intersects),
                             'removed_m2':union.intersection(mask).area,'component_residual_m2':union.difference(mask).area})
    assert vector['total_tile_buildings']==41 and len(affected)==1 and affected[0]['id']==38934830
    assert affected[0]['affected_components']==1 and 290<affected[0]['removed_m2']<360
    lane=LineString(site.to_xy(np.array(source['street']['coords'])))
    assert lane.distance(mask)>15 and lane.distance(collision)>15
    probes=[]
    tests=[('timber house centre',0,0,True),('recessed veranda room',.8,-6.7,True),
           ('front garden step',0,-9.21,True),('side of porch floor',7.9,-7.26,True),
           ('northwest room',-7.48,5.7,True),('garden ahead of stair',.2,-10.1,False),
           ('west lane',-10.30,1.12,False),('garden left of stair',-3.2,-8.85,False),
           ('east lane',10.25,1.5,False)]
    for name,x,y,blocked in tests:
        point=Point(x,y);assert collision.covers(point)==blocked,(name,collision.covers(point))
        probes.append(dict(label=name,xy=[x,y],point=site.to_wgs(np.array([[x,y]]))[0].tolist(),model_collision=blocked,under_mask=mask.covers(point)))
    contract={'id':model,**source['author_frame']['anchor'],'heading':source['author_frame']['runtime_heading_deg'],
              'scale':1,'altitude':0,'owner':{'macro_id':owner['macro_id'],'feature_local_id':784},
              'source_feature_ids':{'building':[owner['source_key'].split(':')[1]],'building_part':[]},
              'model_geometry_sha256':{k:v['sha256']for k,v in assets.items()},'bounds_glb':bounds,
              'replacement_geometry':site.wgs(mask),'collision_geometry':site.wgs(collision),
              'overviewBearing':-30,'overviewPitch':34,'overviewZoom':20.16,'maxDistance':670,'lod_switch_in_m':620,'lod_switch_out_m':820,
              'placement':{'status':'estimated','note':'1898年木屋按保护铭牌门牌、2018和2020年带廊屋顶照片及三版正射影像定位至近方形784。保留庭院、西侧小体2520及附近各排住宅。'},
              'navigation':{'listed':False,'status':'在院内查看抬高的方柱木廊、中央绿窗与几组翘檐老虎窗。'},
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
                other_group_owners={i:gaps[i] for i in group['feature_local_ids'] if i!=784},
                adjacent_sources={i:gaps[int(i)] for i in source['neighboring_buildings']},nearest_source=min(gaps,key=lambda i:gaps[i]['gap_m']),
                surveyed_lane={'osm_way':source['street']['osm_way'],'distance_to_mask_m':lane.distance(mask),'distance_to_ground_collision_m':lane.distance(collision)},
                fallback_tile_count=vector['total_tile_buildings'],fallback_affected=affected,osm_fallback={'sha256':vector['sha256'],'features':41,'affected':affected})
    write(args.out/'placement-geometry.json',result)
    print('Fenyang Customs Club',states,result['surveyed_lane'],result['osm_fallback'])
