"""Yellow-brick courtyard facade seen in the dated pictures of 561 Jiaozhou Road."""
from math import cos, pi, sin
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union
from photo_architecture import Facade

BRICK='Buff and russet masonry'
MORTAR='Muted horizontal mortar'
ACCENT='Red brick and tile'
WOOD='Brown pierced timber'
SHADE='Dark wood soffit'
STONE='Worn grey stone'
WHITE='Painted sash and iron'
GLASS='Window glass'
DARK='Recessed dark door leaf'
MATERIALS = {k:dict(color=c,roughness=r) for k,c,r in [
    (BRICK,[.653,.49,.342],.93),(MORTAR,[.544,.427,.333],.92),
    (ACCENT,[.458,.231,.166],.9),(WOOD,[.430,.345,.282],.83),
    (SHADE,[.182,.143,.119],.92),(STONE,[.532,.5,.439],.87),
    (WHITE,[.704,.692,.623],.77),(GLASS,[.234,.262,.247],.39),
    (DARK,[.144,.15,.152],.88)]}
GABLE_X=3.04
GABLE_HALF=2.02
EAVE=6.02
RIDGE=8.92
PORCH_HALF=1.62
PORCH_EAVE=2.63
PORCH_RIDGE=4.62
FRONT=-1.36
BACK=.75

def strip(face,l,r,b,t,low,high,material,label):
    face.prism(box(l,b,r,t),low,high,material,label)

def courses(face,wall,d,far,label):
    """Short staggered joints and restrained variations follow the visible brickwork."""
    x0,z0,x1,z1=wall.bounds
    stride=.088
    joints=[];headers=[]
    for j in range(int(z0/stride)+1,int(z1/stride)):
        z=j*stride
        if j%(6 if far else 2)==0:joints.append(box(x0,z-.004,x1,z+.004))
        if far or j%2:continue
        pitch=.31
        for i in range(int((x1-x0)/pitch)):
            x=x0+(i+.25+.5*(j%4==0))*pitch
            joints.append(box(x-.004,z,x+.004,z+stride*1.95))
            if (i*11+j*7)%19==3:headers.append(box(x+.018,z+.014,x+.22,z+stride*.85))
    for pieces,material,tag in [(joints,MORTAR,' joints'),(headers,ACCENT,' occasional red headers')]:
        if pieces:face.prism(wall.intersection(unary_union(pieces)),d+.002,d+.009,material,label+tag)

def framed_window(face,l,r,b,t,d,divisions,far,label):
    """Paired side-hung outer sashes and the narrower physically visible rectangular panes."""
    o=box(l,b,r,t);inner=o.buffer(-.053,join_style=2)
    w=r-l;h=t-b
    face.prism(o,d-.16,d-.135,GLASS,label+' glass')
    bars=[o.difference(inner)]
    for j in range(1,divisions):
        u=l+j*w/divisions
        thickness=.040 if j==divisions//2 else .021
        bars.append(box(u-thickness,b,u+thickness,t))
    for s in [.34,.69]:
        z=b+s*h;bars.append(box(l,z-.020,r,z+.020))
    face.prism(unary_union(bars),d-.105,d-.045,WHITE,label+' divided sashes')
    strip(face,l-.072,r+.072,b-.077,b+.008,d-.09,d+.069,STONE,label+' sill')

def roof_face(builder,points,material,label,thick=.074):
    other=[(x,y,z-thick) for x,y,z in points]
    faces=[(0,1,2),(0,2,3),(4,6,5),(4,7,6)]
    for i in range(4):
        j=(i+1)%4;faces.extend(((i,j,j+4),(i,j+4,i+4)))
    builder.add(points+other,faces,material,label)

def pierced_edge(face,c,half,eaves,peak,d,far,label):
    """Saw-cut hooks are joined at their shoulders with real openings below the raking fascia."""
    count=(8 if half>1.7 else 7) if far else (12 if half>1.7 else 10)
    for side in (-1,1):
        tip=(c+side*half,eaves)
        edge=LineString([(c,peak),tip]).buffer(.067,cap_style=2,join_style=2)
        face.prism(edge,d-.045,d+.035,WOOD,label+' outer raking board')
        hooks=[]
        for i in range(count):
            length=((half/count)**2+((peak-eaves)/count)**2)**.5
            t=(i+.45)/count;u=c+side*half*t;z=peak-(peak-eaves)*t
            tx=side*(half/count)/length;tz=-(peak-eaves)/count/length
            nx=side*tz;nz=-abs(tx)
            def position(along,inward):
                return (u+length*(along*tx+inward*nx),z+length*(along*tz+inward*nz))
            # Flat sawn timber curls toward the open triangle; alternate tails join the fascia.
            coords=[position(-.44,.040),position(-.30,.22),position(-.13,.39),position(.10,.40),
                    position(.36,.52),position(.42,.73),position(.29,.90),position(.08,.91),
                    position(-.06,.80),position(-.03,.68)]
            hooks.append(LineString(coords).buffer(.025 if far else .030,cap_style=1,join_style=1,quad_segs=4))
        face.prism(unary_union(hooks),d-.030,d+.006,WOOD,label+' pierced scrolls')
    face.prism(LineString([(c,peak-.035),(c,peak-.51)]).buffer(.030,cap_style=2),d-.03,d+.019,WOOD,label+' pendant shaft')
    tip=Polygon([(c-.028,peak-.33),(c-.065,peak-.39),(c-.051,peak-.46),(c,peak-.57),(c+.051,peak-.46),(c+.065,peak-.39),(c+.028,peak-.33)])
    face.prism(tip,d-.043,d+.038,WOOD,label+' turned pendant')

