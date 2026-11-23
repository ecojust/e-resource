"""Render the villa from two registered garden photographs, the street station and an overall view."""
import argparse
import ctypes
import hashlib
import json
from pathlib import Path
import runpy
import subprocess
import tempfile
from unittest.mock import patch

import numpy as np

HERE=Path(__file__).resolve().parent
PRECISE=HERE.parents[1]
shared=runpy.run_path(str(PRECISE/'changning-hongji-yuyuan-garden-houses-8-and-9/measurements/render-garden-stations.py'))
renderer=shared['renderer']


def garden_camera(c):
    u,v,s,k,dv,ds,yaw,r=c
    den=np.array([yaw,-k,0.,1.])
    local=np.stack([u*den+[s,ds,r,0.],v*den+[-r,dv,-s,0.],den])
    transform=np.array([[-1.,0.,0.,9.55],[0.,1.,0.,-13.60],[0.,0.,1.,-2.96],[0.,0.,0.,1.]])
    return local@transform


def stations():
    eye=np.array([3.7,-8.8,1.73])
    scale=116./2.60
    f=8.80*scale
    K=np.array([[f,79.5+eye[0]*scale,0.],[0.,616.-eye[2]*scale,-f],[0.,1.,0.]])
    yield 'street-gable',np.column_stack([K,-K@eye]),[0,15,549,667],[-.44,-.61,.64]
    records=json.loads((HERE/'south-garden-two-photographs.json').read_bytes())['views']
    for n,key,crop in [(0,'garden-elevation',[205,0,870,456]),(8,'garden-balcony',[24,25,1058,1160])]:
        yield key,garden_camera(records[str(n)]['camera_coefficients']),crop,[-.47,.51,.72]
    cam=json.loads((HERE.parent/'source/cameras.json').read_bytes())[0]
    eye,target=np.asarray(cam['eye']),np.asarray(cam['target'])
    direction=target-eye
    distance=np.linalg.norm(direction)
    direction/=distance
    right=np.cross(direction,[0,0,1]);right/=np.linalg.norm(right)
    up=np.cross(right,direction)
    w,h=cam['width'],cam['height'];focal=w*distance/cam['width_m']
    K=np.stack([right*focal+direction*w/2,direction*h/2-up*focal,direction])
    yield 'overall',np.column_stack([K,-K@eye]),[0,0,w,h],[.43,-.54,.72]


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('source',type=Path)
    p.add_argument('out',type=Path)
    p.add_argument('--width',type=int,default=760)
    a=p.parse_args()
    a.out.mkdir(parents=True,exist_ok=True)
    scene=renderer.read_glb(a.source)
    report={'source_glb_sha256':hashlib.file_digest(a.source.open('rb'),'sha256').hexdigest(),'views':{}}
    with tempfile.TemporaryDirectory(dir=a.out)as d:
        so=Path(d)/'depth.so'
        subprocess.run(['cc','-O2','-shared','-fPIC',PRECISE/'huangpu-old-jiefu-nanjing-road-shopfront/measurements/northwest_raster.c','-lm','-o',so],check=True)
        lib=ctypes.CDLL(str(so))
        for name,camera,crop,light in stations():
            projected=shared['projected_parts'](scene,camera)
            sun=np.asarray(light,dtype='float32')
            sun/=np.linalg.norm(sun)
            bearing=[float(np.degrees(np.arctan2(sun[0],sun[1]))%360),float(np.degrees(np.arcsin(sun[2])))]
            with patch.object(renderer,'read_glb',return_value=projected):
                image,note=renderer.raster(a.source,lib,a.width,camera,crop,sun,bearing)
            dest=a.out/(name+'.jpg')
            image.save(dest,quality=92,subsampling=0)
            report['views'][name]=dict(**note,projection=camera.tolist(),sha256=hashlib.file_digest(dest.open('rb'),'sha256').hexdigest())
    (a.out/'render-stations.json').write_text(json.dumps(report,ensure_ascii=False,indent=1)+'\n')


if __name__=='__main__':
    main()
