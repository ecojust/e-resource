"""The photographed gable, inset double attic sash and the curved shutter bay below it."""
import math
import random

def pigment(rgb):
    return {'color':[v/3294.6 if v<=10 else ((v/255+.055)/1.055)**2.4 for v in rgb],'roughness':.83}
PALETTE={k:pigment(c) for k,c in {'aggregate':(125,123,110),'light stone grains':(151,147,130),'dark stone grains':(110,108,97),'brown oak':(88,78,66),'edge moulding':(123,113,99),'window frame':(157,157,137),'attic glass':(117,177,172),'shutter blade':(204,190,155),'cream surround':(194,180,148),'shutter recess':(88,81,64),'granite band':(113,111,101)}.items()}

def plane(point):
    u,v=point
    x=(u-319.)*.00635
    return (x,1.83+(353.-.175*(u-319.)-v)*.00625)

def face(builder,points,y0,y1,material,name):
    points=[plane(q) for q in points]
    area=sum(x*z1-x1*z for (x,z),(x1,z1) in zip(points,points[1:]+points[:1]))
    if area<0:points.reverse()
    n=len(points)
    vertices=[(x,y,z) for y in (y0,y1)for x,z in points]
    faces=[tuple(range(n)),tuple(reversed(range(n,2*n)))]
    faces.extend(((j+1)%n,j,n+j,n+(j+1)%n)for j in range(n))
    builder.add(vertices,faces,material,name)

def panel(b,a0,a1,z0,z1,d0,d1,m,name):
    """A flat shutter, reveal or strip between two points on the measured bow."""
    r=1.82
    lo=(r*math.sin(a0),.96-r*math.cos(a0));hi=(r*math.sin(a1),.96-r*math.cos(a1))
    theta=(a0+a1)/2;out=(math.sin(theta),-math.cos(theta))
    v=[(p[0]+out[0]*d,p[1]+out[1]*d,z)for z in(z0,z1)for d in(d0,d1)for p in(lo,hi)]
    b.add(v,[(0,2,3,1),(4,5,7,6),(0,1,5,4),(2,6,7,3),(0,4,6,2),(1,3,7,5)],m,name)

