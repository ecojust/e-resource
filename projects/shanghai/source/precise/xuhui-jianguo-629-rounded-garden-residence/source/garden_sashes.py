"""Steel casements and recessed plate-glass lights from the garden photograph."""
from shapely.geometry import box
from shapely.ops import unary_union
from materials import DARK,FRAME,GLASS,MID_GLASS,SILL,TRIM
def insert_sash(face,opening,label,divisions,transoms,light=GLASS,outer_rebate=.09):
    x0,z0,x1,z1=opening.bounds
    rebate=opening.buffer(-.045,join_style=2)
    face.solid(opening.difference(rebate),-.185,-.004,DARK,label+' | outer reveal')
    face.solid(rebate,-.197,-.183,light,label+' | recessed pane')
    frame=rebate.difference(rebate.buffer(-.037,join_style=2));glass_area=rebate.buffer(-.025,join_style=2)
    bars=[frame]
    for fraction in divisions:
        x=x0+(x1-x0)*fraction
        bars.append(box(x-.016,z0,x+.016,z1).intersection(glass_area))
    for fraction in transoms:
        z=z0+(z1-z0)*fraction
        bars.append(box(x0,z-.018,x1,z+.018).intersection(glass_area))
    face.solid(unary_union(bars),-.182,-.137,FRAME,label+' | steel stiles and rails')
    if outer_rebate:
        face.solid(opening.buffer(outer_rebate,join_style=2).difference(opening),.001,.043,TRIM,label+' | mineral trim')
        face.rect(x0-outer_rebate,x1+outer_rebate,z0-.077,z0-.018,.001,.092,SILL,label+' | sill')

def open_casements(face,opening,label,angles):
    """Fixed top and bottom lights flank two opening steel leaves in the 2019 published photograph."""
    from math import cos,radians,sin
    x0,z0,x1,z1=opening.bounds
    z_low=z0+(z1-z0)*.23
    z_high=z0+(z1-z0)*.78
    clear=opening.buffer(-.032,join_style=2)
    face.solid(opening.difference(clear),-.175,-.005,DARK,label+' | outer rebate')
    face.solid(clear,-.362,-.340,DARK,label+' | shadow behind the open lights')
    frame=clear.difference(clear.buffer(-.032,join_style=2))
    fixed=clear.intersection(unary_union([box(x0,z0,x1,z_low),box(x0,z_high,x1,z1)]))
    face.solid(fixed,-.186,-.168,MID_GLASS,label+' | fixed top and bottom lights')
    for z in [z_low,z_high]:
        frame=frame.union(box(x0,z-.027,x1,z+.027).intersection(clear))
    face.solid(frame,-.155,-.115,FRAME,label+' | fixed sash rails')
    lo=x0+.058;hi=x1-.058;length=(hi-lo)/2-.005
    for n,angle in enumerate(angles):
        a=radians(angle)
        if n==0:
            leaf=face.face(lo,.134,cos(a),-sin(a))
        else:
            leaf=face.face(hi-length*cos(a),.134-length*sin(a),cos(a),sin(a))
        outline=box(0,z_low+.023,length,z_high-.024)
        pane=outline.buffer(-.027,join_style=2)
        leaf.solid(outline.difference(pane),-.017,.017,FRAME,label+' | opening steel leaf')
        leaf.solid(pane,-.010,.002,GLASS,label+' | glass in opening leaf')
