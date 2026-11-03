"""Checks closed author components and actual FLOAT32 triangles; no survey claim."""
from pathlib import Path
import argparse,json,hashlib
import numpy as np
from build_model import build,ID

def check(lod=False):
 b,meta,features,probes=build(lod);fails=[];volume=0;minarea=1e99;groups={}
 for part in b.parts:
  v=np.asarray(part['vertices'],np.float32).astype(float);f=np.asarray(part['triangles'],int)
  ee=np.concatenate([f[:,[0,1]],f[:,[1,2]],f[:,[2,0]]]);ss=np.sort(ee,axis=1);unique,index,counts=np.unique(ss,axis=0,return_inverse=True,return_counts=True)
  signs=np.where(ee[:,0]<ee[:,1],1,-1);winding=np.bincount(index,weights=signs)
  groups.setdefault(part['material'],[]).append((v[:,[0,2,1]]*np.array([1,1,-1]))[f])
  triangles=v[f];normals=np.cross(triangles[:,1]-triangles[:,0],triangles[:,2]-triangles[:,0]);areas=np.linalg.norm(normals,axis=1)/2
  vol=np.sum(np.einsum('ij,ij->i',triangles[:,0],np.cross(triangles[:,1],triangles[:,2])))/6
  state={'closed':bool(np.all(counts==2)),'winding':bool(np.all(winding==0)),'positive_volume':bool(vol>1e-10),'nonzero_float32':bool(np.all(areas>1e-12))}
  if not all(state.values()):fails.append({'label':part['label'],'state':state,'volume':float(vol),'edge_counts':dict(zip(*[x.tolist() for x in np.unique(counts,return_counts=True)]))})
  volume+=vol;minarea=min(minarea,float(areas.min()))
 digests={}
 for material,arrays in groups.items():
  q=np.asarray(np.concatenate(arrays),dtype='<f4');q[q==0]=0;starts=np.lexsort((q[:,:,2],q[:,:,1],q[:,:,0]),axis=-1)[:,0];q=q[np.arange(len(q))[:,None],(starts[:,None]+np.arange(3))%3]
  rows=np.ascontiguousarray(q.reshape(-1,9)).view(np.dtype((np.void,36))).ravel();digests[material]=hashlib.sha256(np.sort(rows).tobytes()).hexdigest()
 report={'oriented_float32_surface_digests_by_material':digests,'id':ID,'variant':'lod' if lod else 'raw','author_parts':len(b.parts),'triangles':sum(len(p['triangles']) for p in b.parts),'failures':fails,'passed':not fails,'minimum_float32_triangle_area_m2':minarea,'sum_of_component_volumes_not_boolean_union_m3':volume,'features':features,'metadata':meta,'all_elevations_estimated':True}
 return report
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--lod',action='store_true');p.add_argument('--out',type=Path,required=True);a=p.parse_args();r=check(a.lod);a.out.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'variant':r['variant'],'passed':r['passed'],'failures':r['failures'][:10],'triangles':r['triangles']},ensure_ascii=False));raise SystemExit(0 if r['passed'] else 1)
