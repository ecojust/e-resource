"""Street entrance at 129 Wukang Road, with the plaque and fittings seen in 2017/2026."""
import json
from pathlib import Path

from shapely.affinity import translate
from shapely.geometry import Point, Polygon, box
from shapely.ops import unary_union

WOOD = 'Wukang street door | deep red painted wood'
GREEN = 'address green'
SCRIPT = 'Wukang street plaque | pale enamel lettering'
PALETTE = {
    WOOD: {'color':[.064,.012,.010],'roughness':.70},
    GREEN: {'color':[.004,.079,.047],'roughness':.54},
    SCRIPT: {'color':[.61,.68,.54],'roughness':.68},
}
REFERENCES = Path(__file__).absolute().parent.parent/'measurements/street-door-fittings.json'

def rounded_box(x,z,width,height,radius):
    return box(x-width/2+radius,z-height/2+radius,
               x+width/2-radius,z+height/2-radius).buffer(radius,quad_segs=5)

def add_street_door(builder, facade, door, lod=False):
    # Street U=1.90 is the original rough-opening centre. Convert the
    # registered global coordinates to this directed facade's local abscissa.
    left,_,right,_=door.bounds
    offset=(left+right)/2-1.90
    def prism(shape,back,front,material,label):
        facade.prism(translate(shape,xoff=offset),back,front,material,label)

    facade.prism(door.buffer(-.015),-.09,-.045,WOOD,'red-arched-entry-leaf')
    # A barely projecting perimeter encloses the wide flush panel. It meets
    # the backing, including around the small raised ornament below the plaque.
    cx=1.956
    panel=box(1.615,.315,2.228,1.49).union(Point(cx,1.49).buffer(.268,quad_segs=20))
    cap=panel.difference(panel.buffer(-.006))
    prism(cap,-.047,-.041,WOOD,'border-of-flush-lower-panel')

    body=box(cx-.094,1.28,cx+.094,1.535)
    top=box(cx-.055,1.518,cx+.055,1.552).union(Point(cx,1.552).buffer(.054,quad_segs=16))
    crest=unary_union([body,top])
    prism(crest,-.046,-.039,WOOD,'rounded-head-small-escutcheon')
    prism(crest.difference(crest.buffer(-.009)), -.040,-.033,WOOD,'beaded-escutcheon-perimeter')
    # The bright narrow slot is distinct in the 2026 reference. Its central
    # opening is recessed and the rim and leaf meet along their backs.
    slot=rounded_box(1.960,1.204,.193,.022,.004)
    prism(slot,-.046,-.035,'brass fitting','letter-slot')
    prism(rounded_box(1.960,1.206,.168,.006,.002),-.036,-.033,'wrought iron','recess-of-letter-slot')
    prism(rounded_box(2.240,.844,.032,.170,.010),-.046,-.036,'wrought iron','right-handle-backplate')
    for z in (.778,.910):
        facade.line((2.24+offset,z,-.038),(2.24+offset,z,-.009),.006,'wrought iron',8,'pull-mount')
    facade.line((2.24+offset,.778,-.009),(2.24+offset,.910,-.009),.008,'wrought iron',10,'door-pull')

    # The plate's rear face meets the door face. Glyph outlines are recovered
    # from Antigng's dated photograph and kept as small closed enamel solids.
    # At the coarser level simplify only the strokes, keeping the counter of 9.
    plate=rounded_box(1.958,1.771,.185,.146,.004)
    prism(plate,-.046,-.035,GREEN,'129-address-plate')
    glyphs=json.loads(REFERENCES.read_text())['glyphs']
    for name, rings in glyphs.items():
        shape=Polygon(rings['exterior'],rings['holes'])
        if lod:
            shape=shape.simplify(.0013,preserve_topology=True)
        if not plate.covers(shape):
            raise ValueError(f'Lettering outside the measured address plate: {name}')
        prism(shape,-.0354,-.0340,SCRIPT,'address-numeral-'+name if name.isdigit() else 'plaque-'+name)
