"""Check all ten northeast lights, the circular windows, stonework, door and both gables of the University Auditorium."""
import argparse
import json
import hashlib
from pathlib import Path

import numpy as np

AUDIT=Path(__file__).resolve().parent
SAMPLES = [
    ('northeast upper light 1', 'south', -2.6449999999999996, 10.06, ('recessed grey green glass',), 0.31, 0.35),
    ('northeast lower light 1', 'south', -2.6449999999999996, 6.05, ('recessed grey green glass',), 0.31, 0.35),
    ('northeast upper light 2', 'south', -1.265, 10.06, ('recessed grey green glass',), 0.31, 0.35),
    ('northeast lower light 2', 'south', -1.265, 6.05, ('recessed grey green glass',), 0.31, 0.35),
    ('northeast upper light 3', 'south', 0.115, 10.06, ('recessed grey green glass',), 0.31, 0.35),
    ('northeast lower light 3', 'south', 0.115, 6.05, ('recessed grey green glass',), 0.31, 0.35),
    ('northeast upper light 4', 'south', 1.4949999999999999, 10.06, ('recessed grey green glass',), 0.31, 0.35),
    ('northeast lower light 4', 'south', 1.4949999999999999, 6.05, ('recessed grey green glass',), 0.31, 0.35),
    ('northeast upper light 5', 'south', 2.875, 10.06, ('recessed grey green glass',), 0.31, 0.35),
    ('northeast lower light 5', 'south', 2.875, 6.05, ('recessed grey green glass',), 0.31, 0.35),
    ('main gable stone spandrel', 'south', 0.35, 9.17, ('weathered pale stone',), -0.1, -0.06),
    ('inner gable stone mullion', 'south', 0.7, 11.04, ('weathered pale stone',), -0.1, -0.06),
    ('sloping arch outside centre lights', 'south', 3.38, 11.15, ('weathered pale stone',), -0.1, -0.06),
    ('main door wood panel', 'south', 0.28, 3.0, ('dark timber',), 0.74, 0.84),
    ('main door glazing', 'south', 0.62, 2.03, ('recessed grey green glass',), 0.69, 0.77),
    ('main entrance arch mould', 'south', 1.84, 2.15, ('weathered pale stone',), -0.2, -0.03),
    ('small highest vent', 'south', 0.11, 17.02, ('recessed grey green glass',), 0.31, 0.35),
    ('roundel glass at 3.11', 'west', 3.3499999999999996, 10.55, ('recessed grey green glass',), -8.24, -8.17),
    ('round stone jamb at 3.11', 'west', 4.24, 10.3, ('weathered pale stone',), -8.7, -8.57),
    ('roundel glass at 8.12', 'west', 8.36, 10.55, ('recessed grey green glass',), -8.24, -8.17),
    ('round stone jamb at 8.12', 'west', 9.25, 10.3, ('weathered pale stone',), -8.7, -8.57),
    ('paired upper light at 13.42', 'west', 14.36, 7.23, ('recessed grey green glass',), -8.24, -8.17),
    ('paired upper light at 18.76', 'west', 19.700000000000003, 7.23, ('recessed grey green glass',), -8.24, -8.17),
    ('paired upper light at 24.1', 'west', 25.040000000000003, 7.23, ('recessed grey green glass',), -8.24, -8.17),
    ('paired upper light at 29.44', 'west', 30.380000000000003, 7.23, ('recessed grey green glass',), -8.24, -8.17),
    ('paired upper light at 34.36', 'west', 35.3, 7.23, ('recessed grey green glass',), -8.24, -8.17),
    ('southwest central upper light', 'north', 0.21, 10.14, ('recessed grey green glass',), 36.84, 36.9),
    ('northwest three visible return bays', 'east', 28.62, 7.23, ('recessed grey green glass',), 8.16, 8.25),
    ('northern shared wall', 'east', 9.82, 8.18, ('red brick',), 8.5, 8.57),
    ('terracotta at middle of slope', 'top', 4.31, 12.51, ('burnt red roof tiles',), 16.9, 17.25),
    ('raised ridge', 'top', 0.027, 12.34, ('clay ridge cap',), 20.15, 20.29),
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
        doc={'model_id':'yangpu-hujiang-university-auditorium','script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'variants':variants}
        args.report.write_text(json.dumps(doc,ensure_ascii=False,indent=2)+'\n')
        print('Checked',sum(len(v['rays'])for v in variants),'first surfaces, across the northeast gable, twin circular windows, both long walls and ridge')
if __name__=='__main__':main()
