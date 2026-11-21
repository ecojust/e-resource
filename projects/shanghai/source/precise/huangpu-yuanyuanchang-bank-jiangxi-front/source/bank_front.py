"""Draw the east street wall of Yuanyuanchang Bank, 473 Middle Jiangxi Road."""
from math import cos, pi, sin
from pathlib import Path
from shapely.geometry import Point, Polygon, box
from shapely.ops import unary_union
from photo_architecture import Facade
from masonry import uv

WIDTH = 19.05446
HALF = WIDTH / 2
WING = 11.51
SHOULDER = 12.69
PILASTER = 13.02
PARAPET = 13.52
CREST = 14.17
WALL_DEPTH = .72
BRICK = 'brown firebrick and pale joints'
CEMENT = 'warm pale rendered cement'
SHADOW = 'shaded warm grey cement'
TRIM = 'chalk moulding arrises'
STONE = 'worn plinth stone'
PLINTH = 'faded terracotta skirting'
GLASS = 'smoky recessed glass'
FRAME = 'pale painted sash'
GATE = 'deep green entrance iron'
METAL = 'dull sill and window bars'
RECESS = 'dark timber and shadow'
PANEL = 'weathered shutter'
BRASS = 'muted bronze plate'
PALETTE = {
    BRICK: {'color': [1., 1., 1.], 'texture': str(Path(__file__).with_name('brown-firebrick.png')), 'roughness': .92},
    CEMENT: {'color': [.72, .674, .587], 'roughness': .86},
    SHADOW: {'color': [.45, .419, .367], 'roughness': .87},
    TRIM: {'color': [.806, .758, .651], 'roughness': .83},
    STONE: {'color': [.55, .528, .478], 'roughness': .87},
    PLINTH: {'color': [.47, .277, .211], 'roughness': .91},
    GLASS: {'color': [.20, .245, .265], 'roughness': .32, 'metallic': .10},
    FRAME: {'color': [.70, .706, .67], 'roughness': .64},
    GATE: {'color': [.101, .190, .144], 'roughness': .56, 'metallic': .31},
    METAL: {'color': [.342, .348, .321], 'roughness': .54, 'metallic': .50},
    RECESS: {'color': [.134, .132, .114], 'roughness': .80},
    PANEL: {'color': [.44, .444, .401], 'roughness': .68},
    BRASS: {'color': [.495, .421, .272], 'roughness': .67, 'metallic': .36},
    'carved pale stone': {'color': [.66, .63, .56], 'roughness': .83},
}

# From the south lane to the northern return, seen when facing the street wall.
STATIONS = (-7.42, -2.76, 0., 2.76, 7.42)
PILLARS = (-4.99, 4.99)


def half_disc(center, width, height, count):
    x, z = center
    return Polygon([(x-width/2, z), (x+width/2, z)] +
                   [(x+width/2*cos(pi*i/count), z+height*sin(pi*i/count)) for i in range(1, count)])


def pane(wall, cut, lod, columns, material=FRAME):
    x0, z0, x1, z1 = cut.bounds
    width, height = x1-x0, z1-z0
    wall.prism(cut.buffer(.012,join_style=2), -.36, -.335, GLASS, 'Recessed glazing')
    inner = cut.buffer(-.082, join_style=2)
    bars = [box(x0-1, z1-height*.22-.032, x1+1, z1-height*.22+.032)]
    for i in range(1, columns):
        x = x0 + width*i/columns
        bars.append(box(x-.033, z0, x+.033, z1))
    grid=cut.buffer(-.018,join_style=2).difference(inner.difference(unary_union(bars)))
    wall.prism(grid,-.245,-.135,material,'Transomed sash')
    wall.prism(cut.buffer(.105,join_style=2).difference(cut),-.04,.065,TRIM,'Rectangular window surrounds')
    wall.box((x0+x1)/2, z0-.075, width+.25, .15, .23 if lod else .29, .064, STONE, 'Projecting sills')


