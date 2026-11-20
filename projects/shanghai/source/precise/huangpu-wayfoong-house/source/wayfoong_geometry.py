"""West street elevation and bounded roof of Wayfoong House, 210–220 Middle Sichuan Road."""
from math import cos, pi, sin
from shapely.geometry import Polygon, box
from shapely.ops import unary_union
from photo_architecture import Facade

WALL="warm grey mineral facing"
RUST="greyer rusticated wings"
CUT="cut light stone"
SHADE="underside of stone"
GLASS="smoky window glass"
SASH="dark painted steel"
IRON="embossed cast iron"
ROOF="flat parapet roof"
BACK="rear plaster"
PALETTE={
    WALL:{"color":[.535,.484,.420],"roughness":.87},
    RUST:{"color":[.463,.417,.368],"roughness":.90},
    CUT:{"color":[.636,.57,.478],"roughness":.79},
    SHADE:{"color":[.384,.341,.288],"roughness":.88},
    GLASS:{"color":[.139,.170,.168],"roughness":.29,"metallic":.16},
    SASH:{"color":[.205,.212,.191],"roughness":.49,"metallic":.29},
    IRON:{"color":[.158,.177,.160],"roughness":.60,"metallic":.46},
    ROOF:{"color":[.395,.394,.352],"roughness":.92},
    BACK:{"color":[.490,.472,.428],"roughness":.92}}
HALF=20.46
WING_CENTER=17.58
PITCH=5.91
COURSES=(8.48,12.50,16.52,20.54)
ATTIC=31.84
CROWN=35.53
CORNICE=25.25


def sash(f,openings,depth,low,wide=False):
    bars=[]
    for shape,cols,rows in openings:
        l,z,r,t=shape.bounds
        rim=shape.buffer(-.068,join_style="mitre")
        mullions=[box(l+(r-l)*n/cols-.033,z,l+(r-l)*n/cols+.033,t) for n in range(1,cols)]
        for split in rows:
            v=z+(t-z)*split
            mullions.append(box(l,v-.036,r,v+.036))
        bars.append(shape.difference(rim.difference(unary_union(mullions))))
    if not openings:return
    shapes=unary_union([v[0].buffer(.018,join_style="mitre") for v in openings])
    f.prism(shapes,-depth-.033,-depth,GLASS,"glazing within the reveals")
    f.prism(unary_union(bars),-depth+.008,-depth+.064,SASH,"steel frames and opening lights")


def relief(f,x,z,w,h,low):
    """Dark cast panels with raised border, standing lozenge and central rosette."""
    panel=box(x-w/2,z-h/2,x+w/2,z+h/2)
    f.prism(panel,.084,.136,IRON,"cast spandrel")
    ring=panel.difference(panel.buffer(-.065,join_style="mitre"))
    diamond=Polygon([(x-w*.35,z),(x,z+h*.31),(x+w*.35,z),(x,z-h*.31)])
    filigree=[ring,diamond.boundary.buffer(.026,join_style="mitre")]
    if not low:
        for off in [-.23,0,.23]:
            width=.14*w if off else .095*w
            flower=Polygon([(x+off*w+width*(.66+.3*cos(4*t))*cos(t),
                             z+h*.29*(.72+.27*cos(4*t))*sin(t)) for t in (k*pi/16 for k in range(32))])
            filigree.append(flower.boundary.buffer(.022))
    f.prism(unary_union(filigree),.14,.185,SASH,"diamond and floral ironwork")


def portal(f,x,low):
    # Open rectangular door under a projecting frieze, with real stone return and inset door leaf.
    w=2.84;h=3.54
    for u in [x-w/2-.20,x+w/2+.20]:
        for side,d,hgt in [(0,.42,3.9),(-.01,.54,.20)]:
            f.box(u+side,hgt/2,.32 if hgt>1 else .50,hgt,d,.06,CUT,"entrance jamb and plinth")
    for z,wid,hgt,d in [(3.85,3.64,.28,.37),(4.07,3.81,.17,.49),(4.22,3.98,.13,.58)]:
        f.box(x,z,wid,hgt,d,.10,CUT,"entrance doorhead")
    f.box(x,.06,3.16,.12,.66,.12,RUST,"entrance threshold")
    return box(x-w/2,.12,x+w/2,h)


