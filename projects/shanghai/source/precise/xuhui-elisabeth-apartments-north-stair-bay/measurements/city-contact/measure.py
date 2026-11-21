"""Replay the city and model geometry comparison using SHA-256-verified mesh inputs."""
from pathlib import Path
from contextlib import ExitStack
from tempfile import TemporaryDirectory
from hashlib import sha256
import numpy as np, math, sys, subprocess, runpy, json, os, shutil, gzip, time
from shapely.geometry import Point, Polygon, LineString
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
a = p / 'data/audit/elisabeth-apartments-north-stair-bay-v1/preflight'
auth = json.loads((a / 'model-review.json').read_bytes())
id = auth['id']
source = p / 'source/precise' / id / 'measurements'
survey = json.loads((source / 'stair-crown-intersection.json').read_bytes())
ref = json.loads((q / 'inputs.json').read_bytes())

def jh(f):
    return sha256(f.read_bytes()).hexdigest()

def put(f, d):
    f.write_text(json.dumps(d, ensure_ascii=False, indent=2) + '\n')
events = []

def execute(cmd, env):
    begin = time.time()
    proc = subprocess.Popen(cmd, env=env)
    status = proc.wait()
    events.append({'pid': proc.pid, 'exit_code': status, 'started': begin, 'ended': time.time(), 'program': Path(cmd[1]).name})
    assert status == 0
scene_module = runpy.run_path(str(home / 'glb_triangles.py'))
load = scene_module['load_triangles']
ll = np.array(ref['anchor'])
rad = math.pi / 180
unit = np.array([6371008.8 * math.cos(ll[1] * rad) * rad, 6371008.8 * rad])
rows = json.load(gzip.open(q / 'feature-table.json.gz'))['features']
building = next((r for r in rows if r['localId'] == 1005))
ring = (np.array(building['geometry']['coordinates'][0]) - ll) * unit
seg = min(zip(ring, ring[1:]), key=lambda pair: LineString(pair).distance(Point(0, 0)))
edge = np.asarray(seg[1]) - seg[0]
edge = edge / np.linalg.norm(edge)
east = edge if edge[0] > 0 else -edge
axis = -east
norm = np.array([-east[1], east[0]])
assert norm[1] > 0
owner = Polygon(ring)
ground_ranges = [float((ring @ axis).min()), float((ring @ axis).max())]

def roundf(x):
    return round(float(x), 5)

def hit(t, o, d):
    d = np.array(d)
    o = np.array(o)
    v0 = t[:, 0]
    e1 = t[:, 1] - v0
    e2 = t[:, 2] - v0
    cross = np.cross(d, e2)
    det = (cross * e1).sum(axis=1)
    good = np.abs(det) > 1e-10
    inv = np.divide(1.0, det, out=np.zeros_like(det), where=good)
    delta = o - v0
    u = (delta * cross).sum(axis=1) * inv
    qq = np.cross(delta, e1)
    v = (qq * d).sum(axis=1) * inv
    dist = (qq * e2).sum(axis=1) * inv
    valid = good & (u >= -1e-06) & (v >= -1e-06) & (u + v <= 1.000001) & (dist >= 0) & (dist <= 16)
    return None if not valid.any() else roundf(8 - dist[valid].min())
