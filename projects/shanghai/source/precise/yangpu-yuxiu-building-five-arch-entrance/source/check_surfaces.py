"""Compare first visible surfaces across the uncompressed, web and distant geometries."""
from pathlib import Path
import os,runpy
from math import pi,sin,cos
from portal import BAYS,PIERS,SPRING,INNER,OUTER,RING,WEATHERED,BEAD,STONE,DARKSTONE,DOOR,GLASS,GRILLE,FLOOR,SHADOW
root=Path(os.environ.get('SHANGHAI_PROJECT_ROOT',Path(__file__).resolve().parents[4]))
Reader=runpy.run_path(str(root/'data/audit/postal-office-v1/independent-glb-review-helpers.py'))['SerialScene']
def check(reader):
    rows=[]
    def ray(name,x,z,mat,front):
        start=[x,-1.,z];hit=reader.ray(start,[0,1,0],4.)
        ok=bool(hit and hit['material']==mat and abs(hit['distance_m']-front-1)<.012)
        rows.append(dict(part=name,origin=start,expected=mat,expected_m=front+1,hit=hit,passed=ok))
    for i,x in enumerate(BAYS):
        for k in (1,3,5,7,9):
            a=(k+.5)*pi/11
            for radius,mat,front in [(1.119,WEATHERED if (k+2*i)%5 in (1,4) else RING,-.012),(1.24,BEAD,-.04)]:
                ray('Opening '+str(i+1),x+radius*cos(a),SPRING+radius*sin(a),mat,front)
    for x in PIERS:
        for z,mat,front in [(.22,DARKSTONE,-.054),(.95,STONE,-.012),(1.50,STONE,-.080),(1.81,STONE,-.025)]:
            ray('Pier and projecting band',x,z,mat,front)
    for x in BAYS[1:4]:
        for dx in (-.61,-.3,.0,.65):
            ray('Glazed leaves and meeting stile',x+dx,1.05,DOOR if dx==0 else GLASS,1.633 if dx==0 else 1.686)
        ray('Transom rail',x+.3,2.133,DOOR,1.637)
    for x in [BAYS[0],BAYS[-1]]:
        ray('Diamond edge',x+.14,2.03,GRILLE,1.657)
        ray('Diamond clear centre',x,2.17,GLASS,1.79)
        ray('Solid end wall',x,.80,SHADOW,1.72)
    ray('Continuous coping',.7,4.279,DARKSTONE,-.065)
    ray('Visible threshold',.4,.025,FLOOR,-.30)
    return dict(passed=all(v['passed']for v in rows),samples=rows)
