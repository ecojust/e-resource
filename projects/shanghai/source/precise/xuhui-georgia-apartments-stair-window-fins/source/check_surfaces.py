"""Verify the forward face, inset distance and material of every window light."""
from pathlib import Path
import os,runpy
root=Path(os.environ.get('SHANGHAI_PROJECT_ROOT',Path(__file__).resolve().parents[4]))
Reader=runpy.run_path(str(root/'data/audit/postal-office-v1/independent-glb-review-helpers.py'))['SerialScene']
def check(reader):
    tests=[]
    def front(label,x,z,wanted,depth):
        origin=[x*0.842491166990,-.7,z*0.756751055254];hit=reader.ray(origin,[0,1,0],1.5)
        passed=bool(hit and hit['material'] in wanted and depth[0]<=hit['distance_m']-.7<=depth[1])
        tests.append(dict(part=label,origin=origin,wanted=wanted,y_limits=depth,hit=hit,passed=passed))
    for x in (-1.31,0,1.31):
        for z in (.12,2.12,3.79,5.9,7.48):front('Continuous concrete fin',x,z,['pale cast cement'],[-.151,-.130])
    for x in (-.655,.655):
        for lo,hi in ((.28,3.28),(4.29,6.96)):
            pitch=(hi-lo-.114)/8;bottom=lo+.057
            for row in range(8):
                z=bottom+(row+.5)*pitch
                for dx in (-.18,.18):front('Recessed light',x+dx,z,['shaded glass','slate grey glass'],[.221,.231])
                front('Steel mullion',x,z,['weathered steel'],[.157,.167])
                if row<7:front('Steel cross rail',x+.14,bottom+(row+1)*pitch,['weathered steel'],[.139,.179])
            front('Perimeter steel',x+.418,lo+1.81,['weathered steel'],[.149,.160])
            front('Rendered reveal',x+.448,lo+1.87,['dark reveal'],[.020,.030])
            front('Sloping cement sill',x+.215,lo-.039,['sloping cement sill'],[-.081,-.067])
        for z in (.135,3.82,7.47):front('Rendered spandrel',x,z,['buff stair spandrel'],[-.005,.005])
    return dict(passed=all(i['passed']for i in tests),samples=tests)
