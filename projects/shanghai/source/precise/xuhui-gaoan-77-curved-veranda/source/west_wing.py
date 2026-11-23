"""West chimney face, stepped entrance bay and visible outside return of the early house."""
import json
from math import pi,cos,sin
from pathlib import Path
import numpy as np
from shapely.geometry import Polygon,box
from shapely.ops import unary_union
from garden_sashes import sash
from house_layout import DECK_Z,POST_SPAN,U
from materials import BASE,BRICK,DARK,IRON,PLASTER,RECESS,RIDGE,STONE
from side_eave import add_side_eave
from south_verandah import slab
HERE=Path(__file__).resolve().parent
SURVEY=json.loads((HERE.parent/'measurements/west-eave-photo-control.json').read_bytes())
H=np.array(SURVEY['cameras']['paper2022']['plane_to_pixel'])
WEST_SPAN=SURVEY['reference_units']['span_first_to_last_saddle_m']
ORIGIN=WEST_SPAN+.47
# The west rectification was fitted in units conditional on a 65.5 mm facing course.
# Reconcile both photographed elevations to the independent street-view baseline.
BRICK_PRIOR=json.loads((HERE.parent/'measurements/south-brick-course-scale.json').read_text())
WEST_CAL=POST_SPAN/BRICK_PRIOR['conditional_mean_span_m']
# The garden-end cross timber is identifiable on the 2012 and 2018 west photos.
# Their independent wall-plane intersections put the saddle datum at 9.23–9.37 m.
SEAT=(DECK_Z+.22)/WEST_CAL
SOFFIT=SEAT+1.31
def on_plane(x,y):
    q=np.linalg.solve(H,[x,y,1.]);return q[:2]/q[2]
def rect_from_photo(corners):
    a,b,c,d=[on_plane(x,y)for x,y in corners]
    return box((a[0]+d[0])/2,SEAT+(d[1]+c[1])/2,(b[0]+c[0])/2,SEAT+(a[1]+b[1])/2)
def arch(a,b,bottom,shoulder,n=24):
    r=(b-a)/2;mid=(a+b)/2
    return Polygon([(a,bottom),(b,bottom),*[(mid+r*cos(pi*k/n),shoulder+r*sin(pi*k/n))for k in range(n+1)]])
