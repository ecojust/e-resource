"""Verify unchanged published triangles, UVs and images; audit new wall cores."""
import argparse,json,struct,hashlib,math
from pathlib import Path
from collections import Counter,defaultdict
import numpy as np
ap=argparse.ArgumentParser();ap.add_argument('--baseline',type=Path,required=True);ap.add_argument('--candidate',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
DT={5120:'i1',5121:'u1',5122:'<i2',5123:'<u2',5125:'<u4',5126:'<f4'};N={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}
def load(path):
 data=path.read_bytes();n,t=struct.unpack_from('<II',data,12);doc=json.loads(data[20:20+n]);binary=data[28+n:]
 def accessor(i):
  ac=doc['accessors'][i];view=doc['bufferViews'][ac['bufferView']];dtype=np.dtype(DT[ac['componentType']]);columns=N[ac['type']];off=view.get('byteOffset',0)+ac.get('byteOffset',0);stride=view.get('byteStride',columns*dtype.itemsize)
  return np.ndarray((ac['count'],columns),dtype=dtype,buffer=binary,offset=off,strides=(stride,dtype.itemsize)).copy()
 groups=defaultdict(Counter);added=[];nodes=doc.get('nodes',[])
 # Blender exporter has identity mesh nodes in these assets. Reject unhandled
 # transforms so equality cannot accidentally compare incompatible coordinates.
 for node in nodes:
  if 'mesh' in node:
   assert node.get('translation',[0,0,0])==[0,0,0]
   assert node.get('rotation',[0,0,0,1])==[0,0,0,1]
   assert node.get('scale',[1,1,1])==[1,1,1]
   assert node.get('matrix',[1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1])==[1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1]
 for mesh in doc['meshes']:
  for pr in mesh['primitives']:
   mat=doc['materials'][pr['material']]['name'];idx=accessor(pr['indices']).reshape(-1,3);attrs={k:accessor(v) for k,v in pr['attributes'].items()};assert all(np.isfinite(v).all() for v in attrs.values())
   if mat=='Bund18_Recessed_LimeMortar':
    p=attrs['POSITION'][idx].astype(np.float64);volume=np.einsum('ij,ij->i',p[:,0,:],np.cross(p[:,1,:],p[:,2,:])).sum()/6
    added.append({'mesh':mesh['name'],'triangles':len(idx),'signed_volume_m3':float(volume),'attributes':list(attrs)});continue
   attributes=sorted(attrs)
   signature='|'.join(attributes)
   for tri in idx:
    verts=[b''.join(np.ascontiguousarray(attrs[k][j]).tobytes() for k in attributes) for j in tri]
    # Equivalent cyclic vertex order preserves winding; reversed winding fails.
    canonical=min(b''.join(verts[i:]+verts[:i]) for i in range(3))
    groups[(mat,signature)][canonical]+=1
 images=[]
 for im in doc.get('images',[]):
  view=doc['bufferViews'][im['bufferView']];blob=binary[view.get('byteOffset',0):view.get('byteOffset',0)+view['byteLength']];images.append({'bytes':len(blob),'sha256':hashlib.sha256(blob).hexdigest(),'mimeType':im.get('mimeType')})
 return {'path':str(path),'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data),'groups':groups,'added':added,'images':images,'doc':doc}
b=load(a.baseline);c=load(a.candidate)
assert b['groups']==c['groups'],'Original oriented triangle data changed (position, normal, UV and other attributes included).'
assert b['images']==c['images']
assert b['doc']['asset']['copyright']==c['doc']['asset']['copyright']
assert len(c['added'])==2 and all(v['signed_volume_m3']>0 for v in c['added'])
bm={m['name']:m for m in b['doc']['materials']};cm={m['name']:m for m in c['doc']['materials']}
# Material texture indexes are expected to stay stable with one embedded image.
assert all(cm[k]==v for k,v in bm.items()),'Original material definition changed.'
report={'baseline':{'sha256':b['sha256'],'bytes':b['bytes']},'candidate':{'sha256':c['sha256'],'bytes':c['bytes']},'original_oriented_triangle_attributes_exact':True,'original_material_definitions_exact':True,'original_triangle_count':sum(sum(x.values()) for x in b['groups'].values()),'photo_image_unchanged':b['images']==c['images'],'embedded_images':c['images'],'copyright_unchanged':True,'new_wall_core_meshes':c['added'],'candidate_triangle_count':sum(sum(x.values()) for x in c['groups'].values())+sum(x['triangles'] for x in c['added'])}
a.output.write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps(report,ensure_ascii=False,indent=2))
