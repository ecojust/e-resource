"""The continuous west wall from the street corner through the V-panel beside the second pediment."""
from math import cos,pi,sin
from pathlib import Path
import json

import numpy as np
from shapely.geometry import LineString,Polygon,box
from shapely.ops import unary_union

WALL='scored pale render'
TRIM='off-white cast moulding'
IRON='painted metal joinery'
GLASS='cool recessed glass'
DARK='charcoal metal apron'
STONE='grey plinth and shadow mould'
HERE=Path(__file__).absolute().parent

def add(b,lod):
    # u increases down the lane. Using -u as the extrusion coordinate keeps the
    # outward orientation for a wall that faces the lane on the left.
    station=json.loads((HERE/'side-window-axes.json').read_bytes())
    bays=station['axes_metres'];end=station['observed_end_m']
    skew=station['west_shift_per_m']
    def map_side(u,z,d):return (-.322+skew*(-u)-d,-u,z)
    def layer(shape,out0,out1,mat,name):
        b.prism(shape,out0,out1,map_side,mat,'west facade/'+name)
    def rectangle(a,b,z0,z1):
        return box(-b,z0,-a,z1)
    def panel(span,base,top,inner,outer,mat,name):
        layer(rectangle(*span,base,top),inner,outer,mat,name)
    def trimline(uz,size,lo,hi,mat,name):
        shape=LineString([(-u,z)for u,z in uz]).buffer(size/2,cap_style='flat',join_style='mitre')
        layer(shape,lo,hi,mat,name)
    op={}
    for key,axis in bays.items():
        mid=key=='central';w=.53 if key=='corner-light' else (2.10 if mid else 1.48)
        if key=='V-panel':w=1.13
        for floor,(z0,z1) in enumerate([(5.02,7.27 if mid else 6.88),(8.73 if mid else 9.35,11.04)]):
            op[(key,floor)]=rectangle(axis-w/2,axis+w/2,z0,z1)
    # The 2021 lane-mouth oblique exposes the lower windows of the first three
    # wide axes. Street furniture occludes the lower facade farther up the lane.
    for k in ['square-1','square-2','square-3']:
        u=bays[k];op[(k,-1)]=rectangle(u-.71,u+.71,1.07,3.00)
    wall=rectangle(.032,end,.14,12.42).difference(unary_union(list(op.values())))
    layer(wall,-.41,-.010,WALL,'wall with recessed lights')
    for idx,z in enumerate(np.arange(.44,12.31,.354)):
        layer(wall.intersection(rectangle(.03,end,z,z+.011)),-.009,.002,STONE,f'bed joint {idx+1:02}')
    for (bay,floor),opening in op.items():
        key=f'{bay} level {floor+2}';l,z0,r,z1=opening.bounds;h=z1-z0;w=r-l
        layer(opening.buffer(.083,join_style='mitre').difference(opening),-.095,.103,TRIM,key+'/plaster surround')
        layer(opening.difference(opening.buffer(-.047,join_style='mitre')),-.199,-.104,IRON,key+'/dark frame')
        left=l+.048;right=r-.048;bottom=z0+.05;top=z1-.05
        fractions=([0,1]if bay=='corner-light' else ([0,.29,.71,1]if bay=='central'else[0,.33,.66,1]))
        horizontal=[0,.235,.77,1]
        for j,t in enumerate(fractions[1:-1]):
            x=left+t*(right-left);layer(box(x-.021,bottom,x+.021,top),-.155,-.106,IRON,key+f'/mullion {j+1}')
        for j,t in enumerate(horizontal[1:-1]):
            z=bottom+t*(top-bottom);layer(box(left,z-.019,right,z+.019),-.176,-.131,IRON,key+f'/transom {j+1}')
        for i,(a,c) in enumerate(zip(fractions,fractions[1:])):
            for j,(t,v)in enumerate(zip(horizontal,horizontal[1:])):
                if bay=='central' and i==0 and not lod:continue
                gl=box(left+(right-left)*a+.022,bottom+(top-bottom)*t+.019,left+(right-left)*c-.022,bottom+(top-bottom)*v-.019)
                layer(gl,-.208,-.192,GLASS,key+f'/glass {i+1}-{j+1}')
        if bay=='central' and not lod:
            # On the press close-up the right-hand light of each central casement
            # is open. An actual hinged leaf projects out of the wall plane.
            hinge=left+.29*(right-left);length=.29*(right-left)-.034
            leaf=box(-length,bottom,0,top)
            def tilted(x,z,d):
                u=hinge+cos(.62)*x-sin(.62)*d
                normal=-.128-sin(.62)*x-cos(.62)*(-d)
                return map_side(u,z,normal)
            b.prism(leaf.difference(leaf.buffer(-.036,join_style='mitre')),-.029,.004,tilted,IRON,'west facade/'+key+'/open casement')
            b.prism(leaf.buffer(-.038,join_style='mitre'),-.028,-.010,tilted,GLASS,'west facade/'+key+'/open glazing')
        layer(box(l-.13,z0-.126,r+.13,z0-.040),-.084,.168,TRIM,key+'/sill')
        layer(box(l-.102,z1+.05,r+.102,z1+.142),-.080,.136,TRIM,key+'/hood')
    for key,u in bays.items():
        if key=='corner-light':continue
        if key=='central':
            panel([u-1.08,u+1.08],7.34,8.70,-.01,.086,DARK,'central window/metal spandrel')
            continue
        width=1.63 if key!='V-panel' else 1.30
        panel([u-width/2,u+width/2],7.12,9.16,-.014,.030,WALL,key+'/recessed spandrel field')
        for row in range(2):
            z=7.55+row*.81
            if key=='V-panel':
                trimline([(u-.46,z+.092),(u,z-.116),(u+.46,z+.092)],.068,.034,.119,TRIM,key+f'/V mould {row+1}')
            else:
                n=3 if key in ('square-2','square-3','square-4') else 2
                for i in range(n):
                    uc=u+width*((i+.5)/n-.5)*.87
                    shp=rectangle(uc-width*.34/n,uc+width*.34/n,z-.195,z+.19)
                    layer(shp.difference(shp.buffer(-.052,join_style='mitre')),.031,.116,TRIM,key+f'/coffer {row+1}-{i+1}')
        panel([u-width*.56,u+width*.56],7.021,7.138,-.015,.164,TRIM,key+'/lower spandrel course')
    for j,z in enumerate([4.20,4.36,12.07,12.26,12.43,12.60]):
        y=bays['central']
        periods=[(.025,end)] if j<3 else [(.025,y-2.22),(y+2.22,end)]
        for i,span in enumerate(periods):panel(span,z,z+.103,-.012,.18+j*.026,TRIM,f'long cornice {j+1}-{i+1}')
    center=bays['central'];base=12.55;peak=13.22
    shp=Polygon([(-center+2.22,12.18),(-center+2.22,base),(-center,peak),(-center-2.22,base),(-center-2.22,12.18)])
    layer(shp,-.38,.208,WALL,'lane pediment/triangular infill')
    for j,(off,w)in enumerate([(0,.158),(.093,.066),(-.095,.061)]):
        trimline([(center-2.24,base+off),(center,peak+off),(center+2.24,base+off)],w,-.25,.303+j*.015,TRIM,f'lane pediment/raking course {j+1}')
    return b
