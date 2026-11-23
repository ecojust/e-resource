"""Four folded red brick window bays at 42 Wanping Road, in the 22 m study frame."""
from math import cos, hypot, pi, sin
from street_materials import RED, SOLDIER, STEEL, GLASS, CREAM, SHADE

# From left to right on the 2019 street photograph. Rear and front corners
# belong to different vertical planes. Depth is constrained by the visible slab returns.
BAYS = (
    (-9.29, -8.40, -6.81, -5.96, .57),
    (-5.20, -4.49, -3.02, -2.23, .60),
    ( 1.59,  2.50,  3.91,  4.94, .62),
    ( 6.87,  7.81,  9.31, 10.17, .65),
)
BASE, TOP = 6.15, 13.38
# Individual storey opening and relief limits, common to the three folded faces.
ROWS = ((7.31, 9.28), (10.69, 12.55))
RELIEF = (6.48, 7.16)


def bay_openings():
    """Rear-plane outlines, ordered x-min, z-min, x-max, z-max."""
    return [(a + .04, BASE + .025, d - .04, TOP - .025) for a, _, _, d, _ in BAYS]


def _face(b, a, c, left, right, low, high, outside, thickness, material, label):
    dx, dy = c[0] - a[0], c[1] - a[1]
    length = hypot(dx, dy)
    tangent = (dx / length, dy / length)
    normal = (tangent[1], -tangent[0])
    def at(s, z, t):
        return (a[0] + tangent[0]*s + normal[0]*t, a[1] + tangent[1]*s + normal[1]*t, z)
    vertices = [at(s,z,t) for t in (outside,outside-thickness)
                for s,z in ((left,low),(right,low),(right,high),(left,high))]
    faces = [(0,1,2),(0,2,3),(6,5,4),(7,6,4)]
    for i in range(4):
        j=(i+1)%4
        faces.extend(((i+4,j+4,j),(i+4,j,i)))
    b.add(vertices, faces, material, label)


def _slab(b, corners, z0, z1, material, label):
    # Perimeter follows the exposed three facets and the back wall.
    a,fl,fr,d=corners
    points=[a,fl,fr,d]
    vertices=[(x,y,z) for z in (z0,z1) for x,y in points]
    faces=[(0,2,1),(0,3,2),(4,5,6),(4,6,7)]
    for i in range(4):
        j=(i+1)%4
        faces.extend(((i,j,j+4),(i,j+4,i+4)))
    b.add(vertices, faces, material, label)


def _cord(b, a, c, dots, radius, label, lod):
    dx,dy=c[0]-a[0],c[1]-a[1]
    length=hypot(dx,dy);tx,ty=dx/length,dy/length
    nx,ny=ty,-tx
    verts=[];faces=[];sides=5 if lod else 8
    for i,(s,z) in enumerate(dots):
        first=dots[max(i-1,0)];last=dots[min(i+1,len(dots)-1)]
        ds,dz=last[0]-first[0],last[1]-first[1];k=hypot(ds,dz)
        for n in range(sides):
            phase=n*2*pi/sides
            side=cos(phase)*radius;out=.012+sin(phase)*radius
            u=s-side*dz/k
            verts.append((a[0]+u*tx+nx*out,a[1]+u*ty+ny*out,z+side*ds/k))
    for i in range(len(dots)-1):
        for n in range(sides):
            j=(n+1)%sides;p=i*sides;q=p+sides
            faces.extend(((p+n,p+j,q+j),(p+n,q+j,q+n)))
    last=(len(dots)-1)*sides
    for i in range(1,sides-1):
        faces.extend(((0,i+1,i),(last,last+i,last+i+1)))
    # Guarantee outward winding on all three differently oriented planes.
    import numpy as np
    v=np.asarray(verts);f=np.asarray(faces)
    if (v[f[:,0]]*np.cross(v[f[:,1]],v[f[:,2]])).sum()<0:faces=[(u,k,j) for u,j,k in faces]
    b.add(verts,faces,CREAM,label)


