"""Render opaque architecture first, then composite the single glazing plane in linear light."""
import ctypes
import hashlib
import json
from pathlib import Path
import runpy
import struct
import subprocess
import tempfile
import numpy as np
from PIL import Image

COMMON=Path(__file__).resolve().parent.parent/'fifth-textile-warehouse-river-front-v1/inspect-export.py'
lib=runpy.run_path(COMMON)
unit=lib['unit']
sha=lib['sha']


def render(mesh,out,views,width,height):
    reader,raster=lib['helpers']()
    tri,material,names,asset=runpy.run_path(str(reader))['load_triangles'](mesh)
    textures,source,uv,pigment=lib['load_textures'](mesh,material)
    with mesh.open('rb')as inp:
        inp.seek(12);n,_=struct.unpack('<II',inp.read(8));doc=json.loads(inp.read(n))
    alpha=np.ones(len(names))
    for m in doc['materials']:
        if m.get('alphaMode')=='BLEND':
            assert m.get('doubleSided') and not m.get('pbrMetallicRoughness',{}).get('baseColorTexture')
            alpha[names.index(m['name'])]=m['pbrMetallicRoughness']['baseColorFactor'][3]
    assert (alpha<1).sum()==3
    transparent=alpha[material]<1
    # All the thin glazing is on one vertical plane. No two sheets overlap
    # along a ray, so a single transparent depth pass is sufficient.
    plane=tri[transparent].reshape(-1,3);ref=(plane-plane[0])[:,:2]
    _,s,_=np.linalg.svd(ref,full_matrices=False);assert s[1]/s[0]<1e-6
    normal=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0])
    normal/=np.maximum(np.linalg.norm(normal,axis=1)[:,None],1e-15)
    light=.70+.30*np.maximum(0,normal@unit(np.array([-.75,.39,.62])))
    out.mkdir(parents=True,exist_ok=True);rows=[]
    with tempfile.TemporaryDirectory(prefix='concrete-screen-render-')as temp:
        so=Path(temp)/'raster.so'
        subprocess.run(['c++','-O2','-fPIC','-shared',str(raster),'-o',str(so)],check=True)
        draw=ctypes.CDLL(str(so)).draw
        vp=ctypes.c_void_p;draw.restype=None
        draw.argtypes=[ctypes.c_int,ctypes.c_int,ctypes.c_double,ctypes.c_double,ctypes.c_double,ctypes.c_int,vp,vp,vp,vp,ctypes.c_int,vp,vp]
        for name,eye,target,span in views:
            eye=np.array(eye,float);target=np.array(target,float);ray=unit(target-eye)
            right=unit(np.cross(ray,[0,0,1]));up=np.cross(right,ray);f=width*np.linalg.norm(target-eye)/span
            rel=tri-eye;proj=np.zeros((*tri.shape[:2],5),dtype=np.float64)
            proj[:,:,0]=rel@right;proj[:,:,1]=rel@up;proj[:,:,2]=rel@ray
            mask=np.zeros(4);clip=np.zeros(len(tri),np.int32)
            def rasterize(sel):
                pos=np.ascontiguousarray(proj[sel]);tag=np.flatnonzero(sel).astype(np.int32)+1
                depth=np.zeros((height,width),np.float32);hit=np.zeros((height,width),np.int32)
                draw(width,height,width/2,height/2,f,len(tag),pos.ctypes.data,tag.ctypes.data,clip.ctypes.data,mask.ctypes.data,0,depth.ctypes.data,hit.ctypes.data)
                return depth,hit
            depth,hit=rasterize(~transparent);gd,gh=rasterize(transparent)
            pixel=np.zeros((height,width,3))+lib['srgb_to_linear'](np.array([222.,228.,229.])/255)
            proof={};seen={}
            for m in np.unique(material[hit[hit>0]-1]):
                yy,xx=np.nonzero((hit>0)&(material[hit-1]==m));face=hit[yy,xx]-1
                rgb=pigment[m]
                if m in textures:
                    pts=eye+(ray+((xx+.5-width/2)/f)[:,None]*right-((yy+.5-height/2)/f)[:,None]*up)/depth[yy,xx,None]
                    weights=lib['barycentric'](tri[face],pts);coords=np.einsum('ni,nij->nj',weights,uv[face])
                    tex=lib['sample'](*textures[m],coords);rgb=tex*rgb
                    sampled=np.rint(255*lib['linear_to_srgb'](tex)).astype('uint8')
                    proof[names[m]]=dict(pixels=len(face),sampled_srgb_sha256=sha(sampled.tobytes()),sampled_srgb_range=[sampled.min(axis=0).tolist(),sampled.max(axis=0).tolist()])
                pixel[yy,xx]=rgb*light[face,None];seen[names[m]]=len(face)
            y,x=np.nonzero((gh>0)&(gd>depth));m=material[gh[y,x]-1];a=alpha[m,None]
            pixel[y,x]=(1-a)*pixel[y,x]+a*pigment[m]
            for key in np.unique(m):seen[names[key]]=int((m==key).sum())
            covered=int(np.sum((hit>0)|(gh>0)));assert covered>width*height*.015
            path=out/(name+'.jpg')
            Image.fromarray(np.rint(np.clip(lib['linear_to_srgb'](pixel),0,1)*255).astype('uint8')).save(path,quality=92)
            rows.append(dict(view=name,eye=eye.tolist(),target=target.tolist(),width_m_at_target=span,pixels=covered,image=path.name,image_sha256=sha(path.read_bytes()),texture_samples=proof,material_pixels=seen,composited_glazing_pixels=len(m)))
    assert all(r['composited_glazing_pixels']>0 for r in rows if r['view'] in ('west-front','inner-face','rings'))
    return dict(passed=True,model=asset,mesh_faces=len(tri),bounds_x_y_z=[tri.min(axis=(0,1)).tolist(),tri.max(axis=(0,1)).tolist()],reader_sha256=sha(reader.read_bytes()),raster_sha256=sha(raster.read_bytes()),inspection_script_sha256=sha(Path(__file__).read_bytes()),image_size=[width,height],embedded_textures=list(source.values()),views=rows)
