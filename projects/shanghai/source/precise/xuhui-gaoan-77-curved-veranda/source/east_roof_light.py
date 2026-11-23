"""Short east-facing roof light visible beyond the garden hip in plates 35 and 38."""
from shapely.geometry import Polygon, box

from garden_sashes import sash
from house_layout import D, U, Z
from materials import DARK, PLASTER, STONE

# Working roof intersection in registered photograph 35, in local post spans.
INNER_U, FACE_U = 2.02, 2.35
FRONT_D, REAR_D = 1.15, 1.42
CUT = box(U(INNER_U) + .020, D(FRONT_D) + .020,
          U(FACE_U) - .020, D(REAR_D) - .020)


def lid(x,d):
    """The two visible coping edges descend towards the east face and its far end."""
    return Z(.715) - .30*(x-U(FACE_U)) - .21*(d-D(FRONT_D))


def add_east_roof_light(f,lod=False):
    x0,x1 = U(INNER_U),U(FACE_U)
    d0,d1 = D(FRONT_D),D(REAR_D)
    low = Z(.17)
    # The foliage hides the bottom of the frame and the last pane at the far end.
    east = f.face(x1,0,0,1)
    left,right = D(1.174),D(1.392)
    aperture = box(left,Z(.235),right,Z(.534))
    side = Polygon([(d0,low),(d1,low),(d1,lid(x1,d1)-.320),
                    (d0,lid(x1,d0)-.320)])
    east.solid(side.difference(aperture),-.092,0,PLASTER,
               'east roof light | rendered window wall')
    sash(east,aperture,'east roof light | narrow glazed timber leaves',2,(.25,),False,depth_scale=.43)
    front = f.face(0,d0,1,0)
    cheek = Polygon([(x0,low),(x1,low),(x1,lid(x1,d0)-.320),
                     (x0,lid(x0,d0)-.320)])
    front.solid(cheek,-.087,0,PLASTER,'east roof light | plain garden cheek')
    # Two small closures stop at the shortest envelope evidenced by the visible window.
    back = f.face(0,d1,-1,0)
    rear = Polygon([(-x1,low),(-x0,low),(-x0,lid(x0,d1)-.320),(-x1,lid(x1,d1)-.320)])
    back.solid(rear,-.087,0,PLASTER,'east roof light | short rear return')
    inner = f.face(x0,0,0,-1)
    inside = Polygon([(-d1,low),(-d0,low),(-d0,lid(x0,d0)-.320),(-d1,lid(x0,d1)-.320)])
    inner.solid(inside,-.087,0,PLASTER,'east roof light | short inner return')
    for projection,base,top,mat,name in [
            (.050,-.334,-.151,DARK,'dark fascia and soffit'),
            (.076,-.156,-.091,STONE,'weathered intermediate course'),
            (.085,-.094,0,STONE,'upper coping')]:
        plan=box(x0-.030,d0-projection,x1+projection,d1+projection)
        f.b.prism(plan,base,top,lambda x,d,s:f.point(x,d,lid(x,d)+s),mat,
                  'east roof light | '+name)
