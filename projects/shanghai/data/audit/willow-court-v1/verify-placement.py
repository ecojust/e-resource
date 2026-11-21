"""Check the Willow Court tower, the raised entrance, the eastern vehicle route, the garden, and adjoining native buildings."""
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

model='xuhui-willow-court'
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
assert owner['feature_local_id']==4000 and len(group['feature_local_ids'])==17
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
    original=site.footprints[4000]
    decoded=site.decode_group(group,4000)
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
    gaps={i:dict(removed_m2=g.intersection(mask).area,gap_m=g.distance(mask)) for i,g in site.footprints.items()if i!=4000}
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
    assert affected[0]['affected_components']==1 and 345<affected[0]['removed_m2']<360
    lane=LineString(site.to_xy(np.array(source['street']['coords'])))
    assert lane.distance(mask)>6 and lane.distance(collision)>6
    surveyed_streets=[]
    for route in source['surveyed_streets']:
        line=LineString(site.to_xy(np.array(route['coords'])))
        assert line.distance(mask)>6 and line.distance(collision)>6
        surveyed_streets.append({'name':route['name'],'osm_way':route['osm_way'],'distance_to_mask_m':line.distance(mask),'distance_to_collision_m':line.distance(collision)})
    probes=[]
    tests=[('centre of main building',0,0,True),('garden entry threshold',0,-7.10,True),
           ('raised garden steps',0,-8.45,True),('east drive centre',9.9,0,False),
           ('east drive south mouth',9.9,-6.7,False),('east drive north mouth',9.9,6.8,False),
           ('west recessed loggia',-9.9,-5.5,False),('west loggia back wall',-9.9,1.2,True),
           ('west side wall',-12.14,-3.25,True),('front garden',0,-11.2,False),
           ('east neighboring gap',13.42,1.4,False),('north courtyard',1.4,8.4,False)]
    for name,x,y,blocked in tests:
        point=Point(x,y);assert collision.covers(point)==blocked,(name,collision.covers(point))
        probes.append(dict(label=name,xy=[x,y],point=site.to_wgs(np.array([[x,y]]))[0].tolist(),model_collision=blocked,under_mask=mask.covers(point)))
    contract={'id':model,**source['author_frame']['anchor'],'heading':source['author_frame']['runtime_heading_deg'],
              'scale':1,'altitude':0,'owner':{'macro_id':owner['macro_id'],'feature_local_id':4000},
              'source_feature_ids':{'building':[owner['source_key'].split(':')[1]],'building_part':[]},
              'model_geometry_sha256':{k:v['sha256']for k,v in assets.items()},'bounds_glb':bounds,
              'replacement_geometry':site.wgs(mask),'collision_geometry':site.wgs(collision),
              'overviewBearing':-23,'overviewPitch':53,'overviewZoom':18.67,'maxDistance':670,'lod_switch_in_m':620,'lod_switch_out_m':820,
              'placement':{'status':'estimated','note':'据市表2D043、徐汇区房管局所引历史总平面、1935年外观和三期航片定位复兴西路34号院内主楼。主体与底图4000对应，南侧抬高阶梯和弧形阳台向花园挑出。高度、窗距与侧背面分格依照片估计。'},
              'navigation':{'listed':False,'status':'从南花园可见半圆门阶、逐层外挑的红色弧形阳台和两端内阳台。'},
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
                other_group_owners={i:gaps[i] for i in group['feature_local_ids'] if i!=4000},
                adjacent_sources={i:gaps[int(i)] for i in source['neighboring_buildings']},nearest_source=min(gaps,key=lambda i:gaps[i]['gap_m']),
                surveyed_streets=surveyed_streets,surveyed_lane={'osm_way':source['street']['osm_way'],'distance_to_mask_m':lane.distance(mask),'distance_to_ground_collision_m':lane.distance(collision)},
                fallback_tile_count=vector['total_tile_buildings'],fallback_affected=affected,osm_fallback={'sha256':vector['sha256'],'features':23,'affected':affected})
    write(args.out/'placement-geometry.json',result)
    print('Willow Court',states,result['surveyed_lane'],result['osm_fallback'])
