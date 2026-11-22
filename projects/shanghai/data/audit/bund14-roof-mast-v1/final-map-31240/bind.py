"""Bind both official Bund 14 sites, their four model files, the two unchanged adjacent buildings and the original photo section."""
from pathlib import Path
from urllib.request import urlopen, Request
from hashlib import sha256, file_digest
from math import cos, radians, sin, hypot, atan2, degrees
import os, sys, json
w = Path(__file__).resolve().parent
p = Path('/workspace/e-resource/projects/shanghai')
a = p / 'data/audit/bund14-roof-mast-v1'
source = p / 'source/precise/bund14/revisions/roof-mast'
sys.path.insert(0, '/tmp/shanghai-yongjia-porch')
from common import full, canon
h = lambda b: sha256(b).hexdigest()
read = lambda p: json.loads(p.read_bytes())
old = read(a / 'final-site-downloads.json')
assert old['passed'] and old['historic_landmark'] == 'bund14'
stages = {}
landmarks = {}
want = ['index.html', 'landmarks.html', 'data/landmarks.json', 'data/bund/manifest.json', 'data/bund/lod-v4.json', 'data/candidate-city-integrations.json', 'src/app.js', 'src/map-scene.js', 'src/building-beacons.js', 'src/walk-controller.js']
for n in (239, 240):
    port = 31000 + n
    origin = f'http://127.0.0.1:{port}/'
    prod = full(n)
    sc = Path('/tmp/shanghai-yongjia-porch/scenes')
    cmp = read(sc / f'{n}-comparison.json')
    assert cmp['passed'] and h(canon(prod)) == cmp['production_receipt_sha256']
    http = read(sc / f'{n}-all-http.json')
    assert http['passed'] and http['count'] == len(prod['files']) and (http['production_receipt_sha256'] == cmp['production_receipt_sha256'])
    assets = {}
    got = {}
    for name in want:
        with urlopen(origin + name, timeout=50) as r:
            assert r.status == 200
            body = r.read()
        digest = h(body)
        expected = prod['files'].get(name)
        assert digest == (expected or h((p / name).read_bytes())), name
        got[name] = dict(sha256=digest, bytes=len(body))
        if name == 'data/landmarks.json':
            landmarks[n] = json.loads(body)
        if name == 'data/candidate-city-integrations.json':
            assert json.loads(body)['resulting_city_count'] == 276
        if name == 'landmarks.html':
            assert b'index.html#landmark=bund14&amp;mode=walk' in body
    info = next((r for r in landmarks[n] if r['id'] == 'bund14'))
    for role, (name, sig) in {'raw': ('editable_model', 'raw_sha256'), 'full': ('model', 'web_sha256'), 'lod': ('lod_model', 'lod_sha256'), 'native': ('native_model', 'native_sha256')}.items():
        path = info[name]
        expected = info[sig]
        prior = old['sources'][str(port)][role]
        assert prior['sha256'] == expected and prior['url'] == origin + path
        with urlopen(origin + path, timeout=100) as r:
            assert r.status == 200
            digest = file_digest(r, 'sha256').hexdigest()
            size = int(r.headers['content-length'])
            assert size == prior['bytes'] and digest == expected
        with urlopen(Request(origin + path, headers={'Range': 'bytes=0-31'}), timeout=30) as r:
            assert r.status == 206 and r.headers['Content-Range'] == f'bytes 0-31/{size}'
            part = r.read()
            assert len(part) == 32
        assets[role] = dict(path=path, sha256=digest, bytes=size, prefix_sha256=h(part))
    stages[str(n)] = dict(port=port, origin=origin, sha256=cmp['production_receipt_sha256'], count=276, inputs=len(prod['files']), catalog=got['data/candidate-city-integrations.json'], row=info, files=got, assets=assets, all_http_sha256=h((sc / f'{n}-all-http.json').read_bytes()))
assert stages['239']['catalog'] == stages['240']['catalog']
before = stages['239']['row']
now = stages['240']['row']
assert [r for r in landmarks[239] if r['id'] != 'bund14'] == [r for r in landmarks[240] if r['id'] != 'bund14']
assert len(landmarks[239]) == len(landmarks[240]) == 40
for key in ('lng', 'lat', 'walkStart', 'bearing', 'candidate_id', 'bund_number', 'districtId'):
    assert before[key] == now[key]
for role in stages['240']['assets']:
    assert stages['239']['assets'][role]['sha256'] != stages['240']['assets'][role]['sha256']
assert (before['triangles'], now['triangles'], before['lod_triangles'], now['lod_triangles']) == (77324, 78204, 68640, 68948)
f = read(source / 'geometry-input.json')['front']
c = f['center_local_east_north_m']
t = f['tangent_east_north']
normal = f['outward_normal_east_north']
u = 0.12001386797795273
depth = -1.75
world = lambda du, dep: [now['lng'] + (c[0] + du * t[0] + dep * normal[0]) / (111320 * cos(radians(now['lat']))), now['lat'] + (c[1] + du * t[1] + dep * normal[1]) / 111320]
points = [dict(name='staff lower', position=world(u, depth), z=34.5), dict(name='finial', position=world(u, depth), z=35.636), dict(name='cloth fold', position=world(0.48, depth), z=33.55), dict(name='cloth hem', position=world(0.62, depth), z=33.18)]
cam = lambda du, dep, elevation, angle, pitch, zoom: dict(center=world(du, dep), elevation=elevation, bearing=angle, pitch=pitch, zoom=zoom, padding=dict(top=0, bottom=0, left=0, right=0))
roof_angle = degrees(atan2(-12 * t[0] - 12.1 * normal[0], -12 * t[1] - 12.1 * normal[1]))
river_angle = (f['outward_azimuth_deg'] + 180) % 360
cameras = {'roof': cam(0.24, depth, 34.23, roof_angle, 68, 22.35), 'river': cam(0, -1.3, 28.0, river_angle, 70, 20.75)}
neighbors = {r['id']: r for r in landmarks[240] if r['id'] in ('customs-house', 'bund15')}
assert len(neighbors) == 2
case = dict(id='bund14', cityDestinations=276, base_landmarks=40, unchanged_other_base_landmarks=39, stages=stages, photo_points=points, cameras=cameras, neighbors=neighbors, source_photo_refs=h((source / 'reference-review.json').read_bytes()), native_reference=h((source / 'render_mast.py').read_bytes()), roof_ray_receipt=h((a / 'roof-probes.json').read_bytes()), reference_images={k: h((a / k).read_bytes()) for k in ('roof-prior.png', 'roof-revised.png', 'river-view.png')})
(w / 'bound.json').write_text(json.dumps(case, ensure_ascii=False, indent=2) + '\n')
print('31239/31240', [(s['inputs'], s['count']) for s in stages.values()], cameras['roof'], flush=True)
