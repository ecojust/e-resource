#!/usr/bin/env python3
"""Finite read-only camera/source/actual RAW sightline checks; no model/runtime edits."""
import gzip,json,hashlib,math,struct
from pathlib import Path
import numpy as np
from shapely.geometry import shape,Point,LineString
from shapely.ops import transform
H=Path(__file__).resolve().parent;V=H.parent.parent;P=Path('/workspace/shanghai_project')
G=H.parent/'frozen-main-v12/yangpu-library/geometry-input.json';g=json.loads(G.read_bytes());anchor=g['anchor'];R=6378137.;c=math.cos(math.radians(anchor[1]));ox=R*math.radians(anchor[0]);oy=R*math.log(math.tan(math.pi/4+math.radians(anchor[1])/2))
def descriptor(p):
 b=p.read_bytes();return {'path':str(p),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
def xy(x,y,z=None):return((R*math.radians(x)-ox)*c,(R*math.log(math.tan(math.pi/4+math.radians(y)/2))-oy)*c)
def offset(e,n,z):return {'lng':anchor[0]+math.degrees(e/(R*c)),'lat':anchor[1]+math.degrees(n/R),'alt':z}
def actual_enu(q):return [*xy(q['lng'],q['lat']),q['alt']]
def segment_interval(geom,line):
 if geom.is_empty:return []
 if geom.geom_type in ('LineString','Point'):
  ts=[line.project(Point(p))/line.length for p in geom.coords];return [(min(ts),max(ts))]
 return [r for sub in geom.geoms for r in segment_interval(sub,line)]
def clear3d(f,poly,eye,aim):
 line=LineString([eye[:2],aim[:2]]);ints=segment_interval(poly.intersection(line),line);hits=[]
 for lo,hi in ints:
  zs=[eye[2]+t*(aim[2]-eye[2])for t in [lo,hi]]
  if max(zs)>=f['base'] and min(zs)<=f['height']:hits.append({'t_interval':[lo,hi],'ray_alt_interval':zs,'building_z':[f['base'],f['height']]})
 return hits
table_path=P/'assets/city-detail/macros/14-13722-6690/feature-table.json.gz';table=json.loads(gzip.decompress(table_path.read_bytes()));all_features=[(f,transform(xy,shape(f['geometry'])))for f in table['features']]
# The old navigation screen selected all footprints within150m of east55m.
selected=[(f,p)for f,p in all_features if p.distance(Point(55,0))<=150];assert len(selected)==64
requested={'from_enu_m':[0,-85,12],'to_enu_m':[.8,-40.91,5],'fov_degrees':52}
geo={'from':offset(*requested['from_enu_m']),'to':offset(*requested['to_enu_m']),'fov':52};eye=actual_enu(geo['from']);aim=actual_enu(geo['to']);line=LineString([eye[:2],aim[:2]])
assert max(Point(55,0).distance(Point(v))for v in [eye[:2],aim[:2]])+.5<150,'64-building screen does not cover new segment'
old={'from':{'lng':121.51890357575401,'lat':31.309848792591403,'alt':12.380500000000001},'to':{'lng':121.51878770435401,'lat':31.310840957391402,'alt':5.177300000000001},'fov':52};old_eye=actual_enu(old['from']);old_aim=actual_enu(old['to']);old_inside=[];rows=[]
for f,p in selected:
 base=float(f['base']);height=float(f['height']);d=p.distance(Point(eye[:2]));dz=max(base-eye[2],eye[2]-height,0.);distance=math.hypot(d,dz)
 if p.covers(Point(old_eye[:2])) and base<=old_eye[2]<=height:old_inside.append({'localId':f['localId'],'key':f['key'],'base_m':base,'height_m':height})
 rows.append({'localId':f['localId'],'key':f['key'],'source_footprint_local_enu':p.__geo_interface__,'base_m':base,'height_m':height,'eye_planar_distance_m':d,'eye_extruded_volume_distance_m':distance,'camera_half_metre_ball_clear':distance>.5,'sightline_planar_clearance_m':p.distance(line),'sightline_source_extrusion_hits':clear3d(f,p,eye,aim)})
neighbors=[r for r in rows if r['localId']!=1196]
assert all(r['camera_half_metre_ball_clear'] for r in rows)
assert all(not r['sightline_source_extrusion_hits']for r in neighbors)
assert old_inside,'Old camera embedding must be observed, not guessed'
# Actual final RAW, all365524 triangles, oriented geometry; last0.5m at intended facade excluded.
raw=V/'model/package-v6/yangpu-library-raw.glb';data=raw.read_bytes();magic,version,size=struct.unpack_from('<4sII',data);assert(magic,version,size)==(b'glTF',2,len(data));n,kind=struct.unpack_from('<II',data,12);assert kind==0x4e4f534a;doc=json.loads(data[20:20+n]);blen,bkind=struct.unpack_from('<II',data,20+n);assert bkind==0x004e4942;binary=data[28+n:28+n+blen]
for node in doc['nodes']:
 assert not any(k in node for k in ['matrix','translation','rotation','scale','extensions']),'Explicit transforms require a separate world decoder'
def acc(i):
 a=doc['accessors'][i];b=doc['bufferViews'][a['bufferView']];assert not a.get('sparse') and not b.get('extensions');dtype={5123:'<u2',5125:'<u4',5126:'<f4'}[a['componentType']];count={'SCALAR':1,'VEC3':3}[a['type']];item=np.dtype(dtype).itemsize
 return np.ndarray((a['count'],count),dtype=dtype,buffer=binary,offset=b.get('byteOffset',0)+a.get('byteOffset',0),strides=(b.get('byteStride',item*count),item))
tri=[]
for mesh in doc['meshes']:
 for p in mesh['primitives']:
  xyz=acc(p['attributes']['POSITION']).astype(float);ids=acc(p['indices']).ravel().astype(int);assert p.get('mode',4)==4;tri.append(xyz[ids.reshape(-1,3)])
tri=np.concatenate(tri);assert len(tri)==365524
orig=np.array([eye[0],eye[2],-eye[1]]);target=np.array([aim[0],aim[2],-aim[1]]);delta=target-orig;length=np.linalg.norm(delta);direction=delta/length
e1=tri[:,1]-tri[:,0];e2=tri[:,2]-tri[:,0];h=np.cross(direction,e2);det=np.einsum('ij,ij->i',e1,h);valid=np.abs(det)>1e-10;inv=np.zeros(len(tri));inv[valid]=1/det[valid];s=orig-tri[:,0];u=inv*np.einsum('ij,ij->i',s,h);q=np.cross(s,e1);v=inv*np.einsum('ij,j->i',q,direction);distance=inv*np.einsum('ij,ij->i',e2,q);hit=valid&(u>=-1e-8)&(v>=-1e-8)&(u+v<=1+1e-8)&(distance>=0)&(distance<=length)
hits=sorted(float(d)for d in distance[hit]);obstructions=[d for d in hits if d<length-.5];assert not obstructions,'Actual model obstructs centerline before intended facade'
out={'schema':'yangpu-safe-south-review-camera-v3','passed':True,'scope':'Finite camera/extruded mapped neighbors and one actual final RAW center sightline. QA view proposal only, no product/nav/model changes or browser acceptance.','requested_enu':requested,'requested_geographic_as_actual_qa_offset_helper':geo,'actual_source_builder_enu':{'from':eye,'to':aim},'input_files':[descriptor(G),descriptor(table_path),descriptor(raw)],'same64_source_features_screen':{'center_enu':[55,0],'radius_m':150,'count':len(rows),'new_segment_and_half_metre_ball_inside_screen':True},'camera_ball_radius_m':.5,'all64_eye_balls_clear':True,'other63_sightline_extrusion_hits':0,'nearest_non_target':sorted([{k:r[k]for k in ['localId','key','base_m','height_m','eye_planar_distance_m','eye_extruded_volume_distance_m']}for r in neighbors],key=lambda r:r['eye_planar_distance_m'])[:5],'previous_actual_requested_camera':old,'previous_eye_actual_enu':old_eye,'previous_eye_inside_source_buildings':old_inside,'actual_raw_sightline':{'triangles_tested':len(tri),'segment_length_m':float(length),'end_exclusion_at_intended_facade_m':.5,'hits_before_exclusion':len(obstructions),'all_hit_distances_m':hits,'passed':True},'source_features':rows,'limitations':['Finite eye sphere and central sightline only; not every pixel, FOV ray, vegetation or street furniture.','Source-building heights are original city estimates; not measured architectural facade elevations.','Actual RAW center ray intentionally permits the final0.5m to hit the intended south facade.','No claimed walkable terrain/public-access proof; this is an overview review camera only.','Final browser screenshot remains required to judge framing and nearby context.']}
p=H/'safe-south-view.json'
with p.open('x')as f:json.dump(out,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
print(json.dumps({'output':descriptor(p),'from_to':geo,'nearest':out['nearest_non_target'][0],'old_inside':old_inside,'raw_sightline':out['actual_raw_sightline']},ensure_ascii=False,indent=2))
