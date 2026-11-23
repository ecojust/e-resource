"""Northeast entrance and tower of the Land Bank of China, 239 East Beijing Road."""
from math import cos, pi, sin

from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union

from photo_architecture import Facade

WIDTH = 7.10352
HEIGHT = 44.70
HALF = WIDTH / 2
WINDOW_LEVELS = (11.53, 15.12, 18.73, 22.35, 25.94, 29.55, 33.13, 36.73, 40.31)
WINDOW_STATIONS = ((-1.64, 1.10), (0, 1.30), (1.64, 1.10))
WALL = 'pale grey stone facing'
WASH = 'soft grey joint and reveal'
TRIM = 'pale stone at the arris'
GRANITE = 'warm ashlar entrance granite'
EDGE = 'weathered stone relief'
GLASS = 'recessed blue grey window'
FRAME = 'dark window frames'
SILL = 'upper stone sills'
IRON = 'black iron entrance rail'
HIGHLIGHT = 'weathered raised iron'
BACK = 'entrance recess shadow'
PLATE = 'old sign plate beds'
BRASS = 'bronze street plaque'
PALETTE = {
    WALL: {'color': [.76,.75,.717], 'roughness': .87},
    WASH: {'color': [.60,.594,.568], 'roughness': .88},
    TRIM: {'color': [.81,.797,.755], 'roughness': .83},
    GRANITE: {'color': [.61,.547,.465], 'roughness': .83},
    EDGE: {'color': [.486,.461,.410], 'roughness': .91},
    GLASS: {'color': [.26,.326,.360], 'roughness': .32, 'metallic': .17},
    FRAME: {'color': [.255,.259,.243], 'roughness': .63},
    SILL: {'color': [.664,.646,.599], 'roughness': .82},
    IRON: {'color': [.13,.141,.144], 'roughness': .58, 'metallic': .55},
    HIGHLIGHT: {'color': [.22,.227,.221], 'roughness': .53, 'metallic': .59},
    BACK: {'color': [.142,.139,.126], 'roughness': .85},
    PLATE: {'color': [.377,.371,.327], 'roughness': .91},
    BRASS: {'color': [.55,.474,.350], 'roughness': .53, 'metallic': .38},
}

def line(wall, points, depth, radius, material, label, lod):
    wall.builder.tube([wall.point(u,z,depth) for u,z in points],radius,material,4 if lod else 6,wall.label+'/'+label)


def ring(wall,x,z,rx,ry,depth,radius,material,label,lod):
    steps = 12 if lod else 24
    path = [(x+rx*cos(2*pi*i/steps),z+ry*sin(2*pi*i/steps)) for i in range(steps+1)]
    line(wall,path,depth,radius,material,label,lod)


def sash(wall,x,z,width,lod):
    height=2.22
    aperture=box(x-width/2,z-height/2,x+width/2,z+height/2)
    wall.prism(aperture.buffer(.015,join_style=2),-.34,-.31,GLASS,'Window glazing')
    bars=[box(x-width,z+.47,x+width,z+.54)]
    if not lod or width>1.2:
        bars.append(box(x-.036,z-height/2,x+.036,z+.51))
    frame=aperture.difference(aperture.buffer(-.065,join_style=2).difference(unary_union(bars)))
    wall.prism(frame,-.27,-.19,FRAME,'Transomed window frames')
    wall.prism(aperture.buffer(.065,join_style=2).difference(aperture),-.023,.059,TRIM,'Inset window margins')
    wall.box(x,z-height/2-.10,width+.16,.16,.31,.070,SILL,'Projecting window sills')
    wall.box(x,z+height/2+.11,width+.19,.13,.15,.035,TRIM,'Shallow window hoods')


