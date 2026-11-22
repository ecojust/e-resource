"""Project nine documented bridge features using the camera module and the area geometry actually served on 31230."""
from pathlib import Path
from urllib.request import urlopen
from hashlib import sha256
import runpy,json,math,importlib.util,gzip
from shapely.geometry import shape,Point
from shapely.affinity import scale,translate
w=Path(__file__).parent;p=Path('/workspace/e-resource/projects/shanghai')
a=p/'data/audit/zhapu-road-bridge-v1';src=p/'data/audit/pure-heart-church-v1/check-overview-sightlines.py'
read=lambda f:json.loads(f.read_bytes())
digest=lambda b:sha256(b).hexdigest()
stage=Path('/tmp/shanghai-yongjia-porch');sp=importlib.util.spec_from_file_location('final_stage',stage/'common.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);files=m.full(230)['files']
base='http://127.0.0.1:31230/'
key='src/candidate-overview-camera.js';camera_url=base+key
with urlopen(camera_url) as response:camera=response.read()
assert digest(camera)==files[key]
fixture=w/'signed-camera';(fixture/'src').mkdir(parents=True,exist_ok=True)
(fixture/key).write_bytes(camera);(fixture/'package.json').write_text('{"type":"module"}\n')
macro='assets/city-detail/macros/14-13720-6693/feature-table.json.gz'
with urlopen(base+macro,timeout=60)as r: assert r.status==200;table=r.read()
assert digest(table)=='d9b50cd29e04014e5017669347a3849a29a60171d1586325bdd6bd5096072762'
case=read(a/'final-placement-contract.json')
historical=read(a/'overview-sightlines.json')
assert historical['contract_sha256']==digest((a/'final-placement-contract.json').read_bytes())and historical['feature_table_sha256']==digest(table)
source=historical['views'][0]['probes'];assert len(source)==9
positions=[(x['feature'],*x['target_enu'])for x in source];lon,lat=case['lng'],case['lat']
north=math.pi/180*6371008.8;east=north*math.cos(math.radians(lat));volumes=[]
for row in json.loads(gzip.decompress(table))['features']:
 if not row.get('geometry'):continue
 poly=scale(translate(shape(row['geometry']),-lon,-lat),xfact=east,yfact=north,origin=(0,0))
 if poly.distance(Point(0,0))<450:volumes.append((row['localId'],poly,row['height']))
eval_camera=runpy.run_path(str(src))['evaluate'];eval_camera.__globals__['PROJECT']=fixture
views=[eval_camera(case,{'width':ww,'height':hh},device,volumes,lon,lat,east,north,positions)for ww,hh,device in [(850,620,'desktop'),(390,844,'phone')]]
assert all(v['clear_count']==9 for v in views)
result=dict(order=230,passed=True,origin=base,source_url=camera_url,signed_camera_sha256=digest(camera),source_table_sha256=digest(table),source_contract_sha256=historical['contract_sha256'],checker_sha256=digest(src.read_bytes()),nearby_footprints=len(volumes),views=views,scope='冻结楼体与屏幕边界；水面渲染、文字灯牌和实际操控由街图检查。')
(w/'ordinary-cameras.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print([(v['view'],v['clear_count'])for v in views],len(volumes))
