"""North street range, northeast cut corner and first east bay, in metres.

The origin is the centre of the frozen 43.429 m north edge. X runs along the
street towards its west end. Positive Y points into the block. The additional
east bay stops at the light-coloured long-window field of the Huqiu elevation.
"""
from shapely.geometry import Point, Polygon, box
from shapely.ops import unary_union
from photo_architecture import Facade, opening

BRICK = 'rose horizontal brickwork'
TRIM = 'rose sandstone mouldings'
WHITE = 'cream stucco long window field'
SHADOW = 'recessed brick joints'
LIGHT = 'muted blue glazing'
DARK = 'charcoal metal sash'
PANEL = 'dark pressed spandrel'
LINTEL = 'light weathered stone'
ROOF = 'grey roof covering'
DOOR = 'dark green door metal'
PALETTE = {
    BRICK: dict(color=[.674,.493,.422],roughness=.91),
    TRIM: dict(color=[.727,.569,.493],roughness=.84),
    WHITE: dict(color=[.916,.881,.781],roughness=.90),
    SHADOW: dict(color=[.449,.326,.281],roughness=.93),
    LIGHT: dict(color=[.290,.367,.374],roughness=.37,metallic=.18),
    DARK: dict(color=[.173,.172,.158],roughness=.62,metallic=.27),
    PANEL: dict(color=[.173,.189,.197],roughness=.60,metallic=.21),
    LINTEL: dict(color=[.745,.691,.591],roughness=.83),
    ROOF: dict(color=[.427,.425,.389],roughness=.84),
    DOOR: dict(color=[.183,.267,.240],roughness=.60,metallic=.26),
}
NORTH_EAST = (-18.38,0.0)
EAST_NORTH = (-21.61,3.23)
WEST = (21.52,0.0)
EAST_STOP = (-21.55,8.75)
DEPTH = 3.22
GROUND = 4.37
ARCH_SILL = 5.03
UPPER = 14.28
CORNICE = 17.28
ATTIC = 19.16
WING_WIDTH = 5.16
OUTLINE = Polygon([EAST_STOP,EAST_NORTH,NORTH_EAST,WEST,(WEST[0],DEPTH),
                   (-16.97,DEPTH),(-18.45,4.70),(-18.43,EAST_STOP[1])])


def skin(f,hole,material,depth=-.29):
    f.prism(hole.buffer(.013,join_style=2),depth-.015,depth,material,'set back panes')


def square_lights(f,axis,z,width,height,material=LIGHT,transom=True):
    hole=box(axis-width/2,z,axis+width/2,z+height)
    skin(f,hole,material)
    inside=hole.buffer(-.050,join_style=2)
    f.prism(hole.difference(inside),-.232,-.174,DARK,'recessed sash')
    if transom:
        f.box(axis,z+height*.70,width-.083,.045,.045,-.185,DARK,'transoms')
    return hole


def long_arch(f,u,lod):
    width=1.96
    top=13.43
    rise=1.04
    arch=opening(u,ARCH_SILL,width,top-ARCH_SILL,rise,12 if lod else 28)
    skin(f,arch,LIGHT)
    trim=opening(u,ARCH_SILL-.06,width+.62,top-ARCH_SILL+.40,rise+.26,12 if lod else 28)
    f.prism(trim.difference(arch),.003,.115,TRIM,'long arched stone surrounds')
    f.prism(arch.difference(arch.buffer(-.087,join_style=2)),-.222,-.138,DARK,'arched frame')
    coords=[(u-.19,top+.20),(u-.23,top+.64),(u+.23,top+.64),(u+.19,top+.20)]
    f.prism(Polygon(coords),.090,.190,TRIM,'projecting keystones')
    for dx in [-.45,.45]:
        f.box(u+dx,ARCH_SILL+1.43,.057,2.82,.055,-.171,DARK,'lower three light sash')
        f.box(u+dx,11.21,.054,1.98,.060,-.166,DARK,'upper three light sash')
    f.box(u,6.74,width-.12,.072,.07,-.157,DARK,'lower transoms')
    f.box(u,9.24,width-.13,2.12,.10,-.163,PANEL,'opaque storey spandrels')
    for z in (8.15,10.32):
        f.box(u,z,width-.074,.095,.09,-.142,DARK,'spandrel rails')
    if not lod:
        for z in [8.50,9.87]:
            f.box(u,z,width-.19,.034,.035,-.104,PANEL,'pressed horizontal panel edges')
    circle=Point(u,12.22).buffer(.40,quad_segs=6 if lod else 12)
    f.prism(circle.difference(circle.buffer(-.053)),-.176,-.123,DARK,'round fanlight sash')
    for s in [-1,1]:
        f.box(u+.67*s,12.23,.53,.054,.040,-.153,DARK,'fanlight spring bars')
    f.box(u,ARCH_SILL-.080,width+.37,.12,.36,.055,TRIM,'individual sills')
    return arch


def stone_joint(f,holes,start,stop,spacing):
    cut=unary_union(holes).buffer(.055,join_style=2)
    z=start
    while z<stop:
        joint=box(-f.length/2+.012,z-.014,f.length/2-.012,z+.014).difference(cut)
        f.prism(joint,.001,.011,SHADOW,'horizontal rustication')
        z+=spacing


