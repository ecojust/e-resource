"""Original geometry from the three public photographic records of the south garden front."""
from math import cos, sin, pi, tau
from shapely.geometry import box, Polygon, LineString
from shapely.ops import unary_union
from photo_architecture import Facade

PLASTER='Warm grey dressed stucco'
STONE='Pale stone frames'
LIMESTONE='Pale granite columns'
PANEL='Grey stone panels'
RISER='Brown grey entrance granite'
OCHRE='Weathered roof tiles'
WOOD='Stained mahogany'
GLASS='Shaded casement glass'
SHUTTER='Oxide red shutters'
SHADE='Deep reveal shadow'
MATERIALS={k:dict(color=c,roughness=r)for k,c,r in (
    (PLASTER,[.67,.65,.59],.91),(STONE,[.76,.735,.66],.84),
    (LIMESTONE,[.715,.705,.65],.76),(PANEL,[.49,.50,.47],.9),
    (RISER,[.475,.43,.36],.86),(OCHRE,[.48,.25,.18],.88),
    (WOOD,[.295,.149,.115],.74),(GLASS,[.16,.215,.217],.36),
    (SHUTTER,[.422,.225,.18],.82),(SHADE,[.112,.127,.12],.90))}
HALF=10.95
OPEN=4.63
COLUMN=2.12
BACK=2.64
RETURN=3.35
FIRST=.84
BALCONY=4.84
BEAM=8.65
EAVE=11.8

def cuboid(b,l,r,front,back,low,high,mat,name):
    b.box(((l+r)/2,(front+back)/2,(low+high)/2),(r-l,back-front,high-low),mat,label=name)

def horizontal_slab(b,xy,lo,hi,mat,name):
    b.prism(Polygon(xy),lo,hi,lambda x,y,z:(x,y,z),mat,name)

def glazed(f,shape,*,door=False,shutters=False,far=False):
    x0,z0,x1,z1=shape.bounds
    wid=x1-x0;h=z1-z0
    f.prism(shape.buffer(.007,join_style=2),-.196,-.166,GLASS,'setback glass')
    frame=shape.difference(shape.buffer(-.055,join_style=2))
    bars=[frame]
    n=(6 if wid>2.3 else 2) if door else (4 if wid>2.3 else 2)
    for i in range(1,n):
        x=x0+i*wid/n;bars.append(box(x-.026,z0,x+.026,z1))
    for percent in ([.29,.77] if door else [.48,.77]):
        z=z0+h*percent;bars.append(box(x0,z-.022,x1,z+.022))
    f.prism(unary_union(bars),-.141,-.071,WOOD,'mullions and transom')
    if door:
        for i in range(n):
            a=x0+i*wid/n+.04;c=x0+(i+1)*wid/n-.04
            f.prism(box(a,z0+.03,c,z0+.28*h),-.156,-.132,WOOD,'panelled door leaves')
            if not far:
                inner=box(a+.055,z0+.10,c-.055,z0+.26*h)
                f.prism(inner.difference(inner.buffer(-.035,join_style=2)),-.113,-.09,SHUTTER,'door panel mouldings')
                mid=(a+c)/2
                g=LineString([(a+.01,z0+.695*h),(mid,z0+.747*h),(c-.01,z0+.695*h)]).buffer(.022,cap_style=2)
                octagon=Polygon([(mid+.068*cos(j*pi/4),z0+.54*h+.085*sin(j*pi/4))for j in range(8)])
                f.prism(g.union(octagon.difference(octagon.buffer(-.015))),-.109,-.085,WOOD,'upper door fret')
    if shutters:
        sw=min(.275,wid*.22)
        for start in (x0+.012,x1-sw-.012):
            end=start+sw
            panel=box(start,z0+.032,end,z1-.03)
            f.prism(panel,-.064,-.04,SHUTTER,'folded shutter leaves')
            for i in range(2,10 if far else 23):
                z=z0+.07+h*i/(11 if far else 24)
                f.box((start+end)/2,z,sw*.88,.026,.045,-.024,WOOD,'shutter louvers')
    f.prism(shape.buffer(.072,join_style=2).difference(shape),-.025,.045,STONE,'plain stone opening trim')
    if not door:f.box((x0+x1)/2,z0-.045,wid+.19,.095,.25,.064,STONE,'sills')

def rustication(f,wall,low,top,label):
    half=f.length/2
    for i in range(1,16):
        z=low+.55*i
        if z>=top:break
        band=wall.intersection(box(-half,z-.012,half,z+.012))
        if band.area>.001:f.prism(band,.002,.013,PANEL,label)

