"""Check the first visible material and signed front-facing surface on the four school elevations and roof."""
import argparse
import json
import hashlib
from pathlib import Path

import numpy as np

AUDIT=Path(__file__).resolve().parent
SASH='grey green painted shutters';GLASS='smoke blue glass';BRICK='rubbed red brick';STONE='pale carved granite'
ROOF='slate roofing';FLASH='slate batten and flashings';BASE='grey granite';TIMBER='dark timber frames';DOOR='ochre door timber'
# Each camera faces straight toward the subject. Depth is the local world coordinate on that direction's axis.
SAMPLES=[
    ('south entrance leaf','south',.42,1.62,(DOOR,),.60,.86),
    ('south entrance light','south',.48,2.34,(GLASS,),.52,.87),
    ('south entrance keystone','south',0,4.10,(STONE,),-.38,-.10),
    ('central first-floor shutter','south',.42,7.48,(SASH,BASE),.10,.25),
    ('central upper round window','south',.43,12.95,(SASH,BASE),.10,.25),
    ('west central brick shaft','south',-2.35,8.31,(BRICK,),-.50,-.12),
    ('east central brick shaft','south',2.35,8.31,(BRICK,),-.50,-.12),
    ('west shaft pale capital','south',-2.35,14.49,(STONE,),-.58,-.10),
    ('east wing shutter recessed behind centre','south',13.9,7.58,(SASH,BASE),1.40,1.67),
    ('west wing shutter recessed behind centre','south',-13.9,7.58,(SASH,BASE),1.40,1.67),
    ('west end lower gable glass','south',-28.00,16.29,(GLASS,),.19,.33),
    ('east end lower gable glass','south',28.00,16.29,(GLASS,),.19,.33),
    ('south middle curved crest glass','south',.20,16.89,(GLASS,),.16,.29),
    ('south west triangular dormer glass','south',-12.83,15.68,(GLASS,),1.10,1.27),
    ('south east triangular dormer glass','south',13.12,15.68,(GLASS,),1.10,1.27),
    ('south upper small dormer glass','south',8.99,18.77,(GLASS,),3.21,3.47),
    ('north terrace return window','north',14.75,10.02,(GLASS,),22.65,23.10),
    ('north stone eave on stair riser','north',15.50,16.25,(FLASH,),23.22,23.43),
    ('north centre entrance leaf','north',.42,1.62,(DOOR,),23.12,23.47),
    ('north centre red shaft','north',-2.35,8.31,(BRICK,),24.16,24.62),
    ('roof west hip, outward face','west',12.04,20.17,(ROOF,),-32.0,-29.0),
    ('roof east hip, outward face','east',12.04,20.17,(ROOF,),29.0,32.0),
    ('upper south roof slope','top',3.5,7.13,(ROOF,FLASH),19.9,20.9),
    ('upper northern roof slope','top',3.5,17.18,(ROOF,FLASH),19.8,21.2),
    ('lower pitched roof toward courtyard','top',2.0,.65,(ROOF,FLASH),15.6,17.4),
    ('ridge','top',3.71,12.035,(FLASH,),22.32,22.42),
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
            axes,depth_axis,_=DIRECTIONS[direction]
            scale=(66.140/68.10,25.144/24.07,66.140/68.10)
            offset=(0,12.035*(1.0-scale[1]),0)
            x=x*scale[axes[0]]+offset[axes[0]]; y=y*scale[axes[1]]+offset[axes[1]]
            low=low*scale[depth_axis]+offset[depth_axis]; high=high*scale[depth_axis]+offset[depth_axis]
            mat,depth,dot=first_contact(tri,ids,rec['material_names'],direction,x,y)
            valid=mat in target and low<=depth<=high and dot>.01
            if args.preview:print('OK'if valid else'FIX',rec['variant'],label,mat,depth,dot)
            else:assert valid,(rec['variant'],label,mat,depth,dot)
            hits.append({'feature':label,'view':direction,'plane_xy_m':[x,y],'first_depth_m':depth,'material':mat,'outward_normal_dot':dot})
        variants.append({'variant':rec['variant'],'sha256':rec['sha256'],'rays':hits})
    if not args.preview:
        doc={'model_id':'xuhui-chongsi-building','script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'variants':variants}
        args.report.write_text(json.dumps(doc,ensure_ascii=False,indent=2)+'\n')
        print('Checked',sum(len(v['rays'])for v in variants),'first surfaces, including both end-hip normals and three dormer windows')
if __name__=='__main__':main()
