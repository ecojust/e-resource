"""Model the 2014 museum inscription with separately editable replacement lettering."""
from pathlib import Path
import json
import numpy as np
from shapely.geometry import Polygon
from photo_architecture import Facade

WOOD='Brown board behind museum sign'
METAL='Patinated metal museum lettering'
PALETTE={WOOD:dict(color=[.20,.18,.21],roughness=.87),METAL:dict(color=[.25,.31,.38],metallic=.15,roughness=.73)}
def add_museum_sign(builder,lod,position,support_y):
    f=Facade(builder,(-1.,0.),(1.,0.),'Sign')
    y=support_y-.038
    quad=np.array([[273.,685.],[513.,695.],[514.,753.],[272.,747.]])
    def at(u,v):return (1-u)*(1-v)*quad[0]+u*(1-v)*quad[1]+u*v*quad[2]+(1-u)*v*quad[3]
    def xy(uv,d):
        x,_,z=position(*uv,d);return x,z
    f.prism(Polygon([xy(p,y)for p in quad]),-support_y,-y,WOOD,'museum board')
    glyphs=json.loads((Path(__file__).resolve().parents[1]/'measurements/museum-sign-lettering.json').read_bytes())['glyphs']
    layout=json.loads((Path(__file__).resolve().parents[1]/'measurements/museum-sign-layout.json').read_bytes())
    for i,g in enumerate(glyphs):
        entry=layout['characters'][i]
        assert entry['character']==g['char']
        letter=np.array(entry['source_quad_px'])
        for shape in g['shapes']:
            def ring(uvs):
                pts=[(1-u)*(1-v)*letter[0]+u*(1-v)*letter[1]+u*v*letter[2]+(1-u)*v*letter[3] for u,v in uvs]
                return [xy(pt,y-.013) for pt in pts]
            p=Polygon(ring(shape[0]),[ring(h)for h in shape[1:]])
            if lod:p=p.simplify(.001,preserve_topology=True)
            if p.is_valid and p.area>.00001:f.prism(p,-y,-y+.013,METAL,'sign character '+str(i+1)+' '+g['char'])
