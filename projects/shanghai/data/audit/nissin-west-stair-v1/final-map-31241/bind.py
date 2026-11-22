"""Bind both official Bund 5 sites, their four model files, the two unchanged adjacent buildings and the original photo section."""
from pathlib import Path
from urllib.request import urlopen, Request
from hashlib import sha256, file_digest
from math import cos, radians, sin, hypot, atan2, degrees
import os, sys, json
w = Path(__file__).resolve().parent
p = Path('/workspace/e-resource/projects/shanghai')
a = p / 'data/audit/nissin-west-stair-v1'
source = p / 'source/precise/bund05/revisions/west-service-stair'
sys.path.insert(0, '/tmp/shanghai-yongjia-porch')
from common import full, canon
h = lambda b: sha256(b).hexdigest()
read = lambda p: json.loads(p.read_bytes())
prior_files = read(a / '31240-prior-downloads.json')['four_previous_downloads']
newer = read(a/'31241-edition-http.json')
assert newer['passed'] and newer['model']=='bund05'
new_files = newer['records']
stages = {}
landmarks = {}
want = ['index.html', 'landmarks.html', 'data/landmarks.json', 'data/bund/manifest.json', 'data/bund/lod-v4.json', 'data/candidate-city-integrations.json', 'src/app.js', 'src/map-scene.js', 'src/building-beacons.js', 'src/walk-controller.js']
for n in (240, 241):
    port = 31000 + n
    origin = f'http://127.0.0.1:{port}/'
    prod = full(n)
    sc = Path('/tmp/shanghai-yongjia-porch/scenes')
    cmp = read(sc / f'{n}-comparison.json')
    assert cmp['passed'] and h(canon(prod)) == cmp['production_receipt_sha256']
    http = read(sc / f'{n}-all-http.json') if (sc / f'{n}-all-http.json').is_file() else None
    if http: assert http['passed'] and http['count'] == len(prod['files']) and (http['production_receipt_sha256'] == cmp['production_receipt_sha256'])
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
            assert b'index.html#landmark=bund05&amp;mode=walk' in body
    info = next((r for r in landmarks[n] if r['id'] == 'bund05'))
    for role, (name, sig) in {'raw': ('editable_model', 'raw_sha256'), 'full': ('model', 'web_sha256'), 'lod': ('lod_model', 'lod_sha256'), 'native': ('native_model', 'native_sha256')}.items():
        path = info[name]
        expected = info[sig]
        prior = prior_files[role] if n==240 else new_files[path]
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
    stages[str(n)] = dict(port=port, origin=origin, sha256=cmp['production_receipt_sha256'], count=276, inputs=len(prod['files']), catalog=got['data/candidate-city-integrations.json'], row=info, files=got, assets=assets, all_http_sha256=h((sc / f'{n}-all-http.json').read_bytes()) if http else None)

assert stages['240']['catalog'] == stages['241']['catalog']
before,now=[stages[str(n)]['row'] for n in (240,241)]
assert len(landmarks[240])==len(landmarks[241])==40
assert [v for v in landmarks[240]if v['id']!='bund05']==[v for v in landmarks[241]if v['id']!='bund05']
for k in ('lng','lat','walkStart','bearing','districtId','candidate_id','bounds_glb','bund_number','photo_texture'):assert before[k]==now[k], k
for role in stages['240']['assets']:assert stages['240']['assets'][role]['sha256']!=stages['241']['assets'][role]['sha256'],role
shape=read(a/'geometry-comparison.json')
for role,key in [('web','triangles'),('lod','lod_triangles')]:
 v=shape['variants'][role];assert (before[key],now[key])==(v['old_triangles'],v['new_triangles'])
g=read(Path('/tmp/nisshin241/geometry-input.json'));f=g['front_edge'];frame=read(source/'west-wall-frame.json');assert frame['source_geometry_sha256']==h(Path('/tmp/nisshin241/geometry-input.json').read_bytes())
sx,sy=frame['original_southwest_vertex'];nx,ny=frame['west_wall_start'];L=frame['west_wall_length_m'];ux,uy=(nx-sx)/L,(ny-sy)/L
# Earth/axis conversion is the author's local Mercator frame, north retained.
from math import log,tan,atan,exp,pi
r=6378137.;lon,lat=now['lng'],now['lat'];k=r*cos(radians(lat));m0=log(tan(pi/4+radians(lat)/2))
def pos(x,y):return [lon+degrees(x/k),degrees(2*atan(exp(m0+y/k))-pi/2)]
def st(s,depth):return pos(sx+ux*s-uy*depth,sy+uy*s+ux*depth)
origin=f['center_local_east_north_m'];u=f['tangent_east_north'];out=f['outward_normal_east_north']
def front(s,depth):return pos(*[c+b*s+q*depth for c,b,q in zip(origin,u,out)])
def camera(center,z,bear,pitch,zoom):return dict(center=center,elevation=z,bearing=bear,pitch=pitch,zoom=zoom,padding=dict(top=0,left=0,bottom=0,right=0))
def point(name,pos,z):return dict(name=name,position=pos,z=z)
b=f['outward_azimuth_deg']+180
wc=frame['native_camera'];cams={'west-stair':camera(wc['target_lnglat'],2.12,wc['view_bearing_degrees'],72,22.12),'roof':camera(front(0,-4),27.7,b+13,60,20.2),'main-door':camera(front(0,0),4.4,b,68,21.5),'corner':camera(st(0,.1),8.3,wc['view_bearing_degrees']+18,62,20.1)}
ray=read(a/'west-stair-surface-rays.json')['outcomes'];assert sum(bool(x['passes'])for x in ray['original_web']['checks'])==4
points={'west-stair':[point('stone tread',st(1.82,.96),.8),point('landing',st(4.4,.96),2.25),point('iron rail',st(3.53,1.4),2.34),point('arched west glass south',st(2.19,.05),3.90),point('arched west glass north',st(6.20,.05),3.90)],'roof':[point('retained left gable',front(-4,-1),26.2),point('retained right gable',front(4,-1),26.2)],'main-door':[point('river front door center',front(0,.08),2.8),point('river front door left',front(-1.4,.08),2.8),point('river front door right',front(1.4,.08),2.8)],'corner':[point('Guangdong Road west corner',st(.15,.05),5),point('west transom',st(2.18,.05),4)]}
neighbors={r['id']:r for r in landmarks[241]if r['id']in ('bund03','bund06')};assert len(neighbors)==2
case=dict(id='bund05',cityDestinations=276,base_landmarks=40,unchanged_other_base_landmarks=39,stages=stages,cameras=cams,photo_points=points,neighbors=neighbors,source_photo_refs=h((source/'reference-review.json').read_bytes()),source_frame_sha256=h((source/'west-wall-frame.json').read_bytes()),reference_inputs={n:h((a/n).read_bytes())for n in ('west-stair-surface-rays.json','geometry-comparison.json','registered-glass.json','native-reopen.json','bund05-west-service-stair-preview.png','in-place-catalog-comparison.json')},standalone_route={'public_landmarks_card':'index.html#landmark=bund05&mode=walk','dedicated_public_page':False,'test_only':'private isolated viewer loads four original assets from the signed site'})
(w/'bound.json').write_text(json.dumps(case,ensure_ascii=False,indent=2)+'\n')
print([stages[str(n)]['inputs']for n in (240,241)], 'landmarks',len(landmarks[241]),'source',before['triangles'],now['triangles'])
