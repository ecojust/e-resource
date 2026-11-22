"""Surveyed proportions of the street-visible gabled school wing, Julu Road 334."""
from math import cos, pi, sin

def pigment(rgb,roughness,metallic=0):
    def linear(v):
        s=v/255
        return s/12.92 if s<=.04045 else ((s+.055)/1.055)**2.4
    return dict(color=[linear(v) for v in rgb],roughness=roughness,metallic=metallic)
PALETTE={'white lime render':pigment((224,219,204),.92),'cream sill':pigment((189,181,164),.86),
         'ochre gable bed':pigment((134,112,93),.90),'tile shadow':pigment((118,67,48),.89),
         'red clay tiles':pigment((173,98,72),.86),'pale painted frame':pigment((191,191,175),.75),
         'shadowed reveal':pigment((82,76,65),.90),'pale reflected glass':pigment((120,133,133),.38,.13),
         'shaded top glass':pigment((65,76,76),.48,.08),'glazing seal':pigment((87,90,80),.72)}
# X and Z use the 2021 rectilinear reference. Window breadth is nominally 1.30 m.
def x(u):return (u-202)*.025
def z(v):return (228-v)*.025
def contour(b,pixels,front,back,mat,label):
    points=[(x(u),z(v))for u,v in pixels]
    area=sum(a[0]*c[1]-a[1]*c[0]for a,c in zip(points,points[1:]+points[:1]))
    if area<0:points.reverse()
    n=len(points);v=[[u,y,h]for y in (front,back) for u,h in points]
    faces=[list(range(n)),list(reversed(range(n,n*2)))]
    faces.extend([[i,i+n,(i+1)%n+n,(i+1)%n]for i in range(n)])
    b.add(v,faces,mat,label)
def box(b,l,r,top,bottom,front,back,mat,label):
    contour(b,[(l,top),(r,top),(r,bottom),(l,bottom)],front,back,mat,label)
def sloping_edge(b,start,end,y0,y1,thick,height,mat,label,lod=False):
    u1,v1=start;u2,v2=end
    a,c=(x(u1),z(v1)),(x(u2),z(v2));dx,dz=c[0]-a[0],c[1]-a[1];norm=(dx**2+dz**2)**.5
    side=(-dz/norm,dx/norm)
    if side[1]<0:side=(-side[0],-side[1])
    profile=[(-thick/2,y1),(-thick/2,y0),(-thick/2+height,y0-height),(thick/2-height,y0-height),(thick/2,y0),(thick/2,y1)]
    if lod:profile=[(-thick/2,y1),(-thick/2,y0),(thick/2,y0),(thick/2,y1)]
    n=len(profile)
    verts=[[u+side[0]*s,y,h+side[1]*s]for u,h in [a,c]for s,y in profile]
    faces=[list(range(n)),list(reversed(range(n,2*n)))]+[[i,i+n,(i+1)%n+n,(i+1)%n] for i in range(n)]
    vol=0
    for f in faces:
        va=verts[f[0]]
        for i in range(1,len(f)-1):
            vb,vc=verts[f[i]],verts[f[i+1]]
            vol+=va[0]*(vb[1]*vc[2]-vb[2]*vc[1])+va[1]*(vb[2]*vc[0]-vb[0]*vc[2])+va[2]*(vb[0]*vc[1]-vb[1]*vc[0])
    b.add(verts,faces if vol>0 else [f[::-1]for f in faces],mat,label)
def add_building(b,lod):
    wall='white lime render'
    # The rectangular opening interrupts the actual facade. No glass-facing wall overlaps it.
    contour(b,[(148,123),(202,5),(255,119),(255,128),(148,128)],0,.38,wall,'lime rendered gable triangle')
    box(b,148,176,128,227,0,.38,wall,'left gable wall')
    box(b,231,255,128,227,0,.38,wall,'right gable wall')
    box(b,176,231,174.5,227,0,.38,wall,'window spandrel')
    box(b,148,255,217,223,-.018,.02,'cream sill','rendered floor string visible below window')
    for side,start,end in [('left',(140,125),(201.8,2)),('right',(201.8,2),(261,119))]:
        stu=lambda t:(start[0]*(1-t)+end[0]*t,start[1]*(1-t)+end[1]*t)
        sloping_edge(b,start,end,-.115,.60,.23,.023,'ochre gable bed',side+' ochre board under tiles',lod)
        sloping_edge(b,stu(.002),stu(.998),-.14,.63,.15,.017,'tile shadow',side+' continuous verge bed',lod)
        for i in range(13):
            off=lambda t:(stu(t)[0],stu(t)[1]-2.3)
            sloping_edge(b,off((i+.027)/13),off((i+.975)/13),-.172,.62,.106,.014,
                         'red clay tiles',f'{side} verge tile section {i+1:02d}',lod)
    box(b,174.5,232,127.3,131.2,-.055,.26,'shadowed reveal','dark projecting lintel')
    box(b,175.4,231.5,173.2,176,-.042,.24,'cream sill','projecting lower sill')
    box(b,176,177.75,130.2,174,.018,.19,'cream sill','left reveal')
    box(b,229.2,231,130.2,174,.018,.19,'cream sill','right reveal')
    box(b,177.6,229.3,130.6,173.4,.195,.214,'shadowed reveal','deep window back')
    for ri,(top,bottom) in enumerate([(132,143.2),(145.3,172.7)]):
        for ci,(l,r) in enumerate([(178.5,192.2),(194,210.2),(212,228.8)]):
            box(b,l,r,top,bottom,.121,.137,'shaded top glass' if ri==0 else 'pale reflected glass',f'window light {ri+1}-{ci+1}')
    for i,(l,r) in enumerate([(177.35,178.95),(192.05,194.0),(210.2,212.01),(228.1,229.7)]):
        box(b,l,r,131.3,173.3,.068,.126,'pale painted frame',f'painted upright {i+1}')
    for i,(a,c) in enumerate([(130.9,132.4),(142.2,145.2),(171.9,173.5)]):
        box(b,177.35,229.7,a,c,.065,.126,'pale painted frame',f'window rail {i+1}')
    if not lod:
        for i,(l,r) in enumerate([(178.95,192.05),(194,210.2),(212,228.1)]):
            for j,(top,bottom) in enumerate([(132.4,142.2),(145.2,171.9)]):
                box(b,l,r,top,top+.22,.101,.122,'glazing seal',f'glazing rebate {i+1}-{j+1}')
