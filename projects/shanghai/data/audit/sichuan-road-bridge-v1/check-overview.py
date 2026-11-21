"""Project the bridge lamps, sidewalks and approaches against retained city buildings."""
from pathlib import Path
from hashlib import sha256
from shapely.affinity import scale,translate
from shapely.geometry import Point,shape
import gzip,json,math,runpy,subprocess
here=Path(__file__).resolve().parent
p=here.parents[2]
shared=here.parent/'pure-heart-church-v1/check-overview-sightlines.py'
evaluate=runpy.run_path(str(shared))['evaluate']
c=json.loads((here/'final-placement-contract.json').read_bytes())
fp='projects/shanghai/assets/city-detail/macros/14-13720-6693/feature-table.json.gz'
revision='ae55637ce1d7cbc4d21fd94934c8309aca1dcd09'
raw=subprocess.check_output(['git','-C',p.parents[1],'show',revision+':'+fp]);assert sha256(raw).hexdigest()=='d9b50cd29e04014e5017669347a3849a29a60171d1586325bdd6bd5096072762'
lon,lat=c['lng'],c['lat'];north=math.pi/180*6371008.8;east=north*math.cos(math.radians(lat))
volumes=[]
for source in json.loads(gzip.decompress(raw))['features']:
 if not source.get('geometry'):continue
 poly=scale(translate(shape(source['geometry']),-lon,-lat),xfact=east,yfact=north,origin=(0,0))
 if poly.distance(Point(0,0))<450:volumes.append((source['localId'],poly,source['height']))
# Heights in photo-model coordinates; add the verified walking datum offset.
targets=[];angle=math.radians(c['heading'])
for name,x,y,z in [('north crossing',34,0,4.25),('south crossing',-34,0,4.25),('east walkway',0,-7.7,4.93),('west walkway',0,7.7,4.93),('south-east lantern',-18.29,-8.72,9.62),('north-east lantern',18.29,-8.72,9.62),('south-west lantern',-18.29,8.72,9.62),('north-west lantern',18.29,8.72,9.62)]:
 x-=.26*y;targets.append((name,x*math.cos(angle)+y*math.sin(angle),-x*math.sin(angle)+y*math.cos(angle),z+c['altitude']))
views=[evaluate(c,dict(width=ww,height=hh),device,volumes,lon,lat,east,north,targets) for ww,hh,device in [(900,650,'desktop'),(390,844,'mobile')]]
print([(d['view'],d['clear_count'],[(t['feature'],t['obstructions'])for t in d['probes']if not t['clear']])for d in views])
record=dict(id=c['id'],contract_sha256=sha256((here/'final-placement-contract.json').read_bytes()).hexdigest(),feature_table_sha256=sha256(raw).hexdigest(),method='Tests retained building obstruction and screen bounds for eight above-water points. Water occlusion of the three soffits is outside this test.',views=views)
(here/'overview-sightlines.json').write_text(json.dumps(record,indent=2,ensure_ascii=False)+'\n')
assert all(v['clear_count']==len(targets)for v in views)
