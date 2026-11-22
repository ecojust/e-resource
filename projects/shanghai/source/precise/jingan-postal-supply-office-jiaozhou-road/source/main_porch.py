"""Stone surround and projecting canopy on the historical Jiaozhou Road elevation."""
import json
from pathlib import Path

from shapely.geometry import Polygon
from south_bay_frieze import material

S = Path(__file__).resolve().parents[1]
OBS = json.loads((S / 'measurements/main-porch-observations.json').read_bytes())
LAYOUT = OBS['layout']
STONE = 'Door porch | warm grey stone'
EDGE = 'Door porch | pale dressed lip'
BED = 'Door porch | recessed stone bed'
PALETTE = {STONE: material([193,188,174], .88), EDGE: material([207,201,185], .85),
           BED: material([172,165,149], .90)}


def opening():
    """Return the rough opening in the main wall as left X, right X, bottom Z, top Z."""
    return tuple(LAYOUT['opening_for_wall'])


def add_main_porch(b, lod=False):
    """Add the photographed masonry. The doorway stays open through the wall plane."""
    low = lod is True or lod == 'lod'
    def block(x0,x1,y0,y1,z0,z1,m,label):
        b.box(((x0+x1)/2,(y0+y1)/2,(z0+z1)/2),(x1-x0,y1-y0,z1-z0),m,label=label)
    def plan(x0,x1,front,back,clipped,z0,z1,m,label):
        # The narrow return is visible at each end of the pale cap in the side views.
        shape=Polygon([(x0,front+clipped),(x0+clipped,front),(x1-clipped,front),
                       (x1,front+clipped),(x1,back),(x0,back)])
        b.plan_prism(shape,z0,z1,m,label)
    for side,(x0,x1) in zip(('north','south'),LAYOUT['jambs']):
        front,back=LAYOUT['shaft_y']
        block(x0,x1,front,back,0,3.704,STONE,side+' porch upright')
        block(x0-.025,x1+.025,front-.035,back,3.704,3.759,EDGE,side+' upright top fillet')
        block(x0-.050,x1+.050,front-.055,back,3.759,3.858,STONE,side+' upright impost')
        # Model the visible outward sweep under each overhanging tip.
        # In profile the element widens towards the cornice. No embellishment
        # is visible behind the hedge at the foot of either upright.
        if side=='north':
            outside,inside=x0-.59,x1-.005
            profile=[(x0,3.02),(x0-.012,3.35),(x0-.055,3.57),(x0-.14,3.78),
                     (x0-.29,3.96),(outside,4.08),(outside,4.235),(inside,4.235),(inside,3.02)]
        else:
            outside,inside=x1+.59,x0+.005
            profile=[(inside,3.02),(inside,4.235),(outside,4.235),(outside,4.08),
                     (x1+.29,3.96),(x1+.14,3.78),(x1+.055,3.57),
                     (x1+.012,3.35),(x1,3.02)]
        if low:
            profile=[p for p in profile if abs(p[1]-3.35)>.001]
        b.prism(Polygon(profile).buffer(0),.09,.245,lambda x,z,d:(x,-d,z),
                STONE,side+' swept porch console')
    # The horizontal underside is recessed behind the outer eave but in front
    # of the frame in both the north and the south winter photographs.
    block(-14.22,-12.42,-.20,.205,3.73,3.86,EDGE,'Stone flat door head')
    block(-14.88,-11.77,-.245,.19,3.86,4.065,STONE,'Horizontal masonry header')
    if not low:
        block(-14.89,-11.76,-.258,-.236,3.861,3.887,BED,'Narrow line beneath header')
    plan(-15.45,-11.16,-.735,.15,.10,4.065,4.174,STONE,'Canopy soffit return')
    plan(-15.71,-10.90,-.865,.15,.12,4.174,4.265,STONE,'Stepped projecting bed')
    plan(-15.87,-10.73,-.95,.15,.12,4.265,4.305,BED,'Underside of projecting lip')
    plan(-15.93,-10.68,-.99,.16,.14,4.305,4.448,EDGE,'Pale stone canopy cap')
