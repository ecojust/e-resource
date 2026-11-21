"""Broad cut-corner shop, brick fascia, two cloth awnings and the photographed slatted return."""
import math
import numpy as np
from shapely.geometry import Polygon,box
from photo_architecture import Facade
from frontage import BRICK,GLASS,METAL,RED,SHADOW,STONE
from pitched_roofs import roof_panel

CLOTH='Faded rose awning cloth'
CREAM='Ivory awning cloth'
WOOD='Sienna wood fascia'


def awning(f,centre,width,z,material,lod):
    b=f.builder;w=width/2;back=.11;tip=.85
    pts=[f.point(centre-w,z,back),f.point(centre+w,z,back),f.point(centre+w,z-.21,tip),f.point(centre-w,z-.21,tip)]
    roof_panel(b,pts,material,'Corner shop / sloping fabric',thickness=.029)
    n=max(5,round(width/.14));span=width/n;edge=[]
    for k in range(n):
        angles=np.linspace(math.pi,0.,5 if lod else 9)
        for a in (angles[1:] if k else angles):
            edge.append((centre-w+span*(k+.5)+span*.5*math.cos(a),z-.29-.053*math.sin(a)))
    flap=Polygon([(centre-w,z-.207),(centre+w,z-.207),*reversed(edge)])
    f.prism(flap,tip-.026,tip,material,'Scalloped cloth valance')
    for side in (-1,1):
        x=centre+side*(w-.07)
        f.line((x,z-.63,.05),(x,z-.22,tip-.04),.021, METAL,6,'Awning stays')


def corner_shop(b,p,lod):
    n=np.array([-1.,1.])/math.sqrt(2);t=np.array([-1.,-1.])/math.sqrt(2);edge=n*1.67
    left,right=edge-1.82*t,edge+1.82*t
    pts=[[2.65,p['shell']['north']],[1.61,1.72],left,right,[-1.84,-1.60],[p['shell']['west'],-3.0]]
    base=Polygon([*pts,[.4,-.35]])
    b.plan_prism(base,.024,.13,STONE,'Corner shop / floor')
    for i,(a,c) in enumerate(zip(pts,pts[1:])):
        f=Facade(b,a,c,'Corner shop');z=3.47;holes=[]
        if i==2:
            for x,w,sill,top in [(-.11,.64,1.13,2.78),(1.09,1.13,.17,2.77)]:
                h=box(x-w/2,sill,x+w/2,top);holes.append(h)
                f.prism(h.buffer(.01,join_style=2),-.40,-.37,SHADOW,'Recessed shop interior')
                inner=h.buffer(-.043,join_style=2);f.prism(h.difference(inner),-.255,-.208,METAL,'Shop opening frames')
            awning(f,.66,2.14,2.99,CLOTH,lod)
        elif i==3:
            h=box(-f.length*.38,.17,f.length*.38,2.79);holes.append(h)
            f.prism(h.buffer(.012,join_style=2),-.40,-.37,SHADOW,'Recessed side shop entrance')
            awning(f,0.,f.length*.93,2.98,CREAM,lod)
        f.wall(.13,z,holes,.265,BRICK)
        f.beam(z-.21,.19,.065,RED,label='Reddish brick shop band')
        f.beam(z-.055,.069,.108,STONE,label='Shop fascia coping')
    b.plan_prism(base,3.458,3.492,METAL,'Corner shop / fascia top')
    # A wood strip fascia immediately adjoins the corner on Kunshan Road.
    f=Facade(b,[7.18,p['shell']['north']],[2.65,p['shell']['north']],'Kunshan shop')
    f.box(0,3.28,f.length,.87,.18,.128,WOOD,'Timber fascia backing')
    for h in np.linspace(2.91,3.65,7 if lod else 13):
        f.box(0,h,f.length+.014,.030,.09,.248,WOOD,'Raised timber fascia strips')
