"""The exhibition centre's original square foyer and tower facing the south court.

Local X follows the principal facade eastward. Positive Y runs from the court
into the hall. The tower platform sits over the centre of the documented 46 m
square. Its front column count and stepped silhouette follow the 2024 view.
"""
import math
from pathlib import Path
from shapely import affinity
from shapely.geometry import Polygon, Point, LineString, box
from shapely.ops import unary_union
from photo_architecture import Facade

STONE='Ivory limestone'
PLASTER='Warm cream wall'
TRIM='Carved pale limestone'
RUSTIC='Lower stone courses'
SHADE='Recessed warm stone'
DARK='Metal window frames'
GLASS='Recessed window glass'
GOLD='Gilded tower metal'
RED='Red star glass'
COPING='Shadowed coping'
PALETTE={name:{'color':rgb,'roughness':rough} for name,rgb,rough in [
    (STONE,[.78,.724,.622],.85),(PLASTER,[.798,.757,.656],.90),
    (TRIM,[.855,.814,.707],.83),(RUSTIC,[.614,.553,.469],.9),
    (SHADE,[.551,.510,.436],.9),(DARK,[.155,.146,.119],.74),
    (GLASS,[.179,.219,.232],.35),(GOLD,[.764,.547,.206],.48),
    (RED,[.51,.101,.077],.39),(COPING,[.53,.497,.427],.86)]}
SOURCE=Path(__file__).resolve().parent


def arched(x,bottom,spring,radius,segments):
    arc=[(x+radius*math.cos(a*math.pi/segments),spring+radius*math.sin(a*math.pi/segments))
         for a in range(segments+1)]
    return Polygon([(x-radius,bottom),(x+radius,bottom),*arc])


def inset_window(f,hole,cols,rows,tag,distant,offset=-.31):
    """Fit the glazing behind the masonry and retain the visible arch shoulder."""
    grad=hole.buffer(-.085,join_style='mitre')
    x0,z0,x1,z1=hole.bounds
    bars=[]
    for i in range(1,cols):
        x=x0+(x1-x0)*i/cols
        bars.append(box(x-.034,z0,x+.034,z1))
    for i in range(1,rows):
        z=z0+(z1-z0)*i/rows
        bars.append(box(x0,z-.045,x1,z+.045))
    f.prism(hole,offset-.06,offset-.018,GLASS,tag+' glass')
    f.prism(hole.difference(grad.difference(unary_union(bars))),offset,offset+.055,DARK,tag+' sash')


def horizontal(b,w,d,y,z,h,material,tag):
    b.box((0,y,z),(w,d,h),material,label=tag)


def cornice(b,w,d,y,z,tag):
    for relative,extra,h,material in [(-.53,.05,.36,COPING),(-.23,.40,.25,TRIM),(.01,.64,.23,STONE),(.24,.92,.21,TRIM)]:
        horizontal(b,w+extra,d+extra,y,z+relative,h,material,tag)


def column(b,pt,z,h,r,tag,distant=False):
    x,y=pt
    b.box((x,y,z+.10),(2.52*r,2.52*r,.20),TRIM,label=tag+' plinth')
    profile=[(r*1.18,.20),(r*1.18,.34),(r*1.04,.46),(r*.98,.53),
             (r*.91,h-.72),(r*1.05,h-.61),(r*1.10,h-.48),(r*1.23,h-.31)]
    b.lathe((x,y),[(z+height,radius) for radius,height in profile],TRIM,12 if distant else 22,tag+' carved shaft')
    b.box((x,y,z+h-.16),(r*2.68,r*2.68,.32),STONE,label=tag+' capital')


def faces(b,x0,x1,y0,y1,tag):
    return [Facade(b,(x0,y0),(x1,y0),tag+' front'),
            Facade(b,(x1,y0),(x1,y1),tag+' east'),
            Facade(b,(x1,y1),(x0,y1),tag+' back'),
            Facade(b,(x0,y1),(x0,y0),tag+' west')]


def finial(b,x,y,z,size,tag,distant):
    b.lathe((x,y),[(z,.32*size),(z+.18*size,.35*size),(z+.34*size,.21*size),
                   (z+.65*size,.28*size),(z+.94*size,.12*size),(z+1.30*size,.035*size)],
            GOLD,8 if distant else 14,tag)


def face_rail(f,width,z0,offset,tag,distant):
    f.box(0,z0+.76,width,.075,.095,offset,TRIM,tag+' top rail')
    f.box(0,z0+.14,width,.085,.095,offset,COPING,tag+' lower rail')
    count=max(2,round(width/(.55 if distant else .29)))
    for k in range(count+1):
        f.box(width*(k/count-.5),z0+.44,.052,.62,.065,offset,DARK,tag+' upright')


