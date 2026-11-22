"""Reconstruct the clipped-corner 1912—1936 plaque on the historic roof crown."""
from pathlib import Path
import json
import numpy as np
from shapely.geometry import Polygon

MEASUREMENTS=Path(__file__).resolve().parents[1]/'measurements/dated-cartouche-tracings.json'
CARRIER='Crown plaque | dark perimeter and return'
FIELD='Crown plaque | pale weathered face'
INK='Crown plaque | dark date strokes'


def finish(srgb, roughness):
    rgb=np.asarray(srgb,dtype=float)/255
    linear=np.where(rgb>.04045,((rgb+.055)/1.055)**2.4,rgb/12.92)
    return dict(color=linear.tolist(),roughness=roughness,metallic=0.0)


PALETTE={CARRIER:finish((57,51,48),.92),FIELD:finish((199,198,187),.87),INK:finish((36,36,34),.88)}


def reference_frame(layout=None):
    settings=(layout or {}).get('cartouche',layout or {})
    width=float(settings.get('width_m',1.))
    height=float(settings.get('height_m',.181*width))
    center_x=float(settings.get('center_x_m',0.))
    center_z=float(settings.get('center_z_m',0.))
    wall_y=float(settings.get('wall_y_m',0.))
    if not all(np.isfinite([width,height,center_x,center_z,wall_y])) or min(width,height)<=0:
        raise ValueError('The dated crown requires a positive, finite width and height.')
    return width,height,lambda u,v,d:(center_x+u*width,wall_y-d*width,center_z+v*height)


def add_cartouche(builder,lod=False,layout=None):
    data=json.loads(MEASUREMENTS.read_bytes())
    coarse=lod is True or lod=='lod'
    width,height,point=reference_frame(layout)
    def make_shape(ring,holes=()):
        # Simplify in a width-based physical metric, so the 1:5 elongated panel retains its serif tips.
        ratio=height/width
        p=Polygon([(x,z*ratio)for x,z in ring], [[(x,z*ratio)for x,z in r]for r in holes])
        p=p.simplify(.0018 if coarse else .00038,preserve_topology=True)
        return Polygon([(x,z/ratio)for x,z in p.exterior.coords],
                       [[(x,z/ratio)for x,z in r.coords]for r in p.interiors])
    border=make_shape(data['backing'])
    face=make_shape(data['face'])
    # The two photographs constrain the frontal return. Rear depth and the near-flush pigment treatment are estimates.
    builder.prism(border,-.004,.0135,point,CARRIER,'Dated crown | eight-sided dark return')
    builder.prism(face,.0133,.0165,point,FIELD,'Dated crown | pale panel and shallow arris')
    for glyph in data['glyphs']:
        surface=make_shape(glyph['outline'],glyph['counters'])
        index=glyph['position'];letter=glyph['character']
        name='date separator' if letter=='—' else 'numeral '+letter
        builder.prism(surface,.01648,.01680,point,INK,f'Dated crown | {index:02} {name}')
