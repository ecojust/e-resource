"""Measure actual source-surface separations and the city's two signed Holy Trinity meshes in the school's own frame."""
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.request import urlopen
import os,subprocess,sys,runpy,json,hashlib,math,shutil
import numpy as np,shapely
w=Path(__file__).resolve().parent;p=Path('/workspace/e-resource/projects/shanghai');read=lambda f:json.loads(f.read_bytes());r=read(w/'original-review.json');sha=lambda b:hashlib.sha256(b).hexdigest();sys.path.insert(0,str(p/'tools'))
from candidate_placement_meshes import PlacementMeshes
grouped=runpy.run_path(str(p/'data/audit/metropole-hotel-v1/verify-placement.py'))['grouped_sources']
wanted={1810,587,616}|{v['id']for v in r['all_nearby']}
def projected(a):
 # Horizontal faces, vertical faces and projected points each retain their actual geometry.
 return shapely.convex_hull(shapely.polygons(a[:,:,:2]))
def pair2(a,b):
 tree=shapely.STRtree(projected(a));bb=projected(b);ii,dist=tree.query_nearest(bb,return_distance=True,all_matches=False);k=np.argmin(dist);return float(dist[k]),int(ii[1,k]),int(ii[0,k]),tree,bb
def dot(a,b):return np.einsum('...i,...i->...',a,b)
def near_pairs(a,b):
 """Exact disjoint-triangle distance from the 6 vertex/face and 9 edge/edge combinations."""
 n=len(a);res=np.full(n,np.inf);best_a=np.zeros((n,3));best_b=best_a.copy()
 def record(pa,pb,allow):
  rr=dot(pa-pb,pa-pb);ok=allow&(rr<res);res[ok]=rr[ok];best_a[ok]=pa[ok];best_b[ok]=pb[ok]
 for rev in (False,True):
  ar,br=(b,a)if rev else(a,b);p0=br[:,0];u=br[:,1]-p0;v=br[:,2]-p0;normal=np.cross(u,v);nn=dot(normal,normal)
  for k in range(3):
   pp=ar[:,k];pn=dot(pp-p0,normal)/np.maximum(nn,1e-40);q=pp-pn[:,None]*normal
   t=q-p0;alpha=dot(np.cross(t,v),normal)/np.maximum(nn,1e-40);beta=dot(np.cross(u,t),normal)/np.maximum(nn,1e-40)
   allow=(nn>1e-22)&(alpha>=-1e-9)&(beta>=-1e-9)&(alpha+beta<=1.+1e-9);record(q,pp,allow) if rev else record(pp,q,allow)
 for i in range(3):
  p1=a[:,i];u=a[:,(i+1)%3]-p1;uu=dot(u,u)
  for k in range(3):
   p2=b[:,k];v=b[:,(k+1)%3]-p2;vv=dot(v,v);q=p1-p2;uv=dot(u,v);uq=dot(u,q);vq=dot(v,q);den=uu*vv-uv*uv
   # The unconstrained line solution, both segment endpoints against the other segment.
   tu=(uv*vq-vv*uq)/np.maximum(den,1e-40);tv=(uu*vq-uv*uq)/np.maximum(den,1e-40);good=(den>1e-20)&(tu>=0)&(tu<=1)&(tv>=0)&(tv<=1)
   record(p1+tu[:,None]*u,p2+tv[:,None]*v,good)
   for e in (0,1):
    item=p1+e*u;fac=np.clip(dot(item-p2,v)/np.maximum(vv,1e-40),0,1);record(item,p2+fac[:,None]*v,True)
    item=p2+e*v;fac=np.clip(dot(item-p1,u)/np.maximum(uu,1e-40),0,1);record(p1+fac[:,None]*u,item,True)
 return np.sqrt(res),best_a,best_b
def surface(a,b):
 horizontal,aa,bb,tree,bproj=pair2(a,b)
 # The building projections are disjoint, eliminating edge-through-face intersections.
 assert horizontal>0.02
 first,p1,p2=near_pairs(a[aa:aa+1],b[bb:bb+1]);curr=float(first[0]);hit=[aa,bb,p1[0].tolist(),p2[0].tolist()];candidates=0
 for start in range(0,len(b),384):
  pairs=tree.query(bproj[start:start+384],predicate='dwithin',distance=curr+1.e-7)
  ib,ia=pairs[0]+start,pairs[1]
  for j in range(0,len(ia),1400):
   x=ia[j:j+1400];y=ib[j:j+1400];A=a[x];B=b[y]
   bound=np.maximum(np.maximum(A.min(1)-B.max(1),B.min(1)-A.max(1)),0.);use=dot(bound,bound)<=curr*curr+1.e-6
   if not use.any():continue
   A=A[use];B=B[use];x=x[use];y=y[use];dist,pa,pb=near_pairs(A,B);idx=dist.argmin();candidates+=len(x)
   if dist[idx]<curr:
    curr=float(dist[idx]);hit=[int(x[idx]),int(y[idx]),pa[idx].tolist(),pb[idx].tolist()]
 return dict(horizontal_closest_projected_faces_m=horizontal,closest_3d_face_distance_m=curr,school_triangle=hit[0],other_triangle=hit[1],school_xyz=hit[2],other_xyz=hit[3],exact_pairs_after_aabb_pruning=candidates)
