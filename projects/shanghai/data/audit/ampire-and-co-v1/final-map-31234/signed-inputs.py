from pathlib import Path
from urllib.request import urlopen
from hashlib import sha256
import json,sys
root=Path(__file__).parent;sys.path.insert(0,'/tmp/shanghai-yongjia-porch')
from common import full
receipt=full(234);name='huangpu-ampire-and-co-building';site='http://127.0.0.1:31234/'
files={}
for key in ['ampire-and-co.html','src/candidate-asset-viewer.js','assets/models/candidates/'+name+'/manifest.json']:
 with urlopen(site+key,timeout=45) as response:
  assert response.status==200;data=response.read()
 expected=receipt['files'][key];assert sha256(data).hexdigest()==expected
 dest=root/key;dest.parent.mkdir(parents=True,exist_ok=True)
 if dest.is_file():assert sha256(dest.read_bytes()).hexdigest()==expected
 else:dest.write_bytes(data)
 files[key]={'url':site+key,'http':200,'bytes':len(data),'sha256':expected}
(root/'source-inputs.json').write_text(json.dumps(files,indent=2)+'\n')
