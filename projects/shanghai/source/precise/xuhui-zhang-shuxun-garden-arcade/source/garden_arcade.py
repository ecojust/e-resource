"""Three semicircular fanlights and the carved capitals on the garden face of Zhang Shuxun's house."""
from math import cos, pi, sin
from shapely.geometry import Polygon, box
from shapely.ops import unary_union

WALL='apricot stucco'
STONE='ivory cast stone'
EDGE='sunlit limestone bead'
SHADOW='recessed ochre stone'
METAL='painted glazing bars'
GLASS=('garden glass in shade','slate reflected glass','blue garden reflection')
PALETTE={
    WALL:{'color':[.74,.565,.471],'roughness':.92},
    STONE:{'color':[.792,.734,.609],'roughness':.86},
    EDGE:{'color':[.856,.799,.695],'roughness':.81},
    SHADOW:{'color':[.55,.495,.40],'roughness':.93},
    METAL:{'color':[.080,.083,.074],'metallic':.48,'roughness':.47},
    GLASS[0]:{'color':[.076,.094,.102],'metallic':.22,'roughness':.24},
    GLASS[1]:{'color':[.121,.150,.16],'metallic':.22,'roughness':.26},
    GLASS[2]:{'color':[.136,.17,.18],'metallic':.21,'roughness':.26},
    'oxidized metal kick panel':{'color':[.162,.119,.101],'metallic':.39,'roughness':.67},
    'terracotta threshold':{'color':[.320,.183,.132],'roughness':.84},
}
# Frame at 1.80 s, after cropping x=60,y=820. Axes x=161,370,569;
# clear central span=151 px at the spring, rise=76; common footprint depth is estimated.
R=.78
BAY=2.07
SPRING=2.54
CENTRES=(-BAY,0,BAY)

def front(b,poly,y0,y1,mat,label):
    if not poly.is_empty:
        b.prism(poly,-y1,-y0,lambda x,z,d:(x,-d,z),mat,label)

def cuboid(b,cx,cy,cz,w,d,h,mat,label):
    b.box((cx,cy,cz),(w,d,h),mat,label=label)

def sector(x,z,r,start,end,divisions):
    return [(x+r*cos(start+(end-start)*i/divisions),z+r*sin(start+(end-start)*i/divisions)) for i in range(divisions+1)]

def half_disk(x,z,r,n):
    return Polygon(sector(x,z,r,0,pi,n))

def arch_strip(x,z,r,thickness,n):
    return Polygon(sector(x,z,r+thickness,0,pi,n)+sector(x,z,r,pi,0,n))

def tube_ring(b,x,z,r,y,radius,material,label,n,lod):
    path=[(a,y,h)for a,h in sector(x,z,r,0,pi,n)]
    b.tube(path,radius,material,sides=6 if lod else 10,label=label)

def lathe(b,x,profile,n,material,label):
    # The column is attached to the wall; the rounded shaft projects toward the garden.
    y=.019
    verts=[(x+r*cos(2*pi*i/n),y+r*sin(2*pi*i/n),z) for z,r in profile for i in range(n)]
    faces=[]
    for j in range(len(profile)-1):
        for i in range(n):
            k=(i+1)%n;a=j*n+i;c=j*n+k
            faces.extend(((a,c,c+n),(a,c+n,a+n)))
    for i in range(1,n-1):
        faces.extend(((0,i+1,i),((len(profile)-1)*n,(len(profile)-1)*n+i,(len(profile)-1)*n+i+1)))
    b.add(verts,faces,material,label)

def leaf(b,x,angle,z,r,h,width,name):
    # Three-dimensional lanceolate leaf with an undulating tip and raised midrib.
    def p(u,v,t):
        return (x+(r+t)*cos(angle)-u*sin(angle),.019+(r+t)*sin(angle)+u*cos(angle),z+v)
    v=[p(0,0,.006),p(-width*.54,h*.28,.015),p(-width*.48,h*.61,.028),
       p(-width*.13,h*.89,.044),p(0,h,.052),p(width*.18,h*.85,.043),
       p(width*.54,h*.57,.026),p(width*.48,h*.26,.014),p(0,h*.49,.063)]
    b.add(v,[(i,(i+1)%8,8)for i in range(8)],EDGE,name)