def street(builder,low):
    f=Facade(builder,(-HALF,0),(HALF,0),"Middle Sichuan Road")
    groups=[PITCH*k for k in range(-2,3)]
    upper=[];base=[];doors=[];bottom_open=[];central_open=[];wing_open=[]
    # The five middle bays each have three narrow openings at each ordinary and upper attic storey.
    for x in groups:
        for floor,z in enumerate(COURSES):
            for dx in [-1.54,0.,1.54]:
                shape=box(x+dx-.543,z+.33,x+dx+.543,z+2.82)
                upper.append((shape,1,[.67]));central_open.append(shape)
        for z,hh in [(25.84,2.18),(28.74,2.41)]:
            for dx in [-1.54,0.,1.54]:
                shape=box(x+dx-.53,z,x+dx+.53,z+hh)
                upper.append((shape,1,[.67]));central_open.append(shape)
        shop=box(x-1.94,.27,x+1.94,3.14)
        over=box(x-1.94,5.17,x+1.94,7.30)
        base.extend([(shop,2 if low else 3,[.73]),(over,3,[.66])]);bottom_open.extend([shop,over])
        relief(f,x,4.17,3.85,1.55,low)
    for side in [-1,1]:
        x=side*WING_CENTER
        shape=portal(f,x,low);doors.append((shape,2,[.77]));bottom_open.append(shape)
        shape=box(x-1.10,5.13,x+1.10,7.22);base.append((shape,2,[.68]));bottom_open.append(shape)
        for z in COURSES:
            shape=box(x-1.18,z+.36,x+1.18,z+2.53)
            upper.append((shape,2,[.68]));wing_open.append(shape)
            relief(f,x,z+3.23,2.42,.99,low)
    central=box(-14.81,8.06,14.81,CORNICE-.25).difference(unary_union(central_open))
    f.prism(central,-.395,0,WALL,"four-storey triple window field")
    wings=unary_union([box(-HALF,8.06,-14.81,CORNICE-.25),box(14.81,8.06,HALF,CORNICE-.25)])
    f.prism(wings.difference(unary_union(wing_open)),-.37,.030,RUST,"paired rusticated end bays")
    f.prism(box(-HALF,0,HALF,8.06).difference(unary_union(bottom_open)),-.40,.030,RUST,"two-storey rusticated pedestal")
    # Shallow projecting courses leave the mortar grooves in shadow. Window voids stay open.
    rust=unary_union([wings,box(-HALF,0,HALF,8.06)]).difference(unary_union(wing_open+bottom_open))
    layers=[]
    for n in range(34):
        z=.29+n*.747
        parts=box(-HALF+.05,z,HALF-.05,z+.694).intersection(rust)
        if not parts.is_empty:layers.append(parts)
    f.prism(unary_union(layers),.033,.081,RUST,"horizontal rustication")
    stools=[]
    for op,_,_ in upper:
        x0,z0,x1,_=op.bounds
        if z0<25:stools.append(box(x0-.068,z0-.118,x1+.068,z0-.018))
    f.prism(unary_union(stools),.033,.17,CUT,"individual stone window stools")
    for x in [-14.81,-8.87,-2.96,2.96,8.87,14.81]:
        f.box(x,16.54,.34,16.43,.13,.035,WALL,"engaged wall pier")
        f.box(x,24.52,.51,.29,.25,.059,CUT,"pier capital")
    for h,t,d in [(7.73,.13,.29),(7.96,.24,.45),(8.15,.10,.42),(24.65,.18,.33),(24.89,.30,.61),(25.22,.29,.88),(25.44,.14,.94)]:
        f.beam(h,t,d,CUT,width=HALF*2+.04,label="sill and main projecting cornice")
    for k in range(-25,26):
        f.box(k*.79,24.76,.34,.46,.87,.31,SHADE,"cornice modillion")
        if not low:f.box(k*.79,24.91,.44,.13,.98,.31,CUT,"modillion abacus")
    # Front attic lies slightly behind the main cornice; its two end towers rise above the central parapet.
    af=Facade(builder,(-HALF,.52),(HALF,.52),"Upper front")
    attic_holes=[op for op,_,_ in upper if op.bounds[1]>=25]
    central_width=14.81
    af.prism(box(-central_width,25.30,central_width,ATTIC).difference(unary_union(attic_holes)),-.32,0,WALL,"upper two-storey centre")
    for x in [-WING_CENTER,WING_CENTER]:
        top=[]
        for z,h in [(25.69,1.92),(28.36,2.13),(32.13,2.04)]:
            op=box(x-.96,z,x+.96,z+h);top.append((op,2,[.69]))
        af.prism(box(x-2.88,25.30,x+2.88,CROWN).difference(unary_union([v[0] for v in top])),-.35,0,RUST,"raised square end pavilion")
        sash(af,top,.36,low)
        for z,w,h in [(25.86,3.64,.17),(31.38,2.73,.16),(35.29,5.72,.17)]:
            af.box(x,z,w,h,.20,.07,CUT,"raised pavilion edging")
    sash(f,[v for v in upper if v[0].bounds[1]<25],.42,low)
    sash(af,[v for v in upper if v[0].bounds[1]>=25],.345,low)
    sash(f,base,.43,low);sash(f,doors,.87,low)
    af.box(0,ATTIC,29.66,.16,.35,0,CUT,"central parapet cap")


