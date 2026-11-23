"""The No. 337 frontage measured in April 2015, with its unobstructed December wall finish.

X increases from the left-hand upper window to the west-southwest along the street.
The front of the window wall is Y=0. The historical gate points are in
measurements/courtyard-gate-survey.json. Air space behind the gate is kept open.
"""
from math import hypot

WALL = "Changle 337 | pebble-grey boundary render"
STONE = "Changle 337 | pale rendered pier"
BASE = "Changle 337 | grey rendered gate footing"
STEEL = "Changle 337 | dark sheet-steel gate"
FRAME = "Changle 337 | formed sheet ribs"
GREEN = "Changle 337 | green enamel address tablet"
WHITE = "Changle 337 | light address numerals"
PALETTE = {
    WALL: {"color":[.45,.425,.35],"roughness":.96},
    STONE: {"color":[.62,.60,.53],"roughness":.91},
    BASE: {"color":[.35,.345,.31],"roughness":.91},
    STEEL: {"color":[.10,.117,.105],"metallic":.34,"roughness":.73},
    FRAME: {"color":[.125,.137,.122],"metallic":.33,"roughness":.68},
    GREEN: {"color":[.075,.255,.19],"roughness":.52},
    WHITE: {"color":[.88,.86,.76],"roughness":.70},
}
GATE_EAST, GATE_WEST = 11.72, 13.44
FRONT_Y = -.21
START_X, END_X = 4.10, 16.86

def tapered_rectangle(b, bottom, top, material, label):
    """Two counterclockwise rectangular rings with a solid top and bottom."""
    a,c=bottom,top
    def ring(r):
        x0,x1,y0,y1,z=r
        return [(x0,y0,z),(x1,y0,z),(x1,y1,z),(x0,y1,z)]
    pts=ring(a)+ring(c)
    faces=[(0,2,1),(0,3,2),(4,5,6),(4,6,7)]
    for i in range(4):
        j=(i+1)%4
        faces.extend(((i,j,j+4),(i,j+4,i+4)))
    b.add(pts,faces,material,"337 | "+label)

def block(b, x0,x1,y0,y1,z0,z1, material,label):
    tapered_rectangle(b,(x0,x1,y0,y1,z0),(x0,x1,y0,y1,z1),material,label)

def strip(b, p,q,y0,y1,thickness, material,label):
    """A short solid strip in the XZ plane for the original enamel figures."""
    x,z=p
    xx,zz=q
    length=hypot(xx-x,zz-z)
    dx,dz=(zz-z)*thickness/(2*length),-(xx-x)*thickness/(2*length)
    face=[(x+dx,z+dz),(xx+dx,zz+dz),(xx-dx,zz-dz),(x-dx,z-dz)]
    pts=[(u,y,v) for y in (y0,y1) for u,v in face]
    faces=[(0,1,2),(0,2,3),(4,6,5),(4,7,6)]
    for i in range(4):
        j=(i+1)%4
        faces.extend(((i,j+4,j),(i,i+4,j+4)))
    b.add(pts,faces,material,"337 | "+label)

def gatepost(b, x, name, crest):
    y=FRONT_Y
    block(b,x-.206,x+.206,y,y+.43,0,.205,BASE,name+" footing")
    block(b,x-.183,x+.183,y+.012,y+.41,.205,crest-.096,STONE,name+" pier")
    block(b,x-.208,x+.208,y-.012,y+.43,crest-.096,crest-.058,STONE,name+" cap rim")
    tapered_rectangle(b,(x-.208,x+.208,y-.012,y+.43,crest-.058),
                       (x-.123,x+.123,y+.06,y+.355,crest),STONE,name+" weathered coping")

def address(b):
    x,z=GATE_EAST,1.84
    y=FRONT_Y-.002
    block(b,x-.103,x+.103,y-.016,y+.016,z-.073,z+.073,GREEN,"green street number tablet")
    curves={"3":[(-.019,.039),(.004,.043),(.018,.032),(.017,.019),(.008,.006),(-.003,.002),(.010,-.004),(.020,-.017),(.018,-.032),(.004,-.042),(-.016,-.036)],
            "7":[(-.020,.037),(.018,.037),(.006,.013),(-.006,-.014),(-.014,-.042)]}
    for i,digit in enumerate("337"):
        points=[(x+(i-1)*.052+a,z+c) for a,c in curves[digit]]
        for j,(p,q) in enumerate(zip(points,points[1:])):
            strip(b,p,q,y-.022,y-.016,.0065,WHITE,f"tablet digit {i+1} stroke {j+1}")

def leaf(b, x0,x1,name,lod):
    y=FRONT_Y+.165
    block(b,x0,x1,y,y+.045,.035,2.045,STEEL,name+" steel leaf")
    for a in (x0+.014,x1-.014):
        block(b,a-.013,a+.013,y-.013,y,.042,2.039,FRAME,name+" stile")
    for z in (.066,.99,2.018):
        block(b,x0+.027,x1-.027,y-.013,y,z-.011,z+.011,FRAME,name+" horizontal frame")
    if not lod:
        axis=(x0+x1)*.5
        block(b,axis-.009,axis+.009,y-.008,y,.077,2.007,FRAME,name+" pressed central rib")
        for z in (.445,.745,1.36,1.67):
            block(b,x0+.027,x1-.027,y-.009,y,z-.007,z+.007,FRAME,name+" shallow panel fold")

def add_courtyard_gate(b,lod=False):
    """Make the boundary from the house-wall joint up to the next property's pier."""
    # Six centimetres of return at the east end meet the end face of the tall house.
    y=FRONT_Y+.045
    spans=[(START_X,GATE_EAST-.183,"street-window side"),
           (GATE_WEST+.183,END_X,"west return")]
    for x0,x1,name in spans:
        block(b,x0,x1,y,y+.275,0,.17,BASE,name+" plinth")
        block(b,x0,x1,y+.012,y+.26,.17,2.008,WALL,name+" roughcast")
        block(b,x0,x1,y-.014,y+.286,2.008,2.065,STONE,name+" wall coping")
    block(b,7.63-.15,7.63+.15,FRONT_Y+.007,FRONT_Y+.35,.17,2.045,STONE,"intermediate wall pilaster")
    gatepost(b,GATE_EAST,"numbered east side",2.22)
    gatepost(b,GATE_WEST,"west side",2.24)
    l,r=GATE_EAST+.193,GATE_WEST-.193
    cut=(l+r)/2
    leaf(b,l,cut-.008,"east",lod)
    leaf(b,cut+.008,r,"west",lod)
    address(b)
