"""Lower four-leaf street-facing bay and its single canted return at 41, lane 590 Weihai Road."""
from math import sin, cos, pi, hypot, atan2, tan

def color(rgb,roughness=.82,metallic=0):
    def linear(v):return v/3294.6 if v<=10 else ((v/255+.055)/1.055)**2.4
    return dict(color=[linear(v)for v in rgb],roughness=roughness,metallic=metallic)
PALETTE={
    'granite trim':color((113,111,105)),'edge of weathered band':color((129,126,117)),
    'projecting grey sill':color((98,96,94)),'upper belt shadow':color((85,85,83)),
    'pale wall':color((147,144,132)),'masonry score':color((120,116,108)),'incised frieze':color((105,105,99)),
    'glazing rebate':color((74,59,52)),'red timber':color((133,75,65)),
    'red sash edge':color((147,85,72)),'sky glass':color((133,165,184),.28,.12),
    'shadow glass':color((104,137,154),.31,.12),'awning upper':color((118,113,104)),
    'awning folded edge':color((132,127,119)),'window iron':color((65,66,60),.73,.18)}
for j,rgb in enumerate([(134,132,121),(138,136,125),(145,141,128),(141,140,128)]):
    PALETTE[f'facing block {j+1}']=color(rgb)
FACETS=[((-1.35,0),(1.10,0)),((1.10,0),(1.73,.73))]
def width(part):
    a,b=FACETS[part];return hypot(b[0]-a[0],b[1]-a[1])
def loc(part,s,d,z):
    a,b=FACETS[part];length=width(part);ux=(b[0]-a[0])/length;uy=(b[1]-a[1])/length
    return (a[0]+s*ux-d*uy,a[1]+s*uy+d*ux,z)
def slab(b,part,a,c,front,back,z0,z1,mat,label):
    vertices=[loc(part,x,d,z)for z in (z0,z1)for d in (front,back)for x in (a,c)]
    faces=[(0,2,3,1),(4,5,7,6),(0,1,5,4),(2,6,7,3),(0,4,6,2),(1,3,7,5)]
    b.add(vertices,faces,mat,label)
def horizontal_band(b,z0,z1,front,back,mat,label):
    # Carry the band around its measured return and join both outside mitres.
    a,c=FACETS[1];angle=atan2(c[1]-a[1],c[0]-a[0])
    inset=tan(angle/2)
    for part in range(2):
        vertices=[]
        for z in (z0,z1):
            for d in (front,back):
                first=0 if part==0 else d*inset
                last=width(0)-d*inset if part==0 else width(1)
                vertices.extend([loc(part,x,d,z)for x in (first,last)])
        b.add(vertices,[(0,2,3,1),(4,5,7,6),(0,1,5,4),(2,6,7,3),(0,4,6,2),(1,3,7,5)],mat,f'{label} face {part+1}')
def canopy(b,a,c,lod):
    stride=20 if lod else 44
    verts=[];faces=[]
    for k in range(stride+1):
        t=k/stride;x=a+(c-a)*t
        sag=.023*sin(pi*t)**2;flute=.012*cos(8*pi*t)
        lip=2.108-.034*(.5-.5*cos(22*pi*t))-.012*t
        verts.extend([(x,-.019,2.232),(x,-.312+flute,2.178-sag),(x,-.316+flute,lip),(x,-.296+flute,lip+.005),(x,-.293+flute,2.161-sag),(x,-.018,2.214)])
        if k:
            step=(k-1)*6
            for j in range(6):
                faces.append((step+j,step+j+6,step+(j+1)%6+6,step+(j+1)%6))
    faces.extend([tuple(range(5,-1,-1)),tuple(range(stride*6,stride*6+6))])
    b.add(verts,faces,'awning upper','photo-left bay awning and eleven scallops')
    for j,x in enumerate((a+.02,c-.026)):
        b.tube([(x,-.015,1.982),(x,-.29,2.142),(x,-.025,2.217)],.011,'window iron',5 if lod else 8,f'under-awning end arm {j+1}')