def closed_block(builder,ring,z0,z1,material,label,skip=()):
    for i,(a,b) in enumerate(zip(ring,ring[1:]+ring[:1])):
        if i in skip:continue
        f=Facade(builder,a,b,label)
        f.prism(box(-f.length/2,z0,f.length/2,z1),-.18,0,material,label)
    builder.plan_prism(Polygon(ring),z1-.16,z1,ROOF,label+" roof")


def make_house(builder,low=False):
    street(builder,low)
    # Street wing, two deep light wells and a lower rear bar are the recurring roof divisions
    # in the three aerial releases. Hidden service doors, plant and interiors are unrecorded.
    ring=[(-HALF,0),(HALF,0),(20.48,29.01),(-20.31,29.47)]
    builder.plan_prism(Polygon(ring),0,.16,RUST,"street and service-wing base")
    closed_block(builder,ring,.14,8.03,BACK,"rear podium",(0,))
    front=[(-HALF,0),(HALF,0),(HALF,10.4),(-HALF,10.4)]
    closed_block(builder,front,8.04,25.35,BACK,"front wing side and rear",(0,))
    central=[(-14.70,.52),(14.70,.52),(14.70,9.32),(-14.70,9.32)]
    closed_block(builder,central,25.28,ATTIC-.13,BACK,"central attic",(0,))
    for a,b in [(-HALF,-14.70),(14.70,HALF)]:
        closed_block(builder,[(a,.52),(b,.52),(b,8.55),(a,8.55)],25.27,CROWN-.10,BACK,"end pavilion",(0,))
    # All clerestory/court depths are approximate; both voids have an actual lowered floor and full returns.
    for first,last,top in [(-20.29,-13.05,24.1),(-2.69,.93,24.1),(12.27,20.44,24.1)]:
        closed_block(builder,[(first,10.40),(last,10.40),(last,23.21),(first,23.21)],8.04,top,BACK,"light well return",(0,))
    rear=[(-20.29,23.21),(20.45,23.21),(20.46,29.00),(-20.30,29.45)]
    closed_block(builder,rear,8.04,21.58,BACK,"eastern service range")
    for y,z,w in [(10.31,25.43,40.65),(9.21,ATTIC,29.38)]:
        builder.box((0,y,z),(w,.23,.21),CUT,label="rear edge parapet")
