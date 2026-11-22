"""Upper gable of the paired Tang garden houses. Dimensions use a nominal sash width of 1.20 m."""
from math import hypot

def paint(rgb,rough=.87):
    return {'color':[n/3294.6 if n<11 else ((n/255+.055)/1.055)**2.4 for n in rgb],'roughness':rough}
BRICKS=['burnt sienna','red ochre','umber brick','rose brick']
PALETTE={k:paint(v)for k,v in {'burnt sienna':(143,77,60),'red ochre':(156,88,69),'umber brick':(133,73,58),'rose brick':(166,96,78),
 'pale mortar':(174,143,125),'blue grey stone':(156,159,153),'grey edge':(178,180,176),'iron painted pale grey':(178,185,177),'sash red':(119,51,42),'wood shadow':(78,47,39),'ochre awning':(211,173,72),'shade return':(156,124,59),'steel outrigger':(80,83,75),'reflected blue':(129,151,170),'reflected gold':(165,143,94),'sky reflection':(146,167,183)}.items()}

def rectify(u,v):
    d=1-.00005386039015484505*u+.00004602515339975119*v
    return (.007870437701085326*u-.00022731245425621974*v-1.9003293740718754)/d,(-.003186649388646107*u-.009139069944796374*v+4.908281814957285)/d+.43

def slab(b,poly,y0,y1,mat,name,front_only=False):
    if not poly:return
    area=sum(x*v-z*u for (x,z),(u,v) in zip(poly,poly[1:]+poly[:1]))
    if abs(area)<1e-7:return
    if area<0:poly=poly[::-1]
    n=len(poly);vertices=[(x,y,z) for y in (y0,y1)for x,z in poly]
    faces=[(0,i,i+1) for i in range(1,n-1)]
    if front_only:b.add(vertices[:n],faces,mat,name);return
    faces.extend((n,n+i+1,n+i) for i in range(1,n-1))
    for i in range(n):
        j=(i+1)%n;faces.extend([(i,n+i,n+j),(i,n+j,j)])
    b.add(vertices,faces,mat,name)

def rect(x0,z0,x1,z1):
    return [(x0,z0),(x1,z0),(x1,z1),(x0,z1)]

def clip(poly,a,c,side):
    out=[]
    def value(p):return side*((c[0]-a[0])*(p[1]-a[1])-(c[1]-a[1])*(p[0]-a[0]))
    for start,end in zip(poly[-1:]+poly[:-1],poly):
        d,e=value(start),value(end)
        if (d>=0)!=(e>=0):
            t=d/(d-e);out.append(tuple(x+t*(y-x) for x,y in zip(start,end)))
        if e>=0:out.append(end)
    return out

def inside(poly,frame):
    for a,c in zip(frame,frame[1:]+frame[:1]):poly=clip(poly,a,c,1)
    return poly

def minus(poly,frame):
    for a,c in zip(frame,frame[1:]+frame[:1]):
        fragment=clip(poly,a,c,-1)
        if fragment:yield fragment
        poly=clip(poly,a,c,1)

def strap(b,a,c,width,y0,y1,mat,name):
    x,z=a;u,v=c;L=hypot(u-x,v-z);dx=-(v-z)*width/2/L;dz=(u-x)*width/2/L
    slab(b,[(x+dx,z+dz),(x-dx,z-dz),(u-dx,v-dz),(u+dx,v+dz)],y0,y1,mat,name)

