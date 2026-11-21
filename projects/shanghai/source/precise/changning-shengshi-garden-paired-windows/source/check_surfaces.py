"""Check casement depth, external shutter blades, and the front iron guard against each mesh."""
from pathlib import Path
import os,runpy
from paired_windows import AXES,BASES,WIDTH,HEIGHT,STONE,GLASS,PALE,METAL,RENDER,SLAT,WOOD,IRON,LEAD

root=Path(os.environ.get('SHANGHAI_PROJECT_ROOT',Path(__file__).resolve().parents[4]))
Reader=runpy.run_path(str(root/'data/audit/postal-office-v1/independent-glb-review-helpers.py'))['SerialScene']

def check(reader):
    samples=[]
    def ray(name,x,z,materials,depth,tolerance=.02):
        origin=[x,-1,z];hit=reader.ray(origin,[0,1,0],3)
        if isinstance(materials,str):materials=[materials]
        ok=bool(hit and hit['material']in materials and abs(hit['distance_m']-depth-1)<tolerance)
        samples.append(dict(part=name,origin=origin,expected=materials,expected_depth=depth,tolerance=tolerance,hit=hit,passed=ok))
    for level,z in enumerate(BASES):
        for side,x in enumerate(AXES):
            for dx in (-.37,-.12,.13,.39):
                for dz in (.19,.67,1.08):ray('Individual glazing cell',x+dx,z+dz,[GLASS,PALE],.151)
            for dx,expected in ((-.251,.105),(0,.091),(.251,.105)):
                ray('Opening stile or glazing bar',x+dx,z+.76,METAL,expected)
            ray('Meeting horizontal rail',x+.13,z+.844,METAL,.101)
            ray('Casement sill',x+.19,z-.023,STONE,-.199)
            ray('Rendered-side return and jamb',x-.539,z+.72,STONE,-.044)
            ray('Shutter central cross rail',x-.71,z+.64,WOOD,-.101)
            ray('Inclined louvres',x-.71,z+.295,[WOOD,SLAT],-.084)
            if side==0:
                ray('Right-hand shutter side rail',x+.587,z+.95,WOOD,-.099)
            if level==1:
                ray('Cornice over upper casement',x+.13,z+HEIGHT+.13,STONE,-.175)
    for x in (-1.35,-.99,-.62,-.23,.18,.51,.92,1.29):
        ray('Double horizontal rails',x,1.934,IRON,-.402)
        ray('Bottom iron rail',x,1.705,IRON,-.402)
    for i in (1,4,8,13,19,23):
        x=-1.373+i*(2.746/24)
        ray('Rounded guard loop',x,1.992,IRON,-.392)
        ray('Open area inside loop',x,1.970,RENDER,0.)
    for x,z in ((-1.72,2.34),(1.72,2.10),(0,2.36),(1.75,3.40)):
        ray('Roughcast masonry',x,z,RENDER,0)
    ray('Half-round rain gutter',.46,4.174,LEAD,-.389,.045)
    return dict(passed=all(s['passed']for s in samples),samples=samples)
