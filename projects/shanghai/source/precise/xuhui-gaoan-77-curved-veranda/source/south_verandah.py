"""Open columned loggia beside the attic gallery, its pierced parapet and individually framed dormer."""
from math import pi,cos,sin
from shapely.geometry import Polygon,box
from shapely.ops import unary_union
from garden_sashes import sash
from house_layout import U,D,Z,POST_SPAN
from materials import BASE,BRICK,DARK,FRAME,GLASS,IRON,PLASTER,RECESS,RIDGE,ROOF,STONE

# Outer south corner column and edge of the loggia behind the measured gabled front.
START=.69
END=2.55
FACE=-.045
BACK=.56
FLOOR=-1.13
EAVE=-.065
# Separation of the round capital from the upper plate, read from two garden views.
CAPITAL_BELOW_EAVE_M=.532

def slab(f,plan,z0,z1,mat,name):
    f.b.prism(plan,z0,z1,lambda u,d,z:f.point(u,d,z),mat,name)

def round_column(f,u,d,z0,z1,r,lod,name):
    n=16 if lod else 32
    def ring(rad):return Polygon([(u+rad*cos(2*pi*i/n),d+rad*sin(2*pi*i/n))for i in range(n)])
    for a,b,k,m in [(0,.115,1.15,STONE),(.115,.19,1.065,PLASTER),(.19,z1-z0-.27,1.,PLASTER),(z1-z0-.27,z1-z0-.13,1.08,STONE),(z1-z0-.13,z1-z0,1.20,PLASTER)]:
        slab(f,ring(r*k),z0+a,z0+b,m,name+' | shaft and capital')
    if not lod:
        for i in range(16):
            angle=2*pi*i/16;x=u+r*1.076*cos(angle);y=d+r*1.076*sin(angle)
            f.rail([(x,y,z1-.254),(x,y,z1-.173)],.009,STONE,name+' | incised capital flutes',5)

def balustrade(f,x0,x1,z0,z1,sections,name):
    height=z1-z0
    openings=[]
    for j in range(sections):
        step=(x1-x0)/sections
        a=x0+(j+.12)*step;b=x0+(j+.88)*step
        for k in range(4):
            pitch=(b-a)/4;x=a+(k+.5)*pitch;r=.27*pitch
            openings+=[box(x-r,z0+.29*height,x+r,z0+.62*height),
                       box(x-r,z0+.71*height,x+r,z0+.86*height)]
    plate=box(x0,z0,x1,z1).difference(unary_union(openings))
    f.solid(plate,-.145,0,PLASTER,name+' | pierced panels and mid rails')
    f.rect(x0-.028,x1+.028,z1-.028,z1+.046,-.153,.038,STONE,name+' | cap')
    for j in range(sections+1):
        x=x0+j*(x1-x0)/sections
        f.rect(x-.065,x+.065,z0-.016,z1+.010,-.16,.017,PLASTER,name+' | square piers')
    for j in range(sections):
        x=x0+(j+.5)*(x1-x0)/sections
        f.rect(x-.027,x+.027,z0+.075*height,z0+.18*height,-.002,.001,RECESS,name+' | lower square detail')

def brackets(f,xs,deck_z,depth,name):
    # A rounded underside is visible on the four projecting brackets below the southern porch slab.
    shape=Polygon([(0,0),(depth,0),(depth,-.075),(depth*.94,-.19),(depth*.77,-.32),
                   (depth*.57,-.40),(depth*.36,-.44),(0,-.44)])
    for x in xs:
        s=f.face(x-.095,0,0,-1)
        s.solid(Polygon([(u,deck_z+z) for u,z in list(shape.exterior.coords)[:-1]]),-.19,0,STONE,name+' | curved stone bracket')

