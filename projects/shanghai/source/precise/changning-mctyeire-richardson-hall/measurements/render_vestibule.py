"""Render the registered indoor photograph using the emitted glTF and the tall lawn entrance as a diffuse source."""
import argparse
import ctypes
import hashlib
import json
import os
from pathlib import Path
import runpy
import subprocess
import tempfile
import numpy as np
from PIL import Image
HERE=Path(__file__).resolve().parent
PROJECT=next(p for p in HERE.parents if (p/'tools/package_architectural_model.py').is_file())
READER=PROJECT/'source/precise/huangpu-yuanmingyuan-apartments-street-front/measurements/photo_glb_raster.py'
def render_indoor(mesh,out,station=None,crop=(150,0,1460,1067),pixels=800):
    station=station or json.loads((HERE/'vestibule-station.json').read_text())
    m=np.array(station['projection']);inverse=np.linalg.inv(m[:,:3]);eye=-inverse@m[:,3]
    parts,materials,textures=runpy.run_path(str(READER))['read_glb'](mesh)
    tris=np.concatenate([pos[indices.reshape(-1,3)] for pos,norm,uv,indices,mat,texture in parts])
    uv=np.concatenate([coords[indices.reshape(-1,3)] for pos,norm,coords,indices,mat,texture in parts])
    material=np.concatenate([np.full(len(indices)//3,mat) for pos,norm,coords,indices,mat,texture in parts])
    width=pixels;height=round(width*(crop[3]-crop[1])/(crop[2]-crop[0]));grid=2
    step=(crop[2]-crop[0])/(width*grid);fg=0;canvas=np.empty((height*grid,width*grid,3),'u1')
    def pointer(a):return ctypes.c_void_p(a.ctypes.data)
    tris=np.ascontiguousarray(tris,'f4');eye=np.ascontiguousarray(eye,'f4')
    with tempfile.TemporaryDirectory(dir=out.parent) as directory:
        lib=Path(directory)/'vestibule.so'
        subprocess.run(['c++','-std=c++17','-O2','-fPIC','-shared',str(HERE/'vestibule_daylight.cpp'),os.environ.get('EMBREE_LIB','-lembree4'),'-o',str(lib)],check=True)
        design=ctypes.CDLL(str(lib))
        if design.prepare(len(tris),pointer(tris)):raise RuntimeError('Could not prepare Embree scene')
        try:
            for first in range(0,height*grid,32):
                y,x=np.indices((min(32,height*grid-first),width*grid),dtype='f4')
                pixels_uv=np.stack([crop[0]+(x.ravel()+.5)*step-.5,crop[1]+(first+y.ravel()+.5)*step-.5,np.ones(x.size)],axis=-1)
                rays=np.ascontiguousarray(pixels_uv@inverse.T,'f4')
                ids=np.zeros(x.size,'i4');weights=np.zeros((x.size,2),'f4');ao=np.zeros(x.size,'f4');day=np.zeros_like(ao)
                err=design.paint(len(rays),pointer(rays),pointer(eye),pointer(ids),pointer(weights),pointer(ao),pointer(day))
                if err:raise RuntimeError(f'Embree device returned {err}')
                selected=ids>=0;faces=ids[selected];bary=weights[selected];s=uv[faces]
                texture_uv=s[:,0]+(s[:,1]-s[:,0])*bary[:,:1]+(s[:,2]-s[:,0])*bary[:,1:]
                linear=np.zeros((len(faces),3),'f4');mat=material[faces]
                for i,m in enumerate(materials):
                    hit=mat==i
                    if not np.any(hit):continue
                    pbr=m['pbrMetallicRoughness'];base=np.array(pbr.get('baseColorFactor',[1,1,1,1])[:3])
                    if 'baseColorTexture' in pbr:
                        tex=textures[pbr['baseColorTexture']['index']][0];size=np.array([tex.shape[1],tex.shape[0]])
                        coords=np.floor((texture_uv[hit]%1)*size).astype(int)%size
                        rgb=tex[coords[:,1],coords[:,0]]/255
                        base=base*np.where(rgb<=.04045,rgb/12.92,((rgb+.055)/1.055)**2.4)
                    linear[hit]=base
                # Diffuse interreflection gives the room an ambient fill. Exposure is illustrative.
                intensity=(.15+.56*ao[selected]+1.8*np.minimum(1,day[selected]))[:,None]
                rgb=linear*intensity
                srgb=np.clip(np.where(rgb<=.0031308,rgb*12.92,1.055*np.power(rgb,1/2.4)-.055),0,1)
                row=canvas[first:first+y.shape[0]].reshape(-1,3);row[:]=[221,223,218];row[selected]=np.uint8(np.rint(srgb*255))
                fg+=int(selected.sum())
        finally:design.release()
    im=Image.fromarray(canvas).resize((width,height),Image.Resampling.LANCZOS);im.save(out,quality=92)
    return dict(size=list(im.size),sha256=hashlib.sha256(out.read_bytes()).hexdigest(),source=station['photo'],foreground_subpixels=fg,subpixels=height*width*grid**2,method='Registered GLB. 2×2 supersampling, 20 short-distance diffuse visibility rays, nine samples across the lawn entrance. Approximate indirect exposure falls off along the transverse passages and beyond the gallery.')
if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('mesh',type=Path);ap.add_argument('out',type=Path);ap.add_argument('--width',type=int,default=800);a=ap.parse_args()
    print(json.dumps(render_indoor(a.mesh,a.out,pixels=a.width),ensure_ascii=False))