def add_building(b,lod=False):
    add_weathered_apron(b,lod)
    for part,(left,right,lights) in enumerate([(.32,2.12,4),(.15,.77,1)]):
        length=width(part)
        slab(b,part,0,length,0,.32,.04,.59,'pale wall',f'under-window spandrel {part+1}')
        slab(b,part,0,length,0,.32,2.24,2.70,'granite trim',f'frieze backing {part+1}')
        for k,(x0,x1) in enumerate([(0,left),(right,length)]):
            slab(b,part,x0,x1,0,.32,.59,2.24,'pale wall',f'stone jamb {part+1}-{k+1}')
            for j in range(5):
                zb=.60+j*.32
                slab(b,part,x0+.018,x1-.012,-.004,.002,zb,zb+.307,f'facing block {(2*j+k)%4+1}',f'jamb surface {part+1}-{k+1}-{j+1}')
        for k,(x0,x1) in enumerate([(left,left+.05),(right-.05,right)]):
            slab(b,part,x0,x1,.16,.245,.61,2.24,'glazing rebate',f'recessed perimeter {part+1}-{k+1}')
        bay=right-left;unit=(bay-.072)/lights
        for i in range(lights):
            x0=left+.036+i*unit;x1=x0+unit
            for k,(start,end) in enumerate([(x0,x0+.032),(x1-.032,x1)]):
                slab(b,part,start,end,.151,.22,.67,2.215,'red timber',f'window {part+1}-{i+1} upright {k+1}')
            for label,z0,z1 in [('sill',.67,.728),('cross rail',1.102,1.174),('head',2.152,2.215)]:
                slab(b,part,x0+.032,x1-.032,.153,.22,z0,z1,'red timber',f'window {part+1}-{i+1} {label}')
            for k,(z0,z1) in enumerate([(.728,1.102),(1.174,2.152)]):
                slab(b,part,x0+.032,x1-.032,.204,.218,z0,z1,'shadow glass' if part or (i+k)%5==0 else 'sky glass',f'glass {part+1}-{i+1} light {k+1}')
                for label,side in [('left',x0+.033),('right',x1-.042)]:
                    slab(b,part,side,side+.009,.176,.206,z0,z1,'red sash edge',f'glazing fillet {part+1}-{i+1}-{k+1} {label}')
        for i in range(round(length/.16)):
            x=(i+.5)*.16
            slab(b,part,x-.012,x+.012,-.009,.002,2.288,2.435,'incised frieze',f'frieze rib {part+1}-{i+1}')
    for z0,z1,d,mat,label in [(.025,.092,-.048,'granite trim','lower cut belt'),(.55,.59,-.036,'granite trim','sill bracket course'),(.59,.661,-.108,'projecting grey sill','canted sill lip'),(2.210,2.25,-.018,'granite trim','stone eyebrow'),(2.25,2.282,-.047,'edge of weathered band','frieze lower bead'),(2.447,2.5,-.083,'upper belt shadow','dark course'),(2.50,2.595,-.127,'granite trim','broad crowning band'),(2.595,2.634,-.14,'edge of weathered band','hood flashing')]:
        horizontal_band(b,z0,z1,d,.2,mat,label)
    canopy(b,-1.35+.22,-1.35+2.18,lod)

def cut_apron(b,part,lo,hi,zb,zt,label):
    # Raised frame around a recessed pebbled cement rectangle, visible below the sill.
    thickness=.027
    for name,a,c,z0,z1 in [('bottom',lo,hi,zb,zb+thickness),('top',lo,hi,zt-thickness,zt),('left',lo,lo+thickness,zb+thickness,zt-thickness),('right',hi-thickness,hi,zb+thickness,zt-thickness)]:
        slab(b,part,a,c,-.044,-.001,z0,z1,'granite trim',label+' '+name)
    slab(b,part,lo+thickness,hi-thickness,-.009,.002,zb+thickness,zt-thickness,'masonry score',label+' hammered interior')

def grit(b,part,lo,hi,zb,zt,density,depth,seed,label):
    from random import Random
    rng=Random(seed)
    groups=[([],[])for _ in range(4)]
    for i in range(density):
        u=rng.uniform(lo,hi);z=rng.uniform(zb,zt)
        rx=min(rng.uniform(.002,.010),hi-u,u-lo);rz=min(rx*rng.uniform(.43,1.42),zt-z,z-zb)
        if rx<.0002 or rz<.0002:continue
        index=rng.randrange(4);verts,faces=groups[index];k=len(verts)
        verts.extend([loc(part,u-rx,depth,z),loc(part,u+rx*.12,depth-.0015,z+rz),loc(part,u+rx,depth,z-.001),loc(part,u-rx*.18,depth,z-rz)])
        faces.extend([(k,k+1,k+2),(k,k+2,k+3)])
    for k,(verts,faces) in enumerate(groups):
        if faces:b.add(verts,faces,['aggregate grey','aggregate buff','aggregate silver','aggregate charcoal'][k],label+f' aggregate {k+1}')
PALETTE.update({name:color(rgb) for name,rgb in [('aggregate grey',(125,123,117)),('aggregate buff',(144,140,125)),('aggregate silver',(155,152,142)),('aggregate charcoal',(96,97,94)),('aged handle',(121,105,86))]})

def add_weathered_apron(b,lod):
    for part,pairs in [(0,[(.345,1.195),(1.256,2.102)]),(1,[(.169,.752)])]:
        for j,(a,c) in enumerate(pairs):
            label=f'apron inset {part+1}-{j+1}'
            cut_apron(b,part,a,c,.100,.491,label)
            grit(b,part,a+.038,c-.037,.142,.449,85 if lod else 220,-.0105,519+13*part+j,label)
        end=width(part)
        for j,(a,c) in enumerate([(0,.160),(.80,end)] if part else [(0,.30),(2.13,end)]):
            grit(b,part,a+.018,c-.010,.69,2.21,130 if lod else 520,-.006,1802+15*part+j,f'jamb {part+1}-{j+1}')
        grit(b,part,.05,end-.05,2.292,2.432,84 if lod else 250,-.002,109+part,f'frieze {part+1}')
    for j,x in enumerate([.73,.78]):
        b.tube([loc(0,x,.145,1.20),loc(0,x+.003,.130,1.175),loc(0,x-.009,.132,1.145),loc(0,x-.013,.143,1.140)],.0055,'aged handle',5 if lod else 9,f'paired timber sash catch {j+1}')
