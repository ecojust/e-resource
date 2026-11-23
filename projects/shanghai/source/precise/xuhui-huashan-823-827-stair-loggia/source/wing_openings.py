"""Street wing windows, folding awnings and open ventilation blocks at 823–827 Huashan Road.

Bounds are (left, sill, right, head) in local front-view metres. For a fanlight,
head is the top of the semicircular glazing. Positive face depth enters the wall.
"""
from math import cos, pi, sin

from shapely import affinity, set_precision
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union


def finish(rgb, roughness, metallic=0.):
    def linear(channel):
        value = channel / 255
        return value / 12.92 if value <= .04045 else ((value + .055) / 1.055)**2.4
    return dict(color=[linear(c) for c in rgb], roughness=roughness, metallic=metallic)


STEEL = 'Huashan front wings | green casement steel'
GLASS = 'Huashan front wings | reflected green-grey glass'
DARK = 'Huashan front wings | shadow behind openings'
SILL = 'Huashan front wings | pale cement sill'
VENT = 'Huashan front wings | green ornamental airbrick'
CANVAS = 'Huashan front wings | weathered brown awning fabric'
ROD = 'Huashan front wings | dark awning iron'
CLAY = 'Huashan front wings | red clay verge caps'
PALETTE = {STEEL:finish((62,76,67),.67,.14), GLASS:finish((91,105,105),.27,.15),
           DARK:finish((35,39,36),.94), SILL:finish((185,181,168),.85),
           VENT:finish((56,73,61),.84), CANVAS:finish((108,86,77),.94),
           ROD:finish((74,69,58),.64,.22), CLAY:finish((147,101,83),.89)}


def arc(cx, z, rx, rz, count):
    return [(cx+rx*cos(pi*j/count), z+rz*sin(pi*j/count)) for j in range(count+1)]


def opening(bounds, arched=False, lod=False):
    a, bottom, b, top = bounds
    if not arched:
        return box(a,bottom,b,top)
    w, mid = b-a, (a+b)/2
    radius = w*.333
    spring = top - radius
    cap = Polygon(arc(mid,spring,radius,radius,16 if lod else 32))
    return box(a,bottom,b,spring).union(cap)


def sash(face, bounds, label, *, arched=False, columns=6, rows=4, lod=False):
    a, bottom, b, top = bounds
    width, mid = b-a, (a+b)/2
    radius = width*.333
    spring = top-radius if arched else top
    outline = opening(bounds,arched,lod)
    rim = min(.046,.028*width)
    pieces = [outline.difference(outline.buffer(-rim,join_style=2))]
    for i in range(1,columns):
        x = a+width*i/columns
        bar = rim*.90 if (arched and i in (1,3,5)) else rim*.44
        pieces.append(box(x-bar/2,bottom,x+bar/2,spring))
    for j in range(1,rows):
        z = bottom+(spring-bottom)*j/rows
        bar = rim*.49
        pieces.append(box(a,z-bar/2,b,z+bar/2))
    if arched:
        pieces.append(box(mid-radius,spring-rim*.48,mid+radius,spring+rim*.48))
        inner = radius*.48
        pieces.append(LineString(arc(mid,spring,inner,inner,12 if lod else 28)).buffer(rim*.25,cap_style=2))
        for angle in (pi/4,pi/2,3*pi/4):
            start = (mid+inner*cos(angle),spring+inner*sin(angle))
            end = (mid+radius*cos(angle),spring+radius*sin(angle))
            pieces.append(LineString([start,end]).buffer(rim*.24,cap_style=2))
        pieces.append(box(mid-rim*.22,spring,mid+rim*.22,spring+inner))
    # One solid for connected steel avoids superimposed edges at the muntin joins.
    bars = set_precision(unary_union(pieces).intersection(outline),1e-6)
    face.solid(outline,-.196,-.183,DARK,label+' | interior recess')
    face.solid(outline,-.128,-.118,GLASS,label+' | glazing')
    face.solid(bars,-.117,-.086,STEEL,label+' | casement and glazing bars')
    face.rect(a-.047,b+.047,max(0.,bottom-.054),bottom+.004,-.108,.083,SILL,label+' | pale sill')


