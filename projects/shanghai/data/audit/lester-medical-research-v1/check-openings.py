"""Check the first visible material and signed front-facing surface on the 2024 institute, restored lamp pedestals and flat roof."""
import argparse
import json
import hashlib
from pathlib import Path

import numpy as np

AUDIT=Path(__file__).resolve().parent
SAMPLES=[
    ('main double door', 'south', 0.34, 2.36, ('green bronze door',), 0.128, 0.258),
    ('polished portal', 'south', 1.87, 3.75, ('polished rose granite',), -1.085, -0.955),
    ('main steel tower glass', 'south', 0.24, 12.04, ('slate steel glazing',), -0.445, -0.315),
    ('western narrow side light', 'south', -5.59, 6.29, ('slate steel glazing',), -0.005, 0.125),
    ('central granite cap', 'south', 0.01, 18.94, ('buff granite', 'sand coloured bed joints'), -0.775, -0.645),
    ('narrow shoulder', 'south', 5.99, 16.23, ('buff granite', 'sand coloured bed joints'), -0.305, -0.175),
    ('west tower band', 'south', -2.38, 14.32, ('buff granite', 'sand coloured bed joints'), -0.912, -0.782),
    ('west lamp light', 'south', -2.77, 3.45, ('laminated lamp glass',), -2.685, -2.555),
    ('east lamp column', 'south', 2.86, 2.22, ('patinated copper', 'bronze rim'), -2.655, -2.525),
    ('main stair tread', 'top', 0.18, -2.47, ('grey granite foundation',), 0.054, 0.184),
    ('west lamp cap', 'top', -2.86, -2.35, ('patinated copper', 'bronze rim'), 3.615, 3.745),
    ('east lamp cap', 'top', 2.86, -2.35, ('patinated copper', 'bronze rim'), 3.615, 3.745),
    ('north courtyard wall', 'north', 2.8, 6.24, ('washed stone rear render',), 20.587, 20.717),
    ('west granite side elevation', 'west', 12.8, 14.12, ('buff granite', 'sand coloured bed joints'), -33.867, -33.737),
    ('east granite side elevation', 'east', 12.8, 14.12, ('buff granite', 'sand coloured bed joints'), 33.622, 33.752),
    ('east terrace', 'top', 24.21, 21.9, ('parapet gravel',), 14.878, 15.008),
    ('west roof clerestory', 'top', -13.15, 9.64, ('parapet gravel',), 16.968, 17.098),
    ('central service roof', 'top', 0.0, 12.18, ('parapet gravel',), 17.328, 17.458),
    ('grass elevation steel window -1', 'south', -9.002, 11.63, ('slate steel glazing',), 0.235, 0.365),
    ('grass elevation steel window 1', 'south', 9.342, 11.63, ('slate steel glazing',), 0.235, 0.365),
    ('grass elevation steel window -2', 'south', -12.923, 11.63, ('slate steel glazing',), 0.235, 0.365),
    ('grass elevation steel window 2', 'south', 13.263, 11.63, ('slate steel glazing',), 0.235, 0.365),
    ('grass elevation steel window -3', 'south', -16.746, 11.63, ('slate steel glazing',), 0.235, 0.365),
    ('grass elevation steel window 3', 'south', 17.086, 11.63, ('slate steel glazing',), 0.235, 0.365),
    ('grass elevation steel window -4', 'south', -20.764, 11.63, ('slate steel glazing',), 0.235, 0.365),
    ('grass elevation steel window 4', 'south', 21.104, 11.63, ('slate steel glazing',), 0.235, 0.365),
    ('grass elevation steel window -5', 'south', -24.825, 11.63, ('slate steel glazing',), 0.235, 0.365),
    ('grass elevation steel window 5', 'south', 25.165, 11.63, ('slate steel glazing',), 0.235, 0.365),
    ('grass elevation steel window -6', 'south', -28.816, 11.63, ('slate steel glazing',), 0.235, 0.365),
    ('grass elevation steel window 6', 'south', 29.156, 11.63, ('slate steel glazing',), 0.235, 0.365),
    ('west lamp cap beside narrower door', 'top', -34.73, 17.19, ('patinated copper', 'bronze rim'), 2.975, 3.105),
]
# In each projection X and Y are the chosen in-plane coordinates. Positive normal faces the observer.
DIRECTIONS={'south':((0,2),1,-1),'north':((0,2),1,1),'west':((1,2),0,-1),'east':((1,2),0,1),'top':((0,1),2,1)}
def first_contact(points,ids,names,direction,start,height):
    axes,depth,sign=DIRECTIONS[direction]
    x,y=axes
    visible=(points[:,:,x].min(1)<=start)&(points[:,:,x].max(1)>=start)&(points[:,:,y].min(1)<=height)&(points[:,:,y].max(1)>=height)
    sub=points[visible];materials=ids[visible]
    a,b,c=sub.transpose(1,0,2);u=b-a;v=c-a
    normal=np.cross(u,v)
    denom=u[:,x]*v[:,y]-v[:,x]*u[:,y];ok=abs(denom)>1.e-10
    p=start-a[:,x];q=height-a[:,y]
    ratio=np.divide(p*v[:,y]-q*v[:,x],denom,out=np.zeros(len(a)),where=ok)
    sigma=np.divide(u[:,x]*q-u[:,y]*p,denom,out=np.zeros(len(a)),where=ok)
    ok&=(ratio>=-1e-8)&(sigma>=-1e-8)&(ratio+sigma<=1.00000001)
    if not ok.any():return None,None,None
    positions=a[:,depth]+ratio*u[:,depth]+sigma*v[:,depth]
    k=np.flatnonzero(ok)[np.argmax(sign*positions[ok])]
    n=normal[k];return names[materials[k]],float(positions[k]),float(sign*n[depth]/np.linalg.norm(n))
def main():
    cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('--work',required=True,type=Path)
    cli.add_argument('--report',type=Path,default=AUDIT/'opening-rays.json');cli.add_argument('--preview',action='store_true')
    args=cli.parse_args();variants=[]
    for rec in json.loads((args.work/'delivered-decode.json').read_bytes()):
        tri=np.fromfile(rec['triangle_file'],np.float64).reshape(-1,3,3)[:,:,[0,2,1]]*[1,-1,1]
        ids=np.fromfile(rec['triangle_material_ids_file'],np.uint16);hits=[]
        for label,direction,x,y,target,low,high in SAMPLES:
            mat,depth,dot=first_contact(tri,ids,rec['material_names'],direction,x,y)
            valid=mat in target and low<=depth<=high and dot>.01
            if args.preview:print('OK'if valid else'FIX',rec['variant'],label,mat,depth,dot)
            else:assert valid,(rec['variant'],label,mat,depth,dot)
            hits.append({'feature':label,'view':direction,'plane_xy_m':[x,y],'first_depth_m':depth,'material':mat,'outward_normal_dot':dot})
        variants.append({'variant':rec['variant'],'sha256':rec['sha256'],'rays':hits})
    if not args.preview:
        doc={'model_id':'jingan-lester-medical-research-institute','script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'variants':variants}
        args.report.write_text(json.dumps(doc,ensure_ascii=False,indent=2)+'\n')
        print('Checked',sum(len(v['rays'])for v in variants),'first surfaces, including 12 independent steel window axes, the double doors, bronze lights and roof setbacks')
if __name__=='__main__':main()
