"""Render the installed mesh from the 2016 photo and report plane-fit residuals."""
import argparse
import ctypes
import hashlib
import json
from pathlib import Path
import runpy
import subprocess
import sys
import tempfile
from unittest.mock import patch

import numpy as np
from scipy.optimize import least_squares

HERE=Path(__file__).absolute().parent
sys.path.insert(0,str(HERE.parent/'source'))
from fabric import PROJECT,metric

PRECISE=PROJECT/'source/precise'
shared=runpy.run_path(str(PRECISE/'changning-hongji-yuyuan-garden-houses-8-and-9/measurements/render-garden-stations.py'))
renderer=shared['renderer']


def camera():
    # Three heights at five abscissae constrain the approximate plane camera.
    # The seven reserved points record how much the local plane chart differs
    # from a single pinhole photo. A 27 mm equivalent lens is recorded in EXIF.
    marks=np.array([(u,v)for u in (150.,500.,1010.,1490.,2045.)for v in (430.,630.,891.)])
    check=np.array([(220.,556.),(565.,600.),(908.,542.),(1210.,688.),(1392.,563.),(1703.,609.),(1831.,704.)])
    X=np.array([(*metric(u,v),1) for u,v in marks])
    def matrix(c):return np.r_[c,1.].reshape(3,3)
    def project(H,points):
        pix=H@points.T
        return (pix[:2]/pix[2]).T
    def residual(c):return (project(matrix(c),X)-marks).ravel()
    fit=least_squares(residual,[52,0,119,0,-56,1000,.002,0],x_scale='jac',max_nfev=800)
    H=matrix(fit.x)
    f=2144*27/36.
    K=np.array([[f,0,1072.],[0,f,712.],[0.,0.,1.]])
    hx,hz=np.linalg.solve(K,H[:,:2]).T
    hy=np.cross(hz,hx);hy/=np.linalg.norm(hy)
    scale=(np.linalg.norm(hx)+np.linalg.norm(hz))/2
    P=np.column_stack([H[:,0],K@hy*scale,H[:,1],H[:,2]])/scale
    predicted=project(H,np.array([(*metric(u,v),1)for u,v in check]))
    note={'plane_P':P.tolist(),'eye_m':np.linalg.solve(P[:,:3],-P[:,3]).tolist(),
          'calibration_rms_px':float(np.sqrt(np.mean(np.sum((project(H,X)-marks)**2,axis=1)))),
          'check_points':[{'pixel':p.tolist(),'projected':v.round(2).tolist(),'difference_px':round(float(np.linalg.norm(v-p)),2)}for p,v in zip(check,predicted)],
          'scope':'检验投影相机与原片局部砖皮图表的差异。建筑高度和进深按公开图像估计。'}
    return P,note


def eye_camera(eye,look,w,h,span):
    eye=np.array(eye,dtype=float);look=np.array(look,dtype=float)
    aim=look-eye;distance=np.linalg.norm(aim);aim/=distance
    right=np.cross(aim,[0,0,1]);right/=np.linalg.norm(right)
    up=np.cross(right,aim)
    focal=w*distance/span
    A=np.stack([right*focal+aim*w/2,aim*h/2-up*focal,aim])
    return np.column_stack([A,-A@eye])


def render(path,out,width):
    out.mkdir(parents=True,exist_ok=True)
    P,note=camera()
    parts=renderer.read_glb(path)
    light=np.array([-.36,-.58,.73],dtype='float32');light/=np.linalg.norm(light)
    azel=[float(np.degrees(np.arctan2(light[0],light[1]))%360),float(np.degrees(np.arcsin(light[2])))]
    report={'mesh_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'camera':note,'views':{}}
    with tempfile.TemporaryDirectory(dir=out) as temp:
        so=Path(temp)/'depth.so'
        subprocess.run(['cc','-shared','-fPIC','-O2',str(PRECISE/'huangpu-old-jiefu-nanjing-road-shopfront/measurements/northwest_raster.c'),'-lm','-o',so],check=True)
        corner=eye_camera([-29.,-34.,16.4],[11.6,8.8,4.5],1150,686,44.2)
        courtyard=eye_camera([-9.,-14.,43.5],[13.9,10.8,4.7],1000,808,43.2)
        views=[('whole-window-wall',P,[70,255,2144,1133]),('upper-sashes',P,[837,450,1933,767]),
               ('balcony-and-parapet',P,[159,255,1100,750]),('southeast-corner',corner,[0,0,1150,686]),
               ('court-and-roofs',courtyard,[0,0,1000,808])]
        for name,station,crop in views:
            projected=shared['projected_parts'](parts,station)
            with patch.object(renderer,'read_glb',return_value=projected):
                im,read=renderer.raster(path,ctypes.CDLL(str(so)),width,station,crop,light,azel)
            dest=out/(name+'.jpg');im.save(dest,quality=92,subsampling=0)
            report['views'][name]=dict(**read,projection=station.tolist(),sha256=hashlib.sha256(dest.read_bytes()).hexdigest())
    (out/'render-record.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('glb',type=Path);parser.add_argument('output',type=Path)
    parser.add_argument('--width',type=int,default=980)
    args=parser.parse_args();render(args.glb,args.output,args.width)
