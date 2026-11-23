"""Trace the square/diamond medallions and adjacent genuine through-openings from the original garden cameras."""
import argparse
import hashlib
import json
import runpy
import sys
from pathlib import Path

import numpy as np
from register_court import Camera

HERE=Path(__file__).absolute().parent
PROJECT=next(p for p in HERE.parents if (p/'data/audit/postal-office-v1/independent-glb-review-helpers.py').is_file())
# Top-left, top-right, base-right and base-left of the respective stone fields, in each published image.
QUADS={
    ('05','left court balcony'):[[277,147],[461,202],[468,251],[271,211]],
    ('05','right court balcony'):[[561,234],[632,257],[637,283],[560,263]],
    ('commons','left court balcony'):[[375,378],[532,400],[531,447],[373,428]],
    ('commons','right court balcony'):[[650,418],[756,431],[753,465],[648,457]],
    ('commons','upper west bay'):[[204,187],[286,194],[283,237],[202,228]],
    ('10','upper west bay'):[[178,114],[227,120],[226,150],[176,143]]}
STONE={'Yihe | buff stone balcony','Yihe | weathered pale coping','Yihe | raised stone plaques'}

def projection(quad):
    a=[];b=[]
    for (x,y),(u,v)in zip([(0,0),(1,0),(1,1),(0,1)],quad):
        a.extend([[x,y,1,0,0,0,-u*x,-u*y],[0,0,0,x,y,1,-v*x,-v*y]])
        b.extend([u,v])
    return np.r_[np.linalg.solve(a,b),1].reshape((3,3))

def inspect(path):
    api=runpy.run_path(str(PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'))
    scene=api['SerialScene'](path)
    layout=json.loads((HERE/'balustrade-sections.json').read_bytes())
    rows=[]
    for (view,key),quad in QUADS.items():
        camera=Camera(view);data=layout[key];edge=np.array(data['plan'][:2])
        direction=edge[1]-edge[0];normal=np.r_[direction[1],-direction[0],0.]/np.linalg.norm(direction)
        target=np.r_[edge[0],0.]
        # The marks refer to material and empty fields of the photograph. The close lens
        # resolves individual apertures, while far views only support the gross medallion locations.
        if key=='upper west bay':
            marks=[('crossed lozenge centre',.295,.46,True),('circular plaque centre',.738,.46,True),
                   ('upper rail',.52,.065,True)]
            if view=='commons':marks.append(('open quarter of the circle',.795,.300,False))
        else:
            marks=[('circle 1',.124,.46,True),('diamond 1',.303,.46,True),
                   ('circle 2',.492,.46,True),('diamond 2',.676,.46,True),('circle 3',.856,.46,True)]
            if view=='05' and key=='left court balcony':
                marks.extend([('open sector of first ring',83/760,52/180,False),
                              ('open sector of central ring',387/760,52/180,False),
                              ('open triangle along first cross',180/760,67/180,False),
                              ('open triangle along second cross',472/760,65/180,False)])
        matrix=projection(quad)
        for label,x,y,solid in marks:
            uv=matrix@[x,y,1.];uv=np.rint(uv[:2]/uv[2]).astype(int)
            def probe(dx,dy):
                ray=camera.ray(uv+[dx,dy]);ray/=np.linalg.norm(ray)
                t=(target-camera.c)@normal/(normal@ray)
                point=camera.c+t*ray;depth=.25/abs(normal@ray)
                hit=scene.ray(point-ray*.18,ray,depth+.18)
                return hit
            nearest=None;initial=None
            for radius,dx,dy in sorted((np.hypot(i,j),i,j)for i in range(-4,5)for j in range(-4,5)if np.hypot(i,j)<=4):
                hit=probe(dx,dy)
                is_stone=hit is not None and hit['material']in STONE
                if radius==0:initial=hit
                if is_stone==solid:
                    nearest=dict(offset_px=[dx,dy],radius_px=radius,hit=hit);break
            rows.append(dict(photo=view,panel=key,mark=label,source_pixel=uv.tolist(),expected_stone=solid,
                             first=initial,nearest=nearest))
    exact=sum((r['first'] is not None and r['first']['material'] in STONE)==r['expected_stone']for r in rows)
    return dict(mesh_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),total=len(rows),exact=exact,
                within_four_px=sum(r['nearest'] is not None for r in rows),observations=rows)

if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('mesh',type=Path);cli.add_argument('out',type=Path)
    args=cli.parse_args();report=inspect(args.mesh);args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(report,indent=2)+'\n')
    print(report['exact'],report['within_four_px'],report['total'])
