"""Fit an ellipse to the visible masonry/void edge of the central stair loggia."""
from pathlib import Path
import json
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import map_coordinates,gaussian_filter
from scipy.optimize import least_squares
from register_front import Camera
import argparse
parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('original_photo',type=Path);parser.add_argument('output_directory',type=Path)
args=parser.parse_args();w=args.output_directory;w.mkdir(parents=True,exist_ok=True)
c=Camera();im=Image.open(args.original_photo).convert('L')
# The full-size image is sampled only through a downscaled study raster.
gray=np.array(im.resize((1950,1097),Image.Resampling.LANCZOS),dtype=float)
gray=gaussian_filter(gray,.78)
def px(x,z):return np.array([c.pixel([a,0,b]) for a,b in zip(x,z)])
def brightness(pts):
    return map_coordinates(gray,[pts[:,1]*(gray.shape[0]/731),pts[:,0]*1.5],order=1)
def state(v):
    theta=np.deg2rad(np.arange(4,178,2))
    u,sp,rx,rz=v
    x=u+rx*np.cos(theta);z=sp+rz*np.sin(theta)
    normals=np.stack([np.cos(theta)/rx,np.sin(theta)/rz],axis=1)
    normals/=np.linalg.norm(normals,axis=1)[:,None]
    offsets=np.arange(-.23,.231,.014);curves=[]
    for step in offsets:
        curves.append(brightness(px(x+normals[:,0]*step,z+normals[:,1]*step)))
    values=np.array(curves);edges=np.diff(values,2,axis=0)
    scores=(values[3:]-values[:-3])-.5*np.abs(offsets[1:-2,None]/.23)**2
    best=np.argmax(scores,axis=0)
    key=np.arange(len(x));valid=scores[best,key]>44.
    selected=(offsets[best]+.021)[:,None]*normals+np.stack([x,z],axis=1)
    return theta,selected,valid,scores[best,key]
v=np.array([.04,8.36,2.34,2.14])
for _ in range(4):
    t,obs,mask,contrast=state(v)
    fit=least_squares(lambda q:(((obs[mask,0]-q[0])/q[2])**2+((obs[mask,1]-q[1])/q[3])**2-1),
                      v,bounds=([-.30,8.0,2.15,1.80],[.4,8.80,2.8,2.65]),loss='soft_l1',f_scale=.015)
    v=fit.x
u,sp,rx,rz=v
distance=[]
for x,z in obs[mask]:
    a=np.arctan2((z-sp)/rz,(x-u)/rx)
    distance.append(np.linalg.norm(c.pixel([x,0,z])-c.pixel([u+rx*np.cos(a),0,sp+rz*np.sin(a)])))
sample=Image.open(args.original_photo).convert('RGB').resize((1300,731),Image.Resampling.LANCZOS);d=ImageDraw.Draw(sample);points=[tuple(c.pixel([u+rx*np.cos(a),0,sp+rz*np.sin(a)]))for a in np.linspace(0,np.pi,130)];d.line(points,fill='yellow',width=2)
for (xx,zz),ok in zip(obs,mask):
 x,y=c.pixel([xx,0,zz]);d.ellipse((x-1.7,y-1.7,x+1.7,y+1.7),fill='cyan' if ok else 'red')
sample.crop((555,117,829,278)).resize((650,382)).save(w/'arch-pick-overlay.jpg',quality=93)
out={'stage':'Before independent street scale','method':'Normal-direction brightness transition on the 2018 camera-registered image; minimum contrast excludes weak and screened sections. Exterior-masonry to interior-shadow sign required. Soft L1 conic fit.',
     'model_parameters':dict(centre_x=u,spring_z=sp,radius_x=rx,rise=rz),'sample_count':len(t),'retained_count':int(sum(mask)),
     'pixel_error_median':float(np.median(distance)),'pixel_error_p90':float(np.percentile(distance,90)),
     'selected_control_xy_px':[list(np.round(c.pixel([x,0,z]),2)) for x,z in obs[mask]],
     'crown_and_springs_xy_px':[list(c.pixel(p)) for p in [(u,0,sp+rz),(u-rx,0,sp),(u+rx,0,sp)]]}
(w/'arch-control.json').write_text(json.dumps(out,indent=2)+'\n');print(v,len(t),sum(mask),np.median(distance),np.percentile(distance,90))
