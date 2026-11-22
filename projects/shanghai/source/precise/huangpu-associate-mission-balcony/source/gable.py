"""Pierced street balcony of the Associate Mission Building, with separate front panels and corbels."""
from math import sin,cos,pi
from pathlib import Path
from shapely.geometry import Polygon,box
from profile_tools import BRICK as STONE,cb,slab,bricks_uv
CAP='Dressed stone coping and cornice'
PIER='Square corner post'
TRIM='Raised field and moulding'
SUPPORT='Curved stone corbel'
PALETTE={}
for mat,col in [(STONE,(255,255,255)),(PIER,(157,150,137)),(CAP,(173,167,151)),(TRIM,(162,155,143)),(SUPPORT,(145,138,126))]:
    PALETTE[mat]=dict(color=[(v/255)**2.2 for v in col],roughness=.86)
PALETTE[STONE]['texture']=str(Path(__file__).with_name('finish.png'))
PITCH=.53
CENTRES=[i*PITCH for i in (-2,-1,0,1,2)]
FRONT=-1.12
MID=1.875
HALF=.235
END=1.49

def flower(half=HALF):
    holes=[]
    for i in range(8):
        angle=2*pi*i/8+pi/8
        def vertex(radius,cross):
            return (radius*cos(angle)-cross*sin(angle),radius*sin(angle)+cross*cos(angle))
        # The openings broaden towards the edge. The intervening stone forms eight rays.
        limit=half/max(abs(cos(angle)),abs(sin(angle)))
        radius=limit*.76
        holes.append(Polygon([vertex(.066,-.010),vertex(radius,-.048),vertex(radius+.007,.044),vertex(.066,.010)]))
    shape=box(-half,-half,half,half)
    for h in holes:shape=shape.difference(h)
    return shape

def post(b,x):
    cb(b,x-.163,x+.163,FRONT-.022,FRONT+.23,1.55,2.216,PIER,'Corner post shaft')
    cb(b,x-.185,x+.185,FRONT-.044,FRONT+.25,1.511,1.584,TRIM,'Lower bed of corner post')
    cb(b,x-.185,x+.185,FRONT-.055,FRONT+.258,2.175,2.236,TRIM,'Post neck')
    cb(b,x-.218,x+.218,FRONT-.09,FRONT+.29,2.236,2.297,CAP,'Stepped post cap')
    cb(b,x-.101,x+.101,FRONT-.035,FRONT-.018,1.648,2.111,TRIM,'Shallow raised face field')

def bracket(b,x,lod):
    # In side elevation the corbel curls away from the front edge, then returns to the wall.
    contour=[(.08,.105),(-.149,.13),(-.185,.258)]
    controls=[((-.185,.258),(-.171,.509),(-.50,.55),(-.543,.738)),
              ((-.543,.738),(-.58,.854),(-.76,.903),(-.85,1.114)),
              ((-.85,1.114),(-.936,1.267),(-.955,1.326),(-.94,1.405))]
    steps=5 if lod else 13
    for a,c,d,e in controls:
        for i in range(1,steps+1):
            t=i/steps;s=1-t
            contour.append(tuple(s**3*a[j]+3*s*s*t*c[j]+3*s*t*t*d[j]+t**3*e[j] for j in range(2)))
    contour.extend([(.08,1.405)])
    b.prism(Polygon(contour),x-.098,x+.098,lambda y,z,xx:(xx,y,z),SUPPORT,label='Double-curved load-bearing console')
    cb(b,x-.151,x+.151,-.985,.095,1.38,1.488,CAP,'Wide upper impost of console')

def model(b,lod=False):
    from shapely.affinity import translate,scale
    for lo,hi,x,y in [(1.459,1.513,1.663,-1.125),(1.513,1.573,1.704,-1.164),(1.573,1.63,1.66,-1.125)]:
        cb(b,-x,x,y,.088,lo,hi,CAP,'Stepped edge of balcony slab')
    for x in CENTRES:
        slab(b,translate(flower(),xoff=x,zoff=0,yoff=MID),FRONT,FRONT+.115,STONE,'Pierced eight-ray front stone panel')
    for x in [-1.325,-.795,-.265,.265,.795,1.325]:
        cb(b,x-.039,x+.039,FRONT-.009,FRONT+.132,1.623,2.128,TRIM,'Joint and narrow separating upright')
    for x in (-END,END):
        post(b,x)
        bracket(b,x,lod)
        for y in (-.728,-.269):
            side=translate(scale(flower(),xfact=.88,yfact=1,origin=(0,0)),xoff=y,yoff=MID)
            b.prism(side,x-.06,x+.06,lambda yy,zz,xx:(xx,yy,zz),STONE,label='Pierced stone panel on short balcony return')
        for y in (-.5,-.037):
            cb(b,x-.067,x+.067,y-.023,y+.023,1.625,2.128,TRIM,'Short return separator')
        cb(b,x-.082,x+.082,FRONT+.09,.063,2.103,2.17,CAP,'Coping along short return')
    cb(b,-1.37,1.37,FRONT-.041,FRONT+.161,2.106,2.173,CAP,'Continuous stone front handrail')
    cb(b,-1.37,1.37,FRONT-.024,FRONT+.143,1.61,1.65,CAP,'Sill of pierced stone front')
    bricks_uv(b)
