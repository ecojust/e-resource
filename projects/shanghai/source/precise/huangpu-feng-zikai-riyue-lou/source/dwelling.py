"""Model the south-facing front of the registered residence and the identifiable roof section."""
import math

import numpy as np
from shapely.geometry import Polygon, box
from shapely.ops import unary_union
from photo_architecture import Facade, opening
from courtyard import (BRONZE, GLASS, GREY, IRON, IVORY, SILL, STONE, TILE, TIMBER,
                       casement, entry, front, garden)

HALF=3.00
DEPTH=5.10
EAVE=6.14
GABLE_WIDTH=3.00
GABLE_APEX=7.85


def canopy(f):
    f.box(0,2.91,1.93,.125,1.03,.410,SILL,'entrance canopy slab')
    f.box(0,2.974,1.98,.043,1.06,.416,GREY,'canopy drip edge')
    for sign in (-1,1):
        x=sign*.790
        points=[(x,0,2.40),(x,-.11,2.40),(x,-.22,2.58),
                (x,-.48,2.70),(x,-.63,2.79),(x,-.72,2.88),(x,0,2.88)]
        poly=Polygon([(y,z) for _,y,z in points])
        f.builder.prism(poly,x-.052,x+.052,lambda y,z,u:(u,y,z),TIMBER,'Entrance/dark timber canopy corbel')
    f.builder.lathe((0,-.42),[(2.800,.081),(2.819,.103),(2.852,.082)],SILL,12,'Entrance/canopy lamp')


def lower_front(b,lod):
    fac=front(b,-HALF,HALF,0,'Garden elevation')
    holes=[entry(fac,lod)]
    for u in (-1.96,1.98):
        win=opening(u,.69,1.29,1.70);holes.append(win)
        casement(fac,win,3,4,'historic casement')
        fac.box(u,.65,1.42,.086,.18,.055,SILL,'window sill')
        fac.box(u,2.43,1.40,.060,.13,.024,SILL,'window head')
    # The front room and trapezoidal sun room meet above the same entrance.
    holes.append(box(-1.39,3.82,1.39,5.89))
    holes.extend(opening(sign*2.29,3.99,.73,1.40) for sign in (-1,1))
    fac.wall(.0,EAVE,holes,thickness=.21,material=IVORY)
    fac.prism(box(-HALF,.055,HALF,.33).difference(unary_union(holes)),-.009,.035,STONE,'low rendered plinth')
    canopy(fac)
    for sign in (-1,1):
        u=sign*2.29
        rail=opening(u,3.99,.73,1.40)
        # Only a narrow side bay survives in the family photograph; keep it as a
        # glazed shallow return, without extending it into adjacent households.
        casement(fac,rail,2,3,'eaves-side light')
    for x in (-HALF,HALF):
        b.box((x,.06,3.20),(.060,.135,6.30),IVORY,label='Boundary/shared party edge')


def sun_room(b,lod):
    outline=[(-1.46,0),(-1.13,-.74),(1.13,-.74),(1.46,0)]
    b.plan_prism(Polygon(outline),3.32,3.83,IVORY,'Sun room/trapezoidal apron')
    for i,(a,c)in enumerate(zip(outline,outline[1:])):
        f=Facade(b,a,c,'Sun room/front' if i==1 else 'Sun room/angled return '+str(i));w=f.length
        shape=box(-w*.5+.07,3.83,w*.5-.07,5.80)
        f.wall(3.75,5.94,[shape],.084,TIMBER)
        # 2022 interior photographs show a central meeting stile; the smaller
        # angled casements on either side open out towards the garden.
        casement(f,shape,2 if i==1 else 1,3,'bay casement',.042)
        f.box(0,3.80,w+.02,.092,.105,.030,SILL,'continuous bay sill')
        f.box(0,5.875,w+.035,.093,.113,.027,TIMBER,'top rail')
    # Close the mantle around a real skylight opening instead of laying a second
    # opaque cover beneath the glazing described and photographed by the reporter.
    cap=Polygon([(-1.44,.035),(-1.15,-.80),(1.15,-.80),(1.44,.035)])
    light=box(-.48,-.62,.48,-.11)
    b.plan_prism(cap.difference(light),5.93,6.01,GREY,'Sun room/skylight kerb')
    b.plan_prism(light,5.975,5.995,GLASS,'Sun room/skylight pane')
    b.plan_prism(light.buffer(.037,join_style=2).difference(light),5.99,6.04,TIMBER,'Sun room/skylight frame')


def roof(b,lod):
    # The historic lane photograph singles out the projecting triangular bay.
    # Adjacent ridge heights and the undocumented rear of the row end at this
    # model's roof section. East/west party walls carry no invented windows.
    ridge=7.43;ridge_y=3.40;back=DEPTH
    a=Polygon([(-.15,EAVE-.04),(ridge_y,ridge),(back,7.04),(back,6.88),(ridge_y,ridge-.16),(-.15,EAVE-.20)])
    b.prism(a,-HALF-.045,HALF+.045,lambda y,z,x:(x,y,z),TILE,'Roof/main continuous tile slopes')
    for x in (-HALF,HALF):
        skin=Polygon([(0,0),(back,0),(back,7.01),(ridge_y,ridge-.09),(0,EAVE-.08)])
        b.prism(skin,x-.02,x+.02,lambda y,z,x_:(x_,y,z),IVORY,'Boundary/closed shared section')
    b.box((0,back,3.50),(HALF*2,.105,7.00),IVORY,label='Boundary/rear section')
    b.tube([(-HALF-.04,ridge_y,ridge+.035),(HALF+.04,ridge_y,ridge+.035)],.078,TILE,8 if lod else 12,'Roof/ridge cap')
    for y in np.linspace(.03,ridge_y-.18,7 if lod else 17):
        z=EAVE-.04+(ridge-(EAVE-.04))*(y+.15)/(ridge_y+.15)
        # The cross gable covers the middle of these courses at the front.
        for x0,x1 in [(-HALF-.035,-1.39),(1.39,HALF+.035)] if y<1.97 else [(-HALF-.035,HALF+.035)]:
            b.box(((x0+x1)/2,y,z+.014),(x1-x0,.064,.045),TILE,label='Roof/tile courses')
    half=GABLE_WIDTH/2
    f=front(b,-half,half,-.25,'South gable');f.prism(Polygon([(-half,5.99),(half,5.99),(0,GABLE_APEX)]),-.16,.01,IVORY,'triangular stucco face')
    for s in (-1,1):
        slab=Polygon([(0,GABLE_APEX+.02),(s*(half+.095),5.98),(s*(half+.095),6.10),(0,GABLE_APEX+.15)])
        b.prism(slab,-2.04,.41,lambda x,z,d:(x,-d,z),TILE,'Roof/gable rake and crossing slope')
        for t in np.linspace(.10,.96,4 if lod else 10):
            x=s*(half+.095)*t;z=GABLE_APEX+.15+(6.10-GABLE_APEX-.15)*t
            b.box((x,.815,z+.008),(.057,2.45,.044),TILE,label='Roof/gable tile courses')
    b.tube([(0,-.40,GABLE_APEX+.15),(0,2.03,GABLE_APEX+.15)],.068,TILE,8 if lod else 12,'Roof/cross-gable ridge')
    for lo,hi in ((-HALF,-1.42),(1.42,HALF)):
        b.box(((lo+hi)/2,-.085,EAVE-.12),(hi-lo,.19,.108),TIMBER,label='Roof/eaves fascia')


def model(b,lod):
    lower_front(b,lod);sun_room(b,lod);roof(b,lod);garden(b,lod)
