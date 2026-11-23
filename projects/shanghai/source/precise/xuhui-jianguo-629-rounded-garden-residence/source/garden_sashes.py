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
