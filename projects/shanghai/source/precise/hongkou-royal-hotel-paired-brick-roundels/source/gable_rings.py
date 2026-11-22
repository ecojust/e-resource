"""Raised brick annuli and cross keys of the photographed paired gable lights."""
from math import atan2, cos, pi, sin, sqrt


def surface(rgb):
    return {'color': [((v / 255 + .055) / 1.055) ** 2.4 for v in rgb], 'roughness': .88}


PALETTE = {k: surface(rgb) for k, rgb in {
    'warm joint': (151, 127, 111), 'grey brick': (143, 136, 129), 'cool brick': (128, 129, 127),
    'muted brick': (144, 131, 119), 'red brick': (164, 99, 72), 'burnt brick': (147, 85, 64),
    'sunlit brick': (181, 116, 86), 'header': (154, 94, 73), 'stone coping': (175, 166, 151),
}.items()}
CENTRES = (-.88, .88)
ZC = 1.34
HALF = 1.84
INSIDE = .397
OUTSIDE = .680


def top(x):
    return 2.92 - .43*abs(x)


def solid(builder, poly, front, rear, mat, name):
    points = [(x,d,z) for d in (front,rear) for x,z in poly]; n=len(poly)
    faces = [tuple(range(n)), tuple(range(2*n-1,n-1,-1))]
    faces.extend((i,i+n,(i+1)%n+n,(i+1)%n) for i in range(n))
    builder.add(points,faces,mat,name)


def box(b,l,r,bottom,cap,front,back,mat,label):
    solid(b,[(l,bottom),(r,bottom),(r,cap),(l,cap)],front,back,mat,label)


def polar(c,t,r):
    return c+r*cos(t), ZC+r*sin(t)


def radial_piece(b,c,t0,t1,r0,r1,y0,y1,material,name,divisions):
    for k in range(divisions):
        a=t0+(t1-t0)*k/divisions; h=t0+(t1-t0)*(k+1)/divisions
        solid(b,[polar(c,a,r0),polar(c,a,r1),polar(c,h,r1),polar(c,h,r0)],y0,y1,material,name)


def wall_and_face(b,lod,c):
    left,right = (-HALF,0) if c<0 else (0,HALF)
    corners=[(left,.31),(right,.31),(right,top(right)),(left,top(left))]
    angles={i*2*pi/(48 if lod else 96) for i in range(48 if lod else 96)}
    for x,z in corners: angles.add(atan2(z-ZC,x-c)%(2*pi))
    angles=sorted(angles|{2*pi}); shape=[]
    for a in angles:
        dx,dz=cos(a),sin(a); candidates=[]
        if dx>1e-9:candidates.append((right-c)/dx)
        if dx < -1e-9:candidates.append((left-c)/dx)
        if dz < -1e-9:candidates.append((.31-ZC)/dz)
        slope=.43 if c<0 else -.43
        if dz-slope*dx>1e-9:candidates.append((top(c)-ZC)/(dz-slope*dx))
        d=min(t for t in candidates if t>0)
        shape.append((c+dx*d,ZC+dz*d))
    for j,(a,h) in enumerate(zip(angles,angles[1:])):
        solid(b,[polar(c,a,OUTSIDE),shape[j],shape[j+1],polar(c,h,OUTSIDE)],0,.31,'warm joint','perforated spandrel wall')
    # Each bed follows its true circle intersection. Split a brick at the top and bottom of the eye.
    bed=.077; length=.226 if not lod else .298
    for j in range(35):
        z0=.31+bed*j+.003; z1=z0+bed-.008
        for k in range(-10,11):
            x0=max(left+.002,k*length+(j%2)*length/2+.004); x1=min(right-.002,k*length+(j%2)*length/2+length-.004)
            if x1<=x0:continue
            mat=('grey brick','muted brick','cool brick','grey brick')[(j*7+k*3)%4]
            if z0>2.01:mat=('red brick','header','red brick','burnt brick')[(j+k)%4]
            segments=5 if not lod else 3
            xs=[x0+i*(x1-x0)/segments for i in range(segments+1)]
            for boundary in [c-OUTSIDE,c+OUTSIDE]:
                if x0<boundary<x1:xs.append(boundary)
            for l,r in zip(sorted(xs),sorted(xs)[1:]):
                def band(x,upper):
                    gap=sqrt(max(0,OUTSIDE**2-(x-c)**2)); cut=ZC+(gap if upper else -gap)
                    return (max(z0,cut),min(z1,top(x))) if upper else (z0,min(z1,cut,top(x)))
                for upper in (False,True):
                    lo,hi=band(l,upper); ro,rhi=band(r,upper)
                    if hi<=lo and rhi<=ro:continue
                    ll,rr=l,r
                    if hi<=lo:
                        f=(lo-hi)/((lo-hi)+(rhi-ro));ll=l+f*(r-l);hi=lo=lo+f*(ro-lo)
                    if rhi<=ro:
                        f=(hi-lo)/((hi-lo)+(ro-rhi));rr=l+f*(r-l);rhi=ro=lo+f*(ro-lo)
                    pts=[(ll,lo),(rr,ro)]+([(rr,rhi)] if rhi>ro+1e-7 else [])+([(ll,hi)] if hi>lo+1e-7 else [])
                    if len(pts)>=3 and rr>ll+1e-7:solid(b,pts,-.004,.003,mat,'brickwork in sloping panel')


