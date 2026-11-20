"""The named plot, the auditorium and its two pavilion-tipped courtyard wings."""
import numpy as np
from shapely.geometry import box,Polygon
from shapely.ops import unary_union
from photo_architecture import Facade
from elevations import BRICK,BASE,TRIM,ASPHALT,PALETTE,RED,light,standard,court_elevation,painted,rail
from roofs import TILE,ROLL,PIGMENT,STONE,DARK,GLASS,BLUE,TIMBER,main_roof,pyramid

CENTER=-.95
PLAN=[(-43.59,25.45),(-43.44,6.26),(43.21,6.14),(43.14,26.93),
      (59.63,27.01),(59.28,-11.65),(7.52,-12.10),(7.23,-24.01),
      (-9.74,-23.90),(-9.82,-12.94),(-59.12,-12.72),(-58.95,25.47)]


def slab(b,p,z,material,label):
    if not p.is_empty:b.plan_prism(p,z-.14,z,material,label)


def walkway(b,a,c,lod):
    a=np.array(a);c=np.array(c);along=(c-a)/np.linalg.norm(c-a);side=np.array([-along[1],along[0]]);z=14.38;half=1.44
    for sign in (-1,1):
        pts=[(*a,z+.65),(*c,z+.65),(*(c+sign*half*side),z),(*(a+sign*half*side),z)]
        if np.cross(np.subtract(pts[1],pts[0]),np.subtract(pts[2],pts[0]))[2]<0:pts.reverse()
        b.add(pts,[(0,1,2,3)],TILE,'Roof/gallery tiled canopy')
        for t in np.linspace(0,1,int(np.linalg.norm(c-a)/(.99 if lod else .37))+1):
            x=a+(c-a)*t
            b.tube([(*x,z+.67),(*(x+sign*side*half),z+.035)],.044,ROLL,5,'Roof/gallery tile rolls')
        for t in np.linspace(.08,.93,1+round(np.linalg.norm(c-a)/3.45)):
            x=a+(c-a)*t+side*sign*.77
            b.box((*x,13.31),(.18,.18,2.11),PIGMENT,label='Roof/gallery posts')
        b.tube([(*(a+sign*side*half),z),(*(c+sign*side*half),z)],.074,TIMBER,8,'Roof/gallery eaves')


def endpoint(b,cx,cy,lod):
    h=4.63; deck=12.81; eave=15.61
    for a,c in [((cx-h,cy-h),(cx+h,cy-h)),((cx+h,cy-h),(cx+h,cy+h)),((cx+h,cy+h),(cx-h,cy+h)),((cx-h,cy+h),(cx-h,cy-h))]:
        f=Facade(b,a,c,'End pavilion/open gallery')
        rail(f,0,deck,2*h,lod)
        for u in (-3.04,0,3.04):
            p=f.point(u,0,-.15)
            b.lathe(p[:2],[(deck,.17),(deck+.15,.19),(deck+.26,.14),(15.04,.131),(15.22,.18)],PIGMENT,8 if lod else 16,'End pavilion/red posts')
        painted(f,0,15.32,2*h,.36,lod)
    b.box((cx,cy,deck+.045),(2*h+.22,2*h+.22,.18),TRIM,label='End pavilion/terrace')
    b.box((cx,cy,15.52),(2*h+.24,2*h+.24,.18),TIMBER,label='End pavilion/painted soffit')
    pyramid(b,cx,cy,5.56,eave,2.90,lod)


def southern_projection(b,lod):
    # The projecting flat-roof room is visible on the photograph below the dormers.
    # Its central south bank of tall lights differs from the north lawn entrance.
    corners=[(-9.74,-23.90),(7.23,-24.01),(7.52,-12.10),(-9.82,-12.94)]
    for index in range(3):
        a=corners[index];c=corners[index+1];f=Facade(b,a,c,'South/auditorium stair annex')
        if index==1: # east wall: narrow, spaced staircase lights
            q=[light(f,x,z,.74,h,lod,1,2)for x,z,h in [(-3.2,3.3,1.50),(-.20,5.8,1.45),(2.8,8.50,1.1)]]
            f.wall(.13,11.48,q,.33,STONE)
        elif index==0:
            q=[light(f,u,6.20,1.07,4.07,lod,2,4)for u in np.arange(-5.66,5.70,1.89)]
            f.wall(.13,11.48,q,.35,STONE)
        else: # this is an internal intersection with the long wing
            continue
        f.beam(11.47,.22,.17,TRIM)
    f=Facade(b,corners[-1],corners[0],'South/west stair return')
    f.wall(.13,11.48,[light(f,x,zz,.71,1.31,lod,1,2)for x,zz in [(-2.1,4.3),(1.0,7.1),(3.7,9.4)]],.33,STONE)
    f.beam(11.47,.22,.17,TRIM)
    slab(b,Polygon(corners),11.58,ASPHALT,'South/stair roof')


def model(b,lod):
    original=Polygon(PLAN)
    slab(b,original,.14,BASE,'Foundation/named school building')
    # Along the north side, the two main red-brick wings project toward the lawn.
    court_elevation(b,lod,CENTER,6.18)
    left=CENTER-21.75;right=CENTER+21.75
    sides=[((-43.59,25.45),(-58.95,25.47),4),((-58.95,25.47),(-59.12,-12.72),11),
           ((-59.12,-12.72),(left,-12.63),10),((right,-12.25),(59.28,-11.65),10),
           ((59.28,-11.65),(59.63,27.01),11),((59.63,27.01),(43.14,26.93),4),
           ((43.14,26.93),(43.21,6.14),6),((43.21,6.14),(right,6.18),6),
           ((left,6.18),(-43.44,6.26),6),((-43.44,6.26),(-43.59,25.45),6)]
    for i,(a,c,n) in enumerate(sides):
        standard(Facade(b,a,c,'Wings/'+str(i)),lod,n)
    rear=Facade(b,(left,-12.63),(right,-12.25),'South/main hall windows')
    standard(rear,lod,11,True)
    # The upper drum ends have a circular aperture visible in the oblique southern view.
    for sign in (-1,1):
        xx=CENTER+sign*21.75;y0=-12.48;y1=6.18
        f=Facade(b,(xx,y0 if sign>0 else y1),(xx,y1 if sign>0 else y0),'Main hall/roof drum ends')
        from shapely.geometry import Point
        roundel=Point(0,14.34).buffer(.66,quad_segs=8 if lod else 15)
        f.wall(12.68,15.64,[roundel],.29,BRICK)
        f.prism(roundel,-.25,-.23,GLASS,'circular light')
        f.prism(roundel.buffer(.09).difference(roundel),-.05,.09,TRIM,'circular stone surround')
    # Low buildings meet below the taller central drum. The raised central roof is a separate mesh.
    annex=Polygon([(-9.74,-23.90),(7.23,-24.01),(7.52,-12.10),(-9.82,-12.94)])
    main=Polygon([(left,-12.63),(right,-12.25),(right,6.18),(left,6.18)])
    slab(b,original.difference(unary_union([annex,main])),12.78,ASPHALT,'Wings/terraces')
    slab(b,main.buffer(.39,join_style=2),15.65,TIMBER,'Auditorium/wood soffit')
    southern_projection(b,lod)
    main_roof(b,lod)
    for sign,cx,cy in [(-1,-51.38,17.1),(1,51.27,18.5)]:
        xx=CENTER+sign*21.53
        walkway(b,(xx,-3.12),(cx,-3.12),lod)
        walkway(b,(cx,-3.12),(cx,cy-4.43),lod)
        endpoint(b,cx,cy,lod)