def brick_arch(f,shape,name,lod):
    a,z,b,t=shape.bounds;c=(a+b)/2;r=(b-a)/2;spring=t-r
    f.solid(shape,-.204,-.19,RECESS,name+' | inset dark opening')
    f.solid(shape.buffer(.109,join_style=2).difference(shape),-.02,.035,BRICK,name+' | brick reveal')
    n=11 if lod else 23
    for i in range(n):
        left=pi*(i+.05)/n;right=pi*(i+.95)/n
        outline=Polygon([(c+rad*cos(phi),spring+rad*sin(phi))for rad,phi in [(r,left),(r+.142,left),(r+.142,right),(r,right)]])
        f.solid(outline,.030,.067,STONE if i==n//2 else BRICK,name+' | individual arch brick')
def side_openings():
    points=dict(zip(SURVEY['point_names'],SURVEY['points_m']));rows={}
    for key in ['left','right']:
        a,head=points[key+'-window-tl'];b,_=points[key+'-window-tr'];_,low=points[key+'-window-bl']
        rows[key+' upper']=box(a,SEAT+low,b,SEAT+head)
    rows['right lower']=rect_from_photo([(418,311),(441,309),(446,365),(421,368)])
    rows['left lower']=rect_from_photo([(263,317),(285,315),(284,378),(262,381)])
    return rows
def west_wall(f,lod):
    face=f.face(0,ORIGIN,0,-1);holes=side_openings()
    face.solid(box(-.51,0,ORIGIN,SOFFIT).difference(unary_union(list(holes.values()))),-.185,0,PLASTER,'west wing | lime plaster with four recessed windows')
    for name,hole in holes.items():
        sash(face,hole,'west chimney face | '+name,2,(.20,.44),True)
    add_side_eave(face,lod,dict(first_s=0,last_s=WEST_SPAN,seat_z=SEAT,eave_z=SOFFIT,ground_z=0))
    # The roof emerges behind a substantial pale rendered chimney, ending in three separate open pots.
    # Values below are in the unified street-scaled metre frame. Convert once here, before the west survey is placed.
    def old(metres):return metres/WEST_CAL
    u0,u1=old(-.16),old(.27);d0,d1=old(2.28),old(3.49)
    h=old(DECK_Z+4.18);shoulder=old(DECK_Z+3.00);crown=old(DECK_Z+4.50);top=old(DECK_Z+5.00)
    slab(f,box(u0,d0,u1,d1),SOFFIT-old(.30),shoulder,PLASTER,'west chimney | lower rendered shaft')
    slab(f,box(u0+old(.025),d0+old(.045),u1-old(.025),d1-old(.045)),shoulder-old(.08),h,PLASTER,'west chimney | upper rendered shaft')
    slab(f,box(u0-old(.026),d0-old(.028),u1+old(.024),d1+old(.034)),h-old(.09),h,STONE,'west chimney | projecting cap band')
    wide=[(u0-old(.026),d0-old(.028)),(u1+old(.024),d0-old(.028)),(u1+old(.024),d1+old(.034)),(u0-old(.026),d1+old(.034))]
    small=[(u0+old(.025),d0+old(.06)),(u1-old(.025),d0+old(.06)),(u1-old(.025),d1-old(.06)),(u0+old(.025),d1-old(.06))]
    vertices=[f.point(x,y,z) for plan,z in [(wide,h),(small,crown)] for x,y in plan]
    faces=[(3,2,1,0),(4,5,6,7)]+[(i,(i+1)%4,4+(i+1)%4,i+4) for i in range(4)]
    f.b.add(vertices,faces,PLASTER,'west chimney | battered coping to flue bases')
    from shapely.geometry import Point
    for i,d in enumerate([2.41,2.74,3.03],1):
        c=Point(old(.055),old(d));n=4 if lod else 7
        pipe=c.buffer(old(.078),quad_segs=n).difference(c.buffer(old(.047),quad_segs=n))
        slab(f,pipe,crown,top,STONE,'west chimney | open flue pot '+str(i))
        collar=c.buffer(old(.087),quad_segs=n).difference(c.buffer(old(.047),quad_segs=n))
        slab(f,collar,top-old(.065),top+old(.003),STONE,'west chimney | pot rim')
    return face

def recessed_west_bay(f,lod):
    # The second pair of arches turn a corner below the window of the rear bay. The inaccessible rear is cut.
    a,b=-4.05,-.51;x=.65;top=SOFFIT-.85;face=f.face(x,ORIGIN,0,-1)
    h=arch(a+.38,a+1.76,.16,2.18,12 if lod else 28)
    upper=box(a+.88,SEAT-2.91,a+1.49,SEAT-1.30)
    face.solid(box(a,0,b,top).difference(unary_union([h,upper])),-.16,0,PLASTER,'west rear bay | street-facing wall')
    brick_arch(face,h,'west rear bay | entrance arch',lod);sash(face,upper,'west rear bay | upper sash')
    # The short return faces the garden end, as seen between the two west-facing planes in the 2013 view.
    ret=f.face(-.85,ORIGIN-b,1,0);portal=arch(.10,1.33,.16,2.22,12 if lod else 26)
    sash2=box(.27,SEAT-2.81,.90,SEAT-1.23)
    ret.solid(box(0,0,1.50,top).difference(unary_union([portal,sash2])),-.16,0,PLASTER,'west rear bay | short return')
    brick_arch(ret,portal,'west entrance | returned semicircular arch',lod);sash(ret,sash2,'west return | upper sash')
    slab(f,box(-.89,ORIGIN-b,x+.19,ORIGIN-a),top-.075,top+.08,STONE,'west rear bay | broad soffit')
    for s in [a+.12,a+.69,a+1.26,a+1.84,a+2.41]:
        face.rect(s-.049,s+.049,3.18,3.32,.012,.84,DARK,'west entrance | exposed canopy rafters')


def add_west_wing(f,lod):
    from placement import Facade
    # Model the rectified photo in its original coordinates so its control points and UVs retain their meaning.
    first=len(f.b.parts)
    survey_face=Facade(f.b)
    west_wall(survey_face,lod)
    recessed_west_bay(survey_face,lod)
    for part in f.b.parts[first:]:
        part['vertices']=[f.point(x*WEST_CAL,d*WEST_CAL,z*WEST_CAL) for x,d,z in part['vertices']]
