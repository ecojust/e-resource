"""The two distinct types of openwork in the campus archive, and bounded end returns."""
import math
import numpy as np
from shapely.geometry import Polygon,box as rect
from shapely.ops import unary_union

def pierced_parapet(b,book,z_floor,z_top,x1,wall,box,grey,red,lod):
    axes=book['parapet_post_axes_x_m']
    for i,(a,c) in enumerate(zip(axes,axes[1:])):
        l=a+.42;r=c-.42;cy=z_floor+.36
        # Five round heads connected by a thin central open slot.
        top=[];bottom=[]
        for x in np.linspace(l+.08,r-.08,46 if lod else 101):
            t=(x-l-.08)/(r-l-.16)*5.
            dist=abs(t-math.floor(t)-.5)
            head=max(0.,1.-(dist/.307)**2)**.5
            tail=max(0.,1.-(dist/.20)**2)**.5
            top.append((x,cy+.077+.31*head))
            bottom.append((x,cy-.048-.207*tail))
        fen=Polygon(top+bottom[::-1]);panel=rect(a,z_floor-.01,c,z_top-.055).difference(fen)
        wall(b,panel,-.145,.20,grey,'low wing / linked cinquefoil apertures '+str(i+1))
    for i,x in enumerate(axes):
        lo=x-.44;hi=(x1 if i==len(axes)-1 else x+.44)
        if i==0:lo=book['part_span_m'][0]
        box(b,lo,hi,-.204,.23,z_floor-.02,z_top+.045,red,'low wing / solid panel divider '+str(i+1))
        box(b,lo-.035,hi+.035,-.25,.26,z_top+.045,z_top+.125,red,'low wing / projecting divider cap '+str(i+1))
    box(b,book['part_span_m'][0],x1,-.18,.25,z_top-.070,z_top+.022,red,'low wing / continuous top weathering')

def white_panel(b,cx,z,span,k,lod,wall,mat,book):
    width=span+.14;height=book['visible_panel_height_m'];surface=rect(cx-width/2,z,cx+width/2,z+height)
    period=book['period_in_alternating_rows_m']
    holes=[]
    for i in range(5):
        for j in range(-6,7):
            x=cx+(j+.5*(i%2))*period;v=z+.095+i*.125
            if abs(x-cx)+.073>width/2-.05:continue
            holes.append(Polygon([(x-.073,v),(x,v-.050),(x+.073,v),(x,v+.050)]))
    wall(b,surface.difference(unary_union(holes)),.052,.166,mat,k+' / five rows of pierced diagonal guard')