# Prove the point-face / edge-edge routine on known separated parallel walls and perpendicular edges.
aa=np.array([[[0,0,0],[0,2,0],[0,0,2]]],float);bb=np.array([[[3,.2,.2],[4,.3,0],[4,0,.3]]],float);assert abs(near_pairs(aa,bb)[0][0]-3)<1e-9
parts={'near':{},'far':{}};ties={};records={};anchors=r['author_frame']['anchor'];folder=max([Path('/tmp'),Path('/dev/shm')],key=lambda f:shutil.disk_usage(f).free)
with TemporaryDirectory(dir=folder,prefix='school281-baseline-')as td:
 t=Path(td)
 for f in r['frozen_bindings']:
  n=Path(f['repository_path']).name;(t/n).symlink_to((w/'inputs'/n).resolve())
 site=PlacementMeshes(p,t,r)
 for g in r['near_tiles']:
  for level,tr,owners,unc in grouped(site,g):
   for i in wanted.intersection(g['feature_local_ids']):
    mine=tr[owners==i];assert len(mine)>0
    parts[level][i]=mine.copy()
    if level=='near':ties[i]=int(unc[owners==i].sum())
   for f in t.glob('baseline-'+level+'-triangles.f64'):f.unlink()
 for level,v in parts.items():
  src=v[1810];out={}
  for i in wanted-{1810}:
   ds,ix,jx,tree,projected_b=pair2(src,v[i]);out[str(i)]=dict(distance_m=ds,closest_projected_face_indices=[ix,jx],other_actual_triangles=len(v[i]))
   del tree,projected_b
  records[level]=dict(source_triangles=len(src),source_xyz_bounds=[src.min((0,1)).tolist(),src.max((0,1)).tolist()],source_faces_sha256=sha(src.astype('<f8').tobytes()),nearest_projected_faces_by_original_owner=out,previous_church_meshes={})
 for obj in read(w/'church-contracts.json'):
  near_id=obj['owner']['feature_local_id'];files={};hd={}
  for level,field,role in [('near','model','web'),('far','lod_model','lod')]:
   pn=obj[field]
   with urlopen(r['source_endpoint']+pn,timeout=45)as resp:data=resp.read()
   assert sha(data)==obj['model_geometry_sha256'][role]
   opened=t/f'{role}.glb';opened.write_bytes(data);files[level]=opened;hd[level]=sha(data)
  # Decoder uses filenames passed through a 'delivered' directory with a supplied manifest ID.
  js=(p/'data/audit/postal-office-v1/map-decode-delivered.mjs').read_text()
  assert js.count("id='hongkou-general-post-office'")==1;js=js.replace("id='hongkou-general-post-office'","id='school-peer'")
  helper=t/'decode-peer.mjs';helper.write_text(js)
  subprocess.run(['node',helper,t,'web,lod'],env=site.env,check=True,stdout=subprocess.DEVNULL)
  merc_ratio=math.cos(math.radians(anchors['lat']))/math.cos(math.radians(obj['lat']));ax=site.to_xy(np.array([[obj['lng'],obj['lat']]]))[0];h=math.radians(obj['heading']);axes=np.array([[math.cos(h),-math.sin(h)],[math.sin(h),math.cos(h)]])
  for decoded in read(t/'delivered-decode.json'):
   level='near'if decoded['variant']=='web'else'far';glob=np.fromfile(decoded['triangle_file'],np.float64).reshape(-1,3,3)
   local=glob[:,:,[0,2,1]].copy();local[:,:,1]*=-1
   local[:,:,:2]=(local[:,:,:2]@axes@site.axes.T)*obj['scale']*merc_ratio+ax;local[:,:,2]=local[:,:,2]*obj['scale']+obj.get('altitude',0)
   merged=surface(parts[level][1810],local)
   records[level]['previous_church_meshes'][obj['id']]=dict(owner=near_id,triangles=len(local),actual_sha256=hd[level],**merged)
   Path(decoded['triangle_file']).unlink();print(obj['id'],level,len(local),merged['closest_3d_face_distance_m'],flush=True)
out=dict(passed=True,scope='Existing city before the school model. All actual faces use the source-ring school frame. No facade mask was supplied or written.',source_station=r['source_endpoint'],model_id=r['model_id'],source_boundary_original_review_sha256=sha((w/'original-review.json').read_bytes()),map_source_owners=sorted(wanted),near_centroid_ties_within035_m=ties,variants=records)
(w/'real-face-distances.json').write_text(json.dumps(out,indent=2)+'\n')
