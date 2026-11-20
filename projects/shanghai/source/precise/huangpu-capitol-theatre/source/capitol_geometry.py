"""Capitol Building's northwestern theatre door, curved office floors and two rooftop towers."""
from math import cos, sin, pi
from shapely.geometry import Polygon, box
from shapely.ops import unary_union
from photo_architecture import Facade

PALETTE={
    'warm mineral cladding':{'color':[.52,.458,.369],'roughness':.84},
    'limestone coping':{'color':[.659,.599,.480],'roughness':.77},
    'shade under stonework':{'color':[.386,.333,.278],'roughness':.90},
    'carved stone':{'color':[.604,.530,.412],'roughness':.81},
    'grey steel sash':{'color':[.222,.237,.224],'roughness':.47,'metallic':.35},
    'green-grey windows':{'color':[.148,.172,.175],'roughness':.28,'metallic':.17},
    'smoked entrance glass':{'color':[.094,.122,.121],'roughness':.28,'metallic':.16},
    'bronze shelter':{'color':[.355,.269,.156],'roughness':.51,'metallic':.57},
    'pale shelter glass':{'color':[.545,.535,.427],'roughness':.36,'metallic':.13},
    'lantern brass':{'color':[.520,.406,.204],'roughness':.43,'metallic':.48},
    'roof membrane':{'color':[.362,.357,.321],'roughness':.87},
    'terrace iron':{'color':[.120,.124,.117],'roughness':.58,'metallic':.41},
    'shared masonry':{'color':[.447,.412,.364],'roughness':.89}}
WALL='warm mineral cladding';STONE='limestone coping';GLASS='green-grey windows'
TOP=27.23;STOREY=3.25
# Directed clockwise survey boundary is reversed for all outward-facing street skins.
# Both ends of the western front stop short of the adjoining eastern apartment's wall.
BACK=[(19.715,10.497),(21.413,10.301),(20.938,-4.578),(17.099,-4.569),(16.421,-15.77)]
CURVE=[(-26.19,10.38),(-25.99,5.82),(-23.64,1.27),(-21.07,-2.15),
       (-16.43,-5.87),(-9.50,-9.54),(-1.95,-12.92),(7.26,-14.56),BACK[-1]]
# The northwestern doorway and the principal tower share a single radial axis.
PORTAL=3


def glazing(f,panels,depth,raw_material,low):
    panes=[];joinery=[]
    for o,c,r in panels:
        a,z,b,Z=o.bounds
        panes.append(o.buffer(.003,join_style='mitre'))
        inner=o.buffer(-.062,join_style='mitre')
        lines=[]
        for k in range(1,c):
            x=a+(b-a)*k/c;lines.append(box(x-.023,z,x+.023,Z))
        for k in range(1,r):
            v=z+(Z-z)*k/r;lines.append(box(a,v-.021,b,v+.021))
        joinery.append(o.difference(inner.difference(unary_union(lines))))
    if panes:
        f.prism(unary_union(panes),-depth-.022,-depth,raw_material,'recessed glazing')
        f.prism(unary_union(joinery),-depth+.016,-depth+.078,'grey steel sash','sash grid')


def balcony(f,height,width):
    f.box(0,height,width,.16,.91,.32,STONE,'projecting balcony floor')
    for u in [-width/2+.09,width/2-.09]:
        f.line((u,height+.06,.12),(u,height+.78,.12),.034,'terrace iron')
        f.line((u,height+.78,.12),(u,height+.78,.74),.030,'terrace iron')
    for i in range(12):
        u=-width/2+.09+(width-.18)*i/11
        f.line((u,height+.11,.74),(u,height+.78,.74),.021,'terrace iron',6)
    for z in (height+.33,height+.78):
        f.line((-width/2+.07,z,.74),(width/2-.07,z,.74),.031,'terrace iron')


def awning(f):
    w=3.64
    for i in range(9):
        u=-w/2+i*w/8
        f.line((u,3.74,.08),(u,3.48,1.80),.038,'bronze shelter')
    for i in range(4):
        d=.08+i*1.72/3;z=3.74-i*.26/3
        f.line((-w/2,z,d),(w/2,z,d),.043,'bronze shelter')
    for i in range(8):
        for j in range(3):
            a=-w/2+(i+.5)*w/8;v=.08+(j+.5)*1.72/3
            f.box(a,3.74-(v-.08)*.26/1.72-.05,w/8-.05,.028,1.72/3-.06,v,'pale shelter glass','shelter panes')
    for u in [-1.40,1.40]:
        f.line((u,4.48,.08),(u,3.52,1.66),.027,'bronze shelter')


