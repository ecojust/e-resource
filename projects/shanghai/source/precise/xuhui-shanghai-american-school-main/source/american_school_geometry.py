"""Public exterior of the 1922 classroom range at 10 Hengshan Road."""
from math import cos, pi, sin
from shapely.geometry import Polygon, box
from photo_architecture import Facade, opening

BRICK = 'weathered red facing brick'
STONE = 'warm light limestone'
WHITE = 'painted ivory sash and tower'
GLASS = 'cool recessed glazing'
DOOR = 'dark timber door'
TILE = 'aged reddish roof tiles'
LEAD = 'dark metal flashing'
FINIAL = 'aged copper finial'
PALETTE = {
    BRICK: {'color': [.46, .236, .186], 'roughness': .90},
    STONE: {'color': [.71, .675, .60], 'roughness': .82},
    WHITE: {'color': [.80, .80, .755], 'roughness': .68},
    GLASS: {'color': [.184, .248, .265], 'metallic': .21, 'roughness': .32},
    DOOR: {'color': [.204, .129, .077], 'roughness': .58},
    TILE: {'color': [.405, .218, .177], 'roughness': .88},
    LEAD: {'color': [.231, .239, .227], 'metallic': .40, 'roughness': .56},
    FINIAL: {'color': [.289, .306, .267], 'metallic': .65, 'roughness': .46},
}

# +X follows the long teaching wing north-east. +Y faces its courtyard.
HALF_LENGTH = 37.25
BACK = 9.10
RIDGE_Y = .10
CENTRE = 12.65
CENTRAL_EAVE = 10.54
WING_EAVE = 9.77


def opening_glass(face, hole, columns, rows, lod):
    face.window(hole, columns=max(1, columns-1) if lod else columns,
                rows=max(1, rows-1) if lod else rows, frame=WHITE,
                trim=False, glass=GLASS, label='recessed timber sash')


def entrance(face):
    hole = box(-1.15, .32, 1.15, 3.55)
    face.prism(hole, -.39, -.32, DOOR, 'inset paired entrance doors')
    for x in (-.54, .54):
        for low, high in ((.53, 1.49), (1.68, 3.28)):
            panel = box(x-.375,low,x+.375,high)
            face.prism(panel.boundary.buffer(.043, join_style=2), -.32, -.25,
                       STONE if high > 2 else DOOR, 'entrance leaf panel')
    face.prism(hole.buffer(.22, join_style=2).difference(hole), -.11, .13, STONE,
               'cut stone door surround')
    for x in (-1.47, 1.47):
        face.box(x,2.06,.31,3.48,.33,.16,STONE,'portal pilaster')
    face.box(0,3.89,3.55,.35,.54,.18,STONE,'portal lintel')
    # The dated front photograph shows a low curved pediment with two scrolls
    # framing its central crest over the rectangular doorway.
    outline=[(-1.72,4.02),(-1.58,4.10),(-1.19,4.43),(-.76,4.64),
             (-.48,4.51),(0,4.73),(.48,4.51),(.76,4.64),
             (1.19,4.43),(1.58,4.10),(1.72,4.02)]
    face.prism(Polygon(outline),-.01,.21,STONE,'carved entrance pediment')
    for hand in (-1,1):
        pts=[]
        for j in range(13):
            theta=j*1.44*pi/12
            r=.23*(1-j/19)
            pts.append((hand*(.82+r*cos(theta)),4.40+r*sin(theta)))
        face.builder.tube([face.point(x,z,.24)for x,z in pts],.044,WHITE,6,
                          face.label+'/pediment scroll')
    crest=Polygon([(-.20,4.42),(-.17,4.65),(0,4.76),(.17,4.65),(.20,4.42),(0,4.25)])
    face.prism(crest,.17,.26,STONE,'stone crest')


def front_bay(builder, xmin, xmax, y, eave, central, lod):
    face=Facade(builder,(xmin,y),(xmax,y),'central entrance' if central else 'classroom wing')
    # Upper rows read as strongly vertical openings. The door sits centrally
    # beneath the wider English sash, with three classroom openings on each side.
    bays=[-10.25,-7.03,-4.10,0,4.10,7.03,10.25] if central else [-9.39,-6.30,-3.16,0,3.16,6.30,9.39]
    openings=[]
    for z,h in ((.84,3.05),(5.44,3.64)):
        for x in bays:
            if central and x==0 and z<2:continue
            w=3.15 if central and x==0 else (2.11 if central else 1.66)
            o=box(x-w/2,z,x+w/2,z+h)
            openings.append(o)
            opening_glass(face,o,3 if w>2.2 else 2,4,lod)
            face.prism(box(x-.13,z+h-.012,x+.13,z+h+.22),0,.10,STONE,'window keystone')
    if central:
        holes=[*openings,box(-1.15,.32,1.15,3.55)]
        entrance(face)
        for x in (-12.16,-5.60,5.60,12.16):
            face.box(x,5.28,.57,9.77,.28,.13,BRICK,'brick pilaster')
            face.box(x,.46,.67,.46,.37,.15,STONE,'pilaster plinth')
            face.box(x,10.10,.70,.25,.39,.15,STONE,'pilaster cap')
    else:
        holes=openings
    face.wall(0,eave,holes,material=BRICK)
    for z,h,d,mat in ((.24,.35,.35,STONE),(4.76,.13,.26,STONE),
                       (eave-.26,.18,.31,STONE),(eave-.04,.20,.57,WHITE)):
        face.beam(z,h,d,mat)
    return face


