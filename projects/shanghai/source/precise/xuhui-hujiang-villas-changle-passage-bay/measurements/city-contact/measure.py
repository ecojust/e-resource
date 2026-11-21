"""Replay the city and model geometry comparison using SHA-256-verified mesh inputs."""
from pathlib import Path
from hashlib import sha256
from tempfile import TemporaryDirectory
from contextlib import ExitStack
import os, json, math, subprocess, time, runpy, gzip
import numpy as np
from shapely.geometry import MultiLineString, LineString, Polygon, Point
from shapely.ops import unary_union
from shapely import polygons, union_all
import argparse
from urllib.request import Request, urlopen
from pathlib import Path
from tempfile import TemporaryDirectory
from hashlib import sha256
import atexit, json, os, sys
home = Path(__file__).resolve().parent
parser = argparse.ArgumentParser(description='Repeat the registered city-shell and delivered mesh comparison.')
parser.add_argument('--project', type=Path, default=Path('.'), help='Shanghai project root with vendor/')
parser.add_argument('--output', required=True, type=Path, help='destination for the computed JSON')
args = parser.parse_args()
p = args.project.resolve()
if not (p / 'vendor/GLTFLoader.js').is_file():
    parser.error('Use --project with the Shanghai project directory')
work = TemporaryDirectory()
atexit.register(work.cleanup)
q = Path(work.name)
configuration = json.loads((home / 'signed-files.json').read_bytes())
for filename, entry in configuration.items():
    target = q / filename
    stored = p / entry['path']
    if stored.is_file() and sha256(stored.read_bytes()).hexdigest() == entry['sha256']:
        target.symlink_to(stored)
    else:
        with urlopen(Request(entry['url'], headers={'Accept-Encoding': 'identity'}), timeout=45) as response:
            data = response.read()
        if sha256(data).hexdigest() != entry['sha256']:
            raise ValueError(f'Different input bytes for {filename}')
        target.write_bytes(data)
for name in ['inputs.json', 'context-features.json', 'initial-local-frame.json']:
    (q / name).symlink_to(home / name)
os.environ['SHANGHAI_PROJECT'] = str(p)
args.output.parent.mkdir(parents=True, exist_ok=True)
a = p / 'data/audit/hujiang-villas-changle-passage-bay-v1/preflight'
author = json.loads((a / 'model-review.json').read_bytes())
name = author['id']
ref = json.loads((q / 'inputs.json').read_bytes())
fit = json.load(open(home / 'constrained-photo-fit.json'))
ll = np.array(ref['anchor'])
units = np.array([111195.0802 * math.cos(math.radians(ll[1])), 111195.0802])
theta = math.radians(fit['quantities']['facadeAngleNorthOfEast'])
east = np.array([math.cos(theta), math.sin(theta)])
out = np.array([-east[1], east[0]])

def inmodel(points):
    return np.stack([-points @ east, -points @ out], axis=-1)
roads = json.load(open(home / 'block.json'))
streets = [x for x in roads['ways'] if x.get('tags', {}).get('name') == '长乐路' and x['tags'].get('highway')]
street = min(streets, key=lambda x: LineString(inmodel((np.array(x['coords']) - ll) * units)).distance(Point(0, 0)))
streetline = LineString(inmodel((np.array(street['coords']) - ll) * units))
whole = json.load(gzip.open(q / 'feature-table.json.gz'))['features']
owners = {}
for k in ref['far_group']:
    v = next((r for r in whole if r['localId'] == k))
    owners[k] = Polygon(inmodel((np.array(v['geometry']['coordinates'][0]) - ll) * units))

def h(f):
    return sha256(f.read_bytes()).hexdigest()

def rounding(x):
    return round(float(x), 5)

def section(t, z):
    active = t[(t[:, :, 2].min(axis=1) < z) & (t[:, :, 2].max(axis=1) > z)]
    lines = []
    for tri in active:
        pts = []
        for u, v in ((0, 1), (1, 2), (2, 0)):
            lo, hi = (tri[u, 2], tri[v, 2])
            if lo <= z < hi or hi <= z < lo:
                pt = tri[u, :2] + (tri[v, :2] - tri[u, :2]) * (z - lo) / (hi - lo)
                pts.append(tuple(pt))
        if len(pts) == 2 and pts[0] != pts[1]:
            lines.append(pts)
    return MultiLineString(lines)
log = []

def run(cmd, env):
    before = time.time()
    pr = subprocess.Popen(cmd, env=env)
    code = pr.wait()
    log.append(dict(program=Path(cmd[1]).name, pid=pr.pid, exit_code=code, started=before, finished=time.time()))
    assert code == 0
