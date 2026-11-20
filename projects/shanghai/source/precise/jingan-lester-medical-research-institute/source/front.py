"""Granite window piers, continuous steel window strips and the restored entrance lamps."""
import math
import numpy as np
from shapely.geometry import Polygon,box
from shapely.ops import unary_union
from photo_architecture import Facade,opening

STONE='buff granite'
BASE='grey granite foundation'
JOINT='sand coloured bed joints'
RED='polished rose granite'
GLASS='slate steel glazing'
STEEL='dark steel joinery'
PANEL='embossed charcoal spandrels'
COPPER='patinated copper'
GOLD='bronze rim'
LAMP='laminated lamp glass'
DOOR='green bronze door'
FLAT='parapet gravel'
PALETTE={STONE:(.664,.576,.468),BASE:(.476,.449,.397),JOINT:(.502,.431,.360),RED:(.402,.223,.170),GLASS:(.170,.225,.258),STEEL:(.084,.094,.092),PANEL:(.115,.124,.128),COPPER:(.367,.217,.134),GOLD:(.572,.363,.185),LAMP:(.788,.741,.557),DOOR:(.195,.236,.202),FLAT:(.518,.514,.477)}
PALETTE={k:{'color':list(v),'roughness':.31 if k in (RED,GLASS,COPPER,GOLD) else .80}for k,v in PALETTE.items()}


def steel_window(f,x,z,w,h,lod,arch=0,cols=3):
    aperture=opening(x,z,w,h,arch,12 if lod else 22)
    f.prism(aperture.buffer(.009,join_style=2),-.33,-.30,GLASS,'inset steel lights')
    bars=[]
    for n in range(1,cols):
        xx=x-w/2+w*n/cols
        bars.append(box(xx-.026,z,xx+.026,z+h))
    for t in ([.68] if lod else [.26,.70]):
        bars.append(box(x-w/2,z+h*t-.025,x+w/2,z+h*t+.025))
    inner=aperture.buffer(-.070,join_style=2)
    frame=aperture.difference(inner.difference(unary_union(bars)))
    f.prism(frame,-.252,-.158,STEEL,'steel grid')
    return aperture


def strip(f,x,w,lod,h=13.33,narrow=False):
    low=.55
    full=box(x-w/2,low,x+w/2,h)
    if narrow:
        for base,top in [(1.10,3.64),(5.18,7.80),(9.57,12.03)]:
            steel_window(f,x,base,w,top-base,lod,cols=1 if lod else 2)
        masonry=[box(x-w/2,a,x+w/2,b)for a,b in [(low,1.10),(3.64,5.18),(7.80,9.57),(12.03,h)]]
        f.prism(unary_union(masonry),-.33,0,STONE,'narrow window pier stone')
        return full
    for i,(a,b)in enumerate([(.73,3.55),(5.43,8.31),(10.43,h)]):
        steel_window(f,x,a,w,b-a,lod,cols=2 if w<1.5 else 3)
    for z0,z1 in ((low,.73),(3.55,5.43),(8.31,10.43)):
        f.prism(box(x-w/2,z0,x+w/2,z1),-.32,-.143,PANEL,'recessed steel spandrel')
        if z1-z0>1 and not lod:
            inner=box(x-w/2+.12,z0+.14,x+w/2-.12,z1-.13)
            f.prism(inner.difference(inner.buffer(-.052,join_style=2)),-.148,-.098,STEEL,'embossed spandrel border')
            for side in (-1,1):
                xx=x+side*w*.26
                f.prism(Polygon([(xx-.135,z1-.25),(xx+.135,z1-.25),(xx,z0+.27)]),-.142,-.102,STEEL,'spandrel darts')
    return full


def stone_wall(f,z0,z1,holes,lod):
    surface=f.wall(z0,z1,holes,.41,STONE)
    if not lod:
        band=[]
        for i,z in enumerate(np.arange(.48,z1,.60)):
            band.append(box(-f.length/2,z-.008,f.length/2,z+.008))
            for u in np.arange(-f.length/2+(i%2)*.75,f.length/2,1.50):
                band.append(box(u-.007,z,u+.007,min(z+.60,z1)))
        joints=surface.intersection(unary_union(band))
        if joints.area>0:f.prism(joints,.001,.004,JOINT,'granite ashlar joints')
    f.box(0,z1-.07,f.length+.045,.14,.48,.004,STONE,'plain parapet coping')


