"""Build the two traced brick arches above the adjoining numbered entrances."""
from pathlib import Path
import json,math
SURVEY=json.loads((Path(__file__).parent/'survey.json').read_bytes())['features_metres']
def pigment(rgb,rough=.84):
    def linear(v):return v/3294.6 if v<=10 else ((v/255+.055)/1.055)**2.4
    return {'color':list(map(linear,rgb)),'roughness':rough}
PALETTE={k:pigment(v) for k,v in {'grey brick':(144,136,120),'mortar':(167,155,132),'red brick A':(157,81,59),'red brick B':(172,94,69),'red brick C':(145,75,54),'dark joint':(112,87,72),'stone sill':(188,184,169),'dark timber':(90,67,55),'painted timber':(146,92,79),'open interior':(38,36,34),'window glass':(84,85,80),'rain pipe':(183,178,162)}.items()}
def prism(builder,loop,y0,y1,mat,label):
    if sum(a[0]*b[1]-a[1]*b[0] for a,b in zip(loop,loop[1:]+loop[:1]))<0:loop=loop[::-1]
    n=len(loop);v=[(x,y,z)for y in (y0,y1) for x,z in loop]
    faces=[tuple(range(n)),tuple(reversed(range(n,n*2)))]
    faces.extend(((j+1)%n,j,n+j,n+(j+1)%n)for j in range(n));builder.add(v,faces,mat,label)
def rect(b,x0,x1,z0,z1,y,d,mat,name):
    prism(b,[(x0,z0),(x1,z0),(x1,z1),(x0,z1)],y,d,mat,name)
def curve(points,t):
    # Interpolate the measured arch using a local four-point cubic.
    n=len(points)-1;u=max(0.,min(t,1.))*n;i=min(n-1,int(u));v=u-i
    p0,p1,p2,p3=[points[max(0,min(n,j))]for j in (i-1,i,i+1,i+2)]
    return tuple(.5*((2*b)+(-a+c)*v+(2*a-5*b+4*c-d)*v*v+(-a+3*b-3*c+d)*v*v*v)for a,b,c,d in zip(p0,p1,p2,p3))
def add_building(builder,lod):
    b=builder
    for index,(bay,q) in enumerate(SURVEY.items()):
        lo,hi=(-1.87,.065) if not index else (.065,1.89)
        # The surveyed window is slightly skew. All four masonry returns follow that trace.
        tl,tr,br,bl=q['window'];cap=2.20;base=-.02
        prism(b,[(lo,base),bl,tl,(lo,cap)],.08,.36,'grey brick',bay+' left wall')
        prism(b,[br,(hi,base),(hi,cap),tr],.08,.36,'grey brick',bay+' right wall')
        prism(b,[(lo,base),(hi,base),br,bl],.08,.36,'grey brick',bay+' below sill')
        prism(b,[tl,tr,(hi,cap),(lo,cap)],.08,.36,'grey brick',bay+' above window')
        prism(b,q['window'],.29,.36,'open interior' if index else 'window glass',bay+' recessed opening')
        for i in range(4):
            p,r=q['window'][i],q['window'][(i+1)%4];cx=sum(p[0]for p in q['window'])/4;cz=sum(p[1]for p in q['window'])/4
            inside=lambda p:(p[0]*.91+cx*.09,p[1]*.93+cz*.07)
            prism(b,[p,r,inside(r),inside(p)],.135,.23,'painted timber' if index else 'dark timber',bay+f' window frame {i+1}')
        count=24 if not lod else 16
        out,inn=q['outer'],q['inner']
        for i in range(count):
            t0,t1=i/count,(i+1)/count
            p=[curve(out,t0),curve(out,t1),curve(inn,t1),curve(inn,t0)]
            prism(b,p,.023,.081,'dark joint',bay+f' mortar bed {i+1}')
            s0=t0+.0018;s1=t1-.0018
            p=[curve(out,s0),curve(out,(s0+s1)/2),curve(out,s1),curve(inn,s1),curve(inn,(s0+s1)/2),curve(inn,s0)]
            prism(b,p,-.044,.026,['red brick A','red brick B','red brick A','red brick C'][i%4],bay+f' brick voussoir {i+1}')
        for t,side in [(0,'left'),(1,'right')]:
            outer,inner=curve(out,t),curve(inn,t);l,r=sorted((outer[0],inner[0]));z=(outer[1]+inner[1])/2
            rect(b,l-.05,r+.05,z-.06,z,-.072,.12,'red brick B',bay+' '+side+' springing course')
            rect(b,l-.072,r+.072,z-.017,z+.021,-.087,.105,'red brick A',bay+' '+side+' projecting lip')
        prism(b,q['sill'],-.138,.12,'stone sill',bay+' white projecting sill')
        if not index:
            for leaf in range(2):
                for i in range(19 if not lod else 11):
                    j=(i+.5)/(19 if not lod else 11);z=.454+j*.918
                    l=-1.187+.063*j+leaf*.345;r=l+.316
                    rect(b,l,r,z-.014,z+.014,.154,.224,'dark timber',bay+f' shutter {leaf+1} slat {i+1}')
            rect(b,-.837,-.807,.42,1.45,.138,.205,'dark timber',bay+' centre closing stile')
        else:
            # Only the outer red stile and two visible rails of the projecting leaf are traced.
            rect(b,.61,.659,.38,1.43,-.015,.16,'painted timber',bay+' open leaf hinge stile')
            rect(b,1.275,1.307,.45,1.46,-.16,-.105,'painted timber',bay+' projecting leaf outer stile')
            for j,z in enumerate([.57,1.35]):
                b.add([(.65,.095,z),(1.29,-.13,z), (1.29,-.13,z+.035),(.65,.095,z+.035)],[(0,1,2,3),(3,2,1,0)],'painted timber',bay+f' projecting rail {j+1}')
    sides=6 if lod else 12
    path=[(.095,-.068,-.015),(.071,-.07,1.2),(.055,-.085,2.16)]
    v=[(x+.035*math.cos(i*2*math.pi/sides),y+.035*math.sin(i*2*math.pi/sides),z)for x,y,z in path for i in range(sides)]
    faces=[(j*sides+i,j*sides+(i+1)%sides,(j+1)*sides+(i+1)%sides,(j+1)*sides+i)for j in range(len(path)-1)for i in range(sides)]
    faces.extend([tuple(reversed(range(sides))),tuple(range(2*sides,3*sides))]);b.add(v,faces,'rain pipe','light rain pipe between the two house bays')