def add_building(b,lod):
    trim=lambda pts,near,far,mat,name:face(b,pts,near,far,mat,name)
    # The frame is split at the real sill. The glass sits in the opening.
    g=[(25,402),(321,24),(663,290)]
    lt,rt,rb,lb=[(294,143),(378,128),(379,227),(293,240)]
    for name,pts in [('left', [g[0],g[1],lt,lb]),('right',[g[1],g[2],rb,rt]),('head',[g[1],rt,lt]),('foot',[g[0],lb,rb,g[2]])]:
        trim(pts,.05,.30,'aggregate','gable infill '+name)
    trim([lt,rt,rb,lb],.16,.19,'shutter recess','continuous backstop behind attic glass')
    # Fine, unequal granules catch the raking light on the exposed plaster panels.
    rng=random.Random(54102)
    for material in ('light stone grains','dark stone grains'):
        vertices=[];faces=[]
        for _ in range(450 if not lod else 120):
            u=rng.uniform(27,653);v=rng.uniform(44,399)
            side=403+(24-403)*(u-25)/(321-25) if u<=321 else 24+(290-24)*(u-321)/(663-321)
            if v<side+6 or v>402+(u-25)*(290-402)/(663-25)-3 or (288<u<386 and 121<v<246):continue
            x,z=plane((u,v));r=rng.uniform(.006,.012);i=len(vertices)
            vertices.extend([(x-r,.049,z-r*.22),(x+.26*r,.049,z-r),(x+r,.049,z-.05*r),(x+.2*r,.049,z+.75*r),(x-.15*r,.049-r*.61,z)])
            faces.extend([(i+j,i+(j+1)%4,i+4) for j in range(4)])
        b.add(vertices,faces,material,'roughcast gable '+material)
    for k,(u0,u1) in enumerate([(298,334),(341,374)]):
        for j in range(3):
            v=141-(u0-298)*.16+31*j
            trim([(u0,v),(u1,v-5),(u1,v+25),(u0,v+30)],.105,.15,'attic glass',f'attic sash {k+1} pane {j+1}')
        for j in range(4):
            v=139-(u0-298)*.16+31*j
            trim([(u0-2,v),(u1+2,v-6),(u1+2,v-2),(u0-2,v+4)],.002,.11,'window frame',f'attic sash {k+1} rail {j+1}')
    for i,(u,v,z) in enumerate([(294,140,240),(335,134,234),(375,127,229)]):
        trim([(u,v),(u+6,v-1),(u+6,z-1),(u,z)],-.018,.112,'window frame',f'attic stile {i+1}')
    for i,(u,top,bottom) in enumerate([(117,328,387),(170,258,379),(219,201,371),(269,159,359),(324,242,350),(380,230,341),(441,154,330),(502,192,320),(560,218,307),(608,254,298)]):
        trim([(u,top),(u+12,top+(-14 if u<325 else 8)),(u+12,bottom-3),(u,bottom)],-.033,.056,'brown oak',f'gable timber upright {i+1}')
    for i,pts in enumerate([[(21,401),(661,281),(669,301),(26,418)],[(171,268),(489,210),(508,219),(166,281)]]):
        trim(pts,-.047,.07,'brown oak',f'gable timber cross beam {i+1}')
    for i,(a,c) in enumerate([((18,403),(319,20)),((319,20),(672,287))]):
        u,v=a;h,k=c
        trim([(u,v),(h,k),(h,k+18),(u,v+18)],-.23,.22,'brown oak',f'sloping eave {i+1}')
        trim([(u,v-4),(h,k-4),(h,k+2),(u,v+2)],-.245,-.20,'edge moulding',f'outer verge {i+1}')
    edges=[math.radians(i) for i in (-54,-26,1,28,55)]
    for i,(a,c) in enumerate(zip(edges,edges[1:])):
        span=c-a; tag=f'curved bay {i+1}'
        for j in range(5 if not lod else 2):
            n=5 if not lod else 2;tl=a+span*j/n;tr=a+span*(j+1)/n
            front=[(1.82*math.sin(t),.96-1.82*math.cos(t)) for t in(tl,tr)]
            pts=[(x,y,z) for z in (1.781,1.842) for x,y in [front[0],front[1],(front[1][0],.125),(front[0][0],.125)]]
            b.add(pts,[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],'granite band',tag+' spandrel return to gable')
        for j in range(6 if not lod else 3):
            num=6 if not lod else 3; left=a+j*span/num;right=left+span/num
            for lo,hi,d,m,name in [(0,.12,.065,'cream surround','sill'),(.12,.22,-.025,'granite band','low band'),(1.28,1.52,.018,'cream surround','head'),(1.52,1.56,.068,'cream surround','lip'),(1.56,1.80,-.025,'granite band','spandrel')]:
                panel(b,left,right,lo,hi,-.16,d,m,tag+' '+name)
        panel(b,a,c,.13,1.3,-.085,-.067,'shutter recess',tag+' recess')
        for j,(l,r) in enumerate([(a,a+.12*span),(c-.12*span,c)]):
            panel(b,l,r,.12,1.3,-.09,.026,'cream surround',tag+f' cheek {j+1}')
        for j in range(2):
            l=a+(.15+.36*j)*span;r=l+.335*span
            for k,(u,v) in enumerate([(l,l+.028*span),(r-.028*span,r)]):
                panel(b,u,v,.20,1.22,-.058,-.025,'shutter blade',tag+f' leaf {j+1} stile {k+1}')
            count=20 if not lod else 11
            for k in range(count):
                z=.24+k*.94/count;lo=l+.028*span;hi=r-.028*span
                panel(b,lo,hi,z,z+.74*.94/count,-.066,-.039,'shutter blade',tag+f' leaf {j+1} louvre {k+1}')
            for k,z in enumerate((.18,1.19)):
                panel(b,l,r,z,z+.052,-.06,-.027,'shutter blade',tag+f' leaf {j+1} rail {k+1}')
