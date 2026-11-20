"""Clay-tile roof, shutters, oculus and open east arcade of the north Zikawei library."""
from math import cos,pi,sin,sqrt
import numpy as np
from shapely.geometry import box,Polygon,Point
from shapely.ops import unary_union
from photo_architecture import Facade,opening

PALETTE={
 'warm ivory render':{'color':[.751,.731,.672],'roughness':.85},
 'limestone trim':{'color':[.797,.782,.712],'roughness':.78},
 'deep grey plinth':{'color':[.315,.320,.328],'roughness':.85},
 'grey shutter slats':{'color':[.445,.453,.432],'roughness':.78},
 'shadow in shutters':{'color':[.227,.237,.230],'roughness':.83},
 'deep set glass':{'color':[.156,.188,.191],'roughness':.26,'metallic':.17},
 'window timber':{'color':[.300,.308,.280],'roughness':.68},
 'terracotta roof':{'color':[.552,.302,.232],'roughness':.88},
 'lighter terracotta':{'color':[.626,.356,.273],'roughness':.88},
 'weathered tile joint':{'color':[.448,.292,.244],'roughness':.92},
 'roof ridge':{'color':[.513,.321,.268],'roughness':.88},
 'stained truss timber':{'color':[.232,.190,.143],'roughness':.79},
 'hall interior plaster':{'color':[.652,.621,.567],'roughness':.88},
 'ground stone':{'color':[.449,.437,.408],'roughness':.93},
 'porch pavement':{'color':[.548,.527,.474],'roughness':.92},
 'dark vent metal':{'color':[.203,.212,.210],'roughness':.54,'metallic':.38}}
WALL='warm ivory render';TRIM='limestone trim';PLINTH='deep grey plinth'
L=-14.04;R=14.04;BACK=13.30;EAVE=8.77;RIDGE=11.78;FIRST=4.20;ARCADE=9.69
FLOOR=box(L,0,R,BACK)


def shutter(f,u,shape,opened,lod):
    x,z,X,Z=shape.bounds;middle=(x+X)/2;inner=shape.buffer(-.082,join_style='mitre')
    f.prism(shape.buffer(.004),-.292,-.27,'deep set glass','arched glazing')
    bars=[box(middle-.030,z,middle+.03,Z),box(x,z+(Z-z)*.60,X,z+(Z-z)*.60+.043)]
    f.prism(shape.difference(inner.difference(unary_union(bars))),-.245,-.172,'window timber','arched joinery')
    # Folding halves remain inside the stone reveal. Open examples expose the central glass.
    for side in [-1,1]:
        if opened:
            left=x-.38 if side<0 else X+.025
            right=x-.025 if side<0 else X+.38
            sh=box(left,z+.05,right,Z-.40)
        else:
            panel=box(x+.020,z+.014,middle-.016,Z+.02) if side<0 else box(middle+.016,z+.014,X-.020,Z+.02)
            sh=shape.intersection(panel)
        if sh.is_empty:continue
        outside=.118 if opened else -.083
        f.prism(sh,outside-.051,outside,'shadow in shutters','folding shutter leaf')
        rail=sh.difference(sh.buffer(-.052,join_style='mitre'))
        f.prism(rail,outside+.002,outside+.035,'grey shutter slats','shutter rim')
        inside=sh.buffer(-.065,join_style='mitre');strips=[]
        step=.125 if lod else .073
        for j in range(1,int((Z-z)/step)+1):
            h=z+j*step;strips.append(box(x-.45,h,X+.45,h+step*.62))
        f.prism(inside.intersection(unary_union(strips)),outside+.010,outside+.039,'grey shutter slats','shutter louvers')
    f.box(u,z-.050,X-x+.27,.119,.445,.040,TRIM,'stone sill')
    trim=shape.buffer(.075,quad_segs=6).difference(shape).intersection(box(x-.17,z,X+.17,Z+.16))
    f.prism(trim,-.010,.073,TRIM,'arched raised surround')


