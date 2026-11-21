"""Read model triangles and identify the foremost material at masonry, glass, timber and tile probes."""
from pathlib import Path
import os,runpy
from dormers import AXES,slope,DEPTH
p=(Path(os.environ['SHANGHAI_PROJECT_ROOT']) if 'SHANGHAI_PROJECT_ROOT' in os.environ else Path(__file__).resolve().parents[4])
Reader=runpy.run_path(str(p/'data/audit/postal-office-v1/independent-glb-review-helpers.py'))['SerialScene']

def check(reader):
    samples=[]
    def ray(label,origin,direction,materials,limit=3.):
        hit=reader.ray(origin,direction,limit)
        passed=bool(hit and hit['material'] in materials) if materials else hit is None
        samples.append(dict(part=label,origin=origin,direction=direction,wanted=materials,hit=hit,passed=passed))
    for x in AXES:
        for dx in (-.312,-.118,.117,.315):
            for z in (.265,.531,.774,.984):
                ray('Individual window light',[x+dx,-.7,z],[0,1,0],['weathered glazing'])
        for dx in (-.216,.216,0):
            ray('Vertical glazing bar or meeting stile',[x+dx,-.7,.58],[0,1,0],['stained casement timber'])
        for z in (.425,.679,.902):
            ray('Horizontal glazing bar',[x+.13,-.7,z],[0,1,0],['stained casement timber'])
        ray('Lower sill',[x+.32,-.7,.144],[0,1,0],['raised cream moulding'])
        for dx in (-.565,.565):
            ray('Jamb surround',[x+dx,-.7,.75],[0,1,0],['lime render'])
        ray('Architrave',[x+.516,-.7,.79],[0,1,0],['raised cream moulding'])
        ray('Lintel shadow',[x-.13,-.7,1.198],[0,1,0],['shaded cream fillet'])
        ray('Projecting bed mould',[x+.17,-.7,1.255],[0,1,0],['raised cream moulding'])
        ray('Pediment field',[x+.07,-.7,1.538],[0,1,0],['lime render'])
        ray('Raking moulding',[x+.31,-.7,1.89-.31*.446/.753-.026],[0,1,0],['raised cream moulding'])
        ray('Upper gable hood',[x+.21,.51,2.85],[0,0,-1],['ridge cover'])
        ray('Open sky outside gable',[x+.78,-.7,1.65],[0,1,0],[],1.18)
    for x in (-5.10,-2.48,-1.52,1.67,2.55,4.89):
        for y in (.11,.43,.68):
            ray('Clay tile pans',[x,y,slope(y)+.54],[0,0,-1],['terracotta','pale terracotta','burnt terracotta'])
        ray('Slope break cover',[x,DEPTH,2.35],[0,0,-1],['ridge cover'])
    return dict(samples=samples,passed=all(r['passed'] for r in samples))
