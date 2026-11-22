"""The two-storey projecting porch of Shi Liangcai's residence at 257 Tongren Road."""
from math import cos, sin, pi, sqrt
from shapely.geometry import Point, Polygon, LineString, box
from shapely.ops import unary_union
from shapely.affinity import scale
from photo_architecture import Facade

PALETTE = {
    'warm lime render': {'color': [.84,.78,.61], 'roughness': .91},
    'pale carved stucco': {'color': [.86,.80,.66], 'roughness': .87},
    'recessed joint': {'color': [.60,.55,.43], 'roughness': .94},
    'grey stone base': {'color': [.51,.50,.47], 'roughness': .91},
    'shaded arch soffit': {'color': [.72,.67,.54], 'roughness': .90},
    'ochre relief ground': {'color': [.39,.32,.18], 'roughness': .75},
    'gilt ochre ornament': {'color': [.65,.52,.26], 'roughness': .68},
    'mahogany window wood': {'color': [.325,.17,.11], 'roughness': .72},
    'louvre shadow': {'color': [.18,.13,.11], 'roughness': .81},
    'aged window glass': {'color': [.28,.34,.33], 'roughness': .34},
    'red roof fascia': {'color': [.63,.22,.15], 'roughness': .76},
    'dark drip edge': {'color': [.24,.25,.24], 'roughness': .74},
    'terrace roof finish': {'color': [.50,.50,.46], 'roughness': .92},
    'sandstone paving': {'color': [.66,.64,.58], 'roughness': .88},
}
LIME='warm lime render'
TRIM='pale carved stucco'
TIMBER='mahogany window wood'
GLASS='aged window glass'
HALF=2.42
JOIN=0.0
FRONT=-3.87
BOW=.69
SPRING=2.16
BELT=4.06
TOP=7.73
UPPER_SILL=4.88
UPPER_HEAD=7.12

def arch(u,width,crown,count):
    """Profile of the opening, including the full vertical jamb below springing."""
    a=width/2
    rise=crown-SPRING
    pts=[(u-a,-.05),(u+a,-.05)]
    pts += [(u+a*cos(pi*i/count),SPRING+rise*sin(pi*i/count)) for i in range(count+1)]
    return Polygon(pts)

def ellipse(cx,cy,rx,ry,n):
    return Polygon([(cx+rx*cos(2*pi*i/n),cy+ry*sin(2*pi*i/n)) for i in range(n)])

def floor(b,shape,z0,z1,material,label):
    b.prism(shape,z0,z1,lambda x,y,z:(x,y,z),material,label)

def shape_plan(extra=0,segments=20):
    """The two outer corner piers are straight. The upstairs middle sweeps forward."""
    h=HALF+extra;front=FRONT-extra;run=1.88+extra*.75
    ring=[(-h,JOIN+.015),(-h,front),(-run,front)]
    ring.extend([(-run*cos(pi*i/segments),front-BOW*sin(pi*i/segments)) for i in range(segments+1)])
    ring.extend([(h,front),(h,JOIN+.015)])
    return Polygon(ring).buffer(0)

def profile_frame(f,cx,cz,width,height,t,back,front,mat,name):
    outer=box(cx-width/2,cz-height/2,cx+width/2,cz+height/2)
    inner=box(cx-width/2+t,cz-height/2+t,cx+width/2-t,cz+height/2-t)
    f.prism(outer.difference(inner),back,front,mat,name)

def draw_window(f,cx,lod,shutters_open,width=1.43):
    s=UPPER_SILL;h=UPPER_HEAD-s;cz=(UPPER_HEAD+s)/2
    f.prism(box(cx-width/2,s,cx+width/2,s+h),-.218,-.201,'louvre shadow','rear of window recess')
    profile_frame(f,cx,cz,width+.06,h+.05,.075,-.204,-.042,TIMBER,'outer timber sash')
    if shutters_open:
        pane=box(cx-width/2+.09,s+.08,cx+width/2-.09,s+h-.08)
        f.prism(pane,-.192,-.183,GLASS,'grey glazing')
        f.box(cx,cz,.055,h-.13,.047,-.131,TIMBER,'central mullion')
        f.box(cx,s+h*.66,width-.13,.09,.07,-.116,TIMBER,'deep transom bar')
        for height in ([.32,.84] if not lod else [.32]):
            f.box(cx,s+h*height,width-.14,.046,.040,-.127,TIMBER,'horizontal glazing bar')
        if not lod:
            for direction in [-1,1]:
                f.box(cx+direction*width*.235,s+h*.82,.036,h*.29,.047,-.125,TIMBER,'upper-light glazing bar')
    for side in [-1,1]:
        if shutters_open:
            # The leaf hinges away from the glazing. It does not cover the recessed sash.
            hinge=f.point(cx+side*(width/2+.038),0,.005)[:2]
            tip=f.point(cx+side*(width/2+.25),0,.36)[:2]
            a,b=(hinge,tip) if side==1 else (tip,hinge)
            leaf=Facade(f.builder,a,b,f.label+' open shutter '+str(side))
            sw=leaf.length-.012;u=0;depth=0
        else:
            leaf=f;sw=width/2-.03;u=cx+side*width*.25;depth=-.055
        leaf.box(u,cz,sw,h-.075,.043,depth,'louvre shadow','backing')
        profile_frame(leaf,u,cz,sw,h-.065,.050,depth+.014,depth+.050,TIMBER,'leaf frame')
        count=19 if lod else 38
        for i in range(count):
            zz=s+.115+(h-.23)*(i+.5)/count
            leaf.box(u,zz,sw-.09,(h-.23)/count*.58,.025,depth+.041,TIMBER,'tilted shutter louvre')

