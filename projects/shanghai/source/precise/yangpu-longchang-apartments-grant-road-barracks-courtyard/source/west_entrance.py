"""Street-side entrance of Longchang Apartments, drawn from the 2012 image of no. 362.

The local origin is the centre of the opening on the front wall. X increases to
the right in the photograph, Y into the entrance, and Z up. Dimensions scale
from an estimated clear width. The opening and its local jambs use the same
parameters. Entrances farther into the block lie beyond this component.
"""
from pathlib import Path
from math import cos, radians, sin
import json
import numpy as np
from shapely.geometry import LineString, Polygon, box as rectangle
from shapely.ops import unary_union
from courtyard import C, B, mat

HERE=Path(__file__).absolute().parent
PAINT='362 entrance | sage painted iron'
WEAR='362 entrance | weathered iron'
WASH='362 entrance | pale lower limewash'
RECESS='362 entrance | recessed grey seam'
BOARD='362 entrance | green enamel'
TYPE='362 entrance | pale enamel lettering'
PALETTE={PAINT:mat((113,147,132),.54),WEAR:mat((107,99,88),.76),
         WASH:mat((204,202,190)),RECESS:mat((109,105,96)),BOARD:mat((43,150,127),.43),TYPE:mat((241,239,215),.46)}
BOND='Court | red brick'
AGG='Court | washed aggregate'


def dimensions(layout=None):
    row=layout or {}
    width=float(row.get('gate_clear_width',2.80))
    height=float(row.get('gate_clear_height',3.05))
    if min(width,height)<=0:raise ValueError('The entrance needs a positive opening width and height')
    return width,height


def opening(layout=None):
    width,height=dimensions(layout)
    return dict(a=(-width/2,0.),c=(width/2,0.),low=0.,high=height,outward=(0.,-1.))


def add_entrance(b,lod=False,layout=None):
    width,height=dimensions(layout)
    scale=width/2.80
    for k,v in PALETTE.items():b.palette.setdefault(k,v)
    prefix='362 | '
    def box(center,size,material,label):
        b.box(np.asarray(center)*scale,np.asarray(size)*scale,material,label=prefix+label)
    def face(poly,front,back,material,label):
        b.prism(poly,-back*scale,-front*scale,lambda x,z,d:(x*scale,-d,z*scale),material,prefix+label)
    def tube(points,r,material,label):
        b.tube(np.array(points)*scale,r*scale,material,6 if lod else 12,prefix+label)

    # The front photograph shows a broad textured jamb, a thin edging beside
    # the opening and a lighter painted base. The top is above the image.
    top=height/scale
    for side in (-1,1):
        name='left' if side<0 else 'right'
        foot=.87 if side<0 else .79
        outer=1.61 if side<0 else 1.570
        inner=1.4
        for lo,hi,material in [(0.,foot,WASH),(foot,top,AGG)]:
            box((side*(outer+inner)/2.,.032,(lo+hi)/2.),(outer-inner,.084,hi-lo),material,name+' stone jamb')
        for edge,centre,thickness in [('inner bevel',1.418,.036),('outer bead',outer-.012,.024)]:
            for lo,hi,finish in [(0.,foot,WASH),(foot,top,AGG)]:
                box((side*centre,-.025,(lo+hi)/2),(thickness,.044,hi-lo),finish,name+' '+edge)
        # Thin returns line the jamb. A clear open section runs between them.
        box((side*1.43,.235,top/2),(.060,.36,top),BOND,name+' inner brick return')
    # The right moulding alone shows these diagonal cuts above its white base.
    for i in range(9):
        z=.91+i*.248
        if z+.074<top:
            slant=LineString([(1.456,z+.07),(1.548,z)]).buffer(.004,cap_style=2)
            face(slant,-.019,-.009,RECESS,'right diagonal face joint %02d'%(i+1))
    box((0,.185,top+.035),(2.92,.37,.07),C,'upper reveal at estimated clear height')

    reg=json.loads((HERE.parent/'measurements/west-entrance-photo-fit.json').read_text())
    for side,leaf in [(-1,'left'),(1,'right')]:
        angle=radians(reg['opened_leaf_angles_from_closed_degrees'][leaf])
        start=side*1.35
        def point(t,z):
            return (start-side*1.35*t*cos(angle),.10+1.35*t*sin(angle),z)
        bottom=reg['foot_z_m'];middle=reg['middle_rail_z_m'];head=reg['head_z_m']
        def bar(t,z1,s,z2,r,material,title):
            tube((point(t,z1),point(s,z2)),r,material,leaf+' '+title)
        for name,t in [('front stile',0.),('outer stile',1.)]:
            bar(t,bottom,t,head,.021,PAINT,name)
        bar(0.,bottom,1.,bottom,.016,PAINT,'lower rail')
        bar(0.,head,1.,head,.022,PAINT,'rounded upper rail')
        bar(0.,middle,1. if side>0 else .5,middle,.014,PAINT,'intermediate rail')
        if side<0:
            bar(.5,bottom,.5,head,.021,PAINT,'central upright')
            bar(0.,1.755,1.,1.755,.014,PAINT,'upper rectangular division')
        for i in range(1,9):
            t=i/9
            if side<0 and abs(t-.5)<.05:continue
            x,y,_=point(t,head)
            finial=head+reg['finial_above_head_m']
            bar(t,bottom,t,finial-.055,.0085,WEAR if i%3==0 else PAINT,'vertical %02d'%i)
            # Each narrow tip is a closed, tapered solid above the upper rail.
            b.lathe((x*scale,y*scale),[(scale*(finial-.056),scale*.0085),(scale*finial,scale*.001)],PAINT,5 if lod else 8,prefix+leaf+' tapered end %02d'%i)
        for z in ((.43,2.04) if side<0 else (.40,2.11)):
            # Only the exterior shapes of the worn collars and mounting tabs
            # are legible in the photograph.
            x,y,_=point(0,z)
            box((side*1.379,.101,z),(.100,.083,.024),WEAR,leaf+' exterior strap')
            tube([(x,y,z-.031),(x,y,z+.031)],.032,WEAR,leaf+' exterior collar')

    _enamel_plate(face,reg)