def entrance(wall, opening, lod):
    x0, z0, x1, z1 = opening.bounds
    wall.prism(opening.buffer(.01,join_style=2),-.69,-.66,RECESS,'Entrance back and transom shadow')
    wall.box(0, 1.98, 1.91, 3.42, .10, -.56, GATE, 'Current green gate leaves')
    wall.box(0, 3.79, 2.31, .11, .16, -.47, FRAME, 'Entrance transom')
    wall.box(0, .30, 1.88, .55, .07, -.48, GATE, 'Gate kick plate')
    for side in [-1,1]:
        wall.box(side*1.18, 2.13, .13, 4.21, .40, -.36, STONE, 'Stone door reveals')
        wall.box(side*.47, 2.04, .85, 3.26, .08, -.50, RECESS, 'Glazing behind gate bars')
        count=5 if lod else 10
        for i in range(count):
            x=side*.47 + (i-(count-1)/2)*(.80/count)
            wall.box(x, 2.07, .027 if not lod else .04, 3.13, .061, -.438, GATE, 'Entrance vertical ironwork')
    wall.box(0, 4.18, x1-x0-.12,.14,.30,-.23,STONE,'Door head')
    wall.prism(Polygon([(x0-.10,z1+.02),(x1+.10,z1+.02),(x1+.19,z1+.28),(x0-.19,z1+.28)]),
               .01,.13,BRICK,'Soldier course over entrance')
    for i in range(3):
        depth=.40-i*.105
        wall.box(0,.055+i*.092,2.18, .10, depth,.01+depth/2,STONE,'Three entrance steps')


def applied_pilaster(wall, x, lod):
    side=.61
    wall.box(x, PILASTER/2, side*2, PILASTER, .19, .042, CEMENT, 'Full height pilaster beds')
    low, high=1.56,11.99
    face=box(x-side,low,x+side,high)
    slots=[box(x+offset-.045,low+.14,x+offset+.045,high-.13) for offset in (-.29,0.,.29)]
    wall.prism(face,-.035,.168,SHADOW,'Flute ground')
    wall.prism(face.difference(unary_union(slots)),.155,.244,CEMENT,'Vertical rectangular flutes')
    for z, width,height,depth in [(.62,1.44,1.24,.31),(1.30,1.34,.13,.34),
            (5.21,1.49,.18,.41),(5.36,1.52,.09,.47),(12.17,1.35,.17,.31),
            (12.46,1.42,.52,.35),(12.79,1.58,.14,.44),(12.94,1.66,.10,.47)]:
        wall.box(x,z,width,height,depth,depth/2-.038,CEMENT,'Stepped pilaster bases and capitals')
    crest=half_disc((x,12.26),.66,.30,8 if lod else 16)
    wall.prism(crest,.305,.338,SHADOW,'Fan in pilaster capital')
    if not lod:
        for i in range(1,8):
            ang=pi*i/8
            wall.line((x,12.265,.352),(x+.30*cos(ang),12.265+.26*sin(ang),.352),.012,TRIM,5,'Capital fan rays')


