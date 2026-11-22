"""Measure first mesh intersections through and around the vent, including the clear louver gaps."""
from pathlib import Path
from math import sin,cos,pi
import os,runpy
from gable_vent import BASE,BLADE_PITCH,SLATS,half_open
p=Path(os.environ.get('SHANGHAI_PROJECT_ROOT',Path(__file__).resolve().parents[4]))
Reader=runpy.run_path(str(p/'data/audit/postal-office-v1/independent-glb-review-helpers.py'))['SerialScene']
def check(reader):
    records=[]
    def ray(label,x,z,materials):
        origin=[x,-.25,z];hit=reader.ray(origin,[0,1,0],.55)
        passed=bool(hit and hit['material'] in materials) if materials else hit is None
        records.append(dict(part=label,origin=origin,direction=[0,1,0],wanted=materials,hit=hit,passed=passed))
    for i in range(SLATS):
        z=BASE+.015+BLADE_PITCH*i
        for u in (-.55,0,.55):
            ray('Inclined louver face '+str(i+1),u*half_open(z),z+.009,['dark louver face'])
            ray('Open gap between blades '+str(i+1),u*half_open(z+.039),z+.04,[])
    for i in range(19):
        t=pi*(i+.5)/19
        ray('Continuous spring and arch',.446*cos(t),.244+.43*sin(t),['worn rim'])
    for x in (-.43,-.28,0,.28,.43):ray('Flat sill',x,.116,['worn rim'])
    for x in (-.674,-.615,-.581,.574,.621,.659):
        for z in (.097,.381,.512,.753):ray('Red brick at reveal',x,z,['deep fired brick','red facing brick','sun-faded brick','brick joint'])
    ray('Unfilled crown above highest blade',0,.568,[])
    return dict(samples=records,passed=all(r['passed'] for r in records))
