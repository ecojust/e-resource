"""Fit the west upper return to two photos, taking its inner edge at the main wall's west end."""
import json
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares
from register_court import Camera
HERE=Path(__file__).absolute().parent
# Starting at the southern inner corner, then outward and north along the west elevation.
MARKS={'commons':{'head':[[286,194],[204,187],[115,226]],'base':[[283,237],[202,228],[114,266]]},
       '10':{'head':[[227,120],[178,114],[124,143]],'base':[[226,150],[176,143],[123,169]]}}

def layout():
    c=Camera()
    result={}
    for k,section in c.data['balustrades'].items():
        a,b,y=section['x0'],section['x1'],section['y']
        result[k+' court balcony']=dict(plan=[[a,y],[b,y],[b,0],[a,0]],z0=section['base_z'],z1=section['top_z'],
                 panels=[[[0,1],'OXOXO'],[[3,0],'O'],[[1,2],'O']])
    inner=float(np.median([v[0]for v in c.data['outline_by_view_m'].values()]))
    def evaluate(t):
        outer,y0,y1,y2,top,base=t;points=[(inner,y0),(outer,y1),(outer,y2)]
        e=[]
        for name,record in MARKS.items():
            cam=Camera(name)
            for level,marks in record.items():
                z=top if level=='head'else base
                for p,uv in zip(points,marks):e.extend(cam.pixel([*p,z])-uv)
        return e
    fit=least_squares(evaluate,[-12.48,1.6,2.4,8.,12.07,10.70],loss='huber',f_scale=2.5)
    outer,y0,y1,y2,top,base=map(float,fit.x)
    result['upper west bay']=dict(plan=[[outer,y1],[inner,y0],[inner,y2],[outer,y2]],z0=base,z1=top,
                     panels=[[[0,1],'XO'],[[3,0],'OXOXO']])
    return result

if __name__=='__main__':
    (HERE/'balustrade-sections.json').write_text(json.dumps(layout(),indent=2)+'\n')