def facade(b,a,c,south,lod):
    f=Facade(b,a,c,'South courtyard' if south else 'North side')
    dx=(R-L)/6
    holes=[];covers=[]
    slots=[]
    for i in range(6):
        u=-f.length/2+(i+.5)*dx
        end=i==5 if south else i==0
        upper=opening(u,5.13,1.47,2.49,.68,segments=12 if lod else 24)
        holes.append(upper);covers.append((u,upper,(south and i in [1,3,4])))
        if end:
            op=opening(u,-.012,3.45,3.23,.84,segments=16 if lod else 28)
            holes.append(op);slots.append(op)
        else:
            lower=opening(u,1.24,1.42,2.23,.63,segments=12 if lod else 24)
            holes.append(lower);covers.append((u,lower,south and i==2))
    surface=box(-f.length/2,0,f.length/2,EAVE).difference(unary_union(holes))
    f.prism(surface,-.29,0,WALL,'pierced masonry')
    f.prism(surface.intersection(box(-f.length/2,0,f.length/2,1.07)),.005,.047,PLINTH,'grey base')
    for u,opening_,opened in covers:shutter(f,u,opening_,opened,lod)
    for op in slots:
        f.prism(op.buffer(.133,quad_segs=8).difference(op).intersection(box(-f.length/2,.04,f.length/2,3.61)),
                -.006,.083,TRIM,'arcade outer ring')
    for i in range(7):
        u=-f.length/2+i*dx
        w=.33 if i not in [0,6] else .41
        f.prism(box(max(-f.length/2,u-w/2),1.08,min(f.length/2,u+w/2),EAVE-.27),.003,.078,WALL,'shallow pilasters')
    f.beam(FIRST,.102,.087,TRIM,width=f.length+.02,label='lower string course')
    f.beam(EAVE-.255,.101,.187,TRIM,width=f.length+.04,label='eave mould')
    f.beam(EAVE-.078,.163,.263,TRIM,width=f.length+.08,label='upper cornice')
    dentils=[]
    for i in range(91 if not lod else 56):
        pitch=f.length/(91 if not lod else 56);u=-f.length/2+(i+.5)*pitch
        dentils.append(box(u-.066,EAVE-.47,u+.066,EAVE-.29))
    f.prism(unary_union(dentils),.035,.142,TRIM,'dentil blocks')
    return f


def endwall(b,east,lod):
    a,c=((R,0),(R,BACK)) if east else ((L,BACK),(L,0))
    f=Facade(b,a,c,'Caoxi Road east gable' if east else 'Western return')
    width=f.length;outline=Polygon([(-width/2,0),(width/2,0),(width/2,EAVE),(0,RIDGE),(-width/2,EAVE)])
    eye=Point(0,9.57).buffer(.54,quad_segs=12 if lod else 24)
    openings=[eye];arcades=[]
    if east:
        for i in range(3):
            u=(i-1)*3.46
            op=opening(u,-.014,1.83,3.05,.78,segments=14 if lod else 28)
            openings.append(op);arcades.append(op)
    surface=outline.difference(unary_union(openings))
    f.prism(surface,-.29,0,WALL,'gable wall and lower arcade')
    f.prism(surface.intersection(box(-width/2,0,width/2,1.07)),.004,.047,PLINTH,'grey gable base')
    for op in arcades:
        f.prism(op.buffer(.093,quad_segs=8).difference(op).intersection(box(-width/2,.04,width/2,3.31)),
                -.009,.052,TRIM,'arcade ring')
    for h,w,d in [(FIRST,.10,.121),(8.34,.11,.14)]:
        f.beam(h,w,d,TRIM,width=width+.015,label='horizontal gable band')
    f.prism(eye.buffer(.087).difference(eye),-.022,.067,TRIM,'round vent rebate')
    f.prism(eye,-.22,-.19,'dark vent metal','round grille')
    lines=[box(-.59,9.57+j*.101-.019,.59,9.57+j*.101+.019) for j in range(-5,6)]
    f.prism(eye.intersection(unary_union(lines)),-.165,-.10,'grey shutter slats','oculus louvers')
    gable=outline.boundary.buffer(.085,join_style='mitre').intersection(box(-width/2,EAVE-.02,width/2,RIDGE+.17))
    f.prism(gable,.004,.10,TRIM,'raking gable band')


