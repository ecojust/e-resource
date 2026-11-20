import json,math,sys,subprocess,hashlib,gzip
from pathlib import Path
from urllib.request import urlopen
from shapely.geometry import box,Point
root=Path(__file__).parent
for n in [164]:
 work=Path('/tmp/weile164/placement')
 read=lambda f:json.loads(f.read_bytes());case=read(Path('/tmp/shanghai-main-161-166')/f'{n}-inputs.json')
 cm=read(Path('/tmp/shanghai-riyue-courtyard/scenes')/f'{n}-comparison.json');sha=lambda b:hashlib.sha256(b).hexdigest()
 def fetch(path,expected):
  url=f'http://127.0.0.1:{28000+n}/'+path;buf=urlopen(url,timeout=50).read();assert sha(buf)==expected,(path,sha(buf),expected);return buf
 cam=next(x for x in cm['files']if x['path']=='src/candidate-overview-camera.js');(root/f'{n}-camera.mjs').write_bytes(fetch(cam['actual_url'],cam['sha256']))
 catalog='data/candidate-city-integrations.json';url=next(v['url'].split('/',3)[3] for v in case['origins'][-1]['actual']if v['path']==catalog);row=next(i for i in json.loads(fetch(url,cm['catalog_sha256']))['models']if i['id']==case['model']);(root/f'{n}-place.json').write_text(json.dumps(row))
 ready=read(work/'READY.json');lb=row['lng'],row['lat'];base=f'http://127.0.0.1:{28000+n}/assets/city-detail/macros/14-13718-6695/';R=6371008.8*math.pi/180;xx=55/R/math.cos(lb[1]*math.pi/180);yy=55/R;area=box(lb[0]-xx,lb[1]-yy,lb[0]+xx,lb[1]+yy)
 files=[dict(kind='far',url=base+'far.glb',sha256=ready['far']['sha256'])]+[dict(kind='near',url=base+x['file'],sha256=x['sha256'],ids=x['featureLocalIds'])for x in ready['near']if area.intersects(box(*x['geographic_bbox']))]
 outputs={key:dict(sha256=v['sha256'],url=v['url'].replace(':24',':28'))for key,v in case['outputs'].items()}
 for key in ['full','lod']:fetch(outputs[key]['url'].split('/',3)[3],outputs[key]['sha256'])
 fet=ready['published_files']['feature-table.json.gz'];b=fetch(base.split('/',3)[3]+'feature-table.json.gz',fet['sha256']);assert sha((work/'feature-table.json.gz').read_bytes())==sha(b)
 (root/f'{n}-decode.json').write_text(json.dumps(dict(files=files,anchor=lb,origin=[ready['origin_longitude'],ready['origin_latitude']],catalog_sha256=cm['catalog_sha256'],camera_sha256=cam['sha256'],model=outputs,feature_sha256=sha(b)),indent=2));print(n,len(files),flush=True)
 subprocess.run(['node',root/'decode.mjs',str(n)],check=True,cwd=root)
