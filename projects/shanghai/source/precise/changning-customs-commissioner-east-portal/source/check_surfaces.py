"""Test the depth of the brick splay, curved canopy, staircase and rear door."""
from pathlib import Path
from math import pi,cos,sin,sqrt
import runpy,os
from portal import FRONT,REAR,ARCH,BACK_ARCH,DEPTH,SPRING,BACK_SPRING,BRICK,LIGHT,DEEP,JOINT,STONE,EDGE,SOFFIT,CORBEL,RENDER,BASE,STEP,WOOD,TRIM,METAL,NOSE
project=Path(os.environ.get('SHANGHAI_PROJECT_ROOT',Path(__file__).resolve().parents[4]))
Reader=runpy.run_path(str(project/'data/audit/postal-office-v1/independent-glb-review-helpers.py'))['SerialScene']
def check(r):
    rows=[]
    def test(part,p,d,dist,materials,tolerance=.025):
        hit=r.ray(p,d,10)
        passed=bool(hit and hit['material'] in materials and abs(hit['distance_m']-dist)<tolerance)
        rows.append(dict(part=part,origin=list(p),direction=list(d),expected_distance=dist,expected_materials=materials,tolerance=tolerance,hit=hit,passed=passed))
    for t in (.14,.34,.56,.87):
        rad=FRONT+(REAR-FRONT)*t
        for sign in (-1,1):
            for z in (.88,1.46,1.72):test('Splayed brick cheek',(0,t*DEPTH,z),(sign,0,0),rad,[BRICK,LIGHT,DEEP,JOINT])
        top=ARCH+(BACK_ARCH-ARCH)*t;zc=SPRING+(BACK_SPRING-SPRING)*t
        for a in (.18*pi,.29*pi,.39*pi,.49*pi,.61*pi,.72*pi,.82*pi):
            x=rad*cos(a);dz=top*sin(a);length=sqrt(x*x+dz*dz);test('Radial brick on tapered intrados',(0,t*DEPTH,zc),(x/length,0,dz/length),length,[BRICK,LIGHT,DEEP,JOINT])
    for sign in (-1,1):
        test('Round handrail crossing the wall probe',(0,.5544,1.32),(sign,0,0),.826,[METAL],.012)
    for a in (.08*pi,.22*pi,.35*pi,.5*pi,.64*pi,.78*pi,.92*pi):
        x=(FRONT+.034+.055)*cos(a);z=SPRING+(ARCH+.015+.055)*sin(a)
        test('Front bead of arch hood',(x,-1.2,z),(0,1,0),.514,[EDGE],.04)
    for x in (-1.31,1.31):
        test('Stone impost',(x,-1.2,2.844),(0,1,0),.481,[EDGE],.02)
        test('Curved corbel toe',(x,-1.2,1.84),(0,1,0),1.024,[CORBEL])
    for z,y in ((.035,-.89),(.164,-.72),(.293,-.55),(.422,-.42),(.551,-.31)):
        test('Curved tread centre',(0,y,1),(0,0,-1),1-z,[STEP,NOSE],.012)
    for x,z in ((-1.60,3.58),(1.57,3.69),(-.78,4.25),(.79,4.25)):
        test('Pebble-dashed wall',(x,-1.20,z),(0,1,0),1.20,[RENDER])
    for x in (-.31,.32):
        for z in (.9,1.55,1.99):
            test('Dark door surface',(x,-1.20,z),(0,1,0),2.505,[WOOD])
    return dict(passed=all(a['passed']for a in rows),samples=rows)