def _awning_mesh(face, bounds, top, retract, label, lod, measured_drop=None):
    left,right = bounds
    width = right-left
    span = 8 if lod else 18
    drop = measured_drop if measured_drop is not None else (.075 if retract else .20)
    projection = min(.31 if retract else .58,.38*width)
    points, faces = [], []
    for i in range(span+1):
        t = i/span
        x = left+width*t
        fold = -.029*(sin(2*pi*t)**2) if retract else -.012*sin(pi*t)
        sections = [(0.,top-.016),(-projection*.35,top+fold*.50),
                    (-projection*.84,top+fold-.035),(-projection,top-drop*.49+fold),
                    (-projection*.98,top-drop+fold)]
        outer = sections
        inner = [(d+.006,z-.006) for d,z in reversed(sections)]
        for d,z in outer+inner:
            points.append(face.point(x,d,z))
    ring = len(outer+inner)
    # Caps and side strips use the same edge indices on each station.
    for i in range(span):
        for j in range(ring):
            a=i*ring+j; b=i*ring+(j+1)%ring
            faces.extend([(a,b,b+ring),(a,b+ring,a+ring)])
    for j in range(len(outer)-1):
        near = (j,j+1,ring-2-j,ring-1-j)
        far = tuple(span*ring+k for k in near)
        faces.extend([(near[0],near[3],near[2]),(near[0],near[2],near[1]),
                      (far[0],far[1],far[2]),(far[0],far[2],far[3])])
    # Surface normals must face out on the thin folded canvas.
    import numpy as np
    p=np.asarray(points)
    tri=p[np.asarray(faces)]-p[0]
    if np.einsum('ij,ij->i',tri[:,0],np.cross(tri[:,1],tri[:,2])).sum()<0:
        faces=[(a,c,b) for a,b,c in faces]
    face.b.add(points,faces,CANVAS,face.label+' | '+label+' | fabric')
    for x in (left+.029,right-.029):
        face.rail([(x,.010,top-(.62 if retract else .54)),(x,-projection*.96,top-drop*.55)],
                  .011,ROD,label+' | awning brace',6 if lod else 8)


def awning(face, bounds, label, *, retract=False, lod=False, measurements=None):
    a,bottom,b,top = bounds
    margin = (b-a)*(.145 if retract else .115)
    if measurements is None:
        _awning_mesh(face,(a-margin,b+margin),top+(.17 if retract else .09),retract,label,lod)
    else:
        left,right,attachment,drop=measurements
        _awning_mesh(face,(left,right),attachment,retract,label,lod,drop)


def _diamond():
    return Polygon([(0,.50),(.50,0),(0,-.50),(-.50,0)])


def vent_outline(bounds, cells):
    a,lo,b,hi=bounds
    shape=_diamond()
    if cells>1:
        shape=Polygon([(-1.5,0),(-1.,-.50),(1.,-.50),(1.5,0),(1.,.50),(-1.,.50)])
    return affinity.translate(affinity.scale(shape,(b-a)/cells,hi-lo,origin=(0,0)),
                              xoff=(a+b)/2,yoff=(lo+hi)/2)


def geometric_vent(face,bounds,label,cells=1,lod=False):
    """One diamond flower or a three-cell hexagonal band, each with perforations."""
    a,lo,b,hi=bounds
    unit=(b-a)/cells
    panel=vent_outline(bounds,cells)
    apertures=[]
    for i in range(cells):
        # Four small, concave floral openings sit within diagonal bars.
        for sx in (-1,1):
            for sy in (-1,1):
                base=Point(.115*sx,.104*sy).buffer(.073,quad_segs=5 if lod else 9)
                notch=Point(.137*sx,.160*sy).buffer(.033,quad_segs=5 if lod else 9)
                apertures.append((i,base.difference(notch)))
        # Triangular openings between floral centre and diamond rim.
        for angle in (0,90,180,270):
            cap=Polygon([(-.185,.245),(.185,.245),(0.,.430)])
            bead=Point(0,.245).buffer(.024,quad_segs=5)
            apertures.append((i,affinity.rotate(cap.difference(bead),angle,origin=(0,0))))
    cuts=[]
    for i,shape in apertures:
        hole=affinity.scale(shape,unit,hi-lo,origin=(0,0))
        cuts.append(affinity.translate(hole,xoff=a+(i+.5)*unit,yoff=(lo+hi)/2))
    face.solid(panel,-.166,-.154,DARK,label+' | vent shadow')
    face.solid(panel.difference(unary_union(cuts)),-.090,-.017,VENT,label+' | perforated green airbrick')
