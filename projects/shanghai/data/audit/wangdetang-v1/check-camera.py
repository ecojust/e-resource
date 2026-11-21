import argparse, hashlib, sys, json, math, subprocess, runpy, gzip
from pathlib import Path
import numpy as np
from embreex.rtcore_scene import EmbreeScene
from embreex.mesh_construction import TriangleMesh
aud=Path(__file__).resolve().parent
project=aud.parents[2]
parser=argparse.ArgumentParser(description='Check the actual entrance, south fanlight and upper gables against native city meshes from both default camera sizes.')
parser.add_argument('--work',type=Path,required=True)
parser.add_argument('--out',type=Path,required=True)
parser.add_argument('--manifest',type=Path,default=project/'assets/models/candidates/jingan-wangdetang-augustinian-office/manifest.json')
parser.add_argument('--contract',type=Path,default=aud/'final-placement-contract.json')
args=parser.parse_args()
d=args.work;d.mkdir(exist_ok=True,parents=True)
subprocess.run(['node',aud/'camera-poses.mjs',d/'poses.json',args.contract],check=True)
sys.path.insert(0,str(project/'tools'))
from candidate_placement_meshes import PlacementMeshes,read,write
import shapely
from shapely.geometry import shape
bound=read(project/'source/precise/jingan-wangdetang-augustinian-office/footprint-review.json');c=read(args.contract);w=d;ctx=PlacementMeshes(project,w,bound)
ctx.link('baseline-far.glb',ctx.files['far.glb']);ctx.link('macro-READY.json',ctx.files['READY.json'])
write(w/'context-features.json',[{'localId':x['localId']}for x in json.loads(gzip.decompress(ctx.files['feature-table.json.gz'].read_bytes()))['features']])
# The original rear 31.25-metre mass remains. Only intersections of the owner's
# surfaces inside the exact footprint mask are removed. The generic seam walls
# close the source at their recorded roof elevation and are tested as obstacles.
clip=shapely.transform(shape(c['replacement_geometry']),ctx.to_xy)
g=next(row for row in bound['near_tiles'] if 786 in row['feature_local_ids']);gids=g['feature_local_ids']
decoded=ctx.decode_group(g,786)
old=EmbreeScene();oldgeo=TriangleMesh(old,decoded['near'][0].astype('f'))
sou=[decoded['near'][1]]
for line in shape(c['source_section_caps']['geometry']).geoms:
    pts=ctx.to_xy(np.asarray(line.coords));height=c['source_section_caps']['roof_m']
    for a,b in zip(pts,pts[1:]):
        x,y=a;xx,yy=b
        sou.append(np.array([[[x,y,0],[xx,yy,0],[xx,yy,height]],[[x,y,0],[xx,yy,height],[x,y,height]]]))
write(w/'context-features.json',[{'localId':x['localId']}for x in json.loads(gzip.decompress(ctx.files['feature-table.json.gz'].read_bytes()))['features']])
subprocess.run(['node',ctx.decoders/'map-decode-source.mjs'],env=ctx.env,check=True,stdout=subprocess.DEVNULL)
fs=np.fromfile(w/'baseline-far-triangles.f64').reshape(-1,3,3);fs[:,:,:2]=fs[:,:,:2]@ctx.axes.T
fid=np.fromfile(w/'baseline-far-owners.u32',np.uint32);sou.append(fs[~np.isin(fid,gids)]);city=EmbreeScene();citymesh=TriangleMesh(city,np.concatenate(sou).astype('f'))
modeldoc=read(args.manifest)
raw=args.manifest.parent/modeldoc['assets']['raw']['file']
tri=runpy.run_path(str(project/'data/audit/postal-office-v1/independent-glb-review-helpers.py'))['load_triangles'](raw)[0]
model=EmbreeScene();m=TriangleMesh(model,tri.astype('f'));targets=tri.mean(1)[::7];sx,sy,sz=12.5463/20.768,.90,.89;coords=targets/np.array([sx,sy,sz]);parts={'tall_portal':(abs(coords[:,0])<1.88)&(coords[:,1]<.10)&(coords[:,2]>1.43)&(coords[:,2]<5.30),'two_gables':(coords[:,2]>11.70),'south_fanlight':(coords[:,0]>10.07)&(coords[:,1]>.51)&(coords[:,1]<3.17)&(coords[:,2]>1.2)&(coords[:,2]<4.84)}
out=[]
for op in read(d/'poses.json'):
 cam=op['camera'];h=op['height'];pitch,bear=np.radians([cam['pitch'],cam['bearing']-c['heading']]);dist=h*.5/math.tan(math.radians(36.87)*.5)*math.cos(math.radians(c['lat']))*40075016.68/(512*2**cam['zoom']);center=ctx.to_xy(np.array([cam['center']]))[0];eye=np.array([*center,cam['elevation']])-dist*np.array([np.sin(bear)*np.sin(pitch),np.cos(bear)*np.sin(pitch),-np.cos(pitch)])
 delta=targets-eye;ll=np.linalg.norm(delta,axis=1);dirs=(delta/ll[:,None]).astype('f');org=np.repeat(eye[None,:],len(ll),axis=0).astype('f')
 def shoot(scene):return scene.run(org,dirs,query='DISTANCE').astype(float)
 selfd=shoot(model);r=shoot(city)
 # Follow the next original intersection whenever the preceding one lies inside its clipped area.
 other=np.full(len(org),np.inf);indices=np.arange(len(org));travel=np.zeros(len(org));orig=org.copy()
 for step in range(10):
  if not len(indices):break
  hit=old.run(orig,dirs[indices],query='DISTANCE').astype(float)
  feasible=(hit>=0)&(hit<1e9)
  indices=indices[feasible];orig=orig[feasible];hit=hit[feasible]
  if not len(indices):break
  loc=orig+dirs[indices]*hit[:,None];travel[indices]+=hit
  keep=~shapely.contains_xy(clip,loc[:,0],loc[:,1])
  other[indices[keep]]=travel[indices[keep]]
  indices=indices[~keep];orig=(loc[~keep]+dirs[indices]*.012).astype('f');travel[indices]+=.012
 r=np.minimum(np.where((r>=0)&(r<1e9),r,np.inf),other)
 selfvis=(selfd+.06>=ll)|(selfd<0);vis=selfvis&((r+.06>=ll)|(r<0))
 out.append(dict(viewport=[op['width'],op['height']],camera=cam,samples=len(targets),all_self_visible=int(selfvis.sum()),all_clear=int(vis.sum()),parts={k:[int((v&vis).sum()),int((v&selfvis).sum())]for k,v in parts.items()}))
write(args.out,dict(checker_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),poses_sha256=hashlib.sha256((aud/'camera-poses.mjs').read_bytes()).hexdigest(),sampled_from=modeldoc['assets']['raw']['sha256'],basis='Frozen near/far city triangles; the original rear 786, its cap and all surrounding buildings stay in the ray scene; only the accepted owner mask removes intersections.',views=out));print([(v['viewport'][0],v['camera']['pitch'],v['all_clear'],v['all_self_visible'],v['parts'])for v in out])
