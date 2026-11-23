"""Register the photographed south entrance against the fixed city macro, the contemporary street and named OSM footprint."""
import os
from pathlib import Path
from urllib.request import urlopen
from hashlib import sha256,sha1
from shapely.geometry import shape,Polygon,Point
from shapely.ops import transform
import json,gzip,math,subprocess,shutil
w=Path(__file__).parent;src=next(a for a in Path(__file__).resolve().parents if (a/'tools/package_architectural_model.py').is_file());name='huangpu-cozy-apartments-494-lane-portal';tag='cozy-apartments-huaihai-lane-portal-v1';fid=2172;base='http://127.0.0.1:31276/';macro='14-13720-6694';pref='assets/city-detail/macros/'+macro+'/';rev='ae55637ce1d7cbc4d21fd94934c8309aca1dcd09';R=6371008.8
def load(p):return json.loads(p.read_bytes())
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def fetch(k):
 with urlopen(base+pref+k,timeout=40)as r:assert r.status==200;return r.read()
def bind(k,b):
 path='projects/shanghai/'+pref+k;oid=subprocess.check_output(['git','--no-lazy-fetch','rev-parse',rev+':'+path],cwd=src.parents[1],text=True).strip();assert sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==oid
 return dict(repository_path=path,git_blob=oid,bytes=len(b),sha256=sha256(b).hexdigest())
photo=load(w/'multi-station-portal.json');osm=load((Path(os.environ['COZY_REFERENCE_FILES'])/'neighborhood.json'));assert osm['owner']['id']=='494956474' and osm['owner']['tags']['heritage:ref']=='4C002'
lon,lat=photo['wgs84'];angle=math.radians(photo['runtime_heading_deg']);st,ct=math.sin(angle),math.cos(angle);k=R*math.cos(math.radians(lat));y0=math.asinh(math.tan(math.radians(lat)))
def local(lng,latitude):
 dx=k*math.radians(lng-lon);dy=k*(math.asinh(math.tan(math.radians(latitude)))-y0);return ct*dx-st*dy,st*dx+ct*dy
a=fetch('READY.json');b=fetch('feature-table.json.gz');ready=json.loads(a);features=json.loads(gzip.decompress(b))['features'];owners={r['localId']:r for r in features};owner=owners[fid];group=next(g for g in ready['tiles'] if fid in g['featureLocalIds']);assert owner['properties']['sources'][0]['record_id']=='w494956474@2' and owner['height']==16
assert owner['properties']['@name']=='康绥公寓';raw_geom=transform(local,shape(owner['geometry']));live_geom=transform(local,Polygon(osm['owner']['line']));iou=raw_geom.intersection(live_geom).area/raw_geom.union(live_geom).area;assert iou>.98
nearest=sorted((transform(local,shape(v['geometry'])).distance(Point(0,0)),i) for i,v in owners.items() if i!=fid);other=set(group['featureLocalIds'])-{fid};other.update([97,1180]);oth=sorted(other,key=lambda i:next(d for d,row in nearest if row==i));target=oth+[i for _,i in nearest if i not in other][:13-len(oth)];assert len(target)==13
grps=[r for r in ready['tiles']if set(r['featureLocalIds']).intersection([fid,*target])]
proof=[bind('READY.json',a),bind('feature-table.json.gz',b)];proof.extend(bind(fn,fetch(fn)) for fn in [group['file'],'far.glb']);assert proof[-2]['sha256']==group['sha256'] and proof[-1]['sha256']==ready['far']['sha256']
seen=[dict(local_id=i,key=owners[i]['key'],name=owners[i]['properties'].get('@name'),geometry=owners[i]['geometry'],geometry_wgs84=owners[i]['geometry'],source_height_m=owners[i]['height'],dist_portal_m=transform(local,shape(owners[i]['geometry'])).distance(Point(0,0)))for i in [fid,*target]]
fr=dict(anchor={'lng':lon,'lat':lat},runtime_heading_deg=photo['runtime_heading_deg'],earth_radius_m=R,x='向照片右、沿淮海中路东偏北',y='从题额向室内西北');out=dict(id=name,model_id=name,sequence=328,baseline_commit=rev,frozen_macro=macro,frozen_bindings=proof,near_tiles=[dict(id=group['id'],file=group['file'],feature_local_ids=group['featureLocalIds'],sha256=group['sha256'])],owners=seen,selection=dict(owner=fid,checked_neighbors=target,source='w494956474@2',historical_register='4C002',scope='淮海中路494弄石框门、题额、二层双窗及可见通道前段'),author_frame=fr,source_iou=iou,checked_neighbors=target,source_area_m2=raw_geom.area,osm_resource=osm['source'],photogrammetry_sha256=sha256((w/'multi-station-portal.json').read_bytes()).hexdigest());write(w/'footprint-review.json',out);(src/'source/precise'/name).mkdir(exist_ok=True,parents=True);shutil.copyfile(w/'footprint-review.json',src/'source/precise'/name/'footprint-review.json')
case=dict(anchor=[lon,lat],runtime_heading_degrees=fr['runtime_heading_deg'],outer_bearing=photo['exterior_bearing_deg'],source_hashes=proof,origin=base+pref,original_owner=fid,source_height=16,checked_neighbors=target,checked_source_frame=fr,macro_origin=[ready['origin_longitude'],ready['origin_latitude']],groups=[dict(id=r['id'],file=r['file'],sha256=r['sha256'],owners=r['featureLocalIds'],triangles=r['expandedTriangles'])for r in grps],inward_distance_to_old_wall=round(raw_geom.boundary.distance(Point(0,0)),4));write(w/'portal-frame.json',case);print(iou,round(raw_geom.area,3),case['inward_distance_to_old_wall'],[(r['id'],len(r['featureLocalIds']))for r in grps],target)
