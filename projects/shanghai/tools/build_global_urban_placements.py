"""Build explicitly approximate city placements from frozen named map evidence.

Run from the repository root after inventory_global_models.py. This does not
change the authored assets, infer new source ownership, or claim survey accuracy.
"""
import hashlib
import gzip
import json
import math
import subprocess
from pathlib import Path

from shapely import affinity
from shapely.geometry import Point, Polygon, box, mapping, shape
from shapely.ops import transform, unary_union

ROOT = Path(__file__).resolve().parents[3]
PROJECT = ROOT / 'projects/shanghai'
BASELINE = '65af6bea52780f274d2ee005bbbd513317b559fc'
R = 6378137.0

def frozen(path):
    return subprocess.check_output(['git', 'show', BASELINE + ':' + path], cwd=ROOT)

def digest(raw):
    return {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}

def local_transforms(origin):
    lon, lat = origin
    mx = math.pi / 180 * R * math.cos(math.radians(lat))
    my = math.pi / 180 * R
    def en(x, y, z=None): return ((x - lon) * mx, (y - lat) * my)
    def ll(x, y, z=None): return (lon + x / mx, lat + y / my)
    return en, ll

def place_polygon(poly, origin, heading):
    return transform(local_transforms(origin)[1], affinity.rotate(poly, -heading, origin=(0, 0)))

source_path = 'projects/shanghai/data/audit/landmark-candidate-features.geojson'
raw = frozen(source_path)
features = json.loads(raw)['features']
by_id = {f['properties']['id']: f for f in features}
inventory_path = PROJECT / 'data/audit/global-model-integration-v1/inventory.json'
inventory = {r['id']: r for r in json.loads(inventory_path.read_text())['records']}

# Heading is clockwise in geographic ENU; glTF runtime rotation.y = -heading.
# Frontage side and tower location disambiguate the 180-degree MRR alternatives.
specs = [
    ('hongkou-broadway-mansions', '582fd5f8-2a90-3eba-9fce-81b358492d0b', 0.0, 'centre', '模型底层直接采用该显式关联凹形部件的局部ENU轮廓，因此不追加旋转；各层退台和历史墙线仍含估计。'),
    ('hongkou-russian-consulate', '49f3a80d-d5c3-421a-904a-e17974063f73', 4.917, 'centre', '长边与冻结主楼轮廓对齐，作者前立面朝苏州河侧；尺寸、背面及塔部为估计，园内亭子未并入。'),
    ('huangpu-park-hotel', '64ff37d4-ed69-464b-af4c-3ba55de36d38', -40.70, 'front', '短边前立面对南京西路，沿南侧街墙落位；模型后部较冻结轮廓短，后侧余体保留。'),
    ('huangpu-shanghai-race-club-east-building', '9402a15a-c2dc-478e-87b5-3236bc4c0b8b', 79.11, 'centre', '长轴对齐冻结东楼轮廓，主塔置于西北端，柱廊朝西侧院落；西楼及庭院连接体不并入，主体尺度仍为估计。'),
    ('huangpu-grand-theatre', 'b6b8b7dd-5999-4d4d-b1d1-29e282f7a73d', 216.91, 'grand-front', '入口和灯塔仅沿东北侧南京西路街边局部落位；未建影厅、商铺带及底图余体保留，位置和尺寸为估计。'),
    ('huangpu-pacific-hotel', 'ac43e95f-78ed-4252-b0d5-4f6c48669226', -35.02, 'front', '主楼前立面朝南京西路，沿冻结临街边对齐；保留估计模型未覆盖的后侧底图，北楼不并入。'),
    ('huangpu-sincere-company', '6312d66f-e7fa-43b1-a1cc-63f920d1f53d', -15.11, 'front', '南立面临南京东路、摩星塔在东南角；长轴按冻结同名单体近似对齐，尺度及后部边界未实测。'),
    ('huangpu-old-wing-on-company', '5d94b317-649b-4e66-8805-639274d488c7', -14.43, 'north-front', '北立面临南京东路，东北弧角及北面中西段塔分别保留；新永安与跨街桥不并入，平面及塔高为估计。'),
]
records = []
review = []
selected = {}
tables = {}

