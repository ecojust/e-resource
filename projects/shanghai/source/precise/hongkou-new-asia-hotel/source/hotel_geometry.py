"""The two street wings, recessed entrances and signed southeastern tower of the New Asia Hotel."""
from math import atan2, ceil, cos, pi, sin
from pathlib import Path

from shapely import affinity
from shapely.geometry import LineString, Polygon, box
from shapely.ops import unary_union
from photo_architecture import Facade
from sign_lettering import add_facade_lettering, lettering_shapes

PALETTE = {
    'light toasted brick':{'color':[.42,.246,.168],'roughness':.89},
    'brown brick pilaster':{'color':[.343,.178,.111],'roughness':.9},
    'variegated brick':{'color':[.49,.293,.188],'roughness':.92},
    'buff architectural stone':{'color':[.672,.622,.522],'roughness':.75},
    'pale cut-stone podium':{'color':[.638,.614,.551],'roughness':.81},
    'stone rebates':{'color':[.472,.443,.369],'roughness':.84},
    'warm window glass':{'color':[.159,.184,.185],'roughness':.27,'metallic':.15},
    'smoked door glass':{'color':[.083,.109,.110],'roughness':.24,'metallic':.16},
    'deep bronze joinery':{'color':[.121,.108,.088],'roughness':.51,'metallic':.38},
    'satin dark metal':{'color':[.105,.115,.117],'roughness':.55,'metallic':.42},
    'golden bronze':{'color':[.532,.416,.237],'roughness':.52,'metallic':.34},
    'ivory sign glass':{'color':[.86,.805,.652],'roughness':.47},
    'terrace roofing':{'color':[.382,.369,.311],'roughness':.84},
    'rear masonry':{'color':[.406,.342,.278],'roughness':.89}}
BRICK='light toasted brick'
PIER='brown brick pilaster'
PALE='buff architectural stone'
BASE='pale cut-stone podium'
FRAME='deep bronze joinery'
GLASS='warm window glass'
FONT=Path(__file__).with_name('fonts')/'NewAsiaSign.otf'
BASE_TOP=4.48
STOREY=3.17
ROOF=26.74
R=12.0
CX=46.298
CY=12.0
ANGLE=1.225


def arc(angle,r=R):
    return (CX+r*sin(angle),CY-r*cos(angle))


def directed(b,angle,r,wide,label):
    x,y=arc(angle,r)
    a=(x-cos(angle)*wide/2,y-sin(angle)*wide/2)
    c=(x+cos(angle)*wide/2,y+sin(angle)*wide/2)
    return Facade(b,a,c,label)


def openings(f,panes,lod):
    for label,items in panes.items():
        glasses=[];frames=[]
        for hole,columns,rows,depth in items:
            x,z,X,Z=hole.bounds
            glasses.append(hole.buffer(.009,join_style='mitre'))
            inner=hole.buffer(-.062,join_style='mitre')
            lines=[]
            for col in range(1,columns):
                cx=x+(X-x)*col/columns;lines.append(box(cx-.024,z,cx+.024,Z))
            for row in range(1,rows):
                cz=z+(Z-z)*row/rows;lines.append(box(x,cz-.023,X,cz+.023))
            interior=inner.difference(unary_union(lines)) if lines else inner
            frames.append(hole.difference(interior))
        if not glasses:
            continue
        depth=items[0][3]
        f.prism(unary_union(glasses),-depth-.018,-depth,'smoked door glass' if label=='doors' else GLASS,label+' glazing')
        f.prism(unary_union(frames),-depth+.023,-depth+.087,FRAME,label+' transoms and mullions')


def stone_courses(f,area,lod):
    joints=[]
    for i in range(1,8):
        z=i*.563;joints.append(box(-f.length/2,z-.009,f.length/2,z+.009))
        if lod:
            continue
        for j in range(-ceil(f.length/2),ceil(f.length/2)+1):
            x=1.34*j+(.68 if i%2 else 0)
            joints.append(box(x-.008,z-.558,x+.008,z-.014))
    f.prism(area.intersection(unary_union(joints)),.002,.014,'stone rebates','podium block joints')


