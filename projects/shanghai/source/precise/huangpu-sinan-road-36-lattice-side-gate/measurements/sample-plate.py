"""Locate legible paint and enamel witness points on the 2018 address plaque."""
import argparse
import hashlib
import json
from pathlib import Path
import runpy

import numpy as np
from scipy.ndimage import distance_transform_edt

BOXES={'3':(97,30,188,210),'6':(201,24,293,210),'思':(78,220,142,292),
       '南':(155,215,226,297),'路':(238,214,312,295),'边':(319,195,346,231),'门':(346,195,374,231)}
BACKGROUND={'inside digit 6 upper':(247,122),'inside digit 6 lower':(249,152),
            'between numerals':(192,111),'between 思 and 南':(149,254),
            'between 南 and 路':(230,259),'above side inscription':(347,185),
            'lower margin':(178,302),'left margin':(36,112),'below 门':(362,242)}
def samples(rect):
    points=[]
    for group,(left,top,right,bottom) in BOXES.items():
        window=rect[top:bottom,left:right]
        red,green,blue=window.transpose(2,0,1)
        chroma=red-.35*green
        dark,light=np.percentile(chroma,[8,95])
        signal=(chroma-dark)/(light-dark)
        core=signal>.78
        core[[0,-1],:]=False;core[:,[0,-1]]=False
        depth=distance_transform_edt(core)
        yy,xx=np.indices(depth.shape)
        for i in range(4 if group in ('边','门') else 7):
            y,x=np.unravel_index(np.argmax(depth),depth.shape)
            if depth[y,x]<.9:break
            points.append(dict(group=group,expected='paint',pixel=[int(x)+left,int(y)+top],
                               rgb=rect[y+top,x+left].round().astype(int).tolist(),
                               paint_margin_px=round(float(depth[y,x]),3)))
            gap=(5.5 if group in ('边','门') else 13.)
            depth[(xx-x)**2+(yy-y)**2<gap*gap]=0
    for desc,(x,y) in BACKGROUND.items():
        points.append(dict(group=desc,expected='glaze',pixel=[x,y],rgb=rect[y,x].round().astype(int).tolist()))
    return points
if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('photo',type=Path);ap.add_argument('output',type=Path);ap.add_argument('--trace-script',type=Path,default=Path(__file__).with_name('trace-address.py'));a=ap.parse_args()
    lib=runpy.run_path(str(a.trace_script))
    rect,corners,_=lib['run'](a.photo);h,w=rect.shape[:2]
    coordinates=lib['homography']([(0,0),(w,0),(w,h),(0,h)],corners)
    points=samples(rect)
    for point in points:
        x,y=point['pixel'];q=coordinates@np.array([x+.5,y+.5,1.]);point['original_upright']=(q[:2]/q[2]).round(4).tolist()
    result=dict(photo_sha256=hashlib.sha256(a.photo.read_bytes()).hexdigest(),units='rectified samples and upright original pixel centres',source='Antigng, 2018-07-30, CC BY-SA 4.0',points=points)
    a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(len(points),sum(p['expected']=='paint' for p in points))
