"""The two eastern shop openings and the meter panel visible in February 2018."""
import json
from pathlib import Path

from shapely.geometry import Point, Polygon, box
from shapely.ops import unary_union

from photo_architecture import Facade

DATA = json.loads((Path(__file__).resolve().parents[1] / 'measurements/east-shopfront-controls.json').read_text())
BOUNDS = DATA['control_bounds_m']

GREY = 'Xinle shopfront | grey painted pilaster and fascia'
GLASS = 'Xinle shopfront | warm display glass'
SHADOW = 'Xinle shopfront | shaded recess'
FRAME = 'Xinle shopfront | narrow pale metal frames'
BRONZE = 'Xinle shopfront | bronze fascia strokes'
GREEN = 'Xinle shopfront | deep green panelled leaf'
GREEN_EDGE = 'Xinle shopfront | enamel bead'
METER = 'Xinle shopfront | cream meter cabinet'
DARK = 'Xinle shopfront | meter and condenser grille'
PIPE = 'Xinle shopfront | painted conduit'
PALETTE = {
    GREY: {'color': [.29,.31,.34], 'roughness': .63},
    GLASS: {'color': [.26,.21,.15], 'roughness': .21, 'metallic': .15, 'alpha': .66},
    SHADOW: {'color': [.065,.055,.046], 'roughness': .9},
    FRAME: {'color': [.48,.47,.43], 'roughness': .43, 'metallic': .35},
    BRONZE: {'color': [.57,.40,.20], 'roughness': .28, 'metallic': .62},
    GREEN: {'color': [.038,.10,.064], 'roughness': .62},
    GREEN_EDGE: {'color': [.047,.134,.085], 'roughness': .48},
    METER: {'color': [.65,.646,.60], 'roughness': .79},
    DARK: {'color': [.13,.14,.14], 'roughness': .65},
    PIPE: {'color': [.62,.588,.51], 'roughness': .72},
}


def front_openings():
    return [box(*BOUNDS[name]) for name in ('display_opening','green_door_opening')]


def shop_glazing(face, opening):
    x0,z0,x1,z1 = opening.bounds
    surround = box(-8.719,z0,x1+.25,z1+.068)
    inner = opening.buffer(-.029,join_style=2)
    face.prism(surround.difference(inner),-.10,.069,GREY,'grey surround with two piers')
    face.prism(opening,-.368,-.352,SHADOW,'depth behind street display')
    # In the 2018 view the pale central stile belongs to the door on the right.
    meeting = -6.79
    for no,(left,right) in enumerate([(x0+.018,meeting-.012),(meeting+.012,x1-.018)]):
        leaf = box(left,z0+.014,right,z1-.015)
        glass = box(left+.028,z0+(.091 if no else .082),right-.029,z1-.040)
        face.prism(leaf.difference(glass),-.151,-.111,FRAME,'door frame' if no else 'fixed display frame')
        face.prism(glass,-.149,-.139,GLASS,'door glass' if no else 'fixed display glass')
    face.prism(box(x0-.007,z0-.037,x1+.007,z0+.014),-.208,.087,GREY,'low continuous sill')
    fascia = box(*BOUNDS['shop_fascia'])
    face.prism(fascia,.016,.124,GREY,'shop sign board')
    a,_,b,top=fascia.bounds
    face.prism(box(a,top-.019,b,top+.061),.049,.195,GREY,'top lip of shop board')
    for i,rings in enumerate(DATA['letter_polygons_XZ'],1):
        glyph=Polygon(rings[0],rings[1:])
        face.prism(glyph,.124,.139,BRONZE,f'raised sign strokes {i}')


def green_leaf(face, opening):
    left,bottom,right,top=opening.bounds
    frame=opening.buffer(-.073,join_style=2)
    face.prism(box(left-.038,bottom,right+.04,top+.058).difference(frame),-.12,.035,GREY,'rendered outer door lining')
    leaf=frame.buffer(-.009,join_style=2)
    face.prism(frame.difference(leaf.buffer(-.015,join_style=2)),-.13,-.061,GREEN_EDGE,'fixed green frame')
    face.prism(leaf,-.153,-.103,GREEN,'green entrance leaf')
    for z0,z1 in [(bottom+.16,1.08),(1.23,top-.18)]:
        panel=box(left+.15,z0,right-.15,z1)
        face.prism(panel.difference(panel.buffer(-.032,join_style=2)),-.102,-.087,GREEN_EDGE,'recessed panel surround')
    face.prism(box(left-.016,bottom-.035,right+.016,bottom+.007),-.18,.061,GREY,'door stone threshold')


def meter_and_condenser(face,b,lod):
    x0,z0,x1,z1=BOUNDS['meter_board']
    back=box(x0,z0,x1,z1)
    windows=[box(x-.052,z-.055,x+.052,z+.055)
             for x in [x0+.145,x1-.145] for z in [z1-.355,z1-.596,z1-.82]]
    face.prism(back,.005,.094,METER,'six-meter cabinet body')
    face.prism(back.difference(unary_union(windows)),.094,.127,METER,'cabinet face with six inspection recesses')
    for i,window in enumerate(windows,1):
        face.prism(window,.094,.104,DARK,f'meter inspection pane {i}')
    face.prism(box(x0+.19,z1-.18,x1-.19,z1-.153),.127,.136,DARK,'small header slot')
    x0,z0,x1,z1=BOUNDS['condenser']
    shell=box(x0,z0,x1,z1);centre=(x0+.245,(z0+z1)*.5)
    circle=Point(centre).buffer(.202,quad_segs=8 if lod else 16)
    face.prism(shell,.015,.236,METER,'wall condenser casing')
    face.prism(shell.difference(circle),.236,.258,METER,'front cover around circular fan')
    face.prism(circle,.236,.241,DARK,'visible dark fan recess')
    for x in [x0+.11,x1-.09]:
        face.prism(box(x-.018,z0-.047,x+.018,z0),.0,.229,DARK,'wall-supported condenser foot')
    if not lod:
        for r in [.072,.133,.177]:
            disc=Point(centre).buffer(r,quad_segs=14)
            face.prism(disc.difference(disc.buffer(-.0065)),.244,.25,FRAME,'concentric fan guard')
        face.prism(Point(centre).buffer(.041,quad_segs=12),.241,.256,FRAME,'fan hub')
    for i,(a,z,bottom) in enumerate([(-5.37,2.727,2.57),(-4.14,2.727,1.85)]):
        if i==0:
            face.prism(box(a,z-.02,-4.153,z+.02),.031,.065,PIPE,'horizontal visible service conduit')
        else:
            face.prism(box(a-.019,bottom,a+.019,z),.031,.066,PIPE,'drop beside door')


def add_front_shops(b,lod=False):
    face=Facade(b,(-1,0),(1,0),'Xinle east street frontage')
    display,door=front_openings()
    shop_glazing(face,display)
    green_leaf(face,door)
    meter_and_condenser(face,b,lod)
