"""Model the Yiyuan arch, side doorway, perforated wall, tile ends and iron leaves."""
import math
from pathlib import Path

from shapely.geometry import Polygon, box
from shapely.ops import unary_union
from photo_architecture import Facade
from sign_lettering import add_facade_lettering

FONT = Path(__file__).with_name('fonts') / 'YiyuanGateSign.otf'
PLASTER = 'warm pebble-dash plaster'
SOFFIT = 'cream painted arch soffit'
BASE = 'gray brown base brick'
JOINT = 'gray mortar'
TILE = 'weathered charcoal barrel tile'
CLAY = 'red clay barrel tile'
IRON = 'painted black iron'
GOLD = 'gilt iron ornament'
INK = 'black raised lane name'
ENAMEL = 'green enamel address'
TEXT = 'ivory sign lettering'
BRASS = 'brass plaque'
PALETTE = {name: {'color': colour, 'roughness': rough, 'metallic': metal}
           for name, colour, rough, metal in [
               (PLASTER,[.72,.66,.49],.93,0), (SOFFIT,[.79,.74,.59],.89,0),
               (BASE,[.34,.32,.28],.94,0), (JOINT,[.48,.46,.40],.96,0),
               (TILE,[.28,.29,.25],.84,0), (CLAY,[.48,.22,.15],.85,0),
               (IRON,[.10,.105,.098],.62,.50), (GOLD,[.68,.49,.22],.50,.48),
               (INK,[.115,.105,.083],.68,.22), (ENAMEL,[.055,.236,.174],.43,.16),
               (TEXT,[.91,.90,.75],.50,.06), (BRASS,[.59,.44,.19],.56,.53)]}
HALF = 1.65
SPRING = 3.45
LEFT, RIGHT = -3.55, 5.10
SIDE = -2.76
SIDE_HALF = .49
VENTS = (2.90, 3.32, 3.74, 4.16, 4.58)


def curve(centre, half, height, rise, steps):
    return [(centre+half*(2*i/steps-1), height+rise*(1-(2*i/steps-1)**2))
            for i in range(steps+1)]


def opening(centre, half, height, rise, steps):
    arc = curve(centre, half, height, rise, steps)
    return Polygon([(centre-half,-.02),(centre+half,-.02),*reversed(arc)])


def tile_run(builder, samples, radius, material, lod, label):
    """The hollow curved tile ends face the street. Each cap falls to both eaves."""
    sides = 5 if lod else 9
    for x,z in samples:
        coords = []
        for y, fall in ((-.10,-.01),(.26,.10),(.60,-.01)):
            for inner in (False,True):
                r = radius - (.022 if inner else 0)
                coords.extend((x+r*math.cos(math.pi*j/sides), y, z+fall+r*math.sin(math.pi*j/sides))
                              for j in range(sides+1))
        size = sides+1
        faces = []
        for row in range(2):
            a,b = row*2*size,(row+1)*2*size
            for j in range(sides):
                faces.extend([(a+j,b+j,b+j+1,a+j+1),(a+size+j+1,b+size+j+1,b+size+j,a+size+j)])
            for j in (0,sides):
                faces.append((a+j,a+size+j,b+size+j,b+j))
        for row in (0,2):
            a=row*2*size
            for j in range(sides):
                ring=(a+j,a+j+1,a+size+j+1,a+size+j)
                faces.append(ring if row==0 else ring[::-1])
        builder.add(coords,faces,material,label)


