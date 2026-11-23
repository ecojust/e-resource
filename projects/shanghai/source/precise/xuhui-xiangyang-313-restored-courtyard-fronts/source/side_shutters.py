"""Return shutters and exposed tap, visible to either side of the lower southern bay."""
from pathlib import Path
import json
from shapely.geometry import box
from shapely.ops import unary_union
from photo_architecture import Facade
from foreground_bay import FRAME,REVEAL,LOUVRE,GLASSES,PLASTER,HARDWARE
from register_courtyard import Camera

DATA=json.loads((Path(__file__).parent.parent/'measurements/lower-bay-returns.json').read_bytes())
DEPTH=.6725

def panel(face,left,right,lo,hi,slatted,lod,name):
    frame=box(left,lo,right,hi)
    inset=box(left+.023,lo+.04,right-.023,hi-.042)
    face.prism(frame.difference(inset),-.009,.022,FRAME,name+' / surround')
    face.prism(inset,-.035,-.013,REVEAL if slatted else GLASSES[1],name+' / inner surface')
    n=18 if slatted else 5
    for j in range(n):
        z=lo+.065+(hi-lo-.12)*(j+.5)/n
        face.box((left+right)/2,z,right-left-.047,.015 if slatted else .013,.022,.003,
                 LOUVRE if slatted else FRAME,name+' / horizontal blades' if slatted else name+' / horizontal glazing bars')
    if not slatted:
        for f in (.25,.50,.75):
            face.box(left+(right-left)*f,(lo+hi)/2,.012,hi-lo-.08,.016,.006,FRAME,name+' / short glazing bars')

def add_return_shutters(b,lod=False):
    c=Camera('case1')
    # The reveal on the left of the centre bay falls partly behind a flowering
    # shrub. Only its exposed glazing and adjacent open shutter are resolved.
    face=Facade(b,(-1,DEPTH),(1,DEPTH),'south court / lower left recess')
    l,lo,r,hi=DATA['left_rear_bounds_local_xz']
    opening=box(l,lo,r,hi)
    wall=box(-2.165,0,-1.255,2.55)
    face.prism(wall.difference(opening),-.172,0,PLASTER,'perforated rear wall')
    face.prism(opening,-.19,-.17,REVEAL,'deep shaded reveal')
    panel(face,l+.05,r-.032,lo+.06,hi-.04,False,lod,'fixed dark glazing')
    ends=[c.wall(uv,depth) for uv,depth in DATA['left_open_leaf_top']]
    leaf=Facade(b,ends[0][:2],ends[1][:2],'south court / folded side shutter')
    # The canopy and plants obscure the lower end of the leaf in the photograph.
    panel(leaf,-leaf.length/2,leaf.length/2,.52,sum(p[2] for p in ends)/2,True,lod,'near open louvred leaf')
    l,lo,r,hi=DATA['right_visible_bounds_local_xz']
    right=box(1.403,0,2.433,2.55); aperture=box(l,lo,r,hi)
    face.prism(right.difference(aperture),-.172,0,PLASTER,'recessed right-hand return')
    face.prism(aperture,-.15,-.14,REVEAL,'eastern dark shutter shadow')
    panel(face,l+.018,r-.016,lo+.04,hi-.035,True,lod,'shutter at cropped right edge')
    side=Facade(b,(1.403,0),(1.403,DEPTH),'south court / eastern reveal')
    side.wall(0,2.55,thickness=.10,material=PLASTER)
    b.plan_prism(box(1.403,0,2.433,DEPTH),2.545,2.607,PLASTER,'south court / right overhang underside')
    # The short wall-mounted tap spans the photograph's right-hand jamb.
    points=[c.wall(uv,-depth) for uv,depth in DATA['tap_centreline']]
    b.tube(points,.018,HARDWARE,8 if lod else 12,'south court / horizontal exposed tap with elbow')
