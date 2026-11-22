"""First visible surfaces of the courtyard and tiled entrance in the exported meshes."""
from pathlib import Path
import json
import runpy
import sys
import numpy as np
from shapely.geometry import Point,Polygon

HERE=Path(__file__).absolute().parent
SRC=HERE.parents[2]/'source/precise/huangpu-huanlong-nanchang-212-lane-front/source'
sys.path.insert(0,str(SRC))
from lane_212_fabric import E,R,MATERIAL,WHITE,RAIL,GREY,AIRER,STEEL,PAVING
from huanlong_photo_plane import on_wall,CALIBRATION
from scipy.optimize import brentq
inspect=runpy.run_path(HERE.parent/'central-reserve-bank-changshu-front-v1/verify-export.py')['inspect']

def probes():
    cases=[]
    def sight(label,source,target,materials,tolerance=.12):
        source,target=np.array(source),np.array(target)
        distance=float(np.linalg.norm(target-source))
        cases.append(dict(name=label,origin=source.tolist(),direction=((target-source)/distance).tolist(),length=distance+tolerance+.005,allowed=materials,range_m=[distance-tolerance,distance+tolerance]))
    projection=np.array(CALIBRATION['camera_matrices']['commons_2015'])
    eye=-np.linalg.solve(projection[:,:3],projection[:,3])
    for row in R:
        p=np.array([row[k] for k in ('upper_left','upper_right','lower_right','lower_left')])
        for t in (.25,.54,.78):
            u,v=((p[0]+p[1])*(1-t)+(p[2]+p[3])*t)/2
            at=on_wall(u,v,E['terrace_face_y'])
            sight(f"Upright {row['index']}, height fraction {t}",eye,at,[RAIL],.044)
    # The front portion between pickets must remain genuinely open.
    # Rays end before reaching objects on the setback terrace.
    for i,(r0,r1) in enumerate(zip(R,R[1:])):
        p=np.array([r0[k] for k in ('upper_right','lower_right')]+[r1[k] for k in ('upper_left','lower_left')]).mean(0)
        T=np.array(on_wall(*p,E['terrace_face_y']));a=T-[0,.24,0]
        cases.append(dict(name=f'Terrace open interval {i+1}',origin=a.tolist(),direction=[0,1,0],length=.31,allowed=None,range_m=None))
    for k in ('deck_fascia','lower_cornice'):
        shape=np.array(E[k])
        for t in (.11,.26,.48,.66,.83,.91):
            p=(1-t)*(shape[0]+shape[-1])/2+t*(shape[1]+shape[2])/2
            y=E['terrace_face_y']+.012 if k=='deck_fascia' else -.165
            target=on_wall(*p,y)
            sight(k+f' at {t}',np.array(target)-[0,.18,0],target,[WHITE],.021)
    measured=json.loads((SRC.parent/'measurements/retractable-airer.json').read_bytes())
    for a,r in enumerate(measured['rails']):
        u,v=next(pt for pt in r['observed']if pt[0]==3850)
        z=on_wall(3850,1466,-.53)[2];y=brentq(lambda depth:on_wall(u,v,depth)[2]-z,-1.3,0.)
        for u,v in r['observed']:
            tgt=np.array(on_wall(u,v,y))
            sight(f'Clothes rail {a+1} @ {u}',eye,tgt,[AIRER],.054)
    return cases

if __name__=='__main__':
    rows={name:inspect(Path(path),probes())for name,path in zip(('raw','full','lod'),sys.argv[1:4])}
    Path(sys.argv[4]).write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
    for role,row in rows.items():print(role,len(row['cases']),[(c['name'],(c['first_hit']or{}).get('material')) for c in row['cases']if not c['passed']])
    sys.exit(int(any(not r['passed']for r in rows.values())))
