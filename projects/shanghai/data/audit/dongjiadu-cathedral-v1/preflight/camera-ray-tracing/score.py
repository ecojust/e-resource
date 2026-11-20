import hashlib,json,math,runpy,sys,gzip
from pathlib import Path
import numpy as np
import shapely
from shapely.ops import transform
from shapely.geometry import shape
from embreex.rtcore_scene import EmbreeScene
from embreex.mesh_construction import TriangleMesh
from PIL import Image
project=Path('/workspace/e-resource/projects/shanghai');w=Path('/tmp/dong64/camera');ident='huangpu-dongjiadu-cathedral'
row=json.loads(Path('/tmp/shanghai-view-updates/gate300/stage64/projects/shanghai/data/candidate-city-integrations.json').read_bytes())['models'][-1];lng=row['lng'];lat=row['lat'];cs,sn=np.cos(np.deg2rad(row['heading'])),np.sin(np.deg2rad(row['heading']));rx=6371008.8*np.cos(np.deg2rad(lat));rxdeg=rx*np.pi/180;ln=np.arcsinh(np.tan(np.deg2rad(lat)))
def en(x,y,z=None):return (np.asarray(x)-lng)*rxdeg,rx*(np.arcsinh(np.tan(np.deg2rad(y)))-ln)
def model_en(a):
 v=a.copy();v[...,0]=a[...,0]*cs+a[...,1]*sn;v[...,1]=-a[...,0]*sn+a[...,1]*cs;return v
def en_model(a):
 v=a.copy();v[...,0]=a[...,0]*cs-a[...,1]*sn;v[...,1]=a[...,0]*sn+a[...,1]*cs;return v
def scene(tri):
 s=EmbreeScene();m=TriangleMesh(s,np.asarray(tri,dtype=np.float32));return s,m
def cast(s,o,d):
 d=np.ascontiguousarray(d,dtype=np.float32);o=np.broadcast_to(o,d.shape).copy().astype(np.float32);return s.run(o,d,output=1)
asset=project/Path(row['candidate_manifest']).parent/Path(json.loads((project/row['candidate_manifest']).read_bytes())['assets']['raw']['file']);tri,mt,mnames,_=runpy.run_path(str(project/'data/audit/postal-office-v1/independent-glb-review-helpers.py'))['load_triangles'](asset)
model=model_en(tri);ms,modelmesh=scene(model);review=json.loads((project/f'source/precise/{ident}/footprint-review.json').read_bytes());group=review['near_tiles'][0];ids=group['feature_local_ids'];source={b['localId']:transform(en,shape(b['geometry'])) for b in json.load(gzip.open('/tmp/dong64/source-macro/feature-table.json.gz'))['features']if b['localId'] in ids}
near=np.fromfile(w/'baseline-near-triangles.f64',np.float64).reshape(-1,3,3);far=np.fromfile(w/'baseline-far-triangles.f64',np.float64).reshape(-1,3,3)
farids=np.fromfile(w/'baseline-far-owners.u32',np.uint32);points=shapely.points(near.mean(1)[:,:2]);nearids=np.asarray(ids)[np.column_stack([shapely.distance(points,source[i]) for i in ids]).argmin(1)]
# The per-owner production mask is evaluated at the hit position. This retains native roofs crossing the perimeter.
mask=transform(en,shape(row['replacement_geometry']))
far_keep=~np.isin(farids,ids);city=np.concatenate((near,far[far_keep]));owners=np.concatenate((nearids,farids[far_keep]));ns,citymesh=scene(city)
def cast_city(o,dirs):
 hits=cast(ns,o,dirs);o=np.broadcast_to(o,dirs.shape); pending=np.arange(len(dirs))
 for _ in range(40):
  ids0=hits['primID'][pending];m=(ids0>=0)&(owners[np.maximum(ids0,0)]==1831);idx=pending[m];xyz=o[idx]+dirs[idx]*hits['tfar'][idx,None];idx=idx[shapely.contains_xy(mask,xyz[:,0],xyz[:,1])]
  if not len(idx):return hits
  advance=hits['tfar'][idx]+.012;rest=cast(ns,o[idx]+advance[:,None]*dirs[idx],dirs[idx]);hits['tfar'][idx]=advance+rest['tfar'];hits['primID'][idx]=rest['primID'];pending=idx
 raise ValueError('excessive masked layers')
