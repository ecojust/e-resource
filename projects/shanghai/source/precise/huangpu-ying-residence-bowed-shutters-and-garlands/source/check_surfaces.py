"""Check the bent facade and back of the open balustrade against both decoded mesh levels."""
from pathlib import Path
import os,runpy
from math import sin,cos
from gable import curved,RADIUS,STONE,CAST,SASH,SHADE,BALUSTER,RELIEF,swag_z
project=Path(os.environ.get('SHANGHAI_PROJECT_ROOT',Path(__file__).resolve().parents[4]))
Reader=runpy.run_path(str(project/'data/audit/postal-office-v1/independent-glb-review-helpers.py'))['SerialScene']

def check(reader):
    rows=[]
    def probe(name,u,z,material,y0,tol=.01):
        origin=curved(u,-1,z);direction=[-sin(u/RADIUS),cos(u/RADIUS),0.]
        hit=reader.ray(origin,direction,3)
        ok=(hit is None if material is None else hit and hit['material']==material and abs(hit['distance_m']-(1+y0))<tol)
        rows.append(dict(part=name,origin=origin,direction=direction,expected_material=material,expected_distance=1+y0 if y0 is not None else None,hit=hit,passed=bool(ok)))
    for u in [-1.47,-1.16,-.63,-.31,.23,.59,1.11,1.48]:
        probe('Bowed spandrel',u,.33,STONE,0)
        probe('Rounded window sill',u,1.195,CAST,-.083)
        probe('Deep cornice',u,3.454,CAST,-.22)
        probe('Stone handrail',u,4.057,STONE,-.168)
    for u in [-1.54,0,1.54]:
        probe('Ribbon knot',u,.889,RELIEF,-.117)
    for a,c in [(-1.54,0),(0,1.54)]:
        for t in [.08,.5,.92]:
            probe('Garland loop',a+(c-a)*t,swag_z(t),RELIEF,-.09,.022)
    for u in [-1.662,-.887,.887,1.662]:
        for z in (1.64,2.1,2.9):
            probe('Shutter leaf edge and centre meeting stile',u,z,SASH,.064,.013)
    for u in [-1.19,-.48,.39,1.38]:
        probe('Wide pale transom above the shutters',u,2.637,STONE,-.005)
    for u in [-1.47,-1.237,-.922,-.61,-.297,.297,.61,.922,1.237,1.47]:
        probe('Rounded swelling of balcony baluster',u,3.756,BALUSTER,-.078,.01)
    for u in [-1.33,-1.06,-.77,-.44,.44,.77,1.06,1.33]:
        probe('Open daylight between balusters',u,3.80,None,None)
    return dict(passed=all(sample['passed'] for sample in rows),samples=rows)
