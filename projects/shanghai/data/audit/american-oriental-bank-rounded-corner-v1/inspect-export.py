"""Inspect exported geometry with the existing independent GLB reader and CPU depth buffer."""
import argparse,ctypes,hashlib,json,runpy,struct,subprocess,tempfile
from pathlib import Path
import numpy as np
from PIL import Image
DIR=Path(__file__).resolve().parent
CITY=DIR.parents[2]
SOURCE=CITY/'source/precise/huangpu-american-oriental-bank-rounded-corner/source'
READER=DIR.parent/'postal-office-v1/independent-glb-review-helpers.py'
RASTER=DIR.parent/'weile-garden-gate-v1/default-source-visibility/raster.cpp'
VIEWS=[
 ('market-corner',[49.,-34.,9.1],[20.9,4.2,7.36],23.2),
 ('ningbo-road',[17.,-36.,6.2],[19.,1.3,7.35],24.0),
 ('henan-road',[64.,10.,7.60],[24.7,7.5,7.30],23.8),
 ('entrance-and-board',[29.5,-2.9,2.35],[23.84,2.50,2.30],6.85),
 ('rolled-steel-transoms',[31.,-4.8,6.10],[23.84,2.50,6.02],5.65),
 ('brick-and-air-conditioning',[26.,-7.,4.1],[21.25,1.25,4.65],5.9),
 ('curved-roofline',[40.,-21.,16.9],[22.93,3.10,13.65],12.7)]
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def normal(vec):return vec/np.linalg.norm(vec)
def render(mesh,out):
    tri,indices,names,version=runpy.run_path(READER)['load_triangles'](mesh)
    with mesh.open('rb')as blob:
        blob.seek(12);size,_=struct.unpack('<II',blob.read(8));doc=json.loads(blob.read(size))
    wall=names.index('Meifeng ochre brick strips')
    pigment=np.array([v['pbrMetallicRoughness']['baseColorFactor'][:3] for v in doc['materials']])**(1/2.2)
    # Read the UV streams and PNG actually embedded in the exported mesh.
    import io
    with mesh.open('rb') as stream:
        stream.seek(20+size)
        size_bin,tag_bin=struct.unpack('<II',stream.read(8))
        assert tag_bin==0x004e4942
        buf=stream.read(size_bin)
    def array(idx):
        a=doc['accessors'][idx];v=doc['bufferViews'][a['bufferView']]
        dtype=np.dtype({5126:'<f4',5125:'<u4',5123:'<u2',5121:'u1'}[a['componentType']])
        cols={'VEC2':2,'SCALAR':1}[a['type']]
        start=v.get('byteOffset',0)+a.get('byteOffset',0)
        return np.ndarray((a['count'],cols),dtype=dtype,buffer=buf,offset=start,strides=(v.get('byteStride',cols*dtype.itemsize),dtype.itemsize))
    assert len(doc['meshes'])==1
    uv_faces=np.zeros((len(tri),3,2));cursor=0
    for prim in doc['meshes'][0]['primitives']:
        index=array(prim['indices']).reshape(-1,3);end=cursor+len(index)
        if prim['material']==wall:uv_faces[cursor:end]=array(prim['attributes']['TEXCOORD_0'])[index]
        cursor=end
    assert cursor==len(tri)
    mat=doc['materials'][wall]['pbrMetallicRoughness'];image=doc['textures'][mat['baseColorTexture']['index']]['source']
    view=doc['bufferViews'][doc['images'][image]['bufferView']];start=view.get('byteOffset',0)
    texture=np.asarray(Image.open(io.BytesIO(buf[start:start+view['byteLength']])).convert('RGB'))/255
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
                face_ids=ids[textured]
                triangle=tri[face_ids]
                a=triangle[:,1]-triangle[:,0];b=triangle[:,2]-triangle[:,0]
                delta=pos-triangle[:,0];dot=lambda u,v:np.einsum('ij,ij->i',u,v)
                aa,ab,bb=dot(a,a),dot(a,b),dot(b,b)
                da,db=dot(delta,a),dot(delta,b);det=aa*bb-ab*ab
                r=(bb*da-ab*db)/det;t=(aa*db-ab*da)/det
                uv=np.clip(np.einsum('ni,nij->nj',np.stack([1-r-t,r,t],axis=1),uv_faces[face_ids]),0,1)
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
