"""Two inscribed entrance posts and the four iron panels on Yuyuan Road."""
import math
from pathlib import Path

from shapely.geometry import LineString, Polygon, box

from photo_architecture import Facade
from sign_lettering import add_facade_lettering

FONT = Path(__file__).with_name('fonts') / 'YuguGateInscription.otf'
POST_AXIS = 3.17
POST_WIDTH = .37
CLEAR = POST_AXIS - POST_WIDTH
STONE = 'gray cast stone'
CAP = 'lighter dressed stone'
PLATE = 'ivory name tablet'
INK = 'black calligraphic lettering'
IRON = 'dark ironwork'
IRON_EDGE = 'weathered iron edges'
GREEN = 'green enamel address sign'
CREAM = 'pale enamel letters'
BRONZE = 'dark commemorative plaque'
COPPER = 'aged metal rim'

PALETTE = {
    STONE: {'color': [.40, .411, .413], 'roughness': .92},
    CAP: {'color': [.504, .513, .50], 'roughness': .87},
    PLATE: {'color': [.76, .756, .683], 'roughness': .86},
    INK: {'color': [.072, .077, .071], 'roughness': .80},
    IRON: {'color': [.105, .117, .107], 'metallic': .49, 'roughness': .62},
    IRON_EDGE: {'color': [.179, .179, .147], 'metallic': .41, 'roughness': .68},
    GREEN: {'color': [.059, .242, .192], 'metallic': .16, 'roughness': .48},
    CREAM: {'color': [.840, .850, .769], 'roughness': .49},
    BRONZE: {'color': [.347, .315, .264], 'metallic': .47, 'roughness': .70},
    COPPER: {'color': [.465, .428, .345], 'metallic': .51, 'roughness': .65},
}


def border(face, rect, thickness, back, front, material, name):
    rim = rect.difference(rect.buffer(-thickness, join_style='mitre'))
    face.prism(rim, back, front, material, name)


def posts(face, side):
    x = side * POST_AXIS / 2
    half = POST_WIDTH / 2
    # Each pier ends in a raised central head with two cut-off shoulders.
    head = [(x-half, 0), (x+half, 0), (x+half, 2.72), (x+.123, 2.72),
            (x+.093, 2.81), (x-.092, 2.81), (x-.128, 2.72), (x-half, 2.72)]
    face.prism(Polygon(head), -.42, .004, STONE, 'freestanding inscription pier')
    field = box(x-.126, 1.04, x+.126, 1.91)
    face.prism(field, .005, .020, PLATE, 'ivory vertical inscription tablet')
    border(face, field.buffer(.017, join_style=2), .013, .003, .025, CAP, 'slim tablet border')
    for glyph, z in zip('愚谷邨', (1.746, 1.472, 1.205)):
        add_facade_lettering(face, glyph, x, z, .191, .199, .0202, .023, INK,
                             label='vertical lane name', font=FONT)
    face.box(x, 2.073, .193, .190, .013, .009, CAP, 'square insert above name')

    outer = x + side * .79
    mid = (x + side * half + outer) / 2
    width = abs(outer - (x + side * half))
    face.box(mid, 1.07, width, 2.14, .31, -.182, STONE, 'recessed side wall')
    face.box(mid, 2.145, width+.024, .075, .36, -.172, CAP, 'side wall coping')
    relief = LineString([(mid-width*.38, 2.036), (mid, 1.894), (mid+width*.38, 2.036)])
    face.prism(relief.buffer(.021, cap_style='flat', join_style='mitre'), -.020, .006,
               CAP, 'chevron below coping')
    for i in range(3):
        u = outer + side * i * .072
        height = 2.46 + .077*i
        face.box(u, height/2, .095, height, .365+.045*i, -.128,
                 STONE if i!=1 else CAP, 'stepped outer return fins')

    if side < 0:
        plaque = box(mid-.235, 1.29, mid+.235, 1.67)
        face.prism(plaque, -.027, -.004, BRONZE, 'metal plaque on east return')
        border(face, plaque, .012, -.003, .004, COPPER, 'plaque perimeter')
    else:
        signx = x + .055
        sign = box(signx-.257, 2.237, signx+.257, 2.423)
        face.prism(sign, .005, .035, GREEN, 'enamel street address')
        add_facade_lettering(face, '361弄3–127号', signx, 2.360, .459, .066,
                             .0352, .038, CREAM, label='lane and house numbers', font=FONT)
        add_facade_lettering(face, '愚园路', signx, 2.277, .187, .043,
                             .0352, .038, CREAM, label='street name', font=FONT)


def spiral(builder, cx, z, radius, handed, lod):
    steps = 12 if lod else 22
    path = []
    for i in range(steps+1):
        t = i/steps
        angle = t*1.67*math.pi
        r = radius*(1-.79*t)
        path.append((cx+handed*r*math.cos(angle), .175, z+r*math.sin(angle)))
    builder.tube(path, .010, IRON_EDGE, 5 if lod else 8, 'ironwork/paired scrolls')


def grille(builder, face, panel, lod):
    width = CLEAR / 4
    left = -CLEAR/2 + panel*width + .010
    right = left + width - .020
    cx = (left+right)/2
    for x in (left, right):
        face.box(x, 1.23, .029, 2.38, .051, -.215, IRON, 'four-panel gate stiles')
    for z, h in ((.082,.038),(.28,.024),(.91,.022),(1.16,.024),(2.03,.026),(2.18,.039)):
        face.box(cx,z,right-left,h,.043,-.214,IRON,'horizontal gate rails')
    count = 6
    for i in range(1,count+1):
        x = left+(right-left)*i/(count+1)
        face.box(x,1.191,.014,2.218,.028,-.217,IRON,'iron panel pickets')
        spear = Polygon([(x-.020,2.280),(x-.019,2.316),(x,2.369),
                         (x+.019,2.316),(x+.020,2.280)])
        face.prism(spear,-.230,-.204,IRON_EDGE,'pointed picket finials')
    for handed in (-1,1):
        x=cx+handed*.113
        spiral(builder,x,1.015,.089,handed,lod)
        if not lod:spiral(builder,x,2.116,.050,-handed,lod)
    d=.180
    shape=[(cx,1.43),(cx+.145,1.20),(cx,.99),(cx-.145,1.20),(cx,1.43)]
    builder.tube([(u,d,z) for u,z in shape],.011,IRON_EDGE,5 if lod else 8,
                 'ironwork/central diamond tracery')


def gate(builder, lod):
    front = Facade(builder, (-2.9, 0), (2.9, 0), 'Yuyuan Road gate')
    for side in (-1, 1):posts(front, side)
    for panel in range(4):grille(builder, front, panel, lod)
    for x in (-CLEAR/2, CLEAR/2):
        for z in (.29, 1.84):
            builder.tube([(x,.215,z-.055),(x,.215,z+.055)],.026,
                         IRON_EDGE,6 if lod else 10,'ironwork/hinge barrels')
