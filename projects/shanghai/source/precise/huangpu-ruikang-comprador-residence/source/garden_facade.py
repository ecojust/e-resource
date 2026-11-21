"""Surviving photographic evidence for the lost Bei Runsheng house, Huangpi Road.

Local X runs across the documented garden elevation, positive Y away from its
court. The short returns and recessed arcade interiors are cut off at the
documented facade segment. Dimensions are estimates from the street block and
straightened elevations. The court and rear house are outside this model.
"""
import math
from shapely.geometry import Polygon, box
from shapely.ops import unary_union
from photo_architecture import Facade, opening

BRICK = 'Russet field brick'
ARCH = 'Red arch moulding'
CUT = 'Dark brick bedding'
TERRACOTTA = 'Warm terracotta trim'
STONE = 'Warm ivory limestone'
BASE = 'Grey plinth stone'
FRAME = 'Brown timber joinery'
GLASS = 'Garden glass'
SOFFIT = 'Sheltered plaster'
INSIDE = 'Deep recess'
IRON = 'Roof finial iron'
MAT = {
    BRICK: {'color': [.58, .30, .222], 'roughness': .84},
    ARCH: {'color': [.747, .435, .337], 'roughness': .80},
    CUT: {'color': [.352, .218, .182], 'roughness': .89},
    TERRACOTTA: {'color': [.679, .402, .313], 'roughness': .81},
    STONE: {'color': [.785, .722, .593], 'roughness': .74},
    BASE: {'color': [.585, .552, .482], 'roughness': .84},
    FRAME: {'color': [.285, .226, .167], 'roughness': .67},
    GLASS: {'color': [.269, .341, .335], 'roughness': .33, 'metallic': .14},
    SOFFIT: {'color': [.524, .435, .358], 'roughness': .86},
    INSIDE: {'color': [.194, .179, .157], 'roughness': .88},
    IRON: {'color': [.219, .247, .23], 'roughness': .66, 'metallic': .32}
}

# Five adjoining bays in the front photograph. Recesses behind the two wings
# interrupt the three projecting blocks, as on the unscaled old street plan.
SPANS = [(-15.05,-9.89,'end'), (-9.89,-3.66,'wing'), (-3.66,3.66,'central'),
         (3.66,9.89,'wing'), (9.89,15.05,'end')]
FACES_Y = {'end': 0.0, 'wing': .52, 'central': -.23}
FLOOR = 4.84
MIDDLE_CROWN = 9.65
FINIAL = 16.59


def ellipse_ring(cx, spring, radius, rise, t0, t1, thickness, steps):
    angles = [t0+(t1-t0)*i/steps for i in range(steps+1)]
    outer = [(cx+(radius+thickness)*math.cos(t), spring+(rise+thickness)*math.sin(t))
             for t in angles]
    inner = [(cx+radius*math.cos(t), spring+rise*math.sin(t)) for t in reversed(angles)]
    return Polygon(outer+inner)


def arch_head(face, x, spring, radius, rise, distant, label, thickness=.17):
    pieces = 12 if distant else 23
    ring = ellipse_ring(x,spring,radius,rise,0,math.pi,thickness,pieces*2)
    face.prism(ring,-.021,.044,CUT,label+' mortar bed')
    for i in range(pieces):
        a,b = i*math.pi/pieces,(i+1)*math.pi/pieces
        brick = ellipse_ring(x,spring,radius,rise,a+.0027,b-.0027,thickness,2)
        face.prism(brick,-.014,.076,ARCH if i%4 else TERRACOTTA,label+' arch blocks')
    lip=ellipse_ring(x,spring,radius+thickness-.014,rise+thickness-.014,
                     0,math.pi,.043,pieces*2)
    face.prism(lip,.040,.111,TERRACOTTA,label+' outer moulding')


def courses(face,z,w,distant,label,colour=STONE):
    bands=[(-.055,.100,.10),(0.035,.078,.17)]
    if not distant:bands.append((.095,.045,.213))
    for dz,h,d in bands:
        face.box(0,z+dz,w,h,d+.13,(d-.13)*.5,colour,label)


