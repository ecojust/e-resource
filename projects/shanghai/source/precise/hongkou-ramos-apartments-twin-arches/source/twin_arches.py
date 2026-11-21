"""Measured 2014 street elevation with a recessed double arch and a five-repeat fret."""
from math import cos, pi, sin, sqrt
COLORS={'pale stucco':(196,194,175),'sheltered plaster':(172,173,155),'outer ledge':(211,209,191),
    'raised limewash':(205,203,184),'incised fret':(126,131,115),'groove':(148,149,134),
    'dark frame':(66,68,60),'inner timber':(82,80,68),'deep window':(67,78,78),
    'dim reflection':(91,103,103),'arched glass':(86,96,95)}
def linear(c):
    t=c/255
    return t/12.92 if t<=.04045 else ((t+.055)/1.055)**2.4
PALETTE={name:{'color':[linear(v) for v in rgb],'roughness':.32 if name in ('deep window','dim reflection','arched glass') else .88}for name,rgb in COLORS.items()}
def box(b,label,color,x0,x1,front,back,z0,z1):
    b.box(((x0+x1)/2,(front+back)/2,(z0+z1)/2),(x1-x0,back-front,z1-z0),color,label=label)
def wedge(b,label,color,outline,front,back):
    if sum(x*v-u*z for (x,z),(u,v) in zip(outline,outline[1:]+outline[:1]))<0:outline=list(reversed(outline))
    n=len(outline);vertices=[(x,y,z)for y in (front,back)for x,z in outline];faces=[]
    for i in range(1,n-1):faces.extend([(0,i,i+1),(n,n+i+1,n+i)])
    for i in range(n):
        j=(i+1)%n;faces.extend([(i,n+i,n+j),(i,n+j,j)])
    b.add(vertices,faces,color,label)
def arc(b,label,color,x,z,rx,rz,inner,outer,front,back,steps,whole=False):
    for i in range(steps):
        angle=(2*pi if whole else pi)/steps
        def p(f,a):return (x+(rx+f)*cos(a),z+(rz+f)*sin(a))
        a=i*angle;c=(i+1)*angle
        wedge(b,label,color,[p(inner,a),p(outer,a),p(outer,c),p(inner,c)],front,back)
def fill_arc(b,label,material,x,z,rx,rz,front,back,count):
    for i in range(count):
        a=pi*i/count;c=pi*(i+1)/count
        wedge(b,label,material,[(x,z),(x+rx*cos(a),z+rz*sin(a)),(x+rx*cos(c),z+rz*sin(c))],front,back)
def wall(b,far):
    # The face of the main wall lies in front of the paired fanlights and circular ornament.
    widths=(-1.34,-.92,.92,1.34);base=5.48
    box(b,'Backing to the cropped wall','sheltered plaster',widths[0],widths[-1],.245,.50,0,6.87)
    for side in (-1,1):
        l,r=sorted((side*.92,side*1.34))
        for i in range(16):
            z=i*.44
            if z<6.87:box(b,'Ruled side wall course','pale stucco',l,r,-.004,.27,z,min(6.87,z+.426))
    n=40 if not far else 21
    for i in range(n):
        a=i*pi/n;c=(i+1)*pi/n
        points=[(.92*cos(a),base+.99*sin(a)),(.92*cos(c),base+.99*sin(c))]
        wedge(b,'Solid wall over recessed outer arch','pale stucco',points+[(points[1][0],6.87),(points[0][0],6.87)],-.004,.26)
    # Recessed pale tympanum carries the paired lunettes. The narrower outer edge is visible from below.
    fill_arc(b,'Recessed tympanum','sheltered plaster',0,base,.92,.99,.139,.25,n)
    arc(b,'Roll on recessed great arch','raised limewash',0,base,.92,.99,-.026,.021,-.021,.142,n)
    for x in (-.9,.9):
        box(b,'Cropped wall to side of windows','pale stucco',x-.035,x+.035,-.009,.24,0,base)

