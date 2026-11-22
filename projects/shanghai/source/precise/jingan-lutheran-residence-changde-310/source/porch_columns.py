"""Stone entrance, curved parapet and ceramic pavement at Changde Road 310.

The local datum is the nearest upper corner of the impost in reference 13.
X runs along the abacus, Y runs into the vestibule and Z is vertical.
"""
import math
import numpy as np
from shapely.geometry import Polygon, box
from shapely.ops import unary_union
from pathlib import Path

PREFIX='Entrance porch | '
GRANITE=PREFIX+'grey granite'
CUT=PREFIX+'cut granite moulding'
RELIEF=PREFIX+'carved stone'
COPING=PREFIX+'weathered stone coping'
ASH=PREFIX+'grey face brick'
RUSSET=PREFIX+'russet face brick'
MORTAR=PREFIX+'mortar'
TERRA=PREFIX+'moulded terracotta'
ARCH_BRICK=[PREFIX+'red arch brick '+str(n) for n in range(1,5)]
GROUT=PREFIX+'ceramic grout'
CREAM=PREFIX+'buff tile'
OCHRE=PREFIX+'ochre tile'
GREEN=PREFIX+'green tile'
BROWN=PREFIX+'brown tile'
DARK=PREFIX+'chocolate tile'
TIMBER=PREFIX+'stained timber'
PANEL=PREFIX+'raised timber field'
BEAD=PREFIX+'door moulding'
GLASS=PREFIX+'dark vestibule glazing'
HARDWARE=PREFIX+'aged brass hardware'
FLAGS=[PREFIX+'red-brown flagstone '+str(i) for i in range(1,4)]
FLOOR=-2.29
CENTER=(-.345,.354)

def pigment(rgb,rough):
    values=[c/255 for c in rgb]
    return {'color':[v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in values],'roughness':rough,'metallic':0}

PALETTE={name:pigment(color,r) for name,color,r in [
    (GRANITE,(150,154,151),.83),(CUT,(158,162,158),.77),(RELIEF,(148,150,142),.83),
    (COPING,(168,155,129),.95),(ASH,(107,105,102),.93),(RUSSET,(162,93,76),.92),
    (MORTAR,(167,149,133),.96),(TERRA,(183,109,82),.90),
    *[(n,rgb,.93) for n,rgb in zip(ARCH_BRICK,[(160,88,69),(171,101,80),(145,81,67),(169,94,71)])],
    (GROUT,(130,105,83),.87),(CREAM,(211,184,141),.75),(OCHRE,(195,141,75),.81),
    (GREEN,(83,100,67),.78),(BROWN,(146,95,73),.78),(DARK,(112,72,57),.80),
    (TIMBER,(108,55,39),.69),(PANEL,(129,66,45),.64),(BEAD,(139,77,55),.70),(GLASS,(49,43,38),.39),(HARDWARE,(130,106,66),.54),*[(n,c,.94) for n,c in zip(FLAGS,[(151,125,111),(162,138,119),(158,130,112)])]]}

for stone,factor in [(GRANITE,.985),(CUT,1.),(RELIEF,.940)]:
    PALETTE[stone].update(color=[min(1.,factor**2.2)]*3,texture=str(Path(__file__).with_name('changde-porch-granite.png')))

def mineral_uvs(part):
    # Switch planar projection where a turn in the stone profile would flatten
    # its UV coordinates. Shared positions stay equal across those UV seams.
    source=np.asarray(part['vertices']);lookup={};points=[];uvs=[];faces=[]
    for tri in part['triangles']:
        a,b,c=source[list(tri)];axis=int(np.argmax(np.abs(np.cross(b-a,c-a))))
        projection=((1,2),(0,2),(0,1))[axis];ids=[]
        for i in tri:
            key=(i,axis)
            if key not in lookup:
                lookup[key]=len(points);points.append(tuple(source[i]));uvs.append(tuple(source[i,list(projection)]/.286))
            ids.append(lookup[key])
        faces.append(tuple(ids))
    part.update(vertices=points,triangles=faces,texcoords=uvs)

def front(b,poly,y0,y1,mat,name):
    if not poly.is_empty and poly.area>1.e-9:
        b.prism(poly,-y1,-y0,lambda x,z,d:(x,-d,z),mat,PREFIX+name)

