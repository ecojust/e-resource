"""Reopen the three mesh streams and measure materials and empty balcony openings."""
from pathlib import Path
from math import cos,sin
import os,runpy
root=Path(os.environ.get('SHANGHAI_PROJECT_ROOT',Path(__file__).resolve().parents[4]))
Reader=runpy.run_path(str(root/'data/audit/postal-office-v1/independent-glb-review-helpers.py'))['SerialScene']
def check(reader):
    rows=[]
    def front(label,x,z,material,limit=2.6,ymin=-.25,ymax=1.02):
        origin=[x,-1,z];hit=reader.ray(origin,[0,1,0],limit)
        ok=hit is None if material is None else bool(hit and hit['material'] in material and ymin<=hit['distance_m']-1<=ymax)
        rows.append(dict(part=label,origin=origin,direction=[0,1,0],hit=hit,material=material,limit=limit,passed=ok))
    for x in (-1.50,1.50):
        for z in (2.32,2.46,2.8,3.38,3.76):front('Turned column',x,z,['projecting pale stone'],ymax=.02)
        for z in (4.0,4.08,4.145):front('Capital blocks',x+.06,z,['grey aggregate stone'],ymax=.0)
    for x in (-1.55,-1.,-.40,0,.45,1.05,1.56):
        front('Stone coping',x,2.151,['projecting pale stone'],ymax=-.12)
        front('Front parapet base',x,.735,['grey aggregate stone'],ymax=-.12)
    for x in (-.365,.365):
        front('Bottom of circular band',x,1.33-.355,['ivory pierced balustrade'],ymax=0)
        front('Crossing at centre of circular band',x,1.33,['ivory pierced balustrade'],ymax=0)
        for d in (-.185,.185):front('Open area of circular band',x+d,1.33,None,1.17)
    for x in (-1.005,1.005):
        front('Cusped diamond centre',x,1.345,None,1.17)
        front('Cusped diamond bottom',x,1.33-.40,['ivory pierced balustrade'],ymax=0)
    for a in (.28,.65,1.18,1.57,1.97,2.50,2.86):
        front('Shallow archivolt nose',1.635*cos(a),4.52+1.635*sin(a),['projecting pale stone'],ymax=-.148)
        front('Barrel inner ring',1.52*cos(a),4.52+1.52*sin(a),['grey aggregate stone'],ymax=-.1)
    front('Blank shield',.025,5.04,['projecting pale stone'],ymin=.72,ymax=.77)
    for x in (-.62,.64):front('Bare lunettes beside shield',x,5.12,['recessed grey plaster'],ymin=.80)
    for x in (-2.10,2.10):
        front('Side-window mullion',x,3.15,['faded ivory joinery'],ymin=.84)
        front('Side-window glass',x+.125,3.13,['shaded leaded glass','reflected grey glass'],ymin=.96)
    for x in (-.85,-.52,-.19,.15,.5,.84):
        front('Glass in rear casements',x,3.38,['shaded leaded glass','reflected grey glass'],ymin=.96)
    return dict(passed=all(x['passed']for x in rows),samples=rows)
