"""Locate source mesh groups crossed by the published camera's ten measured sightlines."""
from pathlib import Path
import gzip,math,json
import numpy as np
from shapely.geometry import shape,Point,LineString
from shapely.affinity import translate,scale
p=Path('/workspace/e-resource/projects/shanghai');a=p/'data/audit/amyron-apartments-v1';origin=Path('/dev/shm/gao206/placement');w=Path(__file__).parent
read=lambda f:json.loads(f.read_bytes())
c=read(a/'final-placement-contract.json');v=read(a/'overview-sightlines.json')
n=6371008.8*math.pi/180;e=n*math.cos(math.radians(c['lat']));s=math.sin(math.radians(c['heading']));co=math.cos(math.radians(c['heading']));ax=np.array([[co,-s],[s,co]])
def en(polygon):return scale(translate(polygon,-c['lng'],-c['lat']),xfact=e,yfact=n,origin=(0,0))
def target(f):return [*(np.array(f['author_x_y_z_m'][:2])@ax),f['author_x_y_z_m'][2]]
rays={}
r=math.pi/180;radius=6371008.8*math.cos(c['lat']*r);origin_log=math.asinh(math.tan(c['lat']*r))
for row in v['views']:
 vpt=row['viewport'];cam=vpt['camera'];h=vpt['height'];pitch=cam['pitch']*r;bearing=cam['bearing']*r
 distance=h/(2*math.tan(36.87*r/2))*2*math.pi*radius/(512*2**cam['zoom'])
 lng,lat=cam['center'];eye=[(lng-c['lng'])*r*radius-distance*math.sin(pitch)*math.sin(bearing), (math.asinh(math.tan(lat*r))-origin_log)*radius-distance*math.sin(pitch)*math.cos(bearing), cam['elevation']+distance*math.cos(pitch)]
 rays[str(vpt['width'])]={'origin':eye,'targets':[[f['feature'],target(f)]for f in row['samples']]}
lines=[LineString([v['origin'][:2],q[:2]])for v in rays.values()for name,q in v['targets']]
table=json.loads(gzip.decompress((origin/'feature-table.json.gz').read_bytes()))['features'];cfg=read(origin/'macro-READY.json');ids=set()
for row in table:
 poly=shape(row['geometry'])
 if poly.distance(Point(c['lng'],c['lat']))>.003:continue
 loc=en(poly)
 if min(line.distance(loc) for line in lines)<1.0:ids.add(row['localId'])
ids.add(2081)
groups=[g for g in cfg['near']if ids.intersection(g['featureLocalIds'])]
import urllib.request
url='http://127.0.0.1:31206/data/precise-buildings-v6.json';index=json.load(urllib.request.urlopen(url,timeout=30));repack=next((m['near']for m in index['macros'] if m['id']=='14-13718-6695'),[])
control=next(f for f in table if f['localId']==2081);pt=en(shape(control['geometry'])).representative_point();negative={'owner':2081,'start':[pt.x,pt.y,120.0],'target':[pt.x,pt.y,0.1]}
data={'negative':negative,'origin':{'lng':c['lng'],'lat':c['lat']},'cfg':{'lng':cfg['origin_longitude'],'lat':cfg['origin_latitude']},'macro':cfg['id'],'source_dir':'assets/city-detail/macros/14-13718-6695/','far':cfg['far'],'retained':sorted(ids),'groups':groups,'repacked':[g for g in repack if any(x['id']==g['id']for x in groups)],'rays':rays,'cut_en':list(en(shape(c['replacement_geometry'])).exterior.coords)}
(w/'mesh-view-selection.json').write_text(json.dumps(data,indent=2)+'\n');print('owners',sorted(ids),'groups',[(g['id'],g['file'],g['size_bytes'])for g in groups],len(data['repacked']))
