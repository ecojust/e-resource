"""East street front of the Lianshi Association at 55 Zhonghua Road.

X runs north along the frontage. Positive Y runs into the building. The three
photographically levelled views measure the seven axes and distinguish the
modern shopfront, the common terrace, seven balconies and three roof fronts.
"""
import math
from pathlib import Path
import json
import numpy as np
from shapely.geometry import Polygon, LineString, box
from shapely.ops import unary_union
from photo_architecture import Facade

SOURCE=Path(__file__).resolve().parent
REG=json.loads((SOURCE/'frontage-registration.json').read_bytes())
HALF=13.15
AXES=(-11.006,-7.294,-3.691,0.,3.691,7.294,11.006)
WALL='Warm grey plaster'
TRIM='Limestone mouldings'
RAIL='Carved grey balcony rail'
BLOCK='Recessed cornice'
SASH='Dark sash'
GLASS='Blue grey street glass'
LIGHT='Pale transom glass'
REVEAL='Window reveals'
SHOP='Pale shop tile'
STONE='Dark shop lintel'
PLINTH='Stone entrance plinth'
CUT='Section surface'
MATERIALS={name:{'color':colour,'roughness':rough} for name,colour,rough in [
    (WALL,[.704,.682,.608],.91),(TRIM,[.780,.747,.658],.86),
    (RAIL,[.675,.652,.579],.91),(BLOCK,[.507,.492,.423],.9),
    (SASH,[.177,.166,.146],.72),(GLASS,[.173,.212,.230],.36),
    (LIGHT,[.418,.460,.454],.48),(REVEAL,[.412,.410,.373],.89),(SHOP,[.623,.611,.570],.84),
    (STONE,[.262,.254,.237],.8),(PLINTH,[.349,.350,.333],.91),
    (CUT,[.583,.578,.536],.93)]}


def trim(face,x,z,width,height,depth,mat,label,back=-.023):
    face.prism(box(x-width/2,z-height/2,x+width/2,z+height/2),
               back,depth,mat,label)


def glazing(face,x,z0,z1,width,columns,rows,label,back=-.25):
    """The opening extends through the external wall; the window closes it from within."""
    lo,hi=x-width/2,x+width/2
    aperture=box(lo,z0,hi,z1)
    inner=box(lo+.062,z0+.070,hi-.062,z1-.070)
    face.prism(aperture.difference(inner),back,back+.085,SASH,label+' frame')
    face.prism(inner,back-.045,back-.006,GLASS,label+' glass')
    for col in range(1,columns):
        trim(face,lo+width*col/columns,(z0+z1)/2,.045,z1-z0-.115,back+.054,SASH,label+' sash',back-.002)
    for f in rows:
        trim(face,x,z0+(z1-z0)*f,width-.13,.058,back+.067,SASH,label+' sash',back-.001)


def diamond_panel(face,x,z,w,h,front,back,cells,label):
    """Each open panel contains crossed stone diagonals and a true void on either side."""
    body=box(x-w/2,z,x+w/2,z+h)
    rim=.080
    bars=[body.difference(box(x-w/2+rim,z+rim,x+w/2-rim,z+h-rim))]
    module=w/cells
    for i in range(cells):
        lo=x-w/2+i*module;hi=lo+module
        if i: bars.append(box(lo-.044,z,lo+.044,z+h))
        for ends in [[(lo+.095,z+.105),(hi-.095,z+h-.105)],
                     [(lo+.095,z+h-.105),(hi-.095,z+.105)]]:
            bars.append(LineString(ends).buffer(.041,cap_style='flat',join_style='mitre'))
    face.prism(unary_union(bars),back,front,RAIL,label)


