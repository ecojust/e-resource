"""Paired green steel casements with a projecting glazed leaf, putty and latch handles."""
import math
import numpy as np
from shapely.geometry import box
from shapely.ops import unary_union
from photo_architecture import Facade

STEEL='Weathered green steel';BEAD='Pale green glazing bead';EDGE='Dark sash rebate';IRON='Oiled latch metal'
BLUE='Blue inside glazing';BLUE2='Denim blue glazing';BLUE3='Shaded blue glazing';REFL='Street reflection';REFL2='Grey green reflection'
GAP='Shadow behind open casement'
def leaf(builder,a,b,bottom,top,name,swing,lod):
    f=Facade(builder,a,b,name);width=f.length;x0=-width/2;x1=width/2;outer=box(x0,bottom,x1,top)
    rail=.025 if swing else .024;inner=box(x0+rail,bottom+rail,x1-rail,top-rail)
    h=top-bottom;breaks=[bottom+h*float(t)for t in [.25,.50,.75]]
    bars=unary_union([box(x0,z-.011,x1,z+.011)for z in breaks]).intersection(inner)
    f.prism(outer.difference(inner).union(bars),-.015,.025,STEEL,'rolled frame and three transoms')
    keeper=inner.difference(inner.buffer(-.008,join_style=2)).difference(bars)
    f.prism(keeper,-.015,.006,BEAD,'glazing putty')
    for k,(z0,z1)in enumerate(zip([bottom+rail,*[z+.011 for z in breaks]],[*[z-.011 for z in breaks],top-rail])):
        left=x0+rail;right=x1-rail
        if swing:
            f.prism(box(left-.005,z0-.004,right+.005,z1+.004),-.032,-.020,
                    REFL if k in [0,2]else REFL2,'dark reflecting glass')
        else:
            # Flat strips give the blue backing its observed vertical changes in light.
            # Their outer skins form one flat glazed plane.
            widths=[0,.17,.24,.47,.62,.74,.80,1]if not lod else [0,.24,.68,1]
            for j,(aa,bb) in enumerate(zip(widths,widths[1:])):
                xleft=left+(right-left)*aa;xright=left+(right-left)*bb
                f.prism(box(xleft,z0-.002,xright,z1+.002),-.038,-.024,[BLUE,BLUE2,BLUE,BLUE3,BLUE,BLUE3,BLUE][j],
                        'blue glazing behind steel')
        if not lod:
            for y in [z0+.009,z1-.009]:
                f.box(0,y,right-left,.008,.010,-.014,BEAD,'fine horizontal putty')
    # The lower rail projects just beyond the glass, sheltering the hinge and rebate.
    f.box(0,bottom+.025,width-.011,.022,.055,.018,STEEL,'lower weather bar')
    return f

def hinges(builder,face,x,bottom,top,lod):
    h=top-bottom
    for j,z in enumerate([bottom+h*.17,bottom+h*.82]):
        for k in range(3):
            z0=z+(k-1)*.030
            builder.tube([face.point(x,z0-.013,.043),face.point(x,z0+.013,.043)],.013,
                         IRON,6 if lod else 10,label=face.label+'/hinge knuckles')
        face.box(x,z,.053,.105,.023,.030,STEEL,'hinge plate')

def handle(builder,f,x,z,side,lod):
    f.box(x,z,.043,.085,.018,.037,EDGE,'handle plate')
    a=f.point(x,z,.045);b=f.point(x,z,.077);c=f.point(x+side*.068,z-.014,.083)
    builder.tube([a,b,c],.011,IRON,7 if lod else 12,label=f.label+'/turning handle')
    if not lod:
        for dy in [-.028,.028]:
            f.builder.tube([f.point(x,z+dy,.044),f.point(x,z+dy,.05)],.006,BEAD,7,label=f.label+'/handle rivets')

def window(builder,wall,bounds,d,idx,lod):
    a,b,c,e=bounds;name='Open bay' if idx==0 else 'Closed bay';w=c-a
    hole=box(a,b,c,e)
    casing=hole.buffer(-.005,join_style=2).difference(hole.buffer(-.037,join_style=2))
    wall.prism(casing,-.145,-.099,STEEL,name+' fixed perimeter')
    wall.prism(hole.buffer(.018,join_style=2),-.349,-.336,GAP,name+' backing plane')
    # The inward rebate returns behind both leaves, including the open one.
    for x in [a+.027,c-.027]:
        wall.box(x,(b+e)/2,.013,e-b-.046,.12,-.16,EDGE,name+' jamb shadow line')
    sill=b+.035;head=e-.034
    if idx==0:
        hx=d['hinge_origin_x'];hy=d['hinge_y_m'];width=d['swinging_leaf_width']
        angle=math.radians(d['open_angle_degrees'])
        fx=hx+width*math.cos(angle);fy=hy-width*math.sin(angle)
        swing=leaf(builder,(hx,hy),(fx,fy),d['swing_bottom_m'],d['swing_top_m'],name+' leaf 1',True,lod)
        # Continuous framing at the hinge plane links the moving leaf to its masonry jamb.
        swing.box(-width/2+.011,(d['swing_top_m']+d['swing_bottom_m'])/2,.025,
                  d['swing_top_m']-d['swing_bottom_m'],.09,-.010,STEEL,'projecting hinge stile')
        hinges(builder,swing,-width/2+.009,d['swing_bottom_m'],d['swing_top_m'],lod)
        handle(builder,swing,width/2-.043,sill+.53*(head-sill),-1,lod)
        meeting=hx+width+.026
        # A dark blue interior face is seen behind the open light. Its recess stays visible from the side.
        wall.prism(box(a+.035,sill,meeting-.012,head),-.298,-.29,BLUE3,name+' blue inner plane')
        right=leaf(builder,(meeting+.012,.12),(c-.035,.12),sill,head,name+' leaf 2',False,lod)
        handle(builder,right,-right.length/2+.043,sill+.53*(head-sill),1,lod)
        hinges(builder,right,right.length/2-.009,sill,head,lod)
    else:
        meeting=(a+c)/2
        for i,(x0,x1,side) in enumerate([(a+.035,meeting-.008,-1),(meeting+.008,c-.035,1)]):
            f=leaf(builder,(x0,.12),(x1,.12),sill,head,name+' leaf '+str(i+1),False,lod)
            handle(builder,f,-side*(f.length/2-.043),sill+.53*(head-sill),side,lod)
            hinges(builder,f,side*(f.length/2-.009),sill,head,lod)
    wall.box(meeting,(head+sill)/2,.031,head-sill,.093,-.122,STEEL,name+' meeting bar')
