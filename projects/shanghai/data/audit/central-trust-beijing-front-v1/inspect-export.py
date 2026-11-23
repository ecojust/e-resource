"""Inspect exported geometry with the existing independent GLB reader and CPU depth buffer."""
import argparse,ctypes,hashlib,json,runpy,struct,subprocess,tempfile
from pathlib import Path
import numpy as np
from PIL import Image
DIR=Path(__file__).resolve().parent
CITY=DIR.parents[2]
SOURCE=CITY/'source/precise/huangpu-central-trust-beijing-front/source'
READER=DIR.parent/'postal-office-v1/independent-glb-review-helpers.py'
RASTER=DIR.parent/'weile-garden-gate-v1/default-source-visibility/raster.cpp'
VIEWS=[
 ('beijing-road',[10.4,-64,14.8],[10.62,.1,14.8],43),
 ('front-oblique',[27.,-49,11.3],[10.6,1.25,15.1],45),
 ('carved-entrance',[9.,-13.,3.1],[10.62,0,3.05],9.2),
 ('east-secondary-door',[19.1,-11.5,2.6],[17.25,0,2.9],6.6),
 ('courtyard-from-above',[7.60,27.0,23.78],[9.1,16.0,12.32],11.4),
 ('painted-glass-from-below',[8.1,13.2,4.23],[8.8,19.3,10.72],10.9),
 ('glass-medallions',[8.76,17.49,6.65],[8.8,19.3,10.82],6.6),
 ('upper-cornice',[16.,-22.0,23.8],[11.0,0.,23.7],18.)]
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def normal(vec):return vec/np.linalg.norm(vec)
def render(mesh,out):
    tri,indices,names,version=runpy.run_path(READER)['load_triangles'](mesh)
    with mesh.open('rb')as blob:
        blob.seek(12);size,_=struct.unpack('<II',blob.read(8));doc=json.loads(blob.read(size))
    cover=names.index('Trust skylight grey weather glass')
    pigment=np.array([v['pbrMetallicRoughness']['baseColorFactor'][:3] for v in doc['materials']])**(1/2.2)
    alpha=next(v for v in doc['materials'] if v['name']==names[cover])['pbrMetallicRoughness']['baseColorFactor'][3]
    assert abs(alpha-.27)<1e-4
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
            img=np.full((height,width,3),[236,236,231],dtype=np.uint8)
            img[y,x]=np.clip(255*rgb*light[ids,None],0,255).astype(np.uint8)
            # Blend the protective roof over the opaque first hit behind it.
            # The painted underside stays opaque when looking up from the banking hall.
            fr=indices==cover
            cover_y,cover_x=np.nonzero(np.isin(hits,np.flatnonzero(fr)+1))
            if len(cover_x):
                coord=np.ascontiguousarray(xyz[~fr]);tag=np.ascontiguousarray(tags[~fr])
                cclip=np.zeros(len(tag),np.int32);second=np.zeros_like(hits);z2=np.zeros_like(depth)
                draw(width,height,width/2,height/2,f,len(tag),coord.ctypes.data,tag.ctypes.data,cclip.ctypes.data,mask.ctypes.data,0,z2.ctypes.data,second.ctypes.data)
                behind=second[cover_y,cover_x]-1;mask2=behind>=0
                bg=np.full((len(behind),3),236.0)
                bg[mask2]=255*pigment[indices[behind[mask2]]]*light[behind[mask2],None]
                img[cover_y,cover_x]=np.clip(alpha*img[cover_y,cover_x]+(1-alpha)*bg,0,255).astype(np.uint8)
            path=out/(name+'.jpg');Image.fromarray(img).save(path,quality=90)
            counts=np.bincount(m,minlength=len(names))
            assert len(x)>32000 and sum(counts>0)>3
            rows.append({'view':name,'eye':eye.tolist(),'target':target.tolist(),'width_m_at_target':span,'image_sha256':sha(path),
                         'visible_pixels':len(x),'material_pixels':{n:int(v)for n,v in zip(names,counts)if v}})
    (out/'views.json').write_text(json.dumps({'model':version,'mesh_faces':len(tri),'reader':sha(READER),'raster':sha(RASTER),'views':rows},indent=2)+'\n')
if __name__=='__main__':
    args=argparse.ArgumentParser();args.add_argument('decoded_glb',type=Path);args.add_argument('out',type=Path);a=args.parse_args();render(a.decoded_glb,a.out)
