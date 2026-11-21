"""Timber casements, single panes, putty and removable black balcony rails."""
import math
import numpy as np
from shapely.geometry import box

WOOD='Red painted wood'
EDGE='Warm glazing bead'
BLUE='Blue green glass'
GREY='Smoky old glass'
IRON='Black balcony iron'
CREAM='Warm sill paint'
SHADOW='Deep reveal'


def casing(face,x,z,width,height,thickness,back,front,mat,label):
    outer=box(x-width/2,z,x+width/2,z+height)
    clear=box(x-width/2+thickness,z+thickness,x+width/2-thickness,z+height-thickness)
    face.prism(outer.difference(clear),back,front,mat,label)


def glazing(face,x,z,width,height,columns,rows,depth,lod,label,light_glass=False):
    """Cut the rails and stiles as one planar frame, with individual inset lights."""
    stile=.036 if width>.50 else .022
    sash=box(x-width/2,z,x+width/2,z+height)
    rail=.022 if width>.48 else .015
    openings=[]
    for i in range(columns):
        for j in range(rows):
            xl,xr=x-width/2+stile+i*(width-2*stile)/columns,x-width/2+stile+(i+1)*(width-2*stile)/columns
            zl,zr=z+stile+j*(height-2*stile)/rows,z+stile+(j+1)*(height-2*stile)/rows
            leaf=box(xl+(rail/2 if i else 0),zl+(rail/2 if j else 0),
                     xr-(rail/2 if i<columns-1 else 0),zr-(rail/2 if j<rows-1 else 0))
            openings.append(leaf)
            face.prism(leaf,depth-.060,depth-.055,BLUE if light_glass else GREY,label+'/glass')
            if not lod:
                inner=leaf.buffer(-.007,join_style=2)
                face.prism(leaf.difference(inner),depth-.052,depth-.043,EDGE,label+'/putty')
    from shapely.ops import unary_union
    face.prism(sash.difference(unary_union(openings)),depth-.067,depth,WOOD,label+'/rebated frame')


def upper_frames(face,d,lod):
    width=d['upper_width'];base=d['upper_sill'];height=d['upper_height'];case=.06
    casing(face,width/2,base,width,height,case,-.085,-.020,WOOD,'Upper/four-sash case')
    shares=(.260,.244,.231,.265);edge=case
    for i,ratio in enumerate(shares):
        leaf=(width-2*case)*ratio
        x=edge+leaf/2;edge+=leaf
        cols=[4,3,2,4][i];top_rows=[5,4,4,5][i]
        mid=base+.76
        glazing(face,x,base+case,leaf-.012,mid-base-case,cols,3,-.071,lod,'Upper '+str(i+1)+'/lower',light_glass=i in (1,2))
        glazing(face,x,mid+.045,leaf-.012,base+height-case-mid-.045,cols,top_rows,-.071,lod,'Upper '+str(i+1)+'/upper',light_glass=i in (1,2))
        face.box(x,mid+.020,leaf-.005,.048,.066,-.057,WOOD,'Upper '+str(i+1)+'/cross rail')


def lower_frames(face,d,lod,index):
    width=face.length-.28;height=d['ground_window_top']-d['ground_sill'];base=d['ground_sill']
    casing(face,0,base,width,height,.047,-.095,-.027,WOOD,'Ground/combined surround')
    clear=width-.103;bottom_head=base+height*.685
    for j,side in enumerate([-1,1]):
        x=side*clear/4
        glazing(face,x,base+.05,clear/2-.009,bottom_head-base-.059,2,6,-.078,lod,'Ground '+str(index)+'/tall leaf '+str(j+1))
        glazing(face,x,bottom_head+.223,clear/2-.009,base+height-.049-bottom_head-.223,2,1,-.078,lod,'Ground '+str(index)+'/transom '+str(j+1))
    face.box(0,bottom_head+.105,width+.016,.20,.18,-.048,CREAM,'Ground/solid transom rail')
    face.box(0,base-.036,width+.10,.066,.19,.053,CREAM,'Ground/sloping sill')


def railing(builder,d,lod):
    xs=np.linspace(d['rail_left'],d['rail_right'],24)
    def depth(x):
        u=(x-xs[0])/(xs[-1]-xs[0])
        return -.39-.29*(1-(2*u-1)**2)
    z=d['rail_base'];sides=5 if lod else 9
    for h,r in [(.08,.017),(.62,.016),(.95,.029)]:
        pts=[(float(x),depth(x),z+h)for x in xs]
        builder.tube(pts,r,IRON,sides,'Balcony/long curved horizontal')
        for x in (xs[0],xs[-1]):
            builder.tube([(x,depth(x),z+h),(x,-.010,z+h)],r,IRON,sides,'Balcony/return horizontal')
    for i,x in enumerate(np.linspace(xs[0],xs[-1],22)):
        y=depth(x);builder.tube([(x,y,z+.015),(x,y,z+.948)],.018 if i in (0,7,14,21) else .012,IRON,sides,'Balcony/iron uprights')
    for x in (xs[0],xs[-1]):
        for y in np.linspace(depth(x),0,5)[1:-1]:
            builder.tube([(x,y,z+.018),(x,y,z+.946)],.012,IRON,sides,'Balcony/return pickets')
