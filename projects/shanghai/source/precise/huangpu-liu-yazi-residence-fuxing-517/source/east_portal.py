"""Two-stage east staircase, moulded brick voussoirs and deep red entrance tunnel."""
from math import cos, sin, pi
from pathlib import Path
from shapely.geometry import Polygon, box
from shapely import affinity
from photo_architecture import opening
from sign_lettering import add_facade_lettering
from villa_materials import BRICK, MORTAR, ROUGH, SILL, STONE, WOOD, IRON, SASH, LIGHT, DARK
from villa_roof import HALF_WALL

AXIS=4.19
SILL_Z=1.41
SPRING=5.25
CLEAR=.615
FONT=Path(__file__).with_name('lettering')/'SinanEntryLabels.otf'


def cut_shape(lod):
    return opening(AXIS,SILL_Z,2*CLEAR,SPRING+CLEAR-SILL_Z,arch=CLEAR,segments=20 if lod else 54)


def sector(centre,z,inner,outer,start,end,n):
    arc=[start+(end-start)*i/n for i in range(n+1)]
    return Polygon([(centre+outer*cos(a),z+outer*sin(a)) for a in arc]
                   +[(centre+inner*cos(a),z+inner*sin(a)) for a in reversed(arc)])


def brick_surround(face,lod):
    n=18 if lod else 52
    face.prism(sector(AXIS,SPRING,CLEAR,1.115,0,pi,n),-.039,.092,MORTAR,'brick arch mortar joints')
    for row,(r0,r1,front,count) in enumerate(((.617,.943,.130,45),(.947,.995,.167,47),
                                               (1.001,1.055,.204,45),(1.060,1.110,.165,47))):
        if lod:count=17 if row==0 else 9
        for j in range(count):
            a0=(j+.042)*pi/count;a1=(j+.958)*pi/count
            face.prism(sector(AXIS,SPRING,r0,r1,a0,a1,2 if lod else 4),
                       .081,front,BRICK,'radial brick arch course '+str(row+1))
    for side in (-1,1):
        x=AXIS+side*(CLEAR+.205)
        for i in range(5):
            face.box(x,SPRING-.043-i*.083,.407,.075,.18,.031,BRICK,'brick arch spring blocks')
        for z,width,dep in ((SPRING+.046,.50,.24),(SPRING+.118,.55,.29)):
            face.box(x,z,width,.072,dep,.07,BRICK,'projecting impost moulding')
        for i in range(7):
            t=i/7
            face.box(x,SPRING-.49-.15*i,.31-.12*t,.141,.123,.046,BRICK,'pendant jamb brick')
        for dx in (-.043,.043):
            face.box(x+dx,SPRING-1.59,.051,.19,.12,.045,BRICK,'paired jamb drops')


def red_passage(face,lod):
    n=20 if lod else 52; length=3.35
    ring=sector(AXIS,SPRING,CLEAR,CLEAR+.14,0,pi,n)
    face.prism(ring,-length,-.024,WOOD,'red barrel vault lining')
    for side in (-1,1):
        face.prism(box(AXIS+side*CLEAR-.030,SILL_Z,AXIS+side*CLEAR+.030,SPRING),
                   -length,-.021,WOOD,'red internal stairwell jamb')
    # Rosy ribs follow the barrel of the long opening; they can be seen from street height.
    for i in range(5):
        depth=.15+i*.54
        face.prism(sector(AXIS,SPRING,CLEAR-.046,CLEAR+.027,0,pi,n),
                   -depth-.065,-depth,MORTAR if i==0 else SASH,'entrance ceiling ribs')
        for sign in (-1,1):
            x=AXIS+sign*(CLEAR-.018)
            face.prism(box(x-.028,SILL_Z,x+.028,SPRING),-depth-.065,-depth,WOOD,'red rib upright')
    for i in range(10):
        z=SILL_Z+(3.01-SILL_Z)*(i+1)/10
        d=-.13-i*.258
        face.box(AXIS,(z+SILL_Z-.15)/2,1.222,z-SILL_Z+.15,.265,d,SILL,'straight stone stair behind the arch')
        if not lod:face.box(AXIS,z-.016,1.22,.031,.044,d+.121,STONE,'straight stair nosing')
    face.box(AXIS,2.94,1.24,.14,.82,-2.99,SILL,'upper bookshop landing')
    sh=opening(AXIS,3.01,1.226,SPRING+CLEAR-3.01,arch=CLEAR,segments=n)
    face.prism(sh,-3.38,-3.34,DARK,'far face of entrance hall')
    door=box(AXIS-.42,3.03,AXIS+.42,5.26)
    face.prism(door,-3.34,-3.305,SASH,'far door leaves')
    face.prism(door.buffer(-.071,join_style=2),-3.303,-3.296,'Grey green glazing','far door glass')


