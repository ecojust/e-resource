import struct,json,hashlib,argparse,numpy as np
from pathlib import Path
from shapely.geometry import Polygon,box
from shapely.ops import unary_union
from shapely.strtree import STRtree
ap=argparse.ArgumentParser();ap.add_argument('--model',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);ap.add_argument('--footprint',type=Path,default=Path(__file__).resolve().parent/'news-footprint.json');args=ap.parse_args();raw=args.model;b=raw.read_bytes();n=struct.unpack_from('<I',b,12)[0];g=json.loads(b[20:20+n]);blob=b[28+n:]
def accessor(index):
 a=g['accessors'][index];v=g['bufferViews'][a['bufferView']];cols={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[a['type']];dtype=np.dtype({5120:'i1',5121:'u1',5122:'<i2',5123:'<u2',5125:'<u4',5126:'<f4'}[a['componentType']]);off=v.get('byteOffset',0)+a.get('byteOffset',0);stride=v.get('byteStride',dtype.itemsize*cols);return np.ndarray((a['count'],cols),dtype,blob,off,(stride,dtype.itemsize)).copy()
poly=json.loads(args.footprint.read_text())['polygon_local_east_north'];A=np.array(poly[2]);B=np.array(poly[3]);T=(B-A)/np.linalg.norm(B-A);N=np.array([T[1],-T[0]]);C=(A+B)/2;groups={}
for mesh in g['meshes']:
 for p in mesh['primitives']:
  if g['materials'][p['material']]['name']!='limestone':continue
  verts=accessor(p['attributes']['POSITION']).astype(float);idx=accessor(p['indices']).ravel().reshape(-1,3);ts=verts[idx];en=ts[:,:,[0,2]]*np.array([1,-1]);us=(en-C)@T;ds=(en-C)@N;zs=ts[:,:,1];norms=np.cross(ts[:,1]-ts[:,0],ts[:,2]-ts[:,0]);lengths=np.linalg.norm(norms,axis=1);directions=(norms@np.array([T[0],0,-T[1]]))/np.maximum(lengths,1e-30)
  for i in np.where((np.abs(directions)>.99999)&(zs.min(axis=1)>=9.39)&(zs.max(axis=1)<=26.96)&(ds.min(axis=1)>-.426)&(ds.max(axis=1)<.026)&(lengths>1e-7))[0]:
   u=float(us[i].mean());shape=Polygon(np.column_stack([ds[i],zs[i]]));groups.setdefault(round(u,4),[]).append({'shape':shape,'sign':1 if directions[i]>0 else -1,'u':u,'tri':int(i),'vertices_glb':ts[i].tolist()})
rows=[];total=0
for u,faces in groups.items():
 qs=[f['shape'] for f in faces];tree=STRtree(qs)
 for i,q in enumerate(qs):
  for jj in tree.query(q):
   j=int(jj)
   if j<=i or faces[j]['sign']==faces[i]['sign']:continue
   overlap=q.intersection(qs[j]);area=overlap.area
   if area<=1e-5:continue
   total+=area;rows.append({'plane_u_m':u,'area_m2':area,'z_interval':[overlap.bounds[1],overlap.bounds[3]],'d_interval':[overlap.bounds[0],overlap.bounds[2]],'plane_offset_m':abs(faces[i]['u']-faces[j]['u']),'triangles':[faces[i]['tri'],faces[j]['tri']],'vertices_glb':[faces[i]['vertices_glb'],faces[j]['vertices_glb']]})
summary={u:sum(x['area_m2'] for x in rows if x['plane_u_m']==u) for u in sorted({x['plane_u_m'] for x in rows})}
wing_axis=np.linalg.norm(B-A)/2-3.55/2
layout=[(-wing_axis,1.95),(-3.55,1.12),(-1.23,.50),(0,1.42),(1.23,.50),(3.55,1.12),(wing_axis,1.95)]
jamb_checks=[]
for u,w in layout:
 for side in [-1,1]:
  plane=round(u+side*w/2,4);actual=unary_union([f['shape'] for f in groups.get(plane,[])])
  for row in range(5):
   lo=9.4+row*3.51+.68;hi=9.4+row*3.51+3.51-.62;target=box(-.425,lo,.025,hi);area=actual.intersection(target).area
   jamb_checks.append({'u_m':plane,'row':row+1,'expected_m2':target.area,'covered_m2':area})
assert len(jamb_checks)==70 and max(abs(j['expected_m2']-j['covered_m2']) for j in jamb_checks)<.00002,jamb_checks
r={'scope':'Read-only raw GLB middle-front-wall limestone internal side-face overlap. No geometry changed. Opposing-normal coplanar triangles projected into wall-depth/height plane. Raster cause still needs controlled same-camera confirmation.','asset':raw.name,'sha256':hashlib.sha256(b).hexdigest(),'facing_axis_tangent_east_north':T.tolist(),'facade_outward_axis_east_north':N.tolist(),'wall_front_depth_m':.025,'wall_back_depth_m':-.425,'height_scope_m':[9.39,26.96],'plane_bucket_tolerance_m':.0001,'opposing_side_overlap_pairs':len(rows),'summed_pair_overlap_area_m2':total,'by_plane_u_m':summary,'window_jamb_checks':jamb_checks,'true_window_jamb_area_preserved_m2':sum(j['covered_m2'] for j in jamb_checks),'examples':rows[:12], 'all_contacts':[{k:v for k,v in row.items() if k!='vertices_glb'} for row in rows]}
args.output.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');assert len(rows)==0 and total==0, 'Internal opposing side faces remain';print(json.dumps({k:v for k,v in r.items() if k not in ['examples','all_contacts']},ensure_ascii=False,indent=2))
