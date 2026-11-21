"""The two street elevations of Empire Mansions, photographed after restoration."""
import math
from pathlib import Path
import sys
from shapely.geometry import Point, Polygon, LineString, box
from shapely.ops import unary_union
HERE = Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[3]/'source/precise/hongkou-general-post-office/source/common'))
from photo_architecture import Facade
from sign_lettering import add_facade_lettering

WALL='ivory stucco'
LIP='pale cast trim'
BRICK='brown facing brick'
SASH='dark green steel'
GLASS='blue grey glass'
SHADE='deep recess'
STONE='grey base stone'
BRASS='aged metal lettering'
VENT='pale louvred grille'
BACK='section finish'
ROOF='grey roofing'
PALETTE={name:dict(color=list(rgb),roughness=r,metallic=m) for name,rgb,r,m in [
    (WALL,(.827,.818,.778),.90,0),(LIP,(.90,.879,.835),.84,0),
    (BRICK,(.271,.218,.182),.88,0),(SASH,(.101,.150,.145),.53,.22),
    (GLASS,(.265,.354,.361),.30,.22),(SHADE,(.185,.195,.191),.88,0),
    (STONE,(.444,.440,.412),.89,0),(BRASS,(.546,.432,.270),.53,.39),
    (VENT,(.727,.737,.708),.70,.14),(BACK,(.692,.679,.636),.90,0),
    (ROOF,(.451,.447,.419),.89,0)]}
# Directed, counterclockwise exterior edges, in local metres from the door.
FRONT=[(-47.7019389,62.4809795),(-3.5800115,0.),(3.5800115,0.),(60.9721701,23.0056533)]
GROUND=3.86
FIRST=4.49
FLOOR=3.22
WING_TOP=21.85
UPPER_TOP=25.02
THICK=2.85
FONT=HERE/'fonts/EmpireCornerSubset.otf'

def rect(f,u,z,width,height,back,face,mat,label):
    f.box(u,z,width,height,face-back,(face+back)/2,mat,label)

def strip(front,depth):
    return LineString(front).buffer(depth,single_sided=True,join_style=2)

def window(f,u,base,width,height,lod,holes,cols,rows=5,depth=.20):
    hole=box(u-width/2,base,u+width/2,base+height)
    holes.append(hole)
    f.prism(hole.buffer(.009,join_style=2),-depth-.018,-depth,GLASS,'recessed glazing')
    bars=[]
    for j in range(1,cols):
        x=u-width/2+j*width/cols
        bars.append(box(x-.026,base,x+.026,base+height))
    for j in range(1,rows):
        if lod and rows>3 and j%2:continue
        z=base+j*height/rows
        bars.append(box(u-width/2,z-.020,u+width/2,z+.020))
    frame=hole.difference(hole.buffer(-.054,join_style=2).difference(unary_union(bars)))
    f.prism(frame,-depth+.014,-depth+.061,SASH,'steel sash grid')

def convector(f,u,z,lod):
    """Box projecting from the spandrel with horizontal open louvres."""
    rect(f,u,z,.81,.59,.018,.255,VENT,'grille box')
    for row in range(3 if lod else 6):
        dz=(row-(1 if lod else 2.5))*(.173 if lod else .084)
        rect(f,u,z+dz,.88,.036,.251,.376, LIP,'horizontal grille blades')

def stepped_console(f,u,z,scale=1):
    # Three horizontal courses with rounded ends, visible below the long pilasters.
    for j in range(3):
        length=scale*(1.12-.12*j)
        face=.30-.032*j
        a=(f.point(u-length/2,0,face/2))[:2];b=(f.point(u+length/2,0,face/2))[:2]
        outline=LineString([a,b]).buffer(face/2,quad_segs=5)
        f.builder.plan_prism(outline,z-.20*j,z+.105-.20*j,LIP,f.label+'/rounded bracket courses')

