"""Recompute the end-wall camera from Antigng's original image and a supplied width."""
import argparse
import hashlib
import json
import math
from pathlib import Path

import cv2
import numpy as np
from PIL import Image,ImageOps
from scipy.optimize import least_squares

HERE=Path(__file__).resolve().parent
CONTROLS={"central_axis":[1321.,2247.],"base_center":[1390.,3935.],"left_base":[326.,3965.],"right_base":[2426.,3910.]}
SOURCE_SHA="c704d8f7e2e8900bc362c6ce4d0d0b268c2921b28ba1553d4c562d9ffa49f873"


def vanishing_points(image):
    ratio=.55
    small=cv2.resize(image,(0,0),fx=ratio,fy=ratio)
    raw=cv2.createLineSegmentDetector(cv2.LSD_REFINE_STD).detect(small)[0].reshape(-1,2,2)/ratio
    raw=raw[(raw[:,:,0].min(1)>140)&(raw[:,:,0].max(1)<2440)&(raw[:,:,1].min(1)>1820)&(raw[:,:,1].max(1)<3980)]
    delta=raw[:,1]-raw[:,0]
    lengths=np.linalg.norm(delta,axis=1)
    long=lengths>65
    lines,delta,lengths=raw[long],delta[long],lengths[long]
    angle=np.degrees(np.arctan2(delta[:,1],delta[:,0]))%180
    result={}
    for kind,keep in [("vertical",abs(angle-90)<7),("horizontal",np.minimum(angle,180-angle)<7)]:
        pts=lines[keep]
        weights=lengths[keep]
        normal=np.cross(np.c_[pts[:,0],np.ones(len(pts))],np.c_[pts[:,1],np.ones(len(pts))])
        normal/=np.linalg.norm(normal[:,:2],axis=1)[:,None]
        def homogeneous(q):
            return np.array([q[0],1.,q[1]/1e4] if kind=="vertical" else [1.,q[0],q[1]/1e4])
        def errors(q):
            return (normal@homogeneous(q))*np.sqrt(weights/150.)
        q=least_squares(errors,[0.,0.],loss="soft_l1",f_scale=.004).x
        residual=np.abs(errors(q))
        inliers=residual<max(.007,np.median(residual)*2.7)
        normal,weights=normal[inliers],weights[inliers]
        q=least_squares(errors,q,loss="soft_l1",f_scale=.003).x
        result[kind]={"count":len(weights),"homogeneous_vanishing_point":homogeneous(q).tolist()}
    return result


def calibrate(photo,width):
    if hashlib.sha256(photo.read_bytes()).hexdigest()!=SOURCE_SHA:
        raise ValueError("Provide the original Commons image with its original EXIF data")
    img=np.asarray(ImageOps.exif_transpose(Image.open(photo)).convert("L"))
    height,w=img.shape
    f=math.hypot(w,height)*31./math.hypot(36.,24.)
    K=np.array([[f,0,w/2],[0,f,height/2],[0,0,1.]])
    fits=vanishing_points(img)
    def unit(p):
        return p/np.linalg.norm(p)
    def axis(kind):
        return unit(np.linalg.solve(K,fits[kind]["homogeneous_vanishing_point"]))
    x,z=axis("horizontal"),axis("vertical")
    x*=np.sign(x[0]);z*=-np.sign(z[1]);x=unit(x-z*(z@x))
    R=np.column_stack((x,unit(np.cross(z,x)),z))
    def ray(uv):
        return R.T@np.linalg.solve(K,[*uv,1.])
    v=ray(CONTROLS["base_center"])
    eye=v*1.58/v[2];eye[2]=1.58
    def on_wall(uv):
        d=ray(uv)
        return eye+d*(-eye[1]/d[1])
    # Scale is defined by the measured width. The initial eye above is unit normalization only.
    scale=width/(on_wall(CONTROLS["right_base"])[0]-on_wall(CONTROLS["left_base"])[0])
    position=eye*scale-np.array([on_wall(CONTROLS["central_axis"])[0]*scale,0.,0.])
    matrix=K@R@np.column_stack((np.eye(3),-position))
    return {"matrix":matrix.tolist(),"camera_xyz_m":position.tolist(),"lens_focal_length_px":f,"line_fits":fits,"width_m":width}


if __name__=="__main__":
    a=argparse.ArgumentParser()
    a.add_argument("photo",type=Path);a.add_argument("report",type=Path);a.add_argument("--width",type=float,default=8.8)
    args=a.parse_args();args.report.write_text(json.dumps(calibrate(args.photo,args.width),indent=2)+"\n")
