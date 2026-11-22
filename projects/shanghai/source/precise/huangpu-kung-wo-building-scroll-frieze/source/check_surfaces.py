"""Compare physical first hits across all three planes and the individual frieze faces."""
from pathlib import Path
import os,runpy
from gable import *
project=Path(os.environ.get('SHANGHAI_PROJECT_ROOT',Path(__file__).resolve().parents[4]))
Reader=runpy.run_path(str(project/'data/audit/postal-office-v1/independent-glb-review-helpers.py'))['SerialScene']
def check(reader):
    rows=[]
    def shoot(name,x,z,wall,material,side=0):
        angle=side*37*pi/180;pivot=side*.9
        xdisp=(x-pivot)*cos(angle)-wall*sin(angle)+pivot
        ydisp=(x-pivot)*sin(angle)+wall*cos(angle)
        direction=[-sin(angle),cos(angle),0];distance=1.40
        origin=[xdisp-direction[0]*distance,ydisp-direction[1]*distance,z]
        hit=reader.ray(origin,direction,2.1)
        rows.append(dict(part=name,origin=origin,direction=direction,material=material,hit=hit,passed=bool(hit and hit['material']==material and abs(hit['distance_m']-distance)<.005)))
    for side,centres in [(0,[-.433,.433]),(-1,[-1.33-j*.86 for j in range(4)])]:
        for cx in centres:
            shoot('Smooth shield centre',cx,Z_PANEL,-.115,EDGE,side)
            shoot('Circular frame',cx+.209,Z_PANEL,-.145,RELIEF,side)
            for dx in [-1,1]:
                for dz in [-1,1]:
                    shoot('Cast scroll at outer elbow',cx+dx*.326,Z_PANEL+dz*.111,-.149,RELIEF,side)
                    shoot('Plain square behind scroll',cx+dx*.274,Z_PANEL+dz*.041,-.104,FIELD,side)
            shoot('Lower straight rim',cx,3.095,-.132,RELIEF,side)
    for side,l,r in FACES:
        for x in [l+.31,(l+r)/2,r-.28]:
            shoot('Parapet capping',x,3.97,-.223,EDGE,side)
            shoot('Shelf underneath frieze',x,3.00,-.229,EDGE,side)
    for z in [.23,.69,1.15,1.61,2.07,2.53]:
        shoot('Incised joint across the centre pier',.21,z,-.011,SEAM);shoot('Pier face between two joints',-.14,z+.1,0,BRICK)
    for side,x in [(-1,-2.71),(1,1.29)]:
        shoot('Window vertical reveal',x-.051,1.91,-.069,EDGE,side);shoot('Dark glazing behind left reveal',x+.16,1.92,.304,GLASS,side);shoot('Window transom',x+.18,2.25,.177,SASH,side)
    return dict(passed=all(row['passed'] for row in rows),samples=rows)
