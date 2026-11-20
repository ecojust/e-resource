"""Central brick gatehouse facing Yuyuan Road; X is to the right as seen from the street."""
from math import cos, sin, pi
from pathlib import Path
from shapely.geometry import Point,Polygon,box,LineString
from shapely.ops import unary_union
from shapely import affinity
from photo_architecture import Facade,opening,pieces
from sign_lettering import add_facade_lettering

W=8.60; D=7.25; HALF=W/2; CENTRAL=1.81; SPRING=2.88
FONT=Path(__file__).with_name('fonts')/'BubblingGatePlaqueSubset.otf'
PALETTE={
 'brown brick joints':{'color':[.266,.184,.139],'roughness':.91},
 'umber brick':{'color':[.298,.172,.111],'roughness':.89},'brown brick':{'color':[.367,.220,.141],'roughness':.91},
 'burnt brick':{'color':[.292,.134,.087],'roughness':.91},'ochre brick':{'color':[.426,.267,.163],'roughness':.91},
 'sandstone':{'color':[.64,.596,.502],'roughness':.82},'pale coping':{'color':[.72,.674,.576],'roughness':.82},
 'granite footing':{'color':[.365,.353,.318],'roughness':.83},'glazing':{'color':[.185,.224,.237],'roughness':.27,'metallic':.12},
 'painted sash':{'color':[.108,.104,.088],'roughness':.61},'ironwork':{'color':[.104,.115,.111],'roughness':.58,'metallic':.38},
 'red brown inscription':{'color':[.28,.096,.063],'roughness':.71},'plaque stone':{'color':[.839,.81,.71],'roughness':.79},
 'roof tile':{'color':[.41,.172,.11],'roughness':.87},'tile edge':{'color':[.335,.116,.072],'roughness':.88},
 'glazed green tile':{'color':[.29,.379,.284],'roughness':.40},'light leaf stone':{'color':[.608,.571,.485],'roughness':.79},
 'passage plaster':{'color':[.635,.564,.421],'roughness':.90},'passage paving':{'color':[.45,.42,.365],'roughness':.93},
 'neutral section':{'color':[.438,.363,.281],'roughness':.88},'carved stone':{'color':[.540,.507,.425],'roughness':.78}}


def terrace(f,coords,width,depth,material,label):
    f.prism(LineString(coords).buffer(width/2,join_style='round',cap_style='flat'),.025,depth,material,label)


def archivolt(f,u,spring,r,thickness,lod,material,label,pieces_count):
    # Each voussoir is its own closed annular sector, separated by a mortar joint.
    for k in range(pieces_count):
        a=pi*k/pieces_count+.006;b=pi*(k+1)/pieces_count-.006
        def rim(rad,reverse):
            ts=[a+(b-a)*i/(2 if lod else 4) for i in range(3 if lod else 5)]
            if reverse:ts.reverse()
            return [(u+rad*cos(t),spring+rad*sin(t)) for t in ts]
        f.prism(Polygon(rim(r,False)+rim(r+thickness,True)),.018,.16,material,label)


def brick_courses(f,surface,lod):
    # Raised stretchers reproduce the mottled, exposed brickwork on the 2009 street photograph.
    step=.125 if not lod else .25;length=.265 if not lod else .53
    tones=['brown brick','umber brick','burnt brick','ochre brick','brown brick','umber brick']
    for row in range(int(14.8/step)):
        z=row*step;left=-HALF-length*(row%2)/2
        for col in range(int((W+length)/length)+1):
            x=left+col*length;q=box(x+.008,z+.008,x+length-.008,z+step-.006)
            if not surface.intersects(q):continue
            q=q if surface.covers(q) else q.intersection(surface)
            if q.area<.002:continue
            tone=tones[(col*47+row*31+(137*(col+7)*(row+13))%103)%len(tones)]
            f.prism(q,.001,.014,tone,'face brickwork')


def column(b,x,outer,lod):
    radius=.253 if not outer else .21;name='Arcade/'+('outer' if outer else 'central')+' column '+str(x)
    for z0,z1,rad,mat in [(0,.18,radius*1.30,'granite footing'),(.18,.37,radius*1.13,'sandstone'),(.37,2.52,radius,'sandstone'),(2.52,2.61,radius*1.12,'carved stone'),(2.61,2.87,radius*1.29,'carved stone')]:
        shape=Point(x,-.085).buffer(rad,quad_segs=4 if lod else 6)
        b.plan_prism(shape,z0,z1,mat,name)
    b.box((x,-.075,2.865),(radius*3.00,.74,.115),'sandstone',label=name+'/abacus')
    if not lod:
        for k in range(10):
            a=2*pi*k/10;xx=x+radius*1.22*cos(a);yy=-.085+radius*1.22*sin(a)
            b.tube([(xx,yy,2.64),(xx+.025*cos(a),yy+.025*sin(a),2.76),(xx,yy,2.83)],.047,'sandstone',6,name+'/capital leaf')