def motif(face,center,size,d,distant,tag):
    """Relief lobes and a raised round centre, estimated from the court photograph."""
    u,z=center
    circle=Point(u,z).buffer(.21*size,quad_segs=4 if distant else 8)
    frame=Point(u,z).buffer(.55*size,quad_segs=6 if distant else 12)
    face.prism(frame.difference(frame.buffer(-.085*size)),d,d+.05,TRIM,tag+' ring')
    face.prism(circle,d+.005,d+.085,TRIM,tag+' centre')
    if not distant:
        for i in range(6):
            angle=math.pi*i/3
            petal=affinity.scale(Point(0,.32*size).buffer(.14*size,quad_segs=4),xfact=.62,yfact=1.2,origin=(0,0))
            petal=affinity.translate(affinity.rotate(petal,angle,use_radians=True,origin=(0,0)),xoff=u,yoff=z)
            face.prism(petal,d+.008,d+.082,TRIM,tag+' petals')


def corner_turret(b,x,distant):
    """The gilded pavilions have an open column screen in front of recessed masonry."""
    y=3.4;start=21.06;tag='west pavilion' if x<0 else 'east pavilion'
    b.box((x,y,start+.3),(6.5,6.5,.60),STONE,label=tag+' base')
    for f in faces(b,x-2.85,x+2.85,y-2.85,y+2.85,tag):
        central=arched(0,start+.61,25.40,1.17,12 if distant else 24)
        narrow=[box(a-.32,start+.61,a+.32,25.35) for a in (-2.11,2.11)]
        f.wall(start+.6,27.20,[central,*narrow],thickness=.23,material=STONE)
        f.prism(central.buffer(.19).difference(central),.02,.16,TRIM,'arched hood')
        f.prism(central,-1.02,-.94,SHADE,'recessed inner wall')
        for a in (-2.11,2.11):
            f.box(a,25.40,.91,.22,.38,.07,TRIM,'side bay capital')
        face_rail(f,2.34,start+.60,.04,'gallery railing',distant)
    for dx in [-2.52,2.52]:
        for dy in [-2.52,2.52]:
            column(b,(x+dx,y+dy),start+.59,5.49,.30,tag,distant)
    for dx in (-1.48,1.48):
        for dy in (-2.87,2.87):
            column(b,(x+dx,y+dy),start+.59,4.11,.23,tag+' inner',distant)
    b.box((x,y,27.34),(6.12,6.12,.32),TRIM,label=tag+' roof plate')
    z=27.50;top=31.2;k=2.97
    v=[(x+dx,y+dy,z)for dx,dy in [(-k,-k),(k,-k),(k,k),(-k,k)]]+[(x,y,top)]
    b.add(v,[(0,2,1),(0,3,2),(0,1,4),(1,2,4),(2,3,4),(3,0,4)],GOLD,tag+' pyramidal cap')
    finial(b,x,y,31.15,.60,tag+' finial',distant)


