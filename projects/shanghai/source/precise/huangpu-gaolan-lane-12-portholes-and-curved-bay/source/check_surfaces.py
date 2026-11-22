"""Verify the circular openings, raised rims, recessed glass and two distinct window sashes."""
import os,runpy
from pathlib import Path
from math import radians, sin,cos
from gable import *
project=Path(os.environ.get('SHANGHAI_PROJECT_ROOT',Path(__file__).resolve().parents[4]))
Reader=runpy.run_path(str(project/'data/audit/postal-office-v1/independent-glb-review-helpers.py'))['SerialScene']
def check(reader):
    samples=[]
    def record(name,origin,direction,mat,expected,tolerance=.004):
        result=reader.ray(origin,direction,3)
        samples.append(dict(part=name,origin=origin,direction=direction,expected_m=expected,material=mat,hit=result,passed=bool(result and result['material']==mat and abs(result['distance_m']-expected)<tolerance)))
    def front(label,x,z,mat,y):record(label,[x,-1.6,z],[0,1,0],mat,1.6+y)
    def radial(label,a,z,mat,r):
        x,y=xy(a,2.9);v=radians(a)
        record(label,[x,y,z],[-sin(v),cos(v),0],mat,2.9-r)
    for i,(lo,hi) in enumerate(OPENINGS):
        center=(lo+hi)/2;mat=PALE if i==0 else DARK
        for a in np.linspace(0,2*np.pi,12,endpoint=False):
            front('Raised circular stone surround',PORT+.56*np.cos(a),center+.56*np.sin(a),RIM,BACK-.086)
        for dx in [-.21,.06,.23]:
            for dz in [-.25,.16,.31]:front('Dark round window',PORT+dx,center+dz,ROUND,BACK+.146)
        for a in ANGLES:radial('Pale lower stile' if i==0 else 'Dark upper steel stile',a,lo+.805,mat,(RADIUS+.003)*cos(radians(1.03)))
        for a,c in zip(ANGLES,ANGLES[1:]):
            mid=(a+c)/2;ratio=cos(radians((c-a)/2))
            for z in [lo+.16,lo+.58,lo+.94]:
                radial('Recess in faceted glazing',mid,z,LOW_GLASS if i==0 else GLASS,(RADIUS-.092)*ratio)
            for z in ([hi-.46,hi-.048]if i==0 else [lo+.39,lo+.71,lo+1.04,lo+1.34]):
                radial('Projecting sash transom',mid,z,mat,(RADIUS-.007)*ratio)
    for x in [-.18,.1,.27]:front('Lower round sash crossbar',PORT+x,1.12+.005,DARK,BACK+.09)
    for lo,hi in [(0,.34),(1.9,3.21),(4.78,5.67)]:
        z=(lo+hi)/2
        for x in [-2.01,-1.57,-1.25]:front('Rendered strip adjacent to red bricks',x,z,RENDER,BACK-.08)
        for a in [-43.,-24.,0.,26.,38.]:
            x,y=xy(a,2.9);aa=radians(a);record('Curved rendered spandrel',[x,y,z],[-sin(aa),cos(aa),0],RENDER,2.9-RADIUS-.053,.007)
    return dict(samples=samples,passed=all(t['passed']for t in samples))