for model_id, source_id, heading, mode, note in specs:
    feature = by_id[source_id]
    source_poly = shape(feature['geometry'])
    origin = [source_poly.centroid.x, source_poly.centroid.y]
    en, ll = local_transforms(origin)
    local_source = transform(en, source_poly)
    aligned = affinity.rotate(local_source, heading, origin=(0, 0))
    bounds = inventory[model_id]['geometry']['bounds_enu_m']
    lo, hi = bounds['min'], bounds['max']
    local_model = box(lo[0], lo[1], hi[0], hi[1])
    dx = dy = 0.0
    if mode == 'centre' and model_id != 'hongkou-broadway-mansions':
        c = aligned.minimum_rotated_rectangle.centroid
        dx, dy = c.x, c.y
    elif mode == 'front':
        c = aligned.minimum_rotated_rectangle.centroid
        dx = c.x
        # Main wall locations, not projecting cornices/canopies, align to street.
        front_wall = {'huangpu-park-hotel': -22, 'huangpu-pacific-hotel': -18,
                      'huangpu-sincere-company': -34}[model_id]
        dy = aligned.bounds[1] - front_wall
    elif mode == 'north-front':
        c = aligned.minimum_rotated_rectangle.centroid
        dx, dy = c.x, aligned.bounds[3] - 47
    elif mode == 'grand-front':
        # Exact selected northeast source edge. No centroid placement in auditorium.
        coords = list(local_source.exterior.coords)
        a, b = coords[-2], coords[0]
        midpoint = Point((a[0]+b[0])/2, (a[1]+b[1])/2)
        am = affinity.rotate(midpoint, heading, origin=(0, 0))
        dx, dy = am.x - (lo[0] + hi[0])/2, am.y - 0.6
    offset = affinity.rotate(Point(dx, dy), -heading, origin=(0, 0))
    origin = list(ll(offset.x, offset.y))
    if model_id == 'hongkou-russian-consulate':
        # Its authored 44 m width exceeds the map envelope slightly. A one-metre
        # westward alignment avoids the separate eastern source without scaling
        # or deleting that neighbour; this is within the stated design estimate.
        origin = list(ll(offset.x - 1.0, offset.y))
        note += ' 在估计尺度内向西微调1米，以避开东侧独立源2877；该邻楼未遮蔽。'
    footprint = place_polygon(local_model, origin, heading)
    collision = place_polygon(local_model.buffer(0.18, join_style=2), origin, heading)
    ids = {'building': [], 'building_part': []}
    owner_ids = [source_id]
    if model_id == 'hongkou-broadway-mansions':
        owner_ids = ['8dff7d94-53d9-406e-b208-dd8562bbdafe',
                     '59962d89-0a7a-3c8b-823f-8f12a3d2c3fa', source_id]
    owner_polys = []
    for owner_id in owner_ids:
        f = by_id[owner_id]
        selected[owner_id] = f
        ids[f['properties']['source_layer']].append(owner_id)
        owner_polys.append(shape(f['geometry']))
    owned = unary_union(owner_polys)
    tx = int((origin[0]+180)/360*16384)
    ty = int((1-math.asinh(math.tan(math.radians(origin[1])))/math.pi)/2*16384)
    macro = f'14-{tx}-{ty}'
    if macro not in tables:
        table_path = f'projects/shanghai/assets/city-detail/macros/{macro}/feature-table.json.gz'
        table_raw = frozen(table_path)
        tables[macro] = {'path':table_path, **digest(table_raw),
                         'features':json.loads(gzip.decompress(table_raw))['features']}
    owners = [{'macro_id':macro, 'feature_local_id':f['localId'], 'key':f['key']}
              for f in tables[macro]['features']
              if f['properties']['id'] in owner_ids]
    assert owners
    # 0.25 m placement tolerance covers the small Earth-radius convention
    # difference between this reproducible map projection and MapLibre runtime.
    # The mask remains intersected with explicitly identified source polygons.
    clip_envelope = place_polygon(local_model.buffer(.25, join_style=2), origin, heading)
    clip = clip_envelope.intersection(owned)
    assert clip.is_valid and not clip.is_empty and clip.difference(owned).area < 1e-17
    walk_y = hi[1]+9 if mode == 'north-front' else lo[1]-12
    if model_id == 'huangpu-shanghai-race-club-east-building': walk_y = lo[1]-8
    walk_x = 0.0
    wp = place_polygon(Point(walk_x, walk_y), origin, heading)
    bearing = (heading + (180 if mode == 'north-front' else 0)) % 360
    record = {
        'id': model_id, 'districtId': inventory[model_id]['districtId'],
        'lng': origin[0], 'lat': origin[1], 'heading': heading, 'scale': 1,
        'height_m': hi[2], 'model_bounds_enu_m': bounds,
        'footprint': mapping(footprint), 'collision_geometry': mapping(collision),
        'replacement_geometry': mapping(clip), 'source_feature_ids': ids,
        'owner': owners[0], 'owners': owners,
        'replacementPolicy': 'clip-only-identified-source-intersection-while-model-visible',
        'navigation': {'listed': False, 'walkStart': [wp.x, wp.y], 'bearing': bearing, 'overviewZoom': 18.2,
                       'walk_status': 'suggested-pose-only-not-reviewed-for-city-walking'},
        'placement': {'status': 'estimated', 'method': 'approximate-map-aligned', 'note': note,
                      'surveyed': False, 'source_identity': 'frozen-name-or-explicit-parent-part',
                      'source_path': source_path, 'source_ids': owner_ids,
                      'heading_convention': 'clockwise in ENU; runtime GLTF Y rotation is negative heading',
                      'clip_envelope_tolerance_m': .25},
        'registration_note': note,
    }
    records.append(record)
    metric = local_transforms(origin)[0]
    review.append({'id': model_id, 'anchor': origin, 'heading': heading,
        'source_polygon_area_m2': transform(metric, owned).area,
        'replacement_area_m2': transform(metric, clip).area,
        'preserved_source_area_m2': transform(metric, owned.difference(clip)).area,
        'model_footprint_area_m2': local_model.area,
        'walk_outside_model': not collision.covers(wp),
        'clip_within_identified_sources': clip.difference(owned).area < 1e-17,
        'clip_within_model_envelope_plus_0_25m': clip.difference(clip_envelope).area < 1e-17,
        'unscaled_asset': True, 'historical_survey_claimed': False})

