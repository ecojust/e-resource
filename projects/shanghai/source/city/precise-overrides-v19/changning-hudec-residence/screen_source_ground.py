#!/usr/bin/env python3
"""Read the one bounded OSM response and frozen source context; no mesh or release acceptance."""
import datetime
import hashlib
import json
import math
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from shapely.geometry import LineString, Point, Polygon, shape
from shapely.ops import transform

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
BASE = HERE.parent
MAIN = Path('/workspace/shanghai_project')
ID = 'changning-hudec-residence'
NEIGHBORHOOD_SHA = '0e88ea824d1f573f2fb9db5dcfddb42b64b049dfcae36882d3c1b12bb2c25008'

def read(path):
    return json.loads(Path(path).read_text())

def desc(path):
    path = Path(path).resolve()
    data = path.read_bytes()
    return {'path': str(path), 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}

def save(path, value):
    with path.open('x') as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2, allow_nan=False)
        handle.write('\n')

def main():
    outputs = ['navigation-proposal.json', 'source-ground-review.json', 'source-probe-comparison.json']
    assert not any((HERE / name).exists() for name in outputs), 'Keep actual prior evidence unchanged'
    frozen = BASE / 'source-owner-input-v1' / ID / 'geometry-input.json'
    neighborhood_path = BASE / 'source-neighborhood-v1.json'
    g, neighborhood = read(frozen), read(neighborhood_path)
    assert desc(neighborhood_path)['sha256'] == NEIGHBORHOOD_SHA
    assert neighborhood['source_geometry'] == desc(frozen)
    assert len(neighborhood['features']) == 44 and neighborhood['anchor'] == g['anchor']
    runtime = [MAIN / p for p in ('src/map-scene.js', 'src/street-interaction.js', 'src/walk-controller.js')]
    context = HERE / 'osm-navigation-context.osm'
    receipt = read(HERE / 'fetch.json')
    notes = HERE / 'visual-ground-notes.json'
    watched = [frozen, neighborhood_path, context, notes, *runtime]
    before = [desc(p) for p in watched]
    assert receipt['status'] == 200 and receipt['truncated'] is False
    assert receipt['bytes'] <= 500000 and desc(context)['sha256'] == receipt['sha256']
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
        if not geometry.is_valid:
            invalid.append(w.attrib['id']); continue
        ways.append({'id': w.attrib['id'], 'version': w.attrib.get('version'), 'tags': tags, 'geometry': geometry})
    def water(tags):
        return tags.get('natural') == 'water' or 'waterway' in tags or 'water' in tags or tags.get('landuse') in ('reservoir','basin') or tags.get('leisure') == 'swimming_pool' or tags.get('amenity') == 'fountain'
    waters = [w for w in ways if water(w['tags'])]
    water_relations = []
    for rel in xml.findall('relation'):
        tags = {t.attrib['k']: t.attrib['v'] for t in rel.findall('tag')}
        if water(tags):
            water_relations.append({'id': rel.attrib['id'], 'tags': tags, 'requires_member_geometry_review': True})
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
    choices = []
    for name, start, bearing in [('southwest-outdoor-approach',[-18.,-20.],35.),('panyu-east-side-context-only',[-49.,-20.],0.)]:
        probes, controller, end = probes_for(start,bearing)
        checks = source_checks(probes)
        choices.append({'id':name,'spawn_local_enu_m':start,'walkStart':geographic(start),'bearing':bearing,'first_5m_endpoint_local_enu_m':end,'controller_default':controller,'source_checks':checks,'source_geometry_clear_only':all(r['frozen_source_owner_clearance_m']>0 and not r['live_osm_building_intersections'] and not r['effective_neighbor_intersections'] for r in checks.values()),'final_model_screened':False,'ground_surface_verified':False,'public_path_membership_verified':False})
    selected = choices[0]
    probes, controller, end = probes_for(selected['spawn_local_enu_m'],selected['bearing'])
    limitations = [
        'Working outdoor approach only. Actual detailed raw geometry, final camera poses and browser movement remain separate pending checks.',
        'The source-owner five-sided polygon is a mapped collision/replacement context, not a verified architectural wall boundary.',
        'At the selected southwest coordinate raw aerial imagery appears green/court-like; this is not a verified paved path, an OSM landuse classification, a surveyed ground elevation or proof of current access.',
        'The2018 north-entry photograph shows paving, a raised circular tree planter and a porch step, but is not georegistered and does not establish paving at this southwest coordinate.',
        'Panyu Road is tagged sidewalk=both, but that street centerline is about37m from the selected point. No separate sidewalk geometry or measured width at this point is available.',
        'A mapped footway lies west of Panyu Road, not at the selected outdoor approach. Road centerline distances are not curb, lane-edge or sidewalk-clearance measurements.',
        'Current OSM building/water polygons and frozen44-neighbor polygons were checked for finite probe nonintersection; no full furniture, tree, gate, overhead-wire or access-obstacle inventory is claimed.',
        'The14m default camera boom is an airborne probe; its projected clearance is not pedestrian ground support.',
        'Runtime collision comes from loaded map polygons and explicit proxies. Ordinary GLB windows, stairs, walls and doors do not automatically create collision or ground surfaces.',
        'Default ground0.075m is not measured courtyard/grass/sidewalk elevation. No indoor access, stair climbing or arbitrary route is accepted.',
        'No mapped water in this bounded response is not physical proof of water absence. Returned full road ways extend beyond the query bbox; only in-bbox probes are accepted.'
    ]
    proposal = {'schema':'hudec-v19-working-exterior-navigation-seed','building_id':ID,'status':'WORKING_SOURCE_GROUND_SCREEN_ONLY_NOT_FINAL','navigation':{'listed':True,'overviewZoom':18,'walkStart':selected['walkStart'],'bearing':selected['bearing']},'candidate_id':selected['id'],'spawn_local_enu_m':selected['spawn_local_enu_m'],'first_5m_endpoint_local_enu_m':end,'controller_default':controller,'final_model_accepted':False,'browser_passed':False,'precise_public_sidewalk_membership_verified':False,'current_clear_pedestrian_width_verified':False,'coordinate_contract':desc(frozen),'limitations':limitations}
    save(HERE/'navigation-proposal.json',proposal)
    start, forward = probes['avatar'][0], probes['forward_5m'][0]
    near_highways = sorted([{'osm_way':w['id'],'version':w['version'],'tags':w['tags'],'distance_to_start_centerline_m':w['geometry'].distance(start),'distance_to_first5m_centerline_m':w['geometry'].distance(forward),'distance_is_not_curb_or_lane_edge':True} for w in highways],key=lambda r:r['distance_to_start_centerline_m'])
    tagged_nodes = []
    for n in xml.findall('node'):
        tags = {t.attrib['k']:t.attrib['v'] for t in n.findall('tag')}
        if tags and Point(nodes[n.attrib['id']]).distance(start)<40:
            tagged_nodes.append({'osm_node':n.attrib['id'],'tags':tags,'local_east_north_m':nodes[n.attrib['id']],'distance_to_start_m':Point(nodes[n.attrib['id']]).distance(start)})
    bounds = xml.find('bounds').attrib
    bbox = Polygon([project(float(bounds['minlon']),float(bounds['minlat'])),project(float(bounds['maxlon']),float(bounds['minlat'])),project(float(bounds['maxlon']),float(bounds['maxlat'])),project(float(bounds['minlon']),float(bounds['maxlat']))])
    in_bounds = all(bbox.covers(p.buffer(radius)) for p,radius in probes.values())
    water_checks = [{'osm_way':w['id'],'version':w['version'],'tags':w['tags'],'geometry_type':w['geometry'].geom_type,'probe_clearance_m':{name:w['geometry'].distance(p)-radius for name,(p,radius) in probes.items()}} for w in waters]
    checks = selected['source_checks']
    source_pass = not(incomplete or invalid or water_relations) and in_bounds and selected['source_geometry_clear_only'] and all(min(r['probe_clearance_m'].values())>0 for r in water_checks)
    assert before == [desc(p) for p in watched], 'Source/runtime beforeimages changed'
    report = {'schema':'hudec-v19-bounded-source-ground-review','created_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'passed_source_screen_only':source_pass,'scope_of_pass':'Only complete bounded mapped source-building/water and44 frozen-neighbor finite-probe nonintersection. No measured paving, public-sidewalk/access, final mesh or browser acceptance.','final_model_accepted':False,'browser_passed':False,'main_written':False,'precise_public_sidewalk_membership_verified':False,'current_clear_pedestrian_width_verified':False,'candidate_binding':desc(HERE/'navigation-proposal.json'),'candidate_id':selected['id'],'candidate_navigation':{k:proposal['navigation'][k] for k in ('walkStart','bearing')},'coordinate_contract':desc(frozen),'effective_neighborhood':desc(neighborhood_path),'effective_neighbors_checked':len(neighbors),'osm_input':desc(context),'fetch':receipt,'osm_counts':{k:len(xml.findall(k)) for k in ('node','way','relation')},'query_bbox':bounds,'all_probe_buffers_inside_requested_bbox':in_bounds,'incomplete_way_node_refs':incomplete,'invalid_way_geometries':invalid,'mapped_water_or_fountain_ways':water_checks,'water_relations_pending':water_relations,'live_osm_building_checks':{name:{'nearest':r['live_osm_building_nearest'],'intersections':r['live_osm_building_intersections']} for name,r in checks.items()},'frozen_source_and_effective_neighbor_checks':checks,'nearest_highways':near_highways,'nearest_explicit_footway':next((r for r in near_highways if r['tags'].get('highway')=='footway'),None),'tagged_nodes_within40m':tagged_nodes,'source_land_at_start':[{'osm_way':w['id'],'tags':w['tags']} for w in ways if w['geometry'].geom_type=='Polygon' and any(k in w['tags'] for k in ('landuse','surface','leisure','area:highway')) and w['geometry'].covers(start)],'visual_ground_review':desc(notes),'runtime_source_inputs':[desc(p) for p in runtime],'runtime_scope_review':desc(BASE/'runtime-collision-scope-v1.json'),'tool':desc(__file__),'input_preservation':{'all_watched_exact':True,'files':before},'limitations':limitations}
    save(HERE/'source-ground-review.json',report)
    save(HERE/'source-probe-comparison.json',{'schema':'hudec-v19-source-only-working-spawn-options','accepted':False,'candidate_binding':desc(HERE/'navigation-proposal.json'),'tool':desc(__file__),'choices':choices,'selected_id':selected['id'],'selection_scope':'Parent chose southwest working approach; source nonintersection alone does not prove a public or paved route.'})
    print(json.dumps({'source_screen_only':source_pass,'navigation':proposal['navigation'],'all_probes_in_bbox':in_bounds,'counts':report['osm_counts'],'effective_neighbors':len(neighbors),'mapped_water':len(waters),'water_relations_pending':len(water_relations),'source_owner_min_clearance_m':min(r['frozen_source_owner_clearance_m'] for r in checks.values()),'report':desc(HERE/'source-ground-review.json')},ensure_ascii=False))

if __name__ == '__main__':
    main()