def masonry(builder, face, lod):
    steps=18 if lod else 38
    main=curve(0,1.97,3.64,.66,steps)
    secondary=curve(SIDE,.77,2.59,.33,steps)
    crest=[(LEFT,2.59),*secondary,(-1.986,3.60),*main,
           (2.07,3.61),(2.15,3.38),(2.23,3.12),(2.40,2.78),(2.53,2.62),(RIGHT,2.62)]
    # Only the lower portion of the secondary arch is adjacent to the west building.
    outer=Polygon([(LEFT,0),(RIGHT,0),*reversed(crest)])
    main_void=opening(0,HALF,SPRING,.60,steps)
    side_void=opening(SIDE,SIDE_HALF,2.34,.28,steps)
    vents=[box(x-.118,2.00,x+.118,2.236) for x in VENTS]
    cutouts=unary_union([main_void,side_void,*vents])
    shell=outer.difference(cutouts)
    face.prism(shell,-.51,0,PLASTER,'plaster wall and seven openings')
    for centre,half,z,rise in ((0,HALF,SPRING,.60),(SIDE,SIDE_HALF,2.34,.28)):
        arc=curve(centre,half,z,rise,steps)
        band=Polygon([*arc,*[(x,a+.035) for x,a in reversed(arc)]])
        face.prism(band,-.511,.002,SOFFIT,'pale arch soffit and front arris')
    base=shell.intersection(box(LEFT-.01,0,RIGHT+.01,.36))
    face.prism(base,-.512,.014,JOINT,'base-course mortar bed')
    for row in range(3):
        for col in range(27):
            left=LEFT+col*.37-(row%2)*.185
            block=box(left+.007,row*.12+.005,left+.363,(row+1)*.12-.005).intersection(base)
            if block.area>.002:
                face.prism(block,.0141,.024,BASE,'staggered base bricks')
    tile_run(builder,curve(0,1.97,3.64,.66,36),.061,TILE,lod,'main arch/charcoal tiled cap')
    tile_run(builder,curve(SIDE,.77,2.59,.33,15),.060,TILE,lod,'side passage/tiled cap')
    tile_run(builder,[(2.58+.116*i,2.62) for i in range(22)],.067,CLAY,lod,'east wall/red tiled coping')
    face.box(3.81,2.626,2.58,.08,.59,-.249,PLASTER,'coping under red tiles')
    face.box(2.002,2.724,.50,.167,.038,.022,ENAMEL,'green lane number plate')
    add_facade_lettering(face,'506弄1–57号',2.002,2.748,.453,.057,.0412,.046,
                         TEXT,label='enamel address and range',font=FONT)
    add_facade_lettering(face,'建国西路',2.002,2.682,.192,.038,.0412,.046,
                         TEXT,label='enamel street name',font=FONT)
    for glyph,z in zip('懿園',(2.316,1.827)):
        add_facade_lettering(face,glyph,2.005,z,.36,.419,.001,.030,
                             INK,label='raised vertical garden name',font=FONT)
    face.box(-1.855,1.85,.31,.21,.023,.014,BRASS,'plain bronze plaque on west pier')


def scroll(builder,x,z,rx,rz,hand,lod,label):
    pts=[]
    for i in range((12 if lod else 18)+1):
        t=i/(12 if lod else 18)
        ang=(.12+1.78*t)*math.pi
        pts.append((x+hand*rx*(1-.82*t)*math.cos(ang),.214,z+rz*(1-.82*t)*math.sin(ang)))
    builder.tube(pts,.012,GOLD,5 if lod else 7,label)


def ironwork(builder,face,side,lod):
    edge=1.615
    def arch(u):
        # The two sashes curve highest where they meet at the centre.
        return 2.19+.53*(1-(u/edge)**2)
    cx=side*edge/2
    label=('west leaf' if side<0 else 'east leaf')
    for x in (side*.015,side*edge):
        h=arch(x)
        face.box(x,(.045+h)/2,.042,h-.045,.075,-.253,IRON,label+'/stiles')
    for z,height in ((.085,.066),(.327,.041),(1.19,.045),(1.41,.053),(2.02,.040)):
        face.box(cx,z,edge-.015,height,.045,-.255,IRON,label+'/continuous bars')
    for down in (0,.208):
        pts=[(side*edge*i/22,.251,arch(edge*i/22)-down) for i in range(23)]
        builder.tube(pts,.020,IRON,5 if lod else 8,label+'/arched top rail')
    for i in range(1,10):
        x=side*edge*i/10
        h=arch(x)-.207
        face.box(x,(h+.10)/2,.020,h-.10,.031,-.256,IRON,label+'/slim pickets')
    for i in range(5):
        ax=side*(.14+.313*i)
        for z,sz,rx in ((.204,.080,.084),(1.300,.078,.094),(arch(ax)-.110,.077,.088)):
            if lod and z<.25 and i%2:continue
            for hand in (-1,1):
                scroll(builder,ax+hand*.042,z,rx,sz,hand,lod,label+'/paired gilt scrolls')
        if i%2==0:
            z=arch(ax)+.007
            body=Polygon([(ax-.026,z),(ax-.027,z+.049),(ax-.042,z+.065),(ax,z+.145),
                          (ax+.042,z+.065),(ax+.027,z+.049),(ax+.026,z)])
            face.prism(body,-.270,-.231,GOLD,label+'/floral finials')
    # Tall rectangular filigree strip next to the central meeting stile.
    for i in range(8):
        z=.47+.18*i
        if lod and i%2:continue
        for hand in (-1,1):
            scroll(builder,side*.119+hand*.028,z,.048,.066,hand,lod,label+'/meeting stile filigree')
    for z in (.265,1.774):
        builder.tube([(side*1.607,.255,z-.063),(side*1.607,.255,z+.063)],
                     .035,IRON,6 if lod else 10,label+'/hinges')


def gate(builder,lod):
    face=Facade(builder,(-6,0),(6,0),'Jianguo West Road')
    masonry(builder,face,lod)
    for side in (-1,1):ironwork(builder,face,side,lod)
