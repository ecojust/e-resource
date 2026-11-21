"""Measure the front, green address, eaves and two pairs of windows against the preserved city."""
from pathlib import Path
from hashlib import sha256
from shapely.affinity import scale,translate
from shapely.geometry import Point,shape
import gzip,json,math,runpy,subprocess
here=Path(__file__).resolve().parent
p=here.parents[2];check=runpy.run_path(str(here.parent/'pure-heart-church-v1/check-overview-sightlines.py'))['evaluate'];read=lambda f:json.loads(f.read_bytes())
contract=here/'final-placement-contract.json';c=read(contract);ref=read(p/'source/precise'/c['id']/'footprint-review.json')
binding=next(r for r in ref['frozen_bindings']if r['repository_path'].endswith('feature-table.json.gz'))
raw=subprocess.check_output(['git','-C',p.parents[1],'show',ref['baseline_commit']+':'+binding['repository_path']]);assert sha256(raw).hexdigest()==binding['sha256']
lon,lat=c['lng'],c['lat'];north=math.pi/180*6371008.8;east=north*math.cos(math.radians(lat));volumes=[]
for s in json.loads(gzip.decompress(raw))['features']:
 if not s.get('geometry')or s['localId']==832:continue
 g=scale(translate(shape(s['geometry']),-lon,-lat),xfact=east,yfact=north,origin=(0,0))
 if g.distance(Point(0,0))<420:volumes.append((s['localId'],g,s['height']))
a=math.radians(c['heading']);targets=[]
for name,x,y,z in [('lane plaque',-4.135,-.04,2.31),('left ground bow',-2.05,-.02,1.45),('right ground bow',2.12,-.02,1.45),('first straight-head pair',-2.05,-.07,4.99),('second straight-head pair',2.02,-.07,4.99),('first arch-head pair',-2.03,-.07,8.10),('second arch-head pair',2.02,-.07,8.10),('south roofline',0,-.25,11.13)]:
 targets.append((name,x*math.cos(a)+y*math.sin(a),-x*math.sin(a)+y*math.cos(a),z))
screens=[(900,650,'desktop'),(390,844,'phone')]
def views(row):
 return [check(row,{'width':w,'height':h},device,volumes,lon,lat,east,north,targets) for w,h,device in screens]
chosen=views(c)
if min(q['clear_count']for q in chosen)!=len(targets):
 options=[]
 for pitch in [45,40,34,28,24]:
  for off in [0,-17,15,30,-30,45,-45,70,-70]:
   for zoom in [20.3,20.55,20.7,20.12]:
    candidate=dict(c,overviewBearing=(c['heading']+off)%360,overviewPitch=pitch,overviewZoom=zoom);vs=views(candidate);options.append((min(q['clear_count']for q in vs),candidate,vs))
    if options[-1][0]==len(targets):break
   if options[-1][0]==len(targets):break
  if options[-1][0]==len(targets):break
 count,c,chosen=max(options,key=lambda v:v[0])
 if count==len(targets):contract.write_text(json.dumps(c,indent=2,ensure_ascii=False)+'\n')
print([(q['view'],q['clear_count'])for q in chosen],c['overviewBearing'],c['overviewPitch'],c['overviewZoom'])
(here/'overview-sightlines.json').write_text(json.dumps({'contract_sha256':sha256(contract.read_bytes()).hexdigest(),'feature_table_sha256':binding['sha256'],'views':chosen},ensure_ascii=False,indent=2)+'\n')
assert all(q['clear_count']==len(targets)for q in chosen)
