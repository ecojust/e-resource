"""Two deep arched iron frames, the caged posts and the open east gate leaf."""
from math import atan2, cos, degrees, pi, sin, sqrt
from shapely.geometry import Polygon,box
from photo_architecture import Facade
from details import IRON,EDGE,RED,RETURN,WOOD,GRAIN,WHITE,GREEN,INK,VIOLET,letters,oval,scroll,strip

SPRING=2.70
AXIS=1.97
POST=.44
DEPTH=.48


def circular_rail(x,half,rise):
    radius=(half*half+rise*rise)/(2*rise)
    return SPRING+rise-radius+sqrt(max(0,radius*radius-x*x))

def rails(builder,lod):
    faces=[Facade(builder,(-3,y),(3,y),name) for y,name in ((0,'street arch'),(DEPTH,'lane arch'))]
    configs=[(AXIS,1.49,.061),(1.86,1.075,.061)]
    count=26 if lod else 52
    for face in faces:
        for half,rise,width in configs:
            coords=[(-half+2*half*i/count,circular_rail(-half+2*half*i/count,half,rise))for i in range(count+1)]
            strip(face,coords,width,-.025,.026,IRON,'continuous rolled flat arch')
        for i in range(-5,6):
            x=i*.30
            lower=circular_rail(x,1.86,1.075);upper=circular_rail(x,AXIS,1.49);mid=(lower+upper)/2
            tangent=degrees(atan2(circular_rail(x+.01,AXIS,1.49)-circular_rail(x-.01,AXIS,1.49),.02))
            for s in (-1,1):
                scroll(face,x+s*.066,mid,.108,(upper-lower)*.41,s,-.001,.019,EDGE,'paired web scroll '+str(i),lod,tangent)
            if i%2==0 or not lod:
                a=tangent*pi/180
                def crest_point(dx,dz):
                    return (x+dx*cos(a)-dz*sin(a),upper+dx*sin(a)+dz*cos(a))
                for s in (-1,1):
                    scroll(face,x+s*.077,upper+.11,.123,.119,s,-.009,.016,EDGE,'crest tendrils '+str(i),lod,tangent)
                    strip(face,[crest_point(-s*.045,0),crest_point(-s*.018,.035),
                                crest_point(s*.025,.072),crest_point(s*.066,.097)],
                          .014,-.008,.010,EDGE,'branching crest stems '+str(i))
                    if not lod or i%2==0:
                        bud=Polygon([crest_point(s*.046,.069),crest_point(s*.074,.078),
                                     crest_point(s*.096,.10),crest_point(s*.068,.096)])
                        face.prism(bud,-.005,.013,EDGE,'scroll leaf tips '+str(i))
    for i in range(-6,7):
        x=i*.28;z=circular_rail(x,AXIS,1.49)
        builder.box((x,DEPTH/2,z),(.039,DEPTH+.02,.040),IRON,label='arch crown transverse ties')
        if i%2==0:
            builder.tube([(x,0,circular_rail(x,1.86,1.075)),(x,DEPTH,z)],.014,EDGE,5 if lod else 7,'diagonal depth braces')
    front=faces[0]
    for i,(char,x,angle) in enumerate([('沁',-.94,23),('園',.04,0),('邨',.99,-23)]):
        z=(circular_rail(x,AXIS,1.49)+circular_rail(x,1.86,1.075))/2
        letters(front,char,x,z,.432,.383,.028,.115,RETURN,'enamel name / sides',lod,angle)
        letters(front,char,x,z,.432,.383,.115,.123,RED,'enamel name / outward faces',lod,angle)
    sign=Facade(builder,(-2,DEPTH*.49),(2,DEPTH*.49),'hanging oval')
    board=oval(.04,3.29,.74,.184,lod)
    sign.prism(board,-.035,.035,WOOD,'elliptical wood sign')
    for side in (-1,1):
        x=.04+side*.43
        builder.tube([(x,DEPTH*.49,3.44),(x+side*.095,DEPTH*.47,circular_rail(x,1.86,1.075)-.021)],
                     .010,IRON,5 if lod else 7,'wood sign suspension chains')
    letters(sign,'沁園邨',.04,3.29,.69,.173,.035,.039,GRAIN,'incised lane name relief',lod)
    if not lod:
        for z in [-.122,-.098,-.073,-.044,.062,.103,.130]:
            length=.68*sqrt(1-(z/.18)**2)
            for side in (-1,1):
                path=[(.04+side*(.36+(length-.36)*i/9),3.29+z+.0036*sin(7*i/9+4*z))for i in range(10)]
                strip(sign,path,.0035,.035,.037,GRAIN,'short flowing timber grain')
    return faces

