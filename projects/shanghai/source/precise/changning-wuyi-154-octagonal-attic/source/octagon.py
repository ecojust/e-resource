"""Observed attic opening and soldier courses at 154 Wuyi Road, from Antigng's 2018 photograph."""

# Origin is centered on the observation crop. One pixel is nominally 9 mm from the brick courses.
ORIGIN = (170, 321)
SCALE = .009
INNER = [(146,195),(190,195),(216,221),(219,259),(190,287),(150,288),(121,261),(121,224)]
OUTER = [(141,184),(195,183),(230,217),(232,264),(195,299),(145,301),(107,266),(106,220)]
WALL = [(60,102),(274,100),(274,258),(202,320),(60,323)]
GLASS = [(148,202),(187,202),(209,224),(210,257),(187,280),(153,281),(129,258),(129,227)]
BRICKS = ['oxblood brick','brown brick','terracotta brick','faded red brick']

def paint(rgb,rough=.85):
    return dict(color=[v/3294.6 if v<11 else ((v/255+.055)/1.055)**2.4 for v in rgb],roughness=rough)
PALETTE={k:paint(v) for k,v in {
    'pink lime mortar':(155,105,85),'oxblood brick':(131,66,52),'brown brick':(139,75,56),
    'terracotta brick':(151,81,61),'faded red brick':(164,88,67),'brick in reveal':(109,59,47),
    'dark sash':(72,55,45),'interior shadow':(37,39,39),'eaves shadow':(87,58,45),
    'warm fascia':(127,93,73),'pale gutter rim':(157,137,117)}.items()}

def xy(p):
    u,v=p
    return (u-ORIGIN[0])*SCALE,(ORIGIN[1]-v)*SCALE

def slab(b,poly,y0,y1,material,name,face_only=False):
    if len(poly)<3:return
    points=[xy(p) for p in poly]
    area=sum(a[0]*c[1]-a[1]*c[0] for a,c in zip(points,points[1:]+points[:1]))/2
    if abs(area)<1e-8:return
    if area<0:points.reverse()
    n=len(points);vertices=[(x,y,z) for y in (y0,y1) for x,z in points]
    if face_only:
        b.add(vertices[:n],[(0,i,i+1) for i in range(1,n-1)],material,name)
        return
    faces=[]
    for i in range(1,n-1):faces.extend([(0,i,i+1),(n,n+i+1,n+i)])
    for i in range(n):
        j=(i+1)%n;faces.extend([(i,n+i,n+j),(i,n+j,j)])
    b.add(vertices,faces,material,name)

def rect(x0,y0,x1,y1):return [(x0,y0),(x1,y0),(x1,y1),(x0,y1)]

def cut(poly,a,c,inside=True):
    """Clip to a signed half plane in clockwise image coordinates."""
    def distance(p):return ((c[0]-a[0])*(p[1]-a[1])-(c[1]-a[1])*(p[0]-a[0]))*(1 if inside else -1)
    out=[]
    for start,end in zip(poly[-1:]+poly[:-1],poly):
        x,y=distance(start),distance(end)
        if (x>=0)!=(y>=0):
            t=x/(x-y);out.append((start[0]+t*(end[0]-start[0]),start[1]+t*(end[1]-start[1])))
        if y>=0:out.append(end)
    return out

def inside(poly,frame):
    for a,c in zip(frame,frame[1:]+frame[:1]):
        if not poly:break
        poly=cut(poly,a,c)
    return poly

def outside(poly,frame):
    """Return disjoint convex pieces of a polygon outside the convex frame."""
    for a,c in zip(frame,frame[1:]+frame[:1]):
        if not poly:return
        part=cut(poly,a,c,False)
        if part:yield part
        poly=cut(poly,a,c)

def ring(b,outer,inner,divisions,front,back,material,label,joints=False):
    def along(a,c,t):return (a[0]+(c[0]-a[0])*t,a[1]+(c[1]-a[1])*t)
    for side,count in enumerate(divisions):
        nxt=(side+1)%len(outer)
        for j in range(count):
            gap=.04 if joints else 0
            lo=(j+gap)/count;hi=(j+1-gap)/count
            part=[along(outer[side],outer[nxt],lo),along(outer[side],outer[nxt],hi),
                  along(inner[side],inner[nxt],hi),along(inner[side],inner[nxt],lo)]
            mat=material[(side+j)%len(material)]
            slab(b,part,front,back,mat,f'{label} side {side+1}')

def add_building(b,lod=False):
    for part in outside(WALL,INNER):slab(b,part,.008,.24,'pink lime mortar','solid lime joints around octagon')
    # Lay running bond up to the outer ring, cut to the boundary of the observed facade.
    row=0;v=153
    while v<325:
        x=48-(12 if row%2 else 0);col=0
        while x<274:
            shaped=inside(rect(x+.35,v+.35,x+23.7,v+6.02),WALL)
            for part in outside(shaped,OUTER):
                slab(b,part,0,.010,BRICKS[(col+row*3)%4],f'brickwork course {row+1:02}',face_only=lod)
            x+=24;col+=1
        v+=6.55;row+=1
    ring(b,OUTER,INNER,[5,6,4,6,6,6,5,6],-.006,.010,BRICKS,'octagon voussoir',True)
    ring(b,INNER,GLASS,[1]*8,.006,.134,['brick in reveal'],'deep octagon inner soffit')
    ring(b,GLASS,[(170+(x-170)*.95,242+(y-242)*.95) for x,y in GLASS],[1]*8,.126,.145,['dark sash'],'inner sash')
    slab(b,GLASS,.147,.164,'interior shadow','shadow behind the attic sash')
    slab(b,inside([(115,240.8),(223,238.3),(223,242.1),(115,245.2)],INNER),.063,.092,'dark sash','single horizontal sash bar')
    for i in range(29):
        x=57+i*7.65
        for lo,hi,front,label in [(124.4,133,-.018,'short upper brick heads'),(133.7,151.9,-.014,'long upright brick course')]:
            part=inside(rect(x+.32,lo,x+7.3,hi),WALL)
            slab(b,part,front,.012,BRICKS[(i+int(lo))%4],label)
    slab(b,inside(rect(58,119,275,124),WALL),-.053,.013,'oxblood brick','corbel above the two brick courses')
    slab(b,inside(rect(58,104,275,119),WALL),-.11,.013,'eaves shadow','dark fascia under projecting roof')
    slab(b,inside(rect(58,100,275,104.4),WALL),-.145,.018,'pale gutter rim','light lower rim of eaves')
