"""Read the complete viewer module graph at the source of the interaction report and at the final release."""
from pathlib import Path, PurePosixPath
from urllib.request import urlopen
from urllib.parse import urljoin, urlsplit
from hashlib import sha256
import json,re,sys,subprocess
w=Path(__file__).parent;repo=Path('/workspace/e-resource/projects/shanghai');a=repo/'data/audit/amyron-apartments-v1';v=json.loads((a/'viewer.json').read_bytes());sys.path.insert(0,'/tmp/shanghai-yongjia-porch');from common import full
origin=v['base'];final='http://127.0.0.1:31206/';sign=full(206)['files'];oldsign=json.loads(Path('/tmp/shanghai-west-park-description/scenes/206-production.json').read_bytes())['files'];read=lambda u:urlopen(u,timeout=35)
git='a2ab8c49';git_prefix='projects/shanghai/';refs={};paths=set(v['files']);folder='assets/models/candidates/'+v['id']+'/';paths.update(folder+r['file'] for r in v['downloads'].values());page='amyron-apartments.html';queue=[page];seen=set();comparisons={}
while queue:
 key=queue.pop();seen.add(key)
 with read(urljoin(final,key)) as conn:
  assert conn.status==200;body=conn.read()
 with read(urljoin(origin,key)) as conn:
  assert conn.status==200 and conn.read()==body
 h=sha256(body).hexdigest()
 if key in oldsign and key in sign:
  assert h==oldsign[key]==sign[key];refs[key]='both release manifests'
 else:
  assert (key.startswith('vendor/') or key in ('assets/favicon.svg','src/dacheng-hall.css')) and subprocess.check_output(['git','-C',repo,'cat-file','blob',git+':'+git_prefix+key])==body,key
  refs[key]='published common resource at '+git
 comparisons[key]={'bytes':len(body),'sha256':h}
 if key.endswith(('.js','.html','.css')):
  targets=re.findall(r'''\b(?:from|import)\s*["']([^"']+)["']''',body.decode())
  if key.endswith('.html'):targets+=re.findall(r'''<(?:script|link)\b[^>]*?\b(?:src|href)=["']([^"']+)["']''',body.decode());targets+=list(json.loads(re.search(r'<script type="importmap">(.*?)</script>',body.decode()).group(1))['imports'].values())
  for target in targets:
   target='vendor/three.module.js' if target=='three' else urlsplit(urljoin('http://localhost/'+key,target)).path.lstrip('/')
   if (repo/target).is_file():paths.add(target)
 for k in paths-seen:
  if k not in queue:queue.append(k)
for k,details in v['files'].items():assert details==comparisons[k]
for r in v['downloads'].values():assert comparisons[folder+r['file']]=={k:r[k] for k in ('bytes','sha256')}
for row in v['views']:assert sha256((a/row['file']).read_bytes()).hexdigest()==row['sha256']
assert len(v['views'])==6 and len(v['downloads'])==4 and len(comparisons)>=14
(w/'standalone-signed-replay.json').write_text(json.dumps({'passed':True,'interaction_origin':origin,'final_origin':final,'public_page':page,'signed_http_pairs':comparisons,'independent_binding':refs,'viewer_sha256':sha256((a/'viewer.json').read_bytes()).hexdigest(),'original_screenshots':{r['file']:r['sha256'] for r in v['views']},'saved_downloads':v['downloads']},ensure_ascii=False,indent=2)+'\n');print(len(comparisons),'paired GETs',len(v['views']),'screens',len(v['downloads']),'saved downloads')
