"""Build four independent inscribed plaques including the real voids around the strokes."""
import json
from pathlib import Path
from shapely.geometry import Polygon,box
from shapely.ops import unary_union
ARGS=Path(__file__).resolve().parent.parent/'measurements/incised-name-sections.json'
BOUNDS=[(-.029,2.14,2.77),(-.030,1.53,2.08),(-.026,.89,1.44),(-.030,.24,.78)]
def add_plaques(b,stone,ink,lod):
    sections=json.loads(ARGS.read_bytes())['sections']
    for i,((x,bottom,top),rec)in enumerate(zip(BOUNDS,sections)):
        width=.55;zscale=(top-bottom)*.827
        def world(r):
            return [(x+width*(u-.5),bottom+.086*(top-bottom)+v*zscale)for u,v in r]
        outlines=[]
        for rings in rec['normalised_boundary_rings']:
            poly=Polygon(world(rings[0]),[world(r)for r in rings[1:]])
            if lod:poly=poly.simplify(.0060,preserve_topology=True)
            outlines.append(poly)
        cuts=unary_union(outlines)
        full=box(x-width/2,bottom,x+width/2,top)
        prefix=f'painted incision / plaque {i+1} {rec["character"]}'
        mapper=lambda x,z,out:(x,-out,z)
        b.prism(full.difference(cuts),.003,.047,mapper,stone,prefix+' outer stone')
        b.prism(cuts,.006,.040,mapper,ink,prefix+' recessed strokes')