def plaster_joints(f,width,window,lod):
    for i in range(1,10):
        z=BELT+.25+i*.31
        joint=box(-width/2+.03,z-.007,width/2-.03,z+.007).difference(window)
        if not joint.is_empty and (not lod or i%2==0):
            f.prism(joint,.001,.005,'recessed joint','horizontal incised course')

def pilaster(f,x,which,lod):
    # The ground-floor corbels carry a flowered square above three pendant chains.
    for z,w,h,d in [(2.06,.70,.065,.10),(2.17,.72,.10,.15),(2.52,.70,.063,.12),(2.62,.76,.080,.16)]:
        f.box(x,z,w,h,d,d*.5-.01,TRIM,which+' springing course')
    for z,w,h in [(2.93,.46,.055),(3.53,.53,.062),(3.87,.56,.054)]:
        f.box(x,z,w,h,.083,.049,TRIM,which+' corbel shelf')
    for offset in [-.155,0,.155]:
        count=4 if lod else 7
        for i in range(count):
            zz=2.96+i*(.49/count)
            f.box(x+offset,zz,.049,.038,.047,.066,TRIM,which+' pendant block')
    f.box(x,3.69,.40,.245,.047,.042,TRIM,which+' flower tablet')
    for i in range(5 if lod else 8):
        a=2*pi*i/(5 if lod else 8)
        f.prism(ellipse(x+.068*cos(a),3.69+.062*sin(a),.040,.036,7),.060,.096,TRIM,which+' carved petal')
    f.prism(ellipse(x,3.69,.038,.038,8),.093,.111,TRIM,which+' flower boss')

def carved_panel(f,width,lod):
    """A leaf swag and bosses in each framed panel, scaled to the curved band."""
    h=.51;z=4.53
    f.box(0,z,width-.033,h,.035,.014,'ochre relief ground','rectangular recessed relief')
    profile_frame(f,0,z,width-.024,h+.005,.032,.026,.067,TRIM,'framing of gilt panel')
    nn=9 if lod else 16;nested=[]
    for sign in [-1,1]:
        pts=[(sign*(width*.41-width*.34*i/nn),z+.10-.13*sin(pi*i/nn)) for i in range(nn+1)]
        nested.append(LineString(pts).buffer(.017 if lod else .022,cap_style=1,join_style=1))
        for i in range(1,4 if lod else 7):
            t=i/(4 if lod else 7);leaf_x=sign*(width*.41-width*.34*t)
            nested.append(ellipse(leaf_x,z+.103-.13*sin(pi*t)+(.037 if i%2 else -.038),.037,.057,8))
    nested.append(ellipse(0,z-.049,.065,.075,9))
    f.prism(unary_union(nested),.044,.084,'gilt ochre ornament','paired leaf swags and central boss')