def upper_balcony(b,face,x,idx,distant):
    label='balcony '+str(idx+1)
    w=2.64 if idx==3 else 1.83
    extent=.80 if idx==3 else .71
    top=9.15
    for z,h,width,end in [(top-.16,.22,w+.18,extent+.08),(top-.30,.095,w+.11,extent),
                          (top-.03,.065,w+.20,extent+.10)]:
        trim(face,x,z,width,h,end,TRIM,label+' slab')
    diamond_panel(face,x,top+.03,w,.78,extent+.065,extent-.045,3 if idx==3 else 2,label+' front')
    trim(face,x,top+.855,w+.12,.105,extent+.12,TRIM,label+' coping',extent-.105)
    for sign in (-1,1):
        xx=x+sign*(w/2-.045)
        side=Facade(b,(xx,0),(xx,-extent),label+' side')
        diamond_panel(side,0,top+.035,extent-.04,.77,.048,-.048,1,'open end')
        side.box(0,top+.86,extent+.02,.105,.21,0,TRIM,'coping')
        xx=x+sign*(w/2-.28)
        corbel=Facade(b,(xx,-extent),(xx,.03),label+' bracket')
        L=extent/2
        poly=Polygon([(-L,top-.21),(L,top-.21),(L,top-1.08),
                      (L-.13,top-1.04),(-.17,top-.56),(-L,top-.46)])
        corbel.prism(poly,-.13,.13,RAIL,'profile')


def pilaster(face,x,distant):
    label='rusticated pier'
    for z0,z1 in [(5.48,8.74),(8.85,12.12)]:
        n=round((z1-z0)/(.49 if distant else .34));step=(z1-z0)/n
        for i in range(n):
            z=z0+(i+.5)*step;trim(face,x,z,.83,step-.041,.090,TRIM,label+' courses')
    trim(face,x,12.01,.86,.10,.132,TRIM,label+' neck')
    trim(face,x,12.21,.78,.34,.113,TRIM,label+' capital')
    trim(face,x,12.50,1.04,.16,.194,TRIM,label+' abacus')
    trim(face,x,12.71,.66,.20,.128,TRIM,label+' upper stone')
    if not distant:
        for sign in [-1,1]:
            curve=[(x+sign*(.015+.23*t),12.80-.144*math.sin(math.pi*t))for t in np.linspace(0,1,12)]
            crown_outline(face,curve,.129,.17,.057,RAIL,label+' upper ornament')
    # Pendant flowers between each pair of windows, below the continuous eave.
    for sign in (-1,1):
        leaf=Polygon([(x+sign*.07,12.29),(x+sign*.27,12.26),(x+sign*.36,12.12),
                      (x+sign*.23,12.17),(x+sign*.19,11.98),(x+sign*.10,12.11)])
        face.prism(leaf,.112,.166,RAIL,label+' leaves')
    if not distant:
        diamond=Polygon([(x,12.22),(x+.096,12.08),(x,11.93),(x-.096,12.08)])
        face.prism(diamond,.113,.187,RAIL,label+' pendant')


def terrace(face):
    # Seven street bays share a lower terrace, with solid end and middle panels.
    lower=5.02;top=5.81
    trim(face,0,4.88,26.18,.23,.70,RAIL,'terrace soffit')
    trim(face,0,5.015,26.34,.092,.79,TRIM,'terrace edge')
    limits=[-13.03,-9.25,-5.52,-1.86,1.86,5.52,9.25,13.03]
    for i,(lo,hi) in enumerate(zip(limits,limits[1:])):
        x=(lo+hi)/2;w=hi-lo-.18
        if i in (0,3,6):
            trim(face,x,(lower+top)/2,w,top-lower,.78,RAIL,'terrace solid panels',.59)
            trim(face,x,(lower+top)/2,w-.38,top-lower-.23,.795,WALL,'terrace shallow field',.76)
        else:diamond_panel(face,x,lower+.08,w,top-lower-.13,.74,.56,5,'terrace open panels')
        trim(face,x,top+.055,w+.04,.12,.827,TRIM,'terrace coping',.52)
    # Scroll at the centre of the common terrace, visible between the taller
    # lower windows and the contemporary recessed transom.
    for sign in (-1,1):
        v=[(sign*(.05+.73*t),top+.075+.135*math.sin(math.pi*t)-.11*t)for t in np.linspace(0,1,18)]
        crown_outline(face,v,.773,.845,.078,TRIM,'terrace central scroll')
    for x in limits:
        trim(face,x,(lower+top)/2,.27,top-lower+.16,.85,TRIM,'terrace small piers',.48)


