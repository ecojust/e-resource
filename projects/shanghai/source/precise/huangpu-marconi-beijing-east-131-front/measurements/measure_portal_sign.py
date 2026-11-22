"""Trace the visible enamel numerals and the smaller marks on Antigng's 2017 image."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

import cv2
import numpy as np
from PIL import Image, ImageOps
from shapely.geometry import box, mapping
from shapely.ops import unary_union

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'source'))
from marconi_photo_plane import CALIBRATION

def trace(photo):
    evidence=json.loads((HERE/'portal-photo-traces.json').read_text())
    sha=hashlib.sha256(photo.read_bytes()).hexdigest()
    if sha!=evidence['primary']['sha256']:
        raise ValueError('Expected the original 2017 file from Wikimedia Commons')
    im=np.asarray(ImageOps.exif_transpose(Image.open(photo)).convert('RGB'))
    u,v=np.meshgrid(np.arange(70,143),np.arange(358,406))
    x,z=u/245.-1.26,4.79-v/245.
    world=np.stack((x,np.full_like(x,.79),z,np.ones_like(x)),axis=-1)
    view=world@np.array(CALIBRATION['camera_matrices']['2017_front']).T
    sample=cv2.remap(im,(view[:,:,0]/view[:,:,2]).astype('float32'),
                     (view[:,:,1]/view[:,:,2]).astype('float32'),cv2.INTER_LINEAR)
    lum=sample@np.array([.33,.50,.17])
    active=(lum>128)&(v<392) | (lum>103)&(v>=392)
    n,ids,stats,_=cv2.connectedComponentsWithStats(active.astype('uint8'))
    outlines=[]
    for i in range(1,n):
        if stats[i,cv2.CC_STAT_AREA]<3:
            continue
        rows,cols=np.where(ids==i)
        shape=unary_union([box(x[r,c]-.5/245,z[r,c]-.5/245,x[r,c]+.5/245,z[r,c]+.5/245)
                           for r,c in zip(rows,cols)])
        shape=shape.buffer(.0016,quad_segs=2).buffer(-.0016,quad_segs=2).simplify(.0012)
        outlines.append(dict(field='numeral' if np.mean(rows)<34 else 'small street line',
                             samples=len(rows),outline=mapping(shape)))
    return dict(source=evidence['primary'],plane_y_m=.79,rectified_pitch_m=1/245,
                extraction='Native RGB remapped bilinearly; luminance of cream enamel sampled separately by line.',
                outlines=outlines)
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('photo',type=Path)
    p.add_argument('output',type=Path)
    a=p.parse_args()
    a.output.write_text(json.dumps(trace(a.photo),separators=(',',':'),ensure_ascii=False)+'\n')
