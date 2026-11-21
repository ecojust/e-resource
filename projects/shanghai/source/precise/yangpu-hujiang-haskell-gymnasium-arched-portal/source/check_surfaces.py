"""Check each profile at the jamb and crown and the depth of the recessed door."""
from pathlib import Path
import os,runpy
from portal import COURSES,SPRING,RAIL,DOOR,GLASS,CUT,ASHLAR,SILL,height
root=Path(os.environ.get('SHANGHAI_PROJECT_ROOT',Path(__file__).resolve().parents[4]))
Reader=runpy.run_path(str(root/'data/audit/postal-office-v1/independent-glb-review-helpers.py'))['SerialScene']

def check(reader):
    rows=[]
    def ray(name,x,z,material,depth):
        start=[x,-1,z];hit=reader.ray(start,[0,1,0],3)
        ok=bool(hit and hit['material']==material and abs(hit['distance_m']-depth-1)<.01)
        rows.append(dict(part=name,origin=start,expected=material,expected_m=depth+1,hit=hit,passed=ok))
    for ro,ho,ri,hi,front,back,mat,name in COURSES:
        for side in (-1,1):
            for z in (.60,1.1,1.8,2.29):
                ray(name,side*(ro+ri)/2,z,mat,front)
        for x in (-.43,.0,.43):
            ray(name+' crown',x,(height(x/ro,ho)+height(x/ri,hi))/2,mat,front)
    for i in range(-3,4):ray('Transom glazing bar',i*.217,2.38,RAIL,.312)
    for i in range(-4,4):ray('Transom glass',(i+.5)*.217,2.38,GLASS,.361)
    for side in (-1,1):
        for z in (.76,1.63):ray('Recessed door leaf',side*.437,z,DOOR,.369)
        for z in (.11,1.35,1.97):ray('Door cross rail',side*.437,z,RAIL,.327)
        ray('Jamb cap',side*1.37,.45,CUT,-.106)
        ray('Plinth',side*1.37,.22,ASHLAR,-.072)
    ray('Threshold',0,.029,SILL,-.26)
    return dict(passed=all(v['passed']for v in rows),samples=rows)