def street_gate(b,front,distant):
    divisions=16 if distant else 36
    main=arched(0,2.53,12.11,4.50,divisions)
    niches=[box(s*7.2-1.30,2.54,s*7.2+1.30,14.98) for s in (-1,1)]
    holes=[main,*niches]
    small=[]
    for sign in (-1,1):
        for offset in (11.45,14.73,18.03,21.3):
            x=sign*offset
            upper=arched(x,15.39,16.62,.61,10 if distant else 18)
            lower=box(x-.52,11.62,x+.52,13.79)
            small.extend([lower,upper])
    front.wall(2.52,20.76,holes+small,thickness=.42,material=PLASTER)
    for n,panel in enumerate(small):
        inset_window(front,panel,2,2 if distant else 3,'small window',distant)
        x0,z0,x1,z1=panel.bounds
        front.box((x0+x1)/2,z0-.075,x1-x0+.33,.15,.36,.055,TRIM,'small window stool')
    # A physically inset portal surface closes the opening. The original
    # thresholds and splays are visible from the southern square.
    front.prism(main,-2.66,-2.56,GLASS,'inner glazed portal')
    pane=main.buffer(-.10);bars=[box(x-.045,2.53,x+.045,16.7) for x in (-3.0,-1.5,0,1.5,3.)]
    bars.extend(box(-4.51,z-.056,4.51,z+.056) for z in (4.75,7.15,9.55,12.05))
    for i in range(1,8):
        a=math.pi*i/8
        bars.append(LineString([(0,12.11),(4.52*math.cos(a),12.11+4.52*math.sin(a))]).buffer(.05))
    front.prism(main.difference(pane.difference(unary_union(bars))),-2.54,-2.45,DARK,'portal glazing bars')
    ring=main.buffer(.55,join_style='mitre').difference(main)
    front.prism(ring,-2.55,.19,TRIM,'outer portal arch')
    for sign,panel in zip((-1,1),niches):
        front.prism(panel,-1.02,-.95,SHADE,'blind niche back')
        front.prism(panel.buffer(.25,join_style='mitre').difference(panel),-.96,.12,TRIM,'niche jambs')
        for x in (sign*5.20,sign*9.02):
            column(b,(x,-.12),2.55,14.0,.59,'portal pier',distant)
            if not distant:
                for axis in (-1,1):
                    pts=[]
                    for j in range(97):
                        t=j/96;ang=axis*2*math.pi*5*t+(.5*math.pi if axis<0 else 0)
                        pts.append((x+.59*math.cos(ang),-.12+.59*math.sin(ang),3.12+12.58*t))
                    b.tube(pts,.095,TRIM,6,'portal diamond relief')
    # Scroll silhouettes on a dark ground fill the spandrels outside the grooved arch.
    spandrels=box(-4.70,12.1,4.70,18.35).difference(main.buffer(.55))
    front.prism(spandrels,.012,.089,SHADE,'spandrel ground')
    motifs=[]
    for sign in (-1,1):
        for i in range(6):
            u=sign*(.35+.79*i)
            z=17.87-.055*i
            for j in range(1 if distant else 3):
                cz=z-j*.58
                curl=LineString([(u+sign*(.08+.19*k/16)*math.cos(k*.30),cz+(.08+.19*k/16)*math.sin(k*.30)) for k in range(17)])
                motifs.append(curl.buffer(.062,quad_segs=2))
                motifs.append(affinity.rotate(Point(u+sign*.17,cz+.13).buffer(.09,quad_segs=3),35))
    vines=unary_union(motifs).intersection(spandrels.buffer(-.035))
    front.prism(vines,.092,.16,TRIM,'scroll relief')
    # Separate oblique ridges follow the jambs up and around the vault.
    for sign in (-1,1):
        for j in range(10 if distant else 19):
            z=2.65+j*(9.33/(9 if distant else 18))
            rib=LineString([(sign*4.51,z),(sign*4.94,z+.40)]).buffer(.073,cap_style='flat')
            front.prism(rib,.20,.265,TRIM,'twisted arch ribs')
    for j in range(12 if distant else 30):
        a=(j+.3)*math.pi/(12 if distant else 30)
        ridge=LineString([(4.52*math.cos(a),12.11+4.52*math.sin(a)),
                          (4.98*math.cos(a+.055),12.11+4.98*math.sin(a+.055))])
        front.prism(ridge.buffer(.068,cap_style='flat'),.20,.267,TRIM,'curving arch ribs')
    for sign in (-1,1):
        for x in (sign*5.20,sign*9.02):
            motif(front,(x,17.67),.72,.17,distant,'cap rosette')
            if not distant:
                for level in (4.7,7.15,9.6,12.05,14.5):
                    motif(front,(x,level),.40,.72,distant,'pier rosette')
    for s in (-1,1):
        end=s*7.16
        front.prism(box(end-1.46,16.3,end+1.46,18.35),-.15,.11,COPING,'relief panel ground')
        for i in range(-1,2):
            front.box(end+i*.70,17.32,.12,1.65,.20,.19,TRIM,'relief fluting')
    front.box(0,19.47,16.3,1.68,.49,.18,STONE,'stone name tablet')
    front.box(0,20.55,19.8,.35,.93,.28,TRIM,'gate cornice')
    # Public photographs agree on the permanent inscription. Event banners vary by date.
    from sign_lettering import lettering_shapes
    font=SOURCE/'FoyerSign.otf'
    for char,geom in lettering_shapes('上海展览中心',8.9,.88,font=font):
        g=affinity.translate(geom.simplify(.023 if distant else .008),yoff=19.48)
        front.prism(g,.435,.48,GOLD,'venue name')
    for side in (-1,1):
        front.box(side*16.63,18.1,12.7,.25,.79,.16,TRIM,'side cornice')
        front.box(side*16.63,14.77,12.7,.18,.61,.13,TRIM,'side string course')
    for idx in range(7):
        h=.36*(idx+1);lo=-3.85+.52*idx
        b.box((0,lo+.267,h/2),(20.3-idx*.03,.54,h),RUSTIC,label='south entrance steps')
    horizontal(b,45.9,45.95,23.04,1.25,2.50,RUSTIC,'foyer raised base')


