"""Author-side raw-buffer screening, not independent acceptance QA."""
import json,struct,hashlib,collections
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parent.parent

def read(path):
 data=path.read_bytes();n=struct.unpack_from('<I',data,12)[0];doc=json.loads(data[20:20+n]);blob=data[28+n:]
 def accessor(i):
  a=doc['accessors'][i];v=doc['bufferViews'][a['bufferView']];dt={5126:'<f4',5125:'<u4'}[a['componentType']];k={'SCALAR':1,'VEC2':2,'VEC3':3}[a['type']]
  return np.frombuffer(blob,dtype=dt,count=a['count']*k,offset=v.get('byteOffset',0)+a.get('byteOffset',0)).reshape(-1,k).astype(float)
 return doc,accessor

out={'independent_QA':False,'scope':'Author screening of serialized triangles and UV distances; does not certify source likeness, native routes or all partial coplanar overlaps.','files':[]}
for filename in ['bajin-main-detailed.glb','bajin-main-lod.glb']:
 p=ROOT/'exports'/filename;doc,ac=read(p);area=[];normerr=[];metric=[];hand=[];counter=collections.Counter();textured=0
 for pr in doc['meshes'][0]['primitives']:
  pos=ac(pr['attributes']['POSITION']);ind=ac(pr['indices']).astype(int).reshape(-1,3);pp=pos[ind];nn=np.cross(pp[:,1]-pp[:,0],pp[:,2]-pp[:,0]);aa=np.linalg.norm(nn,axis=1);area.extend(aa.tolist());nn/=aa[:,None]
  normal=ac(pr['attributes']['NORMAL'])[ind];normerr.append(float(np.abs(normal-nn[:,None,:]).max()))
  counter.update(tuple(sorted(tuple(v) for v in tr)) for tr in pp)
  if 'TEXCOORD_0' in pr['attributes']:
   uv=ac(pr['attributes']['TEXCOORD_0'])[ind];textured+=len(ind)
   for i,j in [(0,1),(1,2),(2,0)]:
    ll=np.linalg.norm(pp[:,j]-pp[:,i],axis=1);dd=.4*np.linalg.norm(uv[:,j]-uv[:,i],axis=1);metric.extend(np.abs(ll-dd).tolist())
   a=uv[:,1]-uv[:,0];bb=uv[:,2]-uv[:,0];hand.extend((a[:,0]*bb[:,1]-a[:,1]*bb[:,0]).tolist())
 duplicates=sum(v-1 for v in counter.values() if v>1)
 r={'file':filename,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'triangles':len(area),'minimum_double_area_m2':min(area),'exact_unoriented_duplicate_triangles_all_materials':duplicates,'maximum_serialized_normal_component_error':max(normerr),'textured_triangles':textured,'maximum_uv_edge_distance_error_m':max(metric),'maximum_uv_signed_area':max(hand),'all_uv_negative_handedness':all(x<0 for x in hand),'TANGENT_present':any('TANGENT' in pr['attributes'] for pr in doc['meshes'][0]['primitives']),'samplers':doc.get('samplers')}
 assert r['minimum_double_area_m2']>1e-12 and duplicates==0 and r['all_uv_negative_handedness']
 out['files'].append(r)
(ROOT/'review/author-buffer-screen.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