def porch(f,lod):
    front=f.face(0,D(FACE),1,0)
    a,b=U(START),U(END)
    deck,top=Z(FLOOR),Z(EAVE);inner=D(BACK);outer=D(FACE)
    slab(f,box(a-.12,outer-.11,b+.12,inner),deck-.16,deck+.012,STONE,'south portico | balcony slab')
    slab(f,box(a-.14,outer-.19,b+.15,inner+.06),top-.12,top+.04,PLASTER,'south portico | broad flat soffit')
    front.rect(a-.12,b+.12,deck-.18,deck-.102,.012,.125,PLASTER,'south portico | fascia lip')
    z_rail=deck+1.0
    balustrade(front,a+.18,b-.18,deck+.002,z_rail,3,'south loggia')
    balustrade(f.face(b,outer,0,1),.02,inner-outer,deck,z_rail,1,'east loggia return')
    for x in [a+.12,b-.16]:
        y=outer+.11
        cap=top-CAPITAL_BELOW_EAVE_M
        round_column(f,x,y,deck,cap,.21,lod,'south portico')
        # A square bearing sits on the round moulding; a short square bolster
        # rises to the soffit behind the projecting garden eave.
        slab(f,box(x-.253,y-.231,x+.253,y+.231),cap,cap+.084,STONE,
             'south portico | square bearing above capital')
        slab(f,box(x-.185,y-.164,x+.185,y+.246),cap+.084,top-.12,PLASTER,
             'south portico | short bolster under soffit')
    back=f.face(0,inner,1,0)
    low=a+.34;high=b-.37
    upper=[box(low,deck+.026,low+(high-low)*.44,deck+2.28),box(low+(high-low)*.60,deck+.035,high,deck+2.28)]
    lower=[box(a+.55,.14,a+(b-a)*.43,deck-.52),box(a+(b-a)*.58,.14,b-.62,deck-.52)]
    back.solid(box(a-.08,0,b+.08,top).difference(unary_union(upper+lower)),-.19,0,PLASTER,'south portico | recessed wall and French windows')
    for i,hole in enumerate(upper+lower):
        sash(back,hole,'rear of south loggia | glazed opening '+str(i+1),4,(.23,.53),False)
    # Square brick piers below the upper round columns have pale bases and a corbel under the plate.
    for x in [a+.12,b-.16]:
        slab(f,box(x-.20,outer-.08,x+.20,outer+.36),.01,deck-.18,BRICK,'ground portico | brick pier')
        slab(f,box(x-.235,outer-.11,x+.235,outer+.38),.025,.24,STONE,'ground portico | stone plinth')
    brackets(front,[a+.08,a+(b-a)*.34,a+(b-a)*.67,b-.08],deck-.165,.28,'front of ground portico')
    return a,b,top

def dormer(f,lod):
    # Central gabled dormer on the eastern roof. The three lights and surrounding timber are visible on plate 37.
    d=D(.343);face=f.face(0,d,1,0);cx=U(1.346);a,b=U(1.065),U(1.630)
    z0,shoulder,peak=Z(.344),Z(.694),Z(.892)
    front=Polygon([(a,z0),(b,z0),(b,shoulder),(cx,peak),(a,shoulder)])
    window=box(U(1.142),Z(.368),U(1.555),Z(.637))
    face.solid(front.difference(window),-.17,0,PLASTER,'dormer | gabled dormer with large glazed aperture')
    # The upper triangle is dark timber below a broad bargeboard, above the three paired ochre casements.
    panel=Polygon([(a,shoulder-.14),(cx,peak+.044),(b,shoulder-.14)])
    face.solid(panel.difference(window),.003,.027,DARK,'dormer | dark boarded tympanum')
    sash(face,window,'south roof | three dormer casements',6,(.17,.34),True,depth_scale=.44)
    for k in [1,2]:
        x=window.bounds[0]+k*(window.bounds[2]-window.bounds[0])/3
        face.rect(x-.030,x+.030,window.bounds[1],window.bounds[3],-.092,-.042,FRAME,'dormer | paired leaf post')
    face.band([(a-.115,shoulder-.035),(cx,peak+.035),(b+.115,shoulder-.035)],.205,-.13,.125,DARK,'dormer | dark gable bargeboard')
    back_d=.98
    for lo,direction in [(a,-1),(b,1)]:
        side=face.face(lo,back_d if direction<0 else 0,0,direction)
        side.rect(0,back_d,z0-.04,shoulder,-.10,0,PLASTER,'dormer | plaster cheek')
    for x,y in [(a-.10,cx),(cx,b+.10)]:
        lo=lambda u:peak+.12-(peak-shoulder)*abs(u-cx)/((b-a)/2)
        plan=box(x,-.12,y,back_d+.10)
        face.b.prism(plan,-.077,0,lambda u,v,h:face.point(u,v,lo(u)+h),ROOF,'dormer | paired roof pitch')
    face.rail([(cx,-.12,peak+.145),(cx,back_d+.10,peak+.145)],.055,RIDGE,'dormer | ridge cap',8)
