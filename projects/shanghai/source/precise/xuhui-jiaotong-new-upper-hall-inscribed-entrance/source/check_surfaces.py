"""Measure entrance openings and the foremost modeled finish in three mesh streams."""
from pathlib import Path
import os
import runpy
root = (Path(os.environ['SHANGHAI_PROJECT_ROOT']) if 'SHANGHAI_PROJECT_ROOT' in os.environ else Path(__file__).resolve().parents[4])
Reader = runpy.run_path(str(root/'data/audit/postal-office-v1/independent-glb-review-helpers.py'))['SerialScene']

def check(reader):
    samples = []
    def probe(name, origin, direction, material, limit=4):
        hit = reader.ray(origin, direction, limit)
        passed = (hit is None) if material is None else bool(hit and hit['material']==material)
        samples.append(dict(part=name,origin=origin,direction=direction,wanted=material,hit=hit,passed=passed))
    def front(name,x,z,material):
        probe(name,[x,-1.7,z],[0,1,0],material)
    stone = 'dressed warm grey stone'
    for x in (-5.05,5.05):
        for z in (.86,2.43,3.88):front('Coursed pier',x+.24,z,stone)
        front('Lantern lens',x,3.32,'lamp glass')
        front('Stone cornice',x+.19,5.98,stone)
    front('East bronze plaque',5.02,1.69,'dark bronze')
    for x in (-1.53,-.53,.54,1.53):front('Bare limestone at plaque margin',x,5.417,'title panel limestone')
    front('Right edge of Xin brushstroke',-.79,5.31,'carved dark characters')
    front('Central red header',.32,3.20,'deep red door wood')
    front('Vertical plaque on eastern pier',1.25,2.28,'title panel limestone')
    front('Stroke of Shang',-.036,5.03,'carved dark characters')
    for x in (-3.0,-1.98,1.98,3.0):
        front('Door glazing',x+.09,2.49,'green grey glass')
        front('Door panel',x+.10,1.20,'deep red door wood')
    for x in (-2.5,0,2.5):
        front('Transom glass',x+.32,3.54,'green grey glass')
        front('Transom mullion',x+.69,3.53,'deep red door wood')
        front('Upper rear stone',x+.32,4.22,'shadowed grey stone')
    for x in (-1.25,1.25):front('Intermediate stone jamb',x,1.26,stone)
    for x in (-.73,0,.73):
        for z in (1.02,2.6):front('Open central passage',x,z,None)
    for idx in range(4):
        probe('Individual stair tread',[.19,-1.15+idx*.32,1.18],[0,0,-1],'weathered stair nosings')
    for x in (-3.67,3.67):front('Curved stone bracket',x,4.48,stone)
    return dict(samples=samples,passed=all(sample['passed'] for sample in samples))
