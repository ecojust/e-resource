"""Editable acanthus scroll panel beneath the brick screen on the 9/11 gable.

x0/x1 and z0/z1 are the outer panel rectangle; face_y is the adjacent wall
surface. The photo projectivity determines position and outline. Projection
normal to the wall is approximate and can be adjusted with depth_scale.
"""
from math import ceil, cos, hypot, pi, sin
import numpy as np
from scipy.interpolate import CubicHermiteSpline, PchipInterpolator
from acanthus_contours import BASES, BOSSES, LEAVES, SCROLLS, metric_point

MATERIALS = ['Wujin | red relief ground','Wujin | carved brick','Wujin | raised leaf face']
def srgb(t):
    t=t/255
    return t/12.92 if t<=.04045 else ((t+.055)/1.055)**2.4
PALETTE={key:{'color':[srgb(c) for c in rgb],'roughness':rug,'metallic':0}
         for key,rgb,rug in zip(MATERIALS,[(136,72,51),(170,86,61),(174,90,64)],[.91,.86,.88])}

def add_closed(b,points,faces,mat,name):
    vertices=np.asarray(points,dtype=float);iv=np.asarray(faces,dtype=int)
    loc=vertices-vertices.mean(axis=0)
    triangles=loc[iv]
    volume=np.einsum('ij,ij->i',triangles[:,0],np.cross(triangles[:,1],triangles[:,2])).sum()/6
    if abs(volume)<1e-13:raise ValueError('Zero volume relief part '+name)
    if volume<0:iv=iv[:,[0,2,1]]
    b.add(vertices.tolist(),iv.tolist(),mat,name)

def connect_rings(rings):
    n=len(rings[0]);faces=[]
    for j in range(len(rings)-1):
        for k in range(n):
            a=j*n+k;d=j*n+(k+1)%n
            faces.extend([(a,d,a+n),(d,d+n,a+n)])
    return faces

def stroke(b,points,far,project,name,is_scroll,lower=False):
    controls=np.asarray(points,dtype=float);xy=controls[:,:2]
    distance=np.r_[0,np.cumsum(np.linalg.norm(np.diff(xy,axis=0),axis=1))]
    tangent=np.gradient(xy,distance,axis=0)
    spline=CubicHermiteSpline(distance,xy,tangent)
    width=PchipInterpolator(distance,controls[:,2])
    # Retain all measured knots even where a long smooth segment can be coarsened.
    step=10.5 if far else 4.7
    ts=np.concatenate([np.linspace(a,c,max(2,ceil((c-a)/step)+1))[:-1]
                       for a,c in zip(distance[:-1],distance[1:])]+[distance[-1:]])
    rxy=spline(ts);dxy=spline.derivative()(ts);widths=width(ts)
    if not is_scroll:widths*=1.10 if lower else 1.15
    if is_scroll:
        # The cut tapers at a tight turn around a boss. At the inside edge a
        # constant profile wider than the turning radius would fold over itself.
        speed=np.linalg.norm(dxy,axis=1)
        normals=np.column_stack([-dxy[:,1],dxy[:,0]])/speed[:,None]
        delta=rxy[None,:,:]-rxy[:,None,:]
        square=(delta**2).sum(axis=2)
        normal_separation=np.abs(np.einsum('ijk,ik->ij',delta,normals))
        reach=np.divide(square,2*normal_separation,out=np.full_like(square,np.inf),
                        where=normal_separation>1e-8).min(axis=1)
        widths=np.minimum(widths,.83*reach)
    if is_scroll:
        profile=[(-1,.0),(-.90,.38),(-.66,.80),(-.32,.98),(.10,1),(.50,.94),(.86,.68),(1,.20)]
    else:
        profile=[(-1,0),(-.80,.32),(-.50,.56),(-.11,.93),(.05,1),(.23,.68),(.73,.40),(1,.02)]
    if far:profile=[profile[k] for k in (0,2,4,6,7)]
    rings=[]
    for (cx,cy),(dx,dy),r in zip(rxy,dxy,widths):
        n=hypot(dx,dy)
        nx,ny=-dy/n,dx/n
        # Width is measured on the rectification. The ridge changes height at
        # blade tips so that they taper in elevation as well as in plan.
        height=(.0205 if is_scroll else .0173)*min(1.,r/8.)+.0020
        base=.0115 if is_scroll else .0145
        if lower:
            base=.0107;height*=.58
        ring=[project(cx+nx*r*f,cy+ny*r*f,base+height*v) for f,v in profile]
        ring.extend([project(cx+nx*r,cy+ny*r,.0077),project(cx-nx*r,cy-ny*r,.0077)])
        rings.append(ring)
    size=len(rings[0]);vertices=[v for ring in rings for v in ring]
    faces=connect_rings(rings)
    for row,reverse in [(0,True),(len(rings)-1,False)]:
        # The cap is a fan around its interior centroid.
        centre=len(vertices);vertices.append(np.mean(rings[row],axis=0))
        start=row*size
        for k in range(size):
            a,c=start+k,start+(k+1)%size
            faces.append((a,centre,c) if reverse else (centre,a,c))
    add_closed(b,vertices,faces,MATERIALS[1 if is_scroll else 2],'Gable leaf | '+name)

