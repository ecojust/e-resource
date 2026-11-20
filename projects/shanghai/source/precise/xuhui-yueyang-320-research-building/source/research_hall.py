"""East exterior, seven-arch loggia and the two open courts of the former research building."""
from math import pi, sin, cos
import numpy as np
from shapely.geometry import box, Polygon, LineString
from shapely.ops import unary_union
from photo_architecture import Facade, opening

BRICK='brown vertical face brick'
RIB='light ochre rib stone'
SILL='brown stone sill'
GLASS='grey window glass'
SASH='dark window sash'
ROOF='weathered roof finish'
BAND='brick header courses'
LIGHT_BRICK='pale brown fired brick'
STONE='ochre portico stone'
SHADE='entry in shadow'
STEP='grey granite step'
DOOR='dark entrance door'
PALETTE={label:{'color':rgb,'roughness':rough,'metallic':metal}for label,rgb,rough,metal in [
    (BRICK,[.445,.335,.270],.88,0),(RIB,[.57,.467,.361],.83,0),(SILL,[.454,.368,.301],.87,0),
    (GLASS,[.268,.300,.293],.39,.12),(SASH,[.145,.142,.129],.54,.20),(ROOF,[.382,.324,.274],.91,0),
    (LIGHT_BRICK,[.524,.405,.318],.87,0),(BAND,[.381,.279,.233],.87,0),(STONE,[.563,.475,.378],.85,0),(SHADE,[.236,.209,.182],.89,0),
    (STEP,[.458,.430,.385],.87,0),(DOOR,[.188,.170,.145],.69,.12)]}
# X follows the east wall to the north, Y measures west from that wall, Z is altitude.
# Coordinates of the courtyards follow the frozen ring, with sub-metre source noise removed.
COURTS=[Polygon([(-32.67,12.05),(-11.03,11.62),(-10.52,33.77),(-32.67,34.27)]),
        Polygon([(11.20,11.61),(32.42,11.77),(32.68,32.41),(11.04,32.84)])]
EAST=[(-47.56,2.10),(-46.75,.14),(-43.88,-.72),(-40.65,-.12),(-39.43,1.04),
      (-10.48,1.04),(-9.63,-.64),(-7.91,-1.57),(-5.82,-.82),
      (5.82,-.82),(7.91,-1.57),(9.63,-.64),(10.48,1.04),(39.43,1.04),
      (40.65,-.12),(43.88,-.72),(46.75,.14),(47.56,2.10)]
OUTLINE=Polygon([*EAST,(47.81,45.95),(-47.81,46.02)])
BODY=OUTLINE.difference(unary_union(COURTS))
CROWN=23.12
WING=15.07
PORT_WIDTH=17.69
PORT_CENTER=.716
PORT_FRONT=-6.02


def rectangle(mid,z,w,h):
    return box(mid-w/2,z,mid+w/2,z+h)


def window(f,u,z,w,h,paired,lod):
    """Inset panes and iron sashes, with masonry splitting each of the paired lights."""
    gap=.137 if paired else 0
    lights=[(u-w*.25-gap*.25,(w-gap)/2),(u+w*.25+gap*.25,(w-gap)/2)] if paired else [(u,w)]
    openings=[]
    for center,width in lights:
        aperture=rectangle(center,z,width,h)
        openings.append(aperture)
        f.prism(aperture.buffer(.012,join_style=2),-.264,-.241,GLASS,'recessed rectangular glazing')
        rim=aperture.difference(aperture.buffer(-.044,join_style=2))
        bars=[rim,rectangle(center,z+h*.52,width,.041)]
        if not lod:
            bars.extend([rectangle(center,z+h*.25,width,.032),rectangle(center,z+h*.77,width,.032)])
        f.prism(unary_union(bars).intersection(aperture),-.212,-.174,SASH,'iron glazing divisions')
    f.prism(rectangle(u,z-.095,w+.12,.105),-.078,.085,SILL,'thin window sill')
    return openings


