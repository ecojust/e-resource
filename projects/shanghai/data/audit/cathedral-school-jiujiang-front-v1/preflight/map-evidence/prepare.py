"""Identify the Jiujiang Road north wall against both source rings and the completed church models."""
from pathlib import Path
import subprocess,json,math,gzip,hashlib,os
from urllib.request import urlopen
import numpy as np,shapely,shapely.ops
from shapely.geometry import shape,mapping,Polygon,LineString,Point
w=Path(__file__).resolve().parent;project=Path('/workspace/e-resource/projects/shanghai');repo=project.parents[1];base='http://127.0.0.1:31259/';rev='65af6bea52780f274d2ee005bbbd513317b559fc';evidence=w.parent/'geometry-evidence.json';j=json.loads(evidence.read_bytes());o=j['way'];owner=j['matches'][0];assert o['id']==292718777 and o['version']==4 and owner['id']==1810 and j['macro']=='14-13720-6694';sha=lambda b:hashlib.sha256(b).hexdigest()
def put(f,v):f.write_text(json.dumps(v,ensure_ascii=False,indent=1)+'\n')
inputs=w/'inputs';inputs.mkdir(exist_ok=True);receipts=[]
def pin(s):
 path='assets/city-detail/macros/'+j['macro']+'/'+s;prefix='projects/shanghai/'+path
 h=subprocess.check_output(['git','rev-parse',rev+':'+prefix],cwd=repo,text=True).strip()
 with urlopen(base+path,timeout=20)as r:data=r.read();assert r.status==200 and sha(data)==r.headers['X-Audit-SHA256']
 assert hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()==h
 p=inputs/Path(s).name
 if not p.exists():
  possibles=[project/path,Path('/tmp/nankin278/mapping/inputs')/p.name,Path('/tmp/portal256-work')/p.name]
  for q in possibles:
   if q.is_file()and sha(q.read_bytes())==sha(data):p.symlink_to(q.resolve());break
  else:p.write_bytes(data)
 assert sha(p.read_bytes())==sha(data);receipts.append(dict(repository_path=prefix,git_blob=h,sha256=sha(data),bytes=len(data),url=base+path));return p
table=json.loads(gzip.decompress(pin('feature-table.json.gz').read_bytes()))['features'];rows={r['localId']:r for r in table};ready=json.loads(pin('READY.json').read_bytes());pin('far.glb')
assert rows[1810]['geometry']==owner['geometry']and sha((inputs/'feature-table.json.gz').read_bytes())==j['feature_table_sha256']
src_ring=owner['geometry']['coordinates'][0];osm_ring=o['coords']
# Use the western origin of the original city ring. Store the equivalent named OSM frame separately.
origin=src_ring[0];end=src_ring[1];R=6371008.8;k=R*math.cos(math.radians(origin[1]));north0=math.asinh(math.tan(math.radians(origin[1])))
def en(points):
 p=np.array(points);return np.column_stack((np.radians(p[:,0]-origin[0])*k,(np.arcsinh(np.tan(np.radians(p[:,1])))-north0)*k))
axis=en([end])[0];length=float(np.linalg.norm(axis));u=axis/length;l=np.array([-u[1],u[0]])
def xy(coords):v=en(coords);return np.column_stack((v@u,v@l))
native=shapely.transform(shape(rows[1810]['geometry']),xy);osm=shapely.transform(Polygon(osm_ring),xy);street=LineString([[0,0],[length,0]])
assert .984<native.intersection(osm).area/native.union(osm).area<.986 and native.centroid.y<0 and length>70
foot=lambda r:shapely.transform(shape(r['geometry']),xy)
nearest=[]
for i,row in rows.items():
 if i==1810 or shape(row['geometry']).distance(shape(owner['geometry']))>.0008:continue
 f=foot(row);a,b=shapely.ops.nearest_points(native,f)
 nearest.append(dict(id=i,key=row['key'],name=row.get('name'),height_m=row.get('height'),full_footprint_distance_m=native.distance(f),north_frontage_distance_m=street.distance(f),intersection_m2=native.intersection(f).area,closest_author_xy=[list(a.coords[0]),list(b.coords[0])]))
nearby=sorted(nearest,key=lambda r:r['full_footprint_distance_m'])[:12];ids={1810,587,616}|{r['id']for r in nearby};groups=[g for g in ready['tiles']if ids.intersection(g['featureLocalIds'])]
for g in groups:assert sha(pin(g['file']).read_bytes())==g['sha256']
allids=sorted({i for g in groups for i in g['featureLocalIds']})
with urlopen(base+'data/candidate-city-integrations.json',timeout=15)as response:catalog=response.read()
models=json.loads(catalog)['models'];church=[r for r in models if r['id']in ['huangpu-holy-trinity-cathedral','huangpu-holy-trinity-bell-tower']];assert {r['owner']['feature_local_id']for r in church}=={587,616};assert not any(r.get('owner',{}).get('feature_local_id')==1810 and r.get('owner',{}).get('macro_id')==j['macro']for r in models if isinstance(r.get('owner'),dict))
review=dict(model_id='huangpu-cathedral-school-jiujiang-front',baseline_commit=rev,frozen_macro=j['macro'],owner=dict(feature_local_id=1810,source_key=rows[1810]['key'],source_record='w292718777@4',source_height_m=rows[1810]['height']),author_frame=dict(anchor=dict(lng=origin[0],lat=origin[1]),runtime_heading_deg=math.degrees(math.atan2(-u[1],u[0]))%360,earth_radius_m=R,x_axis='Western to eastern end of the north wall of original city polygon 1810, metres',positive_y='Outward towards Jiujiang Road',source_west=origin,source_east=end),north_wall_length_m=length,osm_north_wall_local=xy([osm_ring[1],osm_ring[2]]).tolist(),osm_iou=native.intersection(osm).area/native.union(osm).area,source_polygon_author_xy_m=list(native.exterior.coords),osm_polygon_author_xy_m=list(osm.exterior.coords),near_tiles=[dict(id=g['id'],file=g['file'],sha256=g['sha256'],feature_local_ids=g['featureLocalIds'])for g in groups],frozen_bindings=receipts,owners=[dict(local_id=i,key=rows[i]['key'],height=rows[i]['height'],geometry_wgs84=rows[i]['geometry'])for i in allids],all_nearby=nearby,church_footprints=[r for r in nearest if r['id']in [587,616]],source_register_sha256=sha(evidence.read_bytes()),signed_source_catalog_sha256=sha(catalog),source_endpoint=base)
put(w/'original-review.json',review);put(w/'church-contracts.json',church);print('origin',origin,'east',end,'heading',review['author_frame']['runtime_heading_deg'],'length',length,'church',[(r['id'],r['full_footprint_distance_m'],r['north_frontage_distance_m'])for r in review['church_footprints']],'groups',[(g['id'],len(g['featureLocalIds']))for g in groups],flush=True)
