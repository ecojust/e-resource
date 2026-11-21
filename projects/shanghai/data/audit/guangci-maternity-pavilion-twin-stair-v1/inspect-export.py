"""Inspect the courtyard windows, terrace, stair and relief by depth-testing the textured exported mesh."""
import argparse
import ctypes
import hashlib
import io
import json
from pathlib import Path
import runpy
import struct
import subprocess
import sys
import tempfile

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parents[2]/'source/precise/huangpu-guangci-maternity-pavilion-twin-stair/source'
READER = HERE.parent/'postal-office-v1/independent-glb-review-helpers.py'
RASTER = HERE.parent/'weile-garden-gate-v1/default-source-visibility/raster.cpp'
sys.path.insert(0, str(SOURCE))
from pavilion_materials import BRICK, brick_coordinates


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


def normal(vector):
    return vector / np.linalg.norm(vector)


def read_uv_mesh(path, faces, material_ids, names):
    """Follow the same scene traversal as the independent positions reader."""
    with path.open('rb') as stream:
        magic, version, total = struct.unpack('<4sII',stream.read(12))
        assert magic == b'glTF' and version == 2 and total == path.stat().st_size
        jsize, chunk = struct.unpack('<II',stream.read(8))
        assert chunk == 0x4e4f534a
        doc = json.loads(stream.read(jsize))
        size, chunk = struct.unpack('<II',stream.read(8))
        assert chunk == 0x004e4942
        binary = stream.read(size)
    wall = names.index(BRICK)
    texture_ref = doc['materials'][wall]['pbrMetallicRoughness']['baseColorTexture']
    assert texture_ref.get('texCoord',0) == 0 and not texture_ref.get('extensions')
    tex = doc['textures'][texture_ref['index']]
    sampler = doc.get('samplers',[{}])[tex.get('sampler',0)]
    assert sampler.get('wrapS',10497) == sampler.get('wrapT',10497) == 10497
    image = doc['images'][tex['source']]
    view = doc['bufferViews'][image['bufferView']]
    start = view.get('byteOffset',0)
    png = binary[start:start+view['byteLength']]
    png_sha = hashlib.sha256(png).hexdigest()
    assert image['mimeType']=='image/png' and png_sha==sha(SOURCE/'brick-facing.png')
    texture = np.asarray(Image.open(io.BytesIO(png)).convert('RGB'),dtype=np.float32)/255

    def accessor(index):
        spec = doc['accessors'][index]
        assert 'sparse' not in spec
        dimensions = {'SCALAR':1,'VEC2':2}[spec['type']]
        dtype = np.dtype({5121:'u1',5123:'<u2',5125:'<u4',5126:'<f4'}[spec['componentType']])
        view = doc['bufferViews'][spec['bufferView']]
        offset = view.get('byteOffset',0)+spec.get('byteOffset',0)
        values = np.ndarray((spec['count'],dimensions),dtype=dtype,buffer=binary,offset=offset,
                            strides=(view.get('byteStride',dimensions*dtype.itemsize),dtype.itemsize))
        return values.astype(float)/np.iinfo(dtype).max if spec.get('normalized') else values

    uv = np.zeros((len(faces),3,2),dtype=np.float32)
    cursor=0
    def node(index):
        nonlocal cursor
        item = doc['nodes'][index]
        if 'mesh' in item:
            for prim in doc['meshes'][item['mesh']]['primitives']:
                attrs=prim['attributes']
                indices=accessor(prim['indices']).reshape(-1) if 'indices'in prim else np.arange(doc['accessors'][attrs['POSITION']]['count'])
                indices=indices.reshape(-1,3)
                end=cursor+len(indices)
                mat=prim.get('material',-1)
                assert np.all(material_ids[cursor:end]==mat)
                if mat==wall:
                    uv[cursor:end]=accessor(attrs['TEXCOORD_0'])[indices]
                cursor=end
        for child in item.get('children',[]):node(child)
    for root in doc['scenes'][doc.get('scene',0)]['nodes']:node(root)
    assert cursor==len(faces)
    owned=material_ids==wall
    assert owned.any()
    x,y,z=faces[owned].transpose(2,0,1)
    surface=faces[owned]
    normals=np.cross(surface[:,1]-surface[:,0],surface[:,2]-surface[:,0])
    axes=np.argmax(np.abs(normals),axis=1)[:,None]
    u,v=brick_coordinates(x,y,z,axes)
    expected=np.stack((u,1-v),axis=-1)
    error=float(np.abs(uv[owned]-expected).max())
    assert error<.0001,('metric UVs changed',error)
    assert np.ptp(uv[owned],axis=(0,1)).min()>1
    return doc,wall,uv,texture,dict(packed_image_sha256=png_sha,image_dimensions=[texture.shape[1],texture.shape[0]],
        uv_triangles=int(owned.sum()),max_metric_uv_error=error,uv_repeat='REPEAT/REPEAT')