def cornice(f,far):
    for z,h,proj,m in [(8.70,.16,.15,STONE),(8.93,.30,.20,PLASTER),(9.12,.11,.30,STONE),(9.32,.10,.31,PANEL),(9.46,.16,.46,STONE),(9.57,.07,.49,PANEL)]:
        f.beam(z,h,proj,m,width=f.length+.004,label='stepped entablature')
    nh=max(1,round(f.length/.34))
    for i in range(nh):
        u=f.length*((i+.5)/nh-.5)
        f.box(u,9.255,.139 if not far else .15,.19,.29,.175,STONE,'dentil course')

def col(b,u,far):
    cuboid(b,u-.53,u+.53,-.50,.56,FIRST,FIRST+.16,LIMESTONE,'Square column plinths')
    b.lathe((u,.02),[(FIRST+.15,.472),(.999,.486),(1.046,.479),(1.103,.420),(1.14,.416),(1.18,.444),(1.24,.404),(1.27,.370),
                      (2.85,.366),(5.5,.342),(8.17,.296),(8.23,.315),(8.27,.347),(8.34,.354),(8.41,.325)], LIMESTONE,18 if far else 36,'Giant tapered columns')
    cuboid(b,u-.45,u+.45,-.38,.42,8.42,8.55,STONE,'Capital abaci')
    cuboid(b,u-.48,u+.48,-.42,.46,8.55,8.65,STONE,'Capital upper slabs')
    for s in (-1,1):
        x=u+s*.30
        for y in [-.245,.286]:
            pts=[]
            for j in range(20 if far else 40):
                t=j/(19 if far else 39);rad=.111*(1-.74*t);a=pi*.44+tau*1.32*t
                pts.append((x+s*rad*cos(a),y,8.35+rad*sin(a)))
            b.tube(pts,.025,LIMESTONE,5 if far else 8,'Capital volutes')
    b.tube([(u-.30,-.247,8.455),(u+.3,-.247,8.455)],.032,LIMESTONE,8,'Capital moulding')

def axial_bay(b,side,far):
    # The flat central face and both short cants carry windows; adjacent solid strips continue the bay to the wall.
    pts=[(OPEN,0),(OPEN+.44,0),(OPEN+1.17,-.55),(HALF-1.68,-.55),(HALF-.88,0),(HALF,0)]
    if side<0:pts=[(-x,y)for x,y in pts[::-1]]
    for i,(a,z) in enumerate(zip(pts,pts[1:])):
        f=Facade(b,a,z,'Bay '+('W' if side<0 else 'E')+str(i+1))
        slot=i in (1,2,3);half=f.length/2;holes=[]
        if slot:
            width=f.length*(.82 if i==2 else .70)
            for bot,top in [(1.17,3.86),(5.36,8.24)]:holes.append(box(-width/2,bot,width/2,top))
        wall=f.wall(.10,8.65,holes,.285,PLASTER)
        if not slot:rustication(f,wall,.18,8.65,'horizontal joints')
        for opening in holes:glazed(f,opening,shutters=i==2 or f.length>.95,far=far)
        if slot:
            panel=box(-half+.072,4.09,half-.072,5.12)
            f.prism(panel,-.012,.055,PANEL,'recessed spandrel field')
            f.prism(panel.difference(panel.buffer(-.071,join_style=2)),.052,.102,STONE,'spandrel surround')
        f.beam(.22,.24,.095,PANEL,width=f.length,label='plinth')
    outer=Facade(b,(side*HALF,0) if side>0 else (side*HALF,RETURN),(side*HALF,RETURN) if side>0 else (side*HALF,0),'End '+str(side))
    wall=outer.wall(0,8.65,(),.29,PLASTER);rustication(outer,wall,.18,8.65,'short return joints')
    # Stop the two short returns before the east doorway and the unrecorded west side.
    cornice(outer,far)

def attic(b,far):
    # The roof is a partial, visibly stepped strip. The centre recedes behind the two slightly projecting ends.
    spans=[(-HALF,-OPEN,.77),( -OPEN,OPEN,1.53),(OPEN,HALF,.77)]
    for j,(l,r,y) in enumerate(spans):
        f=Facade(b,(l,y),(r,y),'Attic '+str(j+1));n=2 if j==1 else 1;hal=f.length/2
        holes=[]
        for k in range(n):
            c=f.length*((k+.5)/n-.5);wid=2.55 if n==1 else 2.05
            holes.append(box(c-wid/2,9.85,c+wid/2,11.21 if n==1 else 10.66))
        walltop=11.53 if n==1 else 10.77
        f.wall(9.58,walltop,holes,.26,PLASTER)
        for h in holes:glazed(f,h,shutters=True,far=far)
        for z,h,d in [(walltop-.03,.09,.15),(walltop+.07,.11,.2)]:f.beam(z,h,d,SHUTTER,width=f.length+.03,label='tile fascia')
        peak=11.82 if n==1 else 11.05;dx=.13;yb=RETURN
        upper=[(l-dx,y-.22,peak-.12),(r+dx,y-.22,peak-.12),(r+dx,yb,peak+.34*(yb-y)),(l-dx,yb,peak+.34*(yb-y))]
        b.add(upper+[(x,yy,z-.12)for x,yy,z in upper],[(0,1,2,3),(7,6,5,4),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)],OCHRE,'Short front roof slopes')
        if not far:
            for k in range(max(1,int((r-l)/.36))):
                x=l+.16+.36*k
                b.tube([(x,y-.22,peak-.111),(x,yb,peak+.34*(yb-y)+.009)],.016,SHUTTER,5,'Shallow roof tile ribs')
    for x in [-OPEN,OPEN]:
        cuboid(b,x-.1,x+.1,.77,1.53,9.58,11.52,PLASTER,'Attic wall returns')

