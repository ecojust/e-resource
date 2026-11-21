"""Check the two clear openings, the soffits and every individually visible group of cut stones."""
from pathlib import Path
from math import sin, cos, radians
import os, runpy
from veranda import CENTRES, RADIUS, SPRING, TOP, X0, X1
here = Path(__file__).resolve().parent
project = Path(os.environ.get('SHANGHAI_PROJECT_ROOT', here.parents[3]))
Reader = runpy.run_path(str(project/'data/audit/postal-office-v1/independent-glb-review-helpers.py'))['SerialScene']
def check(scene):
    samples = []
    stone = ('grey dressed stone', 'granite facet in light', 'granite facet in shade')
    def sample(label, x, y, z, vector, expected, maximum=3):
        hit = scene.ray([x,y,z],vector,maximum)
        ok = (hit is None) if expected is None else bool(hit and hit['material'] in expected)
        samples.append(dict(part=label,origin=[x,y,z],direction=vector,expected=expected,hit=hit,passed=ok))
    for index, center in enumerate(CENTRES):
        for a in (23,55,82.9,90,97.1,126,153):
            angle = radians(a)
            for r in (RADIUS+.09,RADIUS+.19):
                sample(f'arch {index} separate grey stone at {a} degrees',center+r*cos(angle),-1,
                       SPRING+r*sin(angle),[0,1,0],stone)
        for a in (9,40,68,109,140,172):
            angle = radians(a);r = RADIUS+.09
            sample('render separating voussoirs',center+r*cos(angle),-1,SPRING+r*sin(angle),
                   [0,1,0],('rough cream render',))
            sample('sheltered arch reveal',center+.64*cos(angle),.26,SPRING+.64*sin(angle),
                   [cos(angle),0,sin(angle)],('warm intrados render',))
        for dx in (-.73,0,.73):
            for z in (.27,1.3,2.27):
                sample('open garden arcade',center+dx,-1,z,[0,1,0],None)
    for pier in (X0+.112,0,X1-.112):
        for z,name in ((.76,'rough cream render'),(SPRING-.096,'dark grey spring bed'),(3.72,'cream cornice')):
            sample('actual shared and terminal piers',pier,-1,z,[0,1,0],(name,))
        sample('stone supporting the spring',pier,-1,SPRING+.005,[0,1,0],stone)
        sample('sheltered side of structural pier',pier,1.1,.76,[0,-1,0],('warm intrados render',))
    for dx in (.22,-.43,1.02):
        sample('above the measured horizontal cornice',dx,-1,TOP+.065,[0,1,0],None)
    return dict(passed=all(s['passed'] for s in samples),samples=samples)
