"""Independent first-hit checks on the delivered GLBs."""
import os,runpy
from pathlib import Path
from math import sin,cos,pi
from blackstone_portico import AXES,SPAN,RAIL_FOOT,RAIL_HEAD,RAIL_LEFT,RAIL_RIGHT,PANELS,front_y
p=Path(os.environ.get('SHANGHAI_PROJECT_ROOT',Path(__file__).resolve().parents[4]))
Reader=runpy.run_path(str(p/'data/audit/postal-office-v1/independent-glb-review-helpers.py'))['SerialScene']
def check(reader):
    samples=[]
    def probe(label,x,y,z,d,materials,limit=1.6):
        origin=[x,y,z]
        hit=reader.ray(origin,d,limit)
        passed=bool(hit and hit['material'] in materials) if materials else hit is None
        samples.append(dict(part=label,origin=origin,direction=d,wanted=materials,hit=hit,passed=passed))
    for x,y in AXES:
        for z in (.26,.75,1.38,2.21,2.99,3.24):
            probe('Smooth stone shaft',x,y-.82,z,[0,1,0],['shaft aggregate'])
        probe('Neck ring',x,y-.82,3.34,[0,1,0],['shadowed stone moulding'])
        probe('Square abacus',x,y-.82,3.76,[0,1,0],['dressed grey stone'])
        for k in (-1,0,1):
            a=-pi/2+k*.42;d=[-cos(a),-sin(a),0]
            probe('Capital bell and carved leaves',x+.67*cos(a),y+.67*sin(a),3.485,d,['dressed grey stone','carved pale stone'])
    for x in (.58,2.12,3.3,4.7):
        y=front_y(x)
        for z,m in [(3.842,'shadowed stone moulding'),(3.91,'dressed grey stone'),(4.01,'carved pale stone'),(4.095,'shadowed stone moulding'),(4.237,'carved pale stone'),(4.32,'carved pale stone'),(4.37,'dressed grey stone'),(5.26,'pale parapet')]:
            probe('Continuous curved fascia or cap',x,y-.86,z,[0,1,0],[m])
        if x==.58:
            probe('Projecting capital below the fascia',x,y+.1,3.26,[0,0,1],['carved pale stone'])
            probe('Visible underside beyond the east capital',1.25,front_y(1.25)+.1,3.26,[0,0,1],['soffit'])
        else:
            probe('Visible underside',x,y+.1,3.26,[0,0,1],['soffit'])
    for i in range(PANELS):
        width=(RAIL_RIGHT-RAIL_LEFT)/PANELS
        x0=RAIL_LEFT+i*width
        for u,z,materials,lab in [(.50,.50,['pale parapet'],'Saltire crossing'),(.045,.48,['pale parapet'],'Upright edge'),(.51,.80,[],'Open top light'),(.51,.20,[],'Open lower light')]:
            x=x0+width*u;y=front_y(x)
            probe(lab,x,y-.65,RAIL_FOOT+z*(RAIL_HEAD-RAIL_FOOT),[0,1,0],materials,1.0)
    for x in (1.08,2.14,3.08,4.28):
        for z in (.5,1.77,2.84):
            probe('Continuous open arcade',x,-1.05,z,[0,1,0],[],2.5)
    for x in (0.,5.593,6.236):
        probe('Post panel field',x,front_y(x)-.8,4.85,[0,1,0],['pale parapet'])
        probe('Post cap button',x,front_y(x)+.057,5.7,[0,0,-1],['carved pale stone'])
    return dict(passed=all(v['passed']for v in samples),samples=samples)
