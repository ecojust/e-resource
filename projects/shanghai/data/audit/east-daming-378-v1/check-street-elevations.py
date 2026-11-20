"""Trace the actual street facade, set-back tiers, supported lookout and corner joins."""
from pathlib import Path
import argparse,hashlib,json,runpy
import numpy as np
a=argparse.ArgumentParser(description=__doc__)
for k in ('project','manifest','decoded','out'):a.add_argument('--'+k,type=Path,required=True)
a=a.parse_args();doc=json.loads(a.manifest.read_bytes());Scene=runpy.run_path(str(a.project/'data/audit/postal-office-v1/independent-glb-review-helpers.py'))['SerialScene']
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
rows=[]
for role in ('raw','full','lod'):
 f=a.manifest.parent/doc['assets'][role]['file'];assert sha(f)==doc['assets'][role]['sha256']
 dec=f if role=='raw'else a.decoded/(role+'.glb');s=Scene(dec);tests=[]
 def ray(name,o,d,mats,br):
  h=s.ray(o,d,60)
  assert h and h['material']in mats and br[0]<=h['distance_m']<=br[1],(role,name,h,br)
  tests.append({'part':name,'origin':o,'direction':d,'distance_m':h['distance_m'],'material':h['material']})
 glaze={'metal sash','window glass'};brick={'old red brick','burnt brick','rose brick','red pointing'}
 for j in range(7):
  u=(j-3)*(27.76/7)
  for z in (2.4,6.4,11.3):ray('east Daming Road continuous seven-bay window row',[u+.20,-4,z],[0,1,0],glaze,(4.16,4.33))
  ray('street-level segmental brick hood',[u,-4,4.03],[0,1,0],{'burnt brick','red pointing'},(3.88,4.03))
 for j in range(6):
  u=(-11.9+11.6)/2+(j-2.5)*(23.5/6);ray('fourth-storey recessed street window',[u+.20,-4,14.37],[0,1,0],glaze,(6.15,6.35))
 for j in range(4):
  u=.10+(j-1.5)*(17.4/4);ray('fifth-storey recessed street window',[u+.20,-4,17.09],[0,1,0],glaze,(8.52,8.77))
 n=46
 for idx in (7,12,17):
  u=(idx+.5)*27.76/n-13.88
  ray('open square perforation in front parapet',[u,-4,9.54],[0,1,0],brick,(3.96,4.03))
  ray('solid white web between perforations',[u+.238,-4,9.54],[0,1,0],{'cream concrete'},(3.53,3.60))
 for z in (3.24,7.2,14.2):
  ray('tower front recessed sash',[14.34,8.29,z],[0,1,0],glaze,(.88,1.07))
  ray('tower west return recessed sash',[19.6,11.24+.16,z],[-1,0,0],glaze,(3.7,3.90))
 for dx in (-.74,.17,.76):
  ray('three points through glazed pavilion',[13.81+dx,6.45,19.76],[0,1,0],glaze,(2.86,3.10))
 ray('tower shell behind lookout railing',[15.66,6.46,16.63],[0,1,0],brick,(2.49,2.63))
 ray('green curved roof canopy south exterior',[16.39,11.24,30],[0,0,-1],{'green tile','tile ridges','eaves wood'},(8.39,8.59))
 ray('steep green tiled pyramid upper face',[14.42,11.24,30],[0,0,-1],{'green tile','tile ridges'},(4.66,5.22))
 ray('pale roof finial',[13.81,11.24,30],[0,0,-1],{'grey stone sill'},(3.20,3.35))
 ray('short link street wall',[12.0,5.44,15.25],[0,1,0],{'shaded render'},(1.36,1.44))
 ray('short link return behind full-depth front wall',[13.9,7.26,15.25],[-1,0,0],{'shaded render'},(1.73,1.77))
 rows.append({'variant':role,'sha256':sha(f),'decoded_sha256':sha(dec),'triangles':len(s.tri),'checks':tests})
a.out.parent.mkdir(exist_ok=True,parents=True);a.out.write_text(json.dumps({'id':doc['id'],'passed':True,'manifest_sha256':sha(a.manifest),'script_sha256':sha(Path(__file__)),'count':sum(len(z['checks'])for z in rows),'variants':rows},ensure_ascii=False,indent=2)+'\n');print(sum(len(z['checks'])for z in rows))