def corner_piers(b):
    # Each orthogonal masonry return has a closed, overlapping corner. A single
    # stepped pier gives it one continuous exterior skin on both visible faces.
    for x,dx in [(L,1),(R,-1)]:
        for y,dy in [(0,1),(BACK,-1)]:
            outline=[(x+dx*u,y+dy*v) for u,v in
                     [(-.084,-.084),(.36,-.084),(.36,.10),(.10,.10),(.10,.36),(-.084,.36)]]
            pier=Polygon(outline)
            name='Corner pier/'+('east' if dx<0 else 'west')+('-court' if dy>0 else '-outer')
            b.plan_prism(pier,0,1.072,PLINTH,name+' base')
            b.plan_prism(pier,1.072,EAVE-.26,WALL,name+' plaster return')


def roof(b,lod):
    left,right=L-.19,R+.19
    far=BACK+.22;front=-.22;peak=BACK*.5
    for start,end in [(front,peak),(peak,far)]:
        def height(y):
            return EAVE+.035+(RIDGE-EAVE+.03)*(1-abs((y-peak)/(peak-front)))
        def mapper(x,y,d):
            return (x,y,height(y)+d)
        face=box(left,start,right,end)
        b.prism(face,-.09,.015,mapper,'terracotta roof','Roof/tiled plane')
        rows=14 if lod else 22;columns=52 if lod else 90
        # Stagger the tile-head joints. Row lines cross the roof along its ridge.
        field=[];joints=[]
        for j in range(rows):
            ya=start+(end-start)*j/rows;yb=start+(end-start)*(j+1)/rows
            field.append(box(left,ya+.008,right,ya+.026))
            for i in range(columns):
                x=left+(right-left)*(i+(.55 if j%2 else .05))/columns
                joints.append(box(x,ya+.028,x+.016,yb-.01))
        b.prism(unary_union(field),.020,.038,mapper,'lighter terracotta','Roof/overlapping tile courses')
        b.prism(unary_union(joints),.017,.023,mapper,'weathered tile joint','Roof/staggered side joints')
    for i in range(46 if lod else 76):
        step=(right-left)/(46 if lod else 76);a=left+i*step
        b.tube([(a,peak,RIDGE+.10),(a+step-.012,peak,RIDGE+.10)],.115,'roof ridge',8,'Roof/capped ridge units')


def make_library(b,lod):
    facade(b,(L,0),(R,0),True,lod);facade(b,(R,BACK),(L,BACK),False,lod)
    endwall(b,True,lod);endwall(b,False,lod);corner_piers(b);roof(b,lod)
    b.plan_prism(box(L+.023,.03,ARCADE,BACK-.028),.008,.064,'ground stone','Library room/solid floor')
    b.plan_prism(box(ARCADE+.02,.025,R-.05,BACK-.025),.006,.042,'porch pavement','East arcade/walkable paving')
    # Stop inside the longitudinal wall thickness. Taking the partition all the
    # way to the outer skin would expose overlapping end faces on both sides.
    room=Facade(b,(ARCADE,.13),(ARCADE,BACK-.13),'West inner arcade wall')
    room.wall(0,FIRST,thickness=.26,material='hall interior plaster')
    b.plan_prism(box(ARCADE,-.008,R+.012,BACK+.008),FIRST-.15,FIRST+.065,'hall interior plaster','East arcade/upper floor soffit')
    for y in [1.08,4.76,8.53,12.40]:
        x=(ARCADE+R)/2
        b.tube([(ARCADE,y,3.94),(R-.20,y,3.94)],.093,'stained truss timber',4,'East arcade/truss tie')
        b.tube([(x-1.59,y,3.95),(x-.04,y,3.29),(x+1.58,y,3.95)],.069,'stained truss timber',4,'East arcade/diagonal braces')