def column(face,u,z0,spring,label,distant,radius=.225):
    p=face.point(u,0,.018)
    shaft=spring-z0
    profile=[(z0,.97),(z0+.07,1.29),(z0+.18,1.29),(z0+.23,1.08),
             (z0+.29,.92),(z0+.32,.82),(z0+shaft*.54,.78),
             (spring-.30,.73),(spring-.25,.82),(spring-.21,.93),
             (spring-.15,1.01),(spring-.10,1.20),(spring-.045,1.20)]
    face.builder.lathe(p[:2],[(z,rad*radius)for z,rad in profile],STONE,
                       10 if distant else 16,label+' turned limestone shaft')
    face.box(u,spring-.029,2.60*radius,.08,.55,.015,STONE,label+' slab capital')


def balusters(face,x0,x1,z0,distant,label):
    span=x1-x0
    face.box((x0+x1)/2,z0+.060,span,.12,.29,.038,STONE,label+' sill')
    face.box((x0+x1)/2,z0+.743,span+.06,.11,.325,.045,STONE,label+' rail')
    count=max(2,round((span-.28)/.38))
    for i in range(count):
        u=x0+.18+(i+.50)*(span-.36)/count
        x,y,_=face.point(u,z0,.035)
        prof=[(.11,.062),(.16,.081),(.225,.061),(.33,.043),(.48,.069),
              (.55,.085),(.59,.079),(.63,.051),(.692,.068)]
        face.builder.lathe((x,y),[(z0+z,r)for z,r in prof],STONE,
                           6 if distant else 10,label+' open stone balusters')
    for u in (x0+.09,x1-.09):
        face.box(u,z0+.40,.18,.65,.28,.035,TERRACOTTA,label+' end die')


def window(face,holes,x,sill,width,height,rise,distant,label,cols=3,rows=3,depth=.31):
    aperture=opening(x,sill,width,height,rise,16 if distant else 28)
    holes.append(aperture)
    frame=aperture.buffer(-.045,join_style=2)
    glazing=frame.buffer(-.072,join_style=2)
    bars=[]
    for k in range(1,cols):
        u=x-width/2+width*k/cols
        bars.append(box(u-.027,sill,u+.027,sill+height))
    for k in range(1,rows):
        z=sill+(height-rise)*k/rows
        bars.append(box(x-width/2,z-.029,x+width/2,z+.029))
    if rise>.20:
        z=sill+height-rise
        bars.append(box(x-width/2,z-.035,x+width/2,z+.035))
    face.prism(aperture.buffer(.014,join_style=2),-depth-.013,-depth+.003,GLASS,label+' panes')
    face.prism(frame.difference(glazing.difference(unary_union(bars))),
               -depth+.010,-depth+.106,FRAME,label+' timber frame')
    face.box(x,sill-.075,width+.22,.148,.48,-.025,BASE,label+' sill')
    if rise:arch_head(face,x,sill+height-rise,width/2,rise,distant,label+' arch',.105)


def recessed_gallery(face,holes,spans,z0,spring,distant,label,rail):
    # The arches and the column row stand in front of a separate wall plane.
    # Remove all masonry beneath their spring and let the capitals carry the arch.
    margin = .08
    left=spans[0][0]-spans[0][1]/2
    right=spans[-1][0]+spans[-1][1]/2
    openings=[opening(x,z0-.007,width,spring+rise-z0+.007,rise,16 if distant else 30)
              for x,width,rise in spans]
    holes.extend(openings)
    holes.append(box(left,z0-.007,right,spring-.035))
    face.prism(box(left-.024,z0-.025,right+.024,spring+max(s[2]for s in spans)+.03),
               -1.355,-1.337,INSIDE,label+' recessed field')
    face.box((left+right)/2,z0+.018,right-left,.050,1.355,-.66,BASE,label+' paved gallery')
    for x,width,rise in spans:
        arch_head(face,x,spring,width/2,rise,distant,label)
        if rail:balusters(face,x-width/2+margin,x+width/2-margin,z0,distant,label)
    for i in range(len(spans)-1):
        x1,w1,_=spans[i];x2,w2,_=spans[i+1]
        column(face,((x1+w1/2)+(x2-w2/2))/2,z0,spring,label,distant,.245)
    for x in (left-.075,right+.075):
        face.box(x,(spring+z0)/2,.21,spring-z0,.30,-.06,BRICK,label+' outside jamb')
        face.box(x,spring-.095,.38,.17,.48,.015,TERRACOTTA,label+' jamb impost')