def blind_arch(f,u,z,w,lod):
    """A blind brick semicircle rises above the top pair of square-headed windows."""
    radius=w/2
    points=[(u+radius*cos(t),z+radius*sin(t))for t in np.linspace(0,pi,13 if lod else 25)]
    # The tympanum is blind, with upright bricks fanning toward a projecting
    # masonry key. The rectangular iron lights stop at the springing course.
    tympanum=Polygon([(u-radius,z),(u+radius,z),*points[1:-1]])
    spacing=.215 if lod else .135
    light=[];dark=[]
    for index,x in enumerate(np.arange(u-radius+.045,u+radius,spacing)):
        band=box(x,z+.015,x+spacing*.43,z+radius+.01).intersection(tympanum)
        if not band.is_empty:
            (light if index%3 else dark).append(band)
    for pieces,mat in [(light,LIGHT_BRICK),(dark,BAND)]:
        f.prism(unary_union(pieces),.006,.028,mat,'upright fired brick in blind head')
    key=Polygon([(u-.084,z+.038),(u+.084,z+.038),(u+.119,z+.37),(u-.119,z+.37)])
    f.prism(key,.018,.146,RIB,'rectangular key above paired sash')
    f.prism(LineString(points).buffer(.058,cap_style=2),.007,.12,RIB,'brick round head and light outer edging')
    for a in np.linspace(.10,pi-.10,8 if lod else 15):
        inner=radius-.12;outer=radius-.055
        ray=LineString([(u+inner*cos(a),z+inner*sin(a)),(u+outer*cos(a),z+outer*sin(a))])
        f.prism(ray.buffer(.017,cap_style=2),.011,.072,BAND,'recessed arch voussoir')


def vertical_rib(f,u,z0,top,lod):
    w=.38
    f.prism(rectangle(u,z0,w,top-z0),0,.20,RIB,'continuous stepped stone pier')
    f.prism(rectangle(u,z0,w*.42,top-z0+.20),.16,.29,SILL,'front blade of pier')
    f.prism(Polygon([(u-w/2,top),(u,top+.55),(u+w/2,top)]),.02,.24,RIB,'projecting forked pier head')
    if not lod:
        f.prism(rectangle(u,z0+.48,.038,top-z0-.1),.26,.31,RIB,'central pier arris')


def brick_spandrel(f,u,z,w,h,lod):
    if h<.14:
        return
    count=max(2,round(w/(.31 if lod else .16)))
    lines=[rectangle(u-w/2+(i+.5)*w/count,z,.017,h)for i in range(count)]
    f.prism(unary_union(lines),.003,.013,BAND,'upright brickwork in the spandrel')


def wing_entrance(f,u):
    w=2.26
    aperture=Polygon([(u-w/2,.15),(u+w/2,.15),(u+w/2,3.13),(u+.73,3.57),
                      (u,4.21),(u-.73,3.57),(u-w/2,3.13)])
    f.prism(aperture.buffer(.026,join_style=2),-.357,-.337,DOOR,'recessed pointed side entrance')
    f.prism(aperture.buffer(.116,join_style=2).difference(aperture),0,.115,SILL,'pointed entrance archivolt')
    f.prism(rectangle(u,.15,.041,3.26),-.317,-.275,SASH,'side entrance meeting stile')
    return aperture


