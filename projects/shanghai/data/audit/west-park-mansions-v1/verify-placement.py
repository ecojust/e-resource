"""Verify the garden-facing apartment block, both rear lightwells, streets and contiguous native neighbors."""
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

model='changning-west-park-mansions'
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--macro',type=Path,required=True)
parser.add_argument('--vector',type=Path,required=True)
parser.add_argument('--manifest',type=Path,default=project/'assets/models/candidates'/model/'manifest.json')
parser.add_argument('--out',type=Path,default=audit)
args=parser.parse_args()
source_path=project/'source/precise'/model/'footprint-review.json'
source,vector,manifest=read(source_path),read(args.vector),read(args.manifest)
assert manifest['id']==model and vector['sha256']=='c5824df4fb6342396438a7be13d89dad90c0030abb03e8f757dfd28c2b136417'
owner=source['owner']
group,=source['near_tiles']
assert owner['feature_local_id']==271 and len(group['feature_local_ids'])==18
with tempfile.TemporaryDirectory()as folder:
    scratch=Path(folder)
    for binding in source['frozen_bindings']:
        name=binding['repository_path'].split(owner['macro_id']+'/')[1]
        (scratch/Path(name).name).symlink_to((args.macro/name).resolve())
    site=PlacementMeshes(project,scratch,source)
    assets,bounds,profile,ground=site.decode_model(args.manifest)
    collision=ground.buffer(.03,join_style='mitre').simplify(.035,preserve_topology=True)
    assert ground.difference(collision).area<.025
    original=site.footprints[271]
    decoded=site.decode_group(group,271)
    originals={role:site.project_faces(v[0])for role,v in decoded.items()}
    peers={role:site.project_faces(v[1])for role,v in decoded.items()}
    envelope = geo.union_all([profile, original, *originals.values()])
    # Rounded mesh vertices, projecting sills and end quoins add many tiny turns.
    # Choose the tightest exterior polygon that covers every native fragment and
    # meets the runtime ring budget. The complete neighboring meshes are checked below.
    for tolerance in (.035, .065, .095, .14, .20, .30, .42):
        simple = envelope.simplify(tolerance, preserve_topology=True)
        candidate = simple.buffer(tolerance + .055, join_style='mitre').simplify(.018, preserve_topology=True)
        if envelope.difference(candidate).area > .000001:
            continue
        try:
            checked_geometry(site.wgs(candidate), 'replacement_geometry')
        except AssertionError:
            continue
        mask = candidate
        break
    else:
        raise AssertionError('The garden block requires an exterior with more than 65 points')
    assert all(g.difference(mask).area<.00001 for g in [profile,original,*originals.values()])
    gaps={i:dict(removed_m2=g.intersection(mask).area,gap_m=g.distance(mask)) for i,g in site.footprints.items()if i!=271}
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
    assert vector['total_tile_buildings']==293 and len(affected)==1 and affected[0]['id']==59590660
    assert affected[0]['affected_components']==1 and 500<affected[0]['removed_m2']<560
    lane=LineString(site.to_xy(np.array(source['street']['coords'])))
    assert lane.distance(mask)>6 and lane.distance(collision)>6
    surveyed_streets=[]
    for route in source['surveyed_streets']:
        line=LineString(site.to_xy(np.array(route['coords'])))
        assert line.distance(mask)>6 and line.distance(collision)>6
        surveyed_streets.append({'name':route['name'],'osm_way':route['osm_way'],'distance_to_mask_m':line.distance(mask),'distance_to_collision_m':line.distance(collision)})
    probes=[]
    tests=[('south apartment entrance',0,-8.8,True),('west tower foot',-9.3,-8.95,True),
           ('east tower foot',8.91,-8.98,True),('rear center pier',-.25,7.94,True),
           ('northwest wing',-11.7,9.71,True),('east lightwell lower volume',4.62,7.55,True),
           ('west lightwell lower volume',-5.39,7.41,True),('clear garden',.38,-12.2,False),
           ('west courtyard lane',-15.48,-1.22,False),('behind central pier',.35,10.97,False),('north garden behind east well',4.62,9.64,False)]
    for name,x,y,blocked in tests:
        point=Point(x,y);assert collision.covers(point)==blocked,(name,collision.covers(point))
        probes.append(dict(label=name,xy=[x,y],point=site.to_wgs(np.array([[x,y]]))[0].tolist(),model_collision=blocked,under_mask=mask.covers(point)))
    contract={'id':model,**source['author_frame']['anchor'],'heading':source['author_frame']['runtime_heading_deg'],
              'scale':1,'altitude':0,'owner':{'macro_id':owner['macro_id'],'feature_local_id':271},
              'source_feature_ids':{'building':[owner['source_key'].split(':')[1]],'building_part':[]},
              'model_geometry_sha256':{k:v['sha256']for k,v in assets.items()},'bounds_glb':bounds,
              'replacement_geometry':site.wgs(mask),'collision_geometry':site.wgs(collision),
              'overviewBearing':10,'overviewPitch':44,'overviewZoom':19.36,'maxDistance':670,'lod_switch_in_m':620,'lod_switch_out_m':820,
              'placement':{'status':'estimated','note':'按市表2M004、2014年南面庭院实照、2021年长宁路街面与具名底图271安放。庭院、南面其他住宅和北侧道路保留，层高、窗井进深和封窗细节按照片比例估算。'},
              'navigation':{'listed':False,'status':'从南侧庭院可见三组宽浅拱、住户围合的阳台与两端屋顶花架。'},
              'partial_model':True,'model_scope':manifest['model_scope_zh']}
    for key in ['replacement_geometry','collision_geometry']:checked_geometry(contract[key],key,collision=key=='collision_geometry')
    args.out.mkdir(parents=True,exist_ok=True)
    write(args.out/'final-placement-contract.json',contract)
    states={role:{'old_area_m2':originals[role].area,'remaining_m2':originals[role].difference(mask).area,
                  'old_top_m':float(decoded[role][0][:,:,2].max()),'other_triangles_gap_m':peers[role].distance(mask),'assignment':decoded[role][2]}for role in decoded}
    result=dict(id=model,script_sha256=sha(Path(__file__)),manifest_sha256=sha(args.manifest),source_sha256=sha(source_path),
                contract_sha256=sha(args.out/'final-placement-contract.json'),assets=assets,group=group,source_records=states,
                source_outline_m2=original.area,display_m2=profile.area,display_outside_source_m2=profile.difference(original).area,
                collision_m2=collision.area,mask_m2=mask.area,replacement_tolerance_m=tolerance,ground_points=probes,
                other_group_owners={i:gaps[i] for i in group['feature_local_ids'] if i!=271},
                adjacent_sources={i:gaps[int(i)] for i in source['neighboring_buildings']},nearest_source=min(gaps,key=lambda i:gaps[i]['gap_m']),
                surveyed_streets=surveyed_streets,surveyed_lane={'osm_way':source['street']['osm_way'],'distance_to_mask_m':lane.distance(mask),'distance_to_ground_collision_m':lane.distance(collision)},
                fallback_tile_count=vector['total_tile_buildings'],fallback_affected=affected,osm_fallback={'sha256':vector['sha256'],'features':293,'affected':affected})
    write(args.out/'placement-geometry.json',result)
    print('West Park Mansions',states,result['surveyed_lane'],result['osm_fallback'])
