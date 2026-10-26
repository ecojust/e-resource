"""Photo-classified Bund17/18 planting beds on frozen OSM exterior recesses.

The source quadrilaterals are unchanged. Classification uses a 2010 CC0 aerial
photograph; the shallow stone border and soil/grass elevations are estimates on
the existing flat game datum, not a reconstruction of the floodwall elevation.
"""
import hashlib
import json
from pathlib import Path

from shapely.geometry import Polygon, mapping
from shapely.geometry.polygon import orient
from shapely.ops import unary_union

from connector_paving import UNKNOWN_RECESSES

PAVING_TOP_M = .035
CURB_TOP_M = .215  # estimated 0.18m above the current paving datum
CURB_WIDTH_M = .18
SOIL_TOP_M = .080
GRASS_TOP_M = .090


def assemble_planting_beds(root, metric, geographic, water, buildings, roads,
                          connector, existing_paving):
    root = Path(root)
    source_path = root/'planting-evidence.json'
    source = json.loads(source_path.read_text())
    plan_path = root/source['plan_source']['file']
    assert hashlib.sha256(plan_path.read_bytes()).hexdigest() == source['plan_source']['sha256']
    plan = json.loads(plan_path.read_text())
    relation = next(e for e in plan['elements']
                    if e['type'] == 'relation' and e['id'] == 2142077)
    outer = next(m['geometry'] for m in relation['members']
                 if m['ref'] == 160033684 and m['role'] == 'outer')
    photo_path = root/source['photograph']['file']
    assert hashlib.sha256(photo_path.read_bytes()).hexdigest() == source['photograph']['sha256']
    areas = {}
    records = []
    features = []
    for original_id, coordinates in UNKNOWN_RECESSES.items():
        bed_id = original_id.replace('unknown-opening', 'photo-classified-planting')
        expected = source['beds'][original_id]['coordinates_wgs84']
        assert coordinates == expected, 'Evidence and frozen recess coordinates disagree.'
        indices = source['plan_source']['south_vertices' if original_id.startswith('south') else 'north_vertices']
        frozen = [[outer[i]['lon'],outer[i]['lat']] for i in indices]
        assert coordinates == frozen, 'Planting outline must use exact frozen source vertices.'
        footprint = metric(Polygon(coordinates))
        assert footprint.is_valid and footprint.area > 1
        inside = orient(footprint.buffer(-CURB_WIDTH_M, join_style=2), sign=1)
        assert inside.is_valid and inside.geom_type == 'Polygon' and inside.area > 1
        border = orient(footprint.difference(inside), sign=1)
        assert abs(border.union(inside).symmetric_difference(footprint).area) < 1e-8
        excluded = {'water':water, 'candidate_buildings':buildings,
                    'road_surface':roads['surface'], 'road_curb':roads['curb'],
                    'connector_paving':connector}
        overlaps = {name:footprint.intersection(geometry).area
                    for name,geometry in excluded.items()}
        assert max(overlaps.values()) < 1e-6, (bed_id, overlaps)
        # MVT pedestrian vertices are quantized, while these four corners are
        # from exact OSM coordinates. Existing geometry is retained unchanged;
        # sub-decimetre boundary mismatch is reported, not silently re-cut.
        paving_overlap = footprint.intersection(existing_paving).area
        areas[bed_id] = {'footprint':footprint, 'border':border, 'inside':inside}
        record = {'id':bed_id, 'previous_id':original_id,
                  'coordinates_wgs84':coordinates,
                  'classification':'planting bed, inferred from located 2010 aerial photo',
                  'classification_is_osm_tag':False,
                  'footprint_area_m2':footprint.area, 'border_area_m2':border.area,
                  'soil_grass_area_m2':inside.area,
                  'overlap_m2':overlaps,
                  'retained_mvt_paving_overlap_m2':paving_overlap,
                  'height_reference':'unchanged flat game ground datum; not surveyed elevation',
                  'paving_top_m':PAVING_TOP_M,
                  'curb_bottom_m':.005, 'curb_top_m':CURB_TOP_M,
                  'curb_height_above_paving_m':CURB_TOP_M-PAVING_TOP_M,
                  'curb_width_m':CURB_WIDTH_M,
                  'soil_bottom_m':.005, 'soil_top_m':SOIL_TOP_M,
                  'grass_bottom_m':SOIL_TOP_M, 'grass_top_m':GRASS_TOP_M,
                  'construction_dimensions_estimated':True,
                  'added_trees':0}
        records.append(record)
        for role,geometry in [('source_recess_footprint',footprint),
                              ('estimated_stone_border',border),
                              ('estimated_soil_grass_interior',inside)]:
            features.append({'type':'Feature','properties':{'bed':bed_id,'role':role},
                             'geometry':mapping(geographic(geometry))})
    audit = {'version':'bund17-18-photo-classified-planting-v1', 'passed':True,
             'source_relation':2142077, 'source_outer_way':160033684,
             'source_coordinates_changed':False,
             'photo':source['photograph'],
             'evidence_file':source_path.name,
             'evidence_sha256':hashlib.sha256(source_path.read_bytes()).hexdigest(),
             'beds':records,
             'footprint_area_m2':sum(r['footprint_area_m2'] for r in records),
             'grass_area_m2':sum(r['soil_grass_area_m2'] for r in records),
             'existing_geometry_changed':False, 'added_trees':0,
             'platform_elevation_reconstructed':False,
             'limitations':source['limitations']}
    return areas,audit,{'type':'FeatureCollection','features':features}