with ExitStack() as stack:
    tmp = Path(stack.enter_context(TemporaryDirectory(dir=q)))
    out = {}

    def anon(name):
        return tmp / name
    for name in ['context-features.json', 'initial-local-frame.json', 'macro-READY.json', 'baseline-near.glb.gz', 'baseline-far.glb']:
        (tmp / name).symlink_to(q / name)
    for level in ['near', 'far']:
        for part in ['owners.u32', 'triangles.f64']:
            anon('baseline-' + level + '-' + part)
    env = {**os.environ, 'POSTAL_MAPPING_WORK': str(tmp), 'NODE_OPTIONS': '--require=' + str(home / 'decode-texture.cjs')}
    execute(['node', home / 'decode-city.mjs'], env)
    base = {}
    for level in ['near', 'far']:
        arr = np.fromfile(tmp / ('baseline-' + level + '-triangles.f64'), dtype=np.float64).reshape(-1, 3, 3)
        base[level] = arr
    files = q
    roles = {}
    inputs = {}
    for role, tag in [('raw', 'raw'), ('full', 'web'), ('lod', 'lod')]:
        f = files / (id + '-' + tag + '.glb')
        assert jh(f) == auth['assets'][role]['sha256']
        inputs[role] = dict(file=f.name, sha256=jh(f))
        if role == 'raw':
            raw = f
        else:
            raw = anon('scene-' + role + '.glb')
            execute(['node', home / 'decode-meshopt.mjs', f, raw, p / 'vendor/meshopt_decoder.module.js'], os.environ)
        t = load(raw)[0]
        assert len(t) == auth['assets'][role]['triangles']
        roles[role] = t
    all_tri = roles['raw'].reshape(-1, 3)
    maxz = all_tri[:, 2].max()
    crown = all_tri[(abs(all_tri[:, 0]) < 1.81) & (all_tri[:, 2] >= maxz - 0.045)]
    yfront = roundf(crown[:, 1].min())
    for level, model in [('near', 'full'), ('far', 'lod')]:
        old = base[level]
        new = roles[model]
        rows = []
        for x in [-6, -4.2, -3.6, -2.4, -1.08, -0.51, 0, 0.53, 1.08, 2.4, 3.6, 4.2, 6]:
            for z in [0.25, 1.35, 2.67, 3.15, 4.6, 7.25, 9.6, 12.3, 14.2, 15.45, 16.8, 17.65, 17.82]:
                site_xy = axis * x + norm * 8.0
                oldhit = hit(old, [*site_xy, z], [*-norm, 0])
                newhit = hit(new, [x, yfront - 8, z], [0, 1, 0])
                delta = None if newhit is None or oldhit is None else roundf(newhit - oldhit)
                rows.append({'along_m': x, 'z_m': z, 'existing_front': oldhit, 'model_front': newhit, 'new_minus_city': delta})
        both = [z for z in rows if z['new_minus_city'] is not None]
        d = np.array([z['new_minus_city'] for z in both])
        range_offset = survey['sensitivity']['northward_offset_m']
        nominal = survey['nominal']['northward_offset_from_osm_edge_m']
        minus = range_offset[0] - nominal
        plus = range_offset[1] - nominal
        out[level] = dict(source_triangles=len(old), delivered_triangles=len(new), rays=rows, matched=len(both), offset_range_m=[roundf(d.min()), roundf(d.max())], inside_existing_at_nominal=sum((v['new_minus_city'] < -0.025 for v in both)), outside_existing_at_nominal=sum((v['new_minus_city'] > 0.025 for v in both)), flips_across_photo_sensitivity=sum((v['new_minus_city'] + minus < 0 < v['new_minus_city'] + plus for v in both)), existing_beyond_detail=sum((v['existing_front'] is not None and abs(v['along_m']) > 4 for v in rows)), existing_visible_through_model_openings=sum((v['model_front'] is None and v['existing_front'] is not None and (abs(v['along_m']) < 4) for v in rows)))
    decode = json.loads((tmp / 'source-decode.json').read_bytes())
    max_width = np.ptp(all_tri[:, 0])
    max_dep = np.ptp(all_tri[:, 1])
    outv = dict(order=360, id=id, source=ref, model_files=inputs, author_sha256=jh(a / 'model-review.json'), survey_sha256=jh(source / 'stair-crown-intersection.json'), original_geometry=building['geometry'], original_area_m2=roundf(owner.area), original_height_m=building['height'], along_street_projection_m=list(map(roundf, ground_ranges)), north_edge_wgs84=[(ll + v / unit).tolist() for v in seg], source_model_width_m=roundf(max_width), source_model_depth_m=roundf(max_dep), source_model_top_m=roundf(maxz), crown_point_on_model=dict(front_y=yfront, highest_z=roundf(maxz), alignment='中心梯间最高45毫米范围内最前沿的顶点，对齐2015年照片冠顶两线交会。以北外墙对应的长边定向。'), photo_sensitivity=survey['sensitivity'], nominal_photo=survey['nominal'], stages=events, decode_summaries=[{k: t.get(k) for k in ['variant', 'sha256', 'expanded_triangles_total', 'preselected_triangles', 'selected_far_triangle_counts']} for t in decode], results=out)
    for item in outv['results'].values():
        item['retained_shell_above_the_two_shoulders'] = item.pop('existing_visible_through_model_openings')
    put(args.output, outv)
    for l, k in out.items():
        print(l, {n: v for n, v in k.items() if n != 'rays'}, flush=True)
