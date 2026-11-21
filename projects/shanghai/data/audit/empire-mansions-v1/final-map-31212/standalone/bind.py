from pathlib import Path
from urllib.request import urlopen
import hashlib,sys,json,datetime
W=Path(__file__).resolve().parent;P=Path('/workspace/e-resource/projects/shanghai')
sys.path.insert(0,'/tmp/shanghai-yongjia-porch')
import common as c
ID='xuhui-empire-mansions-street-front';base='http://127.0.0.1:31212/';A=P/'data/audit/empire-mansions-v1';assets=P/'assets/models/candidates'/ID
def h(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(p):return json.loads(p.read_bytes())
def remote(rel):
    with urlopen(base+rel,timeout=90)as r:
        assert r.status==200 and r.geturl()==base+rel
        return hashlib.file_digest(r,'sha256').hexdigest()
manifest=read(assets/'manifest.json'); old=read(A/'viewer.json'); geom=read(A/'geometry-native.json')
assert manifest['id']==old['id']==geom['id']==ID and old['passed'] and '26212' in old['base'] and len(old['views'])==4
assert geom['meshopt_decoded_oriented_surfaces_match'] and geom['native_reopened_and_compared']['match_raw']
signature=c.full(212);comp=c.SCENES/'212-comparison.json';comparison=read(comp);assert comparison['passed'] and comparison['production_receipt_sha256']==c.sha(c.canon(signature))
files={}; checks={}; downs={}
for f in (W/'run.py',W/'viewer.cjs',W/'bind.py',comp,A/'viewer.json',A/'geometry-native.json'):files[str(f)]=h(f)
for v in old['views']:
    p=A/v['filename'];assert h(p)==v['sha256'];files[str(p)]=h(p)
public=[P/manifest['viewer_page'],P/'src/candidate-asset-viewer.js',assets/'manifest.json']
for role,item in manifest['assets'].items():
    file=assets/item['file'];assert file.stat().st_size==item['bytes'] and h(file)==geom['sha256'][role]==old['downloads'][role]['sha256']==item['sha256']
    public.append(file);downs[role]={k:item[k]for k in ('file','sha256','bytes')}
for f in public:
    rel=f.relative_to(P).as_posix();digest=remote(rel);assert digest==h(f)==signature['files'][rel],rel;checks[rel]=digest;files[str(f)]=digest
doc=dict(order=212,id=ID,origin=base,page=manifest['viewer_page'],production_sha256=comparison['production_receipt_sha256'],old_origin=old['base'],previous_views=old['views'],reopened_triangles=geom['native_reopened_and_compared']['triangles'],files=files,actual_http=checks,downloads=downs,gate='/tmp/shanghai-main-212/final-map-31212/distant/process.json',bound_at=datetime.datetime.now(datetime.timezone.utc).isoformat())
(W/'inputs.json').write_text(json.dumps(doc,ensure_ascii=False,indent=2)+'\n')
print(h(W/'inputs.json'),len(files),len(public))
