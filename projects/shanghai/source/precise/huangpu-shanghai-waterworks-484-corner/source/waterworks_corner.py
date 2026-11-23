"""Observed southwest corner of the Shanghai Waterworks Company office at 484 Jiangxi Middle Road."""
import math

from shapely.geometry import Polygon, box
from shapely.ops import unary_union

from photo_architecture import Facade

PLASTER = 'light grey ruled stucco'
JOINT = 'recessed grey joint'
STONE = 'pale carved stone'
BAND = 'shadowed stone moulding'
IRON = 'dark green grey sash'
GLASS = 'smoky recessed glazing'
ROOF = 'warm red roof tile'
SEAM = 'terracotta tile bead'
FLASH = 'dark weathered flashing'
PALETTE = {
    PLASTER: {'color': [.76,.76,.72], 'roughness': .94},
    JOINT: {'color': [.46,.47,.46], 'roughness': .96},
    STONE: {'color': [.83,.81,.74], 'roughness': .89},
    BAND: {'color': [.64,.64,.58], 'roughness': .92},
    IRON: {'color': [.22,.25,.22], 'roughness': .77},
    GLASS: {'color': [.32,.37,.36], 'roughness': .41},
    ROOF: {'color': [.66,.36,.25], 'roughness': .90},
    SEAM: {'color': [.72,.40,.28], 'roughness': .88},
    FLASH: {'color': [.28,.29,.28], 'roughness': .83},
}
HALF_WIDTH = 2.98430
FRONT = .42


def oval(cx, z, a, b, samples):
    return Polygon([(cx+a*math.cos(math.tau*i/samples),z+b*math.sin(math.tau*i/samples))
                    for i in range(samples)])


def frame(f, hole, inset, back, front, material, name):
    f.prism(hole.difference(hole.buffer(-inset,join_style=2)),back,front,material,name)


def main_wall(f,lod):
    h=HALF_WIDTH
    window=box(-1.03,7.45,1.03,9.91)
    wall=box(-h,.08,h,10.62).difference(window)
    f.prism(wall,.075,FRONT,PLASTER,'upper ruled corner wall')
    # Horizontal joints cross the two shoulders of the tall smooth central panel.
    blank=box(-1.43,.86,1.43,4.57)
    relief=box(-1.24,4.49,1.24,7.29)
    excluded=unary_union([window.buffer(.16,join_style=2),blank.buffer(.08),relief])
    grooves=[]
    z=.38
    while z<10.60:
        grooves.append(box(-h,z,h,z+.030).difference(excluded))
        z+=.49
    f.prism(unary_union(grooves),FRONT+.002,FRONT+.008,JOINT,'horizontal stucco bed joints')
    for z,height,depth,mat in [(.09,.18,.68,BAND),(.22,.12,.77,STONE),(.32,.09,.71,PLASTER)]:
        f.box(0,z,2*h+.10,height,depth-.08,(depth+.08)/2,mat,'lower floor stringcourse')
    f.prism(blank,FRONT+.009,FRONT+.038,PLASTER,'smooth blank field')
    frame(f,blank,.12,FRONT+.028,FRONT+.13,STONE,'raised border of blank field')
    if not lod:
        frame(f,blank.buffer(-.13,join_style=2),.035,FRONT+.035,FRONT+.067,BAND,'recessed inner panel bead')
    f.prism(window.buffer(.016,join_style=2),.11,.145,GLASS,'sash glazing')
    frame(f,window,.092,.16,.27,IRON,'dark outer sash')
    for x in [-.52,0,.52]:
        f.box(x,8.67,.040,2.36,.072,.213,IRON,'three upright glazing bars')
    for z in [8.04,9.43] if not lod else [9.43]:
        f.box(0,z,1.93,.043,.074,.215,IRON,'horizontal glazing bars')
    frame(f,window.buffer(.091,join_style=2),.078,FRONT-.03,FRONT+.053,STONE,'square window reveal')
    f.box(0,7.42,2.32,.105,.35,FRONT+.018,STONE,'projecting window sill')
    f.box(0,9.96,2.22,.102,.24,FRONT-.005,BAND,'flat window head')


