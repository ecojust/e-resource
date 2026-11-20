"""Measured aerial envelope and interpreted exterior of the Fuxing Road corner house."""
from math import ceil, floor
from shapely.geometry import Polygon, box
from photo_architecture import Facade, opening

CREAM = 'warm pale-yellow roughcast'
BRICK = 'russet facing brick'
JOINT = 'recessed brick joint'
STONE = 'ochre plaster parapet moulding'
BASE = 'grey pebbled plinth'
TILE = 'weathered red clay roof'
RIDGE = 'rounded ridge clay'
FRAME = 'dark brown casement'
GLASS = 'muted blue-grey window glass'
IRON = 'black balcony iron'
DARK = 'dark chimney opening'
DOOR = 'painted front doors'
PALETTE = {name: {'color': col, 'roughness': rough} for name, col, rough in [
    (CREAM,[.76,.70,.565],.87),(BRICK,[.55,.265,.168],.90),(JOINT,[.40,.24,.188],.9),
    (STONE,[.69,.61,.475],.8),(BASE,[.42,.405,.36],.91),(TILE,[.566,.292,.193],.91),
    (RIDGE,[.464,.252,.174],.83),(FRAME,[.164,.134,.111],.7),(GLASS,[.271,.317,.328],.34),
    (IRON,[.164,.163,.143],.50),(DARK,[.158,.145,.130],.9),(DOOR,[.227,.176,.140],.75)]}
FLOORS = (0.,3.12,6.24,9.36)
EAVE = 12.58
# The two south bays and the cut between the rear wings are visible on the aerial.
# Corners in this plan run counterclockwise. Roof projection is added separately.
OUTLINE = [(-9.48,-5.50),(-9.11,-7.36),(-7.62,-8.53),(-5.57,-8.74),(-3.91,-8.00),(-3.20,-6.65),
           (-2.90,-6.15),(2.90,-6.15),(3.20,-6.65),(3.91,-8.00),(5.57,-8.74),(7.62,-8.53),
           (9.11,-7.36),(9.48,-5.50),(9.20,-1.35),(8.69,.17),(9.11,3.73),(8.12,7.72),
           (5.35,8.17),(2.26,7.56),(1.55,3.28),(-1.73,3.03),(-2.58,7.93),(-5.66,8.24),
           (-8.53,7.15),(-9.15,3.54),(-8.52,.23),(-9.16,-1.14)]
PLAN = Polygon(OUTLINE)


def pane(face, u, sill, width, height, lod, *, door=False, arched=0.):
    aperture = opening(u,sill,width,height,arch=arched) if arched else box(u-width/2,sill,u+width/2,sill+height)
    face.window(aperture,columns=2 if lod or width<1.35 else 3,rows=2 if lod else 4,
                frame=FRAME,glass=DOOR if door else GLASS,trim=False,label='recessed multi-light casement')
    face.prism(aperture.buffer(.055,join_style=2).difference(aperture),-.008,.045,BRICK,'red-brick opening surround')
    return aperture


def diamond(face,u,z,rx,rz,mat):
    return face.prism(Polygon([(u,z+rz),(u+rx,z),(u,z-rz),(u-rx,z)]),.021,.053,mat,'diamond brick ornament')


def decorate_brick(face, x, w, z0, z1, lod):
    face.box(x,(z0+z1)/2,w,z1-z0,.075,.018,BRICK,'vertical exposed brick panel')
    if lod:return
    for i in range(1,int((z1-z0)/.125)):
        z=z0+i*.125
        face.box(x,z,w-.018,.009,.014,.056,JOINT,'horizontal brick bed joint')


