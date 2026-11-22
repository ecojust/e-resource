"""Fan-laid brick voussoirs and upper timber sash of the lane corner at Songyun Villas."""
from bisect import bisect_right
H=[[0.009150167768821327, -0.0006576946160509804, -3.7401294040295845], [0.00041795088799880827, -0.008048952193099384, 2.5324117648200195], [-0.0004038602609397319, 0.00015027517873981918, 1.0]]
UPPER=[[52, 90], [80, 78], [113, 66], [151, 58], [190, 54], [221, 55], [259, 61], [300, 71], [342, 86], [386, 105], [419, 125], [452, 147], [463, 156]]
LOWER=[[101, 160], [126, 151], [152, 146], [179, 143], [209, 144], [244, 148], [280, 155], [316, 164], [350, 175], [382, 186], [410, 196], [431, 201]]
JOINTS=[0, 0.039, 0.077, 0.116, 0.156, 0.197, 0.234, 0.277, 0.319, 0.362, 0.407, 0.45, 0.494, 0.534, 0.576, 0.614, 0.65, 0.686, 0.727, 0.765, 0.802, 0.839, 0.88, 0.919, 0.955, 1]

def finish(rgb,roughness=.83):
    def linear(c):
        v=c/255
        return v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4
    return dict(color=[linear(v) for v in rgb],roughness=roughness,metallic=0)
PALETTE={name:finish(rgb)for name,rgb in [('render',(169,162,149)),('mortar',(156,133,117)),('brown brick',(102,69,63)),('red brick',(127,78,62)),('purple brick',(91,65,63)),('dark cap',(85,64,64)),('sash',(79,64,60)),('glazing bead',(98,80,71)),('brick band',(125,92,76)),('eaves recess',(91,75,69))]}
PALETTE['blue reflected glass']=finish((82,107,133),.26)
PALETTE['warm reflected glass']=finish((153,143,117),.31)

def local(uv):
    u,v=uv;w=H[2][0]*u+H[2][1]*v+1
    return ((H[0][0]*u+H[0][1]*v+H[0][2])/w,(H[1][0]*u+H[1][1]*v+H[1][2])/w)

def prism(b,polygon,front,back,material,label):
    # Polygon vertices live on the rectified photographed wall plane, so depths remain independent of the camera.
    area=sum(a[0]*c[1]-c[0]*a[1] for a,c in zip(polygon,polygon[1:]+polygon[:1]))
    if area<0:polygon=polygon[::-1]
    n=len(polygon);points=[(x,y,z) for y in (front,back) for x,z in polygon];faces=[tuple(range(n)),tuple(reversed(range(n,2*n)))]
    for k in range(n):faces.append(((k+1)%n,k,k+n,(k+1)%n+n))
    b.add(points,faces,material,label)

def rectangle(b,x0,x1,z0,z1,y,back,mat,name):prism(b,[(x0,z0),(x1,z0),(x1,z1),(x0,z1)],y,back,mat,name)

def refcurve(curve,t):
    x=curve[0][0]+(curve[-1][0]-curve[0][0])*t
    idx=min(len(curve)-2,max(0,bisect_right([p[0]for p in curve],x)-1));x0,y0=curve[idx];x1,y1=curve[idx+1]
    y=y0+(y1-y0)*(x-x0)/(x1-x0)
    return local((321+x/2.7,100+y/2.7))

def point_on_brick(t,s):
    top=refcurve(UPPER,t);low=refcurve(LOWER,t)
    return (top[0]+s*(low[0]-top[0]),top[1]+s*(low[1]-top[1]))

def face_region(b,t0,t1,s0,s1,depth,back,mat,name):
    prism(b,[point_on_brick(t0,s0),point_on_brick(t1,s0),point_on_brick(t1,s1),point_on_brick(t0,s1)],depth,back,mat,name)

