"""Street elevation measured against the fixed named building and photos of 2013 and 2026."""
import numpy as np
from shapely.geometry import Polygon,box
from shapely.ops import unary_union
from photo_architecture import Facade

PLASTER='warm ivory cement'
TILE='dark umber glazed tile'
JOINT='warm tile joint'
CORNICE='pale grey cement cap'
LIP='light stepped moulding'
IRON='dark steel window grid'
GLASS='grey blue window glass'
SHOP='dark ground glass'
BRONZE='aged bronze frames'
BASE='grey shop base'
ROOF='warm grey roof surface'
CUT='shadowed section render'
PALETTE={
 PLASTER:dict(color=[.802,.764,.685],roughness=.9),TILE:dict(color=[.351,.296,.267],roughness=.68),
 JOINT:dict(color=[.442,.398,.362],roughness=.81),CORNICE:dict(color=[.687,.684,.634],roughness=.84),
 LIP:dict(color=[.823,.816,.765],roughness=.85),IRON:dict(color=[.204,.239,.245],roughness=.54,metallic=.36),
 GLASS:dict(color=[.347,.443,.457],roughness=.29,metallic=.34),SHOP:dict(color=[.267,.332,.322],roughness=.36,metallic=.20),
 BRONZE:dict(color=[.388,.357,.28],roughness=.58,metallic=.26),BASE:dict(color=[.536,.551,.526],roughness=.89),
 ROOF:dict(color=[.508,.497,.456],roughness=.94),CUT:dict(color=[.614,.587,.535],roughness=.95)}
# Front follows the five actual ground edges, projected from OSM w1199798135.
# Ends return short of the adjacent property's nominal shared line.
FRONT=np.array([[-29.16,3.56],[-16.34,-5.22],[-6.674,0],[6.674,0],[18.25,-6.88],[27.29,-.70]])
FRONT[0]+=(FRONT[1]-FRONT[0])/np.linalg.norm(FRONT[1]-FRONT[0])*1.16
FRONT[-1]+=(FRONT[-2]-FRONT[-1])/np.linalg.norm(FRONT[-2]-FRONT[-1])*.7
FLOOR=3.10
SHOP_HEIGHT=4.08
WING_ROOF=29.54
TOWER_ROOF=38.82
SECTIONS=('Nanjing Road wing','south return','central high front','north return','Taixing Road wing')


def inset_front(depth):
    vectors=np.diff(FRONT,axis=0)
    vectors/=np.linalg.norm(vectors,axis=1)[:,None]
    normals=np.column_stack([-vectors[:,1],vectors[:,0]])
    out=[FRONT[0]+depth*normals[0]]
    for i in range(1,len(FRONT)-1):
        displacement=np.linalg.solve(np.array([normals[i-1],normals[i]]),[depth,depth])
        out.append(FRONT[i]+displacement)
    out.append(FRONT[-1]+depth*normals[-1])
    return np.array(out)


def plan_parts(depth=4.48):
    back=inset_front(depth)
    return [Polygon([a,b,back[i+1],back[i]]) for i,(a,b) in enumerate(zip(FRONT,FRONT[1:]))]


def slab(b,polygon,low,high,material,label):
    b.prism(polygon,low,high,lambda x,y,z:(x,y,z),material,label)


def panel(f,x0,x1,z0,z1,back,front,material,label):
    f.prism(box(x0,z0,x1,z1),back,front,material,label)


def sash(f,window,columns,rows,low,material=GLASS):
    x0,z0,x1,z1=window.bounds
    f.prism(window.buffer(.012,join_style=2),-.30,-.27,material,'recessed glazing')
    edge=window.difference(window.buffer(-.075,join_style=2))
    bars=[edge]
    for i in range(1,columns):
        x=x0+(x1-x0)*i/columns
        bars.append(box(x-.026,z0,x+.026,z1))
    for j in range(1,rows):
        z=z0+(z1-z0)*j/rows
        bars.append(box(x0,z-.024,x1,z+.024))
    f.prism(unary_union(bars),-.20,-.13,IRON if material==GLASS else BRONZE,'steel sash and mullions')
    if not low and material==GLASS:
        f.box((x0+x1)/2,z0-.035,x1-x0+.09,.067,.13,-.002,CORNICE,'projecting sill')


def shops(f,low):
    side=f.length/2
    count=max(2,round(f.length/3.7));step=(f.length-.84)/count
    holes=[]
    for n in range(count):
        mid=-side+.42+(n+.5)*step
        h=box(mid-step*.41,.20,mid+step*.41,3.01)
        sash(f,h,3,2,low,SHOP)
        holes.append(h)
    panelshape=box(-side,0,side,SHOP_HEIGHT).difference(unary_union(holes))
    f.prism(panelshape,-.45,0,BASE,'street piers and shop lintels')
    panel(f,-side,side,3.20,3.82,-.1,.12,CORNICE,'shop fascia')
    panel(f,-side,side,3.87,4.01,-.1,.18,LIP,'continuous storey edge')


