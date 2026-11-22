"""Check rays against glazing, engraving, frames, central jamb and divided cap."""
from pathlib import Path
import os,runpy
from gable import LEVELS,HALF_PANELS,GLASS,METAL,CAP,STONE
root=Path(os.environ.get('SHANGHAI_PROJECT_ROOT',Path(__file__).resolve().parents[4]))
Reader=runpy.run_path(str(root/'data/audit/postal-office-v1/independent-glb-review-helpers.py'))['SerialScene']
def check(reader):
    out=[]
    def beam(name,x,z,materials):
        origin=[x,-.8,z];hit=reader.ray(origin,[0,1,0],1.5)
        out.append(dict(part=name,origin=origin,direction=[0,1,0],expected_materials=materials,hit=hit,passed=(hit['material'] in materials) if hit else (materials==[])))
    for index,(base,g,top) in enumerate(LEVELS):
        for side,(left,right) in enumerate(HALF_PANELS):
            for i in range(1,7):
                x=left+(right-left)*i/7
                beam('lower pane',x,g+(top-g)*.39,[GLASS]);beam('steel transom',x,top-.23,[METAL])
            for z in (g+.11,(g+top)/2,top-.09):
                beam('central window stile',(left+right)/2,z,[METAL]);beam('outer jamb',-1.17 if side==0 else 1.17,z,[STONE])
            for k in (1,3,6,8):
                z=(base+.012+g-.025)/2;t=z-(base+.012-.12);x=left+k*.085
                direction=1 if (side==0)==(index%2==0) else -1
                for off,mat in [(0,'Dressed stone face between incisions'),(.0425,'Shaded stone in incisions')]:
                    at=x+direction*t+off
                    if left+.03<at<right-.03:beam('spandrel cutting',at,z,[mat])
    for x in (-.82,-.45,.45,.82):beam('raised head block',x,4.18,[CAP])
    beam('true central joint',0,4.19,[])
    return dict(passed=all(i['passed'] for i in out),samples=out)