def side(b,poly,x0,x1,mat,name):
    if not poly.is_empty and poly.area>1.e-9:
        b.prism(poly,x0,x1,lambda y,z,d:(d,y,z),mat,PREFIX+name)

def ring_stack(b,c,profile,n,mat,label,square=False):
    # Profile entries progress up from the base, in (height,radius) order.
    pts=[];faces=[]
    for z,r in profile:
        if square: section=[(-r,-r),(r,-r),(r,r),(-r,r)]
        else: section=[(r*math.cos(math.tau*i/n),r*math.sin(math.tau*i/n)) for i in range(n)]
        pts.extend((c[0]+x,c[1]+y,z) for x,y in section)
    for k in range(len(profile)-1):
        for i in range(n):
            j=(i+1)%n;faces.append((k*n+i,k*n+j,(k+1)*n+j,(k+1)*n+i))
    faces.extend([tuple(reversed(range(n))),tuple(range(len(pts)-n,len(pts)))])
    b.add(pts,faces,mat,PREFIX+label)

def side_relief(b,poly,face,depth,thickness,mat,name):
    cx,cy=CENTER
    if face=='front':front(b,poly,cy-depth-thickness,cy-depth,mat,name)
    else:side(b,poly,cx+depth,cx+depth+thickness,mat,name)

def volutepath(size,hand,center,z,lod):
    angles=np.linspace(0,math.tau*1.14,16 if lod else 35)
    rr=np.linspace(size,.004,len(angles))
    path=np.c_[center+hand*rr*np.cos(angles+.92),z+rr*np.sin(angles+.92)]
    tang=np.gradient(path,axis=0);norm=np.c_[-tang[:,1],tang[:,0]]
    norm/=np.linalg.norm(norm,axis=1)[:,None]
    wid=np.linspace(.014,.004,len(path))[:,None]
    return Polygon([*(path+wid*norm),*(path-wid*norm)[::-1]])