def arched_door(f,lod):
    width=min(f.length*.49,2.55);top=3.70
    arch=opening(0,.035,width,top,1.03,12 if lod else 24)
    skin(f,arch,DOOR,-.41)
    inner=arch.buffer(-.071,join_style=2)
    f.prism(arch.difference(inner),-.28,-.18,DARK,'deep door reveal frame')
    f.box(0,1.438,.050,2.78,.06,-.325,DARK,'meeting stile')
    f.box(0,2.91,width-.15,.071,.06,-.325,DARK,'door transom')
    for dx in [-.09,.09]:
        f.box(dx,1.20,.025,.29,.11,-.297,LINTEL,'metal pulls')
    ring=opening(0,.035,width+.26,top+.137,1.15,12 if lod else 24).difference(arch)
    f.prism(ring,.002,.088,TRIM,'ground arch surrounds')
    f.prism(Polygon([(-.20,3.88),(-.27,4.17),(.27,4.17),(.20,3.88)]),.03,.206,TRIM,'entrance keystone')
    for s in [-1,1]:
        f.line((s*width*.42,3.30,.09),(s*(width*.72),3.76,.09),.035,SHADOW,4,'radiating brick joint')
    return arch


def belt(f,openings):
    base=box(-f.length/2,.024,f.length/2,.27).difference(unary_union(openings))
    f.prism(base,-.072,.134,TRIM,'interrupted street plinth')
    for z,height,depth,d,mat in [
        (3.38,.095,.23,.055,TRIM),
        (GROUND,.19,.39,.080,TRIM),(4.58,.115,.53,.12,LINTEL),
        (4.71,.11,.42,.075,TRIM),(UPPER-.08,.11,.31,.08,TRIM),
        (UPPER+.04,.09,.43,.13,TRIM),(CORNICE-.19,.16,.36,.07,TRIM),
        (CORNICE+.06,.19,.58,.15,BRICK),(CORNICE+.25,.12,1.02,.30,TRIM),
        (CORNICE+.37,.10,1.09,.31,TRIM)]:
        f.box(0,z,f.length+.015,height,depth,d,mat,'horizontal mouldings')



def west_door(f,lod):
    # At the west end the door has a flat head. The surrounding blocked arch
    # is readable as radial brick joints beside a separate small fixed opening.
    door=box(-.93,.04,.44,3.13)
    skin(f,door,DOOR,-.41)
    f.prism(door.difference(door.buffer(-.063,join_style=2)),-.28,-.18,DARK,'straight headed door jambs')
    for s in (-1,1):
        f.line((-.25+s*.72,3.11,.024),(-.25+s*1.40,3.69,.024),.031,SHADOW,4,'flat head brick joint')
    return [door,square_lights(f,1.13,2.12,.54,.74,transom=False)]


def narrow_wing(f,lod,west=False):
    doors=west_door(f,lod) if west else [arched_door(f,lod)]
    holes=list(doors)
    for z,h in [(5.08,2.81),(9.32,3.18)]:
        for x in (-.89,0,.89):
            holes.append(square_lights(f,x,z,.534,h,transom=False))
        f.box(0,z-.08,2.62,.12,.28,.02,TRIM,'three window ledge')
    f.wall(.025,UPPER,holes,.36,BRICK)
    # Brick grooving clusters on each side of the smooth vertical window panel.
    slit=[*holes,box(-1.33,4.96,1.33,UPPER)]
    stone_joint(f,slit,4.99,14.12,.55)
    stone_joint(f,doors,.46,4.31,.51)
    return doors


def shop_bay(f,index,u,pitch,lod):
    w=pitch-.77
    short_window=index in (4,6)
    entry=index==5
    bottom=1.49 if short_window else (.08 if entry else .27)
    top=3.16
    hole=box(u-w/2,bottom,u+w/2,top)
    skin(f,hole,DOOR if entry else LIGHT,-.59 if entry else -.35)
    depth=-.42 if entry else -.215
    f.prism(hole.difference(hole.buffer(-.077,join_style=2)),depth-.03,depth+.03,DARK,'shop surround')
    if short_window:
        for dx in [-.28,0,.28]:
            f.box(u+dx*w,(top+bottom)/2,.055,top-bottom-.12,.075,-.255,DARK,'high storefront lights')
        f.box(u,bottom-.06,w+.06,.12,.27,.018,TRIM,'remaining masonry window sill')
    elif entry:
        f.box(u,1.58,.063,2.90,.07,-.508,DARK,'recessed double door stile')
    else:
        f.box(u,.385,w-.15,.16,.076,-.229,PANEL,'shop kick panels')
    for dx in (-.34,0,.34):
        x=u+dx*pitch*.50
        vent=box(x-.105,3.72,x+.105,4.22);skin(f,vent,PANEL,-.16)
        if not lod:f.box(x,3.97,.025,.47,.04,-.092,DARK,'small upper vent bars')
        yield vent
    yield hole


