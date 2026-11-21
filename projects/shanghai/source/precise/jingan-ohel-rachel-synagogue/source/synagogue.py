"""Photo-informed exterior of Ohel Rachel in the North Shaanxi Road education compound."""
from math import cos, sin, pi
from shapely.geometry import Point, Polygon, box
from shapely.ops import unary_union
from photo_architecture import Facade

STONE = 'warm weathered ashlar'
CARVED = 'carved pale stone'
PLINTH = 'grey dressed plinth'
FRAME = 'charcoal metal tracery'
GLASS = 'smoky glazing'
DOOR = 'dark timber door'
TILE = 'weathered terracotta tile'
LEDGE = 'grey leaded terrace'
PALETTE = {key: dict(color=color, roughness=roughness) for key,color,roughness in [
    (STONE,[.706,.663,.594],.92),(CARVED,[.827,.778,.681],.88),(PLINTH,[.495,.473,.428],.91),
    (FRAME,[.161,.158,.143],.57),(GLASS,[.212,.260,.270],.32),(DOOR,[.246,.175,.127],.8),
    (TILE,[.625,.351,.256],.88),(LEDGE,[.355,.339,.303],.90)]}

HALF_WIDTH = 8.86
FRONT = -13.21
REAR = 13.21
PORTICO_HALF = 3.00
INNER_FRONT = -10.87
EAVE = 8.50

def arched(center, sill, width, top, resolution):
    half=width/2; spring=top-half
    return box(center-half,sill,center+half,spring).union(Point(center,spring).buffer(half,quad_segs=resolution))

def tubular_loop(f, center, z, rx, rz, d, radius, material, segments, label):
    points=[f.point(center+rx*cos(i*2*pi/segments),z+rz*sin(i*2*pi/segments),d) for i in range(segments+1)]
    f.builder.tube(points,radius,material,6,label)

def window(f,p,columns,rows,lod):
    f.window(p,columns=columns,rows=rows,frame=FRAME,glass=GLASS,trim=False,label='inset window')
    # The sill is modeled explicitly because a round aperture has no horizontal ledge.
    f.builder.parts.pop()
    f.prism(p.buffer(.085,join_style=2).difference(p),-.035,.075,CARVED,'raised window reveal')

def course(f, low, top, holes):
    blank=unary_union(holes)
    for i in range(13):
        z=.56+.50*i
        if not low<=z<top:continue
        face=box(-f.length/2+.018,z,f.length/2-.018,z+.36).difference(blank.buffer(.11))
        if not face.is_empty:f.prism(face,-.005,.071,STONE,'projecting horizontal ashlar band')

def crest(f,u,sill,span):
    z=sill;dx=span/2
    f.line((u-dx,z,.13),(u,z+.39,.16),.083,CARVED,6,'split pediment rake')
    f.line((u,z+.39,.16),(u+dx,z,.13),.083,CARVED,6,'split pediment rake')
    for sign in (-1,1):
        f.box(u+sign*dx*.78,z-.09,dx*.53,.13,.22,.1,CARVED,'pediment return')

def cornice(f,lod,ornament):
    for z,h,out,mat in [(7.58,.15,.20,STONE),(7.77,.20,.28,CARVED),(8.06,.17,.34,CARVED),(8.27,.23,.48,CARVED),(8.48,.12,.52,LEDGE)]:
        f.beam(z,h,out,mat)
    if ornament:
        count=round(f.length/.46)
        for i in range(count):
            u=(i+.5)*f.length/count-f.length/2
            f.box(u,8.03,.23,.16,.29,.25,STONE,'modillion below projecting cornice')
            if not lod:f.box(u,7.92,.14,.085,.22,.26,CARVED,'modillion tip')

def wing(b,a,c,lod):
    f=Facade(b,a,c,'front rusticated pier')
    p=box(-.69,.76,.69,3.57);oculus=Point(0,5.94).buffer(.67,quad_segs=8 if lod else 14)
    f.wall(.22,7.69,[p,oculus],thickness=.28,material=STONE)
    course(f,.45,7.1,[p,oculus]);window(f,p,2,3,lod)
    f.box(0,.70,1.63,.15,.38,.066,CARVED,'window sill');crest(f,0,3.74,1.93)
    f.prism(oculus,-.23,-.20,GLASS,'round window at front')
    tubular_loop(f,0,5.94,.73,.73,.12,.103,CARVED,22 if lod else 40,'oculus stone moulding')
    f.prism(Polygon([(-.12,6.52),(.12,6.52),(.19,6.89),(-.19,6.89)]),.08,.27,CARVED,'radial keystone')
    for sign in (-1,1):f.box(sign*.87,5.91,.23,.09,.13,.10,CARVED,'short oculus springing ledge')

