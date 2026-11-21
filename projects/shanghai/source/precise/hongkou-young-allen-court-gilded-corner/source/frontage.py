"""Punched street walls, wood joinery, brick arches and the round-headed Zhapu window."""
import math

import numpy as np
from shapely.geometry import LineString, Polygon, box
from shapely.ops import unary_union
from photo_architecture import opening
from grey_brick import BRICK

RED='Weathered red facing brick'
BRIGHT='Light fired brick'
STONE='Buff projecting sills'
SASH='Red-brown wood joinery'
GLASS='Recessed window glass'
SHADOW='Dark storefront backing'
SLATE='Dark street-facing roof skirt'
TILE='Weathered clay roof tiles'
CLAY='Orange tile arrises'
METAL='Dull sheet metal'
PLASTER='Pale dormer render'
GILT='Ochre-gold cupola sheet'
SEAM='Folded gold ribs'


def brick_arch(f,x,spring,width,rise,lod,front=.105,label='Segmental brick heads'):
    # Each ring has radial joints, including the tall central keystone.
    n=9 if lod else 17
    for i in range(n):
        a=math.pi*i/n+.004;z=math.pi*(i+1)/n-.004
        outer=.166+(.038 if i==n//2 else 0.)
        def pt(t,k):
            return (x+(width*.5+k)*math.cos(t),spring+(rise+k)*math.sin(t))
        f.prism(Polygon([pt(a,0),pt(a,outer),pt(z,outer),pt(z,0)]),
                .008,front+(i==n//2)*.016,BRIGHT if i==n//2 else RED,label)


def sash(f,x,z,w,h,arc,lod,fan=False,hood=True):
    seg=12 if lod else 26
    aperture=opening(x,z,w,h,arc,seg)
    f.prism(aperture.buffer(.013,join_style=2),-.254,-.23,GLASS,'Recessed glass')
    lo=x-w/2;hi=x+w/2;top=z+h
    bars=[box(x-.031,z,x+.031,top)]
    y=top-(arc if fan else h*.28)
    bars.append(box(lo,y-.035,hi,y+.035))
    if fan:
        for theta in (math.pi/4,math.pi*.75):
            edge=(x+w*.5*math.cos(theta),y+arc*math.sin(theta))
            bars.append(LineString([(x,y),edge]).buffer(.023,cap_style=2))
        for frac in (-.25,.25):
            xx=x+w*frac;bars.append(box(xx-.022,z,xx+.022,y))
    elif not lod and h>1.65:
        bars.append(box(lo,z+h*.39-.02,hi,z+h*.39+.02))
    if not fan and w>1.65:
        for k in (-.25,.25):
            xx=x+k*w;bars.append(box(xx-.024,z,xx+.024,top))
    panes=aperture.buffer(-.071,join_style=2).difference(unary_union(bars))
    f.prism(aperture.buffer(-.009,join_style=2).difference(panes),-.193,-.083,SASH,'Wood casements and transoms')
    f.box(x,z-.050,w+.20,.096,.39,.045,STONE,'Projecting window sills')
    if hood:
        brick_arch(f,x,top-arc,w,arc if arc else .038,lod)
    return aperture


def storefront(f,rows,plinth,lod):
    holes=[]
    for x,w in rows:
        z=.19;h=plinth-.59
        aperture=box(x-w*.5,z,x+w*.5,z+h)
        holes.append(aperture)
        f.prism(aperture.buffer(.009,join_style=2),-.277,-.253,SHADOW,'Shop recesses')
        bars=[box(x-.04,z,x+.04,z+h),box(x-w*.5,z+h*.78-.04,x+w*.5,z+h*.78+.04)]
        if not lod and w>2.4:
            for k in (-.25,.25):
                xx=x+w*k;bars.append(box(xx-.025,z,xx+.025,z+h*.78))
        opened=aperture.buffer(-.09,join_style=2).difference(unary_union(bars))
        f.prism(aperture.difference(opened),-.218,-.131,METAL,'Shop joinery')
    f.wall(.13,plinth,holes,.30,BRICK)
    f.beam(plinth-.18,.31,.11,RED,label='Shop fascia brick course')


def frontage(f,name,p,lod):
    absolute=p['north_bays']
    centres=sorted(f.center[0]-v for v in absolute)
    plinth=3.49
    shops=np.linspace(-f.length/2,f.length/2,max(3,round(f.length/3.8)+1))
    storefront(f,[((s+t)/2,(t-s)*.80)for s,t in zip(shops,shops[1:])],plinth,lod)
    holes=[]
    for j,value in enumerate(absolute):
        x=f.center[0]-value
        upper=(p['north_short_sills'][j],p['north_short_heights'][j]) if j<2 else (7.53,2.05)
        if j<2:
            f.box(x,upper[0]+upper[1]+.17,1.54,.085,.53,.118,METAL,'Hoods over two short sashes')
        for z,h in ((3.86,2.08),upper):
            holes.append(sash(f,x,z,1.21,h,.10,lod))
    f.wall(plinth,p['eave'],holes,.31,BRICK)
    for z,h,m in [(6.83,.102,RED),(7.03,.064,STONE),(p['eave']-.53,.19,RED),(p['eave']-.29,.13,BRIGHT),(p['eave']-.081,.12,STONE)]:
        f.beam(z,h,.10,m,label='Continuous street bands')
    for i in range(2,len(centres),3):
        xx=(centres[i]+centres[i-1])/2
        f.box(xx,(plinth+p['eave'])/2,.24,p['eave']-plinth,.13,.043,RED,'Red party-wall strips')
