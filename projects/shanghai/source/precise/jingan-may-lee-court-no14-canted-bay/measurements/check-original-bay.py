"""Fit the original garden photograph with six outer-envelope points; cast withheld pixels at actual GLBs.

Usage: python check-garden-photograph.py --source-dir PATH --output FILE RAW.glb [DECODED.glb ...]
Camera fitting uses only the six listed outer arrises and assumes projective imaging.
Pixel observations are hand-read from the published 690 × 821 photograph and stay independent
of the fitted points. Each result includes the exact first material and, when needed, a local offset.
"""
from pathlib import Path
import argparse
import hashlib
import json
import sys
import numpy as np
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--source-dir',type=Path,required=True)
parser.add_argument('--output',type=Path,required=True)
parser.add_argument('glbs',nargs='+',type=Path)
args=parser.parse_args()
sys.path.insert(0,str(args.source_dir))
from read_study import decode,hit
from garden_bay import BRICK,COPING,FLOOR,HEIGHT,GLASS,RAIL,STONE,LIP,SOFFIT,STEEL,MULLION
photo='https://s1.sinaimg.cn/mw690/001HIrzOzy7eMoPOZck90&690'
trials=[]
for x,y,upper,lower in [
    (-1.53,0,(395,308),(394,729)),(1.53,0,(505,359),(504,720)),(-1.53,1.52,(319,326),(322,716))]:
    for z,uv in [(HEIGHT,upper),(0,lower)]:trials.append(([x,y,z,1],uv))
design=[]
for p,uv in trials:
    p=np.array(p);u,v=uv
    design.extend([np.r_[p,0*p,-u*p],np.r_[0*p,p,-v*p]])
_,_,vectors=np.linalg.svd(design)
camera=vectors[-1].reshape(3,4)
eye=-np.linalg.solve(camera[:,:3],camera[:,3])
checks=[]
def points(label,material,pairs):
    checks.extend((label,material,p) for p in pairs)
points('Red-brick spandrels and piers','brick',[(351,505),(373,515),(424,510),(455,526),(491,523),(386,602),(402,418),(493,695)])
points('Individual panes of garden glass','glass',[(346,377),(362,395),(346,446),(362,446),(434,401),(462,424),(437,446),(344,582),(361,601),(345,637),(436,588),(462,608),(450,638)])
points('Buff stone jambs, lintels and sills','stone',[(331,407),(375,397),(331,617),(329,596),(417,432),(489,435),(416,626),(489,635),(350,667),(455,673)])
points('Terrace cap projects past brick','cap',[(341,326),(365,320),(447,336)])
categories={**{k:'glass' for k in GLASS},BRICK:'brick',STONE:'stone',LIP:'stone',COPING:'cap',SOFFIT:'cap',FLOOR:'paving',RAIL:'rail',STEEL:'steel',MULLION:'steel'}
def project(v):
    q=camera@v;return q[:2]/q[2]
def inspect_mesh(path):
    tri,names,_=decode(path)
    def cast(u,v):
        ray=np.linalg.solve(camera[:,:3],[u,v,1.])
        if ray@(-eye)<0:ray=-ray
        return hit(tri,names,eye,ray/np.linalg.norm(ray))
    results=[]
    for label,kind,(u,v) in checks:
        first=cast(u,v)
        exact=bool(first and categories[first[0]]==kind)
        nearest=(0,0) if exact else None
        if not exact:
            offsets=sorted([(x,y) for y in range(-3,4) for x in range(-3,4) if (0<x*x+y*y<=9)],key=lambda r:r[0]**2+r[1]**2)
            for dx,dy in offsets:
                other=cast(u+dx,v+dy)
                if other and categories[other[0]]==kind:
                    nearest=(dx,dy);break
        results.append({'observation':label,'pixel':[u,v],'expected':kind,'first_material':None if first is None else first[0],'first_point':None if first is None else first[1],'exact':exact,'nearest_matching_offset_up_to_3_pixels':nearest})
    return {'name':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'triangles':len(tri),'direct':sum(r['exact'] for r in results),'within_3px':sum(r['nearest_matching_offset_up_to_3_pixels'] is not None for r in results),'total':len(results),'checks':results}
result={'photo':photo,'photo_size':[690,821],'calibration':'Three arrises with their top and base; four window openings separately fitted to the two wall planes; the listed interior material samples were held out. Camera residuals are pixel distances.','calibration_controls':[{'model':p[:3],'observed':u,'fitted':project(p).tolist(),'pixel_residual':float(np.linalg.norm(project(p)-u))}for p,u in trials],'projection':camera.tolist(),'camera_position':eye.tolist(),'meshes':list(map(inspect_mesh,args.glbs))}
args.output.write_text(json.dumps(result,indent=2)+'\n')
print([(r['name'],r['direct'],r['within_3px'],r['total']) for r in result['meshes']])
