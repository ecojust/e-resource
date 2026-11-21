"""South garden loggias and two bay wings of the 238 Yan'an West Road house."""
from math import cos, pi, sin
from shapely.geometry import Polygon, box
from photo_architecture import Facade, opening

RENDER = "warm grey pebble render"
TRIM = "carved pale stone"
GRANITE = "grey granite"
TILE = "weathered terracotta"
GLASS = "grey blue glazing"
WOOD = "dark timber window sash"
FLOOR = "grey loggia paving"
METAL = "aged grey metal"
SHADOW = "recessed shadow joint"
OPAL = "opal porch light"
PALETTE = {
    RENDER: dict(color=[.67,.644,.591],roughness=.88),
    TRIM: dict(color=[.79,.771,.714],roughness=.82),
    GRANITE: dict(color=[.57,.557,.528],roughness=.87),
    TILE: dict(color=[.54,.326,.267],roughness=.9),
    GLASS: dict(color=[.33,.371,.373],metallic=.18,roughness=.29),
    WOOD: dict(color=[.235,.175,.133],roughness=.57),
    FLOOR: dict(color=[.56,.549,.522],roughness=.9),
    METAL: dict(color=[.31,.297,.274],metallic=.35,roughness=.56),
    OPAL: dict(color=[.86,.823,.726],roughness=.54),
    SHADOW: dict(color=[.46,.442,.406],roughness=.9),
}
COLUMN_AXES = [-6.88,-2.96,2.96,6.88]
UPPER_WINDOWS = [-6.08,-3.68,-1.25,1.25,3.68,6.08]
CORE_BACK = 5.90


def cornice(f, height, size=1):
    for i,(dz,h,depth) in enumerate([(-.31,.12,.26),(-.15,.16,.30),(.016,.15,.40),(.15,.10,.34)]):
        f.box(0,height+dz*size,f.length+.08,h*size,depth*size,.035+depth*size*.30,TRIM,'profile course '+str(i+1))


def framed(f, center, bottom, width, height, columns=2, rows=3, arch=0):
    shape=opening(center,bottom,width,height,arch,16)
    f.window(shape,columns,rows,frame=WOOD,glass=GLASS,label='timber opening')
    return shape


def balustrade(b, a, c, bottom, height, lod, name):
    f=Facade(b,a,c,name)
    f.box(0,bottom+.10,f.length,.20,.25,0,GRANITE,'low sill')
    f.box(0,bottom+height-.07,f.length+.025,.14,.31,0,TRIM,'handrail')
    count=max(1,round(f.length/.34))
    for i in range(count):
        point=f.point(((i+.5)/count-.5)*f.length,0)[:2]
        form=[(.13,.088),(.19,.082),(.25,.055),(.34,.083),(.45,.098),(.51,.090),(.62,.048),(.71,.057),(.82,.087),(.88,.085)]
        if lod:form=form[::2]+[form[-1]]
        b.lathe(point,[(bottom+h*height,r) for h,r in form],TRIM,6 if lod else 10,name+'/turned balusters')


def column(b,x,y,base,top,lod,name):
    h=top-base
    b.box((x,y,base+.12),(.64,.63,.24),GRANITE,label=name+'/square plinths')
    profile=[(.22,.285),(.29,.28),(.34,.25),(.39,.29),(.44,.28),(.51,.243),(h-.52,.199),(h-.42,.206),(h-.37,.242),(h-.28,.252)]
    b.lathe((x,y),[(base+z,r) for z,r in profile],TRIM,12 if lod else 22,name+'/tapered shafts')
    b.box((x,y,top-.15),(.66,.55,.24),TRIM,label=name+'/Ionic abaci')
    for sign in (-1,1):
        scroll=[]
        for i in range(10 if lod else 23):
            t=i/(9 if lod else 22);r=.143*(1-t)+.015
            scroll.append((x+sign*(.205+r*cos(2*pi*1.25*t)),y-.256,top-.248+r*sin(2*pi*1.25*t)))
        b.tube(scroll,.044,TRIM,5 if lod else 8,name+'/volutes')


