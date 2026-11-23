"""Restored east doorway of the former Chinese YMCA on Sichuan Middle Road.

Facade coordinates are metres. X increases northwards and d is positive
towards the street. The shallow cut letters have closed sidewalls and floors.
Dimensions of ornament and its projection are estimated from the photographs.
"""
from functools import lru_cache
from math import cos, pi, sin
from pathlib import Path

from shapely import affinity
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union

from sign_lettering import lettering_shapes


STONE = 'YMCA grey bush-hammered stone'
EDGE = 'YMCA pale dressed moulding'
CUT = 'YMCA cut stone letters'
WOOD = 'YMCA dark timber'
PANEL = 'YMCA inset timber panels'
GLASS = 'YMCA amber fan glass'
FACE = 'YMCA ivory clock enamel'
INK = 'YMCA black clock markings'
METAL = 'YMCA aged bell metal'

PORTAL_MATERIALS = {
    STONE: {'color': [.485, .457, .407], 'roughness': .9},
    EDGE: {'color': [.52, .5, .455], 'roughness': .82},
    CUT: {'color': [.335, .308, .266], 'roughness': .95},
    WOOD: {'color': [.101, .058, .042], 'roughness': .5},
    PANEL: {'color': [.13, .077, .058], 'roughness': .55},
    GLASS: {'color': [.155, .104, .078], 'roughness': .28, 'metallic': .17},
    FACE: {'color': [.87, .84, .73], 'roughness': .55},
    INK: {'color': [.026, .03, .028], 'roughness': .55},
    METAL: {'color': [.247, .193, .123], 'roughness': .48, 'metallic': .52},
}
FONT = Path(__file__).parent / 'entrance_fonts' / 'PuguangEntranceStudy.otf'
ENGLISH = ('·CHINESE·', "·YOUNG·MEN'S·", 'CHRISTIAN·ASSOCIATION')
SOUTH = ('非㠯役人廼役於人', '光緒三十二年嵗次丙午仲夏')
NORTH = ('基督教中國青年會', '救主降生一千九百有六年')
SPRING = 2.77
RADIUS = 1.33


def course(face, x, bottom, top, width, back, front, material, label):
    face.box(x, (bottom + top) / 2, width, top - bottom,
             front - back, (front + back) / 2, material, label)


def arch(radius, steps):
    return Polygon([(radius*cos(pi*i/steps), SPRING+radius*sin(pi*i/steps))
                    for i in range(steps+1)])


def moulded_ring(face, steps):
    for inner, outer, back, front, material in [
        (1.33, 1.385, -.03, .113, STONE),
        (1.385, 1.448, -.025, .172, EDGE),
        (1.448, 1.507, -.025, .129, STONE),
        (1.507, 1.555, -.025, .177, EDGE),
    ]:
        band = arch(outer, steps).difference(arch(inner, steps))
        face.prism(band, back, front, material, 'round archivolt')
    face.prism(Polygon([(-.134,4.07),(.134,4.07),(.202,4.73),(-.202,4.73)]),
               .11,.255,EDGE,'trapezoid keystone')
    face.prism(Polygon([(-.116,4.18),(.116,4.18),(.157,4.66),(-.157,4.66)]),
               .251,.281,STONE,'keystone face')
    bead = Point(0,4.65).buffer(.091,quad_segs=10)
    face.prism(bead.intersection(box(-.1,4.53,.1,4.659)),
               .269,.292,EDGE,'keystone half round')
    for side in (-1,1):
        x = side*1.446
        course(face,x,2.66,2.755,.33,-.29,.198,EDGE,'arch impost')
        course(face,x,2.755,2.82,.39,-.28,.212,EDGE,'arch impost lip')
        course(face,x,0,2.66,.207,-.38,.031,STONE,'door stone reveal')


@lru_cache(maxsize=100)
def letters(text, width, height, lod):
    tolerance = .00185 if lod else .00075
    return tuple(shape.simplify(tolerance,preserve_topology=True)
                 for _,shape in lettering_shapes(text,width,height,font=FONT))


def cut_panel(face, slab, outlines, back, front, depth, label):
    # One continuous back and an actual void from the floor to the stone face.
    # The inscription has the colour of the shaded stone, without applied ink.
    mask = unary_union(outlines)
    assert slab.covers(mask), label
    face.prism(slab,back,front-depth-.001,STONE,label+' body')
    face.prism(slab.difference(mask),front-depth-.001,front,STONE,label+' cut')
    face.prism(mask,front-depth-.001,front-depth,CUT,label+' floor')


