"""Visible condenser housings, brackets and ground-level vents on the measured wall faces."""
from shapely.geometry import Point,box
from shapely.ops import unary_union
import numpy as np
from house_finishes import SILL

CASING='280-2 | chalk white condenser case'
FAN='280-2 | shaded condenser grille'
WIRE='280-2 | galvanized fan guard'
IRON='280-2 | weathered mounting bracket'
VENT='280-2 | dark plinth vent'
PALETTE={CASING:{'color':[.73,.715,.650],'roughness':.82},
         FAN:{'color':[.148,.152,.132],'roughness':.80},
         WIRE:{'color':[.51,.513,.46],'roughness':.63,'metallic':.36},
         IRON:{'color':[.286,.253,.210],'roughness':.77,'metallic':.26},
         VENT:{'color':[.129,.119,.109],'roughness':.92}}

def coordinates(face,camera,pixels,depth=0.):
    values=np.array([camera.plane(p,face.center+face.n*depth,face.n) for p in pixels])
    return np.column_stack([(values-face.center)@face.t,values[:,2]])

def condenser(face,camera,native_box,label,lod,fan=True):
    x0,y0,x1,y1=native_box
    a=coordinates(face,camera,[(x0,y0),(x1,y0),(x1,y1),(x0,y1)],.30)
    u=np.mean(a[:,0]);z=np.mean(a[:,1]);w=np.ptp(a[:,0]);height=np.ptp(a[:,1])
    # The broadside support depth cannot be independently measured in every view.
    # Preserve measured face widths and put the rear of each case just clear of the wall.
    face.box(u,z,w,height,.276,.165,CASING,label+' cabinet')
    face.prism(box(u-w/2-.008,z+height/2-.021,u+w/2+.008,z+height/2),.010,.310,CASING,label+' folded lid')
    for dx in (-.30*w,.30*w):
        face.box(u+dx,z-height/2-.022,.047,.037,.32,.158,IRON,label+' bracket shelf')
        brace=[face.point(u+dx,z-height/2-.17,.012),face.point(u+dx,z-height/2-.034,.252)]
        face.builder.tube(brace,.012,IRON,5 if lod else 8,label+' diagonal bracket')
    r=.31*min(w,height);cx=u-.15*w if w>1.35*height else u
    if fan:
        disc=Point(cx,z).buffer(r,quad_segs=6 if lod else 11)
        face.prism(disc,.302,.306,FAN,label+' circular opening')
        guard=disc.difference(disc.buffer(-.020,quad_segs=6 if lod else 11))
        if not lod:
            for n in (.35,.64,.83):
                ring=Point(cx,z).buffer(n*r,quad_segs=10)
                guard=guard.union(ring.difference(ring.buffer(-.007)))
            for dx in [-.43,0,.43]:
                guard=guard.union(disc.intersection(box(cx+dx*r-.006,z-r,cx+dx*r+.006,z+r)))
        face.prism(guard,.306,.315,WIRE,label+' fan guard')
    else:
        for n in range(3 if lod else 7):
            x=u-w*.37+w*.74*(n+.5)/(3 if lod else 7)
            face.prism(box(x-.008,z-.30*height,x+.008,z+.30*height),.302,.308,FAN,label+' louvre')
def bracket_pair(face,aperture,lod):
    x0,z0,x1,z1=aperture.bounds
    for u in (x0+.15,x1-.12):
        face.builder.tube([face.point(u,z0-.15,.025),face.point(u,z0+.04,.31),face.point(u,z0+.30,.31)],
                          .011,IRON,5 if lod else 8,'280-2 south / projected guard arm')
    face.builder.tube([face.point(x0+.15,z0+.30,.31),face.point(x1-.12,z0+.30,.31)],.010,IRON,
                      5 if lod else 8,'280-2 south / guard rail')
def ground_vent(face,camera,pixels):
    pos=coordinates(face,camera,pixels,.008)
    u0,z1=pos[0];u1,z0=pos[1]
    u0,u1=sorted((u0,u1));z0,z1=sorted((z0,z1))
    frame=box(u0,z0,u1,z1)
    face.prism(frame,.005,.018,SILL,'small rectangular vent surround')
    inner=frame.buffer(-.024,join_style=2)
    if inner.is_empty:return
    face.prism(inner,.018,.021,VENT,'dark plinth opening')
    for t in np.linspace(.20,.80,4):
        x=u0+(u1-u0)*t
        face.prism(inner.intersection(box(x-.008,z0,x+.008,z1)),.021,.029,IRON,'vent finger')
