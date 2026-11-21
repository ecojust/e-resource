"""Courtyard windows with tall stone mullions, glazed transoms and timber panels."""
from math import cos,sin,pi
from shapely.geometry import box, Polygon
from shapely.ops import unary_union
from photo_architecture import opening
from pavilion_materials import CREAM,EDGE,WOOD,GLASS,REFLECT,DARK,BLACK,BRICK_EDGE


def framed(face,shape,label,lod,cols,rows,opaque_below=None):
    left,low,right,top=shape.bounds
    inner=shape.buffer(-.09,join_style=2)
    frame=shape.difference(inner)
    bars=[]
    for i in range(1,cols):
        x=left+(right-left)*i/cols
        bars.append(box(x-.028,low,x+.028,top))
    for z,thick in rows:
        bars.append(box(left,z-thick/2,right,z+thick/2))
    lattice=inner.intersection(unary_union(bars))
    face.prism(frame,-.14,-.042,WOOD,label+' outer frame')
    if not lattice.is_empty:face.prism(lattice,-.19,-.085,WOOD,label+' glazing bars')
    panes=inner.difference(lattice)
    for i,pane in enumerate(sorted(getattr(panes,'geoms',(panes,)),key=lambda g:(g.centroid.y,g.centroid.x))):
        opaque=opaque_below is not None and pane.centroid.y<opaque_below
        face.prism(pane,-.256,-.195,DARK if opaque else (GLASS,REFLECT,GLASS)[i%3],label+' panes and panels')
        if opaque and not lod and pane.area>.15:
            panel=pane.buffer(-.062,join_style=2)
            if not panel.is_empty:
                face.prism(panel,-.193,-.162,WOOD,label+' raised bottom panels')


def triple(face,x,sill,head,width,lod,label):
    height=head-sill
    group=box(x-width/2,sill,x+width/2,head)
    clear=[(-.341,.228),(0,.375),(.341,.228)]
    lights=[box(x+width*(u-w/2),sill+.07,x+width*(u+w/2),head-.07) for u,w in clear]
    face.prism(group.difference(unary_union(lights)),-.065,.055,CREAM,label+' three-light stone surround')
    for index,shape in enumerate(lights):
        base=shape.bounds[1]
        framed(face,shape,f'{label} sash {index+1}',lod,2 if index==1 else 1,
               [(head-.30*height,.105),(head-.18*height,.043),(base+.36*height,.046),(base+.19*height,.072)],
               opaque_below=base+.19*height)
    face.box(x,sill-.058,width+.19,.115,.23,.035,EDGE,label+' projecting sill')
    return group


def upper_entry(face,lod,sill):
    head=9.055;spring=8.69;w=2.53
    door=opening(0,sill,w,head-sill,head-spring,segments=18 if lod else 36)
    framed(face,door,'upper double door',lod,4,[(sill+.64,.084),(sill+1.81,.046),
             (sill+2.68,.044),(7.63,.16),(8.24,.055)],opaque_below=sill+.64)
    face.box(0,(sill+7.57)/2,.092,7.57-sill,.075,-.054,WOOD,'door meeting stile')
    for x in [-.105,.105]:
        face.box(x,sill+1.35,.041,.255,.064,-.013,BLACK,'entry door pulls')
    for i in range(15 if lod else 31):
        n=15 if lod else 31
        radii=[(w/2+.025,head-spring+.045),(w/2+.18,head-spring+.31)]
        a=(i+.045)*pi/n;b=(i+.955)*pi/n
        coords=[]
        for r,t in [(radii[0],a),(radii[1],a),(radii[1],(a+b)/2),(radii[1],b),(radii[0],b),(radii[0],(a+b)/2)]:
            coords.append((r[0]*cos(t),spring+r[1]*sin(t)))
        face.prism(Polygon(coords),.004,.040,BRICK_EDGE,'radial brick lintel')
    return door


def timber_basement(face,lod):
    w=2.70;h=3.51
    hole=box(-w/2,0,w/2,h)
    edge=hole.buffer(-.074,join_style=2)
    face.prism(hole.difference(edge),-.135,-.036,DARK,'basement door reveal')
    face.prism(edge,-.205,-.14,DARK,'basement timber backing')
    for sign in [-1,1]:
        x=sign*w*.245
        for row,(z,height) in enumerate(((.86,1.40),(2.09,.84),(2.96,.74))):
            panel=box(x-.565,z-height/2,x+.565,z+height/2)
            face.prism(panel,-.14,-.118,WOOD,'basement double door fielded panels')
            if not lod:
                inset=panel.buffer(-.068,join_style=2)
                face.prism(panel.difference(inset),-.12,-.086,DARK,'basement panel bead')
        face.box(sign*.09,1.17,.047,.18,.064,-.077,BLACK,'lower entry handles')
    face.box(0,h+.079,w+.17,.16,.26,.046,EDGE,'lintel below upper terrace')
    return hole