def texture_pixels(world, triangles, corner_uv, texture):
    # A world-space hit recovers perspective-correct barycentric weights for the
    # exact winning triangle. The colour is sampled from its emitted accessor.
    p=world-triangles[:,0];a=triangles[:,1]-triangles[:,0];b=triangles[:,2]-triangles[:,0]
    dot=lambda v,w:np.einsum('ij,ij->i',v,w)
    aa,ab,bb=dot(a,a),dot(a,b),dot(b,b)
    det=aa*bb-ab*ab
    assert np.min(det)>0
    pa,pb=dot(p,a),dot(p,b)
    u=(pa*bb-pb*ab)/det;v=(pb*aa-pa*ab)/det
    uv=(corner_uv[:,0]+u[:,None]*(corner_uv[:,1]-corner_uv[:,0])+v[:,None]*(corner_uv[:,2]-corner_uv[:,0]))%1
    height,width=texture.shape[:2]
    col=uv[:,0]*width-.5;row=uv[:,1]*height-.5
    x=np.floor(col).astype(int);y=np.floor(row).astype(int);fx=(col-x)[:,None];fy=(row-y)[:,None]
    return ((1-fy)*((1-fx)*texture[y%height,x%width]+fx*texture[y%height,(x+1)%width])+
            fy*((1-fx)*texture[(y+1)%height,x%width]+fx*texture[(y+1)%height,(x+1)%width]))


def render(mesh,out):
    tri,indices,names,version=runpy.run_path(READER)['load_triangles'](mesh)
    doc,wall,uv,texture,texture_info=read_uv_mesh(mesh,tri,indices,names)
    pigment=np.array([m.get('pbrMetallicRoughness',{}).get('baseColorFactor',[1,1,1,1])[:3] for m in doc['materials']])
    pigment=np.where(pigment<=.0031308,12.92*pigment,1.055*pigment**(1/2.4)-.055)
    normals=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0])
    normals/=np.maximum(np.linalg.norm(normals,axis=1)[:,None],1e-14)
    light=np.clip(.70+.30*np.maximum(0,normals@normal(np.array([.42,-.54,.73]))),0,1)
    out.mkdir(parents=True,exist_ok=True);views=json.loads((SOURCE/'cameras.json').read_bytes())
    rows=[]
    with tempfile.TemporaryDirectory() as temp:
        lib=Path(temp)/'visibility.so'
        subprocess.run(['c++','-O2','-fPIC','-shared',RASTER,'-o',lib],check=True)
        draw=ctypes.CDLL(str(lib)).draw;P=ctypes.c_void_p
        draw.argtypes=[ctypes.c_int,ctypes.c_int,ctypes.c_double,ctypes.c_double,ctypes.c_double,
                       ctypes.c_int,P,P,P,P,ctypes.c_int,P,P];draw.restype=None
        mask=np.zeros(4);clip=np.zeros(len(tri),np.int32);tags=np.arange(1,len(tri)+1,dtype=np.int32)
        for view in views:
            width,height=view['width'],view['height']
            eye,target=np.array(view['eye']),np.array(view['target'])
            aim=normal(target-eye);right=normal(np.cross(aim,[0,0,1]));up=np.cross(right,aim)
            rel=tri-eye;xyz=np.zeros((*tri.shape[:2],5));xyz[:,:,0]=rel@right;xyz[:,:,1]=rel@up;xyz[:,:,2]=rel@aim
            f=width*np.linalg.norm(target-eye)/view['width_m']
            hits=np.zeros((height,width),np.int32);depth=np.zeros((height,width),np.float32)
            draw(width,height,width/2,height/2,f,len(tri),xyz.ctypes.data,tags.ctypes.data,clip.ctypes.data,
                 mask.ctypes.data,0,depth.ctypes.data,hits.ctypes.data)
            del rel,xyz
            y,x=np.nonzero(hits);ids=hits[y,x]-1;m=indices[ids];rgb=pigment[m].copy()
            textured=np.flatnonzero(m==wall)
            for start in range(0,len(textured),16384):
                pick=textured[start:start+16384];xx,yy=x[pick],y[pick];chosen=ids[pick]
                world=eye+(aim+((xx+.5-width/2)/f)[:,None]*right-((yy+.5-height/2)/f)[:,None]*up)/depth[yy,xx,None]
                rgb[pick]=texture_pixels(world,tri[chosen],uv[chosen],texture)
            image=np.full((height,width,3),[236,236,231],dtype=np.uint8)
            image[y,x]=np.clip(255*rgb*light[ids,None],0,255).astype(np.uint8)
            path=out/(view['name']+'.jpg');Image.fromarray(image).save(path,quality=90)
            counts=np.bincount(m,minlength=len(names))
            assert len(x)>25000 and sum(counts>0)>=4,(view['name'],len(x),counts)
            rows.append(dict(view=view['name'],eye=view['eye'],target=view['target'],width_m_at_target=view['width_m'],
                image_sha256=sha(path),visible_pixels=len(x),material_pixels={n:int(v)for n,v in zip(names,counts)if v}))
    assert len(rows)==9 and all(row['material_pixels'].get(BRICK,0)>0 for row in rows)
    (out/'views.json').write_text(json.dumps(dict(model=version,mesh_faces=len(tri),reader=sha(READER),raster=sha(RASTER),
        glb_sha256=sha(mesh),cameras_sha256=sha(SOURCE/'cameras.json'),texture=texture_info,views=rows),indent=2)+'\n')


if __name__=='__main__':
    args=argparse.ArgumentParser()
    args.add_argument('decoded_glb',type=Path);args.add_argument('out',type=Path)
    options=args.parse_args();render(options.decoded_glb,options.out)