def east_wall(b,index,lod):
    a,c=EAST[index:index+2]
    center=5<=index<=11
    is_range=index in (4,12)
    is_main=index==8
    top=CROWN if center else WING if is_range else WING+1.11
    f=Facade(b,a,c,'east '+('central crown'if center else 'long wing'if is_range else 'canted end'))
    n=8 if is_range else 3 if is_main else 1
    gap=f.length/n
    us=[-f.length/2+(i+.5)*gap for i in range(n)]
    holes=[]
    for i,u in enumerate(us):
        slim=not (is_main or is_range)
        w=min(gap*.69,2.63) if not slim else min(1.25,gap*.61)
        if not center:
            if is_range and ((index==4 and i==4)or(index==12 and i==3)):
                holes.append(wing_entrance(f,u))
            else:
                holes.extend(window(f,u,1.14,w,2.46,not slim,lod))
        elif is_main and i==1:
            # A central shaded doorway behind the seven arches is visible from Yueyang Road.
            central_door=rectangle(u,.54,2.38,3.52)
            holes.append(central_door)
            f.prism(central_door,-.352,-.330,DOOR,'recessed central doorway')
            f.prism(rectangle(u,.54,.045,3.52),-.311,-.275,SASH,'central entrance meeting stile')
        if center:
            tiers=[(5.58,2.46),(9.62,2.48),(13.66,2.48),(17.72,2.59)]
        else:
            tiers=[(5.46,2.49),(9.77,2.47)]
        for z,h in tiers:
            holes.extend(window(f,u,z,w,h,not slim,lod))
            brick_spandrel(f,u,z+h+.10,w,max(.22,.88 if center else .68),lod)
        if is_range or is_main:
            z,h=tiers[-1];blind_arch(f,u,z+h+.04,w+.12,lod)
        if is_range or is_main:
            vertical_rib(f,u-gap/2+.018,4.11 if center else .61,top+.02,lod)
    f.wall(.0,top,holes,.39,BRICK)
    if is_main:
        for i in range(4):
            u=(i-1.5)*gap
            # In the 2014 street photograph, the shaft carries a small stepped
            # lozenge and two sloping ribs above the third row of paired windows.
            arrow=Polygon([(u-.16,13.72),(u,14.21),(u+.16,13.72),(u+.15,14.25),
                           (u+.07,14.36),(u,14.72),(u-.07,14.36),(u-.15,14.25)])
            f.prism(arrow,.204,.347,RIB,'stepped Gothic pier ornament')
            for sign in [-1,1]:
                arm=LineString([(u,14.25),(u+sign*.18,13.94),(u+sign*.39,13.59)]).buffer(.052,cap_style=2)
                f.prism(arm,.053,.221,RIB,'slender arm of pointed pier ornament')
    if is_range or center:
        f.beam(top-.14,.15,.115,SILL)
    if not is_range:
        vertical_rib(f,f.length/2-.04,5.48 if center else .73,top+.02,lod)


def portico(b,lod):
    half=PORT_WIDTH/2;left=PORT_CENTER-half;right=PORT_CENTER+half
    f=Facade(b,(left,PORT_FRONT),(right,PORT_FRONT),'seven-arch east portico')
    interval=PORT_WIDTH/7;opening_width=interval-.39
    holes=[]
    for i in range(7):
        u=(i-3)*interval
        arch=opening(u,.53,opening_width,3.79,opening_width/2,14 if lod else 26)
        holes.append(arch)
        f.prism(arch.buffer(.063).difference(arch).intersection(box(-half,.65,half,5.23)),
                .006,.125,STONE,'pale voussoir arch ring')
    f.wall(.53,6.16,holes,.57,STONE)
    for i in range(8):
        u=(i-3.5)*interval
        colwidth=.59 if i not in (0,7) else .52
        for z,h,width,depth in [(.52,.22,colwidth+.22,.82),(.74,.17,colwidth+.1,.72),
                                  (3.14,.11,colwidth+.10,.72),(3.25,.14,colwidth+.23,.84),
                                  (3.39,.095,colwidth+.28,.90)]:
            b.box((PORT_CENTER+u,PORT_FRONT+.24,z+h/2),(width,depth,h),STONE,label='square loggia capital and plinth')
        b.box((PORT_CENTER+u,PORT_FRONT+.24,1.99),(colwidth-.14,.57,2.21),STONE,label='square sandstone column')
    b.plan_prism(box(left-.13,PORT_FRONT-.12,right+.13,-.67),5.56,5.71,SHADE,'open loggia ceiling')
    b.plan_prism(box(left-.15,PORT_FRONT-.145,right+.15,-.66),6.04,6.19,SILL,'low portico roof')
    f.beam(6.15,.115,.19,STONE)
    b.plan_prism(box(left-.2,PORT_FRONT-.13,right+.2,-.61),.42,.54,STEP,'portico landing')
    for i in range(4):
        b.plan_prism(box(left-.27,PORT_FRONT-.14-.45*(4-i),right+.27,PORT_FRONT-.13-.45*(3-i)),
                     .015,.135*(i+1),STEP,'four ascending front steps')


