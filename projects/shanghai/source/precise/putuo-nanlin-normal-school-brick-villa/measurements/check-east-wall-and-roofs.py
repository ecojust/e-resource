"""Read fixed photo rays, verify the two ridges, and check that the court is open to the sky."""
import argparse
import json
from pathlib import Path
import runpy
import sys
import numpy as np

HERE=Path(__file__).absolute().parent
sys.path.insert(0,str(HERE.parent/'source'))
from fabric import GRAY,RED,STONE,FRAME,GLASS,PROJECT,metric
from window_wall import LIGHT,FACING
from courtyard_roofs import TILE,CLAY,COURT,roof_survey,WIDTH
from nanlin_ornaments import balcony_eye

SCENE=runpy.run_path(str(PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'))['SerialScene']
PHOTO_MARKS=[
    ('grey facing brick',[GRAY],[(336,565),(721,548),(949,568),(1483,589),(1615,609),(1901,623)]),
    ('red horizontal band',[RED],[(408,613),(732,621),(1128,627),(1460,645),(1640,650),(1752,656)]),
    ('upper sashes and door lights',[GLASS,LIGHT],[(544,638),(799,609),(900,598),(1009,597),(1046,609),
                                                  (1194,605),(1390,608),(1544,647),(1690,624),(1813,601)]),
    ('arched red window heads',FACING,[(912,525),(1040,531),(1213,539),(1383,547),(1556,603),(1708,590),(1824,569)]),
    ('individual sills',[STONE],[(916,691),(1042,691),(1204,699),(1398,702),(1556,706),(1707,710),(1829,714)]),
    ('blind arch stone and shoulders',[STONE],[(222,539),(132,618),(298,617)]),
]


def inspect(path):
    seen=SCENE(path);eye=balcony_eye(metric)
    entries=[]
    for feature,materials,pixels in PHOTO_MARKS:
        for u,v in pixels:
            x,z=metric(u,v);hit=seen.ray(eye,np.array([x,0,z])-eye,120)
            entries.append(dict(feature=feature,pixel=[u,v],expected=materials,
                                first=hit,matched=bool(hit and hit['material'] in materials)))
    c,ridges=roof_survey();vertical=[]
    def roof(name,x,y,expected,interval):
        hit=seen.ray([x,y,22.],[0,0,-1],27.)
        ok=bool(hit and hit['material'] in expected and interval[0]<=hit['point_enu_m'][2]<=interval[1])
        vertical.append(dict(feature=name,xy_m=[round(x,4),round(y,4)],first=hit,accepted_z_m=interval,matched=ok))
    for x in np.linspace(c['south']+.30,c['north']-.30,3):
        for y in np.linspace(c['east']+.30,c['west']-.30,3):roof('open lightwell',x,y,[COURT],[-.12,.02])
    for side,x in ridges.items():
        for y in [2.5,7.5,12.5,18.5]:
            roof(side+' barrel ridge',x,y,[CLAY],[9.65,10.2])
    for name,x,y in [('river wing',14.5,2.5),('estate wing',16.1,18.4),
                     ('north outer slope',27.8,8.5),('south outer slope',3.1,13.5),
                     ('north inner slope',22.2,10.2),('south inner slope',8.8,12.2)]:
        roof(name,x,y,[TILE],[7.66,10.05])
    centers={'south':metric(602,297)[0],'north':metric(1873,357)[0]}
    comparison={k:{'photo_gable_x_m':v,'aerial_ridge_x_m':ridges[k],
                   'axis_difference_m':round(abs(v-ridges[k]),3)}for k,v in centers.items()}
    return dict(glb=seen.asset,photo_2016=entries,first_hits_correct=sum(e['matched'] for e in entries),
                photo_rays=len(entries),roof_rays=vertical,roof_checks_correct=sum(e['matched']for e in vertical),
                gables_and_ridges=comparison,perspective_eye_m=list(map(float,eye)))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output',type=Path);parser.add_argument('glb',nargs='+',type=Path)
    args=parser.parse_args();j={p.name:inspect(p) for p in args.glb}
    args.output.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n')
    print([(k,r['first_hits_correct'],r['photo_rays'],r['roof_checks_correct'],len(r['roof_rays']))for k,r in j.items()])
