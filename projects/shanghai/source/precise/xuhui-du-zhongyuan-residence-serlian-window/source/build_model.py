"""Model the Serlian window on the garden side of 1897 Middle Huaihai Road."""
from math import cos, pi, sin
from pathlib import Path
import argparse
import os
import sys

from shapely.geometry import LineString, Polygon, box as rect

SOURCE = Path(__file__).resolve().parent
sys.path.insert(0, str(SOURCE.parents[3] / 'tools'))
import package_architectural_model as package
sys.path.insert(0, str(SOURCE.parents[1] / 'huangpu-somekh-building-street-corner/source'))
from aggregate_mesh import AggregateBuilder
from photo_architecture import Facade, opening
from garden_plaster import STONE, assign_uvs

ID = 'xuhui-du-zhongyuan-residence-serlian-window'
META = dict(id=ID, name='杜重远寓所南花园西端帕拉第奥式窗', viewer_page='du-zhongyuan-residence-serlian-window.html',
            heritage_group='4D007', heritage_address='淮海中路1897号',
            scope='南花园立面西端底层窗组，包括半圆券、两侧平过梁窄窗、卷涡券心石与红木色窗扇。',
            coordinate_convention='Local metres. +X runs towards the centre of the garden elevation. +Y runs into the wall. Z is up.',
            status='documented-garden-window')
STONE_TRIM = 'Pale dressed arch stone'
TIN = 'Shadow below stone lip'
RED = 'Red brown timber joinery'
DARK = 'Deep red glazing bead'
FAN = 'Bronze fanlight bars'
GLASS = 'Shaded garden glazing'
SKY = 'Pale reflected garden glazing'
PLINTH = 'West window sill and plinth'


def color(rgb, roughness, metal=0):
    def linear(c):
        c /= 255
        return c / 12.92 if c <= .04045 else ((c + .055) / 1.055) ** 2.4
    return dict(color=[linear(c) for c in rgb], roughness=roughness, metallic=metal)


PALETTE = {
    STONE: dict(color=[1, 1, 1], roughness=.90, texture=str(SOURCE/'garden-plaster.png')),
    STONE_TRIM: color((202,195,174),.78), TIN: color((134,127,112),.85),
    RED: color((113,64,54),.55), DARK: color((83,57,50),.67), FAN: color((75,70,57),.56,.27),
    GLASS: color((85,105,104),.26,.24), SKY: color((136,153,151),.24,.25),
    PLINTH: color((168,159,139),.80),
}
RADIUS, SPRING, SILL = 1.11, 2.08, .27
SHAFT_X, OUTER_EDGE, WIDTH = 1.235, 2.39, 5.67


def semicircle(inner, outer, start, stop, samples):
    def points(radius, a, b):
        return [(radius*cos(a+(b-a)*i/samples), SPRING+radius*sin(a+(b-a)*i/samples))
                for i in range(samples+1)]
    return Polygon(points(outer,start,stop) + points(inner,stop,start))


def glazing(f, center, width, low, high, columns, transom, name, sky=False):
    """Use separate panes and timber bars behind the masonry returns."""
    gap = .033
    for i in range(columns):
        x = center-width/2+(i+.5)*width/columns
        for j, (bottom, top) in enumerate([(low,transom),(transom,high)]):
            material = SKY if (sky or j == 1) else GLASS
            f.box(x,(top+bottom)/2,width/columns,top-bottom,.025,-.265,material,name+' glass')
    for i in range(columns+1):
        x = center-width/2+i*width/columns
        w = .062 if i in (0,columns) else .052
        f.box(x,(high+low)/2,w,high-low+.025,.09,-.204,RED,name+' stiles')
        for side in (-1,1):
            outside = (i == 0 and side < 0) or (i == columns and side > 0)
            if outside:
                continue
            f.box(x+side*(w/2+gap/4),(high+low)/2,gap/2,high-low,.033,-.227,DARK,name+' glazing beads')
    for z, h in [(low,.078),(transom,.058),(high,.073)]:
        f.box(center,z,width+.059,h,.086,-.201,RED,name+' rails')


def arch(f,b,lod):
    segments=24 if lod else 72
    half_disk=opening(0,SPRING-.012,2*RADIUS,RADIUS+.012,RADIUS,segments)
    f.prism(half_disk,-.276,-.252,GLASS,'Semicircular fanlight glass')
    for a,c,back,front,mat,name in [
        (RADIUS-.026,RADIUS+.026,-.230,-.174,FAN,'Timber and bronze fanlight perimeter'),
        (RADIUS,RADIUS+.065,-.012,.055,STONE_TRIM,'Inner archivolt rebate'),
        (RADIUS+.066,RADIUS+.093,-.016,.028,TIN,'Shadow between arch mouldings'),
        (RADIUS+.089,RADIUS+.142,-.008,.081,STONE_TRIM,'Projecting outer arch moulding')]:
        f.prism(semicircle(a,c,0,pi,segments),back,front,mat,name)
    # The oblique 2018 photograph shows a sector fan behind the arched outer reveal.
    for i in range(1,8):
        t=i*pi/8
        b.tube([f.point(r*cos(t),SPRING+r*sin(t),-.211)for r in (.06,RADIUS-.022)],
               .011,FAN,5 if lod else 9,'Fanlight/Glazing spokes')
    f.prism(semicircle(.34,.365,0,pi,16 if lod else 40),-.224,-.197,FAN,'Fanlight inner half ring')
    f.box(0,SPRING-.018,2*RADIUS+.09,.087,.104,-.159,RED,'Fanlight sill rail')


