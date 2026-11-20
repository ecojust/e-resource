"""Public street facade and corner pavilion at 378 East Daming Road, as photographed in 2014."""
from math import ceil,cos,pi,sin
from shapely import union_all
from shapely.geometry import box,Polygon
import numpy as np
from photo_architecture import Facade,opening

HW=13.88
BACK=7.24
SHAFT_X=13.81
SHAFT_Y=11.24
PALETTE={key:{'color':v,'roughness':r} for key,v,r in [
 ('red pointing',[.296,.154,.123],.98),('old red brick',[.343,.164,.133],.92),
 ('burnt brick',[.309,.148,.120],.92),('rose brick',[.358,.180,.143],.92),
 ('grey granite',[.466,.473,.452],.88),('grey stone sill',[.524,.528,.503],.91),
 ('cream concrete',[.724,.710,.645],.89),('shaded render',[.566,.547,.484],.93),
 ('metal sash',[.132,.144,.135],.73),('window glass',[.253,.291,.304],.35),
 ('dark green flashing',[.145,.229,.190],.70),('eaves wood',[.206,.161,.123],.84),
 ('green tile',[.049,.125,.094],.79),('tile ridges',[.082,.166,.128],.75),
 ('pavilion soffit',[.212,.172,.105],.80),('roof felt',[.314,.327,.307],.90),
 ('plain cut',[.478,.454,.419],.98)]}

