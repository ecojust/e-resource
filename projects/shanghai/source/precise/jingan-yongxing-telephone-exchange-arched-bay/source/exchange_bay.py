"""Arched stone panel and three narrow upper windows on the Yongxing Road telephone exchange."""
import math


def material(rgb,rough=.88,metal=0):
    return dict(color=[c/3294.6 if c<=10 else ((c/255+.055)/1.055)**2.4 for c in rgb],roughness=rough,metallic=metal)


PALETTE={'dress stone':material((176,164,131)),'recess wall':material((180,164,131)),
         'arch intrados':material((137,127,102)),'shadow course':material((129,117,92)),
         'stone sill':material((156,147,120)),'upper facade':material((170,162,133)),
         'casement steel':material((66,67,61),.70,.19),'glass':material((72,79,77),.30,.09)}


def bow(x):
    return .058*x*x


def slab(b,outline,front,back,mat,name):
    """Sweep a convex face across the cylindrical facade, following its bow in plan."""
    vertices=[(x,bow(x)+dy,z) for dy in (front,back) for x,z in outline];n=len(outline)
    faces=[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]
    faces.extend((i,(i+1)%n,(i+1)%n+n,i+n)for i in range(n))
    b.add(vertices,faces,mat,name)


def rect(b,l,r,low,high,front,back,mat,name):
    count=max(1,math.ceil((r-l)/.36))
    for i in range(count):
        x0=l+(r-l)*i/count;x1=l+(r-l)*(i+1)/count
        slab(b,[(x0,low),(x1,low),(x1,high),(x0,high)],front,back,mat,name)


def band(b,r0,r1,front,back,mat,steps,name):
    for i in range(steps):
        a,beta=math.pi*i/steps,math.pi*(i+1)/steps
        shape=[(r*math.cos(t),1.87+r*math.sin(t))for r,t in [(r0,a),(r1,a),(r1,beta),(r0,beta)]]
        slab(b,shape,front,back,mat,name)


def casement(b,l,r,base,top,bars,name,steel,behind):
    mid=(l+r)*.5
    rect(b,l,r,base,top,behind,behind+.026,'glass',name+' glass')
    for x in (l+.018,r-.018):
        rect(b,x-.018,x+.018,base,top,steel,steel+.035,'casement steel',name+' steel jamb')
    for z in (base+.02,top-.02,*bars):
        rect(b,l,r,z-.020,z+.020,steel,steel+.041,'casement steel',name+' horizontal rail')
    if name=='lower set-in window':
        rect(b,mid-.018,mid+.018,base+.04,top-.03,steel-.01,steel+.028,'casement steel',name+' centre mullion')


def add_building(b,lod=False):
    steps=22 if lod else 64
    # A street-level close-up shows joints in the field, continuing radially over the single lower casement.
    divisions=[.08,.377,.655,.935,1.210,1.493,1.751,1.87]
    for left,right in ((-1.38,-.385),(.385,1.38)):
        for j,(bottom,top) in enumerate(zip(divisions,divisions[1:])):
            rect(b,left,right,bottom,top,.032,.42,'shadow course','set-back bed under joint')
            rect(b,left,right,bottom+.006,top-.006,.009,.418,'recess wall','ashlar bed '+str((left,j)))
    for i in range(13):
        a=i*math.pi/13+.004;c=(i+1)*math.pi/13-.004
        # Voussoir beds converge onto the lintel above the opening.
        shape=[(0,1.87)]+[(1.38*math.cos(a+(c-a)*j/5),1.87+1.38*math.sin(a+(c-a)*j/5))for j in range(6)]
        slab(b,shape,.013,.35,'recess wall','radiating head stone '+str(i))
    band(b,.001,1.38,.042,.28,'shadow course',steps,'shadow in radial joints')
    for rad0,rad1,front,mat in [
        (1.38,1.424,-.032,'arch intrados'),(1.424,1.451,-.087,'dress stone'),
        (1.451,1.505,-.063,'shadow course'),(1.505,1.569,-.116,'dress stone'),
        (1.569,1.790,-.191,'dress stone')]:
        band(b,rad0,rad1,front,.39,mat,steps,'arched archivolt '+str(rad0))
        for side in (-1,1):
            l,r=sorted((side*rad0,side*rad1))
            rect(b,l,r,0,1.875,front,.39,mat,'straight jamb beneath archivolt '+str((side,rad0)))
    for i in range(18 if lod else 48):
        n=18 if lod else 48
        l=-1.789+3.578*i/n;r=-1.789+3.578*(i+1)/n
        edge=lambda x:1.87+math.sqrt(max(0,1.79**2-x*x))
        slab(b,[(l,edge(l)),(r,edge(r)),(r,3.820),(l,3.820)],-.108,.36,'upper facade','spandrel over the arch')
    rect(b,-1.81,1.81,-.087,.080,-.185,.40,'stone sill','sill below segmental panel')
    rect(b,-1.82,1.82,3.803,3.911,-.247,.39,'stone sill','ledge between storeys')
    casement(b,-.383,.383,.081,1.869,[.43,.865,1.322,1.50],'lower set-in window',.15,.195)
    slots=[(-1.223,-.755),(-.235,.237),(.745,1.215)]
    spans=[(-1.79,slots[0][0]),(slots[0][1],slots[1][0]),(slots[1][1],slots[2][0]),(slots[2][1],1.79)]
    for i,(l,r) in enumerate(spans):
        rect(b,l,r,3.91,5.37,-.098,.37,'upper facade','upper window pier '+str(i))
    rect(b,-1.79,1.79,5.37,5.65,-.098,.37,'upper facade','unbroken parapet above three openings')
    for j,(l,r) in enumerate(slots):
        casement(b,l,r,3.923,5.37,[4.20,4.53,4.80,5.12],'upper narrow window '+str(j),.13,.181)
        rect(b,l,r,3.91,3.94,-.143,.16,'stone sill','silhouette of upper opening '+str(j))
