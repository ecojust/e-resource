"""Jiangchuan Building at 89 Jiujiang Road, including the two documented later floors."""
from math import cos, pi, sin
from shapely.geometry import Point, Polygon, box
from shapely.geometry.polygon import orient
from photo_architecture import Facade, opening

ASHLAR='grey brown cut granite'; COLUMN='granite Corinthian shaft'
CAP='pale carved facing stone'; SASH='dark bronze sash'; GLASS='inset cool glazing'
BRONZE='aged bronze'; DOOR='dark oak'; ROOF='slate grey roof'; ADDITION='1988 pale rendered upper face'
PALETTE={
    ASHLAR:{'color':[.47,.40,.34],'roughness':.87},
    COLUMN:{'color':[.48,.41,.34],'roughness':.74},
    CAP:{'color':[.64,.54,.44],'roughness':.77},
    SASH:{'color':[.13,.108,.088],'metallic':.35},
    GLASS:{'color':[.137,.195,.21],'metallic':.20,'roughness':.30},
    BRONZE:{'color':[.22,.185,.134],'metallic':.55},
    DOOR:{'color':[.205,.137,.085],'roughness':.65},
    ROOF:{'color':[.28,.29,.29],'roughness':.90},
    ADDITION:{'color':[.66,.59,.50],'roughness':.88},
}
# Local east and north are aligned to the two streets. The estimate allows
# a return inside the map trace where the tall adjoining owner lies to the east.
SW=(-11.20,-11.04); W=(-11.12,10.67); N=(-7.80,12.86); NE=(10.45,13.10)
E=(10.24,10.59); SE=(10.64,-12.78); K=(-3.90,-13.15)
RING=[SW,K,SE,E,NE,N,W]
PLAN=Polygon(RING)
CORNICE=15.8
TOP=25.76


def course(f,z,h,projection,mat=CAP):
    f.box(0,z,f.length+.018,h,projection+.19,projection/2-.095,mat,'continuous stone course')


def glazed(f,hole,lod,columns=2):
    f.window(hole,columns=columns,rows=2,frame=SASH,trim=False,glass=GLASS,label='recessed sash')
    x0,z,x1,_=hole.bounds
    f.box((x0+x1)/2,z-.07,x1-x0+.17,.13,.29,.042,CAP,'window sill')


def cornice(f,lod):
    for z,h,d in [(14.78,.16,.42),(15.04,.23,.51),(15.38,.35,.68),(15.72,.22,.82)]:
        course(f,z,h,d)
    count=max(2,round(f.length/(.85 if lod else .43)))
    for i in range(count):
        u=(i+.5)*f.length/count-f.length/2
        f.box(u,15.12,.14,.23,.37,.43,CAP,'cornice dentil')


def jointed_wall(f,z0,z1,holes,lod):
    surface=f.wall(z0,z1,holes,.40,ASHLAR)
    step=.85 if lod else .48
    for i in range(1,int((z1-z0)/step)):
        z=z0+i*step
        line=surface.intersection(box(-f.length/2,z,f.length/2,z+.030))
        f.prism(line,.003,.015,COLUMN,'rusticated horizontal joint')


def corinthian(f,u,r,lod):
    b=f.builder
    for z,h,width,depth in [(.24,.42,2.85*r,1.46),(1.18,1.45,2.42*r,1.29),
                            (2.02,.21,2.68*r,1.38),(2.20,.14,2.45*r,1.31)]:
        f.box(u,z,width,h,depth,.20,CAP,'column pedestal or base')
    xy=f.point(u,0,.24)
    disc=Point(xy[0],xy[1]).buffer(r,resolution=4 if lod else 8)
    b.plan_prism(disc,2.22,13.67,COLUMN,f.label+'/three-storey shaft')
    xy=f.point(u,0,.24)
    for z,top,rad in [(13.60,13.77,r*1.15),(13.77,14.34,r*1.21)]:
        b.plan_prism(Point(xy[0],xy[1]).buffer(rad,resolution=5 if lod else 8),z,top,CAP,
                     f.label+'/Corinthian echinus')
    # The photographs resolve a ring of turned-up leaves and small volutes.
    n=7 if lod else 12
    for k in range(n):
        angle=k*2*pi/n
        tang=(cos(angle),sin(angle));side=(-tang[1],tang[0]);offset=r*.77
        x,y=xy[0]+offset*tang[0],xy[1]+offset*tang[1]
        base=(x,y,13.72);tip=(x+.42*tang[0],y+.42*tang[1],14.33)
        vertices=[base,(x+.13*side[0],y+.13*side[1],14.00),tip,
                  (x-.13*side[0],y-.13*side[1],14.00),
                  (x+.27*tang[0],y+.27*tang[1],14.02)]
        b.add(vertices,[(0,1,4),(1,2,4),(2,3,4),(3,0,4)],CAP,f.label+'/capital acanthus leaves')
    f.box(u,14.45,r*3.22,.23,1.56,.22,CAP,'capital abacus')


