"""Broken segmental pediment and stepped entablature above the west entry, No. 50."""
import math


def material(rgb):
    return dict(color=[x/3294.6 if x<=10 else ((x/255+.055)/1.055)**2.4 for x in rgb],roughness=.86,metallic=0)


PALETTE={name:material(colour) for name,colour in [
    ('pale stone',(209,192,164)),('weathered edge',(163,142,115)),('stone soffit',(183,165,145)),
    ('light moulding',(223,205,179)),('shaded cut',(134,116,100)),('frieze',(203,183,158))]}


def block(b,x0,x1,y0,y1,z0,z1,mat,name):
    b.box(((x1+x0)/2,(y1+y0)/2,(z1+z0)/2),(x1-x0,y1-y0,z1-z0),mat,label=name)


def profile(t):
    # Rising segment ends abruptly on either side of the window above the portico.
    return 1.78-.45*t*t-.20*t


def curved_course(b,side,zoff,height,front,back,mat,n,name):
    vertices=[]
    for j in range(n+1):
        t=j/n
        x=side*(.335+1.695*t)
        z=profile(t)+zoff
        vertices.extend([(x,front,z),(x,back,z),(x,back,z+height),(x,front,z+height)])
    faces=[]
    for j in range(n):
        a=j*4
        faces.extend((a+k,a+4+k,a+4+(k+1)%4,a+(k+1)%4) for k in range(4))
    faces.extend([(3,2,1,0),(4*n,4*n+1,4*n+2,4*n+3)])
    b.add(vertices,faces,mat,name)


def add_building(b,lod=False):
    # At either end the cornice moves forwards over the column; the middle recedes.
    runs=[(-1.68,-1.18,-.375),( -1.18,1.18,-.015),(1.18,1.68,-.375)]
    for j,(a,c,front) in enumerate(runs):
        for z,h,projection,mat in [(0,.07,.03,'pale stone'),(.07,.04,.054,'light moulding'),
                                    (.11,.18,.015,'frieze'),(.29,.041,.045,'pale stone'),
                                    (.331,.065,.019,'shaded cut'),(.396,.04,.056,'light moulding'),
                                    (.436,.147,.102,'stone soffit'),(.583,.04,.190,'pale stone'),
                                    (.623,.039,.214,'light moulding')]:
            block(b,a,c,front-projection,.32,z,z+h,mat,'entablature course '+str((j,z)))
        count=round((c-a)/.079)
        for i in range(count):
            x=a+(i+.5)*(c-a)/count
            block(b,x-.018,x+.018,front-.051,front-.012,.136,.276,'light moulding','frieze fluting '+str((j,i)))
            block(b,x-.018,x+.018,front-.079,front-.006,.338,.393,'pale stone','dentil '+str((j,i)))
        count=round((c-a)/.272)
        for i in range(count):
            x=a+(i+.5)*(c-a)/count
            block(b,x-.033,x+.033,front-.171,front-.091,.506,.589,'weathered edge','cornice modillion '+str((j,i)))
    block(b,-.33,.33,-.111,-.013,.118,.273,'pale stone','blind central tablet')
    for x in (-.315,.315):
        block(b,x-.036,x+.036,-.125,-.02,.099,.137,'weathered edge','tablet foot '+str(x))
    for side in (-1,1):
        n=12 if lod else 42
        for off,th,y0,y1,mat in [(-.211,.053,-.39,.29,'stone soffit'),(-.158,.035,-.422,.292,'pale stone'),
                                  (-.123,.059,-.445,.296,'weathered edge'),(-.064,.049,-.49,.301,'pale stone'),
                                  (-.015,.042,-.511,.308,'light moulding'),(.027,.042,-.532,.313,'weathered edge')]:
            curved_course(b,side,off,th,y0,y1,mat,n,'raking broken cornice '+str((side,off)))
        # The photograph shows six prominent spaced square corbels under each broken wing.
        for i,t in enumerate((.088,.245,.405,.562,.726,.881)):
            x=side*(.335+1.695*t);z=profile(t)
            block(b,x-.040,x+.040,-.465,-.254,z-.275,z-.132,'stone soffit','raking corbel '+str((side,i)))
            block(b,x-.046,x+.046,-.476,-.252,z-.266,z-.229,'pale stone','corbel nose '+str((side,i)))
        # The two outer end pieces project out of the wall and turn back to meet the raking cornice.
        x0,x1=sorted((side*1.09,side*2.03))
        for j,(z,hh,y0,mat) in enumerate([(.975,.070,-.427,'stone soffit'),(1.045,.040,-.453,'pale stone'),(1.085,.045,-.502,'weathered edge'),(1.13,.061,-.532,'light moulding')]):
            block(b,x0,x1,y0,.30,z,z+hh,mat,'outer horizontal return '+str((side,j)))
        for j,x in enumerate((1.20,1.46,1.72,1.944)):
            x*=side
            block(b,x-.034,x+.034,-.481,-.275,.882,1.047,'pale stone','return corbel '+str((side,j)))
        # Paired tapered stone abutments behind the stepped horizontal return.
        vertices=[]
        for z,inner,outer,front in ((.64,1.20,1.64,-.36),(.975,1.10,1.986,-.408)):
            vertices.extend([(side*inner,front,z),(side*outer,front,z),(side*outer,.25,z),(side*inner,.25,z)])
        b.add(vertices,[(0,1,2,3),(4,7,6,5),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)],'frieze','flared stone base '+str(side))