def gallery(b,width,depth,z0,z1,posts,tag,distant):
    y=23;hx=width/2;hy=depth/2;r=.59 if posts==8 else .39
    horizontal(b,width+.7,depth+.7,y,z0-.13,.26,TRIM,tag+' floor')
    for i in range(posts):
        x=-hx+r+(width-2*r)*i/(posts-1)
        for yy in (y-hy+r,y+hy-r):
            column(b,(x,yy),z0,z1-z0,r,tag,distant)
    for i in range(1,posts-1):
        yy=y-hy+r+(depth-2*r)*i/(posts-1)
        for x in (-hx+r,hx-r):
            column(b,(x,yy),z0,z1-z0,r,tag,distant)
    core_w=.49*width;core_d=.49*depth
    for f in faces(b,-core_w/2,core_w/2,y-core_d/2,y+core_d/2,tag+' inner'):
        low=arched(0,z0+.17,z0+.77,.63,10 if distant else 18)
        apertures=[low]
        if posts==8:
            for level in (.42,.79):
                z=z0+(z1-z0)*level
                apertures.append(box(-.41,z-.44,.41,z+.45))
        f.wall(z0,z1,apertures,material=PLASTER)
        for aperture in apertures:
            inset_window(f,aperture,2,2,'core window',distant)
    rail_faces=faces(b,-hx,hx,y-hy,y+hy,tag+' rail')
    for f in rail_faces:
        face_rail(f,f.length-.3,z0,.09,'colonnade',distant)
    horizontal(b,width+.8,depth+.8,y,z1+.22,.44,STONE,tag+' architrave')
    cornice(b,width+.8,depth+.8,y,z1+1.03,tag+' cornice')


def add_building(b,distant=False):
    front,east,back,west=faces(b,-23,23,0,46,'foyer')
    street_gate(b,front,distant)
    for f in (east,back,west):
        f.wall(2.52,20.76,material=PLASTER)
    cornice(b,46,46,23,20.78,'square foyer cornice')
    horizontal(b,45.95,45.95,23,20.65,.32,STONE,'foyer roof')
    for x in (-19.4,19.4):corner_turret(b,x,distant)
    for f in faces(b,-12.5,12.5,10.5,35.5,'main tower base'):
        apertures=[arched(x,24.08,25.22,.58,10 if distant else 20)for x in (-7.2,-3.6,0,3.6,7.2)]
        f.wall(20.77,31.30,apertures,thickness=.52,material=STONE)
        for p in apertures:inset_window(f,p,2,2,'blind arch row',distant)
    cornice(b,25.4,25.4,23,31.41,'main tower sill')
    gallery(b,21.85,23.05,31.78,39.91,8,'main colonnade',distant)
    horizontal(b,22.0,23.2,23,41.87,1.72,STONE,'main tower frieze')
    cornice(b,22.0,23.2,23,42.9,'main tower coping')
    for f in faces(b,-11.,11.,11.4,34.6,'main frieze'):
        for i in range(9):
            motif(f,((i-4)*f.length/9,41.87),.79,.015,distant,'architrave roundel')
    # Independent roof rail runs beyond the square gallery on both sides.
    for sign in (-1,1):
        start,end=sign*4.62,sign*13.84
        f=Facade(b,(min(start,end),10.22),(max(start,end),10.22),'tower parapet')
        face_rail(f,f.length,31.53,.0,'terrace railing',distant)
    for x in (-10.3,10.3):
        for y in (12.0,34.0):finial(b,x,y,43.07,1.25,'colonnade finial',distant)
    for z,h,wd in [(43.09,5.0,12.1),(48.09,2.28,11.55),(50.37,2.17,10.6)]:
        horizontal(b,wd,wd,23,z+h/2,h,STONE,'upper tower pedestal')
        cornice(b,wd,wd,23,z+h,'pedestal ledge')
    gallery(b,9.6,10.34,52.82,59.58,4,'upper lantern',distant)
    cornice(b,9.92,10.6,23,61.1,'upper lantern coping')
    for z,h,wd in [(61.35,1.7,7.2),(63.05,1.7,6.0),(64.75,1.9,5.25),(66.65,1.9,4.20),(68.55,1.6,3.25)]:
        horizontal(b,wd,wd,23,z+h/2,h,STONE,'stepped spire pedestal')
    profile=[(1.80,70.16),(1.82,70.93),(1.44,71.18),(1.48,72.47),(1.79,72.66),
             (1.81,73.12),(1.34,73.35),(1.09,74.0),(.67,85.0),(.33,102.5),
             (.68,102.85),(.69,103.25),(.40,103.53),(.22,109.6),(.32,109.85),(.24,110.40)]
    b.lathe((0,23),[(z,r) for r,z in profile],GOLD,14 if distant else 32,'tapered gilded steel spire')
    tips=[]
    for i in range(10):
        ang=math.pi/2+i*math.pi/5;r=1.92 if i%2==0 else .83
        tips.append((r*math.cos(ang),112.08+r*math.sin(ang)))
    star=Polygon(tips);face=Facade(b,(-2.2,23),(2.2,23),'summit')
    face.prism(star,-.16,.16,GOLD,'five point star rim')
    body=star.buffer(-.105,join_style='mitre')
    face.prism(body,.16,.205,RED,'red star front')
    face.prism(body,-.205,-.16,RED,'red star reverse')