def central_bays(face,lod):
    # The darker red inset of the southern gable contains separate balconies.
    half=face.length/2
    holes=[]
    for n,level in enumerate(FLOORS):
        if n==0:
            holes.append(pane(face,0,.19,1.72,2.32,lod,door=True,arched=.30))
            for x in (-1.94,1.94):holes.append(pane(face,x,.93,.90,1.56,lod))
        else:
            for x in (-1.40,1.40):holes.append(pane(face,x,level+.41,1.52,2.03,lod,door=True,arched=.20 if n==3 else 0))
            face.box(0,level+.10,5.48,.16,.80,.26,STONE,'balcony slab')
            face.box(0,level+.40,5.46,.47,.13,.60,CREAM,'low balcony parapet')
            face.box(0,level+1.01,5.46,.058,.065,.61,IRON,'balcony handrail')
            for j in range(0,19 if not lod else 10):
                count=19 if not lod else 10
                face.box(-2.62+5.24*j/(count-1),level+.80,.032,.43,.043,.61,IRON,'balcony iron upright')
            for x in (-2.65,2.65):face.box(x,level+.58,.12,.93,.68,.31,CREAM,'balcony cheek')
    face.wall(.05,EAVE,holes,thickness=.25,material=BRICK)
    for x in [-half+.13,half-.13]:face.box(x,6.23,.21,12.36,.15,.025,CREAM,'pale plaster border')
    gable=Polygon([(-half-.11,EAVE-.03),(half+.11,EAVE-.03),(0,EAVE+1.68)])
    vent=box(-.48,EAVE+.19,.48,EAVE+.86)
    face.prism(gable.difference(vent),-.24,.03,CREAM,'street-facing triangular gable with attic opening')
    face.window(vent,columns=2,rows=2,frame=FRAME,glass=GLASS,trim=False,label='attic vent')
    face.line((-half-.12,EAVE+.02),(0,EAVE+1.74),.081,BRICK,6,'gable verge')
    face.line((0,EAVE+1.74),(half+.12,EAVE+.02),.081,BRICK,6,'gable verge')


def facades(b,lod):
    for i,a in enumerate(OUTLINE):
        face=Facade(b,a,OUTLINE[(i+1)%len(OUTLINE)],'wall %02d'%i)
        if i==6:
            central_bays(face,lod)
            continue
        bay = i in {0,1,2,3,4,8,9,10,11,12}
        width=face.length
        holes=[]
        if bay:
            for z in FLOORS:
                holes.append(pane(face,0,z+.89,width-.24,1.77,lod))
                face.beam(z+.81,.095,.16,STONE,label='octagonal bay sill')
                if not lod:face.beam(z+2.71,.075,.10,BRICK,label='bay window lintel')
        elif width>=1.55:
            count=2 if width>=3.68 else 1
            for n,z in enumerate(FLOORS):
                for j in range(count):
                    u=(j-(count-1)/2)*width*.52
                    holes.append(pane(face,u,.19 if i==20 and n==0 else z+.92,min(1.26,width/(count+1)*.85),2.28 if i==20 and n==0 else 1.56,lod,door=i==20 and n==0))
            decorate_brick(face,-width/2+.115,.19,.44,EAVE-.10,lod)
            if width>2.2:
                for z in (3.32,6.44,9.56):diamond(face,0,z,.21,.29,BRICK)
        face.wall(.09,EAVE,holes,thickness=.22,material=CREAM)
        face.beam(.25,.40,.13,BASE,label='grey plinth')
        face.beam(EAVE-.09,.17,.24,BRICK,label='dark brick eave')
        if not bay and width>.72:face.beam(9.11,.11,.08,BRICK,label='upper brick band')
    b.plan_prism(PLAN,.02,.23,BASE,'apartment floor and stone plinth')