def keystone(f,b,lod):
    crown = SPRING+RADIUS
    outline = Polygon([(-.111,crown-.018),(.111,crown-.018),(.170,crown+.24),
                       (.149,crown+.32),(-.149,crown+.32),(-.170,crown+.24)])
    f.prism(outline,.026,.190,STONE_TRIM,'Projecting keystone block')
    f.box(0,crown+.286,.357,.074,.211,.133,STONE_TRIM,'Keystone top lip')
    # A rolled horizontal stone scroll joins the two side cheeks. Carry its
    # curved bed across the width so it remains readable from the garden.
    count = 18 if lod else 52
    curve = []
    for i in range(count+1):
        fraction = i/count
        angle = -pi/2 + 1.75*pi*fraction
        radius = .093*(1-.78*fraction)
        curve.append((.199+radius*cos(angle), crown+.137+radius*sin(angle)))
    ribbon = LineString(curve).buffer(.016, quad_segs=3 if lod else 6)
    # The side-plane coordinates are outward depth and elevation. Its normal
    # points along -X, so increasing the extrusion coordinate runs westward.
    mapper = lambda depth,elevation,side: (-side,-depth,elevation)
    b.prism(ribbon,-.128,.128,mapper,STONE_TRIM,'Keystone/Carved horizontal scroll')
    for side in (-1,1):
        b.tube([f.point(side*.130,z,depth) for depth,z in curve],
               .010,STONE_TRIM,6 if lod else 10,'Keystone/Returned volute')
    f.box(0,crown+.078,.225,.042,.112,.189,STONE_TRIM,'Keystone lower roll')


def add_building(b,lod):
    f=Facade(b,(-WIDTH/2,0),(WIDTH/2,0),'Garden west window')
    segments=24 if lod else 72
    opening_shape=opening(0,SPRING-.015,2*RADIUS,RADIUS+.015,RADIUS,segments)
    lower=rect(-OUTER_EDGE,SILL,OUTER_EDGE,SPRING)
    f.wall(0,SPRING+RADIUS+.60,[lower,opening_shape],.51,STONE)
    f.box(0,.105,WIDTH,.21,.55,-.23,PLINTH,'Low base course')
    f.box(0,SILL-.020,2*OUTER_EDGE+.15,.082,.64,-.165,STONE_TRIM,'Projecting sill')
    # The square side lights sit behind the two round columns. The central pair has a broader meeting stile.
    glazing(f,0,1.49,SILL+.016,SPRING-.063,2,1.25,'Central paired sash')
    for side in (-1,1):
        label='West' if side<0 else 'East'
        edges=[.745,1.57,OUTER_EDGE]
        for a,c,name in zip(edges,edges[1:],['inner sidelight','outer sidelight']):
            glazing(f,side*(a+c)/2,c-a,SILL+.016,SPRING-.063,1,1.25,label+' '+name,sky=name.startswith('outer'))
        for height,thick,deep,mat in [(SPRING-.055,.092,.27,STONE_TRIM),(SPRING+.010,.034,.30,TIN),(SPRING+.051,.067,.32,STONE_TRIM)]:
            f.box(side*(OUTER_EDGE+RADIUS)/2,height,OUTER_EDGE-RADIUS+.11,thick,deep,.010,mat,label+' lateral lintel')
        x=side*SHAFT_X
        f.box(x,SILL+.045,.35,.099,.37,.055,PLINTH,label+' square column foot')
        profile=[(SILL+.093,.166),(SILL+.116,.164),(SILL+.147,.153),(SILL+.172,.140),
                 (SILL+.192,.132),(.67,.132),(1.58,.121),(1.84,.115),(1.866,.116),
                 (1.880,.137),(1.910,.139),(1.938,.125),(1.973,.152),(2.007,.167)]
        b.lathe((x,-.054),profile,STONE_TRIM,18 if lod else 52,label+' freestanding column')
        f.box(x,2.022,.36,.053,.37,.054,STONE_TRIM,label+' abacus')
    arch(f,b,lod)
    keystone(f,b,lod)
    assign_uvs(b)


if __name__=='__main__':
    parser=argparse.ArgumentParser(add_help=False)
    parser.add_argument('--blender',default='blender')
    args,extra=parser.parse_known_args()
    os.environ['DU_GARDEN_BLENDER']=args.blender
    sys.argv[1:]=[*extra,'--blender',str(SOURCE/'native_blender.py')]
    package.Builder=AggregateBuilder
    package.build(SOURCE,META,PALETTE,add_building)