def window(f,cut,u,w,bottom,spring,lod,rounded):
    f.prism(cut.buffer(.012,join_style='mitre'),-.28,-.26,'glazing','recessed window glass')
    inside=cut.buffer(-.055,join_style='mitre');bars=[]
    for dx in [-w/6,w/6]:bars.append(box(u+dx-.023,bottom,u+dx+.023,spring+.75))
    for z in [bottom+.41,bottom+.82]+([spring] if rounded else []):bars.append(box(u-w,z-.026,u+w,z+.026))
    frame=cut.difference(inside.difference(unary_union(bars)));f.prism(frame,-.247,-.195,'painted sash','window sash')
    f.box(u,bottom-.055,w+.18,.11,.22,.055,'sandstone','window sill')
    if rounded:
        archivolt(f,u,spring,w/2,.136,lod,'umber brick','arched brick window head',9 if lod else 13)
        for side in [-1,1]:
            radius=.235;cp=u+side*radius
            coords=[(cp+radius*cos(pi*i/12),spring+radius*sin(pi*i/12))for i in range(13)]
            f.prism(LineString(coords).buffer(.019),-.225,-.18,'painted sash','fanlight curved glazing bars')


def gatehouse(b,lod):
    f=Facade(b,(-HALF,0),(HALF,0),'Street');arches=[(0,CENTRAL),(-2.74,.59),(2.74,.59)]
    apertures=[opening(u,-.10,2*r,SPRING+r+.10,r,16 if lod else 30) for u,r in arches]
    windows=[]
    for u in [-2.91,-.74,.74,2.91]:
        w=.96;bottom=10.37;spring=11.47;windows.append((opening(u,bottom,w,spring-bottom+w/2,w/2,14 if lod else 23),u,w,bottom,spring,True))
    for u in [-.94,.94]:
        w=1.46;bottom=7.12;spring=8.37;windows.append((box(u-w/2,bottom,u+w/2,spring),u,w,bottom,spring,False))
    # Stepped corner piers, concave shoulders, paired volutes and centre shield.
    top=[(-HALF,13.24),(-3.82,13.24),(-3.82,13.03),(-2.07,13.03),(-2.07,13.43),(-1.78,13.47),(-1.4,13.57),(-.96,13.77),(-.62,13.96),(-.41,14.10),(-.41,14.20),(-.20,14.28),(0,14.30)]
    profile=top+[(-u,z) for u,z in reversed(top[:-1])];outer=Polygon([(-HALF,0),(HALF,0),*reversed(profile)]);surface=outer.difference(unary_union([*apertures,*(w[0]for w in windows)]));f.prism(surface,-.48,0,'brown brick joints','pierced structural facade');brick_courses(f,surface,lod)
    terrace(f,profile,.13,.19,'pale coping','profiled parapet coping')
    for side in [-1,1]:
        for z in [6.88,9.08,12.15]:f.box(side*(HALF-.12),z,.19,.11,.13,.06,'glazed green tile','edge tile band')
    for u in [-3.5,-3.08,-2.66,-2.26,2.26,2.66,3.08,3.5]:
        arc=opening(u,12.61,.296,.39,.15,13);f.prism(box(u-.208,12.62,u+.208,13.00).difference(arc),.06,.118,'ochre brick','blind corbel frieze')
    f.prism(Point(0,12.94).buffer(.205,quad_segs=10),.052,.13,'sandstone','circular escutcheon')
    for u in [-.28,.28]:f.prism(Point(u,13.98).buffer(.105,quad_segs=10),.08,.19,'sandstone','parapet scroll boss')
    for pack in windows:window(f,*pack[:5],lod,pack[5])
    f.box(0,10.285,2.83,.12,.34,.09,'sandstone','paired arched window sill')
    b.tube([(0,-.11,10.36),(0,-.11,11.40)],.155,'sandstone',10 if lod else 16,'Upper sash/twisted stone mullion')
    b.box((0,-.115,11.47),(.43,.37,.13),'carved stone',label='Upper sash/mullion capital')
    if not lod:
        for phase in [0,pi]:
            b.tube([(.159*cos(phase+6*pi*i/50),-.11+.159*sin(phase+6*pi*i/50),10.38+i/50) for i in range(51)],.018,'light leaf stone',6,'Upper sash/spiral moulding')
    # The stone lintel has four shallow scallops photographed above the square sashes.
    scallops=[(-1.91+i*3.82/64,8.40+.045*cos(i*pi/8)) for i in range(65)]
    f.prism(Polygon([*scallops,(1.91,8.70),(-1.91,8.70)]),-.046,.195,'pale coping','scalloped window hood')
    f.box(0,7.70,.24,1.20,.19,-.018,'sandstone','centre window mullion')
    f.box(0,5.82,2.65,.84,.17,.062,'plaque stone','lettered gate plaque');f.prism(box(-1.335,5.385,1.335,6.255).difference(box(-1.262,5.457,1.262,6.183)),.15,.183,'sandstone','plaque border')
    add_facade_lettering(f,'坊泉湧',0,5.83,2.07,.54,.16,.175,'red brown inscription',label='plaque right-to-left',font=FONT)
    for u,r in arches:
        archivolt(f,u,SPRING,r,.22 if u==0 else .135,lod,'sandstone','stone voussoirs',11 if u==0 else 7)
    for u in [-3.48,-1.99,1.99,3.48]:column(b,u,abs(u)>3,lod)
    # The photographed shop recesses flank the through-route; the centre stays open.
    for sign in [-1,1]:
        u=sign*2.92
        b.box((u,1.03,1.33),(1.31,.21,2.66),'brown brick',label='Side alcove/enclosure')
        b.box((u,.905,1.45),(1.07,.04,1.22),'glazing',label='Side alcove/shop window')
        for z in [.80,2.09]:b.box((u,.88,z),(1.19,.08,.075),'painted sash',label='Side alcove/shop frame')
        b.box((sign*((HALF+1.96)/2),(D+1.19)/2,2.02),(HALF-1.96,D-1.19,4.04),'neutral section',label='Passage/side room')
        for z in [.94,1.98]:b.box((u,.877,z),(1.07,.063,.045),'painted sash',label='Side alcove/display rails')
        b.box((u,.876,1.44),(.046,.063,1.21),'painted sash',label='Side alcove/display mullion')
        b.box((sign*1.946,(D+.3)/2,1.93),(.048,D-.59,3.86),'passage plaster',label='Passage/stucco return')
        # Movable iron leaves shown folded back against the reveals.
        gx=sign*1.83
        for y in [1.26,2.82]:b.box((gx,y,1.39),(.075,.068,2.77),'ironwork',label='Passage/folded iron gate frame')
        for z in [.13,1.12,2.59]:b.box((gx,2.04,z),(.07,1.58,.067),'ironwork',label='Passage/folded iron gate rails')
        for n in range(1,10 if not lod else 7):
            y=1.26+1.56*n/(10 if not lod else 7);b.tube([(gx,y,.15),(gx,y,2.76)],.017 if not lod else .022,'ironwork',6,'Passage/folded iron pickets')
    b.box((0,D/2,4.227),(W-.16,D-.16,.23),'passage plaster',label='Passage/flat soffit')
    b.box((0,D/2,-.033),(3.85,D-.08,.06),'passage paving',label='Passage/threshold at road level')
    for u in [-HALF+.12,HALF-.12]:b.box((u,D/2,7.97),(.24,D,7.48),'neutral section',label='Gatehouse/cut side')
    b.box((0,D-.13,7.96),(W-.08,.26,7.49),'neutral section',label='Gatehouse/rear above lane')
    b.box((0,D/2,11.66),(W-.12,D-.16,.14),'neutral section',label='Gatehouse/loft floor')
    for y0,y1,z0,z1 in [(.14,D/2,11.72,12.43),(D/2,D-.10,12.43,11.72)]:
        def roof(x,y,h):return(x,y,z0+(y-y0)*(z1-z0)/(y1-y0)+h)
        b.prism(box(-HALF+.055,y0,HALF-.055,y1),-.10,0,roof,'roof tile','Gatehouse/estimated red tiled roof')
        if not lod:
            for n in range(1,15):
                yy=y0+n*(y1-y0)/15;b.prism(box(-HALF+.06,yy,HALF-.06,yy+.029),0,.026,roof,'tile edge','Gatehouse/tile courses')
    for x in [-HALF+.12,HALF-.12]:
        section=Polygon([(.14,11.70),(D-.1,11.70),(D/2,12.37)]);b.prism(section,-.09,.09,lambda y,z,d:(x+d,y,z),'neutral section','Gatehouse/attic end')
