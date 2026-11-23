"""Rectify unobstructed running-bond samples in the 2018 view, using the registered facade plane."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.ndimage import map_coordinates,gaussian_filter1d
from scipy.signal import find_peaks
from register_street import Camera

PATCHES={'doorway upper panel':(474,291,533,360),'right of the service flue':(575,276,616,354),
         'high central panel':(495,174,535,227)}
STEP=.003

def sample(cam,image,region):
    sx,sy,tx,ty=region
    def on(u,v):return cam.wall((u*5312/1120,v*2988/630),0)
    corners=[on(u,v)for u,v in ((sx,sy),(tx,sy),(tx,ty),(sx,ty))]
    x0=max(corners[0][0],corners[3][0]);x1=min(corners[1][0],corners[2][0])
    z0=max(corners[2][2],corners[3][2]);z1=min(corners[0][2],corners[1][2])
    xs=np.arange(x0,x1,STEP);zs=np.arange(z0,z1,STEP);xx,zz=np.meshgrid(xs,zs)
    out=cam.P@np.stack([xx.ravel(),np.zeros(xx.size),zz.ravel(),np.ones(xx.size)])
    u,v=(out[:2]/out[2]).reshape(2,*xx.shape)
    l,t=int(u.min())-2,int(v.min())-2
    crop=np.asarray(image.crop((l,t,int(u.max())+3,int(v.max())+3)).convert('RGB'),float)
    color=np.stack([map_coordinates(crop[:,:,i],[v-t,u-l],order=1)for i in (0,1,2)],axis=-1)
    # Mortar is paler and less red than the unit face. Work in the rectified
    # metric plane so the horizontal and vertical spacing use the same scale.
    score=color.mean(2)-.70*(color[:,:,0]-color[:,:,1])
    levels=gaussian_filter1d(score.mean(axis=1),1.5)
    peaks,_=find_peaks(levels,prominence=5,distance=int(.040/STEP))
    levels_z=zs[peaks]
    widths=[];joints=[]
    for a,b in zip(peaks,peaks[1:]):
        if not .040<(b-a)*STEP<.10:continue
        strip=score[round(.68*a+.32*b):round(.32*a+.68*b)+1].mean(axis=0)
        heights,_=find_peaks(gaussian_filter1d(strip,1.5),prominence=8,distance=int(.083/STEP))
        positions=xs[heights];intervals=np.diff(positions)
        widths.extend(float(x)for x in intervals if .15<x<.36)
        joints.append({'z':round(float((zs[a]+zs[b])/2),4),'x':np.round(positions,4).tolist()})
    course_intervals=np.diff(levels_z)
    keep=course_intervals[(course_intervals>.041)&(course_intervals<.10)]
    tone=score.ravel();body=color[score<np.percentile(tone,62)];mortar=color[score>np.percentile(tone,95)]
    return {'bounds_reference_image_1120x630':region,'bounds_facade_xz_m':[x0,z0,x1,z1],
            'measured_bed_z_m':np.round(levels_z,4).tolist(),'head_joints_by_course':joints,
            'course_intervals_m':np.round(keep,4).tolist(),'running_unit_intervals_m':np.round(widths,4).tolist(),
            'unit_srgb':np.rint(np.median(body,axis=0)).astype(int).tolist(),'joint_srgb':np.rint(np.median(mortar,axis=0)).astype(int).tolist()}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('image',type=Path);p.add_argument('out',type=Path);a=p.parse_args()
    cam=Camera('2018')
    with Image.open(a.image)as im:patches={k:sample(cam,im,v)for k,v in PATCHES.items()}
    get=lambda key:np.concatenate([v[key]for v in patches.values()])
    heights=get('course_intervals_m');widths=get('running_unit_intervals_m')
    out={'photo_sha256':hashlib.sha256(a.image.read_bytes()).hexdigest(),'camera_sha256':hashlib.sha256((Path(__file__).parent/'street-cameras.json').read_bytes()).hexdigest(),
         'patches':patches,'median_module_m':[round(float(np.median(widths)),4),round(float(np.median(heights)),4)],
         'width_interval_count':len(widths),'course_interval_count':len(heights),
         'notes':'Dimensions are projected photographic estimates based on the eight-view street registration. Joint colour includes weathering, JPEG compression and daylight. Separate bricks are visible along the 143-1 wall. Interior wall composition is unmeasured.'}
    a.out.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
    print(out['median_module_m'],len(widths),len(heights),[(k,v['unit_srgb'],v['joint_srgb'])for k,v in patches.items()])
