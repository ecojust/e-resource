"""Trace recorded browser camera positions into the photographed external facade and the rendered city neighborhood."""
from pathlib import Path
import argparse,subprocess,json,runpy,sys,hashlib
import numpy as np,shapely
from embreex.rtcore_scene import EmbreeScene
from embreex.mesh_construction import TriangleMesh
p=argparse.ArgumentParser();p.add_argument('--project',type=Path,required=True);p.add_argument('--source',type=Path,required=True);p.add_argument('--work',type=Path,required=True);p.add_argument('--camera',type=Path,required=True);p.add_argument('--out',type=Path,required=True);args=p.parse_args()
root=args.project;w=args.work;w.mkdir(exist_ok=True,parents=True);sys.path.insert(0,str(root/'tools'));from candidate_placement_meshes import PlacementMeshes,read,write,sha
id='hongkou-tilanqiao-historic-front';reviewfile=root/'source/precise'/id/'footprint-review.json';r=read(reviewfile)
for f in r['frozen_bindings']:
 k=Path(f['repository_path']).name
 if not(w/k).exists():(w/k).symlink_to((args.source/k).resolve())
ctx=PlacementMeshes(root,w,r);groups=r['near_tiles'];ctx.link('baseline-far.glb',ctx.files['far.glb']);ctx.link('macro-READY.json',ctx.files['READY.json'])
parts=[];owners=[];all_group_owners=set()
for g in groups:
 ids=g['feature_local_ids'];all_group_owners.update(ids)
 ctx.link('baseline-near.glb.gz',ctx.files[Path(g['file']).name]);write(w/'context-features.json',[{'localId':i}for i in ctx.footprints]);subprocess.run(['node',ctx.decoders/'map-decode-source.mjs'],env=ctx.env,check=True,stdout=subprocess.DEVNULL)
 tri=np.fromfile(w/'baseline-near-triangles.f64').reshape(-1,3,3);tri[:,:,:2]=tri[:,:,:2]@ctx.axes.T
 near=np.linalg.norm(tri[:,:,:2].mean(1),axis=1)<140;tri=tri[near]
 distances=np.stack([shapely.distance(shapely.points(tri[:,:,:2].mean(1)),ctx.footprints[i]) for i in ids],axis=1)
 labels=np.array(ids)[distances.argmin(1)];parts.append(tri);owners.append(labels)
far=np.fromfile(w/'baseline-far-triangles.f64').reshape(-1,3,3);fids=np.fromfile(w/'baseline-far-owners.u32',np.uint32)
far[:,:,:2]=far[:,:,:2]@ctx.axes.T;keep=~np.isin(fids,list(all_group_owners));parts.append(far[keep]);owners.append(fids[keep])
occ=EmbreeScene();cm=TriangleMesh(occ,np.concatenate(parts).astype('f'));owner=np.concatenate(owners)
asset=root/'assets/models/candidates'/id;mf=read(asset/'manifest.json');raw=asset/mf['assets']['raw']['file'];t=runpy.run_path(str(root/'data/audit/postal-office-v1/independent-glb-review-helpers.py'))['load_triangles'](raw)[0]
mesh=EmbreeScene();mm=TriangleMesh(mesh,t.astype('f'))
def shoot(S,points,dirs):return S.run(np.asarray(points,dtype='f'),np.asarray(dirs,dtype='f'),output=1)
samples=[('door lower center',0,1.05),('door center',0,2.1),('door upper center',0,3.25),('eastern panel',2.45,3.5),('stone pier',-6.5,2.45),('name tablet lower',7.55,2.9),('name tablet center',7.55,4.45),('name tablet upper',7.55,6.0),('upper lintel',0,8.65)]
o=np.array([[u,-7,h]for name,u,h in samples]);v=np.tile([0.,1.,0.],(len(o),1));r0=shoot(mesh,o,v);assert (r0['primID']>=0).all();target=o+v*r0['tfar'][:,None]
eyes=read(args.camera)['actualFrozenCameras'];result=[]
for e in eyes:
 start=np.array([*ctx.to_xy(np.array([e['eye_wgs84']]))[0],e['eye_altitude_m']]);da=target-start;length=np.linalg.norm(da,axis=1);dirs=da/length[:,None];org=np.tile(start,(len(o),1));m=shoot(mesh,org,dirs);c=shoot(occ,org,dirs);rows=[]
 for j,(name,_,_)in enumerate(samples):
  city_first=c['primID'][j]>=0 and c['tfar'][j]+.03<m['tfar'][j]
  rows.append({'public_street_point':name,'model_first_hit_m':float(m['tfar'][j]),'native_first_hit_m':float(c['tfar'][j]) if c['primID'][j]>=0 else None,'native_owner_local_id':int(owner[c['primID'][j]])if c['primID'][j]>=0 else None,'first_visible':'retained city building'if city_first else 'historic facade'})
 result.append({'width':e['width'],'pitch':e['pitch'],'wgs84':e['eye_wgs84'],'altitude_m':e['eye_altitude_m'],'checks':rows})
write(args.out,{'input_camera_sha256':sha(args.camera),'raw_model_sha256':sha(raw),'source_review_sha256':sha(reviewfile),'script_sha256':sha(Path(__file__)),'method':'Actual published exterior glTF and four service-bound native detail groups, plus non-duplicated far group geometry, near tile triangle IDs assigned by nearest footprint. Rendered world camera values replayed by an untouched clone of the same MapLibre transform.','groups':[g['id']for g in groups],'views':result})
print([(v['width'],v['pitch'],sum(x['first_visible']=='historic facade'for x in v['checks']))for v in result])