# The previous source review explicitly could not identify these two owners.
# Retain that finding: no source polygon is removed for either site approximation.
for model_id, origin, heading, note, walk in [
    ('xuhui-soong-ching-ling-residence', [121.43432,31.20602], 0,
     '淮海中路1843号已核院落内的主楼位置示意；北部院内落位及尺度为估计，南阳台朝向依据方志。主楼源身份尚未确认，游客中心和其余底图全部保留。',
     [121.43432,31.205915]),
    ('hongkou-luxun-residence-facade', [121.4799293,31.2682312], 0,
     '山阴路132弄9号鲁迅故居POI附近的正立面与院门位置示意；POI不是单栋轮廓，朝向仍为估计。旧维基坐标落34—36号已排除，所有底图楼体保留。',
     [121.4799293,31.26819]),
]:
    bounds = inventory[model_id]['geometry']['bounds_enu_m']
    lo, hi = bounds['min'], bounds['max']
    local_model = box(lo[0], lo[1], hi[0], hi[1])
    footprint = place_polygon(local_model, origin, heading)
    collision = place_polygon(local_model.buffer(.18, join_style=2), origin, heading)
    record = {'id': model_id, 'districtId': inventory[model_id]['districtId'],
        'lng': origin[0], 'lat': origin[1], 'heading': heading, 'scale': 1, 'height_m': hi[2],
        'model_bounds_enu_m': bounds, 'footprint': mapping(footprint),
        'collision_geometry': mapping(collision), 'replacement_geometry': None,
        'source_feature_ids': {'building': [], 'building_part': []},
        'replacementPolicy': 'preserve-all-baseline-source-owner-unconfirmed',
        'navigation': {'listed': False, 'walkStart': walk, 'bearing': 0, 'overviewZoom': 19.5,
                       'walk_status': 'suggested-pose-only-not-reviewed-for-city-walking'},
        'placement': {'status': 'estimated', 'method': 'approximate-site-display', 'note': note, 'surveyed': False,
                      'source_identity': 'unconfirmed-no-source-removal',
                      'source_path': 'source/precise/'+model_id+'/map-context.json'},
        'registration_note': note}
    records.append(record)
    review.append({'id':model_id,'anchor':origin,'heading':heading,'replacement_area_m2':0,
        'walk_outside_model':not collision.covers(Point(walk)), 'source_owner_unconfirmed':True,
        'all_baseline_preserved':True,'historical_survey_claimed':False})

out_dir = PROJECT/'data/global-models'
out_dir.mkdir(parents=True, exist_ok=True)
out = {'schema': 'urban-candidate-city-placement-v1', 'source_baseline_commit': BASELINE,
       'coordinate_system': 'WGS84; authored ENU metres; heading clockwise about up; scale stays 1',
       'scope': '10 non-Chongming existing assets, approximate global placement; no new model/survey acceptance',
       'records': records}
(out_dir/'urban-placement.json').write_text(json.dumps(out, ensure_ascii=False, indent=2)+'\n')
(out_dir/'urban-source-features.geojson').write_text(json.dumps({
    'type':'FeatureCollection','attribution':'© OpenStreetMap contributors; ODbL-1.0',
    'source_commit':BASELINE,'features':list(selected.values())},ensure_ascii=False,indent=2)+'\n')
audit = {'schema':'urban-placement-review-v1','source':{'path':source_path,'commit':BASELINE,**digest(raw)},
    'inventory':{'path':str(inventory_path.relative_to(ROOT)),**digest(inventory_path.read_bytes())},
    'method':'Frozen named feature or explicit parent/part identity; authored model bounds; documented frontage and approximate alignment. Replacement is strictly model envelope with 0.25 m projection tolerance intersect identified source footprint. No source geometry removed for unconfirmed house identities.',
    'placement_hash':digest((out_dir/'urban-placement.json').read_bytes()),
    'frozen_owner_tables':[{k:v for k,v in t.items() if k != 'features'} for t in tables.values()],
    'checks':review,'limitations':['Metric model dimensions and hidden geometry remain estimates.',
        'Map-derived polygons are not surveyed historical wall lines.',
        'No all-city obstacle or browser acceptance is claimed by this arithmetic review.']}
(PROJECT/'data/audit/global-model-integration-v1/urban-placement-review.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n')
assert len(records)==10 and all(x['walk_outside_model'] for x in review)
print(json.dumps({'records':len(records),'clip_count':sum(r['replacement_geometry'] is not None for r in records),'review':review},ensure_ascii=False))
