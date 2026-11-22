"""Recover the mounted disk centres from the front survey using the published gate frame."""
import argparse
import json
from pathlib import Path
import runpy
import sys

import numpy as np
from PIL import Image,ImageDraw
from scipy.optimize import least_squares

SEEDS = [(194,142,35,34),(271,120,35,35),(352,111,35,35),(433,121,35,35)]
def locate(source,photo,methods):
    sys.path.insert(0,str(source))
    from photo_plane import position,project
    im=Image.open(photo)
    rgb=np.asarray(im.crop((104,45,498,209)),dtype=float)
    low,high=np.percentile(rgb,[3,95])
    rgb=((rgb-low)*220/(high-low)).clip(0,255)
    pieces=[]
    for i,(cx,cy,rx,ry)in enumerate(SEEDS):
        pars,observed,count=methods['fit'](rgb,(cx-104,cy-45,rx,ry))
        pars[:2]+=[104,45];observed+=[104,45]
        # Fit a circle on the shallow gate plane directly. Discard the few
        # fitted rays that fall on a bracket or the trees behind a disk.
        xyz=np.array([position(u,v,-.025)[[0,2]]for u,v in observed])
        x0,z0=position(*pars[:2],-.025)[[0,2]]
        def discrepancy(q):
            return np.linalg.norm(xyz-q[:2],axis=1)-q[2]
        sol=least_squares(discrepancy,[x0,z0,.315],loss='soft_l1',f_scale=.009)
        x,z,r=sol.x; perim=np.linspace(0,2*np.pi,161)
        proj=[project((x+r*np.cos(t),-.025,z+r*np.sin(t))).tolist()for t in perim]
        pieces.append(dict(character='重新小区'[i],radius_m=round(float(r),5),centre_xz_m=np.round([x,z],5).tolist(),centre_in_detail=project((x,-.025,z)).round(3).tolist(),ellipse_in_detail=pars.round(3).tolist(),
                           edge_reprojection_in_detail=np.round(proj,3).tolist(),observed_rim_pixels=observed.round(3).tolist(),number_of_rim_points=len(observed)))
    return pieces
if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    for key in ['source','photo','methods','output']:ap.add_argument('--'+key,required=True,type=Path)
    a=ap.parse_args();methods=runpy.run_path(a.methods)
    discs=locate(a.source,a.photo,methods)
    a.output.write_text(json.dumps(discs,ensure_ascii=False,indent=2)+'\n')
    im=Image.open(a.photo);draw=ImageDraw.Draw(im)
    for d in discs:
        draw.line([tuple(pt)for pt in d['edge_reprojection_in_detail']],fill='#52dec9',width=1)
        print(d['character'],d['centre_xz_m'],d['radius_m'],d['number_of_rim_points'])
    im.crop((125,60,490,195)).resize((730,270)).save(a.output.with_suffix('.jpg'),quality=90)