def street_range(f,lod):
    pitch=f.length/7
    ground=[];arches=[]
    for i in range(7):
        x=(i-3)*pitch
        ground.extend(shop_bay(f,i,x,pitch,lod))
        arches.append(long_arch(f,x,lod))
    f.wall(.025,GROUND,ground,.34,BRICK)
    stone_joint(f,ground,.46,3.48,.51)
    f.wall(GROUND,UPPER,arches,.34,WHITE)
    return ground


def crown(f,axes,lod,corners,openings):
    holes=[]
    for x in axes:
        for dx in [-.61,.61]:
            holes.append(square_lights(f,x+dx,UPPER+.34,.90,2.07))
        if f.length>10 and x<axes[-1]-.1:
            half=(axes[1]-axes[0])*.5
            panel=box(x+half-.68,UPPER+.48,x+half+.68,CORNICE-.64)
            f.prism(panel.difference(panel.buffer(-.045,join_style=2)),.005,.059,TRIM,'square attic panels')
    if len(axes)==1:
        for s in [-1,1]:
            x=s*(f.length*.25+.49)
            w=max(.26,min(f.length*.18,.82))
            panel=box(x-w/2,UPPER+.47,x+w/2,CORNICE-.62)
            f.prism(panel.difference(panel.buffer(-.040,join_style=2)),.005,.053,TRIM,'recessed end panels')
    f.wall(UPPER,CORNICE,holes,.32,BRICK);belt(f,openings)
    count=max(3,round(f.length/.90))
    bracket=Polygon([(0,0),(.13,0),(.19,.085),(.31,.15),(.37,.29),(.46,.36),(.46,.45),(0,.45)])
    for i in range(count):
        x=f.length*((i+.5)/count-.5)
        f.builder.prism(bracket,-.096,.096,lambda d,z,w:f.point(x-w,CORNICE-.21+z,d+.045),TRIM,f.label+'/cornice brackets')
    # A fifth storey is visible above the main cornice, set back behind it.
    a=corners[tuple(f.a[:2])];b=corners[tuple(f.b[:2])]
    attic=Facade(f.builder,a,b,f.label+'/upper setback')
    aps=[]
    for axis in axes:
        x = (f.point(axis,0,-.80)[:2]-attic.center[:2]) @ attic.t[:2]
        for dx in [-.42,.42]:
            aps.append(square_lights(attic,x+dx,17.81,.61,.89))
    attic.wall(CORNICE+.28,ATTIC,aps,.27,BRICK)
    attic.box(0,ATTIC+.015,attic.length+.09,.15,.69,.13,TRIM,'thin upper coping')


def make_front(b,lod):
    left=NORTH_EAST[0];right=WEST[0]
    inner_l=(left+WING_WIDTH,0);inner_r=(right-WING_WIDTH,0)
    # Mitre the setback plane around the two real changes of direction.
    # Stretch the end strips to the cut section so each roof rim joins.
    setback=OUTLINE.buffer(-.80,join_style=2)
    candidates=list(setback.exterior.coords)[:-1]
    corners={p:min(candidates,key=lambda v:(p[0]-v[0])**2+(p[1]-v[1])**2)for p in (EAST_STOP,EAST_NORTH,NORTH_EAST,WEST)}
    corners.update({p:(p[0],.80)for p in (inner_l,inner_r)})
    long=Facade(b,inner_l,inner_r,'north/seven arched bays')
    ground=street_range(long,lod)
    crown(long,[(i-3)*long.length/7 for i in range(7)],lod,corners,ground)
    for a,c,name in [(EAST_STOP,EAST_NORTH,'Huqiu/first narrow bay'),
                     (EAST_NORTH,NORTH_EAST,'northeast/cut corner'),
                     (NORTH_EAST,inner_l,'north/east narrow bay'),
                     (inner_r,WEST,'north/west narrow bay')]:
        f=Facade(b,a,c,name)
        ground=narrow_wing(f,lod,west=c==WEST)
        crown(f,[0.],lod,corners,ground)
    ring=list(OUTLINE.exterior.coords)
    inner=list(setback.exterior.coords)[:-1]
    # Published photographs show the attic only from the street; the rear here is a
    # plain section surface, aligned to the surviving city's extruded building.
    for a,c in zip(ring[3:-1],ring[4:]):
        Facade(b,a,c,'section/back and returns').wall(.025,CORNICE+.24,(),.15,BRICK)
        aa=min(inner,key=lambda v:(a[0]-v[0])**2+(a[1]-v[1])**2)
        cc=min(inner,key=lambda v:(c[0]-v[0])**2+(c[1]-v[1])**2)
        if aa!=cc:
            Facade(b,aa,cc,'section/attic closure').wall(CORNICE+.24,ATTIC,(),.15,BRICK)
    b.plan_prism(OUTLINE,CORNICE+.21,CORNICE+.31,ROOF,'roof/cornice ledge')
    setback=OUTLINE.buffer(-.66,join_style=2)
    b.plan_prism(setback,ATTIC-.12,ATTIC+.015,ROOF,'roof/setback street strip')
    b.plan_prism(OUTLINE,.018,.048,TRIM,'street/closed section floor')