def upper_stories(f,count,lod,corner=False):
    width=f.length/count
    for layer,(z0,z1,sill,head) in enumerate([(15.79,18.83,16.23,18.37),
                                            (18.83,22.25,19.50,21.72),
                                            (22.25,TOP,22.94,25.02)]):
        apertures=[]
        for i in range(count):
            u=(i+.5)*width-f.length/2
            if corner and layer==1:
                ring=Point(u,20.77).buffer(.48,resolution=8 if lod else 16)
                f.prism(ring.buffer(.14).difference(ring),-.03,.10,BRONZE,'octagonal wreath')
                f.prism(ring,-.015,.008,ROOF,'wreath centre')
                continue
            # The original fourth floor has narrower upright sash. The later
            # two floors have longer metal window strips except on the corner.
            w=width*(.50 if layer==0 or corner else .71)
            hole=opening(u,sill,w,head-sill,arch=.34 if corner and layer==0 else 0,
                         segments=9 if lod else 16)
            apertures.append(hole)
            glazed(f,hole,lod,2 if layer==0 or corner else 3)
            if corner and layer in (0,2):
                x0,_,x1,_=hole.bounds
                arch=opening(u,head-.27,w+.38,.55,arch=.38,segments=9 if lod else 18)
                inner=opening(u,head-.35,w+.18,.52,arch=.34,segments=9 if lod else 18)
                f.prism(arch.difference(inner),.015,.22,CAP,'curved hood over corner sash')
        f.wall(z0,z1,apertures,.30,ASHLAR if layer==0 else ADDITION)
        if layer==0:course(f,18.81,.19,.26)
    course(f,TOP-.12,.25,.25)


def street(b,a,end,lod,label):
    f=Facade(b,a,end,label)
    # Three recessed window bays sit below each three-storey colonnade. The
    # flanking edges are solid rusticated end bays with their own narrow windows.
    width=f.length
    span=width*.705
    module=span/3
    centers=[-module,0,module]
    holes=[]
    for u in centers:
        arch=opening(u,.78,module*.65,4.09,arch=.90,segments=10 if lod else 20)
        holes.append(arch);glazed(f,arch,lod)
        f.prism(arch.buffer(.14).difference(arch),-.18,.035,CAP,'round-headed ground window surround')
        for floor in [5.66,10.14]:
            for side in [-1,1]:
                h=opening(u+side*module*.145,floor,module*.226,2.97)
                holes.append(h);glazed(f,h,lod,1)
        f.box(u,1.13,module*.73,.17,.27,.10,CAP,'low sill under colonnade')
    for edge in [-1,1]:
        u=edge*width*.44;w=width*.073
        if edge>0:
            gate=opening(u,.12,w,4.49,arch=.83,segments=10 if lod else 18)
            holes.append(gate);f.prism(gate.buffer(.006),-.49,-.47,DOOR,'end-bay doorway')
        for z in [6.05,10.54]:
            h=opening(u,z,w,2.22);holes.append(h);glazed(f,h,lod)
    jointed_wall(f,0,CORNICE,holes,lod)
    for ix in range(4):
        corinthian(f,-span/2+ix*module,.52,lod)
    cornice(f,lod);upper_stories(f,5,lod)


def corner(b,lod):
    f=Facade(b,N,W,'northwest corner entrance')
    gate=opening(0,.10,2.83,4.38)
    lower=opening(0,5.78,2.05,2.60);higher=opening(0,10.20,2.03,2.71)
    jointed_wall(f,0,CORNICE,[gate,lower,higher],lod)
    f.prism(gate.buffer(.01),-.70,-.63,DOOR,'paired deeply recessed entrance doors')
    for u in [-.68,.68]:
        f.box(u,2.23,1.10,3.27,.10,-.56,DOOR,'door leaf raised rails')
    for u in [-1.54,1.54]:
        f.box(u,2.28,.23,4.65,.41,.12,CAP,'portal jamb')
    glazed(f,lower,lod);glazed(f,higher,lod)
    f.box(0,4.69,3.48,.27,.62,.18,CAP,'pediment lintel')
    outer=Polygon([(-1.72,4.73),(0,6.13),(1.72,4.73),(1.54,4.70),(0,5.86),(-1.53,4.70)])
    f.prism(outer,-.05,.31,CAP,'Baroque portal pediment')
    shield=Point(0,5.12).buffer(.30,resolution=6 if lod else 12)
    f.prism(shield,-.03,.13,CAP,'portal cartouche')
    for hand in [-1,1]:
        branch=Polygon([(hand*.10,5.11),(hand*.44,5.38),(hand*.69,5.21),(hand*.79,5.07),(hand*.34,5.15)])
        f.prism(branch,-.01,.16,CAP,'carved leaf beside portal cartouche')
    for z in [5.70,10.10]:
        f.box(0,z,2.28,.17,.36,.09,CAP,'upper balcony sill')
        for i in range(8 if not lod else 5):
            n=8 if not lod else 5
            f.box((i+.5)*2.00/n-1,z+.35,.056,.6,.06,.20,BRONZE,'corner grille upright')
        f.box(0,z+.65,2.13,.075,.11,.22,BRONZE,'corner grille rail')
    cornice(f,lod);upper_stories(f,1,lod,True)


def add_building(b,lod):
    street(b,W,SW,lod,'Sichuan west facade')
    street(b,NE,N,lod,'Jiujiang north facade')
    corner(b,lod)
    for a,end in [(SW,K),(K,SE),(SE,E),(E,NE)]:
        f=Facade(b,a,end,'rear shared masonry');f.wall(0,TOP,(),.26,ASHLAR)
    b.plan_prism(PLAN,0,.13,ASHLAR,'ground floor')
    b.plan_prism(PLAN,TOP-.13,TOP,ROOF,'main roof slab')
    for a,end in zip(RING,RING[1:]+RING[:1]):
        f=Facade(b,a,end,'upper parapet')
        f.wall(TOP,TOP+.44,(),.19,ADDITION)
    # Shallow sloped roof above the 1988 additions; rear plant arrangement is unknown.
    inset=orient(PLAN.buffer(-1.21,join_style='mitre'),sign=1)
    b.plan_prism(inset,TOP+.02,TOP+.41,ROOF,'raised roof inside parapet')