def stair(b,far):
    count=22 if far else 48
    for j in range(6):
        rx=3.68-j*.30;ry=1.95-j*.221;zc=.14*(j+1)
        edge=[(rx*cos(pi*i/count),-.40-ry*sin(pi*i/count))for i in range(count+1)]
        plan=edge+[(-rx,.10),(rx,.10)]
        horizontal_slab(b,plan,zc-.14,zc-.033,RISER,'Six rounded stone risers')
        outer=[(x*1.009,y-.023)for x,y in edge]+[(-rx*1.009,.10),(rx*1.009,.10)]
        horizontal_slab(b,outer,zc-.038,zc,STONE,'Curved projecting step nosings')

def threshold_finials(b,far):
    # The close photograph shows two pale, small, seated sculptural silhouettes on plinths.
    # Their individual carving is too small to reproduce beyond the visible side and front masses.
    for sign in (-1, 1):
        x=1.37*sign;y=-.43
        cuboid(b,x-.15,x+.15,y-.18,y+.18,.84,.99,RISER,'Paired threshold plinths')
        b.lathe((x,y),[(.986,.103),(1.017,.131),(1.09,.109),(1.155,.14),(1.21,.106),(1.27,.077)],STONE,8 if far else 14,'Small seated stone bodies')
        b.lathe((x,y-.057),[(1.241,.064),(1.29,.121),(1.37,.10),(1.40,.056)],STONE,8 if far else 14,'Carved threshold finials')
        for shift in (-.057,.057):
            b.lathe((x+shift,y-.072),[(1.37,.034),(1.414,.029),(1.438,.008)],STONE,6 if far else 10,'Finial upper corners')

def add_building(b,distant=False):
    axial_bay(b,-1,distant);axial_bay(b,1,distant)
    back=Facade(b,(-OPEN,BACK),(OPEN,BACK),'Inner porch')
    openings=[]
    for x in [-3.35,0,3.35]:
        half=1.59 if x==0 else .83
        openings.extend([box(x-half,FIRST,x+half,3.94),box(x-half,5.27,x+half,8.20)])
    back.wall(0,8.68,openings,.33,PLASTER)
    for k,opening in enumerate(openings):
        glazed(back,opening,door=k%2==0,shutters=k%2==1,far=distant)
    for s in (-1,1):
        x=s*OPEN;f=Facade(b,(x,BACK)if s>0 else (x,0),(x,0) if s>0 else (x,BACK),'Porch return '+str(s))
        f.wall(FIRST,8.65,(),.20,PLASTER)
        col(b,s*COLUMN,distant)
    cuboid(b,-OPEN,OPEN,-.045,BACK,.03,FIRST,RISER,'Porch floor and plinth')
    cuboid(b,-OPEN,OPEN,.24,BACK,BALCONY-.21,BALCONY,STONE,'Upper balcony floor')
    cuboid(b,-OPEN,OPEN,.16,.53,BALCONY-.33,BALCONY-.17,PANEL,'Balcony fascia')
    cuboid(b,-OPEN,OPEN,.19,.48,BALCONY,BALCONY+.17,STONE,'Balustrade bottom rail')
    cuboid(b,-OPEN,OPEN,.13,.53,BALCONY+.94,BALCONY+1.04,STONE,'Balustrade handrail')
    for i in range(31):
        x=(i+.5)*2*OPEN/31-OPEN
        profile=[(.15,.096),(.22,.089),(.27,.070),(.32,.052),(.43,.050),(.57,.082),(.64,.093),(.72,.076),(.80,.045),(.88,.06),(.95,.077)]
        if distant:profile=[profile[k]for k in (0,2,4,6,8,10)]
        b.lathe((x,.34),[(BALCONY+z,r)for z,r in profile],STONE,8 if distant else 14,'Turned balcony balusters')
    cuboid(b,-HALF,HALF,-.12,RETURN,8.65,8.75,PLASTER,'Portico ceiling')
    cornice(Facade(b,(-HALF,-.03),(HALF,-.03),'South'),distant)
    cuboid(b,-HALF,HALF,-.03,RETURN,9.54,9.60,PANEL,'Cornice and attic ledge')
    stair(b,distant);threshold_finials(b,distant);attic(b,distant)
