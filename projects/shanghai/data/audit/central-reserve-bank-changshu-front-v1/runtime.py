"""Exercise the actual signed city and retain the preflight distinction from the eventual 321 parent."""
import hashlib, pathlib, os, re, subprocess, json, sys
from urllib.request import urlopen
from urllib.parse import urljoin,urlsplit
from shapely.geometry import shape
from pathlib import Path
w=Path(os.environ.get('CHANGSHU_WORK',Path(__file__).parent));project=Path(os.environ.get('CHANGSHU_PROJECT',Path(__file__).resolve().parents[2]));family=Path(os.environ['SHANGHAI_RELEASE_TOOLS']);sys.path.insert(0,str(family))
from common import full,canon
n=int(sys.argv[1])if len(sys.argv)>1 else 274;site=w/f'signed-runtime-{n}';site.mkdir(exist_ok=True);(site/'package.json').write_text('{"type":"module"}\n');url=f'http://127.0.0.1:{31000+n}/'
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
  dest.write_bytes(b)
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
assert 3343 not in existing
counts=json.loads(subprocess.check_output(['node',project/'data/audit/kangding-central-portico-v1/count-clip-triangles.mjs'],input=json.dumps([*geo,contract['replacement_geometry']]).encode()))
neighbors=sorted(group.union(review['selection']['checked_neighbors'])-{3343});centers={r['local_id']:list(shape(r['geometry']).representative_point().coords[0])for r in review['owners']if r['local_id']in neighbors};assert len(centers)==len(neighbors)
c=dict(id=contract['id'],previous=reverted,predecessor_catalog_sha256=sha(base),neighbors=neighbors,neighborGround=centers,existingCandidateOwners=sorted(existing&set(neighbors)),existingGroupOwners=sorted(clipped),groupTriangles=sum(counts),addedTriangles=counts[-1],sourceSectionCount=g['cap_segments'],front=dict(center=[0,-.32],elevation=8.4,bearingOffset=1,pitch=51,zoom=20.35),roof=dict(center=[0,0],elevation=16.9,bearingOffset=-14,pitch=43,zoom=20.40),residualCutProbe=[0,1.2],ground=[dict(name=r['name'],xy=r['xy'],expected=r['expected_map'],modelObstacle=r['model_obstacle'],cut=r['source_cut'])for r in g['ground_probes']])
save(w/'map-case.json',c);rows.append(contract);cat['resulting_city_count']+=1
subprocess.run(['node','--require',Path(__file__).with_name('runtime.cjs'),project/'tools/check-sourced-candidate-runtime.mjs',w/'map-case.json'],input=json.dumps(cat).encode(),env={**os.environ,'SHANGHAI_PROJECT_ROOT':str(site),'QA_OUTPUT_DIR':str(w),'CHANGSHU_WORK':str(w)},check=True)
r=rd(w/'runtime-placement.json');assert r['after']['scopedTargetDraw']['clip_feature_local_ids']==sorted(clipped|{3343}) and len(r['ground'])==len(c['ground'])+len(neighbors)
save(w/'runtime-baseline.json',dict(order=n,origin=url,production_sha256=cmp['production_receipt_sha256'],mode='preflight' if n!=321 else 'actual predecessor',source=c['previous'],catalog_sha256=sha(base),inputs=actual,physical_model=True,proposed_added_owner=3343,case_sha256=sha((w/'map-case.json').read_bytes()),checked_runtime_sha256=sha((w/'runtime-placement.json').read_bytes())))
print(len(r['ground']),len(r['vector']),n,c['groupTriangles'],r['after']['triangles'])
