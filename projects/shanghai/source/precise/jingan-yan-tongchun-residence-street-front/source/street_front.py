"""Three connected street bays photographed on 23 July 2022, following the later street widening."""
from math import cos, pi, sin
from shapely.geometry import box
from shapely.ops import unary_union
from photo_architecture import Facade

MORTAR='grey brown mortar'
BRICK='buff ribbed facing brick'
BRICK2='warm grey facing brick'
COURT='warm inner porch brick'
STONE='grey limestone spandrels'
EDGE='sunlit stone arrises'
TRIM='shaded carved stone'
TIMBER='reddish brown joinery'
CARVED='carved timber mouldings'
BRONZE='brown wood glazing bars'
GLASS='smoky porch glass'
STEEL='dark iron glazing bars'
SKY='grey blue upper glazing'
FLOOR='grey stone threshold'
PALETTE={
 MORTAR:dict(color=[.461,.424,.369],roughness=.91), BRICK:dict(color=[.661,.622,.544],roughness=.92),
 BRICK2:dict(color=[.617,.584,.517],roughness=.94),COURT:dict(color=[.594,.485,.375],roughness=.94),
 STONE:dict(color=[.677,.647,.571],roughness=.91),EDGE:dict(color=[.738,.711,.630],roughness=.84),
 TRIM:dict(color=[.591,.560,.493],roughness=.92),TIMBER:dict(color=[.450,.286,.189],roughness=.64),
 CARVED:dict(color=[.500,.332,.219],roughness=.66),BRONZE:dict(color=[.341,.273,.197],roughness=.59),
 GLASS:dict(color=[.226,.276,.259],roughness=.32,metallic=.26),STEEL:dict(color=[.247,.281,.279],roughness=.58,metallic=.29),
 SKY:dict(color=[.491,.592,.627],roughness=.31,metallic=.27),FLOOR:dict(color=[.442,.454,.432],roughness=.84)}
PILLARS=(-5.67,-2.66,2.66,5.67)
BAYS=[(PILLARS[i]+.246,PILLARS[i+1]-.246) for i in range(3)]
TOP=6.76
DEPTH=1.02


def rect(f,x0,z0,x1,z1,back,front,mat,label):
    f.prism(box(x0,z0,x1,z1),back,front,mat,label)


def rim(f,x0,z0,x1,z1,w,back,front,mat,label):
    outer=box(x0,z0,x1,z1);inner=box(x0+w,z0+w,x1-w,z1-w)
    f.prism(outer.difference(inner),back,front,mat,label)


def raised_curve(b,line,r,mat,label,low):
    b.tube(line,r,mat,sides=5 if low else 8,label=label)


def curve(p0,p1,p2,p3,n):
    return [tuple((1-t)**3*p0[i]+3*(1-t)**2*t*p1[i]+3*(1-t)*t*t*p2[i]+t**3*p3[i]
                  for i in (0,1)) for t in (k/n for k in range(n+1))]


def carved_panel(b,f,lo,hi,low):
    c=(lo+hi)/2;w=hi-lo
    # Two stepped borders frame the cut leaf panels. The paired inward turns
    # follow the mirrored motif visible in the dated close-up.
    for z0,z1 in [(.135,.273),(.295,.891),(.916,1.022)]:
        rim(f,lo+.044,z0,hi-.044,z1,.021,.172,.197,CARVED,'door rail and panel border')
    for hand in (-1,1):
        segments=[((0,.478),(.025,.635),(.14,.703),(.152,.580)),
                  ((.152,.580),(.165,.477),(.052,.470),(.085,.567)),
                  ((.085,.567),(.097,.594),(.137,.574),(.107,.549))]
        line=[]
        for i,seg in enumerate(segments):
            pts=curve(*seg,4 if low else 9)
            line.extend(pts[int(i>0):])
        raised_curve(b,[(c+hand*x*w/.61,-.198,z)for x,z in line],.011,CARVED,'paired curls on lower door panels',low)


def door(b,f,lo,hi,leaves,low):
    c=(lo+hi)/2;w=hi-lo;bottom=.075;transom=2.48;top=3.035
    rect(f,lo,bottom,hi,top,.04,.079,GLASS,'recessed glass behind timber joinery')
    rim(f,lo,bottom,hi,top,.052,.067,.178,TIMBER,'fixed outer door frame')
    unit=(w-.100)/leaves
    for j in range(leaves):
        x0=lo+.05+j*unit+.004;x1=x0+unit-.008;mid=(x0+x1)/2
        rect(f,x0,bottom,x1,1.083,.066,.172,TIMBER,'solid lower door leaves')
        rim(f,x0,1.040,x1,transom,.045,.074,.176,TIMBER,'glazed upper leaves')
        rim(f,x0+.095,1.215,x1-.095,transom-.145,.016,.084,.124,BRONZE,'rectangular geometric glazing bars')
        for z in (1.297,transom-.320):
            rect(f,x0+.045,z-.009,x1-.045,z+.009,.078,.115,BRONZE,'short cross rails in door glass')
        if not low:
            for x in (mid-.086,mid+.086):
                rect(f,x-.008,1.091,x+.008,1.218,.084,.115,BRONZE,'paired short grille tails')
                rect(f,x-.008,transom-.148,x+.008,transom-.042,.084,.115,BRONZE,'paired short grille heads')
        carved_panel(b,f,x0,x1,low)
    rect(f,lo+.022,transom-.028,hi-.022,transom+.035,.083,.181,TIMBER,'beam below toplights')
    count=4 if leaves==6 else 2
    for j in range(count):
        x0=lo+.038+j*(w-.076)/count;x1=x0+(w-.076)/count
        rim(f,x0,transom+.023,x1,top-.031,.032,.082,.168,TIMBER,'separate glazed toplight frame')
        rim(f,x0+.11,transom+.110,x1-.11,top-.112,.012,.081,.116,BRONZE,'fine rectangles in toplights')
        for z in (transom+.156,top-.157):
            for left,right in ((x0+.032,x0+.115),(x1-.115,x1-.032)):
                rect(f,left,z-.008,right,z+.008,.082,.113,BRONZE,'toplight grille ends')
    rect(f,lo-.087,.015,hi+.087,.077,-.052,.252,FLOOR,'threshold beneath closed doors')