def capital(b,lod):
    c=CENTER;n=24 if lod else 48
    ring_stack(b,c,[(FLOOR,.344),(-2.039,.342),(-2.008,.335),(-1.974,.312),(-1.955,.312),
        (-1.941,.321),(-1.922,.329),(-1.902,.327),(-1.878,.314),(-1.861,.285),
        (-1.844,.292),(-1.829,.298),(-1.810,.272),(-1.780,.252)],n,GRANITE,'turned drum and two base rolls')
    ring_stack(b,c,[(-1.781,.252),(-1.51,.250),(-1.15,.245),(-.765,.2355),(-.509,.234),
                    (-.471,.244),(-.452,.259),(-.436,.273),(-.418,.274),(-.412,.245)],n,CUT,'shaft, neck and annular collar')
    ring_stack(b,c,[(-.413,.242),(-.387,.239),(-.353,.247),(-.315,.261),(-.288,.274),(-.270,.271)],n,RELIEF,'capital bell')
    ring_stack(b,c,[(-.300,.215),(-.263,.248),(-.224,.261),(-.196,.255)],4,RELIEF,'block under the abacus',True)
    mould=[(-.207,.249),(-.196,.256),(-.182,.254),(-.173,.263),(-.163,.262),(-.153,.253),
           (-.146,.251),(-.134,.258),(-.125,.274),(-.119,.278),(-.111,.274),
           (-.104,.274),(-.096,.285),(-.087,.290),(-.080,.289),(-.069,.298),
           (-.064,.310),(-.053,.313),(-.049,.345),(-.003,.349),(.001,.347)]
    ring_stack(b,c,mould,4,CUT,'stepped square granite abacus',True)
    for face,origin in [('front',c[0]),('right',c[1])]:
        for j,(shift,hand,size) in enumerate([(-.220,1,.047),(-.064,-1,.032),(.036,1,.044),(.215,-1,.046)]):
            scroll=volutepath(size,hand,origin+shift,-.258,lod)
            side_relief(b,scroll,face,.254,.027,RELIEF,'paired volutes on '+face+' face')
        for shift in (-.146,.129):
            u=origin+shift
            leaf=Polygon([(u-.054,-.228),(u-.032,-.235),(u-.009,-.250),(u,-.238),(u+.012,-.250),
                          (u+.034,-.235),(u+.051,-.230),(u+.035,-.274),(u+.008,-.305),(u,-.315),
                          (u-.014,-.292),(u-.036,-.282)])
            side_relief(b,leaf,face,.246,.032,RELIEF,'hanging leaves on '+face+' face')
    # Scalloped foliage follows the rounded bell below the square scroll frieze.
    for angle in np.linspace(-math.pi*.91,math.pi*.23,8):
        t=np.array([-math.sin(angle),math.cos(angle)]);normal=np.array([math.cos(angle),math.sin(angle)])
        poly=Polygon([(-.047,-.316),(-.019,-.332),(0.,-.35),(.025,-.323),(.048,-.315),
                      (.034,-.366),(.020,-.388),(0.,-.403),(-.024,-.381),(-.038,-.35)])
        def mapper(u,z,d):
            xy=np.array(c)+t*u+normal*(.245+d);return xy[0],xy[1],z
        b.prism(poly,0,.023,mapper,RELIEF,PREFIX+'acanthus on the capital bell')
    # The opposite-cap close-up exposes the incised curls below the projecting
    # volutes. Shallow rounded ridges turn around the circular bell.
    for theta in np.linspace(-math.pi,math.pi,10,endpoint=False):
        path=[]
        for t in np.linspace(0,math.tau*.94,11 if lod else 21):
            r=.044-(.038*t/(math.tau*.94))
            off=r*math.cos(t+.35)
            ang=theta+off/.25
            z=-.353+r*math.sin(t+.35)
            radius=.247+.015*(z+.410)/.10+.007
            path.append((c[0]+radius*math.cos(ang),c[1]+radius*math.sin(ang),z))
        b.tube(path,.0065,RELIEF,5 if lod else 8,PREFIX+'scroll carving on the rounded bell')
    # The smaller post meets the coping. Two unaligned cameras resolve its
    # elliptical limbs, which broaden asymmetrically beneath the stone frieze.
    # Foliage screens the bottom in both images.
    sections=[(-.644,.159,.095,.168,FLOOR),(-.644,.159,.095,.168,-1.219),
              (-.644,.158,.095,.167,-1.085),(-.642,.161,.095,.166,-.931),
              (-.636,.156,.090,.165,-.777),(-.626,.175,.079,.142,-.648),
              (-.613,.182,.065,.124,-.518),(-.596,.141,.061,.096,-.432),
              (-.596,.141,.061,.096,-.408),(-.600,.145,.050,.073,-.398),
              (-.600,.145,.050,.073,-.297)]
    count=20 if lod else 40
    verts=[];faces=[]
    for x,y,rx,ry,z in sections:
        for j in range(count):
            phi=math.tau*j/count
            verts.append((x+rx*math.cos(phi),y+ry*math.sin(phi),z))
    for k in range(len(sections)-1):
        for j in range(count):
            e=(j+1)%count;faces.append((k*count+j,k*count+e,(k+1)*count+e,(k+1)*count+j))
    faces.extend([tuple(reversed(range(count))),tuple(range(len(verts)-count,len(verts)))])
    b.add(verts,faces,GRANITE,PREFIX+'secondary post at parapet head')

# The photograph shows two reversals in the stone coping. These Y/Z controls
# are a perspective section of its camera-facing edge.
PARAPET=[(-1.84,-1.85),(-1.67,-1.82),(-1.45,-1.77),(-1.32,-1.73),(-1.21,-1.62),(-1.088,-1.455),(-1.002,-1.354),(-.952,-1.277),
         (-.882,-1.147),(-.837,-1.051),(-.778,-.969),(-.714,-.928),(-.605,-.907),
         (-.449,-.878),(-.330,-.846),(-.251,-.783),(-.152,-.650),(-.035,-.517),
         (.067,-.486),(.166,-.478)]
def parapet(b,lod):
    stops=np.array(PARAPET);ys=stops[:,0];zs=stops[:,1]
    if not lod:
        from scipy.interpolate import PchipInterpolator
        ys=np.linspace(ys[0],ys[-1],65);zs=PchipInterpolator(stops[:,0],stops[:,1])(ys)
    wall=Polygon([(ys[0],FLOOR),(ys[-1],FLOOR),*list(zip(ys,zs-.096))[::-1]])
    side(b,wall,-1.05,-.665,MORTAR,'solid ramped brick parapet')
    coping=Polygon([*zip(ys,zs),*list(zip(ys,zs-.096))[::-1]])
    side(b,coping,-1.069,-.649,COPING,'curved stone coping')
    # Bond and the two red-brick courses are visible on the near side.
    for k,z in enumerate(np.arange(-2.266,-.35,.065)):
        for j,y in enumerate(np.arange(-2.0+(k%2)*.116,.35,.232)):
            brick=wall.intersection(box(y+.004,z+.003,y+.228,z+.062))
            side(b,brick,-.667,-.659,RUSSET if -1.216>=z>=-1.350 else ASH,'parapet face brick')

