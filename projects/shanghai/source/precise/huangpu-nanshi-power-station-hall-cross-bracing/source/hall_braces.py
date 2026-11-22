"""Panels and visible steelwork of one photographed two-storey bay of the power station."""
import json
from math import hypot
from pathlib import Path

SURVEY=json.loads((Path(__file__).parent/'survey.json').read_bytes())
def pigment(rgb,roughness=.83,metallic=0):
    def linear(v):return v/3294.6 if v<=10 else ((v/255+.055)/1.055)**2.4
    return {'color':[linear(v) for v in rgb],'roughness':roughness,'metallic':metallic}
PALETTE={
    'hall infill':pigment((169,157,139)), 'concrete pier':pigment((183,175,157)),
    'pier side':pigment((148,140,123)), 'dark pier stripe':pigment((96,98,100)),
    'steel brace':pigment((100,101,102),.72,.16), 'steel flange':pigment((92,95,99),.69,.20),
    'horizontal steel web':pigment((76,77,78),.80,.16), 'lintel underface':pigment((164,154,137)),
}
def xz(p):
    u,v=p;h=SURVEY['crop_to_xz_homography'];s=h[2][0]*u+h[2][1]*v+h[2][2]
    return ((h[0][0]*u+h[0][1]*v+h[0][2])/s,(h[1][0]*u+h[1][1]*v+h[1][2])/s)
def prism(b,points,y_front,y_back,mat,label):
    if sum(x1*z2-z1*x2 for (x1,z1),(x2,z2)in zip(points,points[1:]+points[:1]))<0:points=points[::-1]
    n=len(points);vertices=[(x,y,z)for y in (y_front,y_back)for x,z in points]
    faces=[tuple(range(n)),tuple(reversed(range(n,2*n)))]
    faces.extend(((i+1)%n,i,i+n,(i+1)%n+n)for i in range(n));b.add(vertices,faces,mat,label)
def rectangle(b,x0,x1,z0,z1,y,d,mat,name):
    prism(b,[(x0,z0),(x1,z0),(x1,z1),(x0,z1)],y,d,mat,name)
def photo_polygon(b,points,y,d,material,label):
    prism(b,[xz(p)for p in points],y,d,material,label)
def brace_shape(a,b,r):
    dx,dz=b[0]-a[0],b[1]-a[1];h=hypot(dx,dz);sx,sz=-dz*r/h,dx*r/h
    return [(a[0]-sx,a[1]-sz),(a[0]+sx,a[1]+sz),(b[0]+sx,b[1]+sz),(b[0]-sx,b[1]-sz)]
def add_building(builder,lod):
    b=builder;h=SURVEY['nominal_height_m']
    rectangle(b,-2,2,-.31,h+.07,.39,.58,'hall infill','recessed concrete infill in two braced storeys')
    for side,a,c in [('photo left',-2.52,-1.98),('photo right',1.98,2.66)]:
        rectangle(b,a,c,-.31,h+.47,-.16,.59,'concrete pier',side+' pale structural pier')
    for name,quad in SURVEY['pier_stripes_crop_px'].items():photo_polygon(b,quad,-.165,-.154,'dark pier stripe',name)
    for i,(name,points) in enumerate(SURVEY['visible_braces_crop_px'].items()):
        start,end=map(xz,points);front=[.04,-.045,.04,-.045][i];w=[.153,.142,.142,.123][i]
        prism(b,brace_shape(start,end,w),front,front+.146,'steel brace',name)
        if not lod:
            # Edge strips let the outward face catch the light along the photographed rolled edge.
            dx,dz=end[0]-start[0],end[1]-start[1];length=hypot(dx,dz)
            for j,off in enumerate([w-.007,-w+.007]):
                step=(-dz*off/length,dx*off/length)
                e,f=[(v[0]+step[0],v[1]+step[1])for v in (start,end)]
                prism(b,brace_shape(e,f,.006),front-.006,front+.006,'steel brace',name+f' edge {j+1}')
    # The two horizontal joints have visibly different depths and double flange edges.
    for label,coords in [('mid-storey',[(122,347),(353,300)]),('lower',[(126,610),(354,615)])]:
        z=sum(xz(p)[1] for p in coords)/2
        rectangle(b,-2.03,2.06,z-.125,z+.125,.025,.14,'horizontal steel web',label+' connecting web')
        for d,part in [(-.142,'lower flange'),(.132,'upper flange')]:
            rectangle(b,-2.03,2.06,z+d-.014,z+d+.014,-.075,.22,'steel flange',label+' '+part)
    rectangle(b,-2.58,2.7,h-.02,h+.27,-.23,.55,'lintel underface','overhead concrete beam above visible bracing')
    rectangle(b,-2.60,2.72,h+.27,h+.41,-.26,.55,'concrete pier','upper edge of concrete beam')
    for side,l,r in [('left',-2.32,-2.16),('right',2.09,2.28)]:
        rectangle(b,l,r,h-.48,h+.22,-.249,-.14,'concrete pier',side+' pendant support of overhead beam')
