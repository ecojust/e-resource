"""Check the voids, radial stone, mouldings, curved brackets and pierced returns in the exported mesh."""
import os,runpy
from math import pi,sin,cos
from pathlib import Path
from gable import STONE,CAP,TRIM,PIER,SUPPORT,CENTRES,FRONT,MID,END
project=Path(os.environ.get('SHANGHAI_PROJECT_ROOT',Path(__file__).resolve().parents[4]))
Reader=runpy.run_path(str(project/'data/audit/postal-office-v1/independent-glb-review-helpers.py'))['SerialScene']
def check(reader):
    rows=[]
    def sample(name,origin,direction,material,limit=1.2):
        hit=reader.ray(origin,direction,limit)
        ok=not hit if material is None else bool(hit and hit['material']==material)
        rows.append(dict(part=name,origin=origin,direction=direction,expected_material=material,hit=hit,passed=ok))
    for x in CENTRES:
        for i in range(8):
            angle=2*pi*i/8+pi/8
            sample('Pierced aperture', [x+.151*cos(angle),-1.6,MID+.151*sin(angle)],[0,1,0],None,.74)
            angle-=pi/8
            sample('Radiating stone',[x+.151*cos(angle),-1.6,MID+.151*sin(angle)],[0,1,0],STONE)
        sample('Centre of stone rosette',[x,-1.6,MID],[0,1,0],STONE)
        sample('Continuous handrail',[x,-1.6,2.142],[0,1,0],CAP)
        sample('Floor projecting edge',[x,-1.6,1.547],[0,1,0],CAP)
    for x in (-END,END):
        sign=1 if x>0 else -1
        for y in (-.728,-.269):
            for dx,dz,mat in [(0,0,STONE),(.143*.88*cos(pi/8),.143*sin(pi/8),None)]:
                sample('Pierced short return',[x+sign*.32,y+dx,MID+dz],[-sign,0,0],mat,.50)
        for z in (.3,.71,1.12):
            sample('Curved console on flank',[x+sign*.4,-.10,z],[-sign,0,0],SUPPORT,.62)
        sample('Raised face of post',[x,-1.55,1.84],[0,1,0],TRIM)
        sample('Corner post coping',[x,-1.55,2.26],[0,1,0],CAP)
    return dict(passed=all(row['passed'] for row in rows),samples=rows)
