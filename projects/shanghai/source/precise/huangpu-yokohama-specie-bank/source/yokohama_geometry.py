"""Current river front of 24 Zhongshan East 1st Road, with its L-shaped rear wing."""
from math import cos, pi, sin
from pathlib import Path
from shapely import affinity
from shapely.geometry import Point, Polygon, box
from shapely.geometry.polygon import orient
from photo_architecture import Facade, opening
from sign_lettering import add_facade_lettering

GRANITE='light grey ashlar'; STONE='pale carved granite'; COLUMN='warm granite shafts'
IRON='blackened metalwork'; GLASS='inset cool grey glass'; BRONZE='patinated bronze'
PANEL='dark bronze spandrels'; BACK='weathered masonry'; ROOF='flat grey roof'
RED='vermilion enamel'
PALETTE={
 GRANITE:{'color':[.59,.556,.496],'roughness':.85}, STONE:{'color':[.68,.643,.574],'roughness':.79},
 COLUMN:{'color':[.615,.579,.519],'roughness':.76}, IRON:{'color':[.109,.102,.091],'metallic':.45},
 GLASS:{'color':[.145,.203,.223],'metallic':.23,'roughness':.3},
 BRONZE:{'color':[.235,.178,.103],'metallic':.57,'roughness':.47},
 PANEL:{'color':[.168,.151,.126],'metallic':.33}, BACK:{'color':[.539,.517,.465],'roughness':.91},
 ROOF:{'color':[.352,.356,.349],'roughness':.92}, RED:{'color':[.67,.051,.040],'roughness':.5},
}
# World heading 8.5824 degrees. The main frontage is on the east, the rear wing
# widens northward behind the separate Yangtze Insurance Building.
SOUTHWEST=(-31.45,-18.97); SOUTH_EAST=(39.07,-18.54); NORTH_EAST=(39.07,7.73)
INNER=(7.22,7.56); REAR_NE=(7.20,24.51); REAR_NW=(-31.43,24.25)
RING=[SOUTHWEST,SOUTH_EAST,NORTH_EAST,INNER,REAR_NE,REAR_NW]
PLAN=orient(Polygon(RING),1)
MAIN_CORNICE=29.95; REAR_TOP=28.12
FONT=Path(__file__).with_name('fonts')/'RiversideBankSign.otf'


def band(f,z,height,depth,material=STONE,back=-.20,label='stone course'):
    f.box(0,z,f.length+.012,height,depth-back,(depth+back)/2,material,label)


def glazing(f,hole,lod,rows=2):
    f.window(hole,columns=2,rows=rows,frame=IRON,trim=False,glass=GLASS,label='recessed sash')
    l,z,r,_=hole.bounds
    f.box((l+r)/2,z-.065,r-l+.19,.11,.20,.03,STONE,'stone window sill')


def circle(u,z,r,lod):
    return Point(u,z).buffer(r,quad_segs=6 if lod else 12)


def ionic(f,u,lod):
    b=f.builder;xy=f.point(u,0,.19)
    # Two full-round shafts rise from the level immediately above the entrances.
    b.lathe(xy[:2],[(9.84,1.00),(9.99,1.07),(10.14,1.03),(10.27,.91),
                    (10.50,.87),(16.5,.805),(23.95,.71),(24.41,.74),
                    (24.54,.82),(24.75,.87),(24.89,.99)],COLUMN,
            segments=16 if lod else 36,label=f.label+'/Ionic shaft and base')
    for side in [-1,1]:
        points=[]
        for i in range(13 if lod else 30):
            count=13 if lod else 30;a=i/(count-1)*pi*2.32
            r=.35*(1-i/(count-1)*.84)
            points.append(f.point(u+side*(.71+cos(a)*r),24.87+sin(a)*r,.94))
        b.tube(points,.073,STONE,sides=5 if lod else 8,label=f.label+'/Ionic volutes')
    f.box(u,25.27,2.56,.27,1.77,.10,STONE,'capital abacus')


def balcony(f,u,lod):
    f.box(u,9.38,3.58,.32,1.04,.31,STONE,'cantilever balcony floor')
    for side in [-1,1]:
        x=u+side*1.15
        bracket=Polygon([(x-.26,9.27),(x+.26,9.27),(x+.19,8.75),(x+.10,8.37),(x-.10,8.37),(x-.19,8.75)])
        f.prism(bracket,.055,.63,STONE,'stepped balcony corbel')
        f.box(u+side*1.60,10.05,.062,1.12,.81,.40,IRON,'railing return')
    f.box(u,10.48,3.34,.073,.09,.86,IRON,'balcony handrail')
    count=12 if lod else 22
    for i in range(count):
        x=u+(i/(count-1)-.5)*3.19
        f.box(x,9.98,.050,.96,.06,.855,IRON,'balcony baluster')
    f.box(u,14.61,3.45,.20,.62,.10,STONE,'hood above tall balcony sash')