def window_guard(face,far):
    l,r=GABLE_X-.84,GABLE_X+.84;z=3.99
    for dz,projection in ((0,.15),(.34,.25)):
        face.line((l,z+dz,projection),(r,z+dz,projection),.025,WHITE,6,'Curved flower guard rails')
    for i in range(11 if not far else 7):
        count=10 if not far else 6
        x=l+(r-l)*i/count
        pts=[face.point(x,z+.014,.15),face.point(x+.023,z+.095,.33),face.point(x+.034,z+.22,.34),face.point(x,z+.338,.25)]
        face.builder.tube(pts,.019,WHITE,6,'Curved flower guard bars')
    for x in [l,r]:
        for dz,p in [(0,.15),(.34,.25)]:face.line((x,z+dz,.006),(x,z+dz,p),.021,WHITE,6,'Flower guard returns')

def add_building(b,distant=False):
    front=Facade(b,(-5,0),(5,0),'Brick gable')
    left=Facade(b,(-5,BACK),(5,BACK),'Porch wall')
    c=GABLE_X;l=c-GABLE_HALF;r=c+GABLE_HALF
    holes=[box(c-.69,1.02,c+.69,2.44),box(c-.66,4.31,c+.66,5.62),box(c-.068,7.03,c+.068,7.47)]
    profile=Polygon([(l,.00),(r,.00),(r,EAVE),(c,RIDGE),(l,EAVE)])
    wall=profile.difference(unary_union(holes));front.prism(wall,-.31,0,BRICK,'Yellow brick gable')
    courses(front,wall,0,distant,'East gable')
    for label,window in zip(('Lower','Upper'),holes[:2]):
        framed_window(front,*[window.bounds[i] for i in (0,2,1,3)],0,4,distant,label+' right-hand window')
    front.prism(holes[2],-.2,-.15,SHADE,'Narrow attic vent')
    for i in range(1,4):strip(front,c-.062,c+.062,7.02+i*.105,7.04+i*.105,-.10,-.067,WOOD,'Attic vent louvers')
    for x in (l+.11,r-.50):strip(front,x,x+.44,5.46,5.57,0,.034,STONE,'Pale gable end stones')
    strip(front,l,r,3.63,3.69,.0,.042,ACCENT,'Ground storey string course')
    window_guard(front,distant)
    for side in (-1,1):
        e=c+side*(GABLE_HALF+.095)
        roof_face(b,[(c,-.14,RIDGE+.06),(e,-.14,EAVE),(e,1.52,EAVE),(c,1.52,RIDGE+.06)],ACCENT,'Short right roof plane')
    pierced_edge(front,c,GABLE_HALF+.065,EAVE,RIDGE+.04,.206,distant,'Gable')
    # The tree obscures the remaining facade. The clipped roof return ends at the last photographed wall.
    door=box(-.62,.12,.62,2.54);small=box(-2.34,1.14,-1.75,2.18);above=box(-1.73,4.53,-.66,5.75)
    junction=Polygon([(-2.58,0),(l+.01,0),(l+.01,6.22),(-2.58,7.35)])
    rear= junction.difference(unary_union([door,small,above]));left.prism(rear,-.29,0,BRICK,'Documented porch wall')
    courses(left,rear,0,distant,'Porch wall')
    for opening,label,div in ((small,'Narrow side sash',2),(above,'Partly seen upper sash',4)):
        framed_window(left,*[opening.bounds[i] for i in (0,2,1,3)],0,div,distant,label)
    left.prism(door,-.36,-.30,DARK,'Dark recessed door')
    outer=box(-.76,.06,.76,2.68);left.prism(outer.difference(door),-.035,.05,SHADE,'Timber door lining')
    # Only the short cheek beside the wall, the photographed porch and its shallow stone step are included.
    join=Facade(b,(l,0),(l,BACK),'Gable return');join.wall(0,EAVE,[],.13,BRICK)
    porch=Facade(b,(-5,FRONT),(5,FRONT),'Front timber porch')
    for sign in (-1,1):
        u=sign*1.29
        for z0,z1,width,depth,m,name in [(.045,.13,.25,.25,STONE,'Foot slab'),(.13,.29,.21,.21,STONE,'Column shoe'),(.29,2.72,.142,.156,WOOD,'Timber post')]:
            strip(porch,u-width/2,u+width/2,z0,z1,-depth/2,depth/2,m,name)
    for s in (-1,1):
        x=s*PORCH_HALF
        roof_face(b,[(0,FRONT-.15,PORCH_RIDGE),(x,FRONT-.15,PORCH_EAVE),(x,BACK+.04,PORCH_EAVE),(0,BACK+.04,PORCH_RIDGE)],ACCENT,'Pitched porch tiles')
        porch.prism(LineString([(0,PORCH_RIDGE-.04),(x,PORCH_EAVE-.04)]).buffer(.087,cap_style=2),-.11,.075,SHADE,'Deep fascia')
    fascia_triangle=Polygon([(-PORCH_HALF+.15,PORCH_EAVE-.01),(PORCH_HALF-.15,PORCH_EAVE-.01),(0,PORCH_RIDGE-.17)])
    # Recessed solid boarding is visible behind the two sawn edges; the lower porch remains open.
    porch.prism(fascia_triangle,-.26,-.17,SHADE,'Recessed timber gable board')
    for i in range(-8,9):
        u=i*.166
        joint=box(u-.008,PORCH_EAVE,u+.008,PORCH_RIDGE).intersection(fascia_triangle)
        if joint.area>.0001:porch.prism(joint,-.168,-.164,WOOD,'Gable board joints')
    pierced_edge(porch,0,PORCH_HALF,PORCH_EAVE,PORCH_RIDGE,.208,distant,'Porch')
    b.box((0,(BACK+FRONT)/2-.09,.045),(3.05,BACK-FRONT+.33,.09),STONE,label='Single shallow porch step')
