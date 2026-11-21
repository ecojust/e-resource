"""Reconstruct both open storeys of the south garden loggia at 5 Dongping Road."""
from pathlib import Path
from math import cos, sin, pi
import argparse
import json
import os
import sys

from shapely.geometry import Polygon, box as rectangle

SOURCE = Path(__file__).resolve().parent
sys.path.insert(0, str(SOURCE.parents[3] / 'tools'))
import package_architectural_model as package
sys.path.insert(0, str(SOURCE.parents[1] / 'huangpu-somekh-building-street-corner/source'))
from aggregate_mesh import AggregateBuilder
from photo_architecture import Facade
from pebble_render import RENDER, assign_uvs

ID = 'xuhui-dongping-five-south-arcade'
META = dict(id=ID, name='东平路5号花园住宅南敞廊', viewer_page='dongping-five-south-arcade.html',
            heritage_group='4D015', heritage_address='东平路5号', status='documented-garden-arcade',
            scope='中央南敞廊、上下层栏杆、入口台阶和老虎窗。')
DIMS = json.loads((SOURCE.parent/'measurements/south-elevation-ratios.json').read_bytes())
photo = DIMS['direct_readings']
SCALE = DIMS['metres_per_pixel']
WHITE, STONE, BRICK = 'Warm white balusters', 'Cream rail ledges', 'Red quarry steps'
DARK, FASCIA, PIPE = 'Recessed gallery plaster', 'Dark timber and eaves', 'Cast iron rainwater goods'
REAR = json.loads((SOURCE.parent/'measurements/rear-gallery-readings.json').read_bytes())
PANEL = 'Blue-black gallery recesses'
JAMB = 'Shaded inner masonry'
ROOF, TILE, SHUTTER = 'Weathered red roof tiles', 'Rounded clay tile edges', 'Dormer shutter boards'


def srgb(rgb, roughness):
    def channel(i):
        value = i / 255
        return value / 12.92 if value < .04045 else ((value+.055) / 1.055)**2.4
    return dict(color=[channel(i) for i in rgb], roughness=roughness)


PALETTE = {RENDER: dict(color=[1,1,1], roughness=.93, texture=str(SOURCE/'pebble-render.png')),
           WHITE: srgb((225,222,208),.83), STONE: srgb((195,190,172),.82),
           BRICK: srgb((151,98,81),.82), DARK: srgb((94,90,79),.91),
           PANEL: srgb((30,33,35),.93), JAMB: srgb((62,60,52),.89),
           FASCIA: srgb((82,75,65),.77), PIPE: srgb((62,65,60),.64),
           ROOF: srgb((131,91,74),.87), TILE: srgb((155,105,84),.87),
           SHUTTER: srgb((97,91,80),.75)}


def x(pixel):
    return (pixel-photo['centre_x'])*SCALE


def z(pixel):
    return (photo['grade_y']-pixel)*SCALE


def opening(cx, width, spring, bottom, segments):
    radius = width/2
    cap = [(cx+radius*cos(i*pi/segments), spring+radius*sin(i*pi/segments))
           for i in range(segments+1)]
    return Polygon([(cx-radius,bottom),(cx+radius,bottom),*cap])


def railing(b, front, left, right, bottom, top, count, lod, label):
    """Turn each spindle on its own axis, leaving daylight between the profiles."""
    span = right-left
    u = (left+right)/2
    front.box(u,bottom+.052,span+.065,.104,.24,.034,STONE,label+'/Foot')
    front.box(u,top-.052,span+.06,.104,.22,.04,WHITE,label+'/Handrail')
    front.box(u,top-.121,span+.018,.038,.158,.038,WHITE,label+'/Underside moulding')
    shaft_height = top-bottom-.232
    step = span/count
    # Collar, rounded belly, pinched waist and bead can all be read against the dark gallery.
    profile = [(0,.055),(.06,.070),(.13,.061),(.21,.039),(.35,.044),(.48,.070),
               (.58,.073),(.69,.056),(.78,.038),(.87,.043),(.93,.061),(1,.054)]
    if lod:
        profile = [profile[i] for i in (0,1,3,5,6,8,10,11)]
    for i in range(count):
        xx = left+(i+.5)*step
        b.lathe((xx,-.04),[(bottom+.104+a*shaft_height,r)for a,r in profile],WHITE,
                8 if lod else 16,label+'/Turned balusters')