def ionic_column(b,x,lod):
    b.lathe((x,FRONT+.32),[(.29,.50),(.39,.52),(.50,.46),(.57,.47),(.63,.41),
            (.78,.39),(3.65,.36),(6.77,.315),(6.90,.35),(7.02,.40),(7.17,.42)],CARVED,20 if lod else 36,label='Ionic column shaft and moulded base')
    f=Facade(b,(x-.63,FRONT+.32),(x+.63,FRONT+.32),'Ionic capital')
    for side in (-1,1):
        curve=[]
        for j in range(16 if lod else 31):
            phi=2.9*pi*j/(15 if lod else 30);r=.159*(1-phi/(3.15*pi))
            curve.append(f.point(side*(.30+r*cos(phi)),7.05+r*sin(phi),.34))
        b.tube(curve,.038,CARVED,6,'Ionic spiral volute')
    b.box((x,FRONT+.32,7.27),(1.01,.92,.17),CARVED,label='capital abacus')

def porch(b,lod):
    f=Facade(b,(-PORTICO_HALF,INNER_FRONT),(PORTICO_HALF,INNER_FRONT),'recessed entrance')
    door=arched(0,.28,1.60,3.83,10 if lod else 18);f.wall(.18,7.58,[door],thickness=.27,material=STONE)
    course(f,.47,7.1,[door]);spring=3.03
    leaf=door.intersection(box(-.80,.28,.80,spring));f.prism(leaf,-.19,-.16,DOOR,'inset double timber door')
    for u in (-.39,.39):
        for z in (1.04,2.10):f.box(u,z,.54,.74,.04,-.127,DOOR,'door panels')
    f.box(0,1.60,.042,2.58,.08,-.118,FRAME,'door meeting stile')
    glazing=door.intersection(box(-.9,spring,.9,3.84));f.prism(glazing,-.19,-.16,GLASS,'semicircular door fanlight')
    for ang in (pi/4,pi/2,3*pi/4):f.line((0,spring,-.107),(.75*cos(ang),spring+.75*sin(ang),-.107),.024,FRAME,6,'fanlight radial bar')
    f.prism(door.buffer(.16,join_style=2).difference(door),-.035,.13,CARVED,'doorway architrave')
    # The accessible photos show a carved cartouche above the entry. Its lettering is indistinct.
    cart=Polygon([(-.75,4.45),(.74,4.45),(.74,4.65),(.88,4.65),(.88,5.61),(.74,5.80),(-.74,5.80),(-.88,5.61),(-.88,4.65),(-.75,4.65)])
    f.prism(cart,.06,.17,CARVED,'central stone cartouche')
    f.prism(cart.buffer(-.09).difference(cart.buffer(-.15)),.17,.23,STONE,'cartouche inner rim')
    for sign in (-1,1):
        pts=[(sign*t,5.81-.19*sin(pi*t/.92),.25)for t in [k*.92/12 for k in range(13)]]
        b.tube([f.point(*q)for q in pts],.069,CARVED,6,'swag above inset panel')
    for x in (-1.86,1.86):ionic_column(b,x,lod)
    for a,c in [((-PORTICO_HALF,FRONT),(-PORTICO_HALF,INNER_FRONT)),((PORTICO_HALF,INNER_FRONT),(PORTICO_HALF,FRONT))]:
        jab=Facade(b,a,c,'portico interior return');jab.wall(.20,7.64,thickness=.20,material=STONE)
    b.plan_prism(box(-PORTICO_HALF,FRONT-.07,PORTICO_HALF,INNER_FRONT+.16),.08,.255,PLINTH,'walkable portico floor')

def long_side(b,a,c,lod):
    f=Facade(b,a,c,'long wall');holes=[]
    for u in (-8.13,-4.065,0,4.065,8.13):
        lo=box(u-.64,.76,u+.64,2.84);hi=arched(u,3.68,1.48,6.72,8 if lod else 14)
        holes.extend([lo,hi]);window(f,lo,2,3,lod);window(f,hi,2,3,lod)
        f.box(u,.70,1.55,.14,.40,.06,CARVED,'lower window sill')
        tubular_loop(f,u,5.95,.43,.42,-.10,.035,FRAME,18 if lod else 30,'round pattern in high arched glazing')
    f.wall(.18,7.74,holes,thickness=.27,material=STONE);f.beam(.34,.36,.20,PLINTH);cornice(f,lod,False)
    for u in (-11.18,-6.10,-2.03,2.03,6.10,11.18):
        f.box(u,3.92,.34,7.14,.23,.068,STONE,'wall pilaster')
    for sign in (-1,1):
        x=sign*(f.length/2-.46)
        for i in range(13):f.box(x,.63+i*.51,.83,.37,.27,.058,STONE,'end quoin')

