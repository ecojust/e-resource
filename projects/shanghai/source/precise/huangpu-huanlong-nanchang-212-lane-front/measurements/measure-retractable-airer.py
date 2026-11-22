"""Read the three parallel hanging rails from their repeated highlights on Antigng's original."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from PIL import Image, ImageOps
from scipy.signal import find_peaks

def measure(photo,output):
    assert hashlib.sha256(photo.read_bytes()).hexdigest()=='6d2e2db453c82e94f11b0bc594e784bcf47689595c1de425afc5f71e1aac94ff'
    image=np.asarray(ImageOps.exif_transpose(Image.open(photo)).convert('L'))
    stations=[3805,3835,3850,3895,3910,4130,4145]
    lines=[[],[],[]]
    for x in stations:
        lo=round(1456-(x-3850)*.182)-4
        signal=image[lo:lo+36,x-2:x+3].mean(1)
        peaks,_=find_peaks(signal,prominence=35)
        groups=[k for k in peaks if lo+k<lo+32]
        if len(groups)!=3:raise ValueError((x,groups))
        for points,v in zip(lines,groups):
            points.append([x,int(lo+v)])
    runs=[]
    for i,points in enumerate(lines):
        a=np.array(points);slope,offset=np.polyfit(a[:,0],a[:,1],1)
        ends=[3678,4767] if i==0 else ([3688,4782] if i==1 else [3700,4794])
        runs.append(dict(ordinal=i+1,observed=points,line_y_per_u=float(slope),line_intercept=float(offset),
                         fit_rms_px=float(np.mean((a[:,1]-(a[:,0]*slope+offset))**2)**.5),
                         ends_xy=[[u,round(float(slope*u+offset),3)]for u in ends]))
    record=dict(photo='Antigng, Nanchang Road Lane 212, 2015-09-09, CC BY-SA 4.0',original_sha256=hashlib.sha256(photo.read_bytes()).hexdigest(),native_dimensions=[5312,2988],
                rails=runs,central_rail_projection_from_wall_m=.53,depth_note='Projection estimated from visible folded arms. Inner and outer rails are solved at a common height from the three observed highlights.',
                scissor_arm_attachments_u=[3706,4164,4765],scissor_extent_note='The central fitting shows the linked V-shaped returns below the rods; cables obscure the ends.')
    output.write_text(json.dumps(record,indent=2)+'\n')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('photo',type=Path);p.add_argument('output',type=Path);a=p.parse_args();measure(a.photo,a.output)
