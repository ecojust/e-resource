"""The four-bay south elevation and its shallow returns, measured in local metres."""
from math import ceil,floor
from shapely.geometry import Polygon,box
from shapely.ops import unary_union
from photo_architecture import Facade

BRICK='weathered umber brick'
HEADER='brown violet headers'
PALE='sunlit russet headers'
MORTAR='buff grey brick flecks'
CEMENT='ivory cement'
STONE='grey rough stone'
SILL='grey sill wash'
SASH='dark glazing bars'
GLASS='blue grey glazing'
ROOF='weathered roof'
SHADOW='shaded recess'
PALETTE={
    BRICK:dict(color=[.44,.345,.309],roughness=.91),
    HEADER:dict(color=[.323,.254,.246],roughness=.91),
    PALE:dict(color=[.520,.421,.373],roughness=.9),
    MORTAR:dict(color=[.571,.489,.440],roughness=.9),
    CEMENT:dict(color=[.83,.805,.741],roughness=.82),
    STONE:dict(color=[.508,.501,.467],roughness=.91),
    SILL:dict(color=[.661,.651,.607],roughness=.87),
    SASH:dict(color=[.213,.236,.235],roughness=.53),
    GLASS:dict(color=[.405,.491,.523],roughness=.29,metallic=.27),
    ROOF:dict(color=[.498,.489,.469],roughness=.93),
    SHADOW:dict(color=[.32,.31,.299],roughness=.94)}
CENTRE_HALF=5.27
BACK=6.05
FLOOR=3.05
GROUND=3.57
TOP=28.30
WING_TOP=25.10

def plate(b,poly,z0,z1,mat,label):
    b.prism(poly,z0,z1,lambda x,y,z:(x,y,z),mat,label)

def jointed_brick(face,wall,low):
    if low:return
    bounds=wall.bounds
    batches={mat:([],[]) for mat in (HEADER,PALE,MORTAR)}
    for row in range(floor(bounds[1]/.119),ceil(bounds[3]/.119)):
        z=(row+.5)*.119
        for column in range(floor(bounds[0]/.252)-1,ceil(bounds[2]/.252)+1):
            val=(column*1879+row*1319+((column+563)*row%41)*607)%101
            if val>32:continue
            x=(column+.5+.5*(row%2))*.252
            brick=box(x-.103,z-.043,x+.103,z+.043)
            if not wall.contains(brick):continue
            mat=HEADER if val<11 else PALE if val<26 else MORTAR
            vertices,faces=batches[mat];n=len(vertices)
            vertices.extend([face.point(u,v,.005)for u,v in ((x-.103,z-.043),(x+.103,z-.043),(x+.103,z+.043),(x-.103,z+.043))]);faces.append((n,n+1,n+2,n+3))
    for mat,(vertices,faces)in batches.items():
        if vertices:face.builder.add(vertices,faces,mat,face.label+' / individual brick headers')

def window(f,cx,z,width,height,low,framed,label):
    hole=box(cx-width/2,z,cx+width/2,z+height)
    f.prism(hole,-.236,-.212,GLASS,label+' glazing')
    grid=[hole.difference(hole.buffer(-.055,join_style=2))]
    count=(3 if low else 6) if width>2.65 else (2 if low else 4)
    for i in range(1,count):
        u=cx+width*(i/count-.5);grid.append(box(u-.021,z,u+.021,z+height))
    for at in ((.57,) if low else (.26,.60)):
        hz=z+height*at;grid.append(box(cx-width/2,hz-.022,cx+width/2,hz+.022))
    f.prism(unary_union(grid),-.174,-.120,SASH,label+' sash')
    if framed:
        outer=hole.buffer(.145,join_style=2)
        f.prism(outer.difference(hole),-.014,.101,CEMENT,label+' white cement reveal')
    f.prism(box(cx-width/2-.09,z-.119,cx+width/2+.09,z-.048),-.01,.16,SILL,label+' sill')
    return hole

def front_bay(f,centers,top,count,low,central=False):
    u=f.length/2;cuts=[]
    for level in range(1,count):
        z=GROUND+(level-1)*FLOOR+.69;w=3.44 if central else min(3.31,f.length-.63)
        for x in centers:
            cuts.append(window(f,x,z,w,1.66,low,central,'paired center window' if central else 'outer window'))
            if not central:
                f.prism(box(x-w/2-.06,z-.68,x+w/2+.06,z-.14),-.013,.054,CEMENT,'ivory wing spandrel')
    shape=box(-u,GROUND,u,top).difference(unary_union(cuts))
    f.prism(shape,-.27,0,BRICK,'brick piers and spandrels');jointed_brick(f,shape,low)
    f.box(0,top-.05,f.length,.1,.19,.025,SILL,'stepped roof coping')

def outer_lower(f,low,label):
    width=min(2.56,f.length*.68);h=window(f,0,1.02,width,1.63,low,False,'splayed base window')
    f.prism(box(-f.length/2,0,f.length/2,GROUND).difference(h),-.3,0,STONE,label+' base masonry')
    for z in (.42,1.0,2.88):f.box(0,z,f.length,.04,.012,.007,SILL,label+' base courses')