def roof_fan(b,outline,peak,edge,rise,label,lod):
    # Each face meets at a short ridge segment instead of an isolated cone.
    for i,p in enumerate(outline):
        v=outline[(i+1)%len(outline)];axis=0 if (p[1]+v[1])/2<peak[1] else 1
        r0=(peak[0],peak[1]-.77,rise);r1=(peak[0],peak[1]+.77,rise)
        ridge=(r0,r1)[axis]
        b.add([(*p,edge),(*v,edge),ridge],[(0,1,2)],TILE,label+'/tile slope')
        # Complete the hip wherever adjacent slopes meet different ridge ends.
        prev=outline[i-1];previous=(r0,r1)[0 if (prev[1]+p[1])/2<peak[1] else 1]
        if ridge!=previous:b.add([(*p,edge),ridge,previous],[(0,1,2)],TILE,label+'/hip return')
        b.tube([(*p,edge),(*v,edge)],.055,BRICK,5,label+'/eave')
        if not lod:
            b.tube([(*p,edge),ridge],.065,RIDGE,6,label+'/hip ridge')
            for j in range(1,ceil(((v[0]-p[0])**2+(v[1]-p[1])**2)**.5/.61)):
                t=j/ceil(((v[0]-p[0])**2+(v[1]-p[1])**2)**.5/.61)
                q=(p[0]*(1-t)+v[0]*t,p[1]*(1-t)+v[1]*t,edge+.015)
                h=(.15*q[0]+.85*ridge[0],.15*q[1]+.85*ridge[1],.15*edge+.85*rise+.012)
                b.tube([q,h],.018,RIDGE,4,label+'/clay tile courses')
    b.tube([(peak[0],peak[1]-.77,rise),(peak[0],peak[1]+.77,rise)],.091,RIDGE,7,label+'/ridge cap')


def chimney(b,x,y,w,d,low,top,lod):
    b.box((x,y,(low+top-.45)/2),(w,d,top-.45-low),CREAM,label='pale square chimney shaft')
    for sx in (-1,1):b.box((x+sx*(w/2-.095),y-d/2-.006,(low+top-.45)/2),(.13,.055,top-.45-low),BRICK,label='brick-edged chimney shaft')
    b.box((x,y,top-.48),(w+.14,d+.14,.15),STONE,label='chimney string course')
    b.box((x,y,top-.21),(w-.17,d-.17,.48),DARK,label='shadow within chimney head')
    for sy in (-1,1):
        for j in range(5):b.box((x-w/2+j*w/4,y+sy*d/2,top-.23),(.11,.14,.47),BRICK,label='chimney ventilating slot pier')
    b.box((x,y,top+.03),(w+.22,d+.22,.13),STONE,label='chimney cap')


def roof(b,lod):
    b.plan_prism(PLAN.buffer(.19,join_style='mitre'),EAVE-.08,EAVE+.08,TILE,'continuous red tile eave')
    for sign in (-1,1):
        front=[(sign*x,y)for x,y in [(3.02,-6.76),(3.79,-8.14),(5.52,-8.92),(7.69,-8.72),(9.31,-7.48),(9.69,-5.48),(8.87,-1.50),(3.04,-.49),(1.98,-3.20)]]
        back=[(sign*x,y)for x,y in [(1.38,2.66),(2.13,7.78),(5.40,8.42),(8.26,7.91),(9.32,3.79),(8.84,.10),(7.81,-2.92),(2.17,-3.55)]]
        for vertices,peak,label,rise in [(front,(sign*6.44,-5.14),'south octagonal bay',13.97),(back,(sign*5.89,3.57),'rear wing roof',14.48)]:
            if not Polygon(vertices).exterior.is_ccw:vertices.reverse()
            roof_fan(b,vertices,peak,EAVE+.09,rise,label,lod)
    points=[(-3.08,-6.39,EAVE+.10),(0,-6.39,EAVE+1.74),(3.08,-6.39,EAVE+.10),(-3.08,2.83,EAVE+.10),(0,2.83,EAVE+1.74),(3.08,2.83,EAVE+.10)]
    b.add(points,[(0,3,4,1),(1,4,5,2)],TILE,'central longitudinal pitched roof')
    b.tube([points[1],points[4]],.095,RIDGE,8,'central clay ridge')
    chimney(b,-8.17,-.73,1.45,1.17,.22,15.50,lod)
    chimney(b,7.19,2.29,.96,.84,11.84,14.98,lod)


def add_building(builder,lod=False):
    assert PLAN.is_valid and PLAN.exterior.is_ccw
    facades(builder,lod)
    roof(builder,lod)
