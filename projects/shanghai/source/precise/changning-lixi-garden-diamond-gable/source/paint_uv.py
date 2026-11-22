"""Shade actual GLB triangles using their UV accessors and embedded sRGB base-color map."""
from io import BytesIO
import ctypes as ct
import json
import struct
import numpy as np
from PIL import Image

def read_uv(path):
    data = path.read_bytes()
    length = struct.unpack_from('<I', data, 12)[0]
    doc = json.loads(data[20:20 + length])
    blob = memoryview(data)[28 + length:]
    def accessor(index):
        a = doc['accessors'][index]
        view = doc['bufferViews'][a['bufferView']]
        dtype = np.dtype({5123:'<u2',5125:'<u4',5126:'<f4'}[a['componentType']])
        dim = {'VEC2':2,'SCALAR':1}[a['type']]
        offset = view.get('byteOffset', 0) + a.get('byteOffset', 0)
        return np.ndarray((a['count'],dim), dtype, buffer=blob,offset=offset,strides=(view.get('byteStride',dtype.itemsize*dim),dtype.itemsize))
    image_view = doc['bufferViews'][doc['images'][0]['bufferView']]
    start = image_view['byteOffset']
    image = Image.open(BytesIO(blob[start:start+image_view['byteLength']])).convert('RGB')
    uv = []
    textured = []
    for node in doc['nodes']:
        for prim in doc['meshes'][node['mesh']]['primitives']:
            indices=accessor(prim['indices']).ravel().reshape(-1,3)
            mat = doc['materials'][prim['material']]['pbrMetallicRoughness']
            mapped = 'baseColorTexture' in mat
            if mapped:
                assert mat['baseColorTexture']['index']==0
                coords=accessor(prim['attributes']['TEXCOORD_0'])[indices]
            else:
                coords=np.zeros((len(indices),3,2),np.float32)
            uv.append(coords);textured.append(np.full(len(indices),mapped))
    return np.asarray(image),np.concatenate(uv),np.concatenate(textured)

def unit(v):
    a = np.array(v, dtype=float)
    return a / np.linalg.norm(a)

def render(path,tri,names,palette,materials,direction,target,field,dest):
    texture,uv,textured=materials
    width,height=660,440
    forward=unit(direction); right=unit(np.cross(forward,[0.,0.,1.])); up=np.cross(right,forward)
    positions=tri-np.asarray(target)
    points=np.stack((positions@right,-positions@up),axis=-1)*width/field+[width/2,height/2]
    depths=-positions@forward
    frame=np.full((height,width,3),[227,228,224],np.uint8)
    depth=np.full((height,width),-np.inf)
    normal=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);normal/=np.maximum(np.linalg.norm(normal,axis=1)[:,None],1e-10)
    light=.60+.40*np.maximum(0,normal@unit([-.4,-.54,.74]))
    for i,triangle in enumerate(points):
        if normal[i] @ forward > 0:continue
        lo=np.maximum(np.floor(triangle.min(axis=0)).astype(int),0)
        hi=np.minimum(np.ceil(triangle.max(axis=0)).astype(int),[width-1,height-1])
        if np.any(hi<lo):continue
        a,b,c=triangle
        e=b-a;f=c-a;det=e[0]*f[1]-e[1]*f[0]
        if abs(det)<1.e-9:continue
        xx,yy=np.meshgrid(np.arange(lo[0],hi[0]+1)+.5-a[0],np.arange(lo[1],hi[1]+1)+.5-a[1])
        u=(xx*f[1]-yy*f[0])/det;v=(e[0]*yy-e[1]*xx)/det;w=1-u-v
        weights=np.stack((w,u,v),axis=-1);z=weights@depths[i]
        region=np.s_[lo[1]:hi[1]+1,lo[0]:hi[0]+1]
        visible=(u>=0)&(v>=0)&(w>=0)&(z>depth[region])
        if not np.any(visible):continue
        depth[region][visible]=z[visible]
        if textured[i]:
            tex=weights[visible] @ uv[i]
            indices=np.rint(np.clip(tex,0,1)*[texture.shape[1]-1,texture.shape[0]-1]).astype(int)
            colors=texture[indices[:,1],indices[:,0]].astype(float)/255
            linear=np.where(colors<.04045,colors/12.92,((colors+.055)/1.055)**2.4)*light[i]
        else:
            linear=np.asarray(palette[names[i]])*light[i]
        srgb=np.where(linear<.0031308,12.92*linear,1.055*np.maximum(linear,0)**(1/2.4)-.055)
        frame[region][visible]=np.clip(srgb*255,0,255).astype(np.uint8)
    assert np.isfinite(depth).mean()>.13
    Image.fromarray(frame).save(dest,quality=91)