def outer_pier(face, side, lod):
    x = side*3.075
    lo, hi = (-3.97,-2.40) if side<0 else (2.39,3.92)
    # The historical and restored views show deep horizontal joints above and
    # below the writing, a concentric half-round shell and two projecting caps.
    for i in range(5):
        bottom = i*.512
        course(face,(lo+hi)/2,bottom,bottom+.484,hi-lo,-.17,.269,STONE,'base ashlar courses')
    for i in range(4):
        bottom = 4.88+i*.407
        course(face,(lo+hi)/2,bottom,bottom+.385,hi-lo,-.17,.269,STONE,'upper ashlar courses')
    for z0,z1,w,d in [(2.49,2.55,1.52,.294),(2.55,2.61,1.60,.311),
                       (4.80,4.86,1.61,.314),(4.86,4.94,1.57,.327),
                       (6.49,6.60,1.57,.335),(6.60,6.76,1.58,.405)]:
        course(face,(lo+hi)/2,z0,z1,min(w, hi-lo),-.17,d,EDGE,'pier course cornice')
    text, date = SOUTH if side<0 else NORTH
    shapes = []
    for inscription, axis, size, first, last in [
        (text,x,.224,4.64,2.77),(date,x+side*.536,.094,4.58,2.77)
    ]:
        for i,char in enumerate(inscription):
            z = first + (last-first)*i/(len(inscription)-1)
            for glyph in letters(char,size,size,lod):
                shapes.append(affinity.translate(glyph,xoff=axis,yoff=z))
    slab = box(lo,2.61,hi,4.81)
    cut_panel(face,slab,shapes,-.15,.295,.011,'south motto' if side<0 else 'north name')
    for offset in (-1,1):
        course(face,x+offset*.43,2.493,2.613,.20,.26,.334,EDGE,'panel sill tab')
    shell = Point(x,4.88).buffer(.338,quad_segs=9 if lod else 16).intersection(box(lo,4.88,hi,5.26))
    face.prism(shell,.27,.339,STONE,'half shell ground')
    for j in range(9):
        a = pi*(j+.5)/9
        petal = LineString([(x+.084*cos(a),4.88+.044*sin(a)),
                            (x+.286*cos(a),4.88+.258*sin(a))]).buffer(.012,cap_style='round')
        face.prism(petal,.337,.365,EDGE,'shell radial flutes')
    crown = shell.boundary.buffer(.027,join_style='round').intersection(box(lo,4.881,hi,5.27))
    face.prism(crown,.322,.378,EDGE,'shell outer hood')


def compound_capital(face, x, lod):
    # Square shafts and rectangular plinths, not round classical shafts.
    for z0,z1,width,projection in [
        (.012,.14,1.10,.459),(.14,.24,.96,.416),(.24,1.51,.855,.377),
        (1.51,1.59,.97,.443),(1.59,1.665,1.08,.487),
        (1.665,1.73,.812,.382),(1.73,5.60,.689,.334),
        (5.60,5.65,.746,.389),(5.65,5.72,.82,.443),
        (5.72,6.05,.835,.442),(6.05,6.275,.972,.49),
        (6.275,6.34,1.03,.515)]:
        course(face,x,z0,z1,width,-.138,projection,STONE if z1 in (1.51,5.60,6.05) else EDGE,
               'capital and square shaft')
    base_inset = Polygon([(x-.28,1.49),(x+.28,1.49),(x+.28,.73),
                          (x+.11,.73),(x+.11,.79),(x-.11,.79),(x-.11,.73),(x-.28,.73)])
    face.prism(base_inset,.376,.423,EDGE,'pier tabbed panel')
    for sign in (-1,1):
        cx,cz=x+sign*.336,6.065
        disk=Point(cx,cz).buffer(.148,quad_segs=8 if lod else 14)
        face.prism(disk,.416,.515,STONE,'volute boss')
        path=[]
        n=22 if lod else 47
        for i in range(n+1):
            ang=pi*.46-i/n*pi*3.76
            rad=.137*(1-i/n)+.015*i/n
            path.append((cx+sign*rad*cos(ang),cz+rad*sin(ang)))
        strip=LineString(path).buffer(.013 if lod else .015,quad_segs=3)
        face.prism(strip,.514,.543,EDGE,'capital spiral')
    for i in range(5):
        offset=(i-2)*.134
        x0=x+offset
        blade=Polygon([(x0-.054,5.754),(x0-.028,5.837),(x0+offset*.17-.039,5.888),
                       (x0+offset*.24,5.97-abs(offset)*.17),
                       (x0+offset*.17+.045,5.877),(x0+.022,5.83),(x0+.051,5.76)])
        face.prism(blade,.44,.484,EDGE,'capital foliate neck')
    crest=LineString([(x-.30,6.225),(x-.18,6.183),(x,6.145),(x+.18,6.183),
                      (x+.30,6.225)]).buffer(.021,join_style='round')
    face.prism(crest,.489,.522,EDGE,'capital swag')


