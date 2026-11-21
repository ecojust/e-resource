"""Use a common curved centreline for the open stone balustrade, cornice and dentils."""
from math import cos, sin, radians
from shapely.geometry import Point, Polygon
from photo_architecture import Facade

PALE='cream render'
CARVED='pale carved stone'
BASE='warm stone moulding'
SHADOW='recessed ochre soffit'
MEDAL='weathered circular relief'
PALETTE={
    PALE:dict(color=[.83,.805,.69],roughness=.85),
    CARVED:dict(color=[.891,.863,.754],roughness=.78),
    BASE:dict(color=[.728,.693,.581],roughness=.88),
    SHADOW:dict(color=[.621,.566,.439],roughness=.92),
    MEDAL:dict(color=[.790,.756,.625],roughness=.86),
}
RADIUS=5.20
ANGLE=46.0


def point(deg,offset=0):
    a=radians(deg);r=RADIUS+offset
    return (r*sin(a),RADIUS-r*cos(a))


def curved_strip(builder,low,z1,z2,inside,outside,mat,label):
    count=18 if low else 48
    steps=[-ANGLE+2*ANGLE*i/count for i in range(count+1)]
    outline=[point(a,outside)for a in steps]+[point(a,inside)for a in reversed(steps)]
    builder.plan_prism(Polygon(outline),z1,z2,mat,label)


def local_block(b,deg,offset,z,width,depth,height,mat,label):
    x,y=point(deg,offset);a=radians(deg)
    b.box((x,y,z),(width,depth,height),mat,
          basis=((cos(a),sin(a),0),(-sin(a),cos(a),0),(0,0,1)),label=label)


def crest(b,low):
    # The photograph shows a continuous rectangular pier, a circular face, two ledges,
    # a stepped upper cap and a small knob. The relief's missing motif is left smooth.
    for z,w,h,d,mat,label in [(2.834,.83,.134,.51,BASE,'central pier bottom ledge'),
                               (3.257,.70,.726,.43,PALE,'central solid pier'),
                               (3.589,.81,.087,.50,CARVED,'crest lower rim'),
                               (3.665,.89,.084,.56,BASE,'crest cornice'),
                               (3.735,.78,.066,.49,CARVED,'crest cap stone'),
                               (3.800,.61,.065,.43,PALE,'stepped upper field')]:
        local_block(b,0,0,z,w,d,h,mat,label)
    front=Facade(b,(-.45,-.220),(.45,-.220),'Central heraldic pier')
    disk=Point(0,3.380).buffer(.142,resolution=8 if low else 24)
    inner=Point(0,3.380).buffer(.107,resolution=8 if low else 24)
    front.prism(disk.difference(inner),-.005,.045,CARVED,'raised circular surround')
    front.prism(inner,-.004,.021,MEDAL,'weathered round central boss')
    for z,w,h,d in [(3.092,.31,.052,.047),(3.012,.40,.051,.085),
                     (2.949,.306,.069,.105),(2.869,.233,.082,.138)]:
        front.box(0,z,w,h,d,.014+d/2,BASE,'tiered corbel below medallion')
    b.lathe((0,.020),[(3.831,.095),(3.860,.101),(3.895,.063),
                       (3.957,.092),(4.00,.056),(4.035,.018)],
            CARVED,segments=10 if low else 22,label='small central cap finial')


def make_gallery(b,low=False):
    # Only the portion of arc visible on the two garden-face photographs is included.
    for z1,z2,inside,out,mat,label in [
        (1.645,1.785,-.72,.09,SHADOW,'curved soffit return'),
        (1.780,1.925,-.43,.115,BASE,'shadow line above support'),
        (1.920,2.218,-.37,.13,PALE,'continuous curved frieze'),
        (2.215,2.280,-.37,.205,CARVED,'fine rising band'),
        (2.277,2.379,-.37,.230,BASE,'dentil backing fascia'),
        (2.376,2.445,-.40,.343,CARVED,'projecting dentil shelf'),
        (2.442,2.505,-.43,.365,BASE,'cornice drip edge'),
        (2.503,2.579,-.35,.305,PALE,'moulded top of cornice'),
        (2.577,2.700,-.22,.225,CARVED,'balustrade plinth'),
        (2.697,2.764,-.19,.191,BASE,'lower sill cap'),
        (3.363,3.430,-.161,.161,BASE,'handrail underside'),
        (3.427,3.514,-.194,.195,CARVED,'convex handrail band'),
        (3.510,3.560,-.147,.147,PALE,'sloped handrail top strip')]:
        curved_strip(b,low,z1,z2,inside,out,mat,label)
    # Individual dentils and balusters are real geometry; their pitch is a photo estimate.
    for i in range(35):
        angle=-44.2+i*(88.4/34)
        local_block(b,angle,.237,2.305,.125,.154,.132,CARVED,'separate projecting dentils')
    for sign in (-1,1):
        for i in range(13):
            a=sign*(5.55+3.11*i);xy=point(a)
            b.lathe(xy,[(2.757,.079),(2.794,.080),(2.821,.061),(2.876,.056),
                        (2.943,.077),(3.019,.079),(3.111,.054),(3.209,.044),
                        (3.266,.055),(3.321,.078),(3.365,.081)],
                    CARVED,segments=9 if low else 20,label='turned freestanding stone balusters')
        local_block(b,sign*45.4,0,3.062,.174,.293,.606,PALE,'flat termination of cropped rail')
    crest(b,low)
    # The shaft below this capital is cut at the point where the leaves hide it.
    x,y=point(16.4,-.36)
    b.lathe((x,y),[(0,.173),(.680,.170),(1.240,.155),(1.293,.162),(1.317,.182),
                   (1.363,.185),(1.401,.164),(1.446,.193),(1.515,.225),(1.548,.219)],
            CARVED,segments=16 if low else 36,label='visible capital and upper shaft')
    local_block(b,16.4,-.36,1.584,.522,.493,.085,PALE,'square capital abacus')
    local_block(b,16.4,-.36,1.644,.576,.550,.046,BASE,'upper bearing plate')