def front_gable(builder,x,y,z,width,height,depth,lod,name,arched=False):
    # A complete dormer face and side cheeks rise through the pitched roof.
    f=Facade(builder,(x-width/2,y),(x+width/2,y),name)
    half=width/2
    eave=z+height*.75
    apex=z+height
    poly=Polygon([(-half,z),(half,z),(half,eave),(0,apex),(-half,eave)])
    hole=opening(0,z+.09,width*(.66 if arched else .62),height*(.81 if arched else .70),
                 width*.285 if arched else 0,9 if lod else 17)
    f.prism(poly.difference(hole),-.25,0,WHITE,'dormer face')
    f.window(hole,columns=1 if lod else 2,rows=2 if lod else 3,
             frame=WHITE,trim=False,glass=GLASS,label='attic sash')
    f.prism(poly.boundary.buffer(.045,join_style=2),0,.11,WHITE,'pediment molding')
    cross=[(-half,eave),(0,apex),(half,eave)]
    if arched:
        # The high-resolution 2017 view distinguishes the gabled hood from
        # the curved fanlight below it. The small raised apex is separate.
        f.prism(hole.buffer(.055,join_style=2).difference(hole),-.015,.055,WHITE,'fanlight rim')
        crest=Polygon([(-.13,apex-.03),(-.105,apex+.047),(0,apex+.09),
                       (.105,apex+.047),(.13,apex-.03)])
        f.prism(crest,-.09,.08,WHITE,'dormer apex finial')
    for (a,za),(c,zc) in zip(cross,cross[1:]):
        builder.add([(x+a,y,za),(x+c,y,zc),(x+c,y+depth,zc),(x+a,y+depth,za)],
                    [(0,1,2,3)],LEAD if arched else TILE,name+'/roof')
    for dx in (-half,half):
        builder.add([(x+dx,y,z),(x+dx,y+depth,z),(x+dx,y+depth,eave),(x+dx,y,eave)],
                    [(0,1,2,3) if dx>0 else (3,2,1,0)],WHITE,name+'/dormer cheek')


def pitched_roof(builder,x0,x1,front,back,eave,ridge,label):
    verts=[(x0,front,eave),(x1,front,eave),(x1,RIDGE_Y,ridge),(x0,RIDGE_Y,ridge),
           (x0,back,eave),(x1,back,eave)]
    builder.add(verts,[(0,1,2,3),(3,2,5,4)],TILE,label+'/pitched tile roof')
    builder.add(verts,[(0,3,4),(1,5,2)],BRICK,label+'/gable end')
    builder.tube([(x0,RIDGE_Y,ridge),(x1,RIDGE_Y,ridge)],.10,TILE,8,label+'/ridge')


def bell_tower(builder,lod):
    # Independent masonry tower, curved upper openings and separate cap make
    # the tower read from above as well as from the front gate.
    cx,cy=0,-.05
    # Continue the square base below both slopes of the main pitched roof.
    builder.box((cx,cy,14.28),(3.20,3.20,1.65),WHITE,label='bell-tower base through roof')
    for z,w,th,mat,lab in [(14.98,3.53,.25,STONE,'base molding'),
                            (16.26,3.28,2.56,WHITE,'square tower base'),
                            (17.58,3.55,.22,LEAD,'dark tower cornice')]:
        builder.box((cx,cy,z),(w,w,th),mat,label=lab)
    pts=[(cx+1.35*cos(pi/8+j*pi/4),cy+1.35*sin(pi/8+j*pi/4)) for j in range(8)]
    for a,b in zip(pts,pts[1:]+pts[:1]):
        f=Facade(builder,a,b,'octagonal belfry')
        hole=opening(0,17.86,.59,1.59,.23,8 if lod else 16)
        f.wall(17.68,19.91,[hole],thickness=.20,material=WHITE)
        f.window(hole,columns=1 if lod else 2,rows=3 if lod else 4,frame=WHITE,
                 trim=False,glass=GLASS,label='arched belfry sash')
        f.prism(hole.buffer(.07,join_style=2).difference(hole),-.02,.08,STONE,'belfry arch surround')
    for x in [-1.43,1.43]:
        for y in [-1.43,1.43]:
            builder.lathe((cx+x,cy+y),[(17.66,.14),(17.80,.10),(17.95,.24),
                        (18.18,.25),(18.31,.13),(18.37,.085),(18.46,.03)],
                        STONE,8 if lod else 12,'urn at belfry-base corner')
    builder.lathe((cx,cy),[(19.88,1.34),(20.04,1.44),(20.15,1.42),(20.19,1.53),
                               (20.41,1.05),(21.18,.53),(21.61,.20)],TILE,8,'pointed tiled cupola')
    builder.lathe((cx,cy),[(21.61,.20),(21.74,.10),(22.46,.024)],FINIAL,8,'copper finial')
    builder.tube([(-.44,cy,22.12),(.44,cy,22.12)],.028,FINIAL,5,'weather vane')
    builder.add([(-.47,cy,22.12),(-.24,cy,22.24),(-.24,cy,22.03)],[(0,1,2)],FINIAL,'vane pointer')


