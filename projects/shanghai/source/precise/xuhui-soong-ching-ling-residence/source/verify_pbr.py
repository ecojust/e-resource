"""Compare actual embedded images and position/UV pairs after Meshopt decoding."""
import argparse,hashlib,io,json,struct
from pathlib import Path
import numpy as np
from PIL import Image

def read(path):
 data=path.read_bytes();n=struct.unpack_from('<I',data,12)[0];return json.loads(data[20:20+n]),data[28+n:]
def access(doc,binary,index):
 ac=doc['accessors'][index];view=doc['bufferViews'][ac['bufferView']]
 dtype=np.dtype({5126:'<f4',5125:'<u4',5123:'<u2',5121:'u1'}[ac['componentType']]);width={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[ac['type']]
 return np.ndarray((ac['count'],width),dtype=dtype,buffer=binary,offset=view.get('byteOffset',0)+ac.get('byteOffset',0),strides=(view.get('byteStride',dtype.itemsize*width),dtype.itemsize)).copy()
def inspect(path):
 doc,binary=read(path);rows=[];images={};material=next(m for m in doc['materials'] if m['name']=='pebbledash')
 for name,info in [('basecolor',material['pbrMetallicRoughness']['baseColorTexture']),('normal',material['normalTexture']),('orm',material['pbrMetallicRoughness']['metallicRoughnessTexture'])]:
  image=doc['images'][doc['textures'][info['index']]['source']];view=doc['bufferViews'][image['bufferView']];png=binary[view.get('byteOffset',0):view.get('byteOffset',0)+view['byteLength']]
  expected=Path(__file__).resolve().parent.parent/'textures'/('soong-original-pebbledash-'+name+'.png')
  assert png==expected.read_bytes(),(name,'embedded texture bytes changed')
  pixels=np.array(Image.open(io.BytesIO(png)));assert pixels.shape[:2]==(512,512)
  if name=='orm':assert pixels[:,:,2].max()==0 and pixels[:,:,1].std()>0
  images[name]={'sha256':hashlib.sha256(png).hexdigest(),'size':[512,512]}
 assert abs(material['normalTexture']['scale']-.35)<1e-7
 for mesh in doc['meshes']:
  for prim in mesh['primitives']:
   if doc['materials'][prim['material']]['name']!='pebbledash':continue
   assert 'TANGENT' not in prim['attributes']
   pos=access(doc,binary,prim['attributes']['POSITION']);uv=access(doc,binary,prim['attributes']['TEXCOORD_0']);ix=access(doc,binary,prim['indices']).ravel()
   assert np.isfinite(uv).all() and np.ptp(uv)>1
   rows.append(np.concatenate([pos,uv],axis=1)[ix])
 rows=np.concatenate(rows).astype('<f4');rows[rows==0]=0
 return np.sort(rows.view('V20').ravel()),images
p=argparse.ArgumentParser()
for key in ['raw','decoded_full','lod','decoded_lod','report']:p.add_argument('--'+key.replace('_','-'),type=Path,required=True)
a=p.parse_args();report={}
for role,raw,decoded in [('full',a.raw,a.decoded_full),('lod',a.lod,a.decoded_lod)]:
 x,images=inspect(raw);y,other=inspect(decoded);assert np.array_equal(x,y) and images==other
 report[role]={'sha256':hashlib.sha256(raw.read_bytes()).hexdigest(),'decoded_sha256':hashlib.sha256(decoded.read_bytes()).hexdigest(),'textured_triangle_corners':len(x),'position_uv_pairs_exact':True,'images':images,'no_tangent_attribute':True,'normal_scale':.35,'metallic_channel_zero':True}
a.report.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