def wooden_doors(face, lod):
    opening=box(-RADIUS,-.002,RADIUS,SPRING)
    face.prism(opening,-.613,-.561,WOOD,'two leaf door backing')
    for side in (-1,1):
        lo,hi=(-1.265,-.012) if side<0 else (.012,1.265)
        panels=[]
        for j in range(3):
            # The outer panels are longer and have no middle break in the photograph.
            x=side*(.218+j*.423)
            intervals=[(.17,.91),(1.04,2.51)] if j==2 else [(.17,.91),(1.04,1.65),(1.80,2.44)]
            for z0,z1 in intervals:
                shape=box(x-.15,z0,x+.15,z1);panels.append(shape)
                inset=shape.buffer(-.028,join_style='mitre')
                ring=shape.difference(inset)
                face.prism(ring,-.553,-.505,WOOD,'bevelled door rails')
                face.prism(inset,-.551,-.529,PANEL,'recessed door panels')
        leaf=box(lo,.068,hi,2.617)
        face.prism(leaf.difference(unary_union(panels)),-.561,-.483,WOOD,'timber door leaves')
        for j in (0,1):
            z=1.315+j*.351
            face.builder.tube([face.point(side*.087,z,-.46),face.point(side*.087,z,-.393)],
                              .022,METAL,7,'YMCA handle anchors')
        face.line((side*.087,1.315,-.391),(side*.087,1.666,-.391),.017,METAL,7,'leaf handles')
    for u in (-1.302,1.302):
        course(face,u,.05,2.70,.058,-.58,-.414,WOOD,'door frame jambs')
    course(face,0,2.62,2.755,2.665,-.57,-.359,WOOD,'door frame transom')
    course(face,0,.004,.078,2.665,-.615,.026,EDGE,'stone threshold')
    fan=arch(1.331,18 if lod else 38)
    face.prism(fan,-.589,-.537,GLASS,'amber fanlight')
    frame=fan.difference(arch(1.253,18 if lod else 38))
    bars=[box(x-.023,SPRING,x+.023,4.111) for x in (-.81,0,.81)]
    bars.append(box(-1.33,3.328,1.33,3.369))
    face.prism(frame.union(unary_union(bars).intersection(fan)),-.536,-.477,
               WOOD,'fanlight muntins')


def clock(face, lod):
    cx,cz=0,3.363
    n=14 if lod else 26
    def disc(r):
        return Point(cx,cz).buffer(r,quad_segs=n)
    for r,inner,d0,d1,material,label in [
        (.494,.448,-.466,-.317,WOOD,'dark clock frame'),
        (.461,.439,-.345,-.302,METAL,'clock bezel'),
        (.447,0,-.454,-.331,FACE,'clock enamel')]:
        shape=disc(r)
        face.prism(shape.difference(disc(inner)) if inner else shape,d0,d1,material,label)
    # 2023-04-29 detail uses IIII for four. Numerals follow the dial's curve.
    numerals=('XII','I','II','III','IIII','V','VI','VII','VIII','IX','X','XI')
    shapes=[]
    for i,text in enumerate(numerals):
        ang=2*pi*i/12
        for g in letters(text,.034*len(text)+.005,.099,lod):
            g=affinity.rotate(g,-i*30,origin=(0,0))
            shapes.append(affinity.translate(g,cx+.32*sin(ang),cz+.32*cos(ang)))
    for i in range(60):
        a=i*pi/30
        line=box(-.005,.397,.005,.422 if i%5==0 else .410)
        shapes.append(affinity.translate(affinity.rotate(line,-i*6,origin=(0,0)),cx,cz))
    face.prism(unary_union(shapes),-.330,-.325,INK,'Roman numerals and minute track')
    for i,(a,r,w) in enumerate([(17,.232,.020),(210,.374,.014)]):
        shape=Polygon([(-w*.54,-.066),(-w,r*.34),(-w*1.44,r*.53),
                       (0,r),(w*1.44,r*.53),(w,r*.34),(w*.54,-.066)])
        shape=affinity.translate(affinity.rotate(shape,-a,origin=(0,0)),cx,cz)
        face.prism(shape,-.320+.005*i,-.315+.005*i,INK,'clock hands')
    face.prism(disc(.028),-.31,-.299,METAL,'clock pivot')


def add_entrance(face, lod):
    steps=24 if lod else 48
    clear=arch(RADIUS,steps).union(box(-RADIUS,-.002,RADIUS,SPRING))
    # The upper central sash descends between the two pilasters and meets the tablet.
    outline = box(-3.97,0,3.92,7.08).difference(box(-1.74,6.37,1.74,7.081))
    face.prism(outline.difference(clear),-1.49,-.027,STONE,'door opening stone backing')
    moulded_ring(face,steps)
    for side,x in ((-1,-2.075),(1,2.045)):
        outer_pier(face,side,lod)
        compound_capital(face,x,lod)
    for z0,z1,w,d in [(4.68,4.74,3.51,.174),(4.74,4.81,3.48,.191),
                       (4.81,4.875,3.45,.159),(6.23,6.295,3.54,.181),
                       (6.295,6.37,3.57,.213)]:
        course(face,0,z0,z1,w,-.032,d,EDGE,'English tablet cornice')
    text=[]
    for words,z,w,h in zip(ENGLISH,(5.891,5.527,5.143),(1.35,2.13,3.12),(.234,.234,.212)):
        text.extend(affinity.translate(g,yoff=z) for g in letters(words,w,h,lod))
    cut_panel(face,box(-1.748,4.868,1.748,6.23),text,-.056,.129,.014,'English tablet')
    wooden_doors(face,lod)
    clock(face,lod)
