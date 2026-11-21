"""Locate source mesh groups crossed by the published camera's eight measured sightlines."""
from pathlib import Path
import gzip,math,json
import numpy as np
from shapely.geometry import shape,Point,LineString
from shapely.affinity import translate,scale
p=Path('/workspace/e-resource/projects/shanghai');a=p/'data/audit/bearn-apartments-v1';origin=Path('/tmp/moneyguild277/macro');w=Path(__file__).parent
read=lambda f:json.loads(f.read_bytes())
c=read(a/'final-placement-contract.json');v=read(a/'overview-sightlines.json')
n=6371008.8*math.pi/180;e=n*math.cos(math.radians(c['lat']));s=math.sin(math.radians(c['heading']));co=math.cos(math.radians(c['heading']));ax=np.array([[co,-s],[s,co]])
def en(polygon):return scale(translate(polygon,-c['lng'],-c['lat']),xfact=e,yfact=n,origin=(0,0))
def target(f):return [*(np.array(f['author_x_y_z_m'][:2])@ax),f['author_x_y_z_m'][2]]
rays={str(view['viewport']['width']):{'origin':[*(view['eye_east_north_m']),view['eye_height_m']],'targets':[[f['feature'],target(f)]for f in view['samples']]}for view in v['views']}
lines=[LineString([v['origin'][:2],q[:2]])for v in rays.values()for name,q in v['targets']]
table=json.loads(gzip.decompress((origin/'feature-table.json.gz').read_bytes()))['features'];cfg=read(origin/'READY.json');ids=set()
for row in table:
 poly=shape(row['geometry'])
 if poly.distance(Point(c['lng'],c['lat']))>.003:continue
 loc=en(poly)
 if min(line.distance(loc) for line in lines)<1.0:ids.add(row['localId'])
groups=[g for g in cfg['near']if ids.intersection(g['featureLocalIds'])]
import urllib.request
url='http://127.0.0.1:31195/data/precise-buildings-v6.json';index=json.load(urllib.request.urlopen(url,timeout=30));repack=next(m for m in index['macros'] if m['id']=='14-13720-6694')['near']
control=next(f for f in table if f['localId']==2123);pt=en(shape(control['geometry'])).representative_point();negative={'owner':2123,'start':[pt.x,pt.y,120.0],'target':[pt.x,pt.y,0.1]}
data={'negative':negative,'origin':{'lng':c['lng'],'lat':c['lat']},'cfg':{'lng':cfg['origin_longitude'],'lat':cfg['origin_latitude']},'macro':cfg['id'],'source_dir':'assets/city-detail/macros/14-13720-6694/','far':cfg['far'],'retained':sorted(ids),'groups':groups,'repacked':[g for g in repack if any(x['id']==g['id']for x in groups)],'rays':rays,'cut_en':list(en(shape(c['replacement_geometry'])).exterior.coords)}
(w/'mesh-view-selection.json').write_text(json.dumps(data,indent=2)+'\n');print('owners',sorted(ids),'groups',[(g['id'],g['file'],g['size_bytes'])for g in groups],len(data['repacked']))
