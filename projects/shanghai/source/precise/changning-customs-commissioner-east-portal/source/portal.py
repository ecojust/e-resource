"""East entrance of the former Inspector General of Customs residence, Jiangsu Road, Shanghai."""
from math import pi,sin,cos
from pathlib import Path
from shapely.geometry import Polygon,box
from photo_architecture import opening

STONE='weathered sand-grey canopy'
EDGE='pale outer moulding'
SOFFIT='sheltered stone soffit'
CORBEL='carved stone brackets'
BRICK='red portal brick'
LIGHT='salmon facing brick'
DEEP='burnt red facing brick'
JOINT='recessed pale mortar'
RENDER='pebble-dashed outer wall'
BASE='grey plinth band'
STEP='exposed aggregate tread'
NOSE='slightly lighter stone tread nosing'
WOOD='deep umber panelled door'
TRIM='dark timber raised moulding'
VOID='darkness of recessed opening'
PLATE='green enamel street number'
WHITE='ivory enamel numeral'
METAL='dull metal stair rails'
PALETTE={n:dict(color=c,roughness=r) for n,c,r in [
(STONE,[.375,.358,.319],.91),(EDGE,[.485,.468,.429],.90),(SOFFIT,[.327,.307,.269],.96),(CORBEL,[.394,.377,.339],.9),
(BRICK,[.401,.146,.086],.94),(LIGHT,[.456,.174,.102],.93),(DEEP,[.352,.129,.078],.96),(JOINT,[.396,.301,.235],.97),
(RENDER,[1,1,1],.97),(BASE,[.371,.359,.317],.95),(STEP,[.400,.374,.346],.89),(NOSE,[.476,.449,.406],.92),(WOOD,[.040,.033,.024],.83),
(TRIM,[.073,.040,.026],.81),(VOID,[.031,.026,.023],.98),(PLATE,[.029,.183,.117],.43),(WHITE,[.824,.838,.792],.71),(METAL,[.313,.301,.271],.52)]}
PALETTE[RENDER]['texture']=str(Path(__file__).with_name('grey-pebble.png'))
FRONT,REAR=1.20,.60
SPRING,BACK_SPRING=2.88,2.14
DEPTH=.99
ARCH=1.05
BACK_ARCH=.57

def front_shape(points,front,back,b,m,label):
    b.prism(points,-back,-front,lambda x,z,t:(x,-t,z),m,label=label)
def rect(b,x0,x1,y0,y1,z0,z1,m,label):
    b.box(((x0+x1)/2,(y0+y1)/2,(z0+z1)/2),(x1-x0,y1-y0,z1-z0),m,label=label)
def slab(b,front,back,m,label):
    n=len(front);faces=[tuple(range(n)),tuple(range(2*n-1,n-1,-1))]
    for i in range(n):
        j=(i+1)%n;faces.append((j,i,i+n,j+n))
    b.add(front+back,faces,m,label)
def mix(seed):
    return (LIGHT,BRICK,BRICK,BRICK,DEEP,BRICK,LIGHT)[seed%7]

def vault_point(a,t,dr=0):
    return ((FRONT+(REAR-FRONT)*t+dr)*cos(a),t*DEPTH,SPRING+(BACK_SPRING-SPRING)*t+(ARCH+(BACK_ARCH-ARCH)*t+dr)*sin(a))
