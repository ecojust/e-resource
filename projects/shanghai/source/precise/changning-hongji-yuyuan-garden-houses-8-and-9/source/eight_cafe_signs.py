"""Raised commercial signs photographed on the north entrance of house 8 in 2023."""
import json
from pathlib import Path
from shapely import set_precision
from shapely.geometry import Polygon
from garden_fabric import paint, face
from house_eight_entrances import wall

DARK = 'Hongji 8 | dark enamel sign edges'
METAL = 'Hongji 8 | pale metal sign face'
RUST = 'Hongji 8 | oxide red plaque'
WORD = 'Hongji 8 | bronze cafe lettering'
PALETTE = {DARK: paint((43,35,30),.55,.36), METAL: paint((213,203,181),.53,.31),
           RUST: paint((129,69,47),.76,.18), WORD: paint((68,51,37),.60,.30)}


def add_signs(b, lod, layout):
    b.palette.update(PALETTE)
    data = Path(__file__).resolve().parents[1] / 'measurements/eight-cafe-sign-outlines.json'
    signs = json.loads(data.read_bytes())['signs']
    for label, sign in signs.items():
        plane = sign['plane']['value_m']
        north = sign['plane']['axis'] == 'X'
        if label == 'bull metal backing':
            outer, inner, material = -.007, .075, DARK
        elif label == 'bull face and cut stripe':
            outer, inner, material = -.021, -.004, METAL
        elif label == 'return plaque':
            outer, inner, material = 0., .069, RUST
        elif label.startswith('porch letter'):
            outer, inner, material = -.013, .030, WORD
        else:
            outer, inner, material = -.010, .002, METAL
        for rings in sign['metric_rings']:
            shape = Polygon(rings[0], rings[1:])
            if not shape.is_valid:
                shape = shape.buffer(0)
            tolerance = .0036 if lod else .00115
            shape = shape.simplify(tolerance, preserve_topology=True)
            # A diagonal contact between two photographed pixels has no
            # physical letter thickness. Trim these contacts before extrusion.
            shape = set_precision(shape.buffer(-.00075, join_style='mitre'), .0002)
            if shape.is_empty:
                continue
            if north:
                wall(b,shape,(plane,0.),(plane,-1.),outer,inner,material,'cafe '+label)
            else:
                face(b,shape,plane+outer,plane+inner,material,'8 | cafe '+label)
