"""Recessed redwood casements, panelled shutters and round attic vents of the 517 villa."""
from math import tau,cos,sin
from shapely.geometry import box, Polygon
from shapely.ops import unary_union
from photo_architecture import opening
from villa_materials import SASH,SHUTTER,GLASS,LIGHT,DARK,STONE,SILL


def circle(u,z,r,segments):
    return Polygon([(u+r*cos(tau*i/segments),z+r*sin(tau*i/segments)) for i in range(segments)])


def shutter(face,u,sill,width,height,lod,side,label):
    """An outer frame, two inset louvred panels and the middle rail are separate visible surfaces."""
    t=min(.043,width*.12);mid=sill+height*.56
    outer=box(u-width/2,sill,u+width/2,sill+height)
    panels=[box(u-width/2+t,sill+t,u+width/2-t,mid-.035),
            box(u-width/2+t,mid+.035,u+width/2-t,sill+height-t)]
    face.prism(outer,0.047,0.067,SHUTTER,label+' shutter back')
    face.prism(outer.difference(unary_union(panels)),0.066,0.103,SASH,label+' raised shutter frame')
    for poly in panels:
        left,low,right,high=poly.bounds
        pitch=.115 if lod else .068
        count=max(2,int((high-low)/pitch));pitch=(high-low)/count
        for i in range(count):
            h=low+i*pitch
            points=[face.point(left,h,.072),face.point(right,h,.072),
                    face.point(right,h+.70*pitch,.091),face.point(left,h+.70*pitch,.091)]
            face.builder.add(points,[(0,1,2,3)],SHUTTER,label+' shutter blades')
    if not lod:
        for h in [sill+.16,sill+height-.16]:
            face.box(u-side*(width/2-.048),h,.042,.10,.034,.118,SASH,label+' hinge')


def casement(face,shape,lod,label,cols=2,transom=True,shutters=(),closed=False,stone_sill=True):
    left,sill,right,head=shape.bounds;u=(left+right)/2;w=right-left;h=head-sill
    inner=shape.buffer(-max(.036,min(.062,w*.049)),join_style=2)
    if inner.is_empty:raise ValueError(label)
    lines=[]
    # The wider balcony windows have paired opening leaves and a continuous row of top lights.
    for col in range(1,cols):
        cut=left+w*col/cols;thickness=.043 if col%2==0 and cols>=4 else .028
        lines.append(box(cut-thickness/2,sill,cut+thickness/2,head))
    if transom:
        z=head-min(.49,h*.26)
        lines.append(box(left,z-.026,right,z+.026))
    if cols>=3:
        mid=sill+.38*h
        lines.append(box(left,mid-.014,right,mid+.014))
    bars=inner.intersection(unary_union(lines)) if lines else Polygon()
    panes=inner.difference(bars)
    face.prism(shape.difference(inner),-.15,-.083,SASH,label+' outer frame')
    if not bars.is_empty:face.prism(bars,-.153,-.100,SASH,label+' casement muntins')
    glass_polys=getattr(panes,'geoms',(panes,))
    for i,glass in enumerate(sorted(glass_polys,key=lambda p:(round(p.centroid.x,3),p.centroid.y))):
        face.prism(glass,-.187,-.156,LIGHT if (i+cols)%4==1 else GLASS,label+' recessed panes')
    if stone_sill:
        face.box(u,sill-.043,w+.174,.095,.27,.028,SILL,label+' stone sill')
    if closed:
        for side in [-1,1]:
            shutter(face,u+side*w/4,sill+.018,w/2-.014,h-.035,lod,side,label)
    else:
        for side in shutters:
            shutter(face,u+side*(w*.75+.035),sill+.015,w*.50-.018,h-.03,lod,side,label)


def round_attic(face,u,z,lod,label):
    n=20 if lod else 40;outer=circle(u,z,.347,n);inside=circle(u,z,.263,n)
    face.prism(outer.difference(inside),-.035,.076,STONE,label+' round stone casing')
    face.prism(inside,-.168,-.148,DARK,label+' louvre backing')
    for i in range(-2,3):
        h=z+i*.070
        strip=inside.intersection(box(u-.30,h-.016,u+.30,h+.016))
        face.prism(strip,-.076,-.039,SHUTTER,label+' horizontal vent slats')
    return inside


def glazed_opening(centre,sill,width,height,arch=0,lod=False):
    return opening(centre,sill,width,height,arch=arch,segments=12 if lod else 28)