def fired_front(b,t0,t1,s0,s1,material,label,lod):
    shape=[point_on_brick(t0,s0),point_on_brick(t1,s0),point_on_brick(t1,s1),point_on_brick(t0,s1)]
    if lod:
        prism(b,shape,-.034,.089,material,label)
        return
    shape=shape[::-1]
    center=tuple(sum(p[i] for p in shape)/len(shape) for i in range(2))
    vertices=[]
    for depth,inset in [(-.034,.046),(-.030,0),(.089,0)]:
        for x,z in shape:vertices.append((x+(center[0]-x)*inset,depth,z+(center[1]-z)*inset))
    faces=[(0,1,2,3),(11,10,9,8)]
    for r in range(2):
        for k in range(4):faces.append((r*4+(k+1)%4,r*4+k,(r+1)*4+k,(r+1)*4+(k+1)%4))
    b.add(vertices,faces,material,label)

def brick_name(i):return ('brown brick','red brick','brown brick','purple brick','red brick')[i%5]

def add_building(b,lod=False):
    # Bright mortar joints separate neighbouring long bricks, including the distinct split courses.
    for i,(t0,t1)in enumerate(zip(JOINTS,JOINTS[1:])):
        face_region(b,t0,t1,0,1,-.017,.16,'mortar',f'setting bed {i+1:02d}')
        if i in (1,4,6,8,10,13,16,18,20,23):rows=[(0,.48),(.514,1)]
        else:rows=[(0,1)]
        for j,(s0,s1)in enumerate(rows):
            fired_front(b,t0+.0019,t1-.0019,s0,s1,brick_name(i),f'fan brick {i+1:02d} part {j+1}',lod)
        # Dark outer rim overhangs the springings on both sides.
        face_region(b,t0,t1,-.17,.018,-.071,.11,'dark cap',f'curved oversailing trim {i+1:02d}')
        a=point_on_brick(t0,-.17);c=point_on_brick(t1,-.17)
        prism(b,[a,c,(c[0],2.30),(a[0],2.30)],.01,.19,'render',f'plaster over head segment {i+1:02d}')
        a=point_on_brick(t0,1);c=point_on_brick(t1,1)
        prism(b,[a,c,(c[0],1.55),(a[0],1.55)],-.013,.12,'brick band',f'brick band over lintel {i+1:02d}')
    for side,t in [('left',0),('right',1)]:
        up=point_on_brick(t,-.17);lo=point_on_brick(t,1);edge=-1.0 if t==0 else 1.0
        prism(b,[(edge,2.3),(up[0],2.3),up,lo,(lo[0],1.55),(edge,1.55)],.012,.19,'render',side+' spandrel return')
        rectangle(b,min(edge,lo[0]),max(edge,lo[0]),.20,1.55,.012,.19,'render',side+' reveal')
    for k,(x0,x1)in enumerate([(-.63,-.566),(-.042,.038),(.566,.63)]):
        rectangle(b,x0,x1,.20,1.55,.104,.198,'sash',f'outer stile or paired meeting stile {k+1}')
    for k,(z0,z1) in enumerate([(.789,.859),(1.48,1.55)]):
        rectangle(b,-.622,.622,z0,z1,.086,.198,'sash',f'head or crossbar {k+1}')
    for i,(x0,x1)in enumerate([(-.565,-.043),(.039,.565)]):
        for j,(z0,z1)in enumerate([(.20,.789),(.859,1.48)]):
            rectangle(b,x0,x1,z0,z1,.149,.174,'warm reflected glass' if i==1 and j==1 else 'blue reflected glass',f'pair {i+1} light {j+1}')
            if not lod:
                for x in [x0+.007,x1-.007]:rectangle(b,x-.007,x+.007,z0,z1,.119,.152,'glazing bead',f'glazing fillet {i} {j} {x:.2f}')
    rectangle(b,-1.01,1.01,2.28,2.36,-.034,.24,'eaves recess','continuous bed beneath the actual eaves')
    rectangle(b,-1.04,1.04,2.36,2.40,-.060,.25,'brick band','narrow cornice moulding')
    for i in range(11):
        x=-.944+i*.187
        rectangle(b,x-.048,x+.048,2.264,2.337,-.076,.04,'brown brick',f'eaves dentil {i+1}')