def front(b,i,a,c,lod):
    f=Facade(b,a,c,'Northwest theatre entrance' if i==PORTAL else 'Curved street section '+str(i+1))
    n=max(1,round(f.length/2.14))
    pitch=f.length/n;upper=[];base=[];carving=[];subframes=[]
    cuts=[]
    for bay in range(n):
        u=(bay+.5-n/2)*pitch
        for floor in range(7):
            z=3.99+floor*STOREY;w=pitch*(.74 if floor==6 else .71)
            op=box(u-w/2,z+.50,u+w/2,z+2.42)
            cuts.append(op);upper.append((op,2 if lod else 3,1 if lod else 2))
            subframes.append(box(u-w/2-.037,z+.401,u+w/2+.037,z+.468))
            if not lod and 0<floor<6:
                panel=box(u-.31*w,z-.45,u+.31*w,z+.25)
                carving.extend([panel.boundary.buffer(.026,join_style='mitre'),
                    Polygon([(u-.22*w,z-.06),(u,z+.17),(u+.22*w,z-.06),(u,z-.26)]).boundary.buffer(.024,join_style='mitre')])
        if i!=PORTAL:
            w=pitch*.68
            op=box(u-w/2,.38,u+w/2,3.28)
            cuts.append(op);base.append((op,2,2))
    if i==PORTAL:
        op=box(-1.56,.0,1.56,3.27);cuts.append(op);base.append((op,3,2))
        for u in [-f.length/2+.34,f.length/2-.34]:
            f.box(u,1.73,.54,3.40,.48,.047,STONE,'theatre door jamb')
        awning(f)
        balcony(f,23.74,min(3.74,f.length-.30))
    skin=box(-f.length/2,0,f.length/2,TOP).difference(unary_union(cuts))
    f.prism(skin,-.28,.0,WALL,'cut limestone and plaster envelope')
    glazing(f,upper,.305,GLASS,lod)
    glazing(f,base,.60 if i==PORTAL else .34,'smoked entrance glass',lod)
    f.prism(unary_union(subframes),.0,.114,STONE,'window stools')
    if carving:f.prism(unary_union(carving),.006,.056,'carved stone','spandrel relief')
    if i in [4,5,6,7]:
        for j in range(1,n):
            if (j+i)%3==1:continue
            u=(j-n/2)*pitch
            f.box(u,18.95,.27,15.56,.35,.049,STONE,'fluted vertical office pier')
            f.box(u-.077,18.95,.028,15.38,.045,.234,'shade under stonework','pier bead recess')
            f.box(u+.077,18.95,.028,15.38,.045,.234,'shade under stonework','pier bead recess')
    for u in [-f.length/2+.10,f.length/2-.10]:
        f.box(u,17.45,.166,17.8,.205,.04,STONE,'vertical arris')
    for h,t,d,mat in [(3.95,.12,.12,STONE),(10.66,.15,.24,'shade under stonework'),
                       (10.85,.26,.42,STONE),(11.08,.095,.29,STONE),
                       (26.83,.11,.33,'shade under stonework'),(27.07,.32,.42,STONE),(27.32,.13,.46,STONE)]:
        f.beam(h,t,d,mat,width=f.length+.012,label='waistline course' if h<12 else 'upper cornice')
    return f


def rectangle(b,cx,cy,angle,w,depth):
    tx,ty=cos(angle),sin(angle);nx,ny=ty,-tx
    def pos(u,v):return (cx+tx*u+nx*v,cy+ty*u+ny*v)
    return [pos(-w/2,-depth/2),pos(-w/2,depth/2),pos(w/2,depth/2),pos(w/2,-depth/2)]