def banded_wing(f,low):
    side=f.length/2
    count=4 if f.length>13.5 else 3
    step=(f.length-.75)/count
    for r in range(8):
        bottom=SHOP_HEIGHT+r*FLOOR
        sill=bottom+.48;head=bottom+2.24
        holes=[box(-side+.375+(i+.5)*step-step*.40,sill,
                   -side+.375+(i+.5)*step+step*.40,head) for i in range(count)]
        for win in holes:sash(f,win,3 if low else 4,2 if low else 3,low)
        if r==0:
            f.prism(box(-side,bottom,side,bottom+FLOOR).difference(unary_union(holes)),-.42,0,PLASTER,'first floor pale facing')
        else:
            panel(f,-side,side,bottom,sill,-.42,0,PLASTER,'continuous pale spandrels')
            band=box(-side,sill,side,head).difference(unary_union(holes))
            f.prism(band,-.42,0,TILE,'umber tile strips at windows')
            panel(f,-side,side,head,bottom+FLOOR,-.42,0,PLASTER,'continuous pale spandrels')
            if not low:
                # Mortar coursing is visible between the coplanar glazed openings.
                joints=[]
                for j in range(1,8):
                    z=sill+(head-sill)*j/8
                    joints.append(box(-side,z-.009,side,z+.009))
                detail=unary_union(joints).intersection(band)
                f.prism(detail,.001,.008,JOINT,'tile course joints')
    panel(f,-side,side,SHOP_HEIGHT+8*FLOOR,WING_ROOF,-.42,.02,CORNICE,'wing cornice backing')
    for z in np.linspace(WING_ROOF-.78,WING_ROOF-.08,4):
        panel(f,-side-.022,side+.022,z,z+.065,-.05,.17,LIP,'horizontal cornice blades')


def central_tower(f,low):
    side=f.length/2
    slots=(-1.74,-.87,0,.87,1.74)
    win=[]
    for r in range(11):
        z=SHOP_HEIGHT+r*FLOOR
        for x in (-4.57,4.57):
            window=box(x-1.36,z+.53,x+1.36,z+2.29)
            sash(f,window,3 if low else 4,2 if low else 3,low)
            win.append(window)
        for left,right in zip(slots,slots[1:]):
            hole=box(left+.09,z+.44,right-.09,z+2.42)
            sash(f,hole,2 if not low else 1,2,low)
            win.append(hole)
    f.prism(box(-side,SHOP_HEIGHT,side,TOWER_ROOF).difference(unary_union(win)),-.54,0,PLASTER,'recessed central tower')
    # The four narrow window lanes retain dark panels between their successive sashes.
    for r in range(10):
        base=SHOP_HEIGHT+r*FLOOR
        for left,right in zip(slots,slots[1:]):
            panel(f,left+.105,right-.105,base+2.43,base+FLOOR+.43,-.02,.028,TILE,'vertical dark spandrel lanes')
    for i,x in enumerate(slots):
        panel(f,x-.105,x+.105,SHOP_HEIGHT,TOWER_ROOF-.85,-.12,.19,LIP,'five full-height uprights')
        panel(f,x-.12,x+.12,TOWER_ROOF-9.35,TOWER_ROOF+.65,-.09,.55,CORNICE,'upper fin projections')
        for z,depth in [(TOWER_ROOF-9.57,.29),(TOWER_ROOF-9.44,.43)]:
            panel(f,x-.18,x+.18,z,z+.14,-.13,depth,LIP,'stepped corbels under the fins')
        # Each blade slopes up toward the back as visible against the skyline.
        yz=Polygon([[-.58,TOWER_ROOF+.23],[.54,TOWER_ROOF+.23],[.54,TOWER_ROOF+.79],[-.58,TOWER_ROOF+1.58]])
        f.builder.prism(yz,-x-.112,-x+.112,lambda d,z,u:f.point(-u,z,d),LIP,'five sloped parapet blades')
    for z in np.linspace(TOWER_ROOF-1.02,TOWER_ROOF-.08,5):
        panel(f,-side-.025,side+.025,z,z+.086,.01,.228,LIP,'tower horizontal cornice blades')
    panel(f,-2.85,2.85,TOWER_ROOF-.04,TOWER_ROOF+.71,-.45,.09,CORNICE,'setback crown panel')
    for z in (TOWER_ROOF+.11,TOWER_ROOF+.36,TOWER_ROOF+.59):
        panel(f,-2.85,2.85,z,z+.057,.09,.18,LIP,'smaller crown mouldings')


def make_front(b,low):
    parts=plan_parts();back=inset_front(4.48)
    for i,part in enumerate(parts):
        f=Facade(b,FRONT[i],FRONT[i+1],SECTIONS[i])
        cap=TOWER_ROOF if i==2 else WING_ROOF
        shops(f,low)
        if i==2:central_tower(f,low)
        else:banded_wing(f,low)
        slab(b,part,0,.14,BASE,SECTIONS[i]+'/floor')
        slab(b,part,cap-.18,cap,ROOF,SECTIONS[i]+'/roof strip')
        ret=Facade(b,back[i+1],back[i],SECTIONS[i]+'/cut')
        ret.wall(.12,cap,thickness=.18,material=CUT)
    for i in (0,len(FRONT)-1):
        f=Facade(b,back[i],FRONT[i],'Nanjing Road end') if i==0 else Facade(b,FRONT[i],back[i],'Taixing Road end')
        f.wall(.12,WING_ROOF,thickness=.18,material=CUT)
    # At the two stepped shoulders the central volume stands three levels above the wings.
    for side in (2,3):
        f=Facade(b,back[side],FRONT[side],'high southern return') if side==2 else Facade(b,FRONT[side],back[side],'high northern return')
        holes=[]
        for r in range(3):
            z=WING_ROOF+.54+r*FLOOR
            q=box(-.61,z,.61,z+1.67);sash(f,q,2,2 if low else 3,low);holes.append(q)
        f.prism(box(-f.length/2,WING_ROOF,f.length/2,TOWER_ROOF).difference(unary_union(holes)),-.32,0,PLASTER,'upper side windows')
        for z in np.linspace(TOWER_ROOF-1.02,TOWER_ROOF-.08,5):
            panel(f,-f.length/2,f.length/2,z,z+.086,-.01,.16,LIP,'cornice on upper return')