def emblem(wall,lod):
    seg=14 if lod else 32
    center=11.69
    shape=box(-2.11,center-.47,2.11,center+.47).buffer(.14,join_style=1,quad_segs=4)
    disc=Point(0,center).buffer(.75,quad_segs=seg//4)
    wall.prism(shape.union(disc),.014,.19,CEMENT,'Winged roundel base')
    for j in range(5 if not lod else 3):
        z=center+(j-(2 if not lod else 1))*(.176 if not lod else .28)
        for side in [-1,1]:
            wall.box(side*1.45,z,1.30,.036,.04,.209,SHADOW,'Horizontal relief wings')
    wall.prism(disc,.17,.251,TRIM,'Circular medallion lip')
    wall.prism(Point(0,center).buffer(.653,quad_segs=seg//4),.237,.277,CEMENT,'Recess-free roundel face')
    wall.prism(Point(0,center).buffer(.091,quad_segs=seg//4),.27,.305,SHADOW,'Small central round boss')
    inner=half_disc((0,PARAPET),1.83,CREST-PARAPET,seg)
    wall.prism(inner,-.46,.128,TRIM,'Semicircular parapet crest')
    wall.prism(half_disc((0,PARAPET),1.56,CREST-PARAPET-.11,seg),.118,.160,CEMENT,'Crest face')
    if not lod:
        for i in range(1,18):
            theta=pi*i/18
            wall.line((.44*cos(theta),PARAPET+.31*sin(theta),.167),
                      (.70*cos(theta),PARAPET+.49*sin(theta),.167),.012,SHADOW,5,'Crest fluting')


def add_building(builder,lod=False):
    face=Facade(builder,(-HALF,0),(HALF,0),'Jiangxi east')
    outline=Polygon([(-HALF,0),(HALF,0),(HALF,WING),(5.56,WING),(5.56,SHOULDER),
                     (4.05,SHOULDER),(4.05,PARAPET),(-4.05,PARAPET),(-4.05,SHOULDER),
                     (-5.56,SHOULDER),(-5.56,WING),(-HALF,WING)])
    upper=[];lower=[]
    for i,x in enumerate(STATIONS):
        width=(2.05,.83,2.20,.83,2.05)[i]
        upper.append(box(x-width/2,6.51,x+width/2,9.54))
        width=(2.68,1.81,2.74,1.81,2.19)[i]
        base=(.06,1.51,.04,1.51,1.46)[i]
        lower.append(box(x-width/2,base,x+width/2,4.45 if i in (0,2) else 4.19))
    skin=face.wall(0,PARAPET,upper+lower,thickness=WALL_DEPTH,material=BRICK,outline=outline)
    for low,high,material in [(0,.45,PLINTH),(.45,1.30,CEMENT)]:
        face.prism(skin.intersection(box(-HALF,low,HALF,high)),-.015,.052,material,'Two-tone rendered base')
    for i,cut in enumerate(upper):
        pane(face,cut,lod,2 if i in (0,2,4) else 1)
        x=STATIONS[i]
        if i in (0,2,4):
            z=9.72
            face.box(x,z,cut.bounds[2]-cut.bounds[0]+.42,.20,.27,.064,CEMENT,'Upper window heads')
        if not lod and i in (0,2,4):
            for xoff in (-.58,.58):
                face.box(x+xoff,6.34,.11,.19,.16,.106,SHADOW,'Window sill brackets')
    for i in (1,3,4):
        cut=lower[i];pane(face,cut,lod,2 if i==4 else 1)
        a,z,b,t=cut.bounds;cnt=5 if lod else 12
        for j in range(cnt):
            face.box(a+.12+(b-a-.24)*(j+.5)/cnt,(z+t)/2,.025 if not lod else .040,t-z-.17,.055,
                     -.065,METAL,'Ground window protection bars')
        face.box((a+b)/2,t+.16,b-a+.61,.19,.37,.11,TRIM,'Ground window projecting lintel')
    a,z,b,t=lower[0].bounds
    face.prism(lower[0].buffer(.01,join_style=2),-.45,-.41,PANEL,'Southern shop shutter')
    for j in range(12 if lod else 38):
        h=z+(t-z)*(j+.5)/(12 if lod else 38)
        face.box((a+b)/2,h,b-a-.04,.025,.05,-.382,METAL,'Horizontal shutter ribs')
    entrance(face,lower[2],lod)
    for x in PILLARS:applied_pilaster(face,x,lod)
    for x in (-7.56,7.56):
        face.box(x,WING-.35,3.95,.66,.32,.067,CEMENT,'Outer bay stucco parapets')
        face.box(x,WING-.62,3.97,.086,.37,.121,TRIM,'Outer cornice lower edges')
        face.box(x,WING-.05,4.02,.104,.42,.126,TRIM,'Outer cornice caps')
    for x in (-4.86,4.86):
        face.box(x,SHOULDER-.18,1.74,.36,.30,.065,CEMENT,'Central parapet shoulder')
        face.box(x,SHOULDER-.01,1.86,.105,.40,.108,TRIM,'Shoulder caps')
    face.box(0,PARAPET-.15,8.09,.30,.30,.086,CEMENT,'Central parapet belt')
    face.box(0,PARAPET-.005,8.23,.095,.37,.113,TRIM,'Central parapet cap')
    emblem(face,lod)
    # The plaque is recognizable by its shape and mounting; the inscription is recorded in the source register.
    face.box(-1.08,1.93,.47,.83,.045,-.386,BRASS,'Heritage plaque beside gate')
    for group in builder.parts:
        if group['material']==BRICK:
            group['texcoords']=[uv(*point) for point in group['vertices']]
