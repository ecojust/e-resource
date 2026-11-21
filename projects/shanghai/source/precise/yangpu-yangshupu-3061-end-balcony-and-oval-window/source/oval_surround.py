"""The capsule-shaped brick surround and the photographed outward-opening red casement."""
import math
import numpy as np
from shapely.geometry import Polygon,box
from photo_architecture import Facade
from window_joinery import WOOD,EDGE,glazing

BRICK='Rose facing brick'
LIGHT='Weathered brick'
MORTAR='Light lime pointing'
RED='Painted red infill'


def capsule(x,z0,z1,rx,rise,n):
    lo=z0+rise;hi=z1-rise
    top=[(x+rx*math.cos(a),hi+rise*math.sin(a))for a in np.linspace(0,math.pi,n+1)]
    bot=[(x+rx*math.cos(a),lo+rise*math.sin(a))for a in np.linspace(math.pi,2*math.pi,n+1)]
    return Polygon(top+bot)


def oval_window(builder,side,d,lod):
    x=d['oval_axis'];bottom=d['oval_bottom'];top=d['oval_top'];r=d['oval_width']/2
    rise=d['oval_rise'];band=d['oval_brick_width'];count=13 if lod else 31
    outer=capsule(x,bottom,top,r,rise,2*count)
    inner=capsule(x,bottom+band,top-band,r-band,rise-band,2*count)
    side.prism(outer.difference(inner),-.050,.026,MORTAR,'Oval/pointed backing')
    for upper,center in [(True,top-rise),(False,bottom+rise)]:
        start=0. if upper else math.pi
        n=15 if lod else 29
        for i in range(n):
            a=start+math.pi*(i+.06)/n;b=start+math.pi*(i+.94)/n
            angles=np.linspace(a,b,3 if lod else 6)
            strip=[(x+r*math.cos(t),center+rise*math.sin(t))for t in angles]
            strip.extend((x+(r-band)*math.cos(t),center+(rise-band)*math.sin(t))for t in angles[::-1])
            side.prism(Polygon(strip),.019,.045,BRICK if i%5 else LIGHT,'Oval/'+('head' if upper else 'foot')+' brick')
    low=bottom+rise;high=top-rise;n=max(6,round((high-low)/.062))
    for sign in (-1,1):
        cx=x+sign*(r-band/2)
        for j in range(n):
            a=low+(high-low)*j/n+.004;b=low+(high-low)*(j+1)/n-.004
            side.box(cx,(a+b)/2,band-.005,b-a,.030,.034,BRICK if (j+sign)%4 else LIGHT,'Oval/straight brick courses')
    glazed_lo=d['side_glazed_base'];glazed_hi=d['side_glazed_head']
    opening=box(x-r+band+.013,glazed_lo,x+r-band-.013,glazed_hi)
    band_floor=bottom+band+.142
    infill=inner.difference(opening)
    side.prism(infill.intersection(box(x-r,bottom-.01,x+r,band_floor)),-.079,-.032,'Warm sill paint','Oval/recessed pale lower segment')
    side.prism(infill.intersection(box(x-r,band_floor,x+r,top+.01)),-.078,-.040,RED,'Oval/arched head and square-bottom blind apron')
    side.box(x,band_floor+.012,2*(r-band)-.065,.039,.06,-.018,'Warm glazing bead','Oval/lower red sill')
    side.prism(opening,-.19,-.17,'Deep reveal','Oval/shadow behind open sash')
    side.prism(opening.difference(opening.buffer(-.047,join_style=2)),-.081,-.012,WOOD,'Oval/fixed jamb and lintel')
    # The hinge side stays in the jamb. The other stile stands over the brick in the photograph.
    width=2*(r-band)-.036
    hinge=side.point(x-width/2,0,-.016)[:2]
    angle=math.radians(d['open_sash_degrees'])
    direction=side.t[:2]*math.cos(angle)+side.n[:2]*math.sin(angle)
    leaf=Facade(builder,hinge,hinge+direction*width,'Oval open leaf')
    glazing(leaf,0,glazed_lo+.017,width,glazed_hi-glazed_lo-.034,2,3,.008,lod,'Six-light casement')
    if not lod:
        for z in [glazed_lo+.16,glazed_hi-.16]:
            side.box(x-width/2,z,.046,.092,.052,.009,EDGE,'Oval/hinge strap')
    return outer