def field(face,lo,hi,holes,lod):
    a=face.wall(lo,hi,holes,.35,'red pointing')
    x0,z0,x1,z1=a.bounds
    # Deep reds alternate gently in staggered masonry courses. The reduced mesh
    # keeps a sample of the joints at larger intervals.
    hz=.33 if lod else .17
    wz=.72 if lod else .39
    for k in range(ceil((hi-lo)/hz)):
        z=lo+k*hz;start=x0-wz/2*(k%2)
        for j in range(ceil((x1-start)/wz)):
            x=start+j*wz
            b=a.intersection(box(x+.006,z+.006,min(x+wz-.006,x1),min(z+hz-.006,hi)))
            if b.area>.002:
                color=('old red brick','rose brick','old red brick','burnt brick','old red brick')[(7*j+k*3+j//3+k//2)%5]
                face.prism(b,-.002,.009,color,'staggered brickwork')
    return a

def frame(f,u,z,w,h,lod,arched=False,label='street windows',cols=3,rows=5):
    a=opening(u,z,w,h,.17 if arched else 0,14 if not lod else 8)
    f.prism(a,-.31,-.282,'window glass',label+'/set-back glass')
    inner=a.buffer(-.061,join_style=2);bars=[]
    for j in range(1,cols):
        x=u-w/2+w*j/cols;bars.append(box(x-.018,z,x+.018,z+h))
    for j in range(1,rows):
        t=z+h*j/rows;bars.append(box(u-w/2,t-.023,u+w/2,t+.023))
    f.prism(a.difference(inner.difference(union_all(bars))),-.231,-.17,'metal sash',label+'/steel glazing bars')
    f.box(u,z-.054,w+.16,.105,.21,.025,'grey stone sill',label+'/sills')
    if arched:
        ring=a.buffer(.18,join_style=2).difference(a).intersection(box(u-w,z+h-.16,u+w,z+h+.24))
        f.prism(ring,.012,.107,'burnt brick','segmental brick lintels')
        if not lod:
            for k in range(1,10):
                x=u-w*.53+w*1.06*k/10;z0=z+h-.17*(2*(x-u)/w)**2
                f.box(x,z0+.090,.020,.145,.031,.112,'red pointing','lintel joints')
    return a

def ledge(f,z,depth,medium='cream concrete'):
    f.box(0,z-.12,f.length+.04,.22,depth+.33,(depth-.33)/2,medium,'cornice bed')
    f.box(0,z+.027,f.length+.07,.12,depth+.48,(depth-.22)/2,'grey stone sill','weathering lip')
    f.box(0,z+.12,f.length+.12,.074,depth+.50,(depth-.19)/2,'dark green flashing','green metal edge')

def parapet(f,z,lod):
    outline=box(-f.length/2,z,f.length/2,z+.64)
    n=max(2,round(f.length/.60));step=f.length/n
    void=[]
    for j in range(n):
        x=(j+.5)*step-f.length/2;w=.235 if j%5==2 else .088
        void.append(box(x-w/2,z+.17 if j%5==2 else z+.10,x+w/2,z+.4 if j%5==2 else z+.55))
    f.prism(outline.difference(union_all(void)),.245,.445,'cream concrete','pierced parapet')
    f.box(0,z+.666,f.length+.09,.10,.36,.345,'cream concrete','parapet cap')
    f.box(0,z-.032,f.length+.10,.10,.48,.275,'grey stone sill','parapet base')

def gutter(f,u,z0,z1,lod):
    if lod:return
    f.line((u,z0,.13),(u,z1-.68,.13),.051,'dark green flashing',8,'rainwater leaders')
    f.line((u,z1-.68,.13),(u,z1-.11,.42),.052,'dark green flashing',8,'offset below cornice')

def primary(f,count,side,lod):
    centers=[(j-(count-1)/2)*(f.length/count) for j in range(count)]
    holes=[]
    for u in centers:
        holes.extend([frame(f,u,.47,1.40 if not side else 1.56,3.48,lod,True,'lower office sashes'),
                      frame(f,u,5.07,1.55,3.38,lod,False,'mid-level sashes'),
                      frame(f,u,10.08,1.70,2.80,lod,False,'upper office sashes')])
    field(f,0,13.22,holes,lod)
    for u in centers:
        f.box(u,4.82,1.73,.24,.25,.055,'grey granite','projected window sills')
    # Two thin courses of raised brick articulate the second storey spandrels.
    for z,h,mat in [(4.18,.092,'burnt brick'),(4.43,.16,'old red brick')]:
        f.box(0,z,f.length,h,.27,.044,mat,'masonry band over segmental heads')
    for j in range(count+1):
        x=-f.length/2+j*f.length/count;w=.26 if j in (0,count)else .49
        x+=w/2 if j==0 else -w/2 if j==count else 0
        f.box(x,6.91,w,4.48,.30,.06,'old red brick','individual brick piers')
        f.box(x,4.76,w+.05,.17,.34,.07,'grey stone sill','small pier foot')
    ledge(f,9.18,.47);parapet(f,9.25,lod)
    ledge(f,13.23,.42,'shaded render')
    for u in centers[1::3]:gutter(f,u+1.1,.17,13.26,lod)

def upper_step(b,x0,x1,y0,y1,z0,z1,number,lod,label):
    # The photo records a direct street-facing window row on each successive terrace.
    f=Facade(b,(x0,y0),(x1,y0),label);holes=[]
    for j in range(number):
        u=(j-(number-1)/2)*f.length/number
        holes.append(frame(f,u,z0+.39,1.43 if number==6 else 1.37,z1-z0-.75,lod,False,'clerestory sashes',3,2))
    field(f,z0,z1,holes,lod);ledge(f,z1,.37,'shaded render')
    for x,reverse in [(x0,True),(x1,False)]:
        edge=Facade(b,(x,y1)if reverse else(x,y0+.35),(x,y0+.35)if reverse else(x,y1),label+'/return')
        if edge.length>3.3:
            hole=frame(edge,0,z0+.46,1.32,z1-z0-.84,lod,False,'return window',2,2)
            field(edge,z0,z1,[hole],lod)
        else:field(edge,z0,z1,[],lod)
        ledge(edge,z1,.32,'shaded render')
    b.plan_prism(box(x0-.02,y0-.03,x1+.02,y1),z1-.01,z1+.12,'roof felt',label+'/terrace roof')
    b.box(((x0+x1)/2,y1,(z0+z1)/2),(x1-x0,.075,z1-z0),'plain cut',label=label+'/neutral section')

def lantern(b,lod):
    cx,cy=SHAFT_X,SHAFT_Y
    # Four faces of the narrower tower, separated from the projecting lookout.
    radius=2.22;x0,x1=cx-radius,cx+radius;y0,y1=cy-radius,cy+radius
    ring=[(x0,y0),(x1,y0),(x1,y1),(x0,y1)]
    for i,(a,e) in enumerate(zip(ring,ring[1:]+ring[:1])):
        f=Facade(b,a,e,'Tower '+('street','west','rear','east')[i]);holes=[]
        if i in (0,1):
            for z,w,h in [(2.18,1.50,3.19),(6.31,1.56,2.83),(13.15,1.76,2.59)]:
                holes.append(frame(f,0,z,w,h,lod,False,'shaft sashes',3,4))
            f.box(0,16.07,2.11,.49,.27,.04,'cream concrete','square hood over shaft window')
        # On the heavily obscured inner and rear faces the shaft is plain.
        if i<2:field(f,.08,17.99,holes,lod)
        else:f.wall(0,17.99,[],.29,'old red brick')
        ledge(f,9.18,.47);parapet(f,9.25,lod)
        f.box(0,17.72,f.length,.38,.41,.026,'cream concrete','lantern sill')
        parapet(f,17.91,lod)
    # Eight glazed faces are separated by actual solid corner piers. The
    # corners are clipped as in the close view of the white lookout.
    b.plan_prism(box(x0-.05,y0-.05,x1+.05,y1+.05),18.04,18.21,'cream concrete','Lookout/sill slab')
    r=2.07;s=.78
    octa=[(-r+s,-r),(r-s,-r),(r,-r+s),(r,r-s),(r-s,r),(-r+s,r),(-r,r-s),(-r,-r+s)]
    pts=[(cx+x,cy+y)for x,y in octa]
    for j,(a,e)in enumerate(zip(pts,pts[1:]+pts[:1])):
        f=Facade(b,a,e,'Lookout glazed lantern')
        w=f.length-.18;ap=frame(f,0,18.66,w,2.12,lod,False,'pavilion lights',3 if w>1.6 else 2,3)
        f.wall(18.20,21.32,[ap],.18,'cream concrete')
    b.plan_prism(Polygon(pts).buffer(.07,join_style=2),21.0,21.37,'cream concrete','Lookout/solid cornice')
    canopy(b,cx,cy,lod)

def canopy(b,cx,cy,lod):
    # Upturned corners and a shallow concave slope under the tall square cone.
    n=10 if lod else 18
    def border(i,t,r):
        a=np.array([(-1,-1),(1,-1),(1,1),(-1,1)][i]);q=np.array([(-1,-1),(1,-1),(1,1),(-1,1)][(i+1)%4]);return (a*(1-t)+q*t)*r
    for side in range(4):
        rings=[]
        for r,z,amount in [(1.63,22.02,.03),(2.24,21.72,.09),(2.73,21.42,.23),(3.05,21.40,.63)]:
            verts=[]
            for j in range(n+1):
                t=j/n;x,y=border(side,t,r);verts.append((cx+x,cy+y,z+amount*abs(2*t-1)**3))
            rings.append(verts)
        for j in range(3):
            strip=rings[j]+rings[j+1];faces=[(k,k+1,n+2+k,n+1+k)for k in range(n)]
            b.add(strip,faces,'green tile','Pavilion roof/upturned tile canopy')
        rim=rings[-1];b.add(rim+[(x,y,z-.13)for x,y,z in rim],[(k,k+1,n+2+k,n+1+k)for k in range(n)],'eaves wood','Pavilion roof/exposed fascia')
        b.add([(cx,cy,21.29)]+[(x,y,z-.13)for x,y,z in rim],[(0,k+2,k+1)for k in range(n)],'pavilion soffit','Pavilion roof/shaded soffit')
        # Clearly visible green tile rows and corner ridges on the steep pyramid.
        low0=border(side,0,1.70);low1=border(side,1,1.70)
        top0=border(side,0,.25);top1=border(side,1,.25)
        b.add([(cx+low0[0],cy+low0[1],21.94),(cx+low1[0],cy+low1[1],21.94),(cx+top1[0],cy+top1[1],26.18),(cx+top0[0],cy+top0[1],26.18)],
              [(0,1,2,3)],'green tile','Pavilion roof/steep green pyramidal roof')
        count=7 if lod else 13
        for j in range(count):
            t=j/count;v=border(side,t,1.70);w=border(side,t,.25)
            b.tube([(cx+v[0],cy+v[1],21.97),(cx+w[0],cy+w[1],26.21)],.029 if j else .047,'tile ridges',5,'Pavilion roof/standing tile ribs')
        if not lod:
            for j in range(1,15):
                t=j/15;v=border(side,0,1.70*(1-t)+.25*t);w=border(side,1,1.70*(1-t)+.25*t)
                b.tube([(cx+v[0],cy+v[1],21.96+4.24*t),(cx+w[0],cy+w[1],21.96+4.24*t)],.014,'tile ridges',4,'Pavilion roof/horizontal tile courses')
    b.box((cx,cy,26.34),(.54,.54,.34),'cream concrete',label='Pavilion roof/pale apex bearing')
    apex=[(cx-.32,cy-.32,26.5),(cx+.32,cy-.32,26.5),(cx+.32,cy+.32,26.5),(cx-.32,cy+.32,26.5),(cx,cy,26.76)]
    b.add(apex,[(0,1,4),(1,2,4),(2,3,4),(3,0,4)],'grey stone sill','Pavilion roof/low finial')

def building(b,lod):
    f=Facade(b,(-HW,.01),(HW,.01),'East Daming Road')
    primary(f,7,False,lod)
    # West return visible beside the tower in the 2014 street photograph.
    ret=Facade(b,(HW,.01),(HW,9.03),'West return')
    primary(ret,3,True,lod)
    b.plan_prism(box(-HW,.015,HW,BACK),13.24,13.39,'roof felt','Street block/front terrace slab')
    b.box((-HW+.036,BACK/2,6.67),(.072,BACK,13.34),'red pointing',label='Street block/short end')
    b.box((0,BACK-.035,6.67),(HW*2,.07,13.34),'plain cut',label='Street block/neutral section')
    upper_step(b,-11.9,11.6,2.01,BACK,13.34,16.08,6,lod,'Fourth storey')
    upper_step(b,-8.6,8.8,4.42,BACK,16.20,18.42,4,lod,'Fifth storey')
    # A pale upper wall and one dark sash are visible between the last terrace
    # and the brick tower. The narrow return ends at the tower's north face.
    join=Facade(b,(8.65,6.84),(12.15,6.84),'Short upper link')
    ap=frame(join,0,14.35,1.13,1.80,lod,False,'short link sash',2,3)
    join.wall(13.29,17.32,[ap],.30,'shaded render')
    side=Facade(b,(12.15,7.14),(12.15,9.08),'Short upper link side')
    side.wall(13.29,17.32,[],.30,'shaded render')
    b.plan_prism(box(8.65,6.84,12.15,9.08),17.30,17.44,'dark green flashing','Short upper link/roof')
    b.plan_prism(box(11.48,7.18,13.88,9.04),13.18,13.38,'roof felt','West return/link terrace')
    b.box((11.52,8.11,6.62),(.08,1.89,13.24),'plain cut',label='West return/rear section')
    b.box((0,-.004,.080),(HW*2,.20,.16),'grey granite',label='East Daming Road/low stone foundation')
    lantern(b,lod)