def pavement(b,lod):
    # The border corners and street/door seams come from the two photographed
    # floor planes. The field is slightly skewed in the abacus coordinate frame.
    start=len(b.parts)
    left,right=.366,2.678
    extent=box(-.83,-.262,3.75,1.597)
    def place(poly,mat,level,name):
        clipped=poly.intersection(extent)
        if not clipped.is_empty and clipped.area>1.e-8:
            b.plan_prism(clipped,FLOOR-.010+level,FLOOR+level,mat,PREFIX+name)
    b.plan_prism(extent,FLOOR-.075,FLOOR,GROUT,PREFIX+'entrance tile bed')
    corners=[box(-3.,-3.,left,.997),box(right,-3.,6.,.970)]
    field=extent.difference(corners[0]).difference(corners[1]).intersection(box(-1.,-.216,4.,1.387))
    def diamond(x,y,r):
        return Polygon([(x-r,y),(x,y-r),(x+r,y),(x,y+r)])
    for row in range(-4,2):
        for col in range(-2,10):
            x=.226+.486*col;y=1.181+.466*row
            small=unary_union([diamond(x+dx,y+dy,.087) for dx,dy in [
                (.243,0),(-.243,0),(0,.233),(0,-.233),(.486,.233),(.243,.466)]])
            # Cut the small buff inserts out of their neighbouring tiles so
            # the ceramic faces meet at a seam without overlapping.
            place(diamond(x,y,.239).difference(small).intersection(field),BROWN,.001,'diagonal pavement field')
            place(diamond(x+.243,y+.233,.194).difference(small).intersection(field),CREAM,.001,'diagonal pavement field')
            for dx,dy in [(.243,0),(0,.233)]:
                place(diamond(x+dx,y+dy,.087).intersection(field),CREAM,.001,'small buff tile')
            for r,mat,k in [(.149,GREEN,.002),(.098,CREAM,.003),(.080,OCHRE,.004)]:
                place(diamond(x,y,r).intersection(field),mat,k,'green and gold floral medallion')
            if not lod:
                for dx,dy in [(0.,-.038),(.038,0.),(0.,.038),(-.038,0.),(0.,0.)]:
                    place(diamond(x+dx,y+dy,.022).intersection(field),BROWN,.005,'floral medallion centre')
    offsets=[(0,.014,CREAM),(.014,.023,OCHRE),(.023,.033,CREAM),(.033,.040,DARK),
             (.040,.057,CREAM),(.057,.083,GREEN),(.083,.097,CREAM),(.097,.153,OCHRE),
             (.153,.168,CREAM),(.168,.190,GREEN),(.190,.208,CREAM)]
    def inset(index,d):
        if index==0:return box(-3.,-3.,left-d,.997-d)
        return box(right+d,-3.,6.,.970-d)
    for side in [0,1]:
        place(inset(side,.208),DARK,.001,'pavement inside turning border')
        for a,e,mat in offsets:
            place(inset(side,a).difference(inset(side,e)),mat,.002,'mitred border around the column')
    for a,e,mat in offsets:
        place(box(-1.,1.387+a,3.8,1.387+e),mat,.002,'straight band at the door')
    for a,e,mat in [(0,.014,OCHRE),(.014,.024,BROWN),(.024,.046,CREAM)]:
        place(box(-1.,-.262+a,3.8,-.262+e),mat,.002,'border at street seam')
    if not lod:
        def floret(u,v):
            return Polygon([(u+dx,v+dy) for dx,dy in [(-.016,0),(-.006,-.014),(.008,-.013),
                                                      (.017,0),(.004,.014),(-.008,.012)]])
        for u in np.arange(-.83,3.75,.050):
            place(floret(u,1.512),BROWN,.0035,'ochre border repeat')
            for outer,y in [(u<left-.125,.872),(u>right+.125,.845)]:
                if outer:place(floret(u,y),BROWN,.0035,'mitred border repeat')
        for v in np.arange(-.204,.844,.050):
            for u in [left-.125,right+.125]:place(floret(u,v),BROWN,.0035,'mitred border repeat')
    for part in b.parts[start:]:
        part['vertices']=[(x,y-.028*x,z) for x,y,z in part['vertices']]
    # Square paving starts at the outer seam and stops at the single broad
    # granite nosing recorded between the terminal piers.
    deck=Polygon([(-.83,-2.293),(3.75,-2.423),(3.75,-.262-.028*3.75),(-.83,-.262+.028*.83)])
    b.plan_prism(deck,FLOOR-.14,FLOOR-.008,GROUT,PREFIX+'forecourt paving bed')
    for i,x in enumerate(np.arange(-1.,3.8,.40)):
        for j,y in enumerate(np.arange(-2.50,-.23,.36)):
            tile=box(x+.003,y+.003,x+.397,y+.357).intersection(deck)
            if not tile.is_empty and tile.area>.0002:
                b.plan_prism(tile,FLOOR-.010,FLOOR-.002,FLAGS[(i+2*j+i*j)%3],PREFIX+'square paving on the approach')
    nose=Polygon([(-1.05,-2.59),(3.95,-2.73),(3.95,-2.42),(-1.05,-2.28)])
    b.plan_prism(nose,FLOOR-.17,FLOOR-.008,COPING,PREFIX+'granite entrance tread')