def boss(b,index,c,far,project):
    x,z,rx,rz=c
    count=18 if far else 32
    # The original casts a short shadow at the bevel and has a broad,
    # nearly flat face on each scroll end, visible in both dated views.
    bands=[(.86,.010),(1,.018),(.99,.025),(.91,.031),(.82,.0335),(.28,.0337)]
    rings=[[project(x+rx*r*cos(t*2*pi/count),z+rz*r*sin(t*2*pi/count),depth)
            for t in range(count)] for r,depth in bands]
    vertices=[v for ring in rings for v in ring];faces=connect_rings(rings)
    low=len(vertices);vertices.append(project(x,z,bands[0][1]))
    hi=len(vertices);vertices.append(project(x,z,.0338))
    for k in range(count):
        j=(k+1)%count
        faces.extend([(low,j,k),(hi,5*count+k,5*count+j)])
    add_closed(b,vertices,faces,MATERIALS[1],'Gable leaf | volute button '+str(index))

def add_acanthus_relief(b,lod,row):
    x0,x1,z0,z1,y=(float(row[k]) for k in ('x0','x1','z0','z1','face_y'))
    span=x1-x0;height=z1-z0
    if min(span,height)<=0:raise ValueError('Expected positive panel width and height')
    far=lod is True or lod=='lod';depth=float(row.get('depth_scale',1.))
    def project(u,v,d):
        return [x0+span*u/720,y-span*depth*d,z1-height*v/370]
    # One back slab, flat and matte beneath the cut brick. The building's top
    # and bottom projecting cornices and the upper blank brick screen join it.
    corners=[(0,0),(720,0),(720,370),(0,370)]
    ends=[[project(u,v,r)for u,v in corners]for r in (-.001,.009)]
    faces=connect_rings(ends)+[(0,2,1),(0,3,2),(4,5,6),(4,6,7)]
    add_closed(b,ends[0]+ends[1],faces,MATERIALS[0],'Gable leaf | relief bed')
    # The outermost rolls meet the frame. Allow their rounded cheeks to
    # approach the measured edges while keeping the stone wholly on the panel.
    def carving(u,v,d):
        q,r=metric_point(7.4+.986*u,1.8+.972*v)
        return project(q,r,d)
    for name,p in BASES.items():stroke(b,p,far,carving,name,False,lower=True)
    for name,p in SCROLLS.items():stroke(b,p,far,carving,name,True)
    for name,p in LEAVES.items():stroke(b,p,far,carving,name,False)
    for index,c in enumerate(BOSSES,1):boss(b,index,c,far,carving)