def doors(f,u,lod):
    # Bronze entrance leaves stand inside each opening. Medallions and grilles
    # are separate geometry, as visible in 2014 and 2025 frontal photographs.
    door=opening(u,.13,2.80,6.85)
    f.prism(door.buffer(.004),-.64,-.54,PANEL,'bronze entrance backing')
    for side in [-1,1]:
        x=u+side*.68
        f.box(x,3.03,1.30,5.42,.105,-.458,BRONZE,'bronze entrance leaf')
        medallion=circle(x,3.48,.485,lod).difference(circle(x,3.48,.37,lod))
        f.prism(medallion,-.398,-.315,IRON,'paired bronze medallions')
        f.box(x,5.63,1.01,.84,.09,-.405,PANEL,'upper door grille')
        for i in range(3 if lod else 5):
            f.box(x+(i/(2 if lod else 4)-.5)*.77,5.64,.035,.59,.037,-.348,BRONZE,'door grille upright')
    f.box(u,6.52,2.66,.44,.11,-.45,BRONZE,'bronze transom')
    for x in [u-1.50,u+1.50]:f.box(x,3.60,.21,7.11,.31,.02,STONE,'stepped square jamb')
    return door


def granite_joints(f,surface,lod):
    from shapely.geometry import box as rect
    z=1.03
    while z<9.10:
        strip=surface.intersection(rect(-f.length/2,z,f.length/2,z+.025))
        f.prism(strip,.002,.015,BACK,'ground ashlar bed joints')
        z+=.87 if lod else .71


def current_sign(f,lod):
    add_facade_lettering(f,'ICBC',-6.18,27.00,3.50,1.01,.025,.120,IRON,font=FONT,label='current ICBC sign')
    add_facade_lettering(f,'中国工商银行',3.17,27.00,8.78,1.10,.025,.120,IRON,font=FONT,label='current bank name')
    u=-2.92;z=27.00
    f.prism(circle(u,z,.82,lod).difference(circle(u,z,.65,lod)),.022,.132,RED,'enamel bank roundel')
    emblem=box(u-.44,z+.22,u+.44,z+.33).union(box(u-.44,z-.33,u+.44,z-.22)).union(box(u-.065,z-.26,u+.065,z+.26))
    f.prism(emblem,.028,.134,RED,'enamel bank monogram')


def river_front(b,lod):
    f=Facade(b,SOUTH_EAST,NORTH_EAST,'river elevation')
    doors_and_windows=[]
    center_bays=[-4.68,0,4.68]
    outer=[-9.64,9.64]
    doors_and_windows.extend(doors(f,u,lod) for u in center_bays)
    for u in outer:
        g=opening(u,1.85,1.60,3.28);doors_and_windows.append(g);glazing(f,g,lod)
    low=f.wall(0,9.60,doors_and_windows,.48,GRANITE)
    granite_joints(f,low,lod);band(f,8.11,.16,.23);band(f,9.53,.21,.33)
    holes=[]
    for u in center_bays:
        for z in [9.94,14.02,18.23,22.49]:
            h=opening(u,z,1.88,2.17);holes.append(h);glazing(f,h,lod,2)
        for z in [13.08,17.26,21.46]:
            f.box(u,z,1.88,1.42,.17,-.03,PANEL,'dark fixed spandrel')
            ring=circle(u,z,.35,lod).difference(circle(u,z,.28,lod))
            f.prism(ring,.047,.088,BRONZE,'round spandrel boss')
    for u in outer:
        for z,h in [(9.85,3.78),(15.18,2.26),(19.31,2.16),(23.55,1.50)]:
            win=opening(u,z,1.72,h);holes.append(win);glazing(f,win,lod)
        balcony(f,u,lod)
    f.wall(9.60,25.80,holes,.43,GRANITE)
    for u in [-2.34,2.34]:ionic(f,u,lod)
    for hand in [-1,1]:
        f.box(hand*6.51,17.54,1.48,15.79,.45,.08,COLUMN,'flat outer pilaster')
        f.box(hand*6.51,25.38,2.06,.35,.66,.08,STONE,'pilaster capital')
    f.wall(25.80,MAIN_CORNICE,(),.42,GRANITE)
    for z,h,d in [(25.8,.21,.31),(26.04,.19,.36),(28.35,.27,.52),(28.75,.24,.67),(29.34,.61,.88),(29.83,.21,1.00)]:
        band(f,z,h,d)
    n=30 if lod else 52
    for i in range(n):
        f.box(((i+.5)/n-.5)*(f.length-.15),28.89,.21,.37,.66,.20,STONE,'projecting cornice dentil')
    current_sign(f,lod)