def loggia(b,lod):
    rear=Facade(b,(-7.58,2.56),(7.58,2.56),'protected garden loggia/rear wall')
    holes=[]
    for x in [-5.5,0,5.5]:
        holes.append(framed(rear,x,.40,3.14 if x==0 else 2.35,2.91,4 if x==0 else 3,3))
    for x in [-5.5,0,5.5]:
        door_width=3.14 if x==0 else 2.35
        for sign in (-1,1):
            leaf=x+sign*door_width*.195
            rear.box(leaf,.84,door_width*.36,.83,.115,-.096,WOOD,'paneled garden door bases')
            rim=box(leaf-door_width*.14,.60,leaf+door_width*.14,1.06)
            rear.prism(rim.difference(rim.buffer(-.047,join_style=2)),-.05,-.032,WOOD,'raised panel mouldings')
            for side in (-1,1):
                # Opposed curved rails and a straight transom are visible in the repaired timber doors.
                points=[(leaf+door_width*.195*cos(t*pi/14),2.745,1.79+side*.10*sin(t*pi/14)) for t in range(15)]
                b.tube(points,.026,WOOD,5 if lod else 8,'garden entrance/curved timber rails')
        b.lathe((x,1.24),[(3.31,.06),(3.34,.15),(3.46,.216),(3.53,.218),(3.57,.180),(3.61,.08)],OPAL,8 if lod else 16,'garden loggia/opal pendant shades')
        b.lathe((x,1.24),[(3.6,.065),(3.67,.055),(3.71,.014),(4.05,.014)],METAL,6 if lod else 10,'garden loggia/light hangers')
    for x in [-5.96,-4.09,-1.37,1.37,4.09,5.96]:
        holes.append(framed(rear,x,4.74,1.1,2.82))
    rear.wall(.26,9.0,holes,.26,RENDER)
    for z,th,front in [(.32,.31,-.38),(4.36,.35,-.30),(9.18,.38,-.34)]:
        b.plan_prism(box(-7.67,front,7.67,CORE_BACK),z-th,z,FLOOR,'garden loggia/floor and ceilings')
    for i,(y,back,top) in enumerate([(-.88,-.30,.11),(-.70,-.30,.21),(-.50,-.30,.32)]):
        b.plan_prism(box(-6.85,y,6.85,back),max(0,top-.13),top,GRANITE,'garden entrance/garden steps')
    for lo,hi,level in [(.32,4.02,'ground'),(4.36,8.82,'first')]:
        for x in COLUMN_AXES:
            for offset in (-.245,.245):column(b,x+offset,.06,lo,hi,lod,'garden loggia/'+level+' columns')
    line=Facade(b,(-7.77,-.18),(7.77,-.18),'garden loggia/front entablatures')
    for z in (4.05,8.88):
        line.box(0,z+.06,line.length,.42,.55,0,RENDER,'architrave');cornice(line,z+.18,.82)
    for z in (4.36,9.18):
        for x in COLUMN_AXES:
            b.box((x,.06,z+.46),(.56,.61,.92),TRIM,label='garden loggia/baluster pedestals')
        for l,r in zip(COLUMN_AXES,COLUMN_AXES[1:]):
            balustrade(b,(l+.26,.035),(r-.26,.035),z,.94,lod,'garden loggia/stone balustrade')
    for u in range(-12,13):
        x=u*.57
        if abs(x)>7.26:continue
        points=[(x+.255*(2*t/8-1),-.37,8.75-.135*sin(pi*t/8))for t in range(9)]
        b.tube(points,.029,TRIM,5 if lod else 7,'garden loggia/frieze swags')
    upper=Facade(b,(-7.57,1.42),(7.57,1.42),'garden loggia/upper window band')
    apertures=[framed(upper,x,9.43,1.47,2.07) for x in UPPER_WINDOWS]
    upper.wall(9.18,12.59,apertures,.28,RENDER)
    for x in UPPER_WINDOWS:
        points=[(x+(.96*cos(pi*i/18)),1.19,11.84+.37*sin(pi*i/18))for i in range(19)]
        b.tube(points,.093,TRIM,6 if lod else 10,'garden loggia/six segmental hoods')
        upper.box(x,11.79,1.98,.12,.29,.055,TRIM,'hood springing')
    cornice(upper,12.51,.80)