def sash(f,lo,hi,count,low):
    bottom=4.715;top=6.612;rail=5.895
    rect(f,lo,bottom,hi,top,.861,.881,SKY,'upper steel window glass')
    rim(f,lo,bottom,hi,top,.040,.875,.940,STEEL,'outer steel window frame')
    for i in range(1,count):
        x=lo+(hi-lo)*i/count
        rect(f,x-.014,bottom+.022,x+.014,top-.022,.877,.925,STEEL,'narrow steel window mullions')
    for z,width in ((5.125,.010),(5.505,.010),(rail,.025),(6.272,.010)):
        rect(f,lo+.02,z-width,hi-.02,z+width,.879,.931 if z==rail else .914,STEEL,'iron sash crossbars')
    if not low:
        for z in (bottom+.12,rail-.19):
            for i in range(1,count):
                x=lo+(hi-lo)*i/count
                rect(f,x-.013,z-.025,x+.013,z+.025,.924,.940,STEEL,'sash hinge caps')


def pier(f,x,low):
    rect(f,x-.241,0,x+.241,TOP,-.065,1.129,MORTAR,'full height brick pier backing')
    course=.0798;total=int(TOP/course)+1
    for i in range(total):
        z=i*course;end=min(z+course-.006,TOP)
        mat=BRICK2 if i%5 in (1,4) else BRICK
        if end<=z:continue
        for lo,hi in ((x-.238,x-.002),(x+.004,x+.238)) if i%2 else ((x-.238,x-.119),(x-.113,x+.116),(x+.122,x+.238)):
            rect(f,lo,z,hi,end,1.127,1.139,mat,'individually coursed pier face')
        if not low:
            for side in (-1,1):
                u=x+side*.241
                rect(f,u-.008,z,u+.008,end,.12,1.127,mat,'brick joints on porch-facing pier returns')
    for aside in (-1,1):
        j=x+aside*.266
        rect(f,j-.023,.084,j+.023,TOP-.015,.862,1.006,BRICK2,'narrow pilaster steps')
    rect(f,x-.246,0,x+.246,.092,1.080,1.142,FLOOR,'individual pier foot')


def make_front(b,low=False):
    f=Facade(b,(-5.95,0),(5.95,0),'2022 street front')
    for j,(lo,hi) in enumerate(BAYS):
        span=hi-lo
        # The side rooms and the roof remain the city source. Only the three
        # photographed bays and their shallow exterior porch are modeled.
        door_lo,door_hi=lo+.236,hi-.236
        opening=box(door_lo,.075,door_hi,3.035)
        f.prism(box(lo,0,hi,3.435).difference(opening),-.105,.024,COURT,'continuous porch wall with door cutout')
        if not low:
            for k in range(42):
                z=.079*k
                for x0,x1 in [(lo,door_lo),(door_hi,hi)]:
                    rect(f,x0,z,x1,z+.004,.024,.028,MORTAR,'mortar beds beside doorways')
        door(b,f,door_lo,door_hi,6 if j==1 else 3,low)
        rect(f,lo,3.366,hi,3.491,-.064,1.035,STONE,'underside of porch lintel')
        rect(f,lo,3.492,hi,4.668,.814,1.031,STONE,'spandrel between porch and metal windows')
        rect(f,lo,3.534,hi,3.590,.998,1.059,EDGE,'lower moulding of stone spandrel')
        rect(f,lo,4.426,hi,4.467,1.007,1.055,EDGE,'rail above rectangular relief panels')
        units=4 if j==1 else 2
        for k in range(units):
            x=lo+(k+.5)*span/units;hw=span/units*.39
            rect(f,x-hw,4.031,x+hw,4.305,1.024,1.047,EDGE,'individual shallow spandrel panels')
        for k in range(units+1):
            x=lo+.15+(span-.3)*k/units
            rect(f,x-.060,4.497,x+.060,4.571,1.024,1.069,TRIM,'small window sill brackets')
            if not low:
                for sign in (-1,1):
                    line=[(x+sign*(.021+.048*cos(v*pi/9)),-1.071,4.586+.033*sin(v*pi/9)) for v in range(13)]
                    raised_curve(b,line,.009,EDGE,'paired volutes beneath metal windows',low)
        rect(f,lo,4.635,hi,4.715,.825,1.074,EDGE,'projecting sill bed')
        sash(f,lo+.046,hi-.046,6 if j==1 else 4,low)
        rect(f,lo,6.612,hi,TOP,.817,1.032,STONE,'cropped stone head')
    for x in PILLARS:pier(f,x,low)
