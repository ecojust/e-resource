"""Measure the pairs of dark sashes, their uninterrupted fanlights, and the raised stone bands."""
import os,runpy
from pathlib import Path
from gable import STUCCO,SILL,SASH,GLASS,JOINT,RIDGE,REVEAL,HALF,FLOORS,CENTRES
project=Path(os.environ.get('SHANGHAI_PROJECT_ROOT',Path(__file__).resolve().parents[4]))
Reader=runpy.run_path(str(project/'data/audit/postal-office-v1/independent-glb-review-helpers.py'))['SerialScene']
def check(reader):
    rows=[]
    def sample(label,x,z,mat,depth,tol=.008):
        pos=[x,-1.,z];direction=[0,1,0];h=reader.ray(pos,direction,3)
        passed=bool(h and h['material']==mat and abs(h['distance_m']-1-depth)<tol)
        rows.append(dict(part=label,origin=pos,direction=direction,expected_material=mat,expected_distance=1+depth,hit=h,passed=passed))
    for z in FLOORS:
        for x in CENTRES:
            for side in (-1,1):
                for hi in (.22,.58,.88,1.30):
                    sample('Glazing in the paired openings',x+side*.26,z+hi,GLASS,.231)
                sample('Inner steel perimeter',x+side*(HALF-.063),z+.82,SASH,.154)
                sample('Wide stone edge of reveal',x+side*(HALF-.028),z+.82,REVEAL,.083)
            for hi in (.415,.749,1.097):
                sample('Main or secondary crossbar',x+.33,z+hi,SASH,.144)
            sample('Vertical member below transom',x,z+.22,SASH,.160)
            sample('Daylit upper light above ends of vertical',x,z+1.35,GLASS,.231)
        for x in (-1.40,-.68,0,.68,1.40):sample('Continuous shared sill between windows',x,z-.041,SILL,-.081)
        sample('Stone between paired frames',0,z+.7,STUCCO,.023)
    for x in [-1.83,1.83]:
        for z in [.1,1,1.9,2.52,3.6,4.8]:
            sample('Middle of vertical fillet',x,z,RIDGE,-.162,.008)
    for z in (2.18,2.43,2.68,2.92):
        for x in [-.59,0,.59]:
            sample('Stone spandrel joint',x,z,JOINT,.015)
            sample('Stone between joints',x,z+.065,STUCCO,.023)
    return dict(passed=all(row['passed'] for row in rows),samples=rows)
