"""The numbered ground-floor entrance and its single window, facing the north lane."""
from math import cos, pi, sin
from shapely.geometry import LineString, box
from shapely.ops import unary_union
from photo_architecture import Facade

LIME = 'warm white lime render'
GREY = 'grey painted plinth'
STONE = 'light buff entrance terrazzo'
RED = 'dark red painted wood'
IRON = 'patinated iron'
PANE = 'window glass in shadow'
GREEN = 'green enamel address plate'
WHITE = 'cream numerals'
GROUND = 'dark grey lane brick'
PALETTE = {
    LIME: dict(color=[.776, .752, .699], roughness=.91),
    GREY: dict(color=[.371, .355, .339], roughness=.86),
    STONE: dict(color=[.69, .62, .53], roughness=.75),
    RED: dict(color=[.258, .054, .043], roughness=.61),
    IRON: dict(color=[.118, .109, .100], metallic=.55, roughness=.66),
    PANE: dict(color=[.100, .116, .123], metallic=.20, roughness=.34),
    GREEN: dict(color=[.047, .315, .232], metallic=.24, roughness=.46),
    WHITE: dict(color=[.880, .856, .737], roughness=.57),
    GROUND: dict(color=[.302, .298, .290], roughness=.93),
}
LEFT, RIGHT = -1.84, 1.84
DOOR = (.66, 1.57)
WINDOW = (-1.56, .02)
SILL, HEAD = .83, 2.22
TOP = 3.10
RECESS = .67


def bar(face, coordinates, depth, radius, sides, name, material=IRON):
    points = [face.point(x, z, depth) for x, z in coordinates]
    face.builder.tube(points, radius, material, sides, face.label + '/' + name)


def door(face, low):
    left, right = DOOR
    center = (left + right) / 2
    for x in (left + .025, right - .025):
        face.box(x, 1.427, .05, 2.704, .09, -.023, IRON, 'iron outer jamb')
        face.box(x, 1.341, .045, 2.52, .074, -RECESS + .018, RED, 'rear timber jamb')
    face.box(center, 2.775, right - left, .055, .085, -.023, IRON, 'iron head')
    face.box(center, 2.116, right - left - .065, .038, .055, -.015, IRON, 'transom spring bar')
    inner_left, inner_right = left + .052, right - .052
    for a, b in (((inner_left, 2.129), (inner_right, 2.746)),
                 ((inner_right, 2.129), (inner_left, 2.746))):
        bar(face, [a, b], -.048, .0125, 6 if low else 12, 'crossed transom irons')
    count = 28 if low else 76
    ellipse = [(center + .264 * cos(2*pi*i/count), 2.435 + .303*sin(2*pi*i/count))
               for i in range(count+1)]
    bar(face, ellipse, -.035, .010, 6 if low else 12, 'open oval transom')
    if not low:
        for z in (2.247, 2.628):
            bar(face, [(center-.207, z), (center+.207, z)], -.038, .007, 8, 'thin transom straps')
    # The interior wall visible from the lane is the return on the left of the opening.
    # The source photograph ends at the back jamb, before the domestic rooms.
    for x in (left-.044, right+.044):
        face.builder.box((x, RECESS/2, 1.413), (.088, RECESS, 2.676), LIME, label='Entrance/white passage return')
        face.builder.box((x, RECESS/2, .167), (.094, RECESS, .188), RED, label='Entrance/painted return skirting')
    face.builder.box((center, RECESS/2, 2.807), (right-left, RECESS, .09), LIME, label='Entrance/recess soffit')
    face.builder.box((center, RECESS/2-.035, .0375), (right-left+.11, RECESS+.17, .075), STONE, label='Entrance/light shallow doorstep')
    face.builder.box((left+.025, .43, 1.26), (.066, .256, .257), GREY, label='Entrance/inset letter box on the return')
    face.builder.box((left+.061, .43, 1.312), (.012, .208, .034), IRON, label='Entrance/dark letter slot')


def window(face, low):
    left, right = WINDOW
    mid = (left+right)/2
    width = right-left
    face.box(mid, (SILL+HEAD)/2, width-.035, HEAD-SILL-.035, .025, -.166,
             PANE, 'recessed panes')
    transom = HEAD-.236
    pieces = [box(left, SILL, right, HEAD).difference(box(left+.058, SILL+.065, right-.058, HEAD-.057)),
              box(left+.038, transom-.025, right-.038, transom+.025)]
    for rank in (1, 2):
        x = left+width*rank/3
        pieces.append(box(x-.025, SILL+.022, x+.025, HEAD-.026))
    face.prism(unary_union(pieces), -.146, -.076, RED, 'three casements with transom lights')
    for i in range(1,9):
        x = left+.068+i*(width-.136)/9
        bar(face, [(x, SILL+.094), (x, transom-.031)], -.041, .009, 5 if low else 10, 'slender red guard bars',RED)
    face.box(mid,SILL-.020,width+.128,.078,.19,.002,STONE,'projecting stone windowsill')
    if not low:
        for x in (left+.065, right-.065):
            face.box(x, (transom+SILL)/2, .020, transom-SILL-.12, .024, -.038, RED, 'window stop beads')


def address(face, low):
    u,z=.368,1.967
    face.box(u,z,.226,.175,.016,.015,GREEN,'green enamel address plate')
    # Outline two rounded, open numerals without mapping the source photograph.
    for shift in (-.044,.044):
        form=[(-.027,.025),(-.022,.038),(-.012,.046),(.006,.048),(.019,.043),(.026,.032),
              (.026,.020),(.020,.007),(-.019,-.026),(-.028,-.040),(.027,-.040)]
        letter=LineString([(x+u+shift,y+z+.014) for x,y in form]).buffer(.0058,quad_segs=2 if low else 5)
        face.prism(letter,.024,.029,WHITE,'raised digits 22')
    if not low:
        for x in (u-.095,u+.095):
            for h in (z-.068,z+.068):
                face.box(x,h,.008,.008,.006,.026,IRON,'address plate fasteners')


def make_entrance(builder, low=False):
    face=Facade(builder,(LEFT,0),(RIGHT,0),'No 22 north facade')
    opening=box(DOOR[0],0,DOOR[1],2.802)
    lights=box(WINDOW[0],SILL,WINDOW[1],HEAD)
    face.prism(box(LEFT,.01,RIGHT,TOP).difference(unary_union([opening,lights])), -.20, 0, LIME,
               'white wall with two real openings')
    for x0,x1 in [(LEFT,DOOR[0]),(DOOR[1],RIGHT)]:
        face.box((x0+x1)/2,.185,x1-x0,.365,.071,.002,GREY,'grey plinth interrupted at doorstep')
    face.box(1.664,.101,.175,.184,.216,.030,GREY,'projecting foot of the right jamb')
    door(face,low)
    window(face,low)
    address(face,low)
    # The visible surface is the short brick apron in front of this particular unit.
    builder.plan_prism(box(LEFT,-.53,RIGHT,-.077),-.045,-.013,GREY,'Lane/apron bed')
    for course in range(3):
        y0=-.53+course*.151
        x=LEFT-.16*(course%2)
        while x<RIGHT:
            a,b=max(x,LEFT),min(x+.310,RIGHT)
            if b-a>.013:
                builder.plan_prism(box(a+.003,y0+.003,b-.003,y0+.148),-.014,-.002,GROUND,'Lane/individual running-bond pavers')
            x+=.316