def low_street(face,holes,distant):
    """The January 2021 photograph has glass shops and a central doorway under a dark fascia."""
    openings=[]
    for i,x in enumerate(AXES):
        width=2.48 if i!=3 else 2.54
        sill=.10 if i in (0,3) else .46
        head=3.52
        aperture=box(x-width/2,sill,x+width/2,head);holes.append(aperture);openings.append((i,x,sill,head,width))
    back=-.31
    for i,x,sill,head,width in openings:
        glazing(face,x,sill,head,width,2 if i in (0,3)else 1,[.77] if i in (0,3) else [],'shop storefront',back)
        if i in (0,3):
            trim(face,x,.055,width-.04,.105,.135,PLINTH,'shop thresholds',-.15)
        if i==3:
            for dx in (-.13,.13):trim(face,x+dx,1.45,.045,.52,back+.105,SASH,'door handles',back+.025)
        trim(face,x,3.78,3.38,.46,.094,STONE,'shop fascia')
    bands=box(-HALF,0,HALF,4.76).difference(unary_union(holes))
    face.prism(bands,-.278,.033,SHOP,'street level')
    base=box(-HALF,0,HALF,.37).difference(unary_union(holes))
    face.prism(base,.033,.060,PLINTH,'continuous plinth')
    trim(face,0,4.42,26.22,.72,.102,STONE,'later shop sign band')


def crown_outline(face,points,back,front,w,mat,label):
    line=LineString(points).buffer(w/2,cap_style='flat',join_style='mitre')
    face.prism(line,back,front,mat,label)


def gable(b,x,distant):
    y=.394; half=3.66;g=Facade(b,(x-half,y),(x+half,y),'roof wing')
    outline=Polygon([(-half,13.58),(half,13.58),(half,16.82),(0,18.565),(-half,16.82)])
    holes=[box(t-.455,14.19,t+.455,15.89)for t in (-1.73,1.73)]
    g.prism(outline.difference(unary_union(holes)),-.24,0,WALL,'gable front')
    for t in (-1.73,1.73):
        glazing(g,t,14.19,15.89,.91,2,[],'gable window',-.183)
        trim(g,t,15.93,1.10,.125,.102,TRIM,'gable window head')
    trim(g,0,13.95,half*2,.38,.19,TRIM,'parapet')
    trim(g,0,14.18,half*2+.10,.105,.245,TRIM,'parapet coping')
    for u in np.arange(-3.08,3.1,.68):
        trim(g,float(u),13.95,.045,.30,.212,RAIL,'parapet joints',.17)
    pts=[(-half,16.82),(0,18.565),(half,16.82)]
    crown_outline(g,pts,-.085,.15,.12,TRIM,'gabled coping')
    for sign in (-1,1):trim(g,sign*(half-.12),15.20,.14,3.13,.071,TRIM,'wall edge')
    # The tall blind band between the two windows has a rounded head.
    curve=[(-.61,14.05),(-.61,17.0),*[(-.61*math.cos(a),17.0+.67*math.sin(a)) for a in np.linspace(0,math.pi,18 if not distant else 8)],(.61,14.05)]
    crown_outline(g,curve,-.003,.058,.07,TRIM,'blind arch band')
    for d in (-1,1):
        xx=x+d*half
        side=Facade(b,(xx,y),(xx,2.89),'roof wing short return')
        side.prism(box(-side.length/2,13.6,side.length/2,16.76),-.106,.030,WALL,'flank')
    # The observed first part of each pitched roof ends at the documented section.
    for sign in (-1,1):
        poly=Polygon([(0,18.565),(sign*half,16.82),(sign*half,16.68),(0,18.423)])
        g.prism(poly,-(2.89-y),-.240,BLOCK,'short roof')
    end=Facade(b,(x+half,2.89),(x-half,2.89),'roof wing')
    end.prism(outline,-.04,.015,CUT,'section')