def add_building(b,lod):
    ends=[(-HALF_LENGTH,-CENTRE,-8.25,WING_EAVE,13.79),
          (-CENTRE,CENTRE,-8.92,CENTRAL_EAVE,14.94),
          (CENTRE,HALF_LENGTH,-8.25,WING_EAVE,13.79)]
    for i,(west,east,front,eave,ridge) in enumerate(ends):
        front_bay(b,west,east,front,eave,i==1,lod)
        pitched_roof(b,west,east,front-.27,BACK+.22,eave,ridge,'roof bay '+str(i+1))
        back=Facade(b,(east,BACK),(west,BACK),'courtyard face')
        holes=[]
        for z in (.94,5.43):
            for u in (-9.35,-6.23,-3.12,0,3.12,6.23,9.35):
                h=box(u-.74,z,u+.74,z+2.72)
                holes.append(h);opening_glass(back,h,2,3,lod)
        back.wall(0,eave,holes,material=BRICK);back.beam(eave-.07,.21,.44,WHITE)
    for x,sgn in [(-HALF_LENGTH,-1),(HALF_LENGTH,1)]:
        face=(Facade(b,(x,BACK),(x,-8.25),'southwest gable') if sgn<0
              else Facade(b,(x,-8.25),(x,BACK),'northeast gable'))
        holes=[]
        for z in (.93,5.45):
            for u in (-4.70,-2.36,0,2.36,4.70):
                h=box(u-.60,z,u+.60,z+2.62);holes.append(h);opening_glass(face,h,2,3,lod)
        face.wall(0,WING_EAVE,holes,material=BRICK)
        face.beam(WING_EAVE-.04,.22,.44,WHITE)
    for x in (-CENTRE,CENTRE):
        b.box((x,-8.58,CENTRAL_EAVE/2),(.34,.67,CENTRAL_EAVE),BRICK,label='central projection return')
    b.plan_prism(box(-HALF_LENGTH,-8.92,HALF_LENGTH,BACK),.03,.22,STONE,'ground floor')
    for x in (-9.80,-4.92,0,4.92,9.80):
        front_gable(b,x,-8.42,10.49,2.13,2.04,3.23,lod,'central arched dormer',True)
    for hand in (-1,1):
        for u in (15.65,21.08,32.72):
            front_gable(b,hand*u,-7.61,9.96,1.79,1.77,2.80,lod,'wing dormer')
        front_gable(b,hand*26.78,-7.75,9.96,3.52,1.96,3.07,lod,'wide wing pediment dormer')
        for u in (8.93,21.47):
            x=hand*u
            b.box((x,1.04,14.40),(.62,.78,2.75),BRICK,label='brick roof chimney')
            b.box((x,1.04,15.81),(.71,.85,.15),STONE,label='chimney cap')
    bell_tower(b,lod)
    # A smaller open-sided hood with a pyramidal top is distinct from the
    # bell tower in the 2017 photograph. Its original function is unknown.
    cx,cy=4.65,1.87
    for dx in [-.90,.90]:
        for dy in [-.84,.84]:
            b.box((cx+dx,cy+dy,15.26),(.20,.21,2.47),WHITE,label='ridge hood pier')
    b.box((cx,cy,16.39),(2.04,1.94,.25),WHITE,label='ridge hood lintel')
    corners=[(cx-1.10,cy-1.03,16.50),(cx+1.10,cy-1.03,16.50),
             (cx+1.10,cy+1.03,16.50),(cx-1.10,cy+1.03,16.50),(cx,cy,17.74)]
    b.add(corners,[(0,1,4),(1,2,4),(2,3,4),(3,0,4)],STONE,'ridge hood pyramidal cap')

