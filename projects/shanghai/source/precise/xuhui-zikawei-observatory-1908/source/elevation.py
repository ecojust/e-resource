"""Arched windows, cut brick moldings and the articulated masonry of the 1908 wings."""
import math

import numpy as np
from shapely.geometry import LineString, Polygon, box
from shapely.ops import unary_union

from photo_architecture import Facade
from historic_masonry import MASONRY

RED='Oxide red trim brick'
STONE='Warm grey carved stone'
IVORY='Limestone and limewashed joinery'
GLASS='Smoked window glass'
FRAME='Dark timber casing'
JOINT='Recessed red mortar'
BASE='Basement grey masonry'
ROOF='Dark pitched roof'
DARK='Deep opening shadow'


def arch(x,sill,width,spring,segments):
    radius=width/2
    arc=[(x+radius*math.cos(a),spring+radius*math.sin(a))
         for a in np.linspace(0,math.pi,segments+1)]
    return Polygon([(x-radius,sill),(x+radius,sill),*arc])


def rim(f,x,sill,width,spring,material,label,lod,depth=.105):
    r=width/2; thickness=.21 if width>1.4 else .14
    outer=arch(x,sill,width+2*thickness,spring,16 if lod else 34)
    inner=arch(x,sill-.01,width,spring,16 if lod else 34)
    f.prism(outer.difference(inner),-.032,depth,material,label+' / arch trim')
    if lod:return
    count=13 if width>1.4 else 9
    for k in range(1,count):
        a=math.pi*k/count
        line=LineString([(x+(r-.005)*math.cos(a),spring+(r-.005)*math.sin(a)),
                         (x+(r+thickness)*math.cos(a),spring+(r+thickness)*math.sin(a))])
        f.prism(line.buffer(.011,cap_style='flat'),depth+.001,depth+.012,JOINT,label+' / joints')


def sash(f,shape,x,sill,spring,width,segments,lod,label):
    f.prism(shape.buffer(.013,join_style=2),-.32,-.30,GLASS,label+' / dark glazing')
    center=width/2
    edge=shape.buffer(-.08,join_style=2)
    bars=[box(x-.035,sill,x+.035,spring+center),box(x-center,spring-.035,x+center,spring+.035)]
    if not lod:
        for dx in (-width*.25,width*.25):
            bars.append(box(x+dx-.022,sill,x+dx+.022,spring))
        bars.append(box(x-center,sill+(spring-sill)*.53-.022,
                        x+center,sill+(spring-sill)*.53+.022))
        for angle in (math.pi/4,3*math.pi/4):
            end=(x+center*math.cos(angle),spring+center*math.sin(angle))
            bars.append(LineString([(x,spring),end]).buffer(.020,cap_style='flat'))
    frame=shape.buffer(-.018).difference(edge.difference(unary_union(bars)))
    f.prism(frame,-.245,-.147,IVORY,label+' / casement')
    f.box(x,sill-.08,width+.45,.17,.54,.07,STONE,label+' / sill')


def shutter(f,x,sill,w,h,label,lod):
    f.box(x,sill+h/2,w,h,.085,.09,FRAME,label+' / shutter')
    f.box(x,sill+h/2,w-.13,h-.17,.04,.149,IVORY,label+' / shutter panel')
    count=8 if lod else 18
    for i in range(count):
        z=sill+.15+i*(h-.30)/max(1,count-1)
        f.box(x,z,w-.14,.054 if lod else .032,.07,.175,STONE,label+' / louvres')


def polygon_tablet(f,x,z,w,h,label,lod):
    pts=[(-.5,-.20),(-.39,-.50),(.39,-.50),(.5,-.20),(.5,.20),(.39,.50),(-.39,.50),(-.5,.20)]
    panel=Polygon([(x+a*w,z+b*h)for a,b in pts])
    f.prism(panel,-.02,.127,RED,label+' / tablet ground')
    f.prism(panel.difference(panel.buffer(-.105,join_style=2)),.126,.21,RED,label+' / tablet frame')
    f.prism(panel.buffer(-.133,join_style=2),.129,.143,MASONRY,label+' / recessed tablet face')
    for hand in (-1,1):
        f.box(x+hand*w*.47,z,w*.12,h*.24,.18,.155,RED,label+' / tablet shoulders')


def window_wall(b,a,c,label,eave,bays,lod,show_tablets=True,main_shutters=False):
    f=Facade(b,a,c,label);holes=[];windows=[]
    for i,x in enumerate(bays):
        for floor,(sill,spring,w) in enumerate([(3.43,4.72,1.80),(7.76,9.45,1.80)]):
            shape=arch(x,sill,w,spring,12 if lod else 28)
            holes.append(shape);windows.append((x,sill,w,spring,shape,floor,i))
        bas=arch(x,.35,1.42,1.26,10 if lod else 20)
        holes.append(bas);windows.append((x,.35,1.42,1.26,bas,-1,i))
    f.wall(.04,eave,holes,.38,MASONRY)
    for x,sill,w,spring,shape,floor,i in windows:
        name=['Basement','Lower','Upper'][floor+1]+' opening'
        sash(f,shape,x,sill,spring,w,20,lod,name)
        rim(f,x,sill,w,spring,STONE if floor==-1 else RED,name,lod)
        if main_shutters and floor>=0:
            for h in (-1,1):shutter(f,x+h*(w/2+.65),sill+.06,.73,spring+.22-sill,'Wing window',lod)
        if floor==0 and show_tablets:polygon_tablet(f,x,6.72,w+.59,.87,'Spandrel',lod)
    for z,h,d,m in [(2.40,.19,.12,STONE),(eave-.63,.17,.13,RED),(eave-.12,.22,.23,STONE)]:
        f.beam(z,h,d,m,label='Continuous stringcourse')
    for x in (-f.length/2+.27,f.length/2-.27):
        f.box(x,eave/2,.48,eave,.18,.082,RED,'Quoin strip')
        for i,z in enumerate(np.arange(.35,eave,.52 if lod else .34)):
            f.box(x,z,.69 if i%2 else .48,.165 if z<2.40 and i%2 else .072,.22,.11,
                  STONE if i%2 and z<2.4 else RED,'Bonded corner blocks')
    return f


def hip(b,xl,xr,front,back,eave,ridge,label):
    width=xr-xl;depth=back-front;cx=(xl+xr)/2;cy=(front+back)/2
    x0,x1=xl-.15,xr+.15;y0,y1=front-.18,back+.18
    vertices=[(x0,y0,eave),(x1,y0,eave),(x1,y1,eave),(x0,y1,eave)]
    if width>=depth:
        vertices.extend([(x0+depth/2,cy,ridge),(x1-depth/2,cy,ridge)])
        faces=[(0,1,5,4),(1,2,5),(2,3,4,5),(3,0,4),(3,2,1,0)]
    else:
        vertices.extend([(cx,y0+width/2,ridge),(cx,y1-width/2,ridge)])
        faces=[(0,1,4),(1,2,5,4),(2,3,5),(3,0,4,5),(3,2,1,0)]
    b.add(vertices,faces,ROOF,label+' / roof')
    b.tube([np.asarray(v) for v in vertices[-2:]],.085,STONE,8,label+' / ridge')