def attic(b,lod):
    # Roof photos show a rectangular eastern block, open space behind the front
    # cornice, and building plant farther west. These setbacks are approximate.
    x=37.55;lo=-17.81;hi=7.01;back=22.45;plan=box(back,lo,x,hi)
    f=Facade(b,(x,lo),(x,hi),'set-back sixth storey')
    holes=[]
    for u,w in [(-9.95,1.48),(-5.05,3.53),(0,3.53),(5.05,3.53),(9.95,1.48)]:
        h=opening(u,30.37,w,1.58);holes.append(h);glazing(f,h,lod,1)
    f.wall(MAIN_CORNICE,33.72,holes,.40,GRANITE)
    band(f,33.38,.25,.40);band(f,33.76,.21,.53)
    for a,end in [((x,hi),(back,hi)),((back,hi),(back,lo)),((back,lo),(x,lo))]:
        wall=Facade(b,a,end,'attic returns')
        wall.wall(MAIN_CORNICE,33.74,(),.31,BACK)
    b.plan_prism(plan,33.62,33.82,ROOF,'roof of recessed attic')
    crest=Polygon([(-4.15,33.76),(-3.85,34.12),(-2.84,34.12),(-2.60,34.65),(-1.76,34.65),(-1.53,35.15),(-.76,35.15),(-.50,35.55),(.50,35.55),(.76,35.15),(1.53,35.15),(1.76,34.65),(2.60,34.65),(2.84,34.12),(3.85,34.12),(4.15,33.76)])
    f.prism(crest,-.33,.09,STONE,'stepped central roof crest')
    for side in [-1,1]:
        for i in range(6):
            u=side*(4.6+i*1.34)
            acro=Polygon([(u-.41,33.77),(u-.32,34.08),(u-.17,34.14),(u,34.54),(u+.17,34.14),(u+.32,34.08),(u+.41,33.77)])
            f.prism(acro,-.28,.035,STONE,'roof-edge palmette')


def returns(b,lod):
    for a,end,label in [(NORTH_EAST,INNER,'north party wall'),(INNER,REAR_NE,'rear east return'),(REAR_NE,REAR_NW,'north rear'),(REAR_NW,SOUTHWEST,'west rear'),(SOUTHWEST,SOUTH_EAST,'south return')]:
        f=Facade(b,a,end,label);holes=[]
        # The southern separation from the Bank of China and the west back
        # wall give light to service rooms. The party side has no invented sash.
        if label in ('south return','west rear'):
            count=max(2,int(f.length/4.65))
            for i in range(count):
                u=(i+.5)*f.length/count-f.length/2
                for z in [5.22,10.12,14.30,18.49,22.69]:
                    hole=opening(u,z,1.26,1.84);holes.append(hole);glazing(f,hole,lod,1)
        f.wall(0,REAR_TOP,holes,.30,BACK)
    b.plan_prism(PLAN,0,.13,BACK,'ground')
    b.plan_prism(PLAN,REAR_TOP-.19,REAR_TOP,ROOF,'L-shaped roof')
    front=orient(PLAN.intersection(box(20,-30,45,26)),1)
    for a,end in zip(list(front.exterior.coords)[:-1],list(front.exterior.coords)[1:]):
        if max(abs(a[0]-39.07),abs(end[0]-39.07))<.02:continue
        f=Facade(b,a,end,'raised front block');f.wall(REAR_TOP,MAIN_CORNICE,(),.25,BACK)
    b.plan_prism(front,MAIN_CORNICE-.13,MAIN_CORNICE,ROOF,'front block roof')
    # A broad paved roof and a raised rear rooflight remain visible in all three releases.
    for x,y,w,h in [(-15.8,10.6,6.5,7.3),(-13.4,-2.1,9.1,7.8),(-21.8,16.9,3.3,4.1)]:
        b.plan_prism(box(x-w/2,y-h/2,x+w/2,y+h/2),REAR_TOP,REAR_TOP+.65,ROOF,'low rear rooflight curb')
        b.plan_prism(box(x-w/2+.14,y-h/2+.14,x+w/2-.14,y+h/2-.14),REAR_TOP+.65,REAR_TOP+.74,GLASS,'rooflight')


def add_building(builder,lod):
    river_front(builder,lod);returns(builder,lod);attic(builder,lod)