def turning_stair(builder,lod):
    # The stair starts at the north side of the projection. It turns clockwise
    # to the west-facing upper tangent and meets the red door exactly at +1.41 m.
    x=HALF_WALL;y=5.18;rad=1.79
    def xy(r,a):return (x+r*cos(a),y+r*sin(a))
    def extrude(poly,bottom,top,mat,label):
        builder.prism(poly,bottom,top,lambda x,y,z:(x,y,z),mat,label)
    # The stair is solid at its centre, as drawn. Its outside stringer follows
    # a single smooth curve even though the walking surface rises in steps.
    count=7
    for i in range(count):
        a=-i*pi/(2*count);b=-(i+1)*pi/(2*count)
        tread=Polygon([(x,y),*[xy(rad,a+(b-a)*j/5)for j in range(6)]])
        z=.31+(SILL_Z-.31)*(i+1)/count
        extrude(tread,-.015,z,SILL,'fan-shaped entrance stair treads')
    builder.box((x+.90,y+.69,.034),(1.93,.465,.068),STONE,label='broad approach sill facing Fuxing Road')
    for j in range(2):
        z=.155*(j+1)
        builder.box((x+.90,y+.36-.24*j,z/2),(1.81,.245,z),SILL,label='two straight approach steps')
    for i in range(32 if not lod else 15):
        n=32 if not lod else 15
        t0=i/n;t1=(i+1)/n
        r0=rad;r1=rad+.24
        for lo,hi,mat,label in ((0,.89,ROUGH,'curved outer stair cheek'),(.89,.98,STONE,'curved pale coping')):
            a=-t0*pi/2;b=-t1*pi/2
            za=.31+(SILL_Z-.31)*t0;zb=.31+(SILL_Z-.31)*t1
            verts=[(*xy(r,angle), (0 if lo==0 else z+lo))for angle,z,r in ((a,za,r0),(a,za,r1),(b,zb,r1),(b,zb,r0))]
            verts.extend([(*xy(r,angle),z+hi)for angle,z,r in ((a,za,r0),(a,za,r1),(b,zb,r1),(b,zb,r0))])
            builder.add(verts,[(0,1,2,3),(7,6,5,4),(0,4,5,1),(3,2,6,7),
                               (0,3,7,4),(1,5,6,2)],mat,label)


def signs(face,lod):
    # The upper sign is a separate dark-red device above two compact lines of lettering.
    # Its stroke layout is reconstructed from the 2023 street photograph.
    glyph_paths=[
        [(-.29,.30),(-.14,.40),(-.12,.27),(-.27,.14),(-.13,.14),(-.16,.02)],
        [(-.08,.25),(.31,.29),(.37,.37)], [(-.05,.17),(.25,.19)],
        [(-.08,.10),(.23,.11),(.14,.02),(-.05,-.07),(-.15,-.19),(-.02,-.23),(.09,-.17),(.04,-.08)]]
    for path in glyph_paths:
        pts=[face.point(AXIS+u,8.40+z,.105)for u,z in path]
        face.builder.tube(pts,.039,WOOD,6 if lod else 10,'raised entrance emblem')
    for z,word in ((8.035,'SINAN'),(7.84,'BOOKS')):
        add_facade_lettering(face,word,AXIS,z,.87,.138,.068,.126,WOOD,label='raised metal '+word,font=FONT)
    # The vertical four-character plaque is mounted on the inner south reveal,
    # angled out slightly. Letter plane is directed east-northeast toward the stair.
    from photo_architecture import Facade
    u=AXIS-CLEAR+.029
    f=Facade(face.builder,(HALF_WALL-.095,u-.049),(HALF_WALL-.69,u+.049),'inside entrance sign')
    f.box(0,3.60,.237,.98,.036,0,SASH,'vertical inscription backing')
    for i,char in enumerate('思南书局'):
        add_facade_lettering(f,char,0,3.95-i*.234,.17,.182,.019,.028,STONE,label='vertical bookshop name',font=FONT)


def east_entrance(face,lod):
    brick_surround(face,lod)
    red_passage(face,lod)
    turning_stair(face.builder,lod)
    signs(face,lod)
