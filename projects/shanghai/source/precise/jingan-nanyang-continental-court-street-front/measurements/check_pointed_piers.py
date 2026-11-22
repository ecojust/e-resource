"""First-hit checks on every measured street pier, without a material prefilter."""
from pathlib import Path
import argparse
import hashlib
import json
import sys
import numpy as np

HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(HERE.parent/'source'),str(HERE.parents[1]/'xuhui-pathe-records-office/measurements/city-contact')]
from glb_triangles import SerialScene
from pointed_piers import STONE, SEAM, EDGE, BOWL, LEAF, RECESS, LOWER

def check(path):
    mesh=SerialScene(path)
    coord=json.loads((HERE/'street-frontage-layout.json').read_text())
    plan=np.array(coord['pier_tip_axes_m']);scale=coord['height_m']['tip']/18.35526679941441
    rows=[]
    for i,center in enumerate(plan):
        t=plan[min(11,i+1)]-plan[max(0,i-1)];t/=np.linalg.norm(t);n=np.array([-t[1],t[0]])
        def shot(feature,x,z,wanted,lo,hi,back=.58):
            pt=center+t*x*scale
            eye=np.r_[pt-n*.95,z*scale]
            hit=mesh.ray(eye,np.r_[n,0],.95+back)
            observed=(hit['distance_m']-.95)/scale if hit else None
            ok=bool(hit and hit['material'] in wanted and lo<=observed<=hi)
            rows.append(dict(station=i,feature=feature,transverse_m=x,height_m=z,expected_surface=wanted,
                             expected_d_interval_m=[lo,hi],first_material=hit['material'] if hit else None,
                             first_d_m=round(observed,4) if hit else None,passed=ok))
        for z in (6.43,8.31,10.89,13.09,16.72):
            for x in (-.391,.383):shot('stone face beside central rib',x,z,[STONE,SEAM],.248,.29)
        for z in (11.86,13.83,16.75,18.14):shot('projecting central ridge',0.,z,[STONE],-.012,.012)
        for x in (-.12,.12):shot('sloping shoulder alongside finial',x,17.79,[STONE],.025,.22)
        for x,z in [(-.24,10.48),(.24,10.48),(.0,10.337),(-.06,10.40),(.05,10.42)]:
            shot('dark terminal, rim and relief',x,z,[BOWL,LEAF],-.09,.27)
        if LOWER[i]:
            point,spring,sill,bottom,r=LOWER[i]
            mid=max((sill+spring)/2,4.51) if i<=3 else (sill+spring)/2
            joints=[3.176,3.542,3.918,4.290,4.665] if i<=6 else [3.178,3.564,3.944,4.326,4.707]
            if mid < point-.06:
                if min(abs(mid-z) for z in joints)<.004:
                    shot('measured midpoint falls in a recessed joint',0.,mid,[SEAM],.391,.402)
                else:
                    shot('floor of blind recess',0.,mid,[RECESS],.382,.395)
            for z in (4.45,4.51,4.55):
                shot('continuous blind recess behind street fascia height',0.,z,[RECESS],.382,.395)
            for z in joints[1:]:
                if max(sill,4.35 if i<=3 else 0.) < z < point-.07:
                    shot('incised transverse joint behind raised jamb',0.,z,[SEAM],.391,.402)
            if mid<spring:
                for side in (-1,1):shot('surviving raised jamb',side*(r+.019),mid,[EDGE],.223,.248)
            if i>=4:
                for frac in (.14,.55,.85,.97):
                    shot('tiers on sill',0.,bottom+(sill-bottom)*frac,[EDGE],.0,.272)
        else:
            shot('unobscured stone above historic shop-front screening',0.,4.85,[STONE,SEAM],.248,.29)
    return {'mesh_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'layout_sha256':hashlib.sha256((HERE/'street-frontage-layout.json').read_bytes()).hexdigest(),
            'passed':all(r['passed'] for r in rows),'count':len(rows),'samples':rows}

if __name__=='__main__':
    cli=argparse.ArgumentParser();cli.add_argument('mesh',type=Path);cli.add_argument('result',type=Path);a=cli.parse_args()
    doc=check(a.mesh);a.result.parent.mkdir(parents=True,exist_ok=True);a.result.write_text(json.dumps(doc,indent=1)+'\n')
    bad=[r for r in doc['samples'] if not r['passed']]
    print(doc['count'], 'first hits;',len(bad),'failures',bad[:3]);sys.exit(int(bool(bad)))
