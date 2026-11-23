"""Cast relief above the central stair lights and along the ground-floor stringcourse."""
from math import cos, sin, pi
import numpy as np
from shapely.geometry import LineString, Point, box
from shapely.ops import unary_union
from street_materials import CREAM, LIME

def spiral(x,z,rx,rz,turns=1.,n=32):
    t=np.linspace(0.,1.,n)
    return [(x+rx*(.12+.88*k)*cos(2*pi*turns*k+.65),
             z+rz*(.12+.88*k)*sin(2*pi*turns*k+.65)) for k in t]

def draped_panel(face, bounds, lod):
    x0,z0,x1,z1=bounds
    width=x1-x0;height=z1-z0;centre=(x0+x1)/2
    face.rect(x0,x1,z0,z1,-.018,.063,CREAM,'staircase | individual cast panel')
    # One curled bud caps a narrow tapered palmette, with short upturned leaves
    # down both sides. The lower fans widen towards the panel corners.
    def at(u,v):return (x0+width*u,z0+height*v)
    stalks=[[(.49,.08),(.51,.23),(.54,.36),(.58,.63),(.57,.72)]]
    for i in range(5 if lod else 9):
        t=i/(4 if lod else 8)
        base=.04+.47*t
        for side in (-1,1):
            a=.48+side*(.025+.145*(1-t))
            b=.5+side*(.235+.135*(1-t))
            c=.50+side*(.36+.025*(1-t))
            stalks.append([(a,base),(b,base+.046),(c,base+.112)])
    shapes=[LineString([at(u,v) for u,v in path]).buffer(.011 if lod else .010,quad_segs=1 if lod else 3,cap_style=1,join_style=1) for path in stalks]
    shapes.append(LineString(spiral(centre,z0+.845*height,.265*width,.095*height,1.13,20 if lod else 36)).buffer(.018,quad_segs=2 if lod else 4))
    face.solid(unary_union(shapes),.059,.095,CREAM,'staircase | scroll, central stem and paired leaves')

def frieze(face,x0,x1,z,lod):
    face.rect(x0,x1,z,z+.46,-.023,.090,CREAM,'stringcourse | continuous cast band')
    face.rect(x0,x1,z-.047,z+.013,-.015,.117,LIME,'stringcourse | lower bead')
    face.rect(x0,x1,z+.44,z+.49,-.021,.114,LIME,'stringcourse | upper bead')
    count=max(1,round((x1-x0)/.71));repeat=(x1-x0)/count
    for i in range(count):
        a=x0+i*repeat;cx=a+.45*repeat
        shape=LineString(spiral(cx,z+.245,.13,.121,1.12,15 if lod else 26)).buffer(.013,quad_segs=1 if lod else 3)
        ribbons=[LineString([(a+.01,z+.43),(a+.28*repeat,z+.045),(a+.94*repeat,z+.43)]).buffer(.013,quad_segs=1 if lod else 3),
                 LineString([(a+.73*repeat,z+.08),(a+.98*repeat,z+.37)]).buffer(.010,quad_segs=1 if lod else 3)]
        face.solid(unary_union([shape,*ribbons]).intersection(box(a,z,a+repeat,z+.45)),.088,.112,
                   CREAM,'stringcourse | repeated scroll and diagonal ribbon')