def finish_roof(b,lod):
    y0=-10.25;y1=12.55;w=8.47;e=8.57;ridge=12.65
    for sign in (-1,1):
        x=sign*w
        p=[(0,y0,ridge),(x,y0,e),(x,y1,e),(0,y1,ridge)]
        if sign<0:p.reverse()
        b.add(p+[(a,v,z-.12)for a,v,z in p],[(0,1,2,3),(7,6,5,4),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)],TILE,'terracotta roof slope')
        # Distinct roof courses follow the long ridge visible in the WMF aerial.
        count=10 if lod else 22
        for j in range(1,count):
            t=j/count
            b.tube([(x*t,y0,ridge+(e-ridge)*t+.016),(x*t,y1,ridge+(e-ridge)*t+.016)],.021,TILE,5,'rows of roof tile')
    b.tube([(0,y0-.08,ridge+.045),(0,y1+.08,ridge+.045)],.092,CARVED,8,'roof ridge')
    for yy,front in [(y0,True),(y1,False)]:
        f=Facade(b,(-w,yy),(w,yy),'pediment') if front else Facade(b,(w,yy),(-w,yy),'rear gable')
        tri=Polygon([(-w,e-.22),(w,e-.22),(0,ridge)])
        if front:
            fan=Point(0,8.49).buffer(2.03,quad_segs=10 if lod else 20).intersection(box(-2.05,8.49,2.05,11))
            f.wall(e-.22,ridge,[fan],thickness=.17,material=STONE,outline=tri)
            f.prism(fan,-.18,-.13,GLASS,'semicircular gable window')
            for off in (-1.28,-.66,0,.66,1.28):
                top=8.49+(2.03**2-off**2)**.5
                f.line((off,8.50,-.10),(off,top-.06,-.10),.042,FRAME,6,'gable window vertical bar')
        else:f.wall(e-.22,ridge,thickness=.17,material=STONE,outline=tri)
        for sign in (-1,1):f.line((sign*w,e,.1),(0,ridge+.09,.1),.115,CARVED,8,'gable rake')

def add_building(b,lod):
    w=HALF_WIDTH
    b.plan_prism(box(-w,FRONT,w,REAR),0,.18,PLINTH,'building foundation and entry landing')
    for lo,hi in [(-w,-PORTICO_HALF),(PORTICO_HALF,w)]:wing(b,(lo,FRONT),(hi,FRONT),lod)
    porch(b,lod);front=Facade(b,(-w,FRONT),(w,FRONT),'eastern front');front.beam(7.47,.38,.12,STONE);cornice(front,lod,True)
    for side in (-1,1):
        a,c=((w,FRONT),(w,REAR)) if side==1 else ((-w,REAR),(-w,FRONT))
        long_side(b,a,c,lod)
    rear=Facade(b,(w,REAR),(-w,REAR),'west wall');rear.wall(.15,7.85,material=STONE);rear.beam(.39,.36,.14,PLINTH);cornice(rear,lod,False)
    b.plan_prism(box(-w,FRONT,w,-10.15),8.33,8.59,LEDGE,'flat terrace within entrance parapet')
    b.plan_prism(box(-w,12.38,w,REAR),8.25,8.57,LEDGE,'rear roof ledge')
    for side in (-1,1):b.plan_prism(box(min(side*w,side*8.42),-10.28,max(side*w,side*8.42),12.57),8.30,8.59,LEDGE,'long roof ledge')
    front.beam(8.70,.16,.22,CARVED)
    for left,right in [(-w,-2.09),(2.09,w)]:
        front.box((left+right)/2,9.02,right-left,.62,.40,.0,STONE,'parapet panels')
        front.box((left+right)/2,9.40,right-left+.04,.14,.51,.02,CARVED,'parapet cap')
    for x in (-5.85,5.85):front.box(x,9.45,1.56,.64,.55,.055,STONE,'raised parapet pier')
    for i in range(13):
        x=-1.94+i*3.88/12
        b.lathe((x,FRONT+.02),[(8.72,.096),(8.79,.102),(8.86,.065),(8.96,.112),(9.07,.073),(9.18,.069),(9.24,.105)],CARVED,8 if lod else 12,label='central parapet baluster')
    front.box(0,9.30,4.24,.15,.46,.015,CARVED,'balustrade rail')
    finish_roof(b,lod)
