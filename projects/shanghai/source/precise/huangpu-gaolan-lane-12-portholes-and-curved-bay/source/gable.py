"""Two stacked round windows beside a curved street bay on Gaolan Road."""
from pathlib import Path
from math import radians,cos,sin
import numpy as np
from shapely.geometry import Polygon,Point,box
from shapely.ops import unary_union
from profile_tools import BRICK as RENDER,cb,slab,bricks_uv
RED='Russet facing brick';JOINT='Recessed brick joints';RIM='Light porthole rim'
DARK='Dark steel sash';GLASS='Steel window glazing';PALE='Lower pale sash';LOW_GLASS='Lower street glazing';SILL='Weathered sill lip';ROUND='Shaded round glazing'
PALETTE={}
for key,rgb in [(RENDER,(255,255,255)),(RED,(104,68,57)),(JOINT,(103,94,81)),(RIM,(166,168,155)),(DARK,(60,65,60)),(GLASS,(76,87,89)),(PALE,(187,188,175)),(LOW_GLASS,(72,84,85)),(SILL,(133,129,111)),(ROUND,(64,74,68))]:
    PALETTE[key]=dict(color=[(v/255)**2.2 for v in rgb],roughness=.86)
PALETTE[RENDER]['texture']=str(Path(__file__).with_name('finish.png'))
CX=.58;CY=1.22;RADIUS=1.65;ANGLES=[-52,-30,-4,21,45]
PORT=-1.43;BACK=.245
OPENINGS=[(.34,1.9),(3.21,4.78)]
def xy(angle,r):
    a=radians(angle)
    return CX+r*sin(a),CY-r*cos(a)
def chord(b,a,c,r0,r1,low,high,mat,name):
    points=[xy(a,r0),xy(c,r0),xy(c,r1),xy(a,r1)]
    b.prism(Polygon(points),low,high,lambda x,y,z:(x,y,z),mat,label=name)
def band(b,a,c,inner,outer,lo,hi,mat,label,segments):
    stops=np.linspace(a,c,segments+1)
    for start,end in zip(stops,stops[1:]):chord(b,start,end,inner,outer,lo,hi,mat,label)
def disk(z,radius,n):
    return Point(PORT,z).buffer(radius,quad_segs=n)
def model(b,lod=False):
    n=9 if lod else 18
    divisions=11 if lod else 26
    left=xy(ANGLES[0],RADIUS)[0]
    # The end of each brick panel follows the left edge of the rounded bay.
    for index,(low,high) in enumerate(OPENINGS):
        h=(low+high)/2;inner=.51;outer=.602
        hole=disk(h,outer,n)
        field=box(-2.23,low,left+.055,high).difference(hole)
        slab(b,field,BACK,BACK+.30,JOINT,'Mortar backing behind round window')
        pitch=.089;length=.331
        for row in range(18):
            z=low+row*pitch
            for column in range(7):
                x=-2.60+length*column+length*(row%2)/2
                area=box(x,z,x+length-.011,min(high+.001,z+pitch-.009)).intersection(field)
                if not area.is_empty:slab(b,area,BACK-.012,BACK,RED,'Porthole brick course')
        slab(b,disk(h,outer,n).difference(disk(h,inner+.018,n)),BACK-.086,BACK+.09,RIM,'Raised porthole surround')
        slab(b,disk(h,inner+.019,n).difference(disk(h,inner-.014,n)),BACK+.06,BACK+.11,DARK,'Round sash rebate')
        slab(b,disk(h,inner,n),BACK+.146,BACK+.20,ROUND,'Recessed circular pane')
        if index==0:
            for dh in [-.12,.005]:
                shape=box(PORT-.56,h+dh-.012,PORT+.56,h+dh+.012).intersection(disk(h,inner,n))
                slab(b,shape,BACK+.09,BACK+.128,DARK,'Lower circular window crossbar')
        sash=PALE if index==0 else DARK
        glass=LOW_GLASS if index==0 else GLASS
        rails=[low+.052,high-.46,high-.048] if index==0 else [low+.044,low+.39,low+.71,low+1.04,low+1.34,high-.045]
        for a,c in zip(ANGLES,ANGLES[1:]):
            chord(b,a,c,RADIUS-.116,RADIUS-.092,low,high,glass,'Flat panes on the curved bay')
            for z in rails:chord(b,a,c,RADIUS-.045,RADIUS-.007,z-.019,z+.019,sash,'Horizontal window rail')
        for a in ANGLES:
            band(b,a-1.03,a+1.03,RADIUS-.094,RADIUS+.003,low,high,sash,'Vertical segment frame',1)
        band(b,ANGLES[0]-1,ANGLES[-1]+1,RADIUS-.22,RADIUS+.079,low-.048,low+.02,SILL,'Projecting curved sill',divisions)
    for lo,hi in [(0,.34),(1.9,3.21),(4.78,5.67)]:
        slab(b,box(-2.23,lo,left+.05,hi),BACK-.08,BACK+.34,RENDER,'Pebble-dash band over round windows')
        band(b,ANGLES[0]-1.4,ANGLES[-1]+1.4,RADIUS-.29,RADIUS+.053,lo,hi,RENDER,'Continuous curved pebble-dash spandrel',divisions)
    bricks_uv(b)