def _relief(b,a,c,left,right,prefix,lod):
    low,high=RELIEF
    _face(b,a,c,left,right,low,high,.006,.035,CREAM,prefix+' | rectangular plaster panel')
    width,height=right-left,high-low
    def cord(points,r,name):
        dots=[(left+x*width,low+y*height) for x,y in points]
        _cord(b,a,c,dots,r,prefix+' | '+name,lod)
    # One coiling head and oblique pendent leaf per unit. The longer front panel
    # repeats this unit twice. The angled flank has one. See the marked photograph.
    spiral=[]
    count=17 if lod else 33
    for i in range(count):
        q=i/(count-1);angle=(.11+1.13*q)*2*pi
        r=.035+.205*q
        spiral.append((.59+r*cos(angle),.72+r*sin(angle)))
    cord(spiral,.014,'rolled head')
    cord([(.87,.98),(.818,.84),(.747,.68),(.634,.48),(.48,.28),(.31,.12),(.19,.075)],.016,'descending oblique stem')
    # Nested sickle-shaped pinnae. The alternating high and low tips are visible
    # even on the narrow return next to the brick pier.
    for i in range(3 if lod else 4):
        t=i*.122
        cord([(.085,.48-t),(.115,.40-t),(.173,.37-t),(.25,.395-t),
              (.328,.455-t),(.414,.57-t),(.49,.70-t)],.012 if lod else .015,'left curled leaflet '+str(i+1))
        cord([(.89,.60-t),(.865,.515-t),(.80,.505-t),(.742,.525-t),
              (.68,.584-t)],.012,'right curled leaflet '+str(i+1))


def _bay(b,index,profile,lod):
    left,fl,fr,right,depth=profile
    corners=((left,.015),(fl,-depth),(fr,-depth),(right,.015))
    prefix='Wanping Road | red projecting bay '+str(index)
    _slab(b,corners,BASE,BASE+.055,SHADE,prefix+' | visible soffit')
    _slab(b,corners,TOP-.07,TOP,RED,prefix+' | weathering cap')
    for n,(a,c) in enumerate(zip(corners,corners[1:])):
        width=hypot(c[0]-a[0],c[1]-a[1]);face=prefix+' | '+('left flank','front','right flank')[n]
        central=n==1;hh=.105 if central else .095
        for low,high,material,label in ((BASE+.05,RELIEF[0],SOLDIER,'edge soldier course'),
            (RELIEF[0],RELIEF[1],RED,'panel backing'),(RELIEF[1],ROWS[0][0],SOLDIER,'sill soldier course'),
            (ROWS[0][1],ROWS[1][0],SOLDIER,'vertical-brick spandrel'),(ROWS[1][1],TOP-.06,RED,'upper brick head')):
            _face(b,a,c,0,width,low,high,0,.16,material,face+' | '+label)
        for row,(low,high) in enumerate(ROWS,3):
            lab=face+' | storey '+str(row)
            for L,R in ((0,hh),(width-hh,width)):
                _face(b,a,c,L,R,low,high,0,.16,RED,lab+' | rounded-edge brick jamb')
            L,R=hh,width-hh;bar=.031
            _face(b,a,c,L,R,low,high,-.083,.016,GLASS,lab+' | glass')
            for U,V in ((L,L+bar),(R-bar,R)):
                _face(b,a,c,U,V,low,high,-.039,.052,STEEL,lab+' | jamb')
            for z in (low+.014,high-.014,low+(high-low)*.27,low+(high-low)*.52,low+(high-low)*.79):
                _face(b,a,c,L,R,z-bar/2,z+bar/2,-.033,.052,STEEL,lab+' | rail')
            if central:
                u=(L+R)/2;_face(b,a,c,u-bar/2,u+bar/2,low,high,-.031,.055,STEEL,lab+' | central mullion')
        lo,hi=hh+.014,width-hh-.014
        if central:
            mid=(lo+hi)/2
            _relief(b,a,c,lo,mid-.009,face+' | plaster 1',lod)
            _relief(b,a,c,mid+.009,hi,face+' | plaster 2',lod)
        else:_relief(b,a,c,lo,hi,face+' | plaster',lod)


def add_bays(builder,lod=False):
    for i,profile in enumerate(BAYS,1):
        _bay(builder,i,profile,lod)
