"""Check the three doors, three transoms, three upper lights, roundels, corner domes and rooftop pavilion in all three models."""
import argparse
import json
import hashlib
from pathlib import Path

import numpy as np

AUDIT=Path(__file__).resolve().parent
SAMPLES = [
    ('paired timber door 1', 'south', -2.8000000000000003, 1.78, ('brown timber doors',), 1.88, 2.0),
    ('arched door transom 1', 'south', -2.8600000000000003, 3.91, ('grey blue window glass',), 1.98, 2.04),
    ('upper arched glass 1', 'south', -2.89, 8.55, ('grey blue window glass',), 0.44, 0.5),
    ('upper radial centre bar 1', 'south', -3.14, 10.15, ('dark enamel window frame',), 0.28, 0.34),
    ('upper stone jamb 1', 'south', -1.7600000000000002, 8.62, ('off-white masonry trim',), 0.06, 0.1),
    ('paired timber door 2', 'south', 0.34, 1.78, ('brown timber doors',), 1.88, 2.0),
    ('arched door transom 2', 'south', 0.28, 3.91, ('grey blue window glass',), 1.98, 2.04),
    ('upper arched glass 2', 'south', 0.25, 8.55, ('grey blue window glass',), 0.44, 0.5),
    ('upper radial centre bar 2', 'south', 0, 10.15, ('dark enamel window frame',), 0.28, 0.34),
    ('upper stone jamb 2', 'south', 1.38, 8.62, ('off-white masonry trim',), 0.06, 0.1),
    ('paired timber door 3', 'south', 3.48, 1.78, ('brown timber doors',), 1.88, 2.0),
    ('arched door transom 3', 'south', 3.42, 3.91, ('grey blue window glass',), 1.98, 2.04),
    ('upper arched glass 3', 'south', 3.39, 8.55, ('grey blue window glass',), 0.44, 0.5),
    ('upper radial centre bar 3', 'south', 3.14, 10.15, ('dark enamel window frame',), 0.28, 0.34),
    ('upper stone jamb 3', 'south', 4.52, 8.62, ('off-white masonry trim',), 0.06, 0.1),
    ('corner roundel glazing 1', 'south', -6.989999999999999, 7.84, ('grey blue window glass',), 0.29, 0.35),
    ('corner roundel stone ring 1', 'south', -6.34, 7.61, ('off-white masonry trim',), -0.14, -0.09),
    ('corner roundel glazing 2', 'south', 7.45, 7.84, ('grey blue window glass',), 0.29, 0.35),
    ('corner roundel stone ring 2', 'south', 8.1, 7.61, ('off-white masonry trim',), -0.14, -0.09),
    ('round portico column -1.56', 'south', -1.5070000000000001, 3.0, ('deep green round columns',), -0.06, 0.01),
    ('round portico column 1.56', 'south', 1.613, 3.0, ('deep green round columns',), -0.06, 0.01),
    ('outermost granite step', 'top', 0.25, -1.13, ('grey stone sill and stair',), 0.09, 0.15),
    ('raised plaque ground', 'south', 0.0, 6.92, ('dark plaque ground',), -0.07, -0.035),
    ('gilt plaque frame', 'south', 2.34, 6.55, ('gold cupola and lettering',), -0.13, -0.075),
    ('projecting court soffit cornice', 'south', 0.22, 5.78, ('off-white masonry trim',), -0.3, -0.08),
    ('green corner dome 1', 'top', -6.609999999999999, 2.6, ('green corner domes',), 14.97, 15.28),
    ('green corner dome 2', 'top', 7.57, 2.6, ('green corner domes',), 14.97, 15.28),
    ('green corner dome 3', 'top', -5.9, 20.529999999999998, ('green corner domes',), 14.97, 15.28),
    ('green corner dome 4', 'top', 6.859999999999999, 20.529999999999998, ('green corner domes',), 14.97, 15.28),
    ('flat roof across the upper gallery', 'top', 3.19, 0.9, ('weathered flat roofing',), 11.55, 11.61),
    ('central gold canopy', 'top', 0.69, 12.62, ('gold cupola and lettering',), 18.2, 18.56),
    ('open central pavilion colonnade', 'south', 0.94, 14.93, ('light cream render',), 9.48, 10.48),
    ('clear air beneath canopy between columns', 'south', 0, 15.35, ('none',), 0, 0),
    ('central crescent finial', 'south', -0.16, 23.05, ('gold cupola and lettering',), 12.1, 12.2),
    ('west projecting middle bay', 'north', 0.2, 8.3, ('light cream render',), 27.48, 27.7),
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
            valid=(mat is None) if target==('none',) else (mat in target and low<=depth<=high and dot>.01)
            if args.preview:print('OK'if valid else'FIX',rec['variant'],label,mat,depth,dot)
            else:assert valid,(rec['variant'],label,mat,depth,dot)
            hits.append({'feature':label,'view':direction,'plane_xy_m':[x,y],'first_depth_m':depth,'material':mat,'outward_normal_dot':dot})
        variants.append({'variant':rec['variant'],'sha256':rec['sha256'],'rays':hits})
    if not args.preview:
        doc={'model_id':'huangpu-xiaotaoyuan-mosque-prayer-hall','script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'variants':variants}
        args.report.write_text(json.dumps(doc,ensure_ascii=False,indent=2)+'\n')
        print('Checked',sum(len(v['rays'])for v in variants),'first surfaces, across the courtyard, four domes and open central pavilion')
if __name__=='__main__':main()