def posts(builder,lod):
    for sign,side in [(-1,'west'),(1,'east')]:
        x=sign*AXIS;group=side+' square open iron pier'
        for z,h,w,d in [(.050,.075,.49,.55),(.150,.036,.43,.48),(2.62,.052,.47,.52),(SPRING,.079,.59,.63)]:
            builder.box((x,DEPTH/2,z),(w,d,h),IRON,label=group+'/cap and shoes')
        for dx in (-POST/2,POST/2):
            for y in (0,DEPTH):
                builder.box((x+dx,y,1.35),(.041,.045,2.58),IRON,label=group+'/four corner angles')
        for y in (0,DEPTH):
            f=Facade(builder,(x-.7,y),(x+.7,y),group)
            for u in (-.105,0,.105):
                f.box(u,1.36,.016,2.52,.020,0.,EDGE,'open iron standards')
            for z in (.26,2.35):
                f.box(0,z,.43,.027,.027,0.,IRON,'scroll ties')
                for si in (-1,1):
                    scroll(f,si*.092,z+(.06 if z<1 else -.06),.068,.093,si,.004,.013,EDGE,'collar curls',lod)
        # Purple cycle notices are visible on both sides of the street photograph.
        front=Facade(builder,(x-.7,-.035),(x+.7,-.035),group)
        front.box(0,1.24,.235,.325,.018,.012,VIOLET,'removable cycle notice plate')
        front.box(0,1.106,.214,.043,.009,.024,WHITE,'notice pale footer')
        if not lod:
            for u in (-.048,.058):
                wheel=oval(u,1.259,.031,.031,False);front.prism(wheel.difference(wheel.buffer(-.005)),.023,.026,WHITE,'cycle pictogram wheels')
            strip(front,[(-.05,1.26),(-.012,1.304),(.024,1.26),(-.031,1.26),(-.014,1.29),(.044,1.29),(.058,1.26)],.006,.023,.027,WHITE,'cycle pictogram frame')


def east_leaf(builder,lod):
    # The free stile extends behind the arch into the courtyard.
    hinge=(AXIS-POST/2,.35)
    length=1.78;angle=57*pi/180
    free=(hinge[0]-length*cos(angle),hinge[1]+length*sin(angle))
    face=Facade(builder,free,hinge,'east inward-open gate leaf')
    r=length/2;top=lambda x:2.08+.23*(r-x)/length
    for x in (-r,r):
        height=top(x)-.065
        face.box(x,.065+height/2,.041,height,.053,0,IRON,'edge stiles')
    for z,height in [(.093,.045),(.36,.024),(1.69,.02)]:
        face.box(0,z,length,height,.038,0,IRON,'long rails')
    strip(face,[(-r,top(-r)),(r,top(r))],.044,-.025,.025,IRON,'sloping upper frame')
    bays=12
    for i in range(1,bays):
        x=-r+length*i/bays
        face.box(x,(.12+top(x))/2,.013,top(x)-.12,.018,0,IRON,'tall spaced uprights')
    for i in range(5):
        x=length*((i+.5)/5-.5);upper=top(x)
        for si in (-1,1):
            for z,rx,rz in [(.27,.089,.102),(upper-.11,.089,.094),(upper+.092,.106,.110)]:
                scroll(face,x+si*.075,z,rx,rz,si,-.012,.013,EDGE,'crest and foot scrolls '+str(i),lod)
    for z in (.31,1.86):
        builder.lathe(hinge,[(z,.026),(z+.102,.026)],IRON,8 if lod else 12,'east gate / hinge barrels')
    notice=box(-.36,.92,.36,1.55)
    face.prism(notice,.032,.054,WHITE,'community notice field')
    for z in (1.43,1.00):
        face.box(0,z,.67,.058,.009,.057,GREEN,'community notice green bands')
