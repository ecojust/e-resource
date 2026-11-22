"""Recompute three facade directions from architectural edges in the original oblique photograph."""
import argparse
import json
from pathlib import Path

import cv2
import numpy as np

HERE=Path(__file__).resolve().parent
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('oblique_photograph',type=Path)
parser.add_argument('output',type=Path)
args=parser.parse_args()
image=cv2.imread(str(args.oblique_photograph))
if image is None:raise ValueError('Cannot read original photograph')
h,w=image.shape[:2];assert (w,h)==(2867,4019)
camera=np.array(json.loads((HERE/'2016-two-window-cameras.json').read_bytes())['oblique']['P'])
scale=1/3
grey=cv2.cvtColor(cv2.resize(image,None,fx=scale,fy=scale),cv2.COLOR_BGR2GRAY)
lines=cv2.createLineSegmentDetector(cv2.LSD_REFINE_STD).detect(grey)[0].reshape(-1,4)/scale
polys=[[(34,190),(202,245),(210,542),(28,540)],[(237,47),(308,59),(331,524),(234,519)],[(322,67),(360,135),(380,507),(342,530)]]
directions=[]
for i,poly in enumerate(polys):
    mask=np.array(poly,dtype=np.float32)*np.array([w/442,h/620],dtype=np.float32)
    angles=[];weights=[];segments=[]
    for x,y,xx,yy in lines:
        middle=((x+xx)/2,(y+yy)/2);length=np.hypot(x-xx,y-yy)
        if length<45 or cv2.pointPolygonTest(mask,middle,False)<0 or abs(yy-y)>1.9*abs(xx-x):continue
        plane=camera[:,:3].T@np.cross([x,y,1.],[xx,yy,1.])
        bearing=(np.degrees(np.arctan2(plane[0],-plane[1]))+90)%180-90
        angles.append(bearing);weights.append(length);segments.append([float(v) for v in (x,y,xx,yy)])
    angles=np.asarray(angles);weights=np.asarray(weights);candidates=np.arange(-86,86,.25)
    scores=[weights[np.abs(angles-a)<2].sum() for a in candidates]
    dominant=candidates[np.argmax(scores)];accepted=np.abs(angles-dominant)<2.5
    directions.append(dict(plane=i,bearing_degrees_from_x=float(np.median(angles[accepted])),
        source='yicao-03',included_native_pixel_segments=[q for q,k in zip(segments,accepted)if k]))
reference=json.loads((HERE/'three-visible-wall-planes.json').read_bytes())
for candidate,stored in zip(directions,reference['linework']):
    assert abs(candidate['bearing_degrees_from_x']-stored['bearing_degrees_from_x'])<.05
args.output.write_text(json.dumps(directions,indent=1)+'\n')
