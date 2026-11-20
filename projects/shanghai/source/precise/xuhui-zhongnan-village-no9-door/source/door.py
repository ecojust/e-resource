"""No. 9 door leaf, stepped grille and enamel address plate, looking in from the lane."""

from math import cos, pi, sin

from shapely.geometry import LineString, Point, box
from shapely.ops import unary_union

from photo_architecture import Facade


WOOD = 'deep green painted timber'
BOARD = 'slightly lighter green boards'
IRON = 'dark painted transom iron'
GLASS = 'grey glass in the transom'
BRASS = 'worn brass lock and pull'
GREEN = 'blue green enamel address plaque'
CREAM = 'cream enamel digit'
PALETTE = {
    WOOD: dict(color=[.106, .153, .126], roughness=.69),
    BOARD: dict(color=[.125, .177, .147], roughness=.74),
    IRON: dict(color=[.104, .129, .111], metallic=.47, roughness=.63),
    GLASS: dict(color=[.222, .229, .211], metallic=.18, roughness=.35),
    BRASS: dict(color=[.543, .406, .234], metallic=.66, roughness=.52),
    GREEN: dict(color=[.033, .271, .216], metallic=.20, roughness=.43),
    CREAM: dict(color=[.897, .863, .679], roughness=.53),
}

# The outer width and height are estimated from the lock and the upper photograph.
WIDTH = .999
HEIGHT = 2.29
TRANSOM = (-.369, 1.557, .369, 1.990)
PANEL = (-.363, .094, .363, 1.443)


def lock_and_handle(facade, low):
    sides = 12 if low else 28
    for height, radius, thickness, name in [
        (1.140, .024, .013, 'circular lock face'),
        (1.025, .017, .010, 'pull upper mount'),
        (.895, .016, .011, 'pull lower mount'),
    ]:
        contour = Point(-.426, height).buffer(radius, quad_segs=sides//4)
        facade.prism(contour, .037, .037+thickness, BRASS, name)
    path = [(-.426, 1.025, .052), (-.427, 1.015, .079), (-.430, .987, .098),
            (-.433, .922, .098), (-.436, .903, .090), (-.435, .895, .052)]
    facade.builder.tube([facade.point(x,z,d) for x,z,d in path], .0075, BRASS, sides, 'No 9/hooked pull')
    # The short horizontal lever below the arched grip points left in the record.
    points = [facade.point(-.433,.900,.085), facade.point(-.447,.893,.089),
              facade.point(-.486,.889,.090)]
    facade.builder.tube(points, .006, BRASS, sides, 'No 9/lower brass lever')
    if not low:
        keyhole = box(-.428,1.129,-.424,1.146)
        facade.prism(keyhole,.0503,.051,IRON,'key slot in lock')


def make_door(builder, low=False):
    face = Facade(builder,(-.5,0),(.5,0),'No 9 lane door')
    xmin, zmin, xmax, zmax = TRANSOM
    # Both the grille and the glass are independent from the surrounding timber.
    panel = box(*PANEL)
    light = box(*TRANSOM)
    stile = box(-.480,.012,.480,2.106).difference(unary_union([panel, light]))
    face.prism(stile,.006,.038,WOOD,'mortised door stiles and rails')
    frame = box(-WIDTH/2,.002,WIDTH/2,HEIGHT).difference(box(-.483,.002,.483,2.113))
    face.prism(frame,-.305,.064,WOOD,'outer door jambs and deep lintel')
    face.prism(light,.008,.014,GLASS,'glazed opening behind the grille')
    face.prism(panel,.006,.019,WOOD,'recessed board bed')
    left,bottom,right,top = PANEL
    course = (right-left)/8
    for i in range(8):
        a = left+i*course
        face.prism(box(a+.0016,bottom,right-.0016 if i==7 else a+course-.0016,top),
                   .019,.027,BOARD,'eight vertical boards')
    flange = light.difference(box(xmin+.011,zmin+.011,xmax-.011,zmax-.011))
    face.prism(flange,.017,.039,IRON,'perimeter glazing rebate')
    for x in (-.074,.074):
        face.box(x,(zmin+zmax)/2,.010,zmax-zmin,.017,.039,IRON,'pair of full-height vertical rods')
    stepped = [(xmin,1.720),(-.228,1.720),(-.228,1.842),(.228,1.842),
               (.228,1.720),(xmax,1.720)]
    crossbar = LineString(stepped).buffer(.005, cap_style='flat', join_style='mitre')
    face.prism(crossbar,.034,.048,IRON,'continuous stepped transom bar')
    lock_and_handle(face,low)
    # Green No. 9 is documented at upper right. The cropped line of tiny street text is omitted.
    x,z=.406,2.160
    face.box(x,z,.190,.140,.012,.072,GREEN,'enamel address plaque')
    loop=[(x+.024*cos(2*pi*k/24), z+.015+.032*sin(2*pi*k/24)) for k in range(25)]
    tail=[(x+.023,z+.017),(x+.020,z-.012),(x+.013,z-.034),(x+.002,z-.045),(x-.010,z-.043)]
    number=unary_union([LineString(loop).buffer(.0048,quad_segs=2 if low else 4),
                         LineString(tail).buffer(.0048,quad_segs=2 if low else 4)])
    face.prism(number,.079,.083,CREAM,'single raised numeral 9')
    if not low:
        for u in (x-.080,x+.080):
            face.prism(Point(u,z).buffer(.0028,quad_segs=3),.078,.080,IRON,'small plaque attachment')
