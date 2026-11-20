"""The covered hall on the west of the 52 Xiaotaoyuan Street court. The neighbouring ranges retain their original city source."""
from math import cos, sin, pi, tau
from pathlib import Path
import json

from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union
from photo_architecture import Facade, opening
from court_front import (BASE,COLUMN,DARK,DOOR,GLASS,GOLD,GREEN,METAL,PALETTE,
                        ROOF,STONE,TURQUOISE,WHITE,curved_light,main_front)

P=json.loads(Path(__file__).with_name('parameters.json').read_bytes())
HALF=P['main_width_m']/2
LENGTH=P['main_length_m']
EAVE=P['wall_parapet_m']
GROUND=.46
PLAN=[(-HALF,0),(-5.04,0),(-5.04,1.71),(5.04,1.71),(5.04,0),(HALF,0),
      (HALF,LENGTH),(3.45,LENGTH),(2.22,LENGTH+1.78),(.11,LENGTH+2.76),
      (-1.99,LENGTH+1.94),(-3.22,LENGTH),(-HALF,LENGTH)]
PLAN=Polygon(PLAN)


def course(f, silhouette, places, lod, material):
    surface=f.wall(0,EAVE,places,.38,material,outline=silhouette)
    p=surface.intersection(box(-f.length/2,0,f.length/2,.58))
    if not p.is_empty:f.prism(p,-.10,.089,BASE,'stone plinth')
    if not lod:
        beds=unary_union([box(-f.length/2,z-.012,f.length/2,z+.012)
                          for z in [i*.49 for i in range(2,25)]])
        joint=surface.intersection(beds)
        if not joint.is_empty:f.prism(joint,.002,.006,BASE,'rendered course cuts')


def circular_window(f, x, lod):
    eye=Point(x,7.61).buffer(.82,quad_segs=14 if lod else 28)
    f.prism(eye.buffer(.011),-.34,-.31,GLASS,'roundel glass')
    w=eye.buffer(-.095)
    bars=unary_union([box(x-.038,6.65,x+.038,8.59),box(x-1,7.57,x+1,7.65)])
    f.prism(eye.difference(w.difference(bars)),-.25,-.149,METAL,'roundel casement')
    f.prism(eye.buffer(.17).difference(eye),-.12,.119,STONE,'pale oculus ring')
    return eye


def east_corners(b,lod):
    for sign,label in [(-1,'south'),(1,'north')]:
        lo,hi=(-HALF,-5.04) if sign<0 else (5.04,HALF)
        f=Facade(b,(lo,0),(hi,0),'East/'+label+' corner')
        hole=circular_window(f,0,lod)
        surface=box(-f.length/2,0,f.length/2,EAVE)
        course(f,surface,[hole],lod,WHITE)
        green=box(-1.35,5.56,1.35,EAVE-.12)
        f.prism(green.difference(hole.buffer(.179)),-.045,.054,GREEN,'green roundel bay')
        for z,h,depth in ((4.75,.18,.18),(5.31,.29,.20),(5.55,.12,.30),(EAVE-.10,.2,.13)):
            f.beam(z,h,depth,STONE)
        for x in (-f.length/2+.17,f.length/2-.17):
            f.box(x,8.40,.28,6.20,.16,.06,WHITE,'tower corner arris')


def volume_walls(b,lod):
    corners=[(HALF,0),(HALF,LENGTH),(3.45,LENGTH),(2.22,LENGTH+1.78),(.11,LENGTH+2.76),
             (-1.99,LENGTH+1.94),(-3.22,LENGTH),(-HALF,LENGTH),(-HALF,0)]
    for n,(a,c) in enumerate(zip(corners,corners[1:])):
        f=Facade(b,a,c,'Peripheral hall/edge '+str(n+1))
        holes=[]
        # Only the visible window rhythm on the two long external walls is
        # approximated. The curved western projection retains its documented footprint.
        if n in (0,7):
            for u in (-5.32,0,5.32):
                hole=opening(u,6.60,1.62,3.14,.75,12 if lod else 22)
                f.window(hole,columns=2,rows=3,frame=METAL,trim=False,glass=GLASS,label='side upper light')
                holes.append(hole)
        course(f,box(-f.length/2,0,f.length/2,EAVE),holes,lod,WHITE)
        f.beam(5.40,.21,.09,STONE)
        f.beam(EAVE-.069,.142,.14,STONE)


