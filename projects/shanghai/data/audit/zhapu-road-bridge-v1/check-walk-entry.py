"""Check the documented walk start and road crown against the two map outlines and actual meshes."""
import hashlib
import json
import math
from pathlib import Path
import runpy
import subprocess
import tempfile

from shapely.geometry import LineString, Point, Polygon

audit = Path(__file__).resolve().parent
project = audit.parents[2]
model_id = 'huangpu-zhapu-road-bridge'
source = project / 'source/precise' / model_id
assets = project / 'assets/models/candidates' / model_id
read = lambda file: json.loads(file.read_bytes())
contract_path = audit / 'final-placement-contract.json'
contract = read(contract_path)
manifest = read(assets / 'manifest.json')
frozen = read(source / 'frozen-bridge-layer.json')
osm = read(source / 'placement-research.json')
lng, lat = contract['lng'], contract['lat']
heading = math.radians(contract['heading'])
radius = 6371008.8 * math.cos(math.radians(lat))
mercator_y = math.asinh(math.tan(math.radians(lat)))


def local(lonlat):
    east = math.radians(lonlat[0] - lng) * radius
    north = (math.asinh(math.tan(math.radians(lonlat[1]))) - mercator_y) * radius
    return east * math.cos(heading) - north * math.sin(heading), east * math.sin(heading) + north * math.cos(heading)


start = Point(local(contract['navigation']['walkStart']))
current_area = Polygon([local(q) for q in next(v['nodes'] for v in osm['ways'] if v['id'] == '815631995')])
frozen_area = Polygon([local(q) for q in next(v['geometry'] for v in frozen['features'] if v['id'] == 8156319952)])
assert current_area.contains(start) and frozen_area.contains(start)
footpaths = {v['id']: LineString([local(q) for q in v['nodes']]) for v in osm['ways']
             if v['id'] in ('1467932122', '1467932126')}
distances = {name: line.distance(start) for name, line in footpaths.items()}
assert distances['1467932126'] < 1 and distances['1467932122'] > 13

walk = contract['bridge_walk']
assert walk['longitudinal_axis'] == '-z' and walk['shear'] == 0
assert walk['half_road_m'] < -start.x < walk['half_deck_m']
assert 1.59 < start.y - walk['stations_m'][0][0] < 1.61
decoder = project / 'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
reader = project / 'data/audit/postal-office-v1/independent-glb-review-helpers.py'
scene_type = runpy.run_path(str(reader))['SerialScene']
hits = {}
samples = [('南端西人行道入口', start.x, start.y, 'paved walk'), ('中央西人行道', -7.55, 0, 'paved walk'),
           ('中央车道', 0, 0, 'asphalt'), ('北端东人行道', 7.55, 34.37, 'paved walk')]
with tempfile.TemporaryDirectory() as scratch:
    for role in ('raw', 'full', 'lod'):
        item = manifest['assets'][role]
        original = assets / item['file']
        assert hashlib.sha256(original.read_bytes()).hexdigest() == item['sha256']
        file = original
        if role != 'raw':
            file = Path(scratch) / (role + '.glb')
            subprocess.run(['node', decoder, original, file, project/'vendor/meshopt_decoder.module.js'], check=True)
        scene = scene_type(file)
        tests = []
        for name, x, y, expected in samples:
            hit = scene.ray([x, y, 11], [0, 0, -1], 12)
            assert hit and hit['material'] == expected
            actual = 11 - hit['distance_m']
            road = 3.74 + .47 * (1 - (y / 35.97) ** 2)
            expected_height = road + (walk['sidewalk_rise_m'] if expected == 'paved walk' else 0)
            assert abs(actual - expected_height) < .002
            tests.append(dict(feature=name, local_xy=[x,y], material=expected,
                              map_surface_altitude_m=actual + contract['altitude'],
                              deviation_from_crown_m=actual - expected_height))
        hits[role] = dict(asset_sha256=item['sha256'], samples=tests)
report = dict(id=model_id, passed=True, contract_sha256=hashlib.sha256(contract_path.read_bytes()).hexdigest(),
              inside_frozen_and_osm_decks=True, start_local_xy=[start.x,start.y],
              distance_to_osm_sidewalk_m=distances, original_feature_ids=walk['transportation_feature_ids'],
              navigation=contract['navigation'], variants=hits)
(audit/'walk-entry.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
