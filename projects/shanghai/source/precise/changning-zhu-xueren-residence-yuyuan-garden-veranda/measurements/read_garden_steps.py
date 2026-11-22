"""Digitize the five stone nosings in Gao 88 photograph 08 at its original size."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image

HERE=Path(__file__).resolve().parent


def read(photo):
    ref=json.loads((HERE/'south-veranda-depth-and-third-camera.json').read_bytes())
    if hashlib.sha256(photo.read_bytes()).hexdigest()!=ref['camera_sha256']:
        raise ValueError('The tracing requires original photograph 08')
    camera=np.asarray(ref['camera_08'])
    values=np.asarray(Image.open(photo).convert('RGB')).mean(axis=2)
    rows=[]
    # Sample only the visible stone, avoiding the planter on the left and the
    # return of the upper landing on the right. End points are silhouette reads.
    for level,(cy,interval,endpoints) in enumerate([
        (463,(260,549),(225,561)),(443,(273,533),(247,548)),
        (425,(291,518),(270,527)),(408,(318,488),(283,498)),
        (392,(320,460),(307,474))],start=1):
        height=.14*level
        transform=camera[:,[0,1,3]].copy()
        transform[:,2]+=height*camera[:,2]
        def floor(pixel):
            xyz=np.linalg.solve(transform,[*pixel,1])
            return xyz[:2]/xyz[2]
        pixels=[]
        for x in range(*interval,5):
            guess=round(cy-5.8*((x-395)/100)**2)
            col=values[guess-4:guess+5,x-2:x+3].mean(axis=1)
            edge=np.argmax(col[:-1]-col[1:])
            if col[edge]-col[edge+1]>45:
                pixels.append([x,float(guess-4+edge+.5)])
        world=np.asarray([floor(p) for p in pixels]);curve=np.polyfit(world[:,0]-9.35,world[:,1],2)
        predicted=np.polyval(curve,world[:,0]-9.35)
        xs=[]
        for u in endpoints:
            # Intersect the pixel-column plane with the traced horizontal arc.
            projected=(camera[0]-u*camera[2])
            poly=np.poly1d(curve)(np.poly1d([1.,-9.35]))*projected[1]
            poly+=np.poly1d([projected[0],height*projected[2]+projected[3]])
            xs.append(float(min(np.roots(poly),key=lambda x:abs(x-9.35))))
        rows.append(dict(level=level,z=height,photo_pixels=pixels,silhouette_x_px=list(endpoints),
                         extent_x_m=xs,arc_mid_x_m=9.35,coefficients_y_of_x=curve.tolist(),
                         rms_y_m=float(np.mean((predicted-world[:,1])**2)**.5)))
    return dict(photograph=ref['camera_file'],sha256=ref['camera_sha256'],steps=rows,
                method='逐级读取亮色踏面向暗色立面的落差，按标定相机在各级水平面交会，拟合平面弧线。最外侧端点有花台及盆栽遮挡。五级等高为模型假定。')


if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('original',type=Path);ap.add_argument('out',type=Path)
    args=ap.parse_args();args.out.write_text(json.dumps(read(args.original),ensure_ascii=False,indent=1)+'\n')