def add_building(b,lod):
    segments=12 if lod else 30
    front=Facade(b,(-HALF,FRONT),(HALF,FRONT),'porch front')
    left=Facade(b,(-HALF,JOIN),(-HALF,FRONT),'south side')
    right=Facade(b,(HALF,FRONT),(HALF,JOIN),'north side')
    for i,f in enumerate([front,left,right]):
        width=f.length
        opening=arch(0,3.25 if i==0 else 2.68,3.60 if i==0 else 3.54,segments)
        wall=box(-width/2,0,width/2,BELT-.03).difference(opening)
        f.prism(wall,-.37,0,LIME,'pier and arched spandrel')
        inner=opening.buffer(.055,join_style=2).difference(opening).intersection(box(-width/2,0,width/2,BELT))
        f.prism(inner,-.405,-.349,'shaded arch soffit','reveal at inner edge of arch')
        for side in [-1,1]:
            pos=side*(width/2-(.395 if i==0 else .28))
            pilaster(f,pos,'left' if side<0 else 'right',lod)
            f.box(pos,.12,.61 if i==0 else .49,.24,.058,.012,'grey stone base','pier foot')
        # The translucent glazing is visible on the 2014 side; the opposite side and front are shuttered in 2013.
        if i:
            window=box(-.76,UPPER_SILL-.025,.76,UPPER_HEAD+.025)
            upper=box(-width/2,BELT+.02,width/2,TOP-.12).difference(window)
            f.prism(upper,-.235,0,LIME,'storey above side arch')
            plaster_joints(f,width,window,lod)
            draw_window(f,0,lod,i==1)
            count=15 if lod else 30
            for j in range(count):
                u=(j+.5)*width/count-width/2
                f.box(u,3.988,.072,.073,.089,.064,TRIM,'small cornice dentil')
            for sign in [-1,1]:
                for offset in [-.07,.07] if lod else [-.10,0,.10]:
                    f.box(sign*(width/2-.25)+offset,6.31,.046,2.21,.026,.020,TRIM,'upper corner fluting')
    n=8 if lod else 16
    # Rectangular middle of a shallow bowed front supports a real recessed shutter.
    coords=[(-HALF,FRONT),(-1.88,FRONT)]
    for k in range(1,n//2):
        t=pi*k/n
        x=-1.88*cos(t);y=FRONT-BOW*sin(t)
        if x<-.80:coords.append((x,y))
    coords.extend([(-.80,FRONT-.641),(.80,FRONT-.641)])
    coords.extend([(-x,y)for x,y in reversed(coords[:-2])])
    for k,(a,c) in enumerate(zip(coords,coords[1:])):
        face=Facade(b,a,c,'upper bow '+str(k+1));width=face.length
        whole=box(-width/2,BELT-.02,width/2,TOP-.09)
        central=a[0]==-.80 and c[0]==.80
        window=box(-.714,UPPER_SILL,.714,UPPER_HEAD) if central else Polygon()
        face.prism(whole.difference(window),-.201,.003,LIME,'bowed facade')
        if width>.08:
            plaster_joints(face,width,window,lod)
        if central:draw_window(face,0,lod,False,1.42)
    # The three period ornament panels follow the bowed edge. The outer panels have their own tangents.
    for i,(a,c) in enumerate([((-1.51,FRONT-.467),(-.58,FRONT-.732)),((-.56,FRONT-.675),(.56,FRONT-.675)),((.58,FRONT-.732),(1.51,FRONT-.467))]):
        plaque=Facade(b,a,c,'swag panel '+str(i+1));carved_panel(plaque,plaque.length,lod)
    for z0,z1,ext,mat,label in [
        (.005,.032,-.01,'sandstone paving','drive-through paving'),
        (3.98,4.045,.055,'shaded arch soffit','soffit level'),
        (4.045,4.105,.150,TRIM,'projecting cornice of upper floor'),
        (4.105,4.145,.069,TRIM,'return across spandrel'),
        (7.54,7.60,.060,TRIM,'upper cornice'),
        (7.60,7.73,.095,'dark drip edge','dark drip under parapet'),
        (7.73,7.93,.055,'red roof fascia','red parapet band'),
        (7.93,7.998,.100,TRIM,'stone cap to parapet')]:
        shape=shape_plan(ext,segments) if z0>.1 else box(-HALF,FRONT,HALF,JOIN)
        floor(b,shape,z0,z1,mat,label)
    floor(b,shape_plan(-.06,segments),7.998,8.013,'terrace roof finish','top surface')
    rear=Facade(b,(-HALF,JOIN+.04),(HALF,JOIN+.04),'rear return to main house')
    rear.prism(box(-HALF,.032,HALF,3.98),-.14,0,LIME,'attachment wall')
    # Only the dark double leaf actually visible beyond the arch is shown.
    rear.box(0,1.21,1.45,2.35,.055,.053,TIMBER,'recessed timber double door')
    for sign in [-1,1]:
        for z in [.54,1.45]:
            profile_frame(rear,sign*.33,z,.48,.60,.035,.084,.10,TIMBER,'door panel')
        rear.box(sign*.07,1.12,.022,.15,.032,.126,'ochre relief ground','door handle')