def central(face,distant):
    holes=[]
    spans=[(-2.40,1.24,.65),(0,2.94,1.31),(2.40,1.24,.65)]
    recessed_gallery(face,holes,spans,.075,3.05,distant,'lower arcade',False)
    recessed_gallery(face,holes,spans,FLOOR+.07,7.85,distant,'upper arcade',True)
    window(face,holes,0,10.61,2.02,2.77,1.01,distant,'upper central',3,3,.43)
    # The central upper window has a large pale half-round hood with short
    # horizontal shoulders, clear against the red triangular gable.
    full_hood=ellipse_ring(0,12.37,1.125,1.125,0,math.pi,.135,28 if distant else 48)
    face.prism(full_hood,.062,.215,STONE,'half round hood of gable window')
    for side in (-1,1):
        face.box(side*1.39,12.376,.40,.12,.34,.076,STONE,'gable window hood shoulders')
        face.box(side*1.028,11.47,.105,1.72,.25,.045,TERRACOTTA,'gable window jamb')
    keystone=Polygon([(-.109,13.34),(.109,13.34),(.17,13.68),(-.17,13.68)])
    face.prism(keystone,.107,.246,TERRACOTTA,'gable centre keystone')
    for x in (-2.25,2.25):
        window(face,holes,x,10.66,.85,2.09,.44,distant,'side lancet',2,3)
    peak=[(-3.66,13.01),(-2.12,13.01),(-2.12,13.42),(0,14.97),
          (2.12,13.42),(2.12,13.01),(3.66,13.01)]
    body=Polygon([(-3.66,0),(3.66,0),*reversed(peak)])
    face.prism(body.difference(unary_union(holes)),-.48,0,BRICK,'central front wall')
    for side in (-1,1):
        x=side*2.79
        for z,h,w,d in [(13.02,.18,1.72,.23),(13.16,.11,1.81,.29)]:
            face.box(x,z,w,h,.56+d,(d-.56)/2,STONE,'central shoulders')
    for left,right in zip(peak[2:4],peak[3:5]):
        face.line((*left,.12),(*right,.12),.075,STONE,7,'gable coping')
        face.line((left[0],left[1]-.15,.085),(right[0],right[1]-.15,.085),.048,ARCH,6,'gable underside')
    face.box(0,13.15,3.98,.12,.65,-.22,TERRACOTTA,'pediment spring')
    origin=face.point(0,0,-.23)
    face.builder.lathe(origin[:2],[(14.89,.065),(15.19,.076),(15.41,.035),(FINIAL,.022)],
                       IRON,7 if distant else 11,'central roof finial')
    for z in (FLOOR-.08,9.79):
        courses(face,z,7.32,distant,'central floor and pediment bed')


def wing(face,distant):
    holes=[]
    for j,x in enumerate((-1.52,1.52)):
        window(face,holes,x,.61,1.63,2.70,.20,distant,'lower wing window',3,3)
    recessed_gallery(face,holes,[(-1.50,2.57,.58),(1.50,2.57,.58)],
                     FLOOR+.07,7.67,distant,'wing loggia',True)
    face.prism(box(-face.length/2,0,face.length/2,11.34).difference(unary_union(holes)),
               -.50,0,BRICK,'wing front wall')
    face.box(0,10.40,face.length,.59,.31,.06,STONE,'wing pale parapet panel')
    for i in range(10):
        x=(i-4.5)*(face.length-.25)/10
        face.box(x,11.04,.38,.40,.038,.030,FRAME,'wing clerestory posts')
        face.box(x,11.04,.31,.32,.037,.052,GLASS,'wing clerestory glass')
    for z in (FLOOR-.08,9.77,11.35):
        courses(face,z,face.length,distant,'wing cornice')
    for i in range(4):
        u=(i-1.5)*face.length/4
        face.prism(Polygon([(u-.19,4.60),(u+.19,4.60),(u+.12,4.18),
                            (u-.09,3.99)]),-.015,.235,TERRACOTTA,'brick gallery bracket')


