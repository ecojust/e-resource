"""Render the embedded glTF texture in the registered 2024 northwest camera and build a credited comparison plate.

Requires Python, NumPy, Pillow, a C compiler and the adjacent northwest_raster.c.
Example filenames are relative to the model source / measurements directories.
"""
from pathlib import Path
import argparse,ctypes as ct,hashlib,io,json,math,struct,subprocess,sys,tempfile
import numpy as np
from PIL import Image,ImageDraw,ImageFont,ImageOps

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'source'))
from crown_plane import CAMERA
PHOTO_HASH='e3181ab81bc036acce916f4e63fb29e6c1a4dfa56b5fb0d81f74dcb95507ad7d'
PHOTO_LINK='https://commons.wikimedia.org/wiki/File:257_Nanjing_East_Road,_Shanghai_%E5%8D%97%E4%BA%AC%E4%B8%9C%E8%B7%AF257%E5%8F%B7_(2024)_-_IMG_01.jpg'
CROP=(45,205,2985,2555)
CROWN=(1030,280,2035,1050)
SASH=(95,1400,1115,2190)
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
 # NOAA fractional-year approximation, 23 April 2024 local CST, at 16:45:49.
 day=114;hours=16+45/60+49/3600;g=2*math.pi/366*(day-1+(hours-12)/24);lat=math.radians(31.23955);lon=121.48063
 eq=229.18*(.000075+.001868*math.cos(g)-.032077*math.sin(g)-.014615*math.cos(2*g)-.040849*math.sin(2*g));dec=.006918-.399912*math.cos(g)+.070257*math.sin(g)-.006758*math.cos(2*g)+.000907*math.sin(2*g)-.002697*math.cos(3*g)+.00148*math.sin(3*g)
 ha=math.radians((hours*60+eq+4*lon-480)/4-180)
 east=-math.cos(dec)*math.sin(ha);north=math.sin(dec)*math.cos(lat)-math.cos(dec)*math.cos(ha)*math.sin(lat);up=math.sin(lat)*math.sin(dec)+math.cos(lat)*math.cos(dec)*math.cos(ha)
 site=json.loads((HERE/'north-front-site.json').read_bytes());xy=site['owner']['geometry']['coordinates'][0];axis=(np.array(xy[2])-xy[3])*[95264.,110871.];axis/=np.linalg.norm(axis);inside=[-axis[1],axis[0]]
 ray=np.array([np.dot([east,north],axis),np.dot([east,north],inside),up]);return packed(ray/np.linalg.norm(ray),'float32'),[round(math.degrees(math.atan2(east,north))%360,2),round(math.degrees(math.asin(up)),2)]
def raster(path,lib,ss):
 parts,materials,texs=read_glb(path);x0,y0,x1,y1=CROP;pix=(x1-x0)/ss
 w=ss;h=round((y1-y0)/pix);res=2304
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
  mat=materials[mi]['pbrMetallicRoughness'];base=packed(mat['baseColorFactor'][:3],'float32')
  if ti is None:tex,tw,th,su,sv=dummy,0,0,33071,33071
  else:tex,su,sv,_=texs[ti];th,tw=tex.shape[:2];uv_faces+=n
  lib.paint(n,ptr(ids),ptr(payload),w,h,ptr(depth),ptr(label),ptr(image),mi,ptr(base),ct.c_float(mat.get('metallicFactor',1.)),ct.c_float(mat.get('roughnessFactor',1.)),ptr(tex),tw,th,su,sv,ptr(linear),ptr(srgb),res,ptr(shadow),ptr(sun))
 counts=np.bincount(label.ravel(),minlength=len(materials)+1)[1:]
 return Image.fromarray(image),{'triangles':triangles,'textured_triangles':uv_faces,'photo_crop_original_px':CROP,'sun_bearing_altitude_deg':angles,'rendered_px':[w,h],'camera_eye_m':eye.tolist(),'materials_visible_samples':{q['name']:int(n)for q,n in zip(materials,counts)if n},'textures':[t[3] for t in texs.values()],'zbuffer_foreground_pixels':int(np.count_nonzero(depth))}
def font(size,bold=False):
 family=Path('/usr/share/fonts/opentype/noto')/('NotoSansCJK-Bold.ttc' if bold else 'NotoSansCJK-Regular.ttc')
 return ImageFont.truetype(str(family),size,index=2)
