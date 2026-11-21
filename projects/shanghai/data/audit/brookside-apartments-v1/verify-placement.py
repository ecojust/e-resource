"""Verify the garden-facing apartment block, the three garden-facing segments, streets and contiguous native neighbors."""
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

model='jingan-brookside-apartments'
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--macro',type=Path,required=True)
parser.add_argument('--vector',type=Path,required=True)
parser.add_argument('--manifest',type=Path,default=project/'assets/models/candidates'/model/'manifest.json')
parser.add_argument('--out',type=Path,default=audit)
args=parser.parse_args()
source_path=project/'source/precise'/model/'footprint-review.json'
source,vector,manifest=read(source_path),read(args.vector),read(args.manifest)
assert manifest['id']==model and vector['sha256']=='ef9df460f908f294d516f8753ac4366603662b592d4fb5bd2c214df51e6cf5e0'
owner=source['owner']
group,=source['near_tiles']
assert owner['feature_local_id']==2669 and len(group['feature_local_ids'])==7
with tempfile.TemporaryDirectory()as folder:
    scratch=Path(folder)
    for binding in source['frozen_bindings']:
        name=binding['repository_path'].split(owner['macro_id']+'/')[1]
        (scratch/Path(name).name).symlink_to((args.macro/name).resolve())
    site=PlacementMeshes(project,scratch,source)
    assets,bounds,profile,ground=site.decode_model(args.manifest)
    # Use the floor-and-door mesh at walking height. Retain its individual garden
    # steps while removing the centimetre-scale recesses of the shallow windows.
    for ground_tolerance in (.035,.05,.065,.08,.095,.12):
        candidate=ground.simplify(ground_tolerance,preserve_topology=True).buffer(ground_tolerance,join_style='mitre').simplify(.02)
        if ground.difference(candidate).area>.0001 or ground.hausdorff_distance(candidate)>.18:
            continue
        try:
            checked_geometry(site.wgs(candidate),'collision_geometry',collision=True)
        except AssertionError:
            continue
        collision=candidate
        break
    else:
        raise AssertionError('Could not retain the garden steps within the walking collision budget')
    original=site.footprints[2669]
    decoded=site.decode_group(group,2669)
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
    gaps={i:dict(removed_m2=g.intersection(mask).area,gap_m=g.distance(mask)) for i,g in site.footprints.items()if i!=2669}
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
    assert vector['total_tile_buildings']==23 and len(affected)==1 and affected[0]['id']==147898520
    assert affected[0]['affected_components']==1 and 755<affected[0]['removed_m2']<775
    lane=LineString(site.to_xy(np.array(source['street']['coords'])))
    assert lane.distance(mask)>6 and lane.distance(collision)>6
    surveyed_streets=[]
    for route in source['surveyed_streets']:
        line=LineString(site.to_xy(np.array(route['coords'])))
        assert line.distance(mask)>6 and line.distance(collision)>6
        surveyed_streets.append({'name':route['name'],'osm_way':route['osm_way'],'distance_to_mask_m':line.distance(mask),'distance_to_collision_m':line.distance(collision)})
    probes=[]
    tests=[('centre garden door landing',8.74,4.20,True),('west garden wing',-16.45,-7.15,True),
           ('east short wing',27.45,-1.40,True),('west wing end',-27.50,-17.15,True),
           ('rear of middle segment',8.72,11.10,True),('garden below crest',8.74,-.55,False),
           ('garden in front of west wing',-11.35,-12.2,False),('outside east wing',36.7,-5.4,False),
           ('outside west wing',-34.9,-22.4,False),('rear roadway side',1.22,14.65,False)]
    for name,x,y,blocked in tests:
        point=Point(x,y);assert collision.covers(point)==blocked,(name,collision.covers(point))
        probes.append(dict(label=name,xy=[x,y],point=site.to_wgs(np.array([[x,y]]))[0].tolist(),model_collision=blocked,under_mask=mask.covers(point)))
    contract={'id':model,**source['author_frame']['anchor'],'heading':source['author_frame']['runtime_heading_deg'],
              'scale':1,'altitude':0,'owner':{'macro_id':owner['macro_id'],'feature_local_id':2669},
              'source_feature_ids':{'building':[owner['source_key'].split(':')[1]],'building_part':[]},
              'model_geometry_sha256':{k:v['sha256']for k,v in assets.items()},'bounds_glb':bounds,
              'replacement_geometry':site.wgs(mask),'collision_geometry':site.wgs(collision),
              'overviewBearing':-15,'overviewPitch':49,'overviewZoom':18.82,'maxDistance':670,'lod_switch_in_m':620,'lod_switch_out_m':820,
              'placement':{'status':'estimated','note':'以市表2B020、2019年飞行相机、2023年庭院正照和三期航片定位华山路731号。底图2669覆盖长翼、中段和短东翼；地面位置、局部开间和屋顶设备按实照与原生轮廓估计。'},
              'navigation':{'listed':False,'status':'从南花园可见折翼围合的立面、中央透空券列和两侧凸窗。'},
              'partial_model':True,'model_scope':manifest['model_scope_zh']}
    for key in ['replacement_geometry','collision_geometry']:checked_geometry(contract[key],key,collision=key=='collision_geometry')
    args.out.mkdir(parents=True,exist_ok=True)
    write(args.out/'final-placement-contract.json',contract)
    states={role:{'old_area_m2':originals[role].area,'remaining_m2':originals[role].difference(mask).area,
                  'old_top_m':float(decoded[role][0][:,:,2].max()),'other_triangles_gap_m':peers[role].distance(mask),'assignment':decoded[role][2]}for role in decoded}
    result=dict(id=model,script_sha256=sha(Path(__file__)),manifest_sha256=sha(args.manifest),source_sha256=sha(source_path),
                contract_sha256=sha(args.out/'final-placement-contract.json'),assets=assets,group=group,source_records=states,
                source_outline_m2=original.area,display_m2=profile.area,display_outside_source_m2=profile.difference(original).area,
                collision_m2=collision.area,ground_simplify_m=ground_tolerance,max_ground_boundary_deviation_m=ground.hausdorff_distance(collision),uncovered_ground_m2=ground.difference(collision).area,mask_m2=mask.area,replacement_tolerance_m=tolerance,ground_points=probes,
                other_group_owners={i:gaps[i] for i in group['feature_local_ids'] if i!=2669},
                adjacent_sources={i:gaps[int(i)] for i in source['neighboring_buildings']},nearest_source=min(gaps,key=lambda i:gaps[i]['gap_m']),
                surveyed_streets=surveyed_streets,surveyed_lane={'osm_way':source['street']['osm_way'],'distance_to_mask_m':lane.distance(mask),'distance_to_ground_collision_m':lane.distance(collision)},
                fallback_tile_count=vector['total_tile_buildings'],fallback_affected=affected,osm_fallback={'sha256':vector['sha256'],'features':23,'affected':affected})
    write(args.out/'placement-geometry.json',result)
    print('Brookside Apartments',states,result['surveyed_lane'],result['osm_fallback'])