def upper_gallery(b, front, lod):
    spring=z(photo['upper_spring_y'])
    bottom=z(photo['upper_slab_y'])
    crown=z(photo['cornice_y'])
    centres=[x(v)for v in photo['upper_centres_x']]
    widths=[v*SCALE for v in photo['upper_diameters_px']]
    arches=[opening(cx,width,spring,spring-.08,12 if lod else 28) for cx,width in zip(centres,widths)]
    outline=rectangle(x(398),spring-.002,x(871),crown)
    front.wall(spring-.002,crown,arches,.34,RENDER,outline)
    # Four individual slender columns support the pointed spandrels between the five round openings.
    for i, (a,c) in enumerate(zip(centres,centres[1:])):
        cx=(a+c)/2
        label='Upper column '+str(i+1)
        radius=(c-a-(widths[i]+widths[i+1])/2)/2
        front.box(cx,bottom+.12,radius*2.2,.24,.345,0,WHITE,label+'/Plinth')
        profile=[(bottom+.20,radius*.98),(bottom+.28,radius*1.05),(bottom+.34,radius*.92),
                 (spring-.18,radius*.90),(spring-.15,radius*1.02),(spring-.115,radius*.97),
                 (spring-.065,radius*1.18),(spring-.015,radius*1.21)]
        b.lathe((cx,.105),profile,WHITE,12 if lod else 28,label+'/Tapered shaft')
        front.box(cx,spring-.024,radius*2.55,.048,.37,.011,WHITE,label+'/Square abacus')
    for edge,jamb in [(x(398),centres[0]-widths[0]/2),(centres[-1]+widths[-1]/2,x(871))]:
        front.box((edge+jamb)/2,(bottom+spring)/2,jamb-edge,spring-bottom,.34,-.17,RENDER,'Upper outer jambs')
    for i,(cx,width)in enumerate(zip(centres,widths)):
        railing(b,front,cx-width/2,cx+width/2,z(photo['railing_foot_y']),z(photo['railing_top_y']),7,lod,'Upper bay '+str(i+1))
    front.box(x(648),(bottom+z(343.5))/2,(835-457)*SCALE,z(343.5)-bottom,.42,.065,WHITE,'Upper continuous apron')
    front.box(x(648),bottom-.032,(843-452)*SCALE,.064,.50,.075,STONE,'Bullnose of upper slab')


def lower_gallery(b, front, lod):
    bottom=z(photo['porch_floor_y'])
    top=z(photo['upper_slab_y'])
    spring=z(photo['lower_spring_y'])
    centres=[x(v)for v in photo['lower_centres_x']]
    widths=[v*SCALE for v in photo['lower_openings_px']]
    arches=[opening(cx,width,spring,bottom-.012,14 if lod else 32)for cx,width in zip(centres,widths)]
    front.wall(bottom,top,arches,.34,RENDER,rectangle(x(398),bottom,x(871),top))
    gallery=DIMS['unseen_dimensions']['gallery_depth_m']
    # The red front coping and the cream gallery deck meet edge-to-edge on the entrance landing.
    joint = .215
    front.box(x(634.5),bottom-.065,(871-398)*SCALE,.13,gallery-joint,-(gallery+joint)/2,STONE,'Ground gallery floor')
    front.box(x(634.5),top-.065,(871-398)*SCALE,.13,gallery,-gallery/2,STONE,'Upper gallery floor')
    for i in (0,2):
        cc,ww=centres[i],widths[i]
        railing(b,front,cc-ww/2,cc+ww/2,bottom,z(470),10,lod,'Ground bay '+str(i+1))
    tread_width = DIMS['ground_step_width_m']
    left_edge,right_edge = centres[1]-tread_width/2,centres[1]+tread_width/2
    for a,c in [(x(398),left_edge),(right_edge,x(871))]:
        front.box((a+c)/2,(bottom-.154)/2,c-a,bottom-.154,.54,.055,RENDER,'Raised base')
        front.box((a+c)/2,bottom-.077,c-a,.154,.57,.070,BRICK,'Red base coping')
    front.box(centres[1],bottom-.065,tread_width,.13,joint,-joint/2,STONE,'Central entrance landing')
    # The front photo shows a break in the balustrade and shallow red treads at the central arch.
    for i in range(4):
        height=bottom*(4-i)/4
        front.box(centres[1],height/2,tread_width,height,.30,.15+i*.30,BRICK,'Red entrance treads')
    # The front openings reveal a second wall with distinct deep, dark openings and light piers.
    rear = Facade(b, (-7,gallery), (7,gallery), 'Recessed gallery')
    rectangles = []
    for floor, fields in REAR['visible_fields'].items():
        sill = z(REAR[floor+'_sill_y'])
        for i, field in enumerate(fields, 1):
            left,right = (x(px) for px in field['limits'])
            head = z(field['head'])
            rectangles.append(rectangle(left,sill,right,head))
            u = (left+right)/2
            label = f'{floor} inner bay {i}'
            recess = REAR['panel_recess_m']
            rear.box(u,(sill+head)/2,right-left+.012,head-sill+.012,.045,-recess-.0225,PANEL,label+'/Shaded field')
            for jamb in (left+.018,right-.018):
                rear.box(jamb,(sill+head)/2,.036,head-sill,recess,-recess/2,JAMB,label+'/Square reveal')
            rear.box(u,head-.022,right-left,.044,recess,-recess/2,JAMB,label+'/Recessed lintel')
    rear.wall(bottom,z(232),rectangles,.14,DARK,rectangle(x(398),bottom,x(871),z(232)))
    # The upper openings reveal the underside of the roof behind the front row of thin columns.
    front.box(x(634.5),z(235)+.045,(871-398)*SCALE,.09,gallery,-gallery/2,JAMB,'Upper gallery soffit')
    for u in (x(402),x(867)):
        front.box(u,(bottom+z(231))/2,.18,z(231)-bottom,gallery,-gallery/2,RENDER,'Sides of the projected loggia')