def door_leaf(wall,x,side,lod):
    low,high=.38,5.97
    width=1.995
    leaf=box(x-width/2,low,x+width/2,high)
    inside=leaf.buffer(-.123,join_style=2)
    wall.prism(leaf.difference(inside),-.286,-.191,IRON,'Double door leaf frame')
    for offset in (-.78,-.64,-.40,.4,.64,.78):
        wall.box(x+offset,(low+high)/2,.034 if not lod else .045,high-low-.27,.077,-.239,IRON,'Gate vertical grille rods')
    wall.box(x,3.12,1.79,.12,.081,-.219,IRON,'Grille rails')
    wall.box(x,5.68,1.79,.058,.075,-.228,IRON,'Grille rails')
    for level in (1.37,4.87):
        for i in range(1 if lod else 3):
            rx=.37-i*.097;rz=.57-i*.145
            line(wall,[(x,level+rz),(x+rx,level),(x,level-rz),(x-rx,level),(x,level+rz)],-.181,.025,HIGHLIGHT,'Stacked gate diamonds',lod)
    face=Point(x,3.12).buffer(.429,quad_segs=6 if lod else 12)
    wall.prism(face,-.220,-.145,IRON,'Plain circular iron boss')
    ring(wall,x,3.12,.440,.440,-.126,.027,HIGHLIGHT,'Iron boss rim',lod)
    for level in (2.38,3.87,5.60):
        ring(wall,x,level,.195,.195,-.199,.023,HIGHLIGHT,'Open grille rosettes',lod)
        if not lod:
            for i in range(8):
                a=pi*i/4;line(wall,[(x+.072*cos(a),level+.072*sin(a)),(x+.197*cos(a),level+.197*sin(a))],-.195,.015,HIGHLIGHT,'Rosette radial spokes',lod)
    if not lod:
        for flank in (-1,1):
            for i in range(12):
                z=.57+i*.427;cx=x+flank*.931
                line(wall,[(cx-.067,z+.08),(cx-.035,z-.042),(cx,z-.075),(cx+.036,z-.04),(cx+.067,z+.08)],-.164,.016,HIGHLIGHT,'Pressed border scallops',lod)


def main_portal(wall,lod):
    opening=box(-2.105,.31,2.105,8.70)
    stone=box(-HALF,0,HALF,10.24)
    wall.prism(stone.difference(opening),-.075,.128,GRANITE,'Granite entrance block')
    wall.prism(opening.buffer(.018,join_style=2),-.665,-.637,BACK,'Dark backing behind iron gates')
    wall.prism(opening.buffer(.125,join_style=2).difference(opening),.105,.235,EDGE,'Portal stone rebate')
    wall.prism(opening.difference(opening.buffer(-.082,join_style=2)),-.316,-.121,IRON,'Iron door jambs')
    for side in (-1,1):
        door_leaf(wall,side*1.015,side,lod)
        panel=box(side*1.007-.924,6.80,side*1.007+.924,8.49)
        wall.prism(panel.difference(panel.buffer(-.095,join_style=2)),-.264,-.168,IRON,'Upper iron grilles')
        for j in range(6 if lod else 10):
            x=side*1.007+(j-(5 if lod else 9)/2)*(.119 if not lod else .187)
            wall.box(x,7.65,.028,1.45,.074,-.229,IRON,'Upper transom bars')
        for z in (7.20,7.64,8.08):
            line(wall,[(side*1.007-.32,z+.19),(side*1.007,z-.14),(side*1.007+.32,z+.19)],-.158,.028,HIGHLIGHT,'Upper transom chevrons',lod)
    wall.box(0,6.37,4.18,.71,.19,-.205,IRON,'Broad iron frieze')
    for j in range(8):
        x=(j-3.5)*.47
        line(wall,[(x-.18,6.23),(x,6.54),(x+.18,6.23)],-.098,.019,HIGHLIGHT,'Iron frieze fan accents',lod)
    for j in range(6):
        x=(j-2.5)*.696;panel=box(x-.290,9.49,x+.290,10.12)
        wall.prism(panel,.124,.151,PLATE,'Weathered former sign beds')
        wall.prism(panel.buffer(.045,join_style=2).difference(panel),.128,.169,EDGE,'Old sign bed margins')
    for side in (-1,1):
        x=side*2.77
        relief=box(x-.32,9.40,x+.32,10.08)
        wall.prism(relief,.125,.178,TRIM,'Entrance lintel end tablets')
        line(wall,[(x,9.99),(x+.22,9.73),(x,9.48),(x-.22,9.73),(x,9.99)],.192,.032,EDGE,'Lintel diamond tablets',lod)
        for z in (.98,2.12,3.26,4.40,5.54,6.68,7.82,8.96):
            wall.box(side*2.86,z,1.26,.026,.035,.137,EDGE,'Granite horizontal joints')
        for j in (-1,0,1):
            wall.box(side*(2.89+.113*j),8.91,.052,3.18,.083,.165,GRANITE,'Stepped outer stone pilaster')
    for j in range(3):
        depth=.51-j*.14
        wall.box(0,.052+j*.099,4.24,.107,depth,depth/2+.022,GRANITE,'Three threshold treads')
    wall.box(-2.77,2.21,.61,.34,.05,.18,BRASS,'Bronze wall plaque')