def detailed_bay(b,side,lod):
    sign=1 if side=='east' else -1
    label=side+' projecting wing'
    # The two outer faces are chamfered around the center window, as in both elevations.
    local=[(7.45,-.01),(9.44,-2.49),(12.64,-2.49),(15.15,-.06),(15.15,CORE_BACK),(7.45,CORE_BACK)]
    ring=[(sign*x,y)for x,y in local]
    if sign<0:ring.reverse()
    footprint=Polygon(ring)
    for a,c in zip(ring,ring[1:]+ring[:1]):
        tag='garden face' if max(a[1],c[1])<.1 else 'return wall'
        f=Facade(b,a,c,label+'/'+tag)
        holes=[]
        if tag=='garden face':
            for z in (.98,5.03):
                width=1.35 if abs(c[1]-a[1])<.10 else min(1.05,f.length*.49)
                holes.append(framed(f,0,z,width,2.51 if z<1 else 2.45,2,3))
        f.wall(.08,9.27,holes,.27,RENDER)
        if tag=='garden face':
            for z in [2.9,4.12,4.36,7.89,8.53,9.14]:
                if z not in (2.9,7.89):cornice(f,z,.63)
            for z in [.52,.88,3.77,5.09,7.76,8.22]:
                f.box(0,z,f.length,.044,.028,.012,SHADOW,'ashlar course')
    b.plan_prism(footprint,.03,.25,GRANITE,label+'/plinth')
    b.plan_prism(footprint.buffer(.105,join_style=2),9.17,9.38,GRANITE,label+'/balcony floor')
    # The upper front wall stands behind the faceted balcony.
    x0,x1=sorted((sign*7.39,sign*15.12));middle=(x0+x1)/2
    upper=Facade(b,(x0,.35),(x1,.35),label+'/upper facade')
    h=framed(upper,0,9.48,1.78,2.50,2,3)
    upper.wall(9.30,14.21,[h],.3,RENDER)
    for xx in (-upper.length*.41,upper.length*.41):
        upper.box(xx,11.80,.35,4.75,.28,.025,TRIM,'upper pilasters')
        upper.box(xx,13.95,.48,.27,.41,.048,TRIM,'pilaster capitals')
    for z in (13.93,14.29):cornice(upper,z,.98)
    boundary=local[:4]
    for a,c in zip(boundary,boundary[1:]):
        balustrade(b,(sign*a[0],a[1]+.09),(sign*c[0],c[1]+.09),9.38,.91,lod,label+'/upper balcony')
    half=upper.length/2
    outline=[(-half,14.31),(half,14.31),(half,14.63),(half-.53,14.63)]
    # Three cusped lobes, both scroll shoulders and the small attic light are visible.
    for cx,cy,rx,rz in [(2.29,14.66,1.01,1.28),(0,15.65,1.26,1.60),(-2.29,14.66,1.01,1.28)]:
        for j in range(17):
            angle=pi*j/16;outline.append((cx+rx*cos(angle),cy+rz*sin(angle)))
    outline.extend([(-half+.53,14.63),(-half,14.63)])
    panel=Polygon(outline)
    attic=opening(0,14.98,.88,.86)
    upper.prism(panel.difference(attic),-.31,.02,RENDER,'trilobed gable')
    upper.window(attic,2,2,frame=WOOD,glass=GLASS,label='attic sash')
    rim=panel.difference(panel.buffer(-.115,join_style=2))
    upper.prism(rim,.021,.11,TRIM,'gable coping')
    b.lathe((middle,.16),[(17.15,.11),(17.28,.15),(17.37,.08),(17.49,.025)],TRIM,8 if lod else 12,label+'/gable finial')
    for x in (x0,x1):
        f=Facade(b,(x,.36),(x,CORE_BACK),label+'/upper roof returns')
        f.wall(9.27,14.23,[],.20,RENDER)
    b.plan_prism(box(x0,.38,x1,CORE_BACK),14.10,14.27,TILE,label+'/roof base')
    return middle


def roof(b,lod):
    # The source register retains the deeper roof behind this southern strip.
    for x0,x1,z0,y0 in [(-15.13,-7.38,14.28,.43),(-7.38,7.38,12.54,1.42),(7.38,15.13,14.28,.43)]:
        f=Facade(b,(x0,CORE_BACK),(x1,CORE_BACK),'garden roof/clipped rear closure')
        height=z0+(CORE_BACK-y0)*.35
        f.wall(.11,height,[],.19,RENDER)
        v=[(x0,y0,z0),(x1,y0,z0),(x1,CORE_BACK,height),(x0,CORE_BACK,height)]
        b.add(v+[(x,y,z-.10) for x,y,z in v],[(0,1,2,3),(7,6,5,4),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)],TILE,'garden roof/terracotta field')
        rows=int((CORE_BACK-y0)/(.52 if lod else .36))
        for i in range(rows):
            y=y0+i*(CORE_BACK-y0)/rows
            b.tube([(x0,y,z0+(y-y0)*.35+.017),(x1,y,z0+(y-y0)*.35+.017)],.021,TILE,4,'garden roof/tile courses')
    for x in (-6.42,6.43):
        b.box((x,5.18,14.58),(.65,.59,1.70),RENDER,label='garden roof/chimney stacks')
        b.box((x,5.18,15.48),(.79,.70,.18),TRIM,label='garden roof/chimney caps')


def make_garden_front(b,lod):
    loggia(b,lod)
    detailed_bay(b,'west',lod)
    detailed_bay(b,'east',lod)
    roof(b,lod)
