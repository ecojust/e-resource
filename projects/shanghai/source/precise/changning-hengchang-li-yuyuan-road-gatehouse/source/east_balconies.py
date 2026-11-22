"""The upper street bays east of the four measured sash windows."""
from math import ceil, cos, pi, sin
import numpy as np
from shapely.geometry import Polygon, box
from shapely.ops import unary_union
from gatehouse_finishes import CREAM, FITTING, GLASS, SHADE, STONE, WOOD, paint

CANE='Street balcony | woven reed screen'
STRAND='Street balcony | binding and reed'
RED='Street balcony | reddish casements'
CLOTH='Street balcony | charcoal canvas'
STRIPE='Street balcony | faded ivory stripe'
PALETTE={CANE:paint((155,120,83),.96),STRAND:paint((116,93,69),.94),
         RED:paint((110,66,54),.74),CLOTH:paint((87,84,80),.86),STRIPE:paint((183,177,158),.90)}
# The two broad arches and the next small arch still lie within the first
# roof. The following arch belongs to the adjoining cropped street section.
BAYS=[(20.52,24.78,7.02,8.99,10.18),(25.08,32.04,7.09,9.02,10.12),
      (32.62,35.47,7.11,9.17,10.25)]


def profile(l,r,b,s,t,n=33):
    cx=(l+r)/2
    return Polygon([(l,b),(r,b),*[(cx+(r-l)*.5*cos(a),s+(t-s)*sin(a)) for a in np.linspace(0,pi,n)]])


def openings():
    return {f'balcony-{i}':profile(*p) for i,p in enumerate(BAYS,1)}


def add_balconies(b,lod,layout):
    y=layout['front_y']['east']
    old=str(layout['period']).startswith('2018')
    def front(shape,near,far,mat,name):
        b.prism(shape,-far,-near,lambda x,z,d:(x,y-d,z),mat,name)
    for i,((left,right,sill,spring,crown),light) in enumerate(zip(BAYS,openings().values()),1):
        label=f'Street balcony {i} | '
        rim=light.buffer(.13,join_style=2).difference(light)
        front(rim,-.065,.010,CREAM,label+'rendered surround')
        glass=light.buffer(-.08,join_style=2)
        rails=[light.difference(glass),box(left,spring-.046,right,spring+.046)]
        for f in ((.31,.65) if i==1 else (.25,.5,.75)):
            x=left+(right-left)*f
            rails.append(box(x-.031,sill,x+.031,crown+.1))
        frame=light.intersection(unary_union(rails))
        front(frame,.079,.145,RED if i<3 else WOOD,label+'arched sash and fan transom')
        for k,pane in enumerate(getattr(light.difference(frame),'geoms',[light.difference(frame)])):
            if pane.area>1e-6:
                front(pane,.145,.161,GLASS,label+f'recessed glazing {k+1}')
        run=right-left
        # Each small platform is outside the street wall. The dirtier 2018
        # awnings are free of the broad reed panels visible in January 2021.
        def section(y0,y1,h0,h1,thick):
            return Polygon([(y0,h0),(y1,h1),(y1,h1-thick),(y0,h0-thick)])
        poly=section(y-1.04,y+.025,crown-.13,crown+.12,.045)
        b.prism(poly,left-.075,right+.075,lambda u,z,x:(x,u,z),CLOTH,label+'pitched canopy')
        screen_base=sill+.05
        screen_top=min(crown-.49,sill+2.16) if not old else sill+.86
        front(box(left-.06,sill-.16,right+.06,sill),-.71,.12,STONE,label+'balcony slab')
        for h in (sill+.18,screen_top-.09):
            b.tube([(left,y-.65,h),(right,y-.65,h)],.017,FITTING,6,label+'horizontal rail')
        for x in np.linspace(left+.04,right-.04,ceil(run/(.35 if lod else .22))):
            b.tube([(x,y-.65,screen_base),(x,y-.65,screen_top)],.015,FITTING,6,label+'vertical baluster')
        if i<=2 and not old:
            front(box(left+.035,screen_base,right-.035,screen_top),-.694,-.660,CANE,label+'woven reed privacy screen')
            for x in np.arange(left+.1,right-.05,.32 if lod else .11):
                front(box(x-.006,screen_base,x+.006,screen_top),-.703,-.694,STRAND,label+'screen seam')
            stripe=section(y-1.04,y+.025,crown-.127,crown+.123,.003)
            for x in np.arange(left-.045,right-.04,.17):
                b.prism(stripe,x,min(right+.06,x+.067),lambda u,z,s:(s,u,z),STRIPE,label+'awning stripe')
        elif i==3:
            for z in np.arange(sill+.14,sill+1.38,.16 if lod else .092):
                front(box(left+.075,z,right-.075,z+.043),-.693,-.651,WOOD,label+'horizontal timber screen')