def board(photo,raw,output):
 im=ImageOps.exif_transpose(Image.open(photo));assert im.size==(3024,4032)
 lr=Image.Resampling.LANCZOS;left,top,right,bottom=CROP;fw,fh=raw.size
 def rendered_crop(rect):
  return raw.crop(((rect[0]-left)*fw/(right-left),(rect[1]-top)*fh/(bottom-top),(rect[2]-left)*fw/(right-left),(rect[3]-top)*fh/(bottom-top)))
 panel=Image.new('RGB',(1836,1276),(249,248,244));d=ImageDraw.Draw(panel);ink=(42,41,37);sub=(89,87,79)
 d.text((42,19),'老介福绸缎局 · 西北角',font=font(44,True),fill=ink)
 d.text((44,84),'上海市黄浦区南京东路257号　｜　2024年4月23日，南京东路与河南中路交叉口',font=font(23),fill=sub)
 gutter=26;pw=863;xcol=[42,42+pw+gutter];y=178;ph=round(pw*(bottom-top)/(right-left))
 for x,title,pic in zip(xcol,['现场照片','同机位三维复原'],[im.crop(CROP),raw]):
  d.text((x,128),title,font=font(24,True),fill=ink);panel.paste(pic.resize((pw,ph),lr),(x,y))
 # Detail regions share the exact same camera and sampling rectangle as the main pair.
 by=y+ph+25
 for pos,(label,rect) in enumerate([('砖冠退台与短石带',CROWN),('北侧砖墩与钢窗',SASH)]):
  x=xcol[pos];d.text((x,by),label,font=font(22,True),fill=ink)
  cw=(pw-14)//2;ch=202;cropim=im.crop(rect);cropgeom=rendered_crop(rect)
  for ix,p in enumerate([cropim,cropgeom]):
   # Vertical framing is shared by both members of each detail pair.
   p=ImageOps.fit(p,(cw,ch),method=lr,centering=(.5,.5));panel.paste(p,(x+ix*(cw+14),by+44))
 fy=by+265;d.line((42,fy,1794,fy),fill=(204,201,192),width=1)
 d.text((42,fy+14),'摄影　Chainwit. · Wikimedia Commons · CC BY 4.0（裁切）',font=font(19),fill=sub)
 d.text((42,fy+48),'模型与对照图板　CC BY-SA 4.0。模型保留弧形大屏的安装面。照片记录当日商号、广告与后方街景。',font=font(18),fill=sub)
 panel=panel.crop((0,0,1836,min(1276,fy+92)));panel.save(output,quality=94,optimize=True,subsampling=0)
def main():
 p=argparse.ArgumentParser();p.add_argument('model',type=Path);p.add_argument('oblique_photo',type=Path);p.add_argument('output',type=Path);p.add_argument('--source-pixels-wide',type=int,default=2080);p.add_argument('--raw-render',type=Path);a=p.parse_args()
 assert sha(a.oblique_photo)==PHOTO_HASH
 with tempfile.TemporaryDirectory()as folder:
  so=Path(folder)/'raster.so';subprocess.run(['cc','-O2','-fPIC','-shared','-o',str(so),str(HERE/'northwest_raster.c'),'-lm'],check=True);lib=ct.CDLL(str(so));lib.shadow_depth.restype=lib.paint.restype=None;raw,meta=raster(a.model,lib,a.source_pixels_wide)
 if a.raw_render:raw.save(a.raw_render)
 board(a.oblique_photo,raw,a.output)
 meta.update({'model_sha256':sha(a.model),'photo_sha256':PHOTO_HASH,'photo_source':PHOTO_LINK,'photo_credit':'Chainwit., 2024-04-23, CC BY 4.0. Cropped and rescaled for comparison.','photo_license':'https://creativecommons.org/licenses/by/4.0/','plate_license':'https://creativecommons.org/licenses/by-sa/4.0/','camera_sha256':sha(HERE/'corner-crown-camera.json'),'texture_method':'glTF material baseColorFactor and embedded baseColorTexture at perspective-correct TEXCOORD_0. sRGB texture decoding, bilinear sampling in linear light, original sampler wrap mode.','lighting':'Approximate local sun for the original capture time. Three-dimensional shadow map and hemispherical skylight. Actual cloud opacity, glass reflections and dated street advertising are not reconstructed.','detail_original_regions':[CROWN,SASH],'software_sha256':sha(Path(__file__)),'raster_sha256':sha(HERE/'northwest_raster.c'),'board_sha256':sha(a.output)})
 a.output.with_suffix('.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n')
 print(a.output,meta['model_sha256'],meta['board_sha256'],meta['triangles'],meta['textured_triangles'])
if __name__=='__main__':main()
