"""CPU proof images with the actual glTF alpha from the museum's single glass sheet."""
# Build the adjacent CPU rasterizer once with:
# c++ -O2 -std=c++17 -shared -fPIC raster.cpp -o raster.so
import ctypes
import json
from pathlib import Path
import struct
import numpy as np
from PIL import Image

def read_alpha(path,material):
    with Path(path).open('rb')as stream:
        prefix=stream.read(20)
        size=struct.unpack_from('<I',prefix,12)[0]
        doc=json.loads(stream.read(size))
    spec,=[m for m in doc['materials']if m['name']==material]
    assert spec['alphaMode']=='BLEND'
    alpha=spec['pbrMetallicRoughness']['baseColorFactor'][3]
    assert .18<alpha<.32
    return alpha

def render(tri,materials,colors,name,direction,center,field,*,folder,glass,alpha):
    width,height,focal=490,540,1300
    unit=lambda vec:vec/np.linalg.norm(vec)
    front=unit(np.array(direction,dtype=float));right=unit(np.cross(front,[0.,0.,1.]));up=np.cross(right,front)
    relative=tri-(np.asarray(center)-front*field*focal/width)
    camera=np.stack([relative@right,relative@up,relative@front,tri[:,:,0],tri[:,:,1]],axis=-1)
    normals=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);length=np.linalg.norm(normals,axis=1)
    sun=unit(np.array([-.47,-.74,.49]))
    diffuse=np.divide(normals@sun,length,out=np.zeros_like(length),where=length>1e-10)
    lighting=.62+.38*np.abs(diffuse)
    rgb=(np.clip(np.array([colors[name]for name in materials])*lighting[:,None],0,1)*255).astype(np.int32)
    ids=1+(rgb[:,0]<<16)+(rgb[:,1]<<8)+rgb[:,2]
    so=ctypes.CDLL(str(Path(__file__).with_name('raster.so')));ptr=ctypes.c_void_p
    so.draw.argtypes=[ctypes.c_int,ctypes.c_int,ctypes.c_double,ctypes.c_double,ctypes.c_double,ctypes.c_int,ptr,ptr,ptr,ptr,ctypes.c_int,ptr,ptr]
    depth=np.zeros((height,width),np.float32)
    def layer(use):
        mesh=np.ascontiguousarray(camera[use]);keys=np.ascontiguousarray(ids[use],dtype=np.int32)
        clip=np.zeros(len(mesh),np.int32);mask=np.zeros(4,np.float64);col=np.zeros((height,width),np.int32)
        so.draw(width,height,width/2,height/2,focal,len(mesh),mesh.ctypes.data,keys.ctypes.data,clip.ctypes.data,mask.ctypes.data,0,depth.ctypes.data,col.ctypes.data)
        hit=col!=0;col-=1
        return np.stack([(col>>16)&255,(col>>8)&255,col&255],axis=-1).astype(np.float32),hit
    out,solid=layer(materials!=glass);out[~solid]=[222,219,214]
    sheet,visible=layer(materials==glass);out[visible]=(1-alpha)*out[visible]+alpha*sheet[visible]
    Image.fromarray(np.rint(out).astype(np.uint8)).save(folder/('test-'+name+'.jpg'),quality=88)
    return int(np.count_nonzero(visible))