def opening(b,i,c,lod):
    prefix='left' if i==0 else 'right'; n=32
    for k in range(n):
        a=2*pi*k/n;h=2*pi*(k+1)/n
        radial_piece(b,c,a,h,INSIDE,OUTSIDE,-.009,.30,'warm joint',prefix+' annular joint bed',2 if lod else 5)
        mat=('red brick','sunlit brick','burnt brick','red brick','header')[k%5]
        radial_piece(b,c,a+.004,h-.004,INSIDE+.003,OUTSIDE-.003,-.038,.29,mat,prefix+' radial brick ring',2 if lod else 5)
    for k in range(4):
        a=pi*k/2;dx,dz=cos(a),sin(a)
        def p(r,t):return(c+r*dx-t*dz,ZC+r*dz+t*dx)
        solid(b,[p(INSIDE+.006,-.058),p(OUTSIDE+.037,-.079),p(OUTSIDE+.037,.079),p(INSIDE+.006,.058)],-.082,-.012,'header',prefix+' four projecting cross keys')


def add_building(b,lod=False):
    for i,c in enumerate(CENTRES):
        wall_and_face(b,lod,c);opening(b,i,c,lod)
    for z0,z1,front,mat in ((0,.087,-.052,'red brick'),(.087,.149,-.078,'header'),(.149,.202,-.108,'red brick'),(.202,.262,-.072,'burnt brick'),(.262,.313,-.038,'red brick')):
        box(b,-HALF-.056,HALF+.056,z0,z1,front,.329,mat,'lower projecting brick cornice')
    for c in (-HALF,0,HALF):
        w=.095 if c==0 else .079
        z=.31;j=0
        while z<top(c):
            cap=min(z+.077,top(c))
            box(b,c-w,c+w,z,cap,-.057,.328,'warm joint','bonded pilaster core')
            if cap-z>.006:box(b,c-w-.006,c+w+.006,z+.003,cap-.003,-.065,-.051,('red brick','header','burnt brick')[j%3],'bonded gable piers')
            z=cap;j+=1
        for offset,width,front in ((-.13,w+.014,-.082),(-.082,w+.036,-.100)):
            box(b,c-width,c+width,top(c)+offset,top(c)+offset+.043,front,.348,'header','pier capital courses')
    for lo,hi in ((-HALF-.081,0),(0,HALF+.081)):
        for dz,h,y,mat,label in ((.00,.055,-.058,'burnt brick','raking moulded course'),(.055,.037,-.081,'stone coping','pale raking coping')):
            solid(b,[(lo,top(lo)+dz),(hi,top(hi)+dz),(hi,top(hi)+dz+h),(lo,top(lo)+dz+h)],y,.362,mat,label)
