#!/usr/bin/env python3
"""Validate actual Ba Jin exterior-route evidence; explicitly execute finite source-ground probes only later.

Reads supplied bounded OSM and actual ground notes. Does not fetch sources, invent a
route, move the frozen anchor, accept a model, or change runtime/MAIN.
"""
import argparse
import datetime
import hashlib
import json
import math
import shutil
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from shapely.geometry import LineString, Point, Polygon, shape
from shapely.ops import transform

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
BASE = HERE.parent
sys.path.insert(0,str(BASE))
from screen_frozen_model import navigation_value
ID = 'xuhui-bajin-residence'
CONTROLLER = {'pitch_degrees':82,'camera_distance_m':14,'ahead_m':2.8,
              'target_altitude_above_ground_m':3,'ground_fallback_m':.075}

def encoded(value):
    return (json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode('utf-8')

def planned_descriptor(path,content):
    return {'path':str(path.resolve()),'bytes':len(content),'sha256':hashlib.sha256(content).hexdigest()}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for flag in ('navigation','osm-context','fetch-receipt','visual-ground-review','runtime-scope-review','root-model-review','output'):
        parser.add_argument('--'+flag,type=Path,required=True)
    parser.add_argument('--root-model-review-sha256',required=True)
    mode=parser.add_mutually_exclusive_group()
    mode.add_argument('--check-only',dest='execute_screen',action='store_false')
    mode.add_argument('--execute-screen',action='store_true')
    parser.set_defaults(execute_screen=False)
    a=parser.parse_args()
    import integration_contract as contract
    need,read,desc=contract.need,contract.read,contract.descriptor
    out=contract.fresh_output(a.output,create=False,budget_bytes=2_000_000)
    binding=contract.validate_root_review(a.root_model_review,a.root_model_review_sha256)
    lock=contract.check_baseline();g,neighborhood=contract.check_frozen_inputs()
    frozen=Path(contract.GEOMETRY['path']);neighborhood_path=Path(contract.NEIGHBORHOOD['path'])
    need(len(neighborhood['features'])==80 and neighborhood['anchor']==g['anchor']==contract.ANCHOR,'Wrong frozen source neighbors/frame')
    need(neighborhood['source_geometry']==contract.GEOMETRY,'Frozen neighborhood source binding differs')
    seed=read(a.navigation);nav=navigation_value(seed,g,'bajin-v20-outdoor-navigation-request-v1')
    need(seed.get('source_geometry_sha256')==contract.GEOMETRY['sha256'],'Actual route request must bind frozen source frame')
    context=a.osm_context;receipt=read(a.fetch_receipt);notes=a.visual_ground_review;visual=read(notes)
    context_descriptor=desc(context)
    need(receipt.get('status')==200 and receipt.get('truncated') is False and type(receipt.get('bytes')) is int and 0<receipt['bytes']<=500000,'Complete bounded OSM receipt required')
    need(context_descriptor['sha256']==receipt.get('sha256') and context_descriptor['bytes']==receipt['bytes'],'Actual OSM bytes differ from receipt')
    need(receipt.get('anchor')==contract.ANCHOR,'OSM receipt must concern the frozen Ba Jin anchor')
    need(isinstance(receipt.get('query_bbox'),list) and len(receipt['query_bbox'])==4 and all(type(x) in (int,float) and math.isfinite(x) for x in receipt['query_bbox']),'Finite receipt bbox required')
    need(visual.get('schema')=='bajin-v20-actual-ground-visual-notes-v1' and visual.get('building_id')==ID,'Actual Ba Jin ground visual review required')
    need(visual.get('source_geometry_sha256')==contract.GEOMETRY['sha256'] and visual.get('candidate_navigation')=={k:nav[k] for k in ('walkStart','bearing')},'Ground visual notes must bind the actual requested route')
    observations=visual.get('observations')
    need(isinstance(observations,list) and len(observations)>0,'Ground notes require actual viewed evidence')
    for observation in observations:
        need(observation.get('actually_viewed_this_review') is True and isinstance(observation.get('visible'),list) and observation['visible'] and isinstance(observation.get('limitations'),list),'Ground evidence needs actual observations and limitations')
        need(desc(observation['path'])=={k:observation[k] for k in ('path','bytes','sha256')},'Actual viewed ground evidence changed')
    runtime=[contract.MAIN/path for path in ('src/map-scene.js','src/street-interaction.js','src/walk-controller.js')]
    scope=read(a.runtime_scope_review)
    need(scope.get('schema')=='bajin-v20-runtime-collision-scope-review-v1' and scope.get('building_id')==ID,'Actual Ba Jin runtime scope review required')
    need(scope.get('source_geometry_sha256')==contract.GEOMETRY['sha256'] and scope.get('controller_parameters')==CONTROLLER,'Runtime scope/default controller binding differs')
    need(scope.get('runtime_files')==[desc(p) for p in runtime],'Runtime scope must bind the actual three controller sources')
    watched=[frozen,neighborhood_path,context,a.fetch_receipt,notes,a.runtime_scope_review,a.navigation,Path(__file__),BASE/'screen_frozen_model.py',*runtime,*[Path(row['path']) for row in observations]]
    before=[desc(p) for p in watched]
    if not a.execute_screen:
        print(json.dumps({'status':'REAL_INPUTS_CHECKED_NO_SOURCE_GROUND_SCREEN_EXECUTED','root_source_owner_authorization':binding,'input_descriptors':before,'screen_executed':False,'output_created':False,'browser_passed':False},indent=2))
        return
    lon0, lat0 = g['anchor']
    R, c = 6378137., math.cos(math.radians(lat0))
    merc0 = math.asinh(math.tan(math.radians(lat0)))
    def project(lon, lat, z=None):
        return R * math.radians(lon-lon0) * c, R * (math.asinh(math.tan(math.radians(lat)))-merc0) * c
    def geographic(xy):
        return [lon0 + math.degrees(xy[0] / (R*c)), math.degrees(math.atan(math.sinh(merc0 + xy[1] / (R*c))))]
    owner = transform(project, shape(g['geometry']))
    xml = ET.parse(context).getroot()
    nodes = {n.attrib['id']: project(float(n.attrib['lon']), float(n.attrib['lat'])) for n in xml.findall('node')}
    ways, incomplete, invalid = [], [], []
    for w in xml.findall('way'):
        tags = {t.attrib['k']: t.attrib['v'] for t in w.findall('tag')}
        refs = [n.attrib['ref'] for n in w.findall('nd')]
        if not refs or any(r not in nodes for r in refs):
            incomplete.append(w.attrib['id']); continue
        xy = [nodes[r] for r in refs]
        geometry = Polygon(xy) if len(xy) > 3 and refs[0] == refs[-1] else LineString(xy) if len(xy) > 1 else Point(xy[0])
        if not geometry.is_valid or (('building' in tags or 'building:part' in tags) and geometry.geom_type!='Polygon'):
            invalid.append(w.attrib['id']); continue
        ways.append({'id': w.attrib['id'], 'version': w.attrib.get('version'), 'tags': tags, 'geometry': geometry})
    def water(tags):
        return tags.get('natural') == 'water' or 'waterway' in tags or 'water' in tags or tags.get('landuse') in ('reservoir','basin') or tags.get('leisure') == 'swimming_pool' or tags.get('amenity') == 'fountain'
    waters = [w for w in ways if water(w['tags'])]
    def water_area(tags):
        return tags.get('natural')=='water' or 'water' in tags or tags.get('landuse') in ('reservoir','basin') or tags.get('leisure')=='swimming_pool' or tags.get('amenity')=='fountain'
    nonpolygon_water_areas=[{'id':way['id'],'tags':way['tags'],'geometry_type':way['geometry'].geom_type,'requires_extent_review':True} for way in waters if water_area(way['tags']) and way['geometry'].geom_type!='Polygon']
    water_nodes=[]
    for node in xml.findall('node'):
        tags={tag.attrib['k']:tag.attrib['v'] for tag in node.findall('tag')}
        if water(tags):water_nodes.append({'id':node.attrib['id'],'tags':tags,'local_east_north_m':nodes[node.attrib['id']],'requires_extent_review':True})
    water_relations = []
    building_relations = []
    for rel in xml.findall('relation'):
        tags = {t.attrib['k']: t.attrib['v'] for t in rel.findall('tag')}
        if water(tags):
            water_relations.append({'id': rel.attrib['id'], 'tags': tags, 'requires_member_geometry_review': True})
        if 'building' in tags or 'building:part' in tags:
            building_relations.append({'id': rel.attrib['id'], 'tags': tags, 'requires_member_geometry_review': True})
    buildings = [w for w in ways if 'building' in w['tags'] or 'building:part' in w['tags']]
    highways = [w for w in ways if 'highway' in w['tags']]
    neighbors = [(row, shape(row['geometry_local_east_north_m'])) for row in neighborhood['features']]
    def probes_for(start, bearing):
        radians = math.radians(bearing)
        u = math.sin(radians), math.cos(radians)
        at = lambda distance: [start[i] + u[i] * distance for i in (0,1)]
        end, target, eye = at(5), at(2.8), at(2.8-math.sin(math.radians(82))*14)
        probes = {'avatar': (Point(start), .38), 'forward_5m': (LineString([start,end]), .38), 'camera': (Point(eye), .12), 'camera_boom': (LineString([target,eye]), .12)}
        controller = {'pitch_degrees':82,'camera_distance_m':14,'ahead_m':2.8,'target_ground_projection_local_enu_m':target,'camera_ground_projection_local_enu_m':eye,'target_altitude_above_ground_m':3,'camera_altitude_above_ground_m':3+math.cos(math.radians(82))*14,'ground_fallback_m':.075}
        return probes, controller, end
    def source_checks(probes):
        result = {}
        for name, (p, radius) in probes.items():
            current = sorted([{'osm_way':w['id'],'version':w['version'],'name':w['tags'].get('name'),'clearance_m':w['geometry'].distance(p)-radius} for w in buildings], key=lambda r:r['clearance_m'])
            effective = sorted([{'macro':r['macro'],'key':r['key'],'local_id':r['local_id'],'clearance_m':geom.distance(p)-radius} for r,geom in neighbors], key=lambda r:r['clearance_m'])
            result[name] = {'radius_m':radius,'frozen_source_owner_clearance_m':owner.distance(p)-radius,'live_osm_building_nearest':current[:3],'live_osm_building_intersections':[r for r in current if r['clearance_m']<=0],'effective_neighbor_nearest':effective[:3],'effective_neighbor_intersections':[r for r in effective if r['clearance_m']<=0]}
        return result
    start=list(project(*nav['walkStart']));bearing=nav['bearing']
    probes,controller,end=probes_for(start,bearing)
    checks=source_checks(probes)
    selected={'id':seed['candidate_id'],'spawn_local_enu_m':start,'walkStart':nav['walkStart'],'bearing':bearing,'first_5m_endpoint_local_enu_m':end,'controller_default':controller,'source_checks':checks,'source_geometry_clear_only':all(row['frozen_source_owner_clearance_m']>0 and not row['live_osm_building_intersections'] and not row['effective_neighbor_intersections'] for row in checks.values()),'final_model_screened':False,'ground_surface_verified':False,'public_path_membership_verified':False}
    limitations=[
        'Only the supplied actual outdoor route is screened. Detailed raw mesh, camera poses and browser movement require separate checks.',
        'The frozen source-owner polygon is mapped replacement context, not a surveyed architectural wall.',
        'Ground observations are explicitly route-bound notes; no historical photograph, garden context or road centerline proves a current paved/public route.',
        'Current bounded OSM building/water features and all 80 frozen neighbors are screened for finite probe nonintersection; furniture, trees, gates and access restrictions are not a complete obstacle inventory.',
        'The default 14 m camera boom is airborne. Its projected clearance is not pedestrian ground support.',
        'Runtime collision uses loaded map polygons and explicit proxies; ordinary model walls, windows, doors and stairs do not automatically create collision or ground surfaces.',
        'Default ground 0.075 m is not measured ground elevation. Interiors, annexes, garden reconstruction, stair climbing and arbitrary routes are outside the authored model scope.',
        'No mapped water in the bounded response does not physically establish water absence; incomplete or invalid geometry prevents this screen passing.',
    ]
    proposal={'schema':'bajin-v20-working-exterior-navigation-seed','building_id':ID,'status':'ACTUAL_SOURCE_GROUND_SCREEN_ONLY_MESH_AND_BROWSER_PENDING','navigation':nav,'candidate_id':selected['id'],'route_scope':'exterior_only','ground_access_note':seed['ground_access_note'],'source_geometry_sha256':contract.GEOMETRY['sha256'],'spawn_local_enu_m':start,'first_5m_endpoint_local_enu_m':end,'controller_default':controller,'final_model_accepted':False,'browser_passed':False,'precise_public_sidewalk_membership_verified':False,'current_clear_pedestrian_width_verified':False,'coordinate_contract':contract.GEOMETRY,'root_source_owner_authorization':binding,'navigation_request':desc(a.navigation),'limitations':limitations}
    start, forward = probes['avatar'][0], probes['forward_5m'][0]
    near_highways = sorted([{'osm_way':w['id'],'version':w['version'],'tags':w['tags'],'distance_to_start_centerline_m':w['geometry'].distance(start),'distance_to_first5m_centerline_m':w['geometry'].distance(forward),'distance_is_not_curb_or_lane_edge':True} for w in highways],key=lambda r:r['distance_to_start_centerline_m'])
    tagged_nodes = []
    for n in xml.findall('node'):
        tags = {t.attrib['k']:t.attrib['v'] for t in n.findall('tag')}
        if tags and Point(nodes[n.attrib['id']]).distance(start)<40:
            tagged_nodes.append({'osm_node':n.attrib['id'],'tags':tags,'local_east_north_m':nodes[n.attrib['id']],'distance_to_start_m':Point(nodes[n.attrib['id']]).distance(start)})
    need(xml.find('bounds') is not None,'Bounded OSM response has no bounds')
    bounds = xml.find('bounds').attrib
    actual_bbox=[float(bounds[k]) for k in ('minlon','minlat','maxlon','maxlat')]
    need(all(abs(x-y)<2e-6 for x,y in zip(actual_bbox,receipt['query_bbox'])),'Response bounds differ from actual fetch receipt')
    need(actual_bbox[0]<lon0<actual_bbox[2] and actual_bbox[1]<lat0<actual_bbox[3],'Bounded source response must contain the frozen anchor')
    bbox = Polygon([project(float(bounds['minlon']),float(bounds['minlat'])),project(float(bounds['maxlon']),float(bounds['minlat'])),project(float(bounds['maxlon']),float(bounds['maxlat'])),project(float(bounds['minlon']),float(bounds['maxlat']))])
    in_bounds = all(bbox.covers(p.buffer(radius)) for p,radius in probes.values())
    in_frozen_radius=all(Point(0,0).buffer(110).covers(p.buffer(radius)) for p,radius in probes.values())
    water_checks = [{'osm_way':w['id'],'version':w['version'],'tags':w['tags'],'geometry_type':w['geometry'].geom_type,'probe_clearance_m':{name:w['geometry'].distance(p)-radius for name,(p,radius) in probes.items()}} for w in waters]
    source_pass = not(incomplete or invalid or water_relations or building_relations or water_nodes or nonpolygon_water_areas) and in_bounds and in_frozen_radius and selected['source_geometry_clear_only'] and all(min(r['probe_clearance_m'].values())>0 for r in water_checks)
    proposal['status']='ACTUAL_SOURCE_GROUND_SCREEN_ONLY_MESH_AND_BROWSER_PENDING' if source_pass else 'ACTUAL_SOURCE_GROUND_SCREEN_FAILED'
    proposal_bytes=encoded(proposal)
    candidate_binding=planned_descriptor(out/'navigation-proposal.json',proposal_bytes)
    report={
        'schema':'bajin-v20-bounded-source-ground-review',
        'created_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'building_id':ID,'root_source_owner_authorization':binding,
        'passed_source_screen_only':source_pass,
        'scope_of_pass':'Only complete bounded mapped building/water and all 80 frozen-neighbor finite-probe nonintersection. No measured paving, public-sidewalk/access, final mesh or browser acceptance.',
        'final_model_accepted':False,'browser_passed':False,'main_written':False,
        'precise_public_sidewalk_membership_verified':False,'current_clear_pedestrian_width_verified':False,
        'candidate_binding':candidate_binding,'candidate_id':selected['id'],
        'candidate_navigation':{k:nav[k] for k in ('walkStart','bearing')},
        'coordinate_contract':contract.GEOMETRY,'effective_neighborhood':contract.NEIGHBORHOOD,
        'effective_neighbors_checked':len(neighbors),'osm_input':desc(context),'fetch':receipt,
        'fetch_receipt':desc(a.fetch_receipt),'navigation_request':desc(a.navigation),
        'osm_counts':{key:len(xml.findall(key)) for key in ('node','way','relation')},
        'query_bbox':bounds,'all_probe_buffers_inside_requested_bbox':in_bounds,
        'all_probe_buffers_inside_frozen_neighborhood_radius':in_frozen_radius,
        'incomplete_way_node_refs':incomplete,'invalid_way_geometries':invalid,
        'mapped_water_or_fountain_ways':water_checks,'water_relations_pending':water_relations,
        'water_nodes_pending':water_nodes,'nonpolygon_water_areas_pending':nonpolygon_water_areas,
        'building_relations_pending':building_relations,
        'live_osm_building_checks':{name:{'nearest':row['live_osm_building_nearest'],'intersections':row['live_osm_building_intersections']} for name,row in checks.items()},
        'frozen_source_and_effective_neighbor_checks':checks,'nearest_highways':near_highways,
        'nearest_explicit_footway':next((row for row in near_highways if row['tags'].get('highway')=='footway'),None),
        'tagged_nodes_within40m':tagged_nodes,
        'source_land_at_start':[{'osm_way':way['id'],'tags':way['tags']} for way in ways if way['geometry'].geom_type=='Polygon' and any(key in way['tags'] for key in ('landuse','surface','leisure','area:highway')) and way['geometry'].covers(start)],
        'visual_ground_review':desc(notes),'runtime_source_inputs':[desc(path) for path in runtime],
        'runtime_scope_review':desc(a.runtime_scope_review),'tool':desc(__file__),
        'input_preservation':{'all_watched_exact':True,'files':before},'limitations':limitations,
    }
    comparison={'schema':'bajin-v20-actual-request-source-probe-comparison','accepted':False,
                'candidate_binding':candidate_binding,'tool':desc(__file__),'choices':[selected],
                'selected_id':selected['id'],'root_source_owner_authorization':binding,
                'selection_scope':'One actual externally supplied exterior route. No default or alternative route is invented by the tool; source nonintersection is not paving or public-access proof.'}
    payload={'navigation-proposal.json':proposal_bytes,'source-ground-review.json':encoded(report),'source-probe-comparison.json':encoded(comparison)}
    need(before==[desc(path) for path in watched],'Source/runtime/actual route inputs changed')
    need(binding==contract.validate_root_review(a.root_model_review,a.root_model_review_sha256),'Root-bound mesh inputs changed')
    contract.check_baseline();contract.check_frozen_inputs()
    total=sum(map(len,payload.values()))
    need(total<2_000_000,'Source-ground output exceeds 2MB budget')
    need(shutil.disk_usage(BASE).free>=300_000_000+total,'Source-ground output would breach 300MB reserve')
    contract.fresh_output(a.output,create=True,budget_bytes=2_000_000)
    for name,content in payload.items():
        with (out/name).open('xb') as handle:handle.write(content)
    need(desc(out/'navigation-proposal.json')==candidate_binding,'Written navigation differs from computed binding')
    need(shutil.disk_usage(BASE).free>=300_000_000,'Source-ground output breached 300MB reserve')
    print(json.dumps({'report':desc(out/'source-ground-review.json'),'source_screen_only':source_pass,'all_probes_in_bbox':in_bounds,'all_probes_in_frozen_radius':in_frozen_radius,'effective_neighbors':len(neighbors),'browser_passed':False},ensure_ascii=False))


if __name__=='__main__':
    try:main()
    except (ValueError,KeyError,TypeError,OSError,ET.ParseError) as error:
        print('BAJIN_SOURCE_GROUND_SCREEN_REJECTED: '+str(error),file=sys.stderr);sys.exit(2)