def raised_turret(b,cx,cy,index,lod):
    size=4.12
    label='Roof/corner '+str(index)
    foot=box(cx-size/2,cy-size/2,cx+size/2,cy+size/2)
    b.plan_prism(foot.buffer(.08,join_style=2),11.42,11.72,STONE,label+' base')
    corners=list(foot.exterior.coords)
    if not foot.exterior.is_ccw:corners=list(reversed(corners))
    base_h=13.40
    for n,(a,c)in enumerate(zip(corners,corners[1:])):
        f=Facade(b,a,c,label+'/drum '+str(n+1))
        holes=[]
        for u in (-.68,.68):
            win=opening(u,11.81,.88,1.28,.43,9 if lod else 19)
            f.prism(win.buffer(.008,join_style=2),-.295,-.257,DARK,'louvred drum opening')
            f.prism(win.buffer(.085,join_style=2).difference(win),-.082,.065,STONE,'arch jamb')
            holes.append(win)
            for z in ([12.12,12.48]if lod else [12.02,12.22,12.42,12.62,12.77]):
                w=.72 if z<12.60 else .62
                f.box(u,z,w,.055,.060,-.211,METAL,'drum louvre')
        f.wall(11.68,base_h,holes,.21,WHITE)
        f.beam(base_h-.06,.15,.12,STONE)
        if index in (1,2) and abs(a[1]-c[1])<.01 and a[1] < cy:
            # The two courtyard towers have a shallow peaked coping in the 2015 oblique view.
            peak=Polygon([(-size/2,base_h-.04),(0,base_h+.50),(size/2,base_h-.04)])
            f.prism(peak,-.15,.07,WHITE,'shallow peaked gable')
            profile=LineString([(-size/2-.09,base_h-.03),(0,base_h+.55),(size/2+.09,base_h-.03)])
            f.prism(profile.buffer(.062,cap_style=2,join_style=2),-.14,.15,STONE,'peaked coping')
    b.plan_prism(foot.buffer(.155,join_style=2),base_h-.04,base_h+.13,STONE,label+' coping')
    r0=1.962
    cap=[]
    for i in range(9 if lod else 18):
        t=(pi/2)*i/(8 if lod else 17)
        cap.append((base_h+.13+1.77*sin(t),max(.012,r0*cos(t))))
    b.lathe((cx,cy),cap,TURQUOISE,20 if lod else 40,label+' turquoise dome')
    b.lathe((cx,cy),[(base_h+.06,2.02),(base_h+.16,2.02),(base_h+.20,1.94)],GREEN,
            20 if lod else 40,label+' spring band')


def lantern(b,lod):
    """Open pale pavilion, broad gold canopy and raised crescent from the 2014 dated view."""
    x0,y0=0.,12.16
    z0,z1=12.03,16.54
    rad=2.45
    octagon=Polygon([(x0+rad*cos(pi/8+i*tau/8),y0+rad*sin(pi/8+i*tau/8))for i in range(8)])
    b.plan_prism(octagon.buffer(.12,join_style=2),11.54,z0,STONE,'Lantern/octagonal plinth')
    for x,y in list(octagon.exterior.coords)[:-1]:
        b.box((x,y,z0+.095),(.48,.48,.19),STONE,label='Lantern/post foot')
        b.lathe((x,y),[(z0+.18,.198),(z0+.32,.185),(z1-.29,.161),(z1-.12,.205),(z1,.239)],
                WHITE,10 if lod else 18,'Lantern/open pale columns')
    b.plan_prism(octagon.buffer(.30,join_style=2),z1-.08,z1+.20,STONE,'Lantern/canopy cornice')
    profile=[(z1+.18,2.80),(z1+.27,2.78),(z1+.37,2.50),(z1+.66,2.30),
             (z1+1.08,2.01),(z1+1.44,1.61),(z1+1.77,.99),(18.55,.24)]
    b.lathe((x0,y0),profile,GOLD,24 if lod else 48,'Lantern/shallow gold canopy')
    if not lod:
        for n in range(8):
            a=n*tau/8+pi/8
            curve=[(x0+(r+.025)*cos(a),y0+(r+.025)*sin(a),z+.026)for z,r in profile[2:]]
            b.tube(curve,.025,GOLD,6,'Lantern/raised ribs')
    b.lathe((x0,y0),[(18.54,.20),(18.69,.27),(18.78,.28),(18.92,.16),(19.02,.09),
                      (19.16,.14),(19.28,.09),(22.88,.031),(23.02,.026)],GOLD,
            12 if lod else 22,'Lantern/knop and mast')
    moon=Point(0,23.075).buffer(.265,quad_segs=12 if lod else 22).difference(
        Point(.071,23.173).buffer(.223,quad_segs=12 if lod else 22))
    face=Facade(b,(-1.,y0),(1.,y0),'Lantern')
    face.prism(moon,-.036,.036,GOLD,'crescent')


def model(b,lod):
    b.plan_prism(PLAN,0,.47,BASE,'Base/western hall floor')
    main_front(b,lod)
    east_corners(b,lod)
    volume_walls(b,lod)
    roof=PLAN.union(box(-5.05,.15,5.05,2.1))
    b.plan_prism(roof.buffer(-.12,join_style=2),EAVE-.31,EAVE-.10,ROOF,'Roof/main hall deck')
    for i,(x,y)in enumerate([(-7.09,2.20),(7.09,2.20),(-6.38,20.13),(6.38,20.13)],1):
        raised_turret(b,x,y,i,lod)
    lantern(b,lod)
    assert all(len(part['label'].encode('utf-8'))<=63 for part in b.parts)