def carved_column(b,x,side,lod):
    prefix=side+' capital'
    cuboid(b,x,.025,.043,.485,.432,.086,SHADOW,side+' square plinth')
    cuboid(b,x,.025,.103,.443,.405,.039,STONE,side+' upper plinth')
    lathe(b,x,[(.122,.194),(.139,.209),(.169,.218),(.189,.217),(.213,.185),(.231,.176)],16 if lod else 32,STONE,side+' round base')
    lathe(b,x,[(.231,.173),(.55,.165),(1.27,.160),(1.96,.155),(2.005,.150)],16 if lod else 32,STONE,side+' unfluted shaft')
    lathe(b,x,[(2.005,.15),(2.033,.16),(2.043,.179),(2.072,.181),(2.087,.157),
               (2.105,.155),(2.144,.167),(2.185,.188),(2.255,.211),(2.31,.229),(2.346,.231)],
          16 if lod else 32,STONE,prefix+' neck and bell')
    for j in range(10):
        angle=2*pi*j/10+pi/10
        leaf(b,x,angle,2.105,.152,.140,.065,prefix+' lower leaves')
        leaf(b,x,angle+pi/10,2.186,.177,.147,.075,prefix+' upper leaves')
    for sign in (-1,1):
        # Volutes appear at both sides of the photographed capital under a square abacus.
        cx=x+sign*.146;cz=2.308
        path=[];n=13 if lod else 25
        for j in range(n):
            t=j/(n-1);a=(.1+1.53*t)*pi;r=.063*(1-.76*t)
            path.append((cx+sign*r*cos(a),-.160-.025*t,cz+r*sin(a)))
        b.tube(path,.017,EDGE,5 if lod else 8,prefix+' paired volutes')
    cuboid(b,x,-.004,2.370,.518,.478,.048,STONE,prefix+' square abacus')
    cuboid(b,x,-.009,2.417,.555,.520,.049,EDGE,prefix+' projecting slab')
    cuboid(b,x,.003,2.474,.505,.451,.063,STONE,prefix+' impost')

def sash(b,cx,lod,index):
    label=('Left','Middle','Right')[index]
    n=24 if lod else 50
    clear=.740;z0=.055;z1=SPRING-.048
    perimeter=box(cx-R,z0,cx+R,SPRING).difference(box(cx-clear,z0+.034,cx+clear,z1))
    front(b,perimeter,.098,.168,METAL,label+' steel perimeter')
    cuboid(b,cx,.111,.141,2*clear,.046,.146,'oxidized metal kick panel',label+' solid lower kick panel')
    bottom=.218
    for i in range(4):
        l=cx-clear+2*clear*i/4;right=cx-clear+2*clear*(i+1)/4
        for j in range(5):
            lo=bottom+(z1-bottom)*j/5;hi=bottom+(z1-bottom)*(j+1)/5
            tint=GLASS[(1 if i==3 else 0)+int(i==3 and j>=3)]
            front(b,box(l,lo,right,hi),.165,.173,tint,label+' rectangular glass')
    for i in (1,2,3):
        xpos=cx-clear+2*clear*i/4
        cuboid(b,xpos,.117,(SPRING+bottom)/2,.026 if i==2 else .016,.047,SPRING-bottom,METAL,label+' vertical glazing bars')
    for i in range(5):
        z=bottom+(z1-bottom)*i/5
        cuboid(b,cx,.121,z,2*clear,.043,.016,METAL,label+' horizontal glazing bars')
    cuboid(b,cx,.098,SPRING-.011,2*R,.084,.045,METAL,label+' transverse steel fanlight bar')
    for j in range(4):
        wedge=Polygon([(cx,SPRING),*sector(cx,SPRING,R,j*pi/4,(j+1)*pi/4,n//4)])
        front(b,wedge,.164,.173,GLASS[1 if j==0 else 0],label+' fanlight glass')
    tube_ring(b,cx,SPRING,R-.015,.108,.017,METAL,label+' steel arched edge',n,lod)
    for ring in (.139,.358):
        tube_ring(b,cx,SPRING,ring,.112,.009,METAL,label+' concentric fanlight tracery',n,lod)
    for j in (1,2,3):
        theta=j*pi/4
        path=[(cx+r*cos(theta),.112,SPRING+r*sin(theta))for r in (.14,R-.018)]
        b.tube(path,.009,METAL,sides=6 if lod else 10,label=label+' radial fanlight bars')
    front(b,arch_strip(cx,SPRING,R,.094,n),-.056,.11,STONE,label+' semicircular arch band')
    tube_ring(b,cx,SPRING,R+.071,-.063,.024,EDGE,label+' curved projecting bead',n,lod)
    for sign in (-1,1):
        if (index==0 and sign==-1) or (index==2 and sign==1):
            cuboid(b,cx+sign*(R+.042),.022,SPRING/2,.084,.162,SPRING,STONE,label+' outer jamb')

def add_arcade(b,lod=False):
    n=24 if lod else 50
    openings=[box(x-R,0,x+R,SPRING).union(half_disk(x,SPRING,R,n)) for x in CENTRES]
    wall=box(-3.124,0,3.124,3.58).difference(unary_union(openings))
    front(b,wall,.011,.298,WALL,'Bounded garden facade and arch spandrels')
    cuboid(b,0,-.03,.024,6.29,.615,.048,'terracotta threshold','Garden threshold')
    for index,cx in enumerate(CENTRES):
        sash(b,cx,lod,index)
    for x,side in ((-BAY/2,'Left'),(BAY/2,'Right')):
        carved_column(b,x,side,lod)
