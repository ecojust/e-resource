"""Independently decode exported triangles, check likely first surfaces, render two views."""
from pathlib import Path
import argparse,hashlib,json,struct,sys
import numpy as np
from PIL import Image,ImageDraw
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'source'))
from nanjing_steel_windows import window_pair_dimensions

def decode(p):
 data=p.read_bytes();magic,version,size=struct.unpack_from('<4sII',data)
 assert (magic,version,size)==(b'glTF',2,len(data))
 n,kind=struct.unpack_from('<II',data,12);assert kind==0x4e4f534a
 j=json.loads(data[20:20+n]);buf=data[28+n:]
 def acc(idx):
  a=j['accessors'][idx];v=j['bufferViews'][a['bufferView']]
  return np.frombuffer(buf,'<f4'if a['componentType']==5126 else '<u4',count=a['count']*(3 if a['type']=='VEC3'else 1),offset=a.get('byteOffset',0)+v.get('byteOffset',0)).reshape(a['count'],-1)
 tri=[];materials=[]
 for q in j['meshes'][0]['primitives']:
  xyz=acc(q['attributes']['POSITION']).astype(float)
  norms=acc(q['attributes']['NORMAL']);idx=acc(q['indices']).reshape(-1,3)
  t=xyz[idx];f=np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]);length=np.linalg.norm(f,axis=1)
  assert np.all(np.isfinite(t)) and min(length)>1e-12 and np.min(np.sum(f/length[:,None]*norms[idx[:,0]],axis=1))>.99999
  t=t[:,:,[0,2,1]];t[:,:,1]*=-1
  tri.extend(t);materials.extend([q['material']]*len(t))
 return np.array(tri),np.array(materials),j

def hit(T,mi,j,x,z):
 a=T[:,0,[0,2]];u=T[:,1,[0,2]]-a;v=T[:,2,[0,2]]-a;d=np.array([x,z])-a
 det=u[:,0]*v[:,1]-u[:,1]*v[:,0];keep=np.abs(det)>1.e-12;det=np.where(keep,det,1)
 s=(d[:,0]*v[:,1]-d[:,1]*v[:,0])/det;t=(u[:,0]*d[:,1]-u[:,1]*d[:,0])/det
 keep&=(s>=0)&(t>=0)&(s+t<=1)
 if not keep.any():return None
 y=T[:,0,1]+s*(T[:,1,1]-T[:,0,1])+t*(T[:,2,1]-T[:,0,1]);idx=np.argmin(np.where(keep,y,np.inf))
 return {'first_y_m':round(float(y[idx]),4),'surface':j['materials'][mi[idx]]['name']}
def checks(T,m,j):
 out=[]
 for k,w in enumerate(window_pair_dimensions()):
  l,r,bt,up=(w[n] for n in ['left','right','bottom','upper'])
  for x,z,allowed,label in [(.24,.76,['glass'],'west half glazing'),(.5,.68,['steel'],'meeting stile'),(.51,.95,['transom'],'upper transom'),(.25,.405,['steel'],'top short vertical'),
    (.12,.405,['glass'],'open upper guard'),(.5,.239,['diagonal','steel edges'],'central X'),
    (.25,.067,['steel'],'lower short vertical'),(.15,.067,['glass'],'open lower guard')]:
   pt=[l+x*(r-l),bt+z*(up-bt)];res=hit(T,m,j,*pt);out.append(dict(bay=k,label=label,xz_m=pt,first=res,expected=allowed,passed=res is not None and any(a in res['surface']for a in allowed)))
 a,b=window_pair_dimensions()
 for i,z in enumerate(np.linspace(a['bottom']+.1,a['upper']-.1,9)):
  x=.45*a['right']+.55*b['left'];res=hit(T,m,j,x,z);out.append(dict(label='central brick pier',xz_m=[x,z],first=res,passed=res is not None and any(a in res['surface']for a in ('brick','mortar'))))
 return out

def render(T,mat,j,target):
 canv=Image.new('RGB',(1072,628),(228,226,222));draw=ImageDraw.Draw(canv)
 palette=[]
 for m in j['materials']:
  c=np.array(m['pbrMetallicRoughness']['baseColorFactor'][:3]);palette.append(np.where(c<.0031308,c*12.92,1.055*c**(1/2.4)-.055)*255)
 palette=np.array(palette)
 for i,(eye,tilt) in enumerate([(0.,0.),(.45,.10)]):
  n=np.array([eye,-1.,tilt]);n/=np.linalg.norm(n);x=np.cross([0,0,1],n);x/=np.linalg.norm(x);z=np.cross(n,x);p=T@np.array([x,z,n]).T
  mx=p[:,:,:2].min(axis=(0,1));hi=p[:,:,:2].max(axis=(0,1));sc=min(486/(hi[0]-mx[0]),545/(hi[1]-mx[1]));q=(p[:,:,:2]-(mx+hi)/2)*sc;q[:,:,0]+=268+i*536;q[:,:,1]=310-q[:,:,1]
  normal=np.cross(T[:,1]-T[:,0],T[:,2]-T[:,0]);normal/=np.linalg.norm(normal,axis=1)[:,None]
  lamp=np.array([-.5,-.8,.6]);lamp/=np.linalg.norm(lamp);illum=np.clip(.65+.46*normal@lamp,.4,1.16)
  # A per-pixel depth test handles long thin strip and brick triangles crossing in projection.
  image=np.asarray(canv).copy();depth=np.full((628,1072),-np.inf)
  for idx in np.nonzero(normal@n>0)[0]:
   pts=q[idx];low=np.maximum([0,0],np.floor(pts.min(axis=0)).astype(int));high=np.minimum([1071,627],np.ceil(pts.max(axis=0)).astype(int))
   if np.any(high<low):continue
   xx,yy=np.meshgrid(np.arange(low[0],high[0]+1)+.5,np.arange(low[1],high[1]+1)+.5)
   ax,ay=pts[1]-pts[0];bx,by=pts[2]-pts[0];det=ax*by-ay*bx
   if abs(det)<1e-10:continue
   dx,dy=xx-pts[0,0],yy-pts[0,1];sa=(dx*by-dy*bx)/det;sb=(ax*dy-ay*dx)/det
   z0,z1,z2=p[idx,:,2];z=z0+sa*(z1-z0)+sb*(z2-z0)
   sx=slice(low[0],high[0]+1);sy=slice(low[1],high[1]+1);keep=(sa>=0)&(sb>=0)&(sa+sb<=1)&(z>depth[sy,sx])
   depth[sy,sx][keep]=z[keep];image[sy,sx][keep]=np.clip(palette[mat[idx]]*illum[idx],0,255).astype(int)
  canv=Image.fromarray(image)
 canv.save(target)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('glb',type=Path);p.add_argument('record',type=Path);p.add_argument('--preview',type=Path);a=p.parse_args()
 T,m,j=decode(a.glb);test=checks(T,m,j);r={'file':a.glb.name,'sha256':hashlib.sha256(a.glb.read_bytes()).hexdigest(),'bytes':a.glb.stat().st_size,'triangles':len(T),'bounds_xyz_m':[T.min(axis=(0,1)).tolist(),T.max(axis=(0,1)).tolist()],'materials':[q['name']for q in j['materials']],'checks':test,'passed':all(t['passed']for t in test)}
 if a.preview:render(T,m,j,a.preview);r['preview_sha256']=hashlib.sha256(a.preview.read_bytes()).hexdigest()
 a.record.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
 print(a.glb.name,r['triangles'],len(test),r['passed'],[(t['label'],t['first']) for t in test if not t['passed']])
 sys.exit(0 if r['passed']else 1)
