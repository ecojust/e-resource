import argparse, hashlib, sys, json, math, subprocess, runpy, gzip
from pathlib import Path
import numpy as np
from embreex.rtcore_scene import EmbreeScene
from embreex.mesh_construction import TriangleMesh
aud=Path(__file__).resolve().parent
project=aud.parents[2]
parser=argparse.ArgumentParser(description='Check the actual gate triangles against native city meshes from both default camera sizes.')
parser.add_argument('--work',type=Path,required=True)
parser.add_argument('--out',type=Path,required=True)
args=parser.parse_args()
d=args.work;d.mkdir(exist_ok=True,parents=True)
subprocess.run(['node',aud/'camera-poses.mjs',d/'poses.json'],check=True)
sys.path.insert(0,str(project/'tools'))
from candidate_placement_meshes import PlacementMeshes,read,write
bound=read(project/'source/precise/xuhui-zhu-mintang-residence/footprint-review.json');c=read(aud/'final-placement-contract.json');w=d;ctx=PlacementMeshes(project,w,bound)
ctx.link('baseline-far.glb',ctx.files['far.glb']);ctx.link('macro-READY.json',ctx.files['READY.json'])
write(w/'context-features.json',[{'localId':x['localId']}for x in json.loads(gzip.decompress(ctx.files['feature-table.json.gz'].read_bytes()))['features']])
gids=[];sou=[]
for g in bound['near_tiles']:
 gids+=g['feature_local_ids'];ctx.link('baseline-near.glb.gz',ctx.files[Path(g['file']).name]);subprocess.run(['node',ctx.decoders/'map-decode-source.mjs'],env=ctx.env,check=True,stdout=subprocess.DEVNULL);t=np.fromfile(w/'baseline-near-triangles.f64').reshape(-1,3,3);t[:,:,:2]=t[:,:,:2]@ctx.axes.T;sou.append(t)
fs=np.fromfile(w/'baseline-far-triangles.f64').reshape(-1,3,3);fs[:,:,:2]=fs[:,:,:2]@ctx.axes.T
fid=np.fromfile(w/'baseline-far-owners.u32',np.uint32);sou.append(fs[~np.isin(fid,gids)]);city=EmbreeScene();citymesh=TriangleMesh(city,np.concatenate(sou).astype('f'))
modeldoc=read(project/'assets/models/candidates/xuhui-zhu-mintang-residence/manifest.json')
raw=project/'assets/models/candidates/xuhui-zhu-mintang-residence'/modeldoc['assets']['raw']['file']
tri=runpy.run_path(str(project/'data/audit/postal-office-v1/independent-glb-review-helpers.py'))['load_triangles'](raw)[0]
model=EmbreeScene();m=TriangleMesh(model,tri.astype('f'));targets=tri.mean(1)[::7];parts={'four_door_fields':(abs(targets[:,0])<1.6)&(targets[:,2]>.16),'151_number_plate':(abs(targets[:,0]+1.92)<.16)&(abs(targets[:,2]-2.58)<.15)&(targets[:,1]<-.34),'paired_lions':(abs(abs(targets[:,0])-3.48)<.46)&(targets[:,2]>.70)}
out=[]
for op in read(d/'poses.json'):
 cam=op['camera'];h=op['height'];pitch,bear=np.radians([cam['pitch'],cam['bearing']-c['heading']]);dist=h*.5/math.tan(math.radians(36.87)*.5)*math.cos(math.radians(c['lat']))*40075016.68/(512*2**cam['zoom']);center=ctx.to_xy(np.array([cam['center']]))[0];eye=np.array([*center,cam['elevation']])-dist*np.array([np.sin(bear)*np.sin(pitch),np.cos(bear)*np.sin(pitch),-np.cos(pitch)])
 delta=targets-eye;ll=np.linalg.norm(delta,axis=1);dirs=(delta/ll[:,None]).astype('f');org=np.repeat(eye[None,:],len(ll),axis=0).astype('f')
 def shoot(scene):return scene.run(org,dirs,query='DISTANCE').astype(float)
 selfd=shoot(model);r=shoot(city);selfvis=(selfd+.06>=ll)|(selfd<0);vis=selfvis&((r+.06>=ll)|(r<0))
 out.append(dict(viewport=[op['width'],op['height']],camera=cam,samples=len(targets),all_self_visible=int(selfvis.sum()),all_clear=int(vis.sum()),parts={k:[int((v&vis).sum()),int((v&selfvis).sum())]for k,v in parts.items()}))
write(args.out,dict(checker_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),poses_sha256=hashlib.sha256((aud/'camera-poses.mjs').read_bytes()).hexdigest(),sampled_from=modeldoc['assets']['raw']['sha256'],basis='Frozen near/far city triangles; number plate, four door fields and guardian centroids visible on delivered geometry.',views=out));print([(v['viewport'][0],v['camera']['pitch'],v['all_clear'],v['all_self_visible'],v['parts'])for v in out])