def add_building(b,lod=False):
    left=rectify(-38,460);right=rectify(607,280);top=rectify(238,-21)
    wall=[(left[0],0),(right[0],0),right,top,left]
    opening=rect(-.60,.43,.60,1.87)
    for part in minus(wall,opening):slab(b,part,.009,.264,'pale mortar','mortar wall with an open attic bay')
    brick_width=.195;row_height=.064
    for row in range(77):
        z0=row*row_height
        for col in range(28):
            x0=-2.40+col*brick_width-(row%2)*brick_width*.5
            poly=inside(rect(x0+.003,z0+.003,x0+brick_width-.003,z0+row_height-.003),wall)
            for part in minus(poly,opening):slab(b,part,0,.011,BRICKS[(col+3*row)%4],f'garden gable brick course {row+1:02}',front_only=lod)
    for i,n in enumerate((left,right)):
        strap(b,n,top,.095,-.054,.272,'grey edge',('left','right')[i]+' coping to gable ridge')
    slab(b,rect(-.60,.43,.60,1.87),.184,.215,'wood shadow','shadowed window recess')
    for side,(low,high) in enumerate([(-.503,-.044),(.083,.531)]):
        for band,(z0,z1) in enumerate([(.505,.826),(.845,1.120),(1.143,1.386),(1.406,1.650)]):
            mat=('sky reflection','reflected blue','sky reflection','reflected gold')[band]
            slab(b,rect(low,z0,high,z1),.144,.178,mat,f'leaf {side+1} glazing light {band+1}')
        for z in (.835,1.131,1.396):
            slab(b,rect(low,z-.011,high,z+.011),.094,.152,'sash red',f'leaf {side+1} three horizontal glazing bars')
    for lo,hi,name in [(-.60,-.505,'left jamb'),(-.044,.021,'left meeting stile'),(.021,.083,'right meeting stile'),(.532,.60,'right jamb')]:
        slab(b,rect(lo,.43,hi,1.87),.080,.179,'sash red',name)
    for lo,hi,name in [(.43,.505,'timber lower frame'),(1.651,1.87,'broad timber head')]:
        slab(b,rect(-.60,lo,.60,hi),.079,.17,'sash red',name)
    for coords,front,mat,name in [
      ([(142,487),(345,413),(348,432),(144,506)],-.122,'blue grey stone','projecting stone sill'),
      ([(151,283),(330,218),(337,228),(158,297)],-.117,'grey edge','stone head upper edge'),
      ([(158,297),(337,228),(320,265),(174,319)],-.074,'blue grey stone','stone head tapered towards the frame')]:
        slab(b,[rectify(*p)for p in coords],front,.04,mat,name)
    # Three rectangular tips are exposed above the hood. The far lower corner vanishes behind it.
    for i,path in enumerate([[(243,118),(278,143)],[(239,120),(213,169)],[(276,145),(254,173)],[(211,170),(232,185)],
            [(231,113),(240,94),(250,100),(243,118),(231,113)],
            [(270,140),(280,123),(290,129),(282,145),(270,140)],
            [(198,177),(207,158),(217,164),(208,184),(198,177)]]):
        for a,c in zip(path,path[1:]):strap(b,rectify(*a),rectify(*c),.021 if i<4 else .028,-.045,.006,'iron painted pale grey','anchor strap and three visible eyelets')
    # The slope and return of the small sheet-metal hood are visible in the reference.
    x0,x1=-.82,.71;back,front=-.047,-.31;zback,zfront=2.86,2.72
    v=[(x,y,z+t)for t in (0,.030)for x,y,z in [(x0,front,zfront),(x1,front,zfront),(x1,back,zback),(x0,back,zback)]]
    f=[(0,2,1),(0,3,2),(4,5,6),(4,6,7),(0,1,5),(0,5,4),(1,2,6),(1,6,5),(2,3,7),(2,7,6),(3,0,4),(3,4,7)]
    b.add(v,f,'ochre awning','ochre hood tilted away from gable')
    slab(b,rect(x0,zfront-.052,x1,zfront),front-.006,front+.014,'shade return','folded front edge of hood')
    for i,x in enumerate([-.71,.04,.63]):
        b.tube([(x,-.014,2.49),(x,front+.03,zfront-.025)],.014,'steel outrigger',6 if lod else 10,f'awning steel outrigger {i+1}')
