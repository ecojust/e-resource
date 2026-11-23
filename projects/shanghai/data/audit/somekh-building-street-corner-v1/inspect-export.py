"""Inspect exported geometry with the existing independent GLB reader and CPU depth buffer."""
import argparse,ctypes,hashlib,json,runpy,struct,subprocess,tempfile
from pathlib import Path
import numpy as np
from PIL import Image
DIR=Path(__file__).resolve().parent
CITY=DIR.parents[2]
SOURCE=CITY/'source/precise/huangpu-somekh-building-street-corner/source'
READER=DIR.parent/'postal-office-v1/independent-glb-review-helpers.py'
RASTER=DIR.parent/'weile-garden-gate-v1/default-source-visibility/raster.cpp'
VIEWS=[
 ('beijing-front',[17.0,-104,12.5],[17,0,14.45],47),
 ('corner-oblique',[53,-48,14.0],[22,1.25,13.],48),
 ('from-pavement',[52,-29,2.20],[30.,1.3,10.1],36),
 ('corner-porch',[46.,-9,2.15],[35.4,1.13,3.15],8.4),
 ('central-portal',[17.4,-18,3.42],[17.38,-.04,3.22],7.75),
 ('drum-from-above',[45.,-19,36.],[34.2,3.40,23.9],12.7)]
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def normal(vec):return vec/np.linalg.norm(vec)
def render(mesh,out):
    tri,indices,names,version=runpy.run_path(READER)['load_triangles'](mesh)
    with mesh.open('rb')as blob:
        blob.seek(12);size,_=struct.unpack('<II',blob.read(8));doc=json.loads(blob.read(size))
    wall=names.index('warm grey washed aggregate')
    pigment=np.array([v['pbrMetallicRoughness']['baseColorFactor'][:3] for v in doc['materials']])**(1/2.2)
    texture=np.asarray(Image.open(SOURCE/'washed-aggregate.png').convert('RGB'))/255
    n=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);n/=np.maximum(np.linalg.norm(n,axis=1)[:,None],1e-12)
    light=np.clip(.74+.26*np.maximum(0,n@normal(np.array([-.43,-.64,.62]))),0,1)
    rows=[];out.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory()as temp:
        so=Path(temp)/'raster.so'
        subprocess.run(['c++','-O2','-fPIC','-shared',RASTER,'-o',so],check=True)
        draw=ctypes.CDLL(str(so)).draw;ptr=ctypes.c_void_p
        draw.argtypes=[ctypes.c_int,ctypes.c_int,ctypes.c_double,ctypes.c_double,ctypes.c_double,ctypes.c_int,ptr,ptr,ptr,ptr,ctypes.c_int,ptr,ptr]
        mask=np.zeros(4);clip=np.zeros(len(tri),np.int32);tags=np.arange(1,len(tri)+1,dtype=np.int32)
        for name,eye,target,span in VIEWS:
            width,height=840,650
            eye=np.array(eye);target=np.array(target);aim=normal(target-eye);right=normal(np.cross(aim,[0,0,1]));up=np.cross(right,aim)
            rel=tri-eye;blank=np.zeros(tri.shape[:2]);xyz=np.ascontiguousarray(np.stack([rel@right,rel@up,rel@aim,blank,blank],axis=-1))
            hits=np.zeros((height,width),np.int32);depth=np.zeros((height,width),np.float32);f=width*np.linalg.norm(target-eye)/span
            draw(width,height,width/2,height/2,f,len(tri),xyz.ctypes.data,tags.ctypes.data,clip.ctypes.data,mask.ctypes.data,0,depth.ctypes.data,hits.ctypes.data)
            y,x=np.nonzero(hits);ids=hits[y,x]-1;m=indices[ids];rgb=pigment[m].copy()
            textured=m==wall
            if np.any(textured):
                xx,yy=x[textured],y[textured]
                pos=eye+(aim+((xx+.5-width/2)/f)[:,None]*right-((yy+.5-height/2)/f)[:,None]*up)/depth[yy,xx,None]
                uv=np.mod(np.column_stack(((pos[:,0]+.68*pos[:,1])/1.36,1-pos[:,2]/1.20)),1.)
                rgb[textured]=texture[(uv[:,1]*(texture.shape[0]-1)).astype(int),(uv[:,0]*(texture.shape[1]-1)).astype(int)]
            img=np.full((height,width,3),[236,236,231],dtype=np.uint8)
            img[y,x]=np.clip(255*rgb*light[ids,None],0,255).astype(np.uint8)
            path=out/(name+'.jpg');Image.fromarray(img).save(path,quality=90)
            counts=np.bincount(m,minlength=len(names))
            assert len(x)>32000 and sum(counts>0)>3
            rows.append({'view':name,'eye':eye.tolist(),'target':target.tolist(),'width_m_at_target':span,'image_sha256':sha(path),
                         'visible_pixels':len(x),'material_pixels':{n:int(v)for n,v in zip(names,counts)if v}})
    (out/'views.json').write_text(json.dumps({'model':version,'mesh_faces':len(tri),'reader':sha(READER),'raster':sha(RASTER),'views':rows},indent=2)+'\n')
if __name__=='__main__':
    args=argparse.ArgumentParser();args.add_argument('decoded_glb',type=Path);args.add_argument('out',type=Path);a=args.parse_args();render(a.decoded_glb,a.out)