def facade(b,a,c,name,n,lod,kind='street',entry=False):
    f=Facade(b,a,c,name);w=f.length;pitch=w/n
    holes=[];upper=[];doors=[];spandrels=[];rails=[];details=[]
    head=ROOF+.12 if kind=='street' else ROOF+.78 if kind=='curve' else ROOF-.10
    for i in range(n):
        x=-w/2+(i+.5)*pitch
        win=.665*pitch
        if kind=='curve':
            win=.76*pitch
        if kind=='west':
            win=.68*pitch
        for j in range(7):
            z=BASE_TOP+j*STOREY
            hole=box(x-win/2,z+.49,x+win/2,z+2.43)
            holes.append(hole);upper.append((hole,2 if kind=='curve' and n==1 else 3,1 if lod else 2,.308))
            spandrels.append(box(x-win/2-.026,z-.19,x+win/2+.026,z+.39))
            rails.append(box(x-win/2-.055,z+.385,x+win/2+.055,z+.470))
            if not lod and kind!='curve' and j>0:
                rw=min(.35,win*.2)
                details.append(box(x-rw,z-.10,x+rw,z+.23).boundary.buffer(.023,join_style='mitre'))
        dw=min(pitch*.68,2.30)
        if entry:
            dw=w*.89
            h=2.76;bottom=.07
        else:
            h=2.97;bottom=.30 if (i%4!=1) else .065
        hole=box(x-dw/2,bottom,x+dw/2,bottom+h)
        doors.append((hole,2 if entry or not lod else 1,2 if not lod else 1,.56 if entry else .38))
    wall=box(-w/2,BASE_TOP,w/2,head).difference(unary_union(holes))
    f.prism(wall,-.29,0,BRICK,'upper pierced walls')
    if entry or kind=='curve':
        apron=wall.intersection(box(-w/2,BASE_TOP,w/2,BASE_TOP+2.81))
        f.prism(apron,.004,.047,BASE,'light second floor around main entrance')
    f.prism(unary_union(spandrels),.007,.098,PALE,'pale spandrel panels')
    f.prism(unary_union(rails),.004,.126,'stone rebates','sashes projecting stools')
    if details:
        f.prism(unary_union(details),.102,.139,PALE,'pressed panels')
    ground=box(-w/2,0,w/2,BASE_TOP).difference(unary_union([x[0] for x in doors]))
    f.prism(ground,-.35,0,BASE,'pierced ashlar street base')
    stone_courses(f,ground,lod)
    openings(f,{'doors':doors,'guestroom':upper},lod)
    f.beam(BASE_TOP+.04,.18,.115,PALE,label='podium coping')
    f.beam(head,.16,.12,PALE,label='roof parapet')
    for i in range(n+1):
        x=-w/2+i*pitch
        left=max(-w/2,x-pitch*.095);right=min(w/2,x+pitch*.095)
        if right-left<.035:
            continue
        shaft=box(left,BASE_TOP+.15,right,head+.08)
        f.prism(shaft,.002,.13,PIER,'projecting brick piers')
        if kind=='street' and (i%4==1 or n>=18 and n-5<=i<=n-2):
            strong=n>=18 and n-5<=i<=n-2
            fin_top=head+(1.12 if strong else .38)
            width=.24 if strong else .13
            narrow=box(x-width,BASE_TOP+.28,x+width,fin_top)
            f.prism(narrow,.13,.31 if strong else .22,PALE,'continuous pale vertical fins')
            if strong:
                f.box(x,fin_top-.27,.70,.72,.53,-.01,BRICK,'raised attic fin backing')
                f.box(x,fin_top,.48,.13,.60,.10,PALE,'pale fin cap')
        if not lod and kind!='curve':
            # Small raised headers give real scale without a texture in close views.
            heads=[]
            for j in range(30):
                z=BASE_TOP+.64+j*.715
                heads.append(box(left+.04,z,right-.04,z+.035))
            f.prism(unary_union(heads),.132,.145,'variegated brick','brick header courses')
    return f