xx,zz=np.meshgrid(np.arange(-15.3,15.3,.25),np.arange(.35,25.6,.29));local=np.stack((xx.ravel(),np.full(xx.size,-38),zz.ravel()),axis=1);orig=model_en(local);dirs=np.broadcast_to(model_en(np.array([0.,1.,0.])),orig.shape)
initial=cast(ms,orig,dirs);valid=initial['primID']>=0;targets=(orig+dirs*initial['tfar'][:,None])[valid];localtargets=en_model(targets);front=localtargets[:,1]<3.5;targets=targets[front];localtargets=localtargets[front];means=localtargets[:,0];center=np.abs(means)<3;arcades=(np.abs(means)>7)&(np.abs(means)<12.5);height=localtargets[:,2];visible=[]
def eye(c,w,h):
 pitch,bear=np.deg2rad([c['pitch'],c['bearing']]);f=h*.5/math.tan(math.radians(36.87)/2);dist=f*math.cos(math.radians(lat))*40075016.68/(512*2**c['zoom']);return np.array([*en(*c['center']),c['elevation']])-dist*np.array([math.sin(bear)*math.sin(pitch),math.cos(bear)*math.sin(pitch),-math.cos(pitch)])
def measure(c,w,h):
 o=eye(c,w,h);delta=targets-o;dist=np.linalg.norm(delta,axis=1);dirs=delta/dist[:,None];hits=cast_city(o,dirs);own=cast(ms,o,dirs)
 enough=hits['tfar']+.075>=dist;selfvis=own['tfar']+.085>=dist
 # Surfaces hidden by their own cornice are excluded from the externally visible denominator.
 def ratio(region):
  s=region&selfvis;return round(float((enough&s).sum())/max(1,s.sum()),4)
 considered=front.size;blocks=owners[hits['primID'][~enough&selfvis]] if np.any(~enough&selfvis) else []
 return {'center':ratio(center),'arcade':ratio(arcades),'all':ratio(np.ones(len(targets),bool)),'lower_center':ratio(center&(height<4.5)),'selfVisibleTargets':int(selfvis.sum()),'clearTargets':int((enough&selfvis).sum()),'originENU':o.tolist(),'topBlockingIDs':{str(int(i)):int(n)for i,n in zip(*np.unique(blocks,return_counts=True))}}
opts=[s for s in json.loads(Path('/tmp/dong64/camera/options.json').read_bytes())if s['id']==ident]
if __name__=='__main__':
 for s in opts:
  c=s['cam'];visible.append({'w':s['w'],'h':s['h'],'bearing':c['bearing'],'pitch':c['pitch'],**measure(c,s['w'],s['h'])})
 (w/'actual-front-measurements.json').write_text(json.dumps(visible,indent=2))
 print('native environment',len(city),'real model surfaces',len(tri),'arch samples',len(targets),flush=True)
 for v in visible:
  if v['bearing']==-9 and v['pitch']==65:print('Current',v['w'],v,flush=True)
 bypose={}
 for r in visible:
  k=(r['bearing'],r['pitch']);bypose.setdefault(k,[]).append(r)
 scores=[]
 for k,rows in bypose.items():
  allmin=min(r['all'] for r in rows);centermin=min(r['center']for r in rows);arcmin=min(r['arcade']for r in rows);lowmin=min(r['lower_center']for r in rows)
  scores.append((round(min(centermin,arcmin)*.43+centermin*.30+allmin*.19+lowmin*.08,4),k,allmin,centermin,arcmin,lowmin))
 print('Best',sorted(scores,reverse=True)[:12],flush=True)
