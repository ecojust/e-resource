from pathlib import Path
import sys,json,numpy as np,shapely,math,runpy,subprocess
from embreex.rtcore_scene import EmbreeScene
from embreex.mesh_construction import TriangleMesh
from shapely.geometry import shape
project=Path('/workspace/e-resource/projects/shanghai');d=Path('/tmp/caldbeck91');sys.path.insert(0,str(project/'tools'))
from candidate_placement_meshes import PlacementMeshes,read,write
audit=project/'data/audit/caldbeck-macgregor-v1';r=read(project/'source/precise/huangpu-caldbeck-macgregor-building/footprint-review.json');contract=read(audit/'final-placement-contract.json');wd=d/'camera';wd.mkdir(exist_ok=True)
for receipt in r['frozen_bindings']:
 name=Path(receipt['repository_path']).name
 if not(wd/name).exists():(wd/name).symlink_to((d/'source-macro'/name).resolve())
ctx=PlacementMeshes(project,wd,r);ids=r['near_tiles'][0]['feature_local_ids'];group=r['near_tiles'][0];ctx.link('baseline-far.glb',ctx.files['far.glb']);ctx.link('baseline-near.glb.gz',ctx.files[Path(group['file']).name]);ctx.link('macro-READY.json',ctx.files['READY.json'])
wanted=list(ctx.footprints);write(wd/'context-features.json',[{'localId':i}for i in wanted]);subprocess.run(['node',ctx.decoders/'map-decode-source.mjs'],env=ctx.env,check=True,stdout=subprocess.DEVNULL)
raw=next((d/'assets').glob('*-raw.glb'));model=runpy.run_path(str(project/'data/audit/postal-office-v1/independent-glb-review-helpers.py'))['load_triangles'](raw)[0]
def scene(tri):s=EmbreeScene();m=TriangleMesh(s,tri.astype('f'));return s,m
ns0=np.fromfile(wd/'baseline-near-triangles.f64').reshape(-1,3,3);ns0[:,:,:2]=ns0[:,:,:2]@ctx.axes.T
fs0=np.fromfile(wd/'baseline-far-triangles.f64').reshape(-1,3,3);fs0[:,:,:2]=fs0[:,:,:2]@ctx.axes.T;fids=np.fromfile(wd/'baseline-far-owners.u32',np.uint32)
ip=shapely.points(ns0.mean(1)[:,:2]);ni=np.array(ids)[np.stack([shapely.distance(ip,ctx.footprints[i])for i in ids],axis=1).argmin(1)]
near=ns0[ni!=1960];far=fs0[~np.isin(fids,ids)];allcity=np.concatenate([near,far]);city,cm=scene(allcity);modelscene,mm=scene(model)
# The residue of owner 1960 stays behind the historical elevation. All foreground
# roofs and western/eastern buildings retain native geometry in this comparison.
def shoot(S,points,directions):
 dirs=np.ascontiguousarray(directions,dtype='f');org=np.broadcast_to(points,dirs.shape).astype('f').copy()
 return S.run(org,dirs,output=1)
x,z=np.meshgrid(np.arange(-14.9,15.5,.27),np.arange(.4,11,.27));o=np.column_stack([x.ravel(),np.full(x.size,-16),z.ravel()]);dv=np.tile([0.,1.,0.],(len(o),1));hit=shoot(modelscene,o,dv);targets=(o+dv*hit['tfar'][:,None])[hit['primID']>=0];targets=targets[targets[:,1]<2];mask=(targets[:,2]<3.6)&(np.abs(targets[:,0])<2.1)
opts=read(wd/'poses.json');out=[]
for opt in opts:
 c=opt['camera'];h=opt['height'];pitch,bear=np.deg2rad([c['pitch'],c['bearing']-contract['heading']]);fac=h*.5/math.tan(math.radians(36.87)/2);dist=fac*math.cos(math.radians(contract['lat']))*40075016.68/(512*2**c['zoom']);center=ctx.to_xy(np.array([c['center']]))[0];eye=np.array([*center,c['elevation']])-dist*np.array([np.sin(bear)*np.sin(pitch),np.cos(bear)*np.sin(pitch),-np.cos(pitch)])
 delta=targets-eye;length=np.linalg.norm(delta,axis=1);dirs=delta/length[:,None];own=shoot(modelscene,eye,dirs);f=shoot(city,eye,dirs);selfvis=own['tfar']+.06>=length;vis=selfvis&(f['tfar']+.06>=length)
 out.append({'w':opt['width'],'pitch':c['pitch'],'bearing':c['bearing'],'samples':len(targets),'whole':round(vis.sum()/selfvis.sum(),5),'centralGround':round((vis&mask).sum()/(selfvis&mask).sum(),5)})
write(wd/'ratio.json',out);print(out)