def lamp(b,f,x,d,z,lod):
    tag=f.label+'/bronze lamps'
    def body(dx,dd,zz,w,depth,h,m,label):
        b.box(f.point(x+dx,z+zz,d+dd),(w,depth,h),m,[f.t,f.n,[0,0,1]],tag+'/'+label)
    for zz,w,depth,h in [(0.10,1.31,1.16,.20),(.25,1.08,1.01,.12),(.38,.83,.80,.15)]:
        body(0,0,zz,w,depth,h,RED,'stepped stone base')
    body(0,0,1.52,.49,.48,2.25,COPPER,'four-sided bronze column')
    for side in (-1,1):
        body(side*.212,0,1.54,.057,.56,2.22,GOLD,'vertical arrises')
        if not lod:
            zz=np.linspace(.59,2.39,31)
            pts=[f.point(x+side*.093*math.sin(t*math.pi*5),z+v,d+.249) for t,v in zip(np.linspace(0,1,len(zz)),zz)]
            b.tube(pts,.020,GOLD,5,tag+'/double volute')
    body(0,0,2.64,.57,.56,.13,GOLD,'lantern collar')
    body(0,0,2.81,.55,.54,.27,LAMP,'translucent lamp')
    # The photograph shows chevrons in front of the glass and a flat metal lid.
    for face in (-1,1):
        for xx in (-.16,0,.16):
            pts=[f.point(x+xx-.087,z+2.70,d+face*.279),f.point(x+xx,z+2.88,d+face*.279),f.point(x+xx+.087,z+2.70,d+face*.279)]
            b.tube(pts,.020,COPPER,5,tag+'/chevron metalwork')
    body(0,0,2.99,.61,.60,.10,COPPER,'lantern lid')


def lobby(f,lod):
    b=f.builder;w=3.26
    # Keep the portal casing, door, central tall grille and twin lamps as independently editable details.
    sh=opening(0,5.45,w,11.46,.43,14 if lod else 24)
    f.prism(sh.buffer(.009),-.36,-.33,GLASS,'tower glazing')
    inner=sh.buffer(-.14);bars=[]
    for x in (-.54,.54):bars.append(box(x-.083,5.45,x+.083,17.0))
    for z,h in [(7.26,.33),(10.01,1.15),(13.42,1.10),(15.14,.13)]:
        bars.append(box(-w/2,z-h/2,w/2,z+h/2))
    f.prism(sh.difference(inner.difference(unary_union(bars))),-.28,-.1,STEEL,'tall window mullions and spandrels')
    if not lod:f.prism(sh.buffer(.14).difference(sh),-.065,.089,STONE,'arched stone head')
    door=box(-1.22,.66,1.22,4.19)
    f.prism(door.buffer(.012,join_style=2),-.95,-.903,DOOR,'bronze double doors')
    for dx in (-.63,.63):
        for z0,z1 in ((.92,1.81),(1.93,2.87),(2.99,3.89)):
            t=box(dx-.445,z0,dx+.445,z1)
            f.prism(t.difference(t.buffer(-.085,join_style=2)),-.901,-.858,DOOR,'inset timber coloured door panels')
    f.box(0,2.42,.053,3.48,.105,-.823,STEEL,'door seam')
    casing=box(-2.13,.58,2.13,5.60)
    f.prism(casing.difference(door),-.67,.31,RED,'polished granite portal')
    for k in range(3):
        ring=door.buffer(.10+.13*k,join_style=2).difference(door.buffer(.047+.13*k,join_style=2))
        f.prism(ring.intersection(box(-2.2,.655,2.2,5.6)),.31,.34+.018*(2-k),RED,'receding portal grooves')
    for side in (-1,1):
        f.box(side*2.84,.32,1.86,.64,2.43,1.04,RED,'lamp plinths')
        lamp(b,f,side*2.86,1.64,.64,lod)
    for k in range(5):
        zz=(k+1)*.119;dep=(5-k)*.31+.34
        f.box(0,zz/2,4.07,zz,dep,dep/2+.15,BASE,'granite entrance steps')
    return [casing,sh]
