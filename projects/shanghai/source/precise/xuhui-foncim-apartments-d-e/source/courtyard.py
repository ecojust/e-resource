"""Covered passage between the two principal entrances of Foncim Apartments D and E."""
import math
import numpy as np
from shapely.geometry import Polygon, box
from north_block import pigment
from garden_ground import build_garden

SOFFIT='Court ivory soffit'
FASCIA='Court golden cement fascia'
BEAM='Court shadowed edge beam'
COLUMN='Court russet round columns'
PAVE='Court grey paving'
JOINT='Court mortar bed'
BORDER='Court granite edge'
COURT_PALETTE={SOFFIT:pigment((218,210,189)),FASCIA:pigment((211,172,119)),
               BEAM:pigment((139,124,102)),COLUMN:pigment((145,87,75)),
               PAVE:pigment((158,154,147)),JOINT:pigment((125,121,114)),
               BORDER:pigment((133,129,117))}

def build_court(b,lod,far_entry):
    start=np.array([0.,11.57]);end=np.asarray(far_entry);line=end-start
    length=float(np.linalg.norm(line));along=line/length
    across=np.array([along[1],-along[0]])
    def pt(x,t):
        return start+across*x+along*t
    def rectangle(x1,t1,x2,t2):
        return Polygon([pt(x1,t1),pt(x2,t1),pt(x2,t2),pt(x1,t2)])
    def slab(x1,t1,x2,t2,z,top,material,tag):
        b.plan_prism(rectangle(x1,t1,x2,t2),z,top,material,'Court '+tag)
    # A low, single deck lies on six paired columns. The gardens are open to either side.
    width=3.52;post_x=1.35
    slab(-width/2,-.08,width/2,length+.085,2.83,3.03,SOFFIT,'continuous roof soffit')
    slab(-width/2-.036,-.09,width/2+.036,length+.09,3.03,3.18,FASCIA,'upper fascia')
    slab(-width/2+.045,-.06,width/2-.045,length+.05,3.18,3.20,BEAM,'roof weathering surface')
    for hand in (-1,1):
        x=hand*post_x
        slab(x-.157,0,x+.157,length,2.69,2.84,BEAM,'longitudinal beams')
        for t in np.linspace(.64,length-.69,6):
            b.lathe(tuple(pt(x,t)),[(.081,.196),(.145,.205),(.18,.199),
                    (2.58,.198),(2.60,.21),(2.66,.209),(2.70,.216)],
                    COLUMN,12 if lod else 24,'Court six pairs of round columns')
        ridge=hand*1.82
        slab(ridge-.05,.29,ridge+.05,length-.31,.055,.138,BORDER,'low walkway kerb')
    slab(-1.80,-.18,1.80,length+.16,.021,.079,JOINT,'pavement bed')
    for i in range(math.ceil(length/.52)):
        for j in range(5):
            t=i*.52;end_t=min(length,t+.52)-.004
            if end_t-t>.008:
                x=-1.77+j*.708
                slab(x+.003,t+.004,x+.704,end_t,.079,.083,PAVE,'individual stone flags')
    build_garden(b,lod,[pt(-1.80,-.18),pt(1.80,-.18),pt(1.80,length+.16),pt(-1.80,length+.16)])
    return dict(length_m=length,roof_width_m=width,clear_height_between_beams_m=2.69-.083,
                column_centres_x_m=[-post_x,post_x],roof_endpoints=[start.tolist(),end.tolist()])