def end_bay(face,distant):
    holes=[]
    for x in (-1.08,1.08):
        window(face,holes,x,.67,1.24,2.95,.18,distant,'base sash',3,3)
        window(face,holes,x,FLOOR+.95,1.70,2.95,.34,distant,'flat arched middle sash',3,3,.655)
        # The end windows are set back behind the raised corner piers. Short
        # reveals in their own masonry material keep the return visible in both LODs.
        for side in (-1,1):
            face.box(x+side*.845,7.02,.075,2.43,.64,-.318,ARCH,'middle end window return')
        hood=ellipse_ring(x,8.40,.868,.368,0,math.pi,.11,16 if distant else 28)
        face.prism(hood,.053,.143,TERRACOTTA,'middle end window hood')
        face.box(x,FLOOR+.47,1.72,.70,.067,.041,STONE,'closed pale spandrel')
    window(face,holes,0,11.15,2.83,1.69,.23,distant,'attic window',4,2)
    outer=box(-face.length/2,0,face.length/2,13.62)
    face.prism(outer.difference(unary_union(holes)),-.52,0,BRICK,'end bay front wall')
    field=box(-1.87,10.73,1.87,13.08).difference(opening(0,11.15,2.83,1.69,.23,22))
    face.prism(field,.005,.074,STONE,'pale attic panel')
    # Long corbel table beneath the attic panel is legible in the two oblique views.
    for i in range(5 if distant else 9):
        u=-face.length/2+.31+i*(face.length-.62)/(4 if distant else 8)
        support=Polygon([(u-.105,9.98),(u+.105,9.98),(u+.078,9.76),(u-.058,9.66)])
        face.prism(support,.018,.180,TERRACOTTA,'end bay cornice blocks')
    for z in (FLOOR-.08,9.77,10.12,13.55):
        courses(face,z,face.length,distant,'end bay cornice')
    for side in (-1,1):
        face.box(side*(face.length/2-.225),6.96,.39,4.00,.34,.115,BRICK,'projecting middle corner pier')
        face.box(side*(face.length/2-.225),8.62,.55,.14,.42,.13,TERRACOTTA,'corner pier cap')
        x=side*(face.length/2-.19)
        for k in range(1,18):
            z=.30+k*.71
            face.box(x,z,.36,.16,.25,.038,TERRACOTTA,'brick corner courses')


def add_building(builder,distant):
    for x0,x1,role in SPANS:
        y=FACES_Y[role]
        face=Facade(builder,(x0,y),(x1,y),role+(' west' if x0<0 else ' east'))
        if role=='central':
            central(face,distant)
        elif role=='wing':
            wing(face,distant)
        else:
            end_bay(face,distant)
        # A small amount of depth shows what the two oblique images establish.
        # Exterior return faces go no farther than the short photographed portion.
        if role in ('central','end'):
            for side,x in ((-1,x0),(1,x1)):
                depth=1.10 if abs(x)>14 else .72
                if side<0:
                    back=Facade(builder,(x,y+depth),(x,y),'short return')
                else:
                    back=Facade(builder,(x,y),(x,y+depth),'short return')
                zmax=13.62 if role=='end' else 13.01
                back.prism(box(-depth/2,0,depth/2,zmax),-.12,0,BRICK,'bounded return')
                for z in (FLOOR-.08,9.79,zmax-.045):
                    courses(back,z,depth,distant,'return bands')
        # A construction section at the unseen end of the visible depth.
        height={'central':12.97,'end':13.57,'wing':11.29}[role]
        face.box(0,height-.03,x1-x0,.09,1.08,-.54,BASE,'upper section edge')
