from pathlib import Path
import json,runpy,hashlib
import argparse, subprocess, tempfile
parser=argparse.ArgumentParser()
parser.add_argument('--manifest',type=Path,required=True)
parser.add_argument('--out',type=Path,required=True)
args=parser.parse_args()
project=Path(__file__).resolve().parents[3]
Scene=runpy.run_path(str(project/'data/audit/postal-office-v1/independent-glb-review-helpers.py'))['SerialScene']
manifest=json.loads(args.manifest.read_bytes());assert manifest['id']=='huangpu-sichuan-road-bridge'
decoder=project/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
results={}
with tempfile.TemporaryDirectory() as scratch:
 for variant in ['raw','full','lod']:
  item=manifest['assets'][variant];packed=args.manifest.parent/item['file']
  assert hashlib.sha256(packed.read_bytes()).hexdigest()==item['sha256']
  path=packed
  if variant!='raw':
   path=Path(scratch)/(variant+'.glb')
   subprocess.run(['node',decoder,packed,path,project/'vendor/meshopt_decoder.module.js'],check=True)
  s=Scene(path);checks=[]
  def ray(name,origin,direction,length,expected):
   hit=s.ray(origin,direction,length);actual=hit and hit['material'];checks.append(dict(name=name,origin=origin,direction=direction,length_m=length,expected=expected,actual=actual,distance=hit and hit['distance_m']));assert actual==expected,(name,hit)
  for x in [-26.5,0,26.5]:
   ray('open river passage',[x,-14,1.2],[-.26,1,0],32,None)
   ray('asphalt above passage',[x,0,14],[0,0,-1],20,'asphalt')
   for y in [-7.75,7.75]:
    ray('sidewalk above passage',[x-.26*y,y,14],[0,0,-1],20,'pavement')
  for x in [-18.29,18.29]:
   for side in [-1,1]:
    y=side*8.72;px=x-.26*y
    ray('lamp pedestal',[px,side*12,6.02],[0,-side,0],8,'pale concrete')
    ray('lantern cap',[px,y,14],[0,0,-1],9,'dark metal')
  for x in [-9,0,9]:
   for side in [-1,1]:
    y=side*8.91;ray('coped solid parapet',[x-.26*y,y,14],[0,0,-1],14,'moulding')
  assert len(s.tri)==item['triangles']
  results[variant]=dict(sha256=item['sha256'],decoded_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),triangles=len(s.tri),checks=checks)
args.out.write_text(json.dumps(dict(id=manifest['id'],manifest_sha256=hashlib.sha256(args.manifest.read_bytes()).hexdigest(),variants=results),indent=2)+'\n')
print({k:len(v['checks']) for k,v in results.items()})