def joinery(b,far):
    for i,(bottom,top) in enumerate(((.67,2.24),(3.38,5.36))):
        box(b,'Pale meeting pier between the pair','pale stucco',-.08,.08,-.018,.25,bottom-.018,top+.032)
        for sign in (-1,1):
            l,r=sorted((.08*sign,.855*sign));cx=(l+r)/2
            box(b,'Limestone window reveal','sheltered plaster',l,r,.181,.254,bottom,top)
            box(b,'Recessed glazed casement','dim reflection' if i==0 else 'deep window',l+.045,r-.045,.134,.158,bottom+.051,top-.045)
            for x in (l+.022,r-.022):
                box(b,'Recessed dark jamb','dark frame',x-.022,x+.022,.091,.185,bottom,top)
            for z in (bottom+.024,top-.027):
                box(b,'Casement horizontal frame','inner timber',l,r,.086,.182,z-.024,z+.024)
            if i==0:
                for z in (bottom+.21,top-.17):
                    box(b,'Lower sash narrow rail','dark frame',l+.035,r-.035,.095,.15,z-.016,z+.016)
        box(b,'Pale sill across paired lights','outer ledge',-.906,.906,-.094,.22,bottom-.09,bottom+.007)
    # Two small lunettes under one outer arch. Their centres and outer spring-line align in the photograph.
    for cx in (-.447,.447):
        fill_arc(b,'Recessed semicircular pane','arched glass',cx,5.51,.394,.386,.111,.152,29 if not far else 15)
        arc(b,'Curved inner glazing bead','dark frame',cx,5.51,.394,.386,-.012,.022,.074,.163,30 if not far else 15)
        arc(b,'Paired arched stucco reveal','raised limewash',cx,5.51,.394,.386,.024,.068,.009,.156,33 if not far else 17)
    box(b,'Common transom below the two lunettes','raised limewash',-.898,.898,-.051,.205,5.357,5.51)
    # Circular patera is a low disc with two concentric outlines and an uncarved centre.
    fill_arc(b,'Upper half of the plain circular disc','pale stucco',0,6.069,.163,.163,.057,.142,26 if not far else 15)
    outline=[(.163*cos(a*pi/24),6.069-.163*sin(a*pi/24))for a in range(25)]
    wedge(b,'Lower half of the plain circular disc','pale stucco',outline,.057,.142)
    arc(b,'Outer moulding of patera','raised limewash',0,6.069,.17,.17,-.006,.026,.006,.145,48 if not far else 26,True)
    arc(b,'Inner line of patera','outer ledge',0,6.069,.135,.135,-.009,.005,.044,.145,42 if not far else 24,True)

def mouldings(b):
    box(b,'Recessed field dividing the two storeys','pale stucco',-.889,.889,.008,.248,2.235,3.31)
    for z in (2.60,3.05):
        box(b,'Outline of rectangular tablet','outer ledge',-.697,.697,-.033,.026,z,z+.034)
    for x in (-.677,.677):
        box(b,'Sides of rectangular tablet','outer ledge',x-.017,x+.017,-.032,.027,2.615,3.067)
    for x in (-.714,.714):
        box(b,'Small return on tablet edge','raised limewash',x-.028,x+.028,-.055,.027,2.73,2.91)
    box(b,'Shallow frieze support','pale stucco',-.904,.904,-.039,.20,.08,.58)
    for z in (.085,.523):
        box(b,'Frieze horizontal arris','outer ledge',-.919,.919,-.095,.00,z,z+.051)
    # Five complete repetitions joined at the foot of each rectangular spiral.
    length=.348;begin=-.87
    pattern=[(0,.03),(0,.34),(.288,.34),(.288,.114),(.083,.114),(.083,.256),(.206,.256),(.206,.18)]
    for i in range(5):
        x=begin+i*length
        for (a,z),(c,v) in zip(pattern,pattern[1:]):
            box(b,'Square fret on lintel','incised fret',x+min(a,c)-.014,x+max(a,c)+.014,-.058,-.035,.132+min(z,v)-.014,.132+max(z,v)+.014)
        box(b,'Connecting fret baseline','incised fret',x-.014,x+length+.014,-.058,-.036,.148,.176)
    box(b,'Lower lip over window heads','outer ledge',-.943,.943,-.112,.216,0,.094)
def add_building(builder,lod=False):
    wall(builder,lod);joinery(builder,lod);mouldings(builder)