def facing(b,lod):
    # A continuous tapered barrel covers the flared brickwork from the outer to the inner arch.
    segments=37 if lod else 59
    bands=5 if lod else 8
    for row in range(bands):
        t0,t1=row/bands,(row+1)/bands
        for i in range(segments):
            a0=pi*i/segments;a1=pi*(i+1)/segments
            locations=[(a0,t0),(a1,t0),(a1,t1),(a0,t1)]
            p=[vault_point(a,t)for a,t in locations]
            slab(b,p,[vault_point(a,t,.055)for a,t in locations],JOINT,'Conical joint bed above opening')
        stagger=.5*(row%2)
        for i in range(-1,segments):
            a0=max(0,(i+stagger+.030)*pi/segments);a1=min(pi,(i+1+stagger-.030)*pi/segments)
            if a1<=a0:continue
            t=[(a0,t0+.0028),(a1,t0+.0028),(a1,t1-.0028),(a0,t1-.0028)]
            slab(b,[vault_point(a,y,-.008)for a,y in t],[vault_point(a,y,.008)for a,y in t],mix(17*i+3*row),'Fan-laid reveal bricks')
    # Flat jamb courses continue along each flared cheek, with staggered joints.
    for sign in (-1,1):
        def pt(t,h,dr):return (sign*(FRONT+(REAR-FRONT)*t+dr),DEPTH*t,h)
        rows=31
        for row in range(rows):
            z0=.005+row*(SPRING-.005)/rows;z1=.005+(row+1)*(SPRING-.005)/rows
            for i in range(6):
                t0=i/6;t1=(i+1)/6
                for a,c,dr,dm,mat,name in [(t0,t1,0,.040,JOINT,'Flared cheek mortar bed')]:
                    f=[pt(a,min(z0,SPRING+(BACK_SPRING-SPRING)*a),dr),pt(c,min(z0,SPRING+(BACK_SPRING-SPRING)*c),dr),pt(c,min(z1,SPRING+(BACK_SPRING-SPRING)*c),dr),pt(a,min(z1,SPRING+(BACK_SPRING-SPRING)*a),dr)]
                    faces=f if sign<0 else list(reversed(f));slab(b,faces,[(x+sign*dm,y,z)for x,y,z in faces],mat,name)
            for i in range(-1,6):
                a=max(0.,(i+(row%2)*.5+.02)/6);c=min(1.,(i+1+(row%2)*.5-.02)/6)
                if c<=a:continue
                f=[pt(t,min(z,SPRING+(BACK_SPRING-SPRING)*t),-.009)for t,z in [(a,z0+.004),(c,z0+.004),(c,z1-.004),(a,z1-.004)]]
                faces=f if sign<0 else list(reversed(f));slab(b,faces,[(x+sign*.015,y,z)for x,y,z in faces],mix(i+3*row),'Horizontal red-brick jambs')

def canopy(b,lod):
    # Continuous external hood. The front arris has a bead, a hollow and an upper weathering.
    profile=[(-.665,0.,SOFFIT),(-.690,.032,EDGE),(-.683,.067,EDGE),(-.628,.088,STONE),(-.623,.117,STONE),(-.662,.150,EDGE),(-.648,.184,EDGE),(-.584,.208,STONE),(-.533,.201,STONE),(-.022,.157,STONE),(.025,.123,STONE),(.01,.008,SOFFIT)]
    segments=24 if lod else 60
    def pt(a,y,t):return ((FRONT+.034+t)*cos(a),y,SPRING+(ARCH+.015+t)*sin(a))
    for i in range(segments):
        angles=[pi*i/segments,pi*(i+1)/segments]
        for j,(a,t,m)in enumerate(profile):
            c,u,_=profile[(j+1)%len(profile)]
            f=[pt(angles[0],a,t),pt(angles[1],a,t),pt(angles[1],c,u),pt(angles[0],c,u)]
            # The visible front perimeter is directed outwards from the hood cross-section.
            b.add(f,[(0,1,2,3),(3,2,1,0)],m,'Layered stone canopy bead, hollow and soffit')
    for s in (-1,1):
        x=s*1.31
        for y,z,width,depth,height in [(-.331,2.843,.43,.777,.074),(-.300,2.763,.37,.737,.092),(-.278,2.660,.319,.703,.115)]:
            b.box((x,y,z),(width,depth,height),EDGE if z>2.80 else STONE,label='Stepped impost block')
        poly=Polygon([(.045,1.75),(-.123,1.75),(-.176,1.792),(-.176,1.897),(-.153,1.933),(-.170,2.084),(-.211,2.241),(-.269,2.382),(-.347,2.478),(-.439,2.535),(-.546,2.552),(-.546,2.632),(.045,2.632)])
        b.prism(poly,x-.122,x+.122,lambda y,z,h:(h,y,z),CORBEL,label='Swept stone corbels with rolled toe')