def add_building(builder,lod=False):
    wall=Facade(builder,(-HALF,0),(HALF,0),'Northeast')
    profile=[(HALF,0),(HALF,32.1),(3.40,32.1),(3.40,34.52),(3.24,34.52),
             (3.24,39.32),(3.10,39.32),(3.10,41.67),(2.95,41.67),(2.95,42.78),
             (2.70,42.78),(2.70,43.51),(2.38,43.51),(2.38,43.96),(2.02,43.96),
             (2.02,44.24),(1.59,44.24),(1.59,44.43),(.88,44.43),(.88,44.58),(0,HEIGHT)]
    outline=Polygon(profile+[(-x,z) for x,z in reversed(profile[:-1])]);holes=[box(-2.105,.31,2.105,8.70)]
    for z in WINDOW_LEVELS:
        holes.extend(box(x-width/2,z-1.11,x+width/2,z+1.11) for x,width in WINDOW_STATIONS)
    slots=[box(x-.123,42.57,x+.123,43.26) for x in (-.54,.54)];holes.extend(slots)
    skin=wall.wall(0,HEIGHT,holes,thickness=.78,material=WALL,outline=outline)
    raised=outline.intersection(box(-HALF,32.00,HALF,HEIGHT+.01))
    wall.prism(raised,-2.38,-.785,WALL,'Tower return and roof backing')
    for slot in slots:wall.prism(slot.buffer(.025,join_style=2),-.285,-.26,BACK,'Two crown ventilation slots')
    for z in WINDOW_LEVELS:
        for x,width in WINDOW_STATIONS:sash(wall,x,z,width,lod)
        for x in (-1.65,0,1.65):
            panel=box(x-.40,z+1.40,x+.40,z+1.99)
            wall.prism(panel,.004,.035,WALL,'Recessed spandrel panels')
            wall.prism(panel.buffer(.042,join_style=2).difference(panel),.010,.059,WASH,'Spandrel panel arrises')
    for x in (-2.57,-.835,.835,2.57):
        width=.23 if abs(x)>2 else .144
        wall.box(x,26.64,width,31.57,.190,.055,TRIM,'Continuous vertical window piers')
        wall.box(x,41.49,width+.055,2.11,.235,.072,TRIM,'Tower pier capitals')
        wall.box(x,42.59,width,.45,.17,.051,WALL,'Pier capital returns')
    for side in (-1,1):
        for off,height in ((3.40,31.95),(3.23,34.49),(3.058,39.28)):
            wall.box(side*off,(height+9.97)/2,.095,height-9.97,.15,.045,WASH,'Stepped corner shoulder flutes')
    main_portal(wall,lod)
