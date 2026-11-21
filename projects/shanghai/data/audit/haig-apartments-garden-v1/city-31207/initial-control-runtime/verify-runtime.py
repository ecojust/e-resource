"""Pin the actual production UI bytes in the two private viewer fixtures."""
from pathlib import Path
from urllib.request import urlopen
from hashlib import sha256
import os,json
q=Path('/dev/shm/haig207-final');w=Path(__file__).parent
stage=json.loads((q/'fixture.json').read_bytes())['stages']
frozen=w/'immutable-runtime';frozen.mkdir(exist_ok=True)
result=[]
for order,rows in stage.items():
 for key in ['src/app.js','src/candidate-overview-camera.js','src/map-scene.js','src/candidate-city-clipping.js','src/candidate-city-integrations.js','src/building-beacons.js','index.html','landmarks.html']:
  rec=rows[key];old=q/f'city{order}'/key;u=Path(rec['url'].split('?')[0]).name
  data=urlopen(rec['url'],timeout=30).read();h=sha256(data).hexdigest();assert h==rec['sha256'] and len(data)==rec['bytes']
  isolated=frozen/h
  if not isolated.exists():isolated.write_bytes(data)
  assert sha256(isolated.read_bytes()).hexdigest()==h
  orig=old.resolve();l=old.with_suffix('.isolated');l.symlink_to(isolated);os.replace(l,old)
  assert sha256(old.read_bytes()).hexdigest()==h
  result.append(dict(stage=order,path=key,url=rec['url'],bytes=len(data),sha256=h,previous_target=str(orig),isolated=str(isolated)))
(w/'isolated-runtime.json').write_text(json.dumps(result,indent=2)+'\n')
