"""Exercise the actual signed city and retain the preflight distinction from the eventual 325 parent."""
import hashlib, pathlib, os, re, subprocess, json, sys
from urllib.request import urlopen
from urllib.parse import urljoin,urlsplit
from shapely.geometry import shape
from pathlib import Path
w=Path(os.environ.get('COZY_WORK',Path(__file__).parent));project=Path(os.environ.get('COZY_PROJECT',str(next(a for a in Path(__file__).resolve().parents if (a/'tools/package_architectural_model.py').is_file()))));family=Path(os.environ['SHANGHAI_VERIFICATION_TOOLS']);sys.path.insert(0,str(family))
from common import full,canon
n=int(sys.argv[1])if len(sys.argv)>1 else 276;site=w/f'signed-runtime-{n}';site.mkdir(exist_ok=True);(site/'package.json').write_text('{"type":"module"}\n');url=f'http://127.0.0.1:{31000+n}/'
sha=lambda b:hashlib.sha256(b).hexdigest();rd=lambda p:json.loads(p.read_bytes());save=lambda p,j:p.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n')
f=full(n);cmp=rd(family/'scenes'/f'{n}-comparison.json');assert cmp['passed']and cmp['production_receipt_sha256']==sha(canon(f));actual={}
def get(k):
 with urlopen(url+k,timeout=30)as r:assert r.status==200;b=r.read()
 actual[k]=sha(b);assert k not in f['files']or actual[k]==f['files'][k];return b
todo=['vendor/three.module.js','src/candidate-city-clipping.js','src/candidate-vector-clipping.js','src/candidate-city-integrations.js'];seen=set()
while todo:
 path=urlsplit(todo.pop()).path.lstrip('/')
 if path in seen:continue
 seen.add(path);b=get(path);dest=site/path;dest.parent.mkdir(parents=True,exist_ok=True)
 if not dest.exists():
  matches=[q for q in (Path(os.environ['COZY_PRIOR_RUNTIME'])/path,project/path)if q.is_file() and q.read_bytes()==b]
  if matches:dest.symlink_to(matches[0].resolve()) if path.startswith('vendor/') else os.link(matches[0].resolve(),dest)
  else:dest.write_bytes(b)
 assert dest.read_bytes()==b,path
 for end in re.findall(r"(?:from|import)\s*['\"]([^'\"]+)['\"]",b.decode()):
  if end.startswith('.'):todo.append(urlsplit(urljoin(url+path,end)).path)
catkey='data/candidate-city-integrations.json';base=get(catkey);cat=json.loads(base);contract=rd(w/'final-placement-contract.json');g=rd(w/'placement-geometry.json');review=rd(w/'footprint-review.json')
assert not any(z['id']==contract['id']for z in cat['models']);rows=cat['models'];reverted=rows[-1]['id'];tile=review['near_tiles'][0];group=set(tile['feature_local_ids']);clipped=set();existing=set();geo=[]
for r in rows:
 chunks=([dict(geometry=r['replacement_geometry'],owners=r.get('owners')or[r['owner']])]if r.get('replacement_geometry')else [])+([r['site_replacement']]if r.get('site_replacement')else [])
 for k in chunks:
  ids={v['feature_local_id']for v in (k.get('owners')or[k.get('owner')])if v and v['macro_id']==review['frozen_macro']};existing|=ids
  if group&ids:geo.append(k['geometry']);clipped|=(group&ids)
assert 2172 not in existing

from shapely.geometry import shape
m=rd(w/'model-assets.json')
row={**contract,'kind':'building','height_m':contract['bounds_glb']['max'][1],'assets':{key:{**m['assets'][role],'file':'assets/models/candidates/'+m['id']+'/'+contract['id']+suffix}for key,role,suffix in [('web','full','-web.glb'),('lod','lod','-lod.glb')]}}
group=set(tile['feature_local_ids']);neighbors=sorted(set(review['checked_neighbors']));centers=[dict(id=r['local_id'],point=list(shape(r['geometry']).representative_point().coords[0]))for r in review['owners']if r['local_id']in neighbors]
assert len(centers)==len(neighbors)==13
points=g['ground_probes'];spec=dict(id=contract['id'],previous=reverted,predecessor_catalog_sha256=sha(base),owner=2172,neighbors=neighbors,existingCandidateOwners=sorted(existing & set(neighbors)),existingGroupOwners=sorted(clipped),group=sorted(group),addedTriangles=4,neighborGround=centers,points=points,ground=[dict(name=b['name'],xy=b['xy'],expected=b['expected_map'],cut=b['source_cut'],modelObstacle=b['model_obstacle']) for b in points],front=dict(center=[0,0],elevation=4,bearingOffset=0,pitch=77,zoom=20.7),roof=dict(center=[0,.2],elevation=6.5,bearingOffset=-8,pitch=73,zoom=20.6))
data=dict(row=row,contract=contract,spec=spec,review=review,catalog=cat);runtime=Path(__file__).with_name('runtime-328.mjs')
receipt=json.loads(subprocess.check_output(['node',runtime,site],input=json.dumps(data).encode()))
assert len(receipt['ground'])==len(points)+13 and len(receipt['vector'])==28
spec['groupTriangles']=receipt['after']['scopedTargetDraw']['triangles'];save(w/'map-case.json',spec);save(w/'runtime-placement.json',receipt)
save(w/'runtime-baseline.json',dict(order=n,source=reverted,origin=url,production_sha256=cmp['production_receipt_sha256'],catalog_sha256=sha(base),inputs=actual,runtime_checker_sha256=sha(runtime.read_bytes()),checked_runtime_sha256=sha((w/'runtime-placement.json').read_bytes())))
print('signed runtime',n,len(receipt['ground']),len(receipt['vector']),receipt['after']['bands'])
