"""First-hit checks for both rings, the open mouths, springers, parapet and number plate."""
from pathlib import Path
from math import sin,cos,pi
import os,runpy
from arcade import *
project=Path(os.environ.get('SHANGHAI_PROJECT_ROOT',Path(__file__).resolve().parents[4]))
Reader=runpy.run_path(str(project/'data/audit/postal-office-v1/independent-glb-review-helpers.py'))['SerialScene']
def check(reader):
    rows=[]
    def test(label,origin,direction,expected,materials,tol=.025):
        hit=reader.ray(origin,direction,8)
        passed=(hit is None if expected is None else bool(hit and hit['material'] in materials and abs(hit['distance_m']-expected)<tol))
        rows.append(dict(part=label,origin=list(origin),direction=list(direction),expected_distance=expected,expected_materials=list(materials),tolerance=tol,hit=hit,passed=passed))
    for cx in CENTRES:
        for i in range(17):
            a=(i+.5)*pi/17
            test('Coursed exterior of stone ring',(cx+1.398*cos(a),-1,SPRING+1.398*sin(a)),(0,1,0),.968,[STONE])
            test('Reveal within open ring',(cx,.22,SPRING),(cos(a),0,sin(a)),RADIUS,[STONE,MORTAR],.015)
        for x in (-.57,0.,.57):
            for z in (.31,.83,1.28): test('Open air leading through arch',(cx+x,-1,z),(0,1,0),None,[])
    for x in (-3.,0.,3.):test('Imposts shared by two arches',(x,-1,1.106),(0,1,0),.925,[PALE])
    for x in (-2.52,-1.34,.71,1.65,2.63):
        test('Balcony ledge',(x,-1,2.935),(0,1,0),.861,[LEDGE])
        test('Rendered parapet',(x,-1,3.357),(0,1,0),.997,[PLASTER])
    test('Blue number plate',(-.14,-1,3.409),(0,1,0),.953,[ENAMEL])
    test('White number',(.011,-1,3.392),(0,1,0),.948,[NUMERAL])
    return dict(passed=all(x['passed']for x in rows),samples=rows)
