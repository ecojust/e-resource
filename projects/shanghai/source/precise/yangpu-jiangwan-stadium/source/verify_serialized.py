"""Actual serialized GLB ray checks and full/FLOAT32 material-surface equivalence."""
from pathlib import Path
import argparse,json,hashlib,struct
import numpy as np
import trimesh

ID='yangpu-jiangwan-stadium'
def load(path):
 scene=trimesh.load(path,force='scene',process=False)
 triangles=[];tags=[];digests={}
 for mesh in scene.geometry.values():
  t=np.asarray(mesh.triangles);material=mesh.visual.material.name;triangles.append(t[:, :, [0,2,1]]*np.array([1,-1,1]));tags.extend([material]*len(t));digests.setdefault(material,[]).append(t)
 def digest(t):
  v=np.array(t,dtype='<f4');v[v==0]=0;starts=np.lexsort((v[:,:,2],v[:,:,1],v[:,:,0]),axis=-1)[:,0];v=v[np.arange(len(v))[:,None],(starts[:,None]+np.arange(3))%3];rows=np.ascontiguousarray(v.reshape(-1,9)).view(np.dtype((np.void,36))).ravel();return hashlib.sha256(np.sort(rows).tobytes()).hexdigest()
 return np.concatenate(triangles),np.array(tags),{k:digest(np.concatenate(v)) for k,v in digests.items()}
def check(path,probes):
 triangles,tags,digests=load(path);a=triangles[:,0];e1=triangles[:,1]-a;e2=triangles[:,2]-a
 def first(origin,direction,max_distance=1000):
  origin=np.array(origin,float);direction=np.array(direction,float);direction/=np.linalg.norm(direction)
  h=np.cross(direction,e2);det=np.einsum('ij,ij->i',e1,h);valid=np.abs(det)>1e-10;inv=np.zeros(len(det));inv[valid]=1/det[valid];s=origin-a;u=inv*np.einsum('ij,ij->i',s,h);q=np.cross(s,e1);v=inv*np.einsum('j,ij->i',direction,q);t=inv*np.einsum('ij,ij->i',e2,q)
  idx=np.flatnonzero(valid&(u>=-1e-9)&(v>=-1e-9)&(u+v<=1+1e-9)&(t>1e-6)&(t<max_distance))
  if not len(idx):return None
  i=idx[np.argmin(t[idx])];return {'distance_m':float(t[i]),'material':str(tags[i]),'point':(origin+direction*t[i]).tolist()}
 rows=[]
 # Every authored window and doorway is tested on the actual whole scene.
 chosen=probes
 for p in chosen:
  normal=np.array(p['normal']);offset=8.0 if p['kind']=='portal-bounded' else .35;origin=np.array(p['point'])+normal*offset;hit=first(origin,-normal,22)
  if p['kind']=='portal-bounded':passed=hit is not None and 13.35<hit['distance_m']<13.9
  else:passed=hit is not None and hit['material']==p['material'] and abs(hit['distance_m']-offset-p['depth'])<1e-4
  rows.append({'label':p['label'],'kind':p['kind'],'origin':origin.tolist(),'direction':(-normal).tolist(),'expected_depth_m':p['depth'],'origin_offset_m':offset,'scope':'Local opening recess depth; external distant visibility is separately reviewed in images','first_hit':hit,'passed':passed})
 ang=np.radians(26.56537);c,s=np.cos(ang),np.sin(ang)
 def enu(q):x,y,z=q;return [c*x-s*y,s*x+c*y,z]
 # Real open inner field, wide separated probes, and end-axis aperture at
 # standing/vehicle heights. Source-independent coordinate choices avoid merely
 # proving that a declared feature lies in its own component's empty bbox.
 for u in [-45,0,45]:
  for v in [-95,-40,30,100]:
   origin=enu([u,v,45]);hit=first(origin,[0,0,-1],44.9);rows.append({'label':f'field void {u}/{v}','origin':origin,'direction':[0,0,-1],'first_hit':hit,'passed':hit is None})
 for side,cx,start,end in [('south',6.8,-178,-135),('north',1.45,181,140)]:
  for shoulder in [-.38,0,.38]:
   for z in [1.825,3.,5.]:
    for reverse in [False,True]:
     a0,b0=(start,end) if not reverse else (end,start);origin=enu([cx+shoulder,a0,z]);direction=np.array(enu([0,b0-a0,0]));hit=first(origin,direction,abs(b0-a0));rows.append({'label':f'{side} true central passage {shoulder}/{z}/{reverse}','origin':origin,'direction':(direction/np.linalg.norm(direction)).tolist(),'first_hit':hit,'passed':hit is None})
 # Connected raised terrace: local downward rays start below the canopy,
 # require the continuous4.50m deck, and separately verify its high pier links.
 for u in [-66.5,-67.5]:
  for v in [-15,-8,0,8,15]:
   origin=enu([u,v,4.70]);hit=first(origin,[0,0,-1],.50)
   rows.append({'label':f'west continuous front terrace {u}/{v}','origin':origin,'direction':[0,0,-1],'first_hit':hit,'expected_top_z_m':4.50,'passed':hit is not None and abs(hit['point'][2]-4.50)<1e-4})
 for v in [-6.195,3.505]:
  origin=enu([-92.825,v,14.0]);hit=first(origin,[0,0,-1],.50)
  rows.append({'label':f'west upper pier canopy link {v}','origin':origin,'direction':[0,0,-1],'first_hit':hit,'expected_top_z_m':13.75,'passed':hit is not None and abs(hit['point'][2]-13.75)<1e-4})
 # Ground-level positive controls on the two stand bodies and the west gate
 # masonry, to ensure that a missing whole model would not pass void checks.
 for u,v,z in [(-75,-65,30),(83,75,30),(-90,12,30)]:
  hit=first(enu([u,v,z]),[0,0,-1],29.9);rows.append({'label':f'solid positive {u}/{v}','first_hit':hit,'passed':hit is not None})
 return {'file':path.name,'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'triangles':len(triangles),'count':len(rows),'passed':all(r['passed'] for r in rows),'failures':[r for r in rows if not r['passed']],'records':rows,'oriented_float32_surface_digests_by_material':digests}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--asset',type=Path,required=True);p.add_argument('--probes',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();r=check(a.asset,json.loads(a.probes.read_text()));a.out.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:r[k] for k in ['file','triangles','count','passed','failures']},ensure_ascii=False));raise SystemExit(0 if r['passed'] else 1)
