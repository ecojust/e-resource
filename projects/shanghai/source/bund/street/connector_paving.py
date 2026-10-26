"""Bounded ESTIMATED flat connector at Bund18; never a mapped/surveyed area.

The construction envelope follows existing rendered road/shoulder geometry and
the mapped pedestrian outer edge between two mapped crossings. Existing source
holes and two unclassified exterior recesses remain open. No furniture is added.
"""
import hashlib
import json
import math
from pathlib import Path

from shapely.geometry import Point, Polygon, LineString, mapping
from shapely.geometry.polygon import orient
from shapely.ops import substring, unary_union

UNKNOWN_RECESSES = {
    'south-unknown-opening': [
        [121.4857584,31.24009], [121.4858181,31.2400967],
        [121.4857843,31.2403154], [121.4857305,31.2403094]],
    'north-unknown-opening': [
        [121.4857184,31.2403961], [121.4857731,31.2403938],
        [121.485765,31.2405612], [121.4857007,31.2405612]],
}
CHECKPOINTS = [[121.48570,31.24045], [121.48575,31.24045], [121.48575,31.24055]]


def polygons(geometry):
    if geometry.is_empty:
        return []
    if geometry.geom_type == 'Polygon':
        return [geometry]
    return [p for child in getattr(geometry, 'geoms', []) for p in polygons(child)]


def shortest_outer_chain(geometry, endpoints):
    polygon = min(polygons(geometry), key=lambda p: sum(p.exterior.distance(point) for point in endpoints))
    ring = LineString(polygon.exterior.coords)
    start, end = [ring.project(point) for point in endpoints]
    direct = substring(ring, start, end)
    low, high = sorted([start, end])
    other = LineString(list(substring(ring, high, ring.length).coords)
                       + list(substring(ring, 0, low).coords)[1:])
    chain = min([direct, other], key=lambda line: line.length)
    if Point(chain.coords[-1]).distance(endpoints[0]) < Point(chain.coords[0]).distance(endpoints[0]):
        chain = LineString(list(chain.coords)[::-1])
    return chain


def clean_ring(ring):
    # Boolean boundaries occasionally repeat identical endpoints. Avoid a zero
    # length wall edge; do not simplify nonzero geometry.
    output = []
    for point in list(ring.coords)[:-1]:
        if not output or math.dist(point, output[-1]) > 1e-9:
            output.append(point)
    if len(output) > 1 and math.dist(output[0], output[-1]) <= 1e-9:
        output.pop()
    return output


