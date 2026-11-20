import json,hashlib
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from urllib.request import urlopen
w=Path('/tmp/hamilton-focus-experiment/real-93');old=json.load(open('/tmp/shanghai-city-groups/scenes/93-production.json'));new=json.load(open('/tmp/shanghai-focus-label-views/scenes/93-production.json'));root=Path('/tmp/cishu-group-stage-93/projects/shanghai')
names=set(k for k,v in new['files'].items() if old['files'].get(k)!=v)
routes={'index.html','landmarks.html','src/app.js','src/building-beacon-groups.js','data/candidate-city-integrations.json','src/building-beacons.js','src/map-scene.js'}|names
def check(k):
 response=urlopen('http://127.0.0.1:20093/'+k,timeout=20);raw=response.read();digest=hashlib.sha256(raw).hexdigest();assert digest==new['files'][k];return k,dict(url=response.url,sha256=digest,bytes=len(raw))
with ThreadPoolExecutor(4)as ex:http=dict(ex.map(check,routes))
for name,d in new['files'].items():
 if name not in names:assert hashlib.sha256((root/name).read_bytes()).hexdigest()==d
(w/'proposal.json').write_text(json.dumps(dict(new_snapshot_sha256=hashlib.sha256(Path('/tmp/shanghai-focus-label-views/scenes/93-production.json').read_bytes()).hexdigest(),old_count=len(old['files']),new_count=len(new['files']),unchanged_from_old=len(new['files'])-len(names),changed_or_added=sorted(names),http=http),indent=2)+'\n')