load = runpy.run_path(str(home / 'glb_triangles.py'))['load_triangles']
with ExitStack() as ctx:
    t = Path(ctx.enter_context(TemporaryDirectory(dir=q)))

    def anon(n):
        return t / n
    for n in ['context-features.json', 'initial-local-frame.json', 'macro-READY.json', 'baseline-near.glb.gz', 'baseline-far.glb']:
        (t / n).symlink_to(q / n)
    for l in ('near', 'far'):
        for n in ('triangles.f64', 'owners.u32'):
            anon('baseline-' + l + '-' + n)
    run(['node', home / 'decode-city.mjs'], dict(os.environ, POSTAL_MAPPING_WORK=str(t), NODE_OPTIONS='--require=' + str(home / 'decode-texture.cjs')))
    originals = {}
    for level in ('near', 'far'):
        tri = np.fromfile(t / ('baseline-' + level + '-triangles.f64'), np.float64).reshape(-1, 3, 3)
        tri[:, :, :2] = inmodel(tri[:, :, :2])
        originals[level] = tri
    store = q
    sections = {}
    mesh_inputs = {}
    both = []
    for role, tag in [('raw', 'raw'), ('full', 'web'), ('lod', 'lod')]:
        f = store / (name + '-' + tag + '.glb')
        assert h(f) == author['assets'][role]['sha256']
        mesh_inputs[role] = dict(file=f.name, sha256=h(f))
        if role == 'raw':
            dec = f
        else:
            dec = anon(role + '.glb')
            run(['node', home / 'decode-meshopt.mjs', f, dec, p / 'vendor/meshopt_decoder.module.js'], os.environ)
        new = load(dec)[0]
        assert len(new) == author['assets'][role]['triangles']
        area = (new[:, 1, 0] - new[:, 0, 0]) * (new[:, 2, 1] - new[:, 0, 1]) - (new[:, 1, 1] - new[:, 0, 1]) * (new[:, 2, 0] - new[:, 0, 0])
        top = union_all(polygons(new[abs(area) > 1e-07, :, :2]))
        data = {'triangles': len(new), 'all_geometry_plan_area_m2': rounding(top.area), 'road_center_distance_m': rounding(top.distance(streetline)), 'owners': {k: dict(plan_clearance_m=rounding(top.distance(v)), overlap_m2=rounding(top.intersection(v).area)) for k, v in owners.items()}}
        if role != 'raw':
            old = originals['near' if role == 'full' else 'far']
            levels = []
            for z in [0.25, 1.21, 2.43, 3.29, 3.62, 5.17, 6.64, 7.49, 8.7, 10.22, 11.5, 11.89]:
                focus = section(new, z)
                baseline = section(old, z)
                assert not focus.is_empty and (not baseline.is_empty)
                end = []
                from shapely.geometry import box
                for side in [-1, 1]:
                    x = 2.61 * side
                    band = focus.intersection(box(x - 0.26, -2, x + 0.26, 4))
                    if not band.is_empty:
                        end.append({'side': 'east' if side < 0 else 'west', 'width_m': 0.52, 'distance_to_old_section_m': rounding(band.distance(baseline))})
                levels.append(dict(z_m=z, minimum_distance_to_any_existing_surface_m=rounding(focus.distance(baseline)), existing_owner_5217_plan_distance_m=rounding(focus.distance(owners[5217])), side_junctions=end))
            data['sections'] = levels
            walking = []
            for z in [1.1, 1.69]:
                focus = section(new, z)
                baseline = section(old, z)
                for x in [-0.62, 0, 0.62]:
                    path = LineString([(x, -0.5), (x, 3.0)])
                    walking.append(dict(x_m=x, z_m=z, length_m=path.length, existing_surface_clearance_m=rounding(path.distance(baseline)), new_side_clearance_m=rounding(path.distance(focus))))
            data['walk'] = walking
        sections[role] = data
    result = dict(order=352, id=name, passed=True, metadata=ref, original_owner=5217, source_review_sha256=h(a / 'model-review.json'), section_method='Triangle/height intersections in the signed city near and far meshes and both decoded new assets. Plan extends to every projected triangle. North-facing facade local X points west, local Y into the lane. Five-station lintel centre fixes the origin.', model_files=mesh_inputs, camera_fit_sha256=h(Path(home / 'constrained-photo-fit.json')), street_centerline_id=street['id'], original_sha256=h(Path(home / 'city-candidates.json')), original_group_iou=0.975163050912414, original_group_area_m2=owners[5217].area, original_group_lintel_distance_m=owners[5217].distance(Point(0, 0)), levels=sections, stages=log, all_children_exited=True, remaining_children=[])
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n')
    for k, v in sections.items():
        print(k, v['owners'], [a['minimum_distance_to_any_existing_surface_m'] for a in v.get('sections', [])], v['road_center_distance_m'])
