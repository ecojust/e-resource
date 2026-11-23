"""Construct the sloping masonry, crest and ventilator from Fayhoo's annotated 2015 photograph."""
import numpy as np
from shapely.geometry import Polygon, box
from shapely import affinity
from ornament_chart import cut
from finishes import BRICK,STONE,RED,DARK_RED,METAL,BACK

def face(b,polygon,front,back,mat,name):
    for p in getattr(polygon,'geoms',[polygon]):
        if p.geom_type=='Polygon' and p.area>.000001:
            b.prism(p,-back,-front,lambda x,z,n:(x,-n,z),mat,name)

def image_polygon(pts,depth):
    return Polygon([cut(pt,depth) for pt in pts])

def from_image(b,pts,front,back,mat,name):
    face(b,image_polygon(pts,front),front,back,mat,name)

def ellipse(cx,cz,rx,rz,n):
    t=np.arange(n)*2*np.pi/n
    return Polygon(np.column_stack([cx+rx*np.cos(t),cz+rz*np.sin(t)]))

def fan_shape(left,right,height,segments,inner=0):
    center=(left+right)/2;half=(right-left)/2
    t=np.linspace(0,np.pi,segments+1)
    rim=np.column_stack([center[0]+half[0]*np.cos(t),center[1]+half[1]*np.cos(t)+height*np.sin(t)])
    if inner:
        core=center+(rim-center)*inner
        return Polygon(np.row_stack([rim,core[::-1]]))
    return Polygon(rim)

def add_pediment(b,lod=False):
    n=36 if lod else 96
    center=cut((777.55,615.8),.0)
    inner=ellipse(*center,.346,.342,n);mouth=ellipse(*center,.558,.518,n)
    profile=[(638.0,680),(766,561),(770,554),(791,550),(797,558),
             (956,619),(965,618),(974,614),(978,616),(978,649)]
    border=[cut(v,0) for v in profile]
    # The cream balustrade hides the red wall to the left. The lower
    # horizontal museum cut sits inside the photographed band.
    bottom=min(p[1] for p in border)-.12
    wall=Polygon([*border,(border[-1][0],bottom),(border[0][0],bottom)])
    face(b,wall.difference(inner),0,.40,BRICK,'Gable | pierced red masonry')
    for side,cap in [('left',[(637,674),(755,562),(762,560),(768,552),(775,551)]),
                     ('right',[(791,551),(801,552),(804,556),(954,611),(961,612),(972,606),(978,605)])]:
        for index,(top,under,front,back) in enumerate([(0,3,-.115,.23),(3,6.2,-.073,.18),(6.2,8,-.13,.21)]):
            poly=[(x,y+top) for x,y in cap]+[(x,y+under) for x,y in cap[::-1]]
            from_image(b,poly,front,back,STONE,f'Coping | {side} moulding {index+1}')
    # Projecting four grey keys interrupt the annular moulding.
    front=-.113
    frame=mouth.difference(inner)
    face(b,frame,front,.047,STONE,'Vent | grey surround')
    face(b,ellipse(*center,.417,.409,n).difference(inner),-.151,-.112,STONE,'Vent | inner quirk')
    for i,(dx,dz) in enumerate([(0,1),(1,0),(0,-1),(-1,0)]):
        tip=np.array([dx,dz]);tangent=np.array([-dz,dx]);rim=.552 if dx else .525
        quad=[center+r*tip+w*tangent for r,w in [(rim+.025,.092),(rim+.025,-.092),(.321,-.073),(.321,.073)]]
        face(b,Polygon(quad),-.194,-.097,STONE,f'Vent | projecting key {i+1}')
    face(b,inner,.265,.278,BACK,'Vent | dark optical backing')
    for i,z in enumerate(np.linspace(center[1]-.27,center[1]+.265,8)):
        # Each blade is angled individually and spans the elliptic opening.
        shaft=inner.intersection(box(center[0]-.4,z-.019,center[0]+.4,z+.019))
        for p in getattr(shaft,'geoms',[shaft]):
            if not p.is_empty:
                b.prism(p,-.204,-.108,lambda x,h,t,z=z:(x,-t,h+.16*(-t-.153)),METAL,f'Vent | sloping blade {i+1}')
    from_image(b,[(766,546),(792,539),(795,551),(768,560)],-.012,.36,BRICK,'Crest | short brick neck')
    ledges=[([(762,545),(797,535),(802,536),(802,539),(763,551)],-.17,.27),
            ([(760,548),(800,537),(802,539),(800,542),(764,552)],-.20,.30),
            ([(763,551),(798,541),(798,544),(767,554)],-.126,.25)]
    for i,(pts,d,h) in enumerate(ledges):
        from_image(b,pts,d,h,STONE,f'Crest | pedestal course {i+1}')
    d=-.145
    left,right=(cut(u,d) for u in [(762,546),(798,536.7)])
    high=cut((780.4,514.4),d)[1]-(left[1]+right[1])*.5
    plate=fan_shape(left,right,high,n//2)
    ring=fan_shape(left,right,high,n//2,.78)
    face(b,plate,d+.072,.36,STONE,'Crest | deep half-round stone tablet')
    face(b,ring,d-.031,d+.074,STONE,'Crest | half-round raised rim')
    center=(left+right)/2
    innerpanel=affinity.scale(plate,xfact=.79,yfact=.79,origin=tuple(center))
    face(b,innerpanel,d+.023,d+.076,DARK_RED,'Crest | red fan recess')
    for i,t in enumerate(np.linspace(.16,np.pi-.14,8)):
        radius=(right-left)/2
        tip=center+radius*np.cos(t)+[0,high*np.sin(t)]
        vec=(tip-center)*.757; length=float(np.linalg.norm(vec))
        perp=np.array([-vec[1],vec[0]])/length
        foot=center+vec*.055
        shape=Polygon([foot-perp*.018,foot+perp*.018,center+vec+perp*.026,center+vec-perp*.026])
        face(b,shape,d-.01,d+.026,RED,f'Crest | radiating clay rib {i+1}')