def facade(b,lod):
    n=25 if lod else 48
    cut=opening(0,-.03,2*FRONT,SPRING+.03+ARCH,ARCH,n)
    wall=box(-1.66,-.005,1.66,4.28).difference(cut)
    front_shape(wall,0,.155,b,RENDER,'Pebble-dashed wall cut at the portal')
    # Front brick pier ends and pale plinth at the foot of the splay.
    for s in (-1,1):
        a,c=sorted((s*FRONT,s*1.46))
        rect(b,a,c,-.015,.09,0,SPRING,JOINT,'Mortar of outer pier ends')
        for j in range(32):
            lo=j*.089+.004
            rect(b,a+.002,c-.002,-.022,-.014,lo,lo+.082,mix(j+int(s)),'Brick pier face')
        rect(b,a-.013,c+.013,-.048,.078,.49,.60,BASE,'Pale belt at plinth')
    for z in range(5):
        w=1.23-.09*z
        poly=Polygon([(-w,.32)]+[(w*cos(pi+pi*k/42),-.01+(.95-.15*z)*sin(pi+pi*k/42))for k in range(43)]+[(w,.32)])
        if z:
            lip=Polygon([(-w,.31)]+[((w+.012)*cos(pi+pi*k/42),-.012+(.963-.15*z)*sin(pi+pi*k/42))for k in range(43)]+[(w,.31)])
            b.plan_prism(lip,.008+z*.129,.0355+z*.129,NOSE,label='Rounded lighter nose at each step')
        b.plan_prism(poly,0 if z==0 else .035+(z-1)*.129,.035+z*.129,STEP,label='Five curved tread profiles including the flush apron')
    landing=Polygon([(-1.054,.242),(1.054,.242),(.60,.993),(.603,1.334),(-.603,1.334),(-.60,.993)])
    b.plan_prism(landing,.003,.551,STEP,label='Landing tapered to follow both brick cheeks')
    toe=Polygon([(-1.21,-.026),(1.21,-.026),(1.054,.242),(-1.054,.242)])
    b.plan_prism(toe,.003,.035,STEP,label='Stone floor between the stair and pier')
    # The rear leaf is visible through the brick arch; interior is intentionally shallow.
    inner=opening(0,.547,1.198,BACK_SPRING+BACK_ARCH-.547,BACK_ARCH,n)
    front_shape(inner,1.305,1.34,b,WOOD,'Recessed brown door and head')
    # The darker thickness of the inner opening joins the leaf to the rear of the brick funnel.
    # Without these returns an oblique view sees daylight around the inner door.
    back_wall=opening(0,.545,1.326,BACK_SPRING+BACK_ARCH+.064-.545,BACK_ARCH+.064,n).difference(inner)
    front_shape(back_wall,.992,1.332,b,WOOD,'Inner jamb and arch returns')
    inner_ring=opening(0,.542,1.239,BACK_SPRING+BACK_ARCH+.022-.542,BACK_ARCH+.022,n).difference(inner)
    front_shape(inner_ring,.971,1.272,b,TRIM,'Dark rounded inner arch frame')
    for sign in (-1,1):
        pts=[(sign*(FRONT+(REAR-FRONT)*t-.017),DEPTH*t,z)for t,z in [(0,.485),(1,.485),(1,.594),(0,.594)]]
        b.add(pts,[(0,1,2,3),(3,2,1,0)],BASE,'Grey plinth continuing along recessed cheek')
    for x in (-.52,0,.52):
        rect(b,x-.021,x+.021,1.275,1.305,.56,2.075,TRIM,'Door rails and centre stile')
    for x in (-.275,.275):
        for z in (.73,1.37):
            outer=box(x-.211,z,x+.211,z+.53).difference(box(x-.192,z+.018,x+.192,z+.51))
            front_shape(outer,1.271,1.30,b,TRIM,'Raised rectangular door panels')
    for s in (-1,1):
        # Handrails are tilted with the rising tread line.
        b.tube([(s*1.165,.050,1.08),(s*1.095,.121,1.115),(s*.682,.830,1.458)],.018,METAL,sides=6 if lod else 10,label='Round stair handrails')
    for part in b.parts:
        if part['material']==RENDER:
            part['texcoords']=[[(x+1.66)/3.32,1-z/4.28]for x,y,z in part['vertices']]

def number_plate(b,lod):
    # Mean wall normal and its horizontal tangent put the enamel plate flush with the left cheek.
    def panel(u,v,o):
        t=.40+u/.99
        return (-FRONT+(FRONT-REAR)*t+o,.99*t,1.915+v)
    p=[panel(u,v,.026)for u,v in [(.10,-.065),(-.10,-.065),(-.10,.065),(.10,.065)]]
    b.add(p,[(0,1,2,3),(3,2,1,0)],PLATE,'Green enamel No. 3 plate')
    for n,(y,r)in enumerate([(.023,.028),(-.024,.029)]):
        pts=[panel(.028*cos(a),y+r*sin(a),.030) for a in [(-pi*.6)+(pi*1.19)*i/9 for i in range(10)]]
        b.tube(pts,.0036,WHITE,sides=4 if lod else 6,label='White enamel numeral three')

def model(b,lod=False):
    facade(b,lod);facing(b,lod);canopy(b,lod);number_plate(b,lod)