def corner_fin(f,u,base,top,wide,lod):
    # The three white blades alternate with four darker brick channels.
    w=2.55*wide
    rect(f,u,(base+top-.62)/2,w,top-.62-base,-.02,.15,BRICK,'brown brick spine')
    for j,delta in enumerate([-.72,0,.72]):
        h=top-(.35 if j!=1 else 0)
        rect(f,u+delta*wide,(h+base)/2,.27*wide,h-base,.13,.46,LIP,'three vertical fins')
        rect(f,u+delta*wide,h-.57,.29*wide,1.03,.41,.58,LIP,'projecting fin heads')
        if not lod:
            for dz in [.89,1.07,1.25]:
                rect(f,u+delta*wide,h-dz,.29*wide,.046,.455,.535,LIP,'stepped head courses')
    for dz in [1.18,1.42,1.69]:
        rect(f,u,top-dz,w+.13,.10,.151,.209,LIP,'transverse crest courses')
    stepped_console(f,u,base+.02,2.17*wide)

def porthole_stack(f,u,lod,wall_holes):
    # Five circular lights occupy a convex white vertical shaft. Divide its
    # curved face into tracts so the reveals follow the rounded plan in both LoDs.
    width=1.90
    surface=box(-width/2,GROUND+.08,width/2,WING_TOP-.12)
    holes=[]
    for level in range(5):
        z=FIRST+level*FLOOR+1.12
        circ=Point(0,z).buffer(.39,quad_segs=6 if lod else 12);holes.append(circ)
        actual=Point(u,z).buffer(.39,quad_segs=6 if lod else 12);wall_holes.append(actual)
        f.prism(actual.buffer(.006),-.12,-.10,GLASS,'small circular landing window')
        for dz in [0.] if lod else [-.13,.11]:
            f.prism(actual.intersection(box(u-.40,z+dz-.023,u+.40,z+dz+.023)),-.08,-.039,SASH,'circular light transom')
    face=surface.difference(unary_union(holes))
    pieces=6 if lod else 12
    def at(x,z,d):
        depth=.05+.31*math.sqrt(max(0,1-(x/(width/2))**2))
        return f.point(u+x,z,d+depth)
    for j in range(pieces):
        x=-width/2+j*width/pieces
        slab=face.intersection(box(x,GROUND,x+width/pieces,WING_TOP))
        f.builder.prism(slab,-.048,0,at,WALL,f.label+'/curved stair window pier')

def wings(f,lod,from_corner):
    """Construct one wing in metres measured away from its junction with the cut corner."""
    n=f.length
    def u(distance):return from_corner*(distance-n/2)
    thresholds=[0,11.0,n*.258,n*.501,n*.753,n]
    spine=n*.501
    port=[n*.258,n*.753]
    ground=[]
    # Neutral windows face the street in place of changeable tenant graphics.
    shops=max(8,round(n/4.2))
    for k in range(shops):
        x=u((k+.5)*n/shops);width=n/shops-.43
        window(f,x,.34,width,2.73,lod,ground,3,rows=2,depth=.27)
    f.wall(0,GROUND,ground,thickness=.30,material=WALL)
    rect(f,0,.17,n,.27,-.005,.045,STONE,'shop plinth')
    rect(f,0,3.62,n,.27,-.02,.12,LIP,'shop header')
    holes=[]
    for k in range(5):
        base=FIRST+FLOOR*k
        for a,b in zip(thresholds,thresholds[1:]):
            start=a+(.19 if a==0 else 1.38 if a==spine else 1.10 if a in port else .15)
            end=b-(.22 if b==n else 1.38 if b==spine else 1.10 if b in port else .15)
            count=max(1,round((end-start)/5.12))
            seg=(end-start)/count
            for j in range(count):
                dist=start+seg*(j+.5);x=u(dist)
                # Narrow brick jambs visually connect the deep green steel sash into a horizontal band.
                window(f,x,base,seg-.14,1.76,lod,holes,max(3,round(seg/.70)))
                if j+1<count:rect(f,u(start+(j+1)*seg),base+.88,.15,1.77,-.015,.015,BRICK,'narrow brick jamb')
                if k in (1,2,3,4):convector(f,x,base-.40,lod)
    for pos in port:porthole_stack(f,u(pos),lod,holes)
    f.wall(GROUND,WING_TOP,holes,thickness=.28,material=WALL)
    corner_fin(f,u(spine),GROUND+.17,24.03,1,lod)
    for pos in [n*.395,n*.635,n*.915]:
        rect(f,u(pos),(GROUND+WING_TOP+.40)/2,.21,WING_TOP+.40-GROUND,-.01,.15,LIP,'narrow vertical fillet')
        stepped_console(f,u(pos),GROUND+.14,.47)
    # Top photographed setback is confined to the short range beside the junction.
    ext=11.0
    taller=Facade(f.builder,f.point(u(0),0)[:2],f.point(u(ext),0)[:2],f.label+' upper corner') if from_corner==1 else Facade(f.builder,f.point(u(ext),0)[:2],f.point(u(0),0)[:2],f.label+' upper corner')
    holes=[]
    for j in [-1,1]:window(taller,j*2.68,WING_TOP+.24,5.23,1.65,lod,holes,4,rows=2,depth=.25)
    taller.wall(WING_TOP,UPPER_TOP,holes,.28,WALL)
    rect(f,0,WING_TOP-.08,n,.13,-.01,.08,LIP,'roof coping')