def garland(f,lod):
    """A raised hollow loop. The two bound horns, top flower and scroll tails are separate solids."""
    sides=5 if lod else 8
    steps=19 if lod else 40
    mid=5.92
    def tube(points,radius,name,mat=STONE):
        f.builder.tube([f.point(x,z,d) for x,z,d in points],radius,mat,sides,'cartouche/'+name)
    # At the bottom the rolled stone ribs nearly touch; the centre of the ring
    # remains open to the wall and has no invented coat of arms or inscription.
    for sign in [-1,1]:
        for index in range(2 if lod else 4):
            trajectory=[]
            for i in range(steps+1):
                t=i/steps;theta=math.radians(178+89*t)
                x=sign*(abs(math.cos(theta))*(1.00+index*.056)+.065*(1-t))
                z=mid+(1.03+index*.04)*math.sin(theta)
                trajectory.append((x,z,FRONT+.105+index*.011))
            tube(trajectory,.081 if lod else .057,'lower swept horn ribs')
        # Each horn flares upwards towards the upper end of the scroll.
        fan=[(.80,5.83),(.92,6.18),(1.05,6.39),(1.31,6.30),(1.42,6.14),(1.22,6.13),(1.15,5.82)]
        f.prism(Polygon([(sign*x,z)for x,z in fan]),FRONT+.033,FRONT+.15,STONE,'flared stone horn')
        for z,wid in [(5.91,.26),(6.02,.33),(6.15,.44)]:
            f.box(sign*1.09,z,wid,.045,.073,FRONT+.173,BAND,'bands binding the horns')
        # The upper garland arches around the blank centre, meeting the top flower.
        pts=[]
        for i in range(steps):
            t=i/(steps-1);theta=(1-t)*.24+t*(math.pi*.49)
            pts.append((sign*1.04*math.cos(theta),mid+1.01*math.sin(theta),FRONT+.11))
        tube(pts,.084,'upper garland stalk')
        for i in range(5 if lod else 10):
            t=(i+.25)/(5 if lod else 10);theta=.27+1.07*t
            x=sign*1.04*math.cos(theta);z=mid+1.02*math.sin(theta)
            leaf=Polygon([(x-sign*.14,z-.11),(x+sign*.12,z+.04),(x+sign*.22,z+.18),(x+sign*.04,z+.16)])
            f.prism(leaf,FRONT+.084,FRONT+.193,STONE,'leaves on upper garland')
        tail=[(sign*.06,4.81,FRONT+.13),(sign*.33,4.69,FRONT+.15),(sign*.68,4.61,FRONT+.13),
              (sign*.91,4.70,FRONT+.13),(sign*1.06,4.85,FRONT+.14),(sign*1.18,4.82,FRONT+.14)]
        tube(tail,.085,'recurved ribbon at foot')
        f.prism(oval(sign*.65,4.87,.24,.11,16),FRONT+.026,FRONT+.105,STONE,'lower leaves')
    for i in range(5 if lod else 8):
        theta=math.tau*i/(5 if lod else 8)
        x=.19*math.cos(theta); z=6.94+.21*math.sin(theta)
        f.prism(oval(x,z,.145,.18,12 if lod else 21),FRONT+.086,FRONT+.208,STONE,'petals at crown')
    f.prism(oval(0,6.94,.145,.15,16),FRONT+.19,FRONT+.266,BAND,'flower centre')
    f.prism(oval(0,4.89,.15,.20,16),FRONT+.07,FRONT+.21,STONE,'lower knot')
    f.box(0,4.46,2.66,.095,.18,FRONT+.042,STONE,'cartouche plinth lip')


def eaves(f,lod):
    h=HALF_WIDTH
    for z,height,width,depth,mat,name in [
        (10.31,.09,2*h+.06,.54,BAND,'thin frieze bed'),(10.59,.48,2*h+.075,.54,PLASTER,'pale fascia band'),
        (10.87,.09,2*h+.18,.62,STONE,'moulded upper fascia'),(11.05,.30,2*h+.30,.70,FLASH,'dark eave flashing'),
        (11.25,.11,2*h+.34,.77,FLASH,'projecting lower roof edge')]:
        f.box(0,z,width,height,depth-.06,(depth+.06)/2,mat,name)
    for i in range(6):
        x=(i-2.5)*.94
        face=box(x-.39,10.40,x+.39,10.76)
        frame(f,face,.044,.537,.583,STONE,'frieze panel border')
        conv=[(x+.27*math.cos(math.pi+math.pi*j/(10 if lod else 23)),
               10.64+.15*math.sin(math.pi+math.pi*j/(10 if lod else 23)),.588)
              for j in range(11 if lod else 24)]
        f.builder.tube([f.point(*q) for q in conv],.028,STONE,5 if lod else 7,'frieze shallow bowed mouldings')
    # The photographed red hipped strip narrows towards the upper dark flashing.
    x0,x1=h+.11,1.88
    z0,z1=11.29,13.01
    y0,y1=-.70,.61
    low=[(-x0,y0,z0),(x0,y0,z0),(x1,y1,z1),(-x1,y1,z1)]
    vertices=low+[(x,y,z-.095) for x,y,z in low]
    f.builder.add(vertices,[(0,1,2,3),(7,6,5,4),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)],ROOF,'street-side red tiled hip')
    for i in range(27 if lod else 65):
        t=(i+.5)/(27 if lod else 65)
        x=(2*t-1)*x0
        # Tile channels run up the slope parallel to the central seam and stop at its hip line.
        end=min(1.,(x0-abs(x))/(x0-x1))
        f.builder.tube([(x,y0-.012,z0+.015),(x,y0+(y1-y0)*end-.012,z0+(z1-z0)*end+.015)],
                       .023 if lod else .017,SEAM,4 if lod else 6,'parallel red tile rolls')
    f.builder.tube([(-x1,y1,z1),(x1,y1,z1)],.055,FLASH,6,'hip upper edge flashing')
    for sign in [-1,1]:
        f.builder.tube([(sign*x0,y0,z0),(sign*x1,y1,z1)],.045,SEAM,6,'tile hip end caps')


def add_building(builder,lod):
    front=Facade(builder,(-HALF_WIDTH,0),(HALF_WIDTH,0),'southwest corner')
    main_wall(front,lod)
    garland(front,lod)
    eaves(front,lod)