def entrance_frame(f,lod):
    f.box(0,3.35,f.length*.95,.19,.87,.26,'stone rebates','underside of main hood')
    f.box(0,3.51,f.length+.18,.14,1.01,.31,PALE,'stepped projecting entrance hood')
    for x in (-f.length*.35,f.length*.35):
        for j in range(3):
            f.box(x,3.21-j*.073,.20,.089,.70-j*.13,.13,PALE,'layered stone corbels')
    if not lod:
        for x in (-.53,.53):
            f.box(x,1.05,.038,.36,.073,-.465,'golden bronze','entrance handles')


def secondary_corner(b,ring,lod):
    for i,(a,c) in enumerate(zip(ring,ring[1:])):
        w=LineString([a,c]).length
        facade(b,a,c,'Western rounded end '+str(i+1),max(1,round(w/3.65)),lod,'west')


def crown(b,lod,angles):
    # The wide gold band follows the curved outer wall. The roof sign is centred over its primary door.
    for a,c in zip(angles,angles[1:]):
        f=Facade(b,arc(a),arc(c),'Corner top')
        f.box(0,27.18,f.length+.009,1.07,.33,.075,'golden bronze','curved letter fascia')
        f.box(0,27.74,f.length+.021,.12,.43,.125,PALE,'curved cap')
    centre=ANGLE/2
    spine=directed(b,centre,R+.035,.6,'Corner centre')
    spine.box(0,16.62,.44,20.12,.20,.08,PALE,'stone ribbon between paired central windows')
    for theta in (ANGLE*.19,ANGLE*.81):
        shaft=directed(b,theta,R+.016,1.0,'Corner brick shafts')
        shaft.box(0,16.40,.66,20.03,.28,.012,PIER,'flanking tower column')
        if not lod:
            segments=[]
            for j in range(90):
                z=6.63+j*.215
                segments.append(box(-.298,z,.298,z+.014))
            shaft.prism(unary_union(segments),.155,.170,'variegated brick','horizontal tile lines')
    for char,shape in lettering_shapes('GOLDEN TULIP',10.16,.637,font=FONT):
        u=shape.centroid.x;theta=centre+u/R
        f=directed(b,theta,R+.22,1.5,'Present entrance lettering')
        f.prism(affinity.translate(shape,xoff=-u,yoff=27.17),.006,.051,'ivory sign glass',char)
    front=directed(b,centre,R-1.64,6.04,'Rooftop tower')
    # Recessed masonry stage just behind the rounded cap.
    def pt(u,v):
        q=front.point(u,0,-v)
        return (q[0],q[1])
    floor=Polygon([pt(-3.05,0),pt(3.05,0),pt(3.05,4.48),pt(-3.05,4.48)])
    b.plan_prism(floor,26.53,27.63,'terrace roofing','Tower/flat podium')
    f=front
    vents=[box(-1.55,28.44,-.26,30.79),box(.26,28.44,1.55,30.79)]
    f.prism(box(-3.02,27.53,3.02,31.36).difference(unary_union(vents)),-.33,0,PALE,'stone stage with vents')
    for hole in vents:
        x,z,X,Z=hole.bounds
        f.prism(hole.buffer(.008,join_style='mitre'),-.30,-.27,'satin dark metal','louvre wells')
        for i in range(6 if lod else 12):
            y=z+.1+i*(Z-z-.16)/(5 if lod else 11)
            f.box((x+X)/2,y,X-x,.044,.11,-.149,FRAME,'louvre blades')
    for x in (-2.56,2.56):
        f.box(x,29.43,.69,3.85,.33,.045,PIER,'tower accent piers')
        f.box(x,29.50,.125,2.66,.12,.24,PALE,'tower accents')
    for a,c in zip([pt(3.02,0),pt(3.02,4.48),pt(-3.02,4.48)],[pt(3.02,4.48),pt(-3.02,4.48),pt(-3.02,0)]):
        side=Facade(b,a,c,'Tower back and returns')
        side.wall(27.53,31.34,thickness=.24,material='rear masonry')
    b.plan_prism(floor.buffer(.09,join_style='mitre'),31.34,31.55,PALE,'Tower/coping')
    sign=directed(b,centre,R-2.44,4.15,'Existing roof name')
    for depth in (0,1.10):
        for x in (-1.57,1.57):
            sign.box(x,34.43,.105,5.65,.095,-depth,'satin dark metal','vertical sign steel')
        for z in (31.70,32.05,34.58,37.16):
            sign.box(0,z,3.20,.105,.125,-depth,'satin dark metal','steel header')
        if not lod:
            for y in (32.03,34.61):
                sign.line((-1.52,y,-depth),(1.52,y+2.48,-depth),.047,'satin dark metal',7,'diagonal bracing')
    for x in (-1.58,1.58):
        for z in (31.73,34.60,37.14):
            sign.box(x,z,.12,.12,1.18,-.56,'satin dark metal','sides of sign frame')
    for i,c in enumerate('新亞'):
        add_facade_lettering(sign,c,0,35.85-i*2.55,2.96,2.24,.125,.217,'ivory sign glass',label='Vertical name',font=FONT)