def tall_body(b,lod):
    center=Polygon([*EAST[5:13],(10.50,11.55),(-10.52,11.55)])
    # The low wings turn around two separate courts. The photographed east wall
    # carries windows; neutral rear walls preserve the mapped envelope.
    b.plan_prism(BODY,.005,.16,SILL,'historic ground perimeter around two open courts')
    b.plan_prism(BODY,WING-.45,WING-.2,ROOF,'double-court flat roof')
    b.plan_prism(center,CROWN-.41,CROWN-.17,ROOF,'central tower flat roof')
    shell=[(EAST[-1],(47.81,45.95)),((47.81,45.95),(-47.81,46.02)),((-47.81,46.02),EAST[0])]
    for a,c in shell:
        f=Facade(b,a,c,'historic outer wing')
        f.wall(0,WING,(),.28,BRICK)
        f.beam(WING-.15,.15,.075,SILL)
    # The back-facing wall of each court is visible in the district oblique.
    # The opposite sides retain a plain wall without undocumented fenestration.
    for court in COURTS:
        points=list(court.exterior.coords)
        back=max(range(len(points)-1),key=lambda i:(points[i][1]+points[i+1][1])/2)
        for i,(a,c) in enumerate(zip(points,points[1:])):
            f=Facade(b,c,a,'open inner courtyard wall')
            if i==back:
                f=Facade(b,min([a,c]),max([a,c]),'west inner courtyard elevation')
                holes=[]
                width=f.length/5
                for j in range(5):
                    u=-f.length/2+(j+.5)*width
                    for z in [1.21,5.55,9.89]:
                        holes.extend(window(f,u,z,min(2.42,width*.65),2.35,True,lod))
                f.wall(0,WING,holes,.26,BRICK)
            else:
                f.wall(0,WING,(),.20,BRICK)
            f.beam(WING-.13,.13,.055,SILL)
    for x in [-1,1]:
        side=Facade(b,(x*10.48,1.04),(x*10.50,11.55),'central tower side above wing')
        side.wall(WING-.21,CROWN,(),.24,BRICK)
        side.beam(CROWN-.15,.15,.075,SILL)
    Facade(b,(10.50,11.55),(-10.52,11.55),'central tower rear above main wing').wall(WING-.21,CROWN,(),.24,BRICK)
    # Half-height enclosure behind the three center window bays, seen above
    # the east parapet in both photographs. Modern plant and flag are omitted.
    lantern=box(-2.32,7.74,2.32,11.52)
    b.plan_prism(lantern,CROWN-.22,25.84,BRICK,'narrow rectangular roof crown')
    for x in [-2.31,2.31]:
        b.box((x,7.70,24.66),(.22,.34,3.49),RIB,label='two raised crown coping blades')
    b.plan_prism(lantern.buffer(.085,join_style=2),25.84,25.99,SILL,'crown coping')
    for sign in [-1,1]:
        # Corner turrets are recognizable in all three aerial layers and both
        # ends of the district image. The flattened corners follow that view.
        end=Polygon([(sign*u,v)for u,v in [(39.43,1.04),(40.65,-.12),(43.88,-.72),(46.75,.14),
                       (47.56,2.10),(47.56,7.32),(39.43,7.32)]])
        b.plan_prism(end,WING+.91,WING+1.11,ROOF,'front canted corner roof')
        b.plan_prism(end.exterior.buffer(.105,cap_style=2,join_style=2),WING+.985,WING+1.15,SILL,'front turret coping')
        for p0,p1 in [((sign*47.56,2.10),(sign*47.56,7.32)),((sign*47.56,7.32),(sign*39.43,7.32)),((sign*39.43,7.32),(sign*39.43,1.04))]:
            Facade(b,p0,p1,'corner connection above the wing').wall(WING-.18,WING+1.05,(),.21,BRICK)
        rear=Polygon([(sign*u,v)for u,v in [(39.83,37.07),(46.52,37.07),(46.52,43.54),(44.87,45.28),(41.62,45.28),(39.83,43.82)]])
        b.plan_prism(rear,WING-.22,17.65,BRICK,'raised rear corner roof volume')
        b.plan_prism(rear.buffer(.09,join_style=2),17.65,17.80,SILL,'rear corner roof coping')


def add_hall(builder,lod):
    tall_body(builder,lod)
    for index in range(len(EAST)-1):
        east_wall(builder,index,lod)
    portico(builder,lod)
