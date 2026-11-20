"""Check the first visible material and signed front-facing surface on the auditorium, hipped gables, stair block and pavilion roofs."""
import argparse
import json
import hashlib
from pathlib import Path

import numpy as np

AUDIT=Path(__file__).resolve().parent
GLASS='blue grey glazing';TIMBER='brown roof timbers';STONE='cream limestone';RED='vermilion lacquer'
TILE='ochre glazed tile';ROLL='gold ridge tiles'
SAMPLES=[
    ('north central entry glazing','north',-.61,2.12,(GLASS,),5.88,5.99),
    ('north lateral entry glazing','north',-4.05,2.33,(GLASS,),5.88,5.99),
    ('north lateral timber door','north',2.55,.90,(TIMBER,),5.85,5.98),
    ('west stone pylon','north',-7.27,9.30,(STONE,),6.58,6.68),
    ('east stone pylon','north',6.49,9.30,(STONE,),6.58,6.68),
    ('red hall column','north',-2.56,9.32,(RED,),6.60,6.77),
    ('stone between arched openings','north',-2.55,2.20,(STONE,),6.68,6.79),
    ('west hall windows','north',-11.06,5.60,(GLASS,),5.88,6.00),
    ('east hall windows','north',11.73,9.75,(GLASS,),5.88,6.00),
    ('projecting hall canopy','north',-.47,13.11,(TILE,ROLL),6.72,7.24),
    ('covered east gallery','top',32.0,-3.02,(TILE,ROLL),14.87,15.18),
    ('western pavilion finial','top',-51.36,17.09,(ROLL,),18.98,19.12),
    ('eastern pavilion finial','top',51.29,18.51,(ROLL,),18.98,19.12),
    ('western pyramidal pavilion pitch','top',-51.2,19.9,(TILE,ROLL),16.63,16.88),
    ('eastern pyramidal pavilion pitch','top',54.19,18.54,(TILE,ROLL),16.56,16.82),
    ('outward-facing west upper gable panel','west',-3.12,18.46,(RED,),-17.13,-16.93),
    ('outward-facing east upper gable panel','east',-3.12,18.46,(RED,),15.04,15.21),
    ('southern stair projection glazing','south',2.73,7.62,(GLASS,),-23.81,-23.67),
    ('principal ridge','top',.14,-3.13,(ROLL,),19.92,20.09),
    ('western auditorium hip','top',-21.20,-3.1,(TILE,ROLL),16.11,16.36),
    ('eastern auditorium hip','top',18.23,-3.49,(TILE,ROLL),16.28,16.55)]
for i,x in enumerate(np.linspace(-.95-13.9,-.95+13.9,9)):
    SAMPLES.append((f'south dormer {i+1} recessed glazing','south',float(x)+.15,17.39,(GLASS,),-9.70,-9.57))
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
        doc={'model_id':'xuhui-medical-college-east-building-one','script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'variants':variants}
        args.report.write_text(json.dumps(doc,ensure_ascii=False,indent=2)+'\n')
        print('Checked',sum(len(v['rays'])for v in variants),'first surfaces, including both end gables, both pavilion finials and nine dormer windows')
if __name__=='__main__':main()
