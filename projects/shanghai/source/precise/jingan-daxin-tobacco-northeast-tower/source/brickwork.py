"""Pressed brick, arched lintels and recessed joinery of the east tower of Guandu Lu."""
from math import cos,pi,sin
from shapely.geometry import Polygon,box
from shapely.ops import unary_union

BRICK='Guandu pressed red brick'
END='End wall red brick'
TRIM='Dark red molded brick'
PALE='Weathered coping stone'
CLAY='Burnt orange arch brick'
CLOVE='Deep kiln flash'
FRAME='Dark varnished window joinery'
GLASS='Grey blue courtyard glazing'
DIM='Sage reflection in window glass'
CURTAIN='Linen behind middle sash'
METAL='Painted window metal'
IRON='Cast iron and rainwater fittings'
SHADE='Stone-grey equipment case'
YARD='Warm grey yard plinth'


def segmental_head(face, shape, rise, lod, name):
    left,bottom,right,top=shape.bounds
    centre=(left+right)/2;radius=(right-left)/2;spring=top-rise
    count=9 if lod else 19
    for i in range(count):
        start=pi*(i+.022)/count;end=pi*(i+.978)/count
        def point(angle,extra):return (centre+(radius+extra)*cos(angle),spring+(rise+extra)*sin(angle))
        piece=Polygon([point(start,.027),point(start,.185),point(end,.185),point(end,.027)])
        face.prism(piece,.003,.074,[CLAY,TRIM,CLAY,CLOVE,CLAY][i%5],name+' radial arch bricks')


def window(face,shape,rise,splits,rows,lod,name):
    left,bottom,right,top=shape.bounds
    width=right-left;height=top-bottom;mid=(left+right)/2
    inside=shape.buffer(-.055,join_style=2);assert not inside.is_empty
    bars=[]
    for frac in splits:
        x=left+frac*width;bars.append(box(x-.030,bottom-.1,x+.030,top+.1))
    for frac in rows:
        z=bottom+height*frac;bars.append(box(left-.1,z-.033,right+.1,z+.033))
    panes=inside.difference(unary_union(bars))
    if rise>.015:
        segmental_head(face,shape,rise,lod,name)
    face.prism(shape.difference(panes),-.240,-.140,FRAME,name+' sash and transoms')
    for pane in (panes.geoms if hasattr(panes,'geoms') else [panes]):
        bounds=pane.bounds;cx,cz=pane.centroid.coords[0]
        panel=GLASS if cz<bottom+.73*height else DIM
        if splits and cx>mid+.16*width and cz<bottom+.68*height:
            panel=DIM
        face.prism(pane.buffer(.012,join_style=2).intersection(inside),-.292,-.255,panel,name+' recessed glass')
        if name=='middle segmental sash' and bottom+.27*height<cz<bottom+.75*height:
            pane_left,pane_right=bounds[0],bounds[2];edge=pane_left+(pane_right-pane_left)*.31
            shade=pane.intersection(box(pane_left,bounds[1],edge,bounds[3]))
            if not shade.is_empty:
                face.prism(shade,-.251,-.243,CURTAIN,'visible linen behind middle sash')
                for index in range(1,3 if lod else 6):
                    fold=pane_left+index*(edge-pane_left)/(3 if lod else 6)
                    shape=pane.intersection(box(fold-.008,bounds[1],fold+.008,bounds[3]))
                    if shape.area>.003:face.prism(shape,-.242,-.237,DIM,'fine vertical curtain folds')
    face.box(mid,bottom-.045,width+.22,.10,.35,.004,PALE,name+' stone sill')
    for side in (left-.062,right+.062):
        face.box(side,(bottom+top-rise)/2,.093,height-rise,.14,-.002,TRIM,name+' brick jambs')


def grating(face,u,z,width,height,lod,label):
    for side in [u-width/2,u+width/2]:face.box(side,z,.035,height,.04,.092,IRON,label+' frame')
    for zz in [z-height/2,z+height/2]:face.box(u,zz,width,.035,.04,.092,IRON,label+' frame')
    for zz in (-.30,0.,.30):face.box(u,z+height*zz,width,.021,.032,.103,IRON,label+' crossbars')
    count=5 if lod else 9
    for j in range(1,count):face.box(u+width*(j/count-.5),z,.023,height,.028,.095,IRON,label+' thin bars')


def fan_case(face,u,z,lod):
    from shapely.geometry import Point
    label='courtyard condenser';width=.81;height=.54
    disk=Point(u-.095,z).buffer(.201,quad_segs=6 if lod else 12)
    shell=box(u-width/2,z-height/2,u+width/2,z+height/2)
    face.prism(shell.difference(disk),.08,.36,SHADE,label+' case')
    face.prism(disk,.13,.205,IRON,label+' dark fan well')
    for i in range(5):
        phi=2*pi*i/5;tip=(u-.095+.181*cos(phi+.26),z+.181*sin(phi+.26));root=(u-.095+.04*cos(phi),z+.04*sin(phi));aft=(u-.095+.158*cos(phi+.88),z+.158*sin(phi+.88))
        face.prism(Polygon([root,tip,aft]),.222,.242,METAL,label+' fan blades')
    for i in range(3 if lod else 7):
        x=u+.16+i*(.17/(2 if lod else 6));face.box(x,z,.011,.34,.026,.375,TRIM,label+' side vents')
    for offset in (-.26,.26):face.box(u+offset,z-.31,.045,.06,.38,.14,IRON,label+' wall brackets')
