"""Project textured meshes through registered cameras. Rasterizer adapted from the project’s Jiefu facade study."""
import argparse, ctypes as ct, hashlib, io, json, os, struct, subprocess, tempfile
from pathlib import Path
import numpy as np
from PIL import Image
HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
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
def sun_vector():
 ray=np.array([-.42,-.65,.63]);return packed(ray/np.linalg.norm(ray),'float32'),None
def raster(path,lib,ss):
 parts,materials,texs=read_glb(path);x0,y0,x1,y1=CROP;pix=(x1-x0)/ss
 w=ss;h=round((y1-y0)/pix);res=1152
 sun,angles=sun_vector();u=np.cross([0.,0.,1.],sun);u/=np.linalg.norm(u);v=np.cross(sun,u);axes=np.array([u,v,sun],dtype='float32')
 lights=[packed(t[0]@axes.T,'float32')for t in parts];mn=np.min([L.min(axis=0)for L in lights],axis=0);mx=np.max([L.max(axis=0)for L in lights],axis=0);scale=(res-10)/max((mx-mn)[:2]);shadow=np.full((res,res),-np.inf,'float32')
 for i,pr in enumerate(parts):
  L=lights[i];L[:,:2]=(L[:,:2]-mn[:2])*scale+5;ids=pr[3];lib.shadow_depth(len(ids)//3,ptr(ids),ptr(L),res,ptr(shadow))
 image=np.full((h,w,3),[230,231,226],'uint8');depth=np.zeros((h,w),'float32');label=np.zeros((h,w),'uint16')
 s=np.linspace(0,1,256);linear=packed(np.where(s<=.04045,s/12.92,((s+.055)/1.055)**2.4),'float32')
 a=np.linspace(0,1,65536);srgb=packed(np.rint(np.clip(np.where(a<=.0031308,12.92*a,1.055*a**(1/2.4)-.055),0,1)*255),'uint8')
 dummy=np.ones(3,'uint8')*255;eye=-np.linalg.solve(CAMERA[:,:3],CAMERA[:,3]);triangles=0;uv_faces=0
 for (pos,nrm,uv,ids,mi,ti),L in zip(parts,lights):
  p=pos@CAMERA[:,:3].T+CAMERA[:,3];assert np.min(p[:,2])>0,'Camera near plane cuts geometry'
  coords=(p[:,:2]/p[:,2,None]-[x0,y0])/pix
  payload=packed(np.column_stack([coords,1./p[:,2],uv,L,nrm]),'float32');n=len(ids)//3;triangles+=n
  mat=materials[mi]['pbrMetallicRoughness'];base=packed(mat.get('baseColorFactor',[1.,1.,1.,1.])[:3],'float32')
  if ti is None:tex,tw,th,su,sv=dummy,0,0,33071,33071
  else:tex,su,sv,_=texs[ti];th,tw=tex.shape[:2];uv_faces+=n
  lib.paint(n,ptr(ids),ptr(payload),w,h,ptr(depth),ptr(label),ptr(image),mi,ptr(base),ct.c_float(mat.get('metallicFactor',1.)),ct.c_float(mat.get('roughnessFactor',1.)),ptr(tex),tw,th,su,sv,ptr(linear),ptr(srgb),res,ptr(shadow),ptr(sun))
 counts=np.bincount(label.ravel(),minlength=len(materials)+1)[1:]
 return Image.fromarray(image),{'triangles':triangles,'textured_triangles':uv_faces,'photo_crop_original_px':CROP,'light_xyz':sun.tolist(),'rendered_px':[w,h],'camera_eye_display_units':eye.tolist(),'materials_visible_samples':{q['name']:int(n)for q,n in zip(materials,counts)if n},'textures':[t[3] for t in texs.values()],'zbuffer_foreground_pixels':int(np.count_nonzero(depth))}

def main():
 global CAMERA,CROP
 opts=argparse.ArgumentParser()
 opts.add_argument('raw',type=Path);opts.add_argument('near',type=Path);opts.add_argument('far',type=Path)
 opts.add_argument('output',type=Path);args=opts.parse_args()
 matrices=json.loads((HERE/'gable-registered-cameras.json').read_bytes())
 report={}
 with tempfile.TemporaryDirectory() as tmp:
  shared=Path(tmp)/'gable.so'
  subprocess.run(['cc','-O2','-shared','-fPIC',str(HERE/'gable_raster.c'),'-o',str(shared),'-lm'],check=True)
  fd=os.memfd_create('gable-raster');os.write(fd,shared.read_bytes());lib=ct.CDLL(f'/proc/self/fd/{fd}')
  lib.shadow_depth.restype=lib.paint.restype=None
  for key,mesh in [('raw',args.raw),('full',args.near),('lod',args.far)]:
   folder=args.output/key;folder.mkdir(parents=True,exist_ok=True);views={}
   for name,mat,crop,width in [('courtyard-2016','first',(0,0,2144,1424),640),('oblique-2009','second',(0,0,850,1130),480),('relief','first',(1010,755,1520,1180),480)]:
    CAMERA=np.array(matrices[mat]);CROP=crop
    im,r=raster(mesh,lib,width);image=folder/(name+'.jpg');im.save(image,quality=88)
    assert r['zbuffer_foreground_pixels']>2500 and r['textured_triangles']>50
    for tex in r['textures']:assert sha(HERE.parent/'source'/tex['embedded'])==tex['sha256']
    assert len(r['textures'])==3
    views[name]={**r,'render_sha256':sha(image)}
   report[key]={'sha256':sha(mesh),'views':views}
  os.close(fd)
 (args.output/'three-role-render.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':main()