def make_hotel(b,lod):
    # Points are the independent current provider owner, transformed to the tangent street edge.
    west=[(-65.813,15.45),(-66.408,5.325),(-64.785,1.688),(-59.974,-1.241),(-55.18,-1.89),(-46.298,0)]
    angles=[ANGLE*i/5 for i in range(6)]
    bend=[arc(a) for a in angles]
    rest=[(65.464,29.791),(63.832,34.568),(57.423,37.714),(37.48,36.64),(38.656,15.68),west[0]]
    course=[west[-1],*bend,*rest,*west[1:-1]]
    footprint=Polygon(course);assert footprint.is_valid and footprint.exterior.is_ccw
    primary=Facade(b,bend[2],bend[3],'Door threshold')
    half=primary.length*.89/2
    pocket=Polygon([primary.point(u,0,d)[:2] for u,d in [(-half,.04),(half,.04),(half,-.56),(-half,-.56)]])
    b.plan_prism(footprint.buffer(-.027,join_style='mitre').difference(pocket),.002,.055,
                 'stone rebates','Hotel/ground floor leaving recessed door')
    b.plan_prism(footprint.buffer(-.08,join_style='mitre'),ROOF-.26,ROOF-.10,'terrace roofing','Main roof/bounded deck')
    facade(b,west[-1],bend[0],'Tiantong Road',22,lod)
    for i,(a,c) in enumerate(zip(bend,bend[1:])):
        f=facade(b,a,c,'Signed entrance round '+str(i+1),1,lod,'curve',entry=i==2)
        if i==2:
            entrance_frame(f,lod)
    facade(b,bend[-1],rest[0],'North Sichuan Road',6,lod)
    for i in (0,1,2):
        f=facade(b,rest[i],rest[i+1],'Northeast return '+str(i+1),max(1,round(LineString([rest[i],rest[i+1]]).length/4.2)),lod,'west')
    # These two backs touch a different owner. Inset the wall body and terminate all ornament here.
    for a,c in zip(rest[3:5],rest[4:6]):
        f=Facade(b,a,c,'Shared rear alignment')
        f.prism(box(-f.length/2,0,f.length/2,ROOF-.07),-.26,-.035,'rear masonry','inset wall')
    secondary_corner(b,west,lod)
    crown(b,lod,angles)
