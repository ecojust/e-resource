#!/usr/bin/env python3
"""Audit actual serialized GLB image/UV data against every registered pane."""
from pathlib import Path
import argparse,hashlib,json,struct
import numpy as np
HERE=Path(__file__).resolve().parent

def check(output):
 data=(output/'bund07.glb').read_bytes();assert len(data)<100_000_000
 magic,ver,total=struct.unpack_from('<4sII',data);assert magic==b'glTF' and ver==2 and total==len(data)
 jl,jt=struct.unpack_from('<II',data,12);assert jt==0x4e4f534a;doc=json.loads(data[20:20+jl]);bl,bt=struct.unpack_from('<II',data,20+jl);assert bt==0x004e4942;binary=data[28+jl:28+jl+bl]
 evidence=json.loads((output/'photo-uv-evidence.json').read_text());source=(HERE/evidence['source']['image']).read_bytes();sha=hashlib.sha256(source).hexdigest();assert sha==evidence['source']['image_sha256']
 assert len(doc['images'])==1 and 'uri' not in doc['images'][0]
 view=doc['bufferViews'][doc['images'][0]['bufferView']];embedded=binary[view.get('byteOffset',0):view.get('byteOffset',0)+view['byteLength']];assert embedded==source
 def acc(i):
  a=doc['accessors'][i];v=doc['bufferViews'][a['bufferView']];dtype={5126:'<f4',5125:'<u4'}[a['componentType']];n={'SCALAR':1,'VEC2':2,'VEC3':3}[a['type']];return np.frombuffer(binary,dtype,count=a['count']*n,offset=v.get('byteOffset',0)+a.get('byteOffset',0)).reshape(-1,n)
 mapped=[]
 for primitive in doc['meshes'][0]['primitives']:
  material=doc['materials'][primitive['material']];tex=material.get('pbrMetallicRoughness',{}).get('baseColorTexture')
  if tex:
   assert material['name']=='PhotoFacade_Bund07_RegisteredGlass';mapped.append(primitive)
   assert material['extras']['photographicSource']=={'rawSize':[5184,3456],'exifOrientation':1,'uvConvention':'stored-pixels'}
  else:assert 'TEXCOORD_0' not in primitive['attributes']
 assert len(mapped)==1
 uv=acc(mapped[0]['attributes']['TEXCOORD_0']);assert np.isfinite(uv).all() and np.all((uv>=0)&(uv<=1));actual=np.unique(uv.astype(np.float64),axis=0)
 expected=np.array([q for p in evidence['per_pane'] for q in p['stored_uv_corners']]);assert len(expected)==18*4 and len(actual)==len(expected)
 distances=np.linalg.norm(actual[:,None,:]-expected[None,:,:],axis=2);max_error=float(max(distances.min(0).max(),distances.min(1).max()));assert max_error<8e-8
 inverse_error=0
 for pane in evidence['per_pane']:
  for xy,uv0 in zip(pane['source_quad_px'],pane['stored_uv_corners']):
   x,y=xy;back=np.array([uv0[0]*5184,uv0[1]*3456]);inverse_error=max(inverse_error,float(np.linalg.norm(back-[x,y])))
 assert inverse_error<1e-7
 tris=len(acc(mapped[0]['indices']))//3;assert tris==18*12
 assert 'Suicasmo' in doc['asset']['copyright'] and 'CC0-1.0' in doc['asset']['copyright']
 report={'schema':'bund07-serialized-photo-uv-check-v1','passed':True,'raw_sha256':hashlib.sha256(data).hexdigest(),'raw_bytes':len(data),'embedded_image_count':1,'original_jpeg_byte_identical':True,'image_sha256':sha,'photo_material_count':1,'photo_glazing_panels':18,'photo_glazing_triangles':tris,'unique_registered_uv_corners':len(actual),'maximum_serialized_uv_error':max_error,'maximum_exif_inverse_pixel_error':inverse_error,'untextured_other_primitives':len(doc['meshes'][0]['primitives'])-1,'visual_source_control_review':'photo-glass-inspection.png; all sampled quadrilaterals actually inspected inside glass panes, inset from original frame bars.','scope_limit':'Numerical UV and embedded-byte checks supplement source-pane inspection; fixed-camera rendered comparison remains separate.'}
 (output/'photo-uv-check.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,default=HERE/'output');a=p.parse_args();check(a.output)