def tower(b,cx,cy,angle,large,lod):
    kind='Theatre entrance tower' if large else 'Southern roof tower'
    def stage(w,d,bottom,top,mat,windows=False,slots=False):
        ring=rectangle(b,cx,cy,angle,w,d)
        for i,(a,c) in enumerate(zip(ring,ring[1:]+ring[:1])):
            f=Facade(b,a,c,kind+' stage '+str(bottom)+' face '+str(i))
            if not(windows or slots):
                f.wall(bottom,top,thickness=.18,material=mat)
                continue
            gap=f.length/(3 if windows else 1);n=3 if windows else 1
            holes=[]
            for j in range(n):
                u=(j+.5-n/2)*gap;wid=gap*.48 if windows else min(.67,gap*.33)
                z=bottom+.55;Z=top-.54
                holes.append(box(u-wid/2,z,u+wid/2,Z))
            f.prism(box(-f.length/2,bottom,f.length/2,top).difference(unary_union(holes)),-.22,0,mat,'pierced tower stage')
            glazing(f,[(q,2 if windows else 1,2 if windows and not lod else 1) for q in holes],.26,GLASS,lod)
            if slots:
                for u in [-f.length*.36,f.length*.36]:
                    f.box(u,(bottom+top)/2,.16,top-bottom,.22,.052,STONE,'tower pilaster')
        b.plan_prism(Polygon(ring).buffer(.10,join_style='mitre'),top-.03,top+.13,STONE,kind+'/coping')
    stage(5.70 if large else 4.60,3.85 if large else 3.18,26.83,30.50 if large else 29.16,STONE,windows=True)
    if large:
        stage(3.87,2.93,30.54,32.91,WALL)
        stage(3.12,2.62,32.94,39.72,WALL,slots=True)
        # Separate high stone buttresses step down to the rectangular ventilation stage.
        ring=rectangle(b,cx,cy,angle,3.17,2.67)
        for i,(a,c) in enumerate(zip(ring,ring[1:]+ring[:1])):
            f=Facade(b,a,c,'Principal tower buttress '+str(i))
            for side in (-1,1):
                f.box(side*(f.length/2-.22),33.67,.38,4.26,.39,.04,STONE,'stepped shallow buttress')
                f.box(side*(f.length/2-.22),36.29,.245,1.0,.27,.034,STONE,'narrow shoulder')
        stage(2.24,1.80,39.75,40.52,STONE)
        # Faceted pyramidal coping and the small blunt brass terminal visible above the shaft.
        ring_a=rectangle(b,cx,cy,angle,1.58,1.27)
        ring_b=rectangle(b,cx,cy,angle,.58,.43)
        vertices=[(x,y,40.55) for x,y in ring_a]+[(x,y,41.38) for x,y in ring_b]
        faces=[(0,2,1),(0,3,2),(4,5,6),(4,6,7)]
        for k in range(4):
            n=(k+1)%4;faces.extend([(k,n,n+4),(k,n+4,k+4)])
        b.add(vertices,faces,STONE,kind+'/four slope coping')
        b.plan_prism(Polygon(ring_b),41.38,41.75,'lantern brass',kind+'/terminal')
    else:
        stage(3.14,2.46,29.20,34.13,WALL,slots=True)
        stage(2.86,2.35,34.17,34.58,STONE)


def make_capitol(b,lod):
    street=[]
    for i,(a,c) in enumerate(zip(CURVE,CURVE[1:])):
        street.append(front(b,i,a,c,lod))
    # Continue around the unphotographed southern returns. The long east party wall
    # has its own plain masonry, and stops before the separate stepped building.
    rest=list(reversed(BACK[:-1]))+[CURVE[0]]
    for i,(a,c) in enumerate(zip([CURVE[-1]]+rest,rest)):
        f=Facade(b,a,c,'Back masonry '+str(i))
        f.wall(0,26.90,thickness=.23,material='shared masonry')
    footprint=Polygon(CURVE+rest[:-1])
    land=footprint.buffer(-.035,join_style='mitre')
    f=street[PORTAL]
    slot=Polygon([f.point(u,0,v)[:2] for u,v in [(-1.56,.07),(1.56,.07),(1.56,-.60),(-1.56,-.60)]])
    b.plan_prism(land.difference(slot),.01,.058,'shade under stonework','Northwest entrance/ground with recess')
    b.plan_prism(footprint.buffer(-.10,join_style='mitre'),26.72,26.84,'roof membrane','Roof/main deck')
    from math import atan2
    theta=atan2(f.t[1],f.t[0])
    cx,cy=f.point(0,0,-2.56)[:2];tower(b,cx,cy,theta,True,lod)
    f2=street[-1];sx,sy=f2.point(1.17,0,-2.43)[:2]
    tower(b,sx,sy,atan2(f2.t[1],f2.t[0]),False,lod)