def tower(b,distant):
    y=.425;halfw=1.78;f=Facade(b,(-halfw,y),(halfw,y),'central tower')
    holes=[box(-.45,15.42,.45,16.62)]
    f.prism(box(-halfw,13.53,halfw,19.22).difference(holes[0]),-.27,0,WALL,'face')
    glazing(f,0,15.42,16.62,.90,2,[],'small tower casement',-.22)
    for sign in (-1,1):
        trim(f,sign*1.48,16.71,.29,4.87,.14,TRIM,'corner pilasters')
        trim(f,sign*1.48,18.99,.43,.21,.22,TRIM,'capital')
    def garland(l,z):
        line=[(l*t,z-.33*math.sin(math.pi*t))for t in np.linspace(0,1,7 if distant else 12)]
        crown_outline(f,line,.015,.088,.097,RAIL,'hanging garland')
    garland(-.70,18.30);garland(.70,18.30)
    trim(f,0,18.34,.22,.15,.12,TRIM,'garland knot')
    roof=[(-1.94,19.41),(-1.70,19.29),(-.86,19.21),(0,19.18),(.86,19.21),(1.70,19.29),(1.94,19.41)]
    crown_outline(f,roof,-.12,.27,.25,TRIM,'tower flared cornice')
    crown_outline(f,[(x,z-.185)for x,z in roof],-.08,.256,.118,BLOCK,'tower cornice soffit')
    crown_outline(f,[(x*.97,z-.290)for x,z in roof],-.075,.184,.074,TRIM,'tower lower cornice')
    for sign in (-1,1):
        xx=sign*halfw
        b.box((xx,(y+2.81)/2,19.104),(.24,2.81-y,.115),BLOCK,label='tower dark return under eave')
        b.box((xx,(y+2.81)/2,19.229),(.30,2.81-y,.125),TRIM,label='tower cap return')
    for sign in (-1,1):
        xx=sign*halfw
        side=Facade(b,(xx,y),(xx,2.81),'tower side')
        side.prism(box(-side.length/2,13.59,side.length/2,18.98),-.075,.062,WALL,'short return')
    b.plan_prism(box(-1.78,y,1.78,2.81),19.010,19.13,BLOCK,'tower upper roof')
    back=Facade(b,(halfw,2.81),(-halfw,2.81),'tower')
    back.prism(box(-halfw,13.55,halfw,19.05),-.06,.04,CUT,'section')
    for z,w,h in [(19.25,1.18,.23),(19.52,.89,.36),(19.79,1.15,.15)]:
        b.box((0,1.70,z),(w,1.08,h),TRIM,label='tower short roof block')