def entry(f,lod):
    holes=[]
    door=box(-1.53,.02,1.53,2.81);holes.append(door)
    rect(f,0,1.43,3.06,2.82,-1.79,-1.72,GLASS,'recessed paired shopfront door')
    for x in [-1.48,0,1.48]:rect(f,x,1.40,.073,2.79,-1.72,-1.64,SASH,'door mullions')
    for z in [.12,1.0,2.39,2.76]:rect(f,0,z,3.0,.065,-1.72,-1.64,SASH,'door rails and transom')
    for sign in [-1,1]:
        rect(f,sign*1.551,1.4,.042,2.80,-1.76,0,SHADE,'dark recessed jamb')
        pos=f.point(sign*1.61,0,.068)
        f.builder.lathe(pos[:2],[(0,.217),(.10,.219),(2.70,.207),(2.79,.21),(2.82,.21)],LIP,14 if lod else 26,f.label+'/round gate columns')
        for z in [2.35,2.55]:f.builder.lathe(pos[:2],[(z,.212),(z+.055,.212)],BRICK,14 if lod else 26,f.label+'/dark neck rings')
        window(f,sign*2.68,.47,1.46,2.27,lod,holes,2,rows=2)
    rect(f,0,2.82,3.05,.05,-1.74,0,SHADE,'doorway soffit')
    rect(f,0,.03,3.07,.05,-1.76,.17,STONE,'inset threshold')
    rect(f,0,3.19,3.62,.78,.015,.16,LIP,'street name lintel')
    add_facade_lettering(f,'淮海大楼',0,3.22,2.05,.42,.161,.199,BRASS,label='typeset corner name',font=FONT)
    for k in range(6):
        z=WING_TOP+.24 if k==5 else FIRST+FLOOR*k
        for side in [-1,1]:
            window(f,side*2.45,z,2.12,1.68,lod,holes,4,rows=2 if k==5 else 5)
    f.wall(0,UPPER_TOP,holes,.285,WALL)
    corner_fin(f,0,GROUND+.17,27.27,1.02,lod)
    rect(f,0,UPPER_TOP+.42,3.27,.86,-.18,.03,WALL,'raised central crown block')

def close_section(b,points,z0,z1,label):
    section=strip(points,THICK)
    b.plan_prism(section,z1-.13,z1,ROOF,label+'/roof slice')
    front=LineString(points)
    coords=list(section.exterior.coords)
    for a,c in zip(coords,coords[1:]):
        mid=Point((a[0]+c[0])/2,(a[1]+c[1])/2)
        if front.distance(mid)<.025:continue
        face=Facade(b,a,c,label+' return')
        face.wall(z0,z1,thickness=.035,material=BACK)

def add_empire(b,lod):
    f1=Facade(b,FRONT[0],FRONT[1],'Changshu Road')
    f2=Facade(b,FRONT[2],FRONT[3],'Middle Huaihai Road')
    wings(f1,lod,-1)
    wings(f2,lod,1)
    entry(Facade(b,FRONT[1],FRONT[2],'1326 corner entrance'),lod)
    close_section(b,FRONT,0,WING_TOP,'adjoining original mass')
    c1=f1.point(f1.length/2-11,0)[:2]
    c2=f2.point(-f2.length/2+11,0)[:2]
    close_section(b,[c1,FRONT[1],FRONT[2],c2],WING_TOP,UPPER_TOP,'raised junction')