def side_return(b,pts,low,wing_top):
    f=Facade(b,*pts,'windowed return')
    u=f.length/2;cuts=[]
    for floor_no in range(1,9):
        z=GROUND+(floor_no-1)*FLOOR+.69;cut=window(f,-.12,z,min(2.65,f.length-.62),1.66,low,False,'return glazing');cuts.append(cut)
        if floor_no<8:f.prism(box(-u+.15,z-.54,u-.16,z-.14),-.01,.042,CEMENT,'return spandrel')
    lower=window(f,0,1.03,min(2.17,f.length-.66),1.61,low,False,'base return')
    f.prism(box(-u,0,u,GROUND).difference(lower),-.24,0,STONE,'stone base of return')
    wall=box(-u,GROUND,u,TOP).difference(unary_union(cuts));f.prism(wall,-.24,0,BRICK,'recessed brick return');jointed_brick(f,wall,low)

def main_entrance(b,low):
    f=Facade(b,(-CENTRE_HALF,.08),(CENTRE_HALF,.08),'central south base')
    # The archive describes a passage and three steps. The photographed trees conceal its leaves.
    recess=box(-1.19,0,1.19,2.80);holes=[recess]
    for x in [-3.10,3.10]:holes.append(window(f,x,1.02,2.66,1.64,low,False,'stone base window'))
    f.prism(box(-CENTRE_HALF,0,CENTRE_HALF,GROUND).difference(unary_union(holes)),-.31,0,STONE,'rough stone base')
    for side in [-1,1]:
        wall=box(side*1.19-.075,.12,side*1.19+.075,1.5)
        plate(b,wall,.11,2.78,STONE,'passage / jamb')
    plate(b,box(-1.23,.08,1.23,1.53),2.78,2.91,SHADOW,'passage / head')
    for n in range(3):plate(b,box(-1.18,.10+n*.33,1.18,1.36),.022,.148+n*.132,STONE,'passage / three steps')
    f=Facade(b,(-1.19,1.53),(1.19,1.53),'passage');f.wall(.0,2.82,thickness=.07,material=SHADOW)

def make_front(b,low):
    front=Facade(b,(-CENTRE_HALF,.08),(CENTRE_HALF,.08),'nine-storey center')
    front_bay(front,[-2.97,2.97],TOP,9,low,True);main_entrance(b,low)
    # Three upright, square-edged fins protrude separately above the stepped crown.
    front.prism(box(-1.40,TOP-.14,1.40,TOP+.68),-.28,0,BRICK,'raised center parapet')
    for x,depth,rise in [(-.43,.22,1.10),(0,.29,1.27),(.43,.22,1.10)]:
        front.prism(box(x-.129,GROUND-.02,x+.129,TOP+rise),-.012,depth,CEMENT,'three vertical cement ribs')
        if not low:front.prism(box(x-.135,GROUND-.02,x-.090,TOP+rise-.02),depth-.006,depth+.005,SILL,'narrow shadow edge of rib')
    for side,outer,y in [(-1,-9.62,4.58),(1,9.11,4.27)]:
        inner=side*CENTRE_HALF
        a,z=sorted([inner,outer]);bank=Facade(b,(a,y),(z,y),'set-back eight-storey wing')
        front_bay(bank,[0],WING_TOP,8,low);outer_lower(bank,low,'wing')
        pts=((inner,y),(inner,.08))if side<0 else((inner,.08),(inner,y));side_return(b,pts,low,WING_TOP)
        pts=((outer,BACK),(outer,y))if side<0 else((outer,y),(outer,BACK))
        end=Facade(b,*pts,'outside cut return');end.wall(0,WING_TOP,thickness=.12,material=BRICK)
        plan=box(a,y,z,BACK);plate(b,plan,WING_TOP-.15,WING_TOP,ROOF,'lower wing flat roof')
        Facade(b,(z,BACK),(a,BACK),'wing rear cut').wall(0,WING_TOP,thickness=.09,material=SHADOW)
        plate(b,plan,.016,.094,STONE,'wing base')
    plan=box(-CENTRE_HALF,.08,CENTRE_HALF,BACK)
    plate(b,plan,TOP-.15,TOP,ROOF,'upper flat roof');plate(b,plan.difference(box(-1.23,.0,1.23,1.57)),.016,.094,STONE,'center base')
    Facade(b,(CENTRE_HALF,BACK),(-CENTRE_HALF,BACK),'rear cut of central block').wall(0,TOP,thickness=.09,material=SHADOW)
    for side in (-1,1):
        x=side*CENTRE_HALF;pts=((x,BACK),(x,4.24))if side<0 else((x,4.24),(x,BACK))
        Facade(b,*pts,'upper shoulders').wall(WING_TOP,TOP,thickness=.11,material=BRICK)