def add_building(builder,distant):
    f=Facade(builder,(-HALF,0),(HALF,0),'east front')
    low=[];low_street(f,low,distant)
    window_holes=[]
    for idx,x in enumerate(AXES):
        wid=1.74 if idx==3 else 1.22
        for sill,head,n in [(5.59,8.085,'lower'),(9.19,11.673,'upper')]:
            aperture=box(x-wid/2,sill,x+wid/2,head);window_holes.append(aperture)
            glazing(f,x,sill,head,wid,2 if idx==3 else 1,[.78],n+' casement')
            trim(f,x,head+.075,wid+.23,.155,.127,TRIM,n+' stone hood')
            trim(f,x,head+.178,wid+.30,.072,.179,TRIM,n+' stepped hood')
            trim(f,x,head-.298,wid-.16,.37,-.237,LIGHT,n+' transom',-.244)
            if not distant and n=='lower' and idx in (5,6):
                for bar in np.linspace(x-wid*.38,x+wid*.38,8):
                    trim(f,float(bar),(sill+head)/2,.021,head-sill-.14,-.135,RAIL,'north lower grille',-.162)
                for high in [sill+.46,sill+1.05,sill+1.72]:
                    trim(f,x,high,wid-.12,.025,-.122,RAIL,'north lower grille',-.153)
        upper_balcony(builder,f,x,idx,distant)
    f.prism(box(-HALF,4.69,HALF,13.57).difference(unary_union(window_holes)),-.27,0,WALL,'upper wall')
    for x in (-12.89,-9.20,-5.50,-1.85,1.85,5.50,9.20,12.89):pilaster(f,x,distant)
    for z,w,h,d,mat in [(12.76,26.38,.28,.16,TRIM),(13.03,26.42,.25,.23,BLOCK),(13.25,26.55,.17,.38,TRIM),(13.51,26.65,.19,.50,TRIM)]:
        trim(f,0,z,w,h,d,mat,'main continuous cornice')
    for x in np.arange(-12.94,13.,.46 if distant else .32):
        trim(f,float(x),13.128,.12,.18,.37,TRIM,'dentils')
    if not distant:
        for x in np.arange(-12.93,12.96,.195):
            trim(f,float(x),12.907,.068,.078,.239,TRIM,'fine cornice teeth',.15)
        for x in [-2.47,2.52]:
            builder.tube([f.point(x,5.91,.134),f.point(x,12.96,.134)],
                         .061,TRIM,sides=8,label='front drainpipes')
    points=[(-2.37,13.47),(0,14.855),(2.37,13.47)]
    f.prism(Polygon([*points,(2.37,13.13),(-2.37,13.13)]),-.14,.16,WALL,'triangular pediment')
    crown_outline(f,[(x,z-.158)for x,z in points],-.10,.535,.176,BLOCK,'pediment projecting soffit')
    crown_outline(f,points,-.15,.624,.235,TRIM,'pediment raking cornice')
    for x in np.arange(-2.15,2.17,.36 if distant else .25):
        z=14.855-abs(x)*(14.855-13.47)/2.37
        trim(f,float(x),float(z-.26),.105,.135,.518,TRIM,'pediment dentils',.37)
    crown_outline(f,[(x*.85,z-.135)for x,z in points],.15,.28,.11,BLOCK,'pediment inner moulding')
    # The triangular hood stands over a separate, deeper stone window frame.
    for sign in (-1,1):
        trim(f,sign*1.10,12.22,.24,1.28,.176,TRIM,'central hood outer posts')
        trim(f,sign*1.10,12.82,.40,.16,.218,TRIM,'central hood capitals')
    trim(f,0,12.05,2.32,.19,.204,TRIM,'central window lintel')
    trim(f,0,12.08,.26,.46,.23,TRIM,'central window keystone')
    terrace(f)
    for sign in (-1,1):
        trim(f,sign*(13.3888+HALF)/2,6.76,13.3888-HALF,13.52,.001,WALL,'party wall closure',-.265)
    # Solid closure is limited to the first three metres of the independently
    # identified owner. The rear of the generic city building remains present.
    poly=Polygon(REG['outline_xy'])
    builder.plan_prism(poly.intersection(box(-16,.314,16,4)),.001,.087,PLINTH,
                       'closed shops internal plinth')
    builder.plan_prism(poly,13.49,13.56,BLOCK,'front section plain roof')
    for i,(e1,e2)in enumerate(zip(poly.exterior.coords,list(poly.exterior.coords)[1:])):
        if max(abs(e1[1]),abs(e2[1]))<.01:continue
        side=Facade(builder,e1,e2,'lower section')
        side.prism(box(-side.length/2,.01,side.length/2,13.49),-.025,.002,CUT,'wall '+str(i))
    for x in (-9.1357,9.1357):gable(builder,x,distant)
    tower(builder,distant)
