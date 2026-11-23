"""Shallow stone carving on the two polygonal garden bays of 336 Jianguo West Road.

The front and canted panels are distinguished in photographs 03 and 04. The
stem paths and corner knots reproduce their silhouettes, not a conjectural
iconography for the small, poorly resolved ornaments.
"""
import math
import numpy as np
from shapely import affinity
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union

STONE='Fudefang | pale pink dressed masonry'
SCULPT='Fudefang | warm carved stone edges'
DEEP='Fudefang | recessed carving field'
PALETTE={STONE:dict(color=[.62,.526,.438],roughness=.95),
         SCULPT:dict(color=[.727,.620,.520],roughness=.91),
         DEEP:dict(color=[.549,.460,.398],roughness=.94)}
def mapped(poly,center,width,bottom,height):
    scale=affinity.scale(poly,xfact=width,yfact=height,origin=(0,0))
    return affinity.translate(scale,center,bottom)
def motif_points(points):
    return LineString(points)
def stroke(points,width=.012):
    return motif_points(points).buffer(width,cap_style=1,join_style=1,quad_segs=3)
def bezier(points,n):
    p=np.asarray(points);t=np.linspace(0,1,n)[:,None]
    return (1-t)**3*p[0]+3*(1-t)**2*t*p[1]+3*(1-t)*t*t*p[2]+t**3*p[3]
def bed(face,poly,center,width,z0,h,back,front,material,name):
    if not poly.is_empty:
        face.prism(mapped(poly,center,width,z0,h),back,front,material,name)
def border(w=.025):
    return box(-.5,0,.5,1).difference(box(-.5+w,w,.5-w,1-w))
def diamond(cx,cz,w,h):
    return Polygon([(cx-w,cz),(cx,cz+h),(cx+w,cz),(cx,cz-h)])
def guilloche(face,center,width,z0,height,lod):
    """Undercut trim that returns from the head and the two jambs."""
    count=max(3,round(width/.145));rows=[]
    for i in range(count):
        left=-.5+i/count
        t=np.linspace(0,1,5 if lod else 11)
        rows.append(stroke(np.column_stack((left+t/count,.53+.16*np.cos(t*2*np.pi))),.015))
    bed(face,unary_union(rows),center,width,z0,height,.062,.074,SCULPT,'running relief at window head')
def spandrel(face,center,width,z0,z1,narrow,lod):
    """One framed spandrel, with drooping boughs on broad faces and a vertical medallion on the cants."""
    h=z1-z0
    bed(face,box(-.5,0,.5,1),center,width,z0,h,.001,.025,DEEP,'recessed panel backing')
    bed(face,border(.036),center,width,z0,h,.022,.070,SCULPT,'perimeter of relief panel')
    line=border(.012)
    bed(face,affinity.scale(line,.904,.887,origin=(0,.5)),center,width,z0,h,.023,.048,STONE,'inner stepped panel border')
    knots=[]
    for x in (-.472,.472):
        for z in (.040,.96):
            knot=diamond(x,z,.041,.039)
            inner=diamond(x,z,.020,.018)
            knots.extend([knot.difference(inner),Point(x,z).buffer(.008,quad_segs=4)])
    bed(face,unary_union(knots),center,width,z0,h,.059,.083,SCULPT,'four square corner knots')
    relief=[];tips=[]
    if narrow:
        for hand in [-1,1]:
            theta=np.linspace(-.55*np.pi,1.46*np.pi,15 if lod else 32);radius=np.linspace(.29,.055,len(theta))
            coords=np.column_stack((hand*(.035+radius*np.cos(theta)),.48+.9*radius*np.sin(theta)))
            relief.append(stroke(coords,.022))
            relief.append(stroke(bezier([(hand*.02,.26),(hand*.13,.28),(hand*.34,.62),(hand*.17,.76)],10 if lod else 20),.022))
            for j in [0,1,2]:
                tips.append(diamond(hand*(.085+.065*j),.56+.042*j,.044,.055))
        relief.append(diamond(0,.43,.105,.135).difference(diamond(0,.43,.064,.092)))
    else:
        for hand in [-1,1]:
            bough=bezier([(hand*.39,.72),(hand*.24,.30),(hand*.10,.42),(0,.51)],16 if lod else 31)
            relief.append(stroke(bough,.022))
            second=bezier([(hand*.38,.69),(hand*.22,.55),(hand*.16,.72),(hand*.09,.71)],10 if lod else 18)
            relief.append(stroke(second,.012))
            for j in range(1,5):
                t=j/5;ix=round(t*(len(bough)-1));x,z=bough[ix]
                tips.append(Polygon([(x,z+.014),(x+hand*.024,z-.024),(x+hand*.037,z-.095),(x,z-.069),(x-hand*.016,z-.036)]))
            tips.append(diamond(hand*.37,.72,.026,.049))
        relief.extend([diamond(0,.40,.086,.076),stroke([(-.065,.60),(0,.55),(.061,.60)],.018)])
        tips.append(Polygon([(-.055,.36),(0,.29),(-.068,.22),(.072,.22),(.018,.30),(.07,.36)]))
    bed(face,unary_union(relief),center,width,z0,h,.022,.061,STONE,'modelled scrolls in panel field')
    bed(face,unary_union(tips),center,width,z0,h,.040,.080,SCULPT,'raised foliage and panel pendant')
    if not lod:
        bars=[]
        for z in [.081,.919]:
            for x in np.arange(-.39,.401,.10):
                bars.append(stroke([(x-.043,z-.008),(x,z+.013),(x+.040,z-.008)],.009))
        bed(face,unary_union(bars),center,width,z0,h,.026,.055,SCULPT,'beaded edges above and below relief')
def apron(face,center,width,base,lod):
    # Both the broad and the narrow sash have their own small carved apron and suspended center.
    h=.29*min(width,1.35)
    outline=Polygon([(-.49,.94),(.49,.94),(.49,.47),(.29,.47),(.29,.32),(.17,.32),
                     (.09,.23),(0,.03),(-.09,.23),(-.17,.32),(-.29,.32),(-.29,.47),(-.49,.47)])
    bed(face,outline,center,width,base-h,h,.002,.062,STONE,'notched apron under sill')
    folds=[]
    for hand in (-1,1):
        folds.append(stroke(bezier([(hand*.39,.70),(hand*.25,.39),(hand*.13,.40),(0,.62)],11),.028))
    folds.append(diamond(0,.31,.087,.18).difference(diamond(0,.31,.05,.10)))
    bed(face,unary_union(folds),center,width,base-h,h,.059,.086,SCULPT,'center diamond with draped folds')
