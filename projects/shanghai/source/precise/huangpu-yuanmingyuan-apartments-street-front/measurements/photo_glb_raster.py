"""Render a photo-registered, textured glTF with a shadow map and a per-pixel depth buffer.

The raster backend is shared with the Old Jiefu comparison (MIT). Camera, crop
and light are supplied by the caller to support a different source photograph.
"""
import ctypes as ct
import hashlib,io,json,struct
import numpy as np
from PIL import Image
def packed(a,kind):return np.ascontiguousarray(a,dtype=kind)

def ptr(a):return ct.c_void_p(a.ctypes.data)

def read_glb(path):
 b=path.read_bytes();magic,ver,size=struct.unpack_from('<4sII',b);assert magic==b'glTF' and ver==2 and size==len(b)
 s,typ=struct.unpack_from('<II',b,12);assert typ==0x4e4f534a;j=json.loads(b[20:20+s]);offset=28+s
 def acc(i):
  a=j['accessors'][i];v=j['bufferViews'][a['bufferView']];k={5126:'<f4',5125:'<u4',5123:'<u2',5121:'u1'}[a['componentType']];nc={'SCALAR':1,'VEC2':2,'VEC3':3}[a['type']];dt=np.dtype(k)
  return np.ndarray((a['count'],nc),dt,buffer=b,offset=offset+v.get('byteOffset',0)+a.get('byteOffset',0),strides=(v.get('byteStride',nc*dt.itemsize),dt.itemsize))
 texs={}
 for i,t in enumerate(j.get('textures',[])):
  image=j['images'][t['source']];v=j['bufferViews'][image['bufferView']];start=offset+v.get('byteOffset',0);raw=b[start:start+v['byteLength']];tarr=np.array(Image.open(io.BytesIO(raw)).convert('RGB'),copy=True)
  sm=j['samplers'][t['sampler']];texs[i]=(packed(tarr,'u1'),sm.get('wrapS',10497),sm.get('wrapT',10497),{'embedded':image['name'],'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'pixel_size':[tarr.shape[1],tarr.shape[0]]})
 parts=[]
 for idx in j['scenes'][j.get('scene',0)]['nodes']:
  node=j['nodes'][idx];assert set(node)<={'name','mesh'},'Expected an identity node from the project exporter'
  for prim in j['meshes'][node['mesh']]['primitives']:
   A=prim['attributes'];pos=acc(A['POSITION']).astype('float32');nrm=acc(A['NORMAL']).astype('float32');ids=packed(acc(prim['indices']).flatten(),'uint32')
   pos=packed(pos[:,[0,2,1]]*[1,-1,1],'float32');nrm=packed(nrm[:,[0,2,1]]*[1,-1,1],'float32');uv=packed(acc(A['TEXCOORD_0']),'float32')if 'TEXCOORD_0' in A else np.zeros((len(pos),2),'float32')
   assert np.isfinite(pos).all() and np.isfinite(uv).all() and ids.max()<len(pos)
   mat=j['materials'][prim['material']]['pbrMetallicRoughness'];ti=mat.get('baseColorTexture',{}).get('index');assert ti is None or 'TEXCOORD_0' in A
   parts.append((pos,nrm,uv,ids,prim['material'],ti))
 return parts,j['materials'],texs

def raster(path,lib,ss,camera,crop,sun,angles):
 parts,materials,texs=read_glb(path);x0,y0,x1,y1=crop;pix=(x1-x0)/ss
 w=ss;h=round((y1-y0)/pix);res=2304
 u=np.cross([0.,0.,1.],sun);u/=np.linalg.norm(u);v=np.cross(sun,u);axes=np.array([u,v,sun],dtype='float32')
 lights=[packed(t[0]@axes.T,'float32')for t in parts];mn=np.min([L.min(axis=0)for L in lights],axis=0);mx=np.max([L.max(axis=0)for L in lights],axis=0);scale=(res-10)/max((mx-mn)[:2]);shadow=np.full((res,res),-np.inf,'float32')
 for i,pr in enumerate(parts):
  L=lights[i];L[:,:2]=(L[:,:2]-mn[:2])*scale+5;ids=pr[3];lib.shadow_depth(len(ids)//3,ptr(ids),ptr(L),res,ptr(shadow))
 image=np.full((h,w,3),[230,231,226],'uint8');depth=np.zeros((h,w),'float32');label=np.zeros((h,w),'uint16')
 s=np.linspace(0,1,256);linear=packed(np.where(s<=.04045,s/12.92,((s+.055)/1.055)**2.4),'float32')
 a=np.linspace(0,1,65536);srgb=packed(np.rint(np.clip(np.where(a<=.0031308,12.92*a,1.055*a**(1/2.4)-.055),0,1)*255),'uint8')
 dummy=np.ones(3,'uint8')*255;eye=-np.linalg.solve(camera[:,:3],camera[:,3]);triangles=0;uv_faces=0
 for (pos,nrm,uv,ids,mi,ti),L in zip(parts,lights):
  p=pos@camera[:,:3].T+camera[:,3];assert np.min(p[:,2])>0,'Camera near plane cuts geometry'
  coords=(p[:,:2]/p[:,2,None]-[x0,y0])/pix
  payload=packed(np.column_stack([coords,1./p[:,2],uv,L,nrm]),'float32');n=len(ids)//3;triangles+=n
  mat=materials[mi]['pbrMetallicRoughness'];base=packed(mat.get('baseColorFactor',[1.,1.,1.,1.])[:3],'float32')
  if ti is None:tex,tw,th,su,sv=dummy,0,0,33071,33071
  else:tex,su,sv,_=texs[ti];th,tw=tex.shape[:2];uv_faces+=n
  lib.paint(n,ptr(ids),ptr(payload),w,h,ptr(depth),ptr(label),ptr(image),mi,ptr(base),ct.c_float(mat.get('metallicFactor',1.)),ct.c_float(mat.get('roughnessFactor',1.)),ptr(tex),tw,th,su,sv,ptr(linear),ptr(srgb),res,ptr(shadow),ptr(sun))
 counts=np.bincount(label.ravel(),minlength=len(materials)+1)[1:]
 return Image.fromarray(image),{'triangles':triangles,'textured_triangles':uv_faces,'photo_crop_original_px':crop,'sun_bearing_altitude_deg':angles,'rendered_px':[w,h],'camera_eye_m':eye.tolist(),'materials_visible_samples':{q['name']:int(n)for q,n in zip(materials,counts)if n},'textures':[t[3] for t in texs.values()],'zbuffer_foreground_pixels':int(np.count_nonzero(depth))}
