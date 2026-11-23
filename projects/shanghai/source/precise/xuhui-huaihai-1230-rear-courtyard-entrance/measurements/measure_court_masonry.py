"""Measure facing courses on three separate wall patches of Gao's 1230 courtyard photograph."""
from pathlib import Path
import argparse,hashlib,json

import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter1d,map_coordinates
from register_court import Camera

PATCHES=((82,22,194,142),(210,22,330,142),(343,22,448,142))
def correlation(a,axis,step,interval):
    # Remove slow lighting variation before testing physical repeat intervals.
    a=np.moveaxis(a,axis,-1)
    a=a-gaussian_filter1d(a,12,axis=-1)
    candidates=[]
    for lag in range(round(interval[0]/step),round(interval[1]/step)+1):
        left,right=a[...,:-lag],a[...,lag:]
        denom=np.sqrt(np.mean(left*left)*np.mean(right*right))
        candidates.append((np.mean(left*right)/denom,lag*step))
    score,pitch=max(candidates)
    return {'best_pitch_m':round(pitch,5),'correlation':round(float(score),5)}
def measure(path):
    camera=Camera('04');im=np.asarray(Image.open(path).convert('RGB'))
    step=.003;rows=[]
    for x0,y0,x1,y1 in PATCHES:
        corners=np.array([camera.wall(uv) for uv in ((x0,y0),(x1,y0),(x0,y1),(x1,y1))])
        xmin,xmax=max(corners[0,0],corners[2,0]),min(corners[1,0],corners[3,0])
        zmin,zmax=max(corners[2,2],corners[3,2]),min(corners[0,2],corners[1,2])
        x,z=np.meshgrid(np.arange(xmin,xmax,step),np.arange(zmin,zmax,step))
        xyz=np.stack((x,np.zeros_like(x),z),axis=-1)
        projected=(xyz-camera.c)@camera.R.T
        u=camera.cx+camera.f*projected[:,:,0]/projected[:,:,2]
        v=camera.cy+camera.f*projected[:,:,1]/projected[:,:,2]
        assert x0-.5<u.min()<=u.max()<x1+.5 and y0-.5<v.min()<=v.max()<y1+.5
        rgb=np.stack([map_coordinates(im[:,:,i].astype(float),[v,u],order=1) for i in range(3)],axis=-1)
        grey=rgb@[.2126,.7152,.0722]
        rows.append({'original_pixel_region':[x0,y0,x1,y1],
                     'course':correlation(grey,0,step,(.045,.095)),
                     'unit_length':correlation(grey,1,step,(.13,.27)),
                     'median_srgb':np.median(rgb,axis=(0,1)).round(1).tolist()})
    return dict(source_author='高参88',reference_image='gao-04',source_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                method='Rectify independent image patches to the registered courtyard face, remove low-frequency luminance and compare shifted samples. Scale is conditional on the photographed door.',
                native_width=im.shape[1],native_height=im.shape[0],patches=rows,
                caution='Joint thickness and mortar depth remain estimates. Brick type and structural wall construction are undocumented.')
if __name__=='__main__':
    c=argparse.ArgumentParser(description=__doc__);c.add_argument('original',type=Path);c.add_argument('output',type=Path);a=c.parse_args()
    a.output.write_text(json.dumps(measure(a.original),ensure_ascii=False,indent=2)+'\n')