def assemble_connector(root, metric, geographic, pedestrian, existing_paving,
                       road_surface, shoulder, curb, water, buildings):
    root = Path(root)
    source_path = root/'bund18-connector-source.json'
    source = json.loads(source_path.read_text())
    elements = source['elements']
    ways = {item['id']: item for item in elements if item['type'] == 'way'}
    crossing_ids = [745201529, 226657312]  # south, north
    crossings = [metric(LineString([(p['lon'], p['lat']) for p in ways[ident]['geometry']])) for ident in crossing_ids]
    endpoints = [Point(max(line.coords, key=lambda point: point[0])) for line in crossings]
    road_footprint = unary_union([road_surface, shoulder, curb])
    road_edge = shortest_outer_chain(road_footprint, endpoints)
    pedestrian_edge = shortest_outer_chain(pedestrian, endpoints)
    envelope = Polygon(list(road_edge.coords) + list(pedestrian_edge.coords)[::-1])
    if not envelope.is_valid or envelope.is_empty:
        raise ValueError('Mapped boundary chains do not form a valid bounded connector envelope.')
    relation = next(item for item in elements if item['type']=='relation' and item['id']==2142077)
    fresh_holes = []
    for member in relation['members']:
        if member.get('role') == 'inner' and member.get('geometry'):
            fresh_holes.append(metric(Polygon([(p['lon'],p['lat']) for p in member['geometry']])))
    mapped_holes = [Polygon(ring) for p in polygons(pedestrian) for ring in p.interiors]
    holes = unary_union(fresh_holes + mapped_holes)
    recesses = {name: metric(Polygon(points)) for name, points in UNKNOWN_RECESSES.items()}
    opening_clearances = []
    opening_records = []
    for item in elements:
        tags = item.get('tags', {})
        protected = tags.get('highway')=='steps' or 'entrance' in tags or tags.get('railway')=='subway_entrance'
        if not protected:
            continue
        if item['type']=='node' and 'lon' in item:
            # A point supplies no opening footprint. A conservative excluded
            # 2m radius is a declared clearance estimate, never new fill.
            geometry = metric(Point(item['lon'],item['lat'])).buffer(2)
            basis = 'estimated 2m exclusion radius around mapped entrance point'
        elif item['type']=='way' and item.get('geometry'):
            geometry = metric(LineString([(p['lon'],p['lat']) for p in item['geometry']])).buffer(2,cap_style=2)
            basis = 'estimated 4m exclusion corridor around mapped steps/entrance way'
        else:
            continue
        opening_clearances.append(geometry)
        opening_records.append({'type':item['type'],'id':item['id'],'tags':tags,'basis':basis,'intersects_envelope':geometry.intersects(envelope)})
    protected_openings = unary_union(opening_clearances)
    exclusions = {'existing_paving':existing_paving,'road_surface':road_surface,'road_shoulder':shoulder,
                  'curbs':curb,'water':water,'candidate_buildings':buildings,
                  'pedestrian_holes':holes,'mapped_entrances_steps':protected_openings,
                  **recesses}
    connector = envelope
    for geometry in exclusions.values():
        connector = connector.difference(geometry)
    # Quantized MVT vs exact OSM recess edges can leave isolated narrow pieces
    # beside the promenade. This task covers the road-connected strip only.
    parts = polygons(connector)
    connected = [p for p in parts if p.distance(road_edge) <= 1e-7]
    detached = unary_union([p for p in parts if p.distance(road_edge) > 1e-7])
    connector = unary_union([orient(Polygon(clean_ring(p.exterior),[clean_ring(r) for r in p.interiors]),sign=1) for p in connected])
    if connector.is_empty or not connector.is_valid:
        raise ValueError('Estimated connector must retain a valid road-connected polygon.')
    # Sample both envelope sides at <=0.2m intervals and all corners. This is a
    # width check between the source-derived chains, not a buffer operation.
    samples = [pedestrian_edge.interpolate(pedestrian_edge.length*i/max(1,math.ceil(pedestrian_edge.length/.2)))
               for i in range(max(1,math.ceil(pedestrian_edge.length/.2))+1)]
    samples += [Point(p) for p in pedestrian_edge.coords]
    maximum_width = max(point.distance(road_edge) for point in samples)
    if maximum_width > 12:
        raise ValueError(f'Connector envelope exceeds the 12m bounded-scope check: {maximum_width:.3f}m')
    # Buffer is used only for a negative width assertion, never to create fill.
    width_cap_excess = envelope.difference(road_edge.buffer(12)).area
    if width_cap_excess > 1e-6:
        raise ValueError('Some envelope geometry lies farther than 12m from the road edge.')
    new_width_samples = []
    for part in polygons(connector):
        for ring in [part.exterior,*part.interiors]:
            line = LineString(ring.coords)
            count = max(1,math.ceil(line.length/.2))
            new_width_samples.extend(line.interpolate(line.length*i/count) for i in range(count+1))
            new_width_samples.extend(Point(p) for p in line.coords)
    maximum_new_width = max(p.distance(road_edge) for p in new_width_samples)
    overlap = {name:connector.intersection(geometry).area for name,geometry in exclusions.items()}
    outside_area = connector.difference(envelope).area
    if max([outside_area,*overlap.values()]) > 1e-6:
        raise ValueError('Connector overlaps an excluded source surface or leaves its envelope.')
    audit = {
        'version':'bund18-estimated-connector-v1','passed':True,
        'classification':'estimated connector paving; not a mapped or measured pedestrian footprint',
        'source_relation':2142077,'source_exterior_way':160033684,'existing_mvt_pedestrian_feature_id':21420773,
        'source_extract_file':source_path.name,'source_extract_element_count':len(source['elements']),
        'source_extract_sha256':hashlib.sha256(source_path.read_bytes()).hexdigest(),
        'parent_source_extract':source['parent_extract'],
        'full_overpass_response_sha256':source['full_response_sha256'],'source_query':source['source'],
        'crossings_south_north':crossing_ids,
        'mapped_river_side_crossing_endpoints_wgs84':[list(geographic(point).coords)[0] for point in endpoints],
        'road_projected_endpoints_wgs84':[list(geographic(Point(p)).coords)[0] for p in (road_edge.coords[0],road_edge.coords[-1])],
        'pedestrian_projected_endpoints_wgs84':[list(geographic(Point(p)).coords)[0] for p in (pedestrian_edge.coords[0],pedestrian_edge.coords[-1])],
        'road_edge_length_m':road_edge.length,'pedestrian_edge_length_m':pedestrian_edge.length,
        'bounded_envelope_area_m2':envelope.area,'new_connector_area_m2':connector.area,
        'maximum_envelope_width_m':maximum_width,'maximum_width_check_m':12,'width_sample_spacing_m':.2,
        'maximum_new_paving_distance_to_road_edge_m':maximum_new_width,'exact_12m_width_cap_excess_m2':width_cap_excess,
        'detached_precision_fragments_excluded_m2':detached.area,'new_polygon_count':len(polygons(connector)),
        'base_height_m':.005,'top_height_m':.035,'construction_height_basis':'existing flat game walk datum; no real step elevations asserted',
        'overlap_m2':overlap,'outside_bounded_envelope_m2':outside_area,
        'unknown_openings':[{'id':name,'area_m2':geometry.area,'new_paving_overlap_m2':overlap[name],
            'reason':'Source exterior recess retained as an unknown opening. Reference photograph shows steps/openings without a matched footprint; this recess is not asserted to be a staircase.'}
            for name,geometry in recesses.items()],
        'mapped_entrance_step_exclusions':opening_records,
        'checkpoints':[{'lng':lon,'lat':lat,'new_paving':connector.covers(metric(Point(lon,lat))),
            'preserved_unknown_openings':[name for name,g in recesses.items() if g.covers(metric(Point(lon,lat)))]}
            for lon,lat in CHECKPOINTS],
        'known_pedestrian_holes_preserved':True,'existing_mesh_geometry_changed':False,'added_furniture':0,'added_trees':0,
        'limitations':['Connector plan is an estimate between source-derived edges, not a newly discovered mapped area.',
                      'Two unidentified exterior recesses and all mapped holes remain open; two original white-gap checkpoints are intentionally not filled.',
                      'The unchanged level ground datum does not reconstruct the actual raised promenade, steps, ramps or accessible route.'],
    }
    features = [{'type':'Feature','properties':{'role':role},'geometry':mapping(geographic(geometry))}
                for role,geometry in [('road_outer_edge',road_edge),('pedestrian_outer_edge',pedestrian_edge),
                    ('estimated_connector_envelope',envelope),('estimated_new_connector_paving',connector),
                    ('source_pedestrian_holes',holes),('detached_fragments_not_added',detached),*recesses.items()]]
    return connector,audit,{'type':'FeatureCollection','features':features}