def arch(b,lod):
    # The rear edge is the colour transition at 120 measured sections in the
    # front photograph. The oblique photograph provides a separate front arris.
    cx,rx,rz,base=1.4925,1.6034,.9752,.0175
    def curve(r,t):
        c=np.cos(t);s=np.sin(t);n=np.hypot(rz*c,rx*s)
        return np.stack((cx+rx*c+r*rz*c/n,base+rz*s+r*rx*s/n),axis=-1)
    def strip(a,e,lo,hi,n):
        t=np.linspace(lo,hi,n+1);return Polygon([*curve(e,t),*curve(a,t)[::-1]])
    front(b,strip(0.,.497,0.,math.pi,66 if lod else 112),.228,.725,MORTAR,'elliptical arch and deep soffit')
    bands=[(0,.147,.211),(.147,.158,.154),(.158,.180,.144),(.180,.222,.158),
           (.222,.265,.161),(.265,.313,.089),(.313,.376,.088),(.376,.437,.066),(.437,.496,.049)]
    for band,(a,e,y) in enumerate(bands):
        n=33 if lod else round((3.96+math.pi*(a+e)/2)/(.129 if band<4 else .073))
        for j in range(n):
            t0=math.pi*j/n;t1=math.pi*(j+1)/n
            q=(t0+t1)/2;speed=math.hypot(rx*math.sin(q),rz*math.cos(q))+(a+e)/2
            gap=.0028/speed
            mat=TERRA if band in (0,1,3) else ARCH_BRICK[(band*3+j+j//6)%len(ARCH_BRICK)]
            front(b,strip(a,e,t0+gap,t1-gap,3 if lod else 5),y,.231,mat,'stepped red archivolt courses')
    # The returned brick soffit has short regular transverse joints. Each block
    # also has a slight radial depth so its red intrados reads inside the opening.
    n=36 if lod else 63
    for j in range(n):
        for k in range(2 if lod else 5):
            step=.515/(2 if lod else 5);y=.209+k*step;t0=math.pi*j/n;t1=math.pi*(j+1)/n
            front(b,strip(-.008,.011,t0+.0018,t1-.0018,3),y+.002,y+step-.002,
                  ARCH_BRICK[(j+k)%4],'radial joints in the curved soffit')
    # Relieved palmettes, each with two curving lobes, follow the tangent.
    n=31 if lod else 43
    for j in range(n):
        t=(j+.5)*math.pi/n
        if abs(t-math.pi/2)<.114:continue
        tangent=np.array([-rx*math.sin(t),rz*math.cos(t)]);tangent/=np.linalg.norm(tangent)
        normal=np.array([tangent[1],-tangent[0]]);root=curve(.012,t)
        for hand in [-1,1]:
            leaf=[(-.036,0),(-.029,.037),(-.026,.063),(-.017,.080),(-.003,.096),
                  (.003,.089),(-.002,.070),(.009,.083),(.015,.075),(.012,.054),
                  (.030,.079),(.039,.066),(.032,.041),(.011,.014),(-.011,.002)]
            uv=np.array([root+tangent*(hand*(u+.016))+normal*v for u,v in leaf])
            front(b,Polygon(uv),.187,.212,TERRA,'paired leaves on the terracotta archivolt')
            if not lod:
                line=[root+tangent*(hand*u)+normal*v for u,v in [(-.011,.006),(0,.033),(.010,.052),(.029,.075)]]
                b.tube([(x,.185,z) for x,z in line],.005,TERRA,6,PREFIX+'relief veins')
    keystone(b,lod)

def keystone(b,lod):
    # A projecting tapered block encloses two separate diamond rosettes in the
    # 3000 px close-up. Mouldings and flowers are original geometry.
    xc=1.475
    def trap(bottom,top,h0,h1):
        return Polygon([(xc-bottom,h0),(xc+bottom,h0),(xc+top,h1),(xc-top,h1)])
    outer=trap(.174,.201,.943,1.545)
    front(b,outer,-.014,.268,RUSSET,'tapered central keystone')
    front(b,trap(.211,.233,1.528,1.577),-.044,.252,TERRA,'keystone capital neck')
    front(b,trap(.228,.250,1.567,1.608),-.053,.260,TERRA,'keystone cap')
    frame=trap(.132,.151,1.015,1.484)
    inside=trap(.104,.119,1.038,1.458)
    front(b,frame.difference(inside),-.042,-.013,TERRA,'raised keystone panel surround')
    for z,r in [(1.340,.100),(1.133,.080)]:
        diamond=Polygon([(xc,z+r),(xc+r,z),(xc,z-r),(xc-r,z)])
        void=Polygon([(xc,z+r-.014),(xc+r-.014,z),(xc,z-r+.014),(xc-r+.014,z)])
        front(b,diamond.difference(void),-.046,-.013,TERRA,'diamond frame around the keystone rosette')
        for j in range(6 if lod else 8):
            rad=np.array([math.cos(j*math.tau/(6 if lod else 8)),math.sin(j*math.tau/(6 if lod else 8))])
            tang=np.array([-rad[1],rad[0]]);o=np.array([xc,z]);rr=r*.63
            leaf=Polygon([o+rad*rr*k+tang*rr*t for k,t in [(0.,0.),(.45,-.20),(.80,-.17),(1.,0),(.77,.18),(.42,.21)]])
            front(b,leaf,-.050,-.014,TERRA,'flower petals on the keystone')
        ring_stack(b,(xc,-.052),[(z-.007,.010),(z+.007,.010)],8,TERRA,'central floral boss')
    for x in [xc-.094,xc+.094]:
        for z,sgn in [(1.448,1),(1.045,-1)]:
            poly=Polygon([(x-.017,z),(x+.017,z),(x+.010,z-.022*sgn),(x,z-.038*sgn),(x-.012,z-.024*sgn)])
            front(b,poly,-.039,-.015,TERRA,'corner leaves on the keystone panel')

def screen(b,lod):
    # Original near-frontal image 3 shows a solid four-panel door flanked by
    # two lower panelled screens with offset rectangular glazing bars above.
    # The narrow top remains in shade in both recorded exposures.
    y=1.84;bottom=FLOOR+.006;top=1.78;portal=(.646,2.385)
    def panel(x0,x1,z0,z1,y0,y1,mat,name):
        b.box(((x0+x1)/2,(y0+y1)/2,(z0+z1)/2),(x1-x0,y1-y0,z1-z0),mat,label=PREFIX+name)
    def raised(x0,x1,z0,z1):
        back=[(x0,z0),(x1,z0),(x1,z1),(x0,z1)]
        frontface=[(x0+.040,z0+.043),(x1-.040,z0+.043),(x1-.040,z1-.043),(x0+.040,z1-.043)]
        vertices=[(x,y-.012,z) for x,z in back]+[(x,y-.038,z) for x,z in frontface]
        faces=[(3,2,1,0),(4,5,6,7)]+[(i,(i+1)%4,4+(i+1)%4,4+i) for i in range(4)]
        b.add(vertices,faces,PANEL,PREFIX+'bevelled timber panel')
        outer=box(x0-.012,z0-.012,x1+.012,z1+.012);hole=box(x0+.008,z0+.008,x1-.008,z1-.008)
        front(b,outer.difference(hole),y-.044,y-.017,BEAD,'door panel moulding')
    panel(-1.35,4.14,FLOOR-.055,top,y+.025,y+.075,GLASS,'shaded head behind the brick arch')
    # The deep side shadow and the continuous door sill are visible beyond the
    # coloured border. These returns join the exterior door screen to its jambs.
    panel(-.97,3.93,FLOOR-.070,FLOOR+.003,1.458,y+.087,DARK,'deep sill behind the mosaic')
    for x in [-.800,3.76]:
        panel(x-.026,x+.026,FLOOR-.01,.44,.647,y+.035,TIMBER,'painted jamb return')
    panel(*portal,bottom,.405,y,y+.040,TIMBER,'four-panel entrance door')
    for u in [portal[0]-.043,portal[1]+.043]:
        panel(u-.036,u+.036,bottom,.44,y-.026,y+.043,TIMBER,'door jamb')
    for z in [.370,.449]:
        panel(portal[0]-.078,portal[1]+.078,z-.030,z+.030,y-.029,y+.027,TIMBER,'door head')
    for x0,x1 in [(.778,1.401),(1.590,2.247)]:
        for z0,z1 in [(bottom+.144,-1.28),(-1.074,-.043)]:raised(x0,x1,z0,z1)
    # Only the small brass letter slot and handle are reproduced from the door.
    panel(1.397,1.604,-1.193,-1.167,y-.052,y-.018,HARDWARE,'brass letter slot')
    panel(.768,.793,-1.213,-1.067,y-.055,y-.015,HARDWARE,'entrance door handle')
    for x0,x1 in [(-.68,.595),(2.436,3.68)]:
        rail=-1.141
        panel(x0,x1,bottom,rail+.041,y,y+.037,TIMBER,'lower panelled sidelight screen')
        panel(x0,x1,rail-.020,rail+.066,y-.031,y+.015,TIMBER,'sidelight crossrail')
        for i in range(2):
            l=x0+.063+(x1-x0-.112)*i/2;r=x0+.063+(x1-x0-.112)*(i+1)/2
            raised(l+.033,r-.032,bottom+.160,rail-.096)
        # The three horizontal bands each have a different arrangement of
        # short vertical pieces. They form the irregular rectangular lattice.
        zs=[rail+.061,-.91,-.68,-.34,-.04,.19,.38,.66]
        for z in zs:
            panel(x0,x1,z-.015,z+.015,y-.013,y+.025,TIMBER,'glazed sidelight crossbars')
        for j,(z0,z1) in enumerate(zip(zs,zs[1:])):
            fractions=[0,.13,.38,.63,.87,1.] if j%3==0 else [0,.24,.48,.75,1.] if j%3==1 else [0,.12,.23,.50,.75,.86,1.]
            for f in fractions:
                x=x0+(x1-x0)*f
                panel(x-.014,x+.014,z0+.011,z1-.011,y-.013,y+.024,TIMBER,'staggered sidelight uprights')

def add_porch(builder,lod,anchor=(0.,0.,0.),yaw=0.):
    """Place the local abacus datum at anchor using a Z-axis rotation in degrees."""
    start=len(builder.parts)
    capital(builder,lod);parapet(builder,lod)
    # Both fully photographed supports have a carved capital and a smaller
    # post joining the curved parapet. Only the two documented faces have relief.
    left=builder.parts[start:]
    for original in left:
        mirrored=dict(original)
        mirrored['vertices']=[(2*1.473-x,y,z) for x,y,z in original['vertices']]
        mirrored['triangles']=[(k,j,i) for i,j,k in original['triangles']]
        mirrored['label']=original['label']+' | opposite side'
        builder.parts.append(mirrored)
    from porch_end_piers import add_piers
    add_piers(builder,lod)
    pavement(builder,lod);arch(builder,lod);screen(builder,lod)
    angle=math.radians(yaw);a=math.cos(angle);s=math.sin(angle);x0,y0,z0=anchor
    for part in builder.parts[start:]:
        if part['material'] in (GRANITE,CUT,RELIEF):mineral_uvs(part)
        part['vertices']=[(x0+a*x-s*y,y0+s*x+a*y,z0+z) for x,y,z in part['vertices']]