def roofs(b,front,lod):
    half=(871-398)*SCALE/2
    mid=x(634.5)
    eave=z(photo['cornice_y'])+.04
    depth=DIMS['unseen_dimensions']['roof_slope_depth_m']
    rise=z(photo['roof_ridge_y'])-eave
    # The two short sloping hips narrow the front tile surface at its high edge.
    outer,inner=half+.24,half-1.64
    def at(y):
        t=y/depth
        return outer+(inner-outer)*t, eave+t*rise
    def snap(a,c,y,height=0):
        width,h=at(y)
        return [(mid+a*width,y-.23,h+height),(mid+c*width,y-.23,h+height)]
    lo=snap(-1,1,0);hi=snap(-1,1,depth)
    bottom=[(xx,yy,zz-.13)for xx,yy,zz in [*lo,hi[1],hi[0]]]
    top=[*lo,hi[1],hi[0]]
    b.add([*bottom,*top],[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],ROOF,'Hipped front roof slope')
    front.box(mid,eave-.055,2*outer,.17,.34,.085,FASCIA,'Dark timber eave')
    # Tile crests follow the fall of the pitch. Course overlaps lie parallel to the eave.
    rows=9 if lod else 15
    for j in range(1,rows):
        y=depth*j/rows
        b.tube(snap(-1,1,y,.016),.015 if lod else .019,TILE,5 if lod else 7,'Clay tile courses')
    divisions=38 if lod else 63
    for k in range(1,divisions):
        a=-1+2*k/divisions
        b.tube([snap(a,a,0,.012)[0],snap(a,a,depth,.012)[0]],.012 if lod else .018,ROOF,5,'Raised tile ribs')
    # Low flat-capped dormer with recessed shaded shutter leaves in the red-tile slope.
    span=(690-566)*SCALE
    base=z(204);head=z(photo['dormer_head_y']);y=.97
    dorm_centre = x(633)
    dorm=Facade(b,(dorm_centre-span/2,y),(dorm_centre+span/2,y),'South dormer')
    aperture=rectangle(-.68,base-.005,.68,head-.25)
    dorm.wall(base,head,[aperture],.22,RENDER)
    dorm.box(0,(base+head-.25)/2,1.39,head-.25-base,.045,-.14,SHUTTER,'Recessed shutters')
    for i in range(3):
        u=-.68+(i+.5)*1.36/3
        for k in range(9 if lod else 15):
            h=base+.045+(k+.5)*(head-.31-base)/(9 if lod else 15)
            dorm.box(u,h,1.36/3-.044,.017,.035,-.104,FASCIA,'Shutter louvers')
    for u in (-.68,-.227,.227,.68):
        dorm.box(u,(base+head-.25)/2,.045,head-.25-base,.06,-.087,FASCIA,'Shutter stiles')
    for side in (-1,1):
        xx=side*(span/2-.07)
        dorm.box(xx,(base+head)/2,.14,head-base,.82,-.41,RENDER,'Dormer cheeks')
    dorm.box(0,head,span+.19,.105,1.06,-.38,FASCIA,'Overhanging dormer cap')
    dorm.box(0,head+.071,span+.23,.044,1.08,-.38,ROOF,'Tile edge over dormer')


def add_building(b,lod):
    f=Facade(b,(-7,0),(7,0),'South arcade')
    lower_gallery(b,f,lod)
    upper_gallery(b,f,lod)
    roofs(b,f,lod)
    for u in (x(440),x(851)):
        z0,z1=z(511),z(249)
        b.tube([(u,-.10,z0),(u,-.10,z1)],.047,PIPE,8 if lod else 16,'Pair of front downpipes')
        b.lathe((u,-.10),[(z1-.11,.055),(z1+.013,.13),(z1+.11,.14)],PIPE,8 if lod else 12,'Rainwater hoppers')
    assign_uvs(b)


if __name__=='__main__':
    parser=argparse.ArgumentParser(add_help=False)
    parser.add_argument('--blender',default='blender')
    args,extra=parser.parse_known_args()
    os.environ['DONGPING_ARCADE_BLENDER']=args.blender
    sys.argv[1:]=[*extra,'--blender',str(SOURCE/'native_blender.py')]
    package.Builder=AggregateBuilder
    package.build(SOURCE,META,PALETTE,add_building)
