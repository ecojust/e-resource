"""Stone steps, central wheel strip and the small visible patch of lane at No. 24."""
from math import cos, sin
from pathlib import Path
import json
from shapely.geometry import Polygon
from gable_face import finish

STAIR='Yefeng entrance | worn stone tread'
RISER='Yefeng entrance | dark recessed riser'
RAMP='Yefeng entrance | worn wheel strip'
JOINT='Yefeng entrance | wheel-strip seam'
LANE='Yefeng entrance | mottled road surface'
CHIP='Yefeng entrance | pale mineral grit'
PALETTE={k:finish(rgb,.93) for k,rgb in [
    (STAIR,(125,127,127)),(RISER,(99,97,91)),(RAMP,(134,137,138)),
    (JOINT,(103,106,105)),(LANE,(106,108,105)),(CHIP,(151,151,144))]}
DATA=json.loads((Path(__file__).resolve().parents[1]/'measurements/entrance-stair-fit.json').read_bytes())

def world(x,y,z):
    c,s=cos(DATA['yaw']),sin(DATA['yaw'])
    return (c*x-s*y,s*x+c*y,z)

def prism(b,left,right,profile,material,name):
    # Extrude a convex section drawn in local run/elevation coordinates.
    area=sum(y*q-z*p for (y,z),(p,q) in zip(profile,profile[1:]+profile[:1]))
    if area<0:profile=list(reversed(profile))
    side=len(profile)
    vertices=[world(x,y,z) for x in (left,right) for y,z in profile]
    faces=[list(reversed(range(side))),list(range(side,2*side))]
    for i in range(side):
        j=(i+1)%side
        faces.append([i,j,j+side,i+side])
    b.add(vertices,faces,material,name)

def add_steps(b,lod=False):
    b.palette.update(PALETTE)
    noses=DATA['nose_positions'];levels=DATA['top_heights']
    lower=DATA['toe_z'];toe=DATA['toe_y']
    families=[(DATA['left_cut'],DATA['ramp_left'],'left'),(DATA['ramp_right'],DATA['right_edge'],'right')]
    for index,(front,top) in enumerate(zip(noses,levels)):
        back=noses[index-1] if index else .03
        thickness=.036
        for left,right,side in ([(DATA['left_cut'],DATA['right_edge'],'landing')] if index==0 else families):
            tag='Entrance steps | '+side+' '+str(index+1)
            support=[(front+.019,lower),(back+.001,lower),(back+.001,top-thickness),(front+.019,top-thickness)]
            prism(b,left,right,support,RISER,tag+' riser')
            tread=[(front,top-.009),(front+.008,top-thickness),(back+.001,top-thickness),(back+.001,top),(front+.008,top)]
            prism(b,left,right,tread,STAIR,tag+' worn lip')
    # The landing meets the sides of the opening; the inner tile and rear door are
    # separate components. Keep the wheel strip level up to the top nose.
    portal_left=-1.975643;portal_right=-.432365
    front=noses[0];top=levels[0]
    back=DATA['landing_rear_y']
    landing=Polygon([world(DATA['left_cut'],.03,top)[:2],world(DATA['right_edge'],.03,top)[:2],
                     (portal_right,back),(portal_left,back)])
    b.plan_prism(landing,top-.047,top-.002,STAIR,'Entrance steps | upper landing')
    # Two measured straight slabs meet at the visible transverse seam near the last nose.
    def on_strip(y):return lower+(top+.005-lower)*(y-toe)/(front-toe)
    seam=noses[3]
    for a,c,material,tag in [(toe,seam-.003,RAMP,'foot'),(seam-.003,seam+.003,JOINT,'seam'),(seam+.003,front,RAMP,'upper run')]:
        z1,z2=on_strip(a),on_strip(c)
        section=[(a,lower-.012),(c,lower-.012),(c,z2),(a,z1)]
        prism(b,DATA['ramp_left'],DATA['ramp_right'],section,material,'Entrance wheel strip | '+tag)
    boundary=Polygon([p[:2] for p in DATA['visible_lane_polygon_world']])
    b.plan_prism(boundary,lower-.035,lower,LANE,'Entrance steps | visible lane paving')
    # Isolated light aggregate on the right of the strip is visible against its darker bed.
    for i,(x,y,z) in enumerate(DATA['aggregate_points_world']):
        if lod and i%3:continue
        k=.009+(i%3)*.002
        cell=Polygon([(x-k,y),(x-k*.25,y-k*.46),(x+k*.85,y-k*.28),(x+k*.42,y+k*.61)]).intersection(boundary)
        if cell.area>1.e-7:b.plan_prism(cell,z,z+.0025,CHIP,'Entrance steps | visible mineral aggregate')
