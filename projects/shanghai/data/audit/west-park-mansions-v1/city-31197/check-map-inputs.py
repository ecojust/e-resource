"""Read the district layer and registered original macro bytes before live city QA."""
from pathlib import Path
from urllib.request import urlopen
import hashlib,json,subprocess
p=Path('/workspace/e-resource/projects/shanghai')
q=Path(__file__).parent
review=json.loads((p/'source/precise/changning-west-park-mansions/footprint-review.json').read_bytes())
gitroot=p.parents[1]
bindings={r['repository_path'].removeprefix('projects/shanghai/'):r for r in review['frozen_bindings']}
for name in ['data/districts-display.geojson','assets/city-detail/manifest.json','assets/city/manifest.json']:
 obj=subprocess.check_output(['git','-C',gitroot,'rev-parse',review['baseline_commit']+':projects/shanghai/'+name],text=True).strip()
 local=subprocess.run(['git','-C',gitroot,'cat-file','-p',obj],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 if local.returncode==0:bindings[name]={'git_blob':obj,'sha256':hashlib.sha256(local.stdout).hexdigest(),'bytes':len(local.stdout)}
 else:bindings[name]={'git_blob':obj}
rows=[]
for n in (196,197):
 for name,expected in bindings.items():
  url=f'http://127.0.0.1:{31000+n}/'+name
  try:
   with urlopen(url,timeout=55)as response:
    body=response.read();assert response.status==200
   observed={'sha256':hashlib.sha256(body).hexdigest(),'git_blob':hashlib.sha1(b'blob '+str(len(body)).encode()+b'\0'+body).hexdigest(),'bytes':len(body)}
   passed=all(expected[k]==observed[k] for k in observed if k in expected)
   row={'url':url,'passed':passed,**observed}
  except Exception as e:row={'url':url,'passed':False,'error':str(e)}
  rows.append(row)
(q/'district-and-original-http.json').write_text(json.dumps({'passed':all(x['passed'] for x in rows),'requests':rows},indent=2)+'\n')
print([(r['url'],r.get('error','byte mismatch'))for r in rows if not r['passed']],len(rows),sum(r.get('bytes',0)for r in rows))