def _enamel_plate(face,reg):
    observed=np.array(reg['plaque_corners_xyz_m'])
    x0,z0=observed[:,[0,2]].min(axis=0);x1,z1=observed[:,[0,2]].max(axis=0)
    w=x1-x0;h=z1-z0
    surround=rectangle(x0+.009,z0+.009,x1-.009,z1-.009).buffer(.009,resolution=3)
    face(surround,-.019,-.004,TYPE,'enamel plaque light lip')
    shape=rectangle(x0+.011,z0+.011,x1-.011,z1-.011).buffer(.007,resolution=3)
    face(shape,-.022,-.019,BOARD,'enamel plaque field')
    # Numerals follow the rounded, condensed strokes in the photographed sign.
    numerals={
     '3':[[(.10,.89),(.31,.98),(.63,.98),(.87,.83),(.88,.68),(.72,.55),(.44,.50),(.70,.48),(.9,.34),(.91,.19),(.77,.07),(.48,.02),(.20,.08),(.08,.18)]],
     '6':[[(.82,.92),(.59,.98),(.35,.9),(.16,.69),(.12,.37),(.18,.15),(.37,.03),(.66,.03),(.84,.16),(.85,.36),(.69,.49),(.40,.49),(.17,.33)]],
     '2':[[(.12,.78),(.25,.94),(.51,.99),(.76,.94),(.88,.79),(.83,.61),(.62,.45),(.39,.26),(.15,.07),(.15,.04),(.88,.04)]]}
    for i,glyph in enumerate('362'):
        dx=x0+w*(.16+i*.246);dy=z0+h*.37
        paths=numerals[glyph]
        p=unary_union([LineString([(dx+a*w*.16,dy+b*h*.49)for a,b in stroke]).buffer(h*.031,resolution=3)for stroke in paths])
        face(p,-.024,-.022,TYPE,'number '+glyph)
    # The small second line reads 隆昌路. These short strokes are author-drawn.
    captions=[
      [[(1,1),(1,9)],[(1,9),(3.5,9),(2.4,6),(3.5,4.7),(3,3.8)],[(4,7),(6.6,9),(8,8.3),(5,6.3)],[(4.9,8.4),(8.8,6.1)],[(4,5.6),(8.9,5.6)],[(4.2,3.7),(8.6,3.7)],[(4.6,2.4),(8.5,2.4)],[(3.8,1),(9.3,1)],[(6.6,5),(6.6,1)]],
      [[(2.6,9),(7.7,9),(7.7,5.5),(2.6,5.5),(2.6,9)],[(2.7,7.3),(7.6,7.3)],[(1.7,4.3),(8.6,4.3),(8.6,1),(1.7,1),(1.7,4.3)],[(1.8,2.7),(8.6,2.7)]],
      [[(1,9),(4,9),(4,6.3),(1,6.3),(1,9)],[(2.8,6.2),(2.8,2.1)],[(2.9,4.5),(4.4,4.5)],[(1.1,5.1),(1.1,1.9),(4.2,2.8)],[(5,7.4),(6.4,9.3),(8.8,8.5),(6.8,6),(4.8,4.8)],[(5.4,8),(8.9,4.8)],[(5,4),(8.7,4),(8.7,1),(5,1),(5,4)]]]
    for i,strokes in enumerate(captions):
        dx=x0+w*(.20+i*.214);dy=z0+h*.101
        glyph=unary_union([LineString([(dx+a*w*.012,dy+b*h*.016)for a,b in line]).buffer(h*.0075,resolution=2)for line in strokes])
        face(glyph,-.023,-.022,TYPE,'street name character %d'%(i+1))
