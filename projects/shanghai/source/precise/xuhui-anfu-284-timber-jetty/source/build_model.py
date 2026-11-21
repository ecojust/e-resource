"""The projecting half-timbered bay of the historic garden residence at 284 Anfu Road."""
from pathlib import Path
from math import hypot
import argparse
import json
import os
import sys

from shapely.geometry import Polygon, box as rectangle

SOURCE = Path(__file__).resolve().parent
sys.path.insert(0, str(SOURCE.parents[3]/'tools'))
import package_architectural_model as package
sys.path.insert(0, str(SOURCE.parents[1]/'huangpu-somekh-building-street-corner/source'))
from aggregate_mesh import AggregateBuilder
from photo_architecture import Facade
from washed_pebbles import STONE, texture_coordinates

ID = 'xuhui-anfu-284-timber-jetty'
META = dict(id=ID, name='安福路284号花园住宅露木构悬挑窗楼', viewer_page='anfu-284-timber-jetty.html',
            heritage_group='4D019', heritage_address='安福路284号', status='documented-half-timbered-jetty',
            scope='面向花园山墙侧面的红色露木构、悬挑托木和相邻一组成对窗。')
DIMENSIONS = json.loads((SOURCE.parent/'measurements/two-face-proportions.json').read_bytes())['adopted_m']
WIDTH = DIMENSIONS['east_panel_width']
RETURN = DIMENSIONS['return_depth']
BASE = DIMENSIONS['projected_footing_above_ground']
STOREY = DIMENSIONS['lower_timber_panel_height']
LOWER_RAIL_HEIGHT = json.loads((SOURCE.parent/'measurements/red-rail-height.json').read_bytes())['adopted_ratio_above_footing']
SASH_STUDY = json.loads((SOURCE.parent/'measurements/adjacent-sashes.json').read_bytes())['adopted_m']
RAIL = 'Oxide red rails'
POST = 'Weathered chestnut studs'
END = 'Dark timber end grain'
SHADOW = 'Warm shaded plaster'
PATCH = 'Pale repaired infill'
SILL = 'Grey stone window sills'
SASH = 'Red brown sash frames'
GLASS = 'Grey green glass'
SKY = 'Pale reflected sky'
EAVE = 'Dark brown roof verge'
CLAY = 'Rough red tile'


def pigment(rgb,roughness,metallic=0):
    def convert(channel):
        n=channel/255
        return n/12.92 if n<=.04045 else ((n+.055)/1.055)**2.4
    return dict(color=[convert(channel)for channel in rgb],roughness=roughness,metallic=metallic)


PALETTE = {STONE:dict(color=[1,1,1],roughness=.93,texture=str(SOURCE/'washed-pebbles.png')),
           RAIL:pigment((136,83,68),.78),POST:pigment((149,94,77),.82),END:pigment((99,61,51),.85),
           SHADOW:pigment((103,99,86),.93),PATCH:pigment((167,163,139),.91),
           SILL:pigment((164,160,146),.85),SASH:pigment((111,73,63),.63),
           GLASS:pigment((110,119,113),.33,.16),SKY:pigment((145,146,128),.35,.14),
           EAVE:pigment((78,67,57),.88),CLAY:pigment((147,98,79),.94)}


def brace(face, a, b, width, material, label, depth=.068):
    """Square-ended solid planks set slightly proud of the stone infill."""
    ax,az=a;bx,bz=b
    length=hypot(bx-ax,bz-az)
    u,z=-(bz-az)*width/(2*length),(bx-ax)*width/(2*length)
    face.prism(Polygon([(ax+u,az+z),(ax-u,az-z),(bx-u,bz-z),(bx+u,bz+z)]),.004,depth,material,label)


def lower_frame(face, bays, is_long):
    lo,hi=BASE,BASE+STOREY
    half=face.length/2
    face.prism(rectangle(-half,lo,half,hi),-.095,0,STONE,'Lower pebble panels')
    step=face.length/bays
    mid=lo+LOWER_RAIL_HEIGHT*STOREY
    for i in range(bays+1):
        u=-half+i*step
        width=.116 if i in (0,bays) else .077
        face.box(u,(lo+hi)/2,width,hi-lo,.079,.042,POST,'Lower upright studs')
    for h,width in ((lo+.035,.105),(mid,.089),(hi-.018,.129)):
        face.box(0,h,face.length+.085,width,.096,.054,RAIL,'Lower continuous red rails')
    if is_long:
        brace(face,(-half+.073,lo+.11),(-half+1.75*step,mid-.035),.095,RAIL,'Lower rising diagonal')
        brace(face,(half-1.78*step,mid-.035),(half-.065,lo+.11),.09,RAIL,'Lower falling diagonal')
    face.box(0,lo-.069,face.length+.12,.10,.125,.058,END,'Shadow at supporting beam')
    face.box(0,lo-.174,face.length+.13,.127,.14,.063,RAIL,'Exposed floor beam')


def verge_height(u):
    # The close elevation shows the eave rising across the bay towards its right-hand roof ridge.
    left,right = (SASH_STUDY[k] for k in ('left_underside_above_storey_band','right_underside_above_storey_band'))
    return BASE+STOREY+left+(u/WIDTH+.5)*(right-left)


def upper_frame(face,is_long):
    lo=BASE+STOREY-.015
    half=face.length/2
    heights=[verge_height(-WIDTH/2),verge_height(WIDTH/2)] if is_long else [verge_height(-WIDTH/2)]*2
    poly=Polygon([(-half,lo),(half,lo),(half,heights[1]),(-half,heights[0])])
    face.prism(poly,-.095,0,STONE,'Upper pebble panels')
    bays=5 if is_long else 3
    spacing=face.length/bays
    crossbar=BASE+STOREY+SASH_STUDY['mid_rail_above_storey_band']
    plate=BASE+STOREY+SASH_STUDY['upper_plate_above_storey_band']
    if is_long:
        # A lighter infill panel is visible under the third brace; it has no glazing bars.
        left=-half+3*spacing
        face.box(left+spacing/2,(lo+crossbar)/2,spacing-.06,crossbar-lo-.06,.024,.008,PATCH,'Pale upper infill')
    for i in range(bays+1):
        at=i/bays
        h=min(plate,heights[0]*(1-at)+heights[1]*at)
        face.box(-half+at*face.length,(lo+h)/2,.10 if i in (0,bays)else .080,h-lo,.076,.041,POST,'Upper framing studs')
    face.box(0,crossbar,face.length+.04,.087,.083,.049,RAIL,'Upper mid rail')
    if is_long:
        brace(face,(-half+.058,lo+.03),(-half+spacing,crossbar),.083,RAIL,'Upper left diagonal')
        brace(face,(half-2*spacing,plate-.085),(half-spacing,crossbar),.086,RAIL,'Upper right diagonal over rail')
        brace(face,(half-spacing,crossbar),(half-.05,lo+.05),.086,RAIL,'Upper right diagonal below rail')
        # A second plate crosses the gable below the exposed rafter feet.
        start=-half+(plate-heights[0])/(heights[1]-heights[0])*face.length
        face.box((start+half)/2,plate,half-start,.115,.085,.045,RAIL,'Gable wall plate')
        for fraction in (.82,1.):
            u=-half+fraction*face.length
            top=verge_height(u)
            face.box(u,(plate+top)/2,.085,top-plate,.076,.041,POST,'Upper gable studs')
    brace(face,(-half-.070,heights[0]),(half+.070,heights[1]),.12,EAVE,'Dark overhanging verge',.15)
    brace(face,(-half-.082,heights[0]+.075),(half+.082,heights[1]+.075),.044,CLAY,'Reddish edge tile',.17)


def floor_structure(b):
    """Expose the joists and the curved bearing under the photographed corner."""
    b.box((0,-RETURN/2,BASE-.10),(WIDTH+.08,RETURN+.06,.095),END,label='Boarded soffit')
    for i in range(7):
        xx=-WIDTH/2+i*WIDTH/6
        b.box((xx,-RETURN/2,BASE-.201),(.087,RETURN+.11,.135),RAIL,label='Exposed short joists')
        b.box((xx,-RETURN-.050,BASE-.201),(.082,.016,.126),END,label='Joist end grain')
    # In the y,z section a concave cut runs from the short nose down and back to the wall.
    depth=RETURN
    top=BASE-.231
    points=[(-depth+.08,top),(.03,top),(.03,top-.86),(-.11,top-.86)]
    for i in range(1,18):
        t=i/17
        y=(1-t)**2*(-.11)+2*(1-t)*t*(-.20)+t*t*(-depth+.08)
        z=(1-t)**2*(top-.86)+2*(1-t)*t*(top-.21)+t*t*(top-.095)
        points.append((y,z))
    b.prism(Polygon(points),-WIDTH/2+.01,-WIDTH/2+.168,lambda y,z,x:(x,y,z),RAIL,'Carved south corner bracket')
    b.box((-WIDTH/2+.092,-.055,top-.44),(.205,.11,.92),END,label='Wall block behind bracket')


def window_pair(face,low,high,lod,label,transom):
    width = SASH_STUDY['window_width']
    rows=5
    for side in (-1,1):
        mid=side*SASH_STUDY['centre_spacing']/2
        sash_top=high-.21 if transom else high
        face.box(mid,(low+high)/2,width+.016,high-low+.016,.04,-.205,GLASS,label+'/Rear glass')
        for col in range(4):
            u=mid-width/2+(col+.5)*width/4
            for row in range(rows):
                bottom=low+row*(sash_top-low)/rows
                height=(sash_top-low)/rows
                face.box(u,bottom+height/2,width/4,height,.016,-.175,SKY if (col+row)%7==1 else GLASS,label+'/Window lights')
            if transom:
                face.box(u,(high+sash_top)/2,width/4,high-sash_top,.016,-.178,GLASS,label+'/Top lights')
        for i in range(5):
            u=mid-width/2+i*width/4
            rail=.048 if i in (0,2,4) else .024
            face.box(u,(low+high)/2,rail,high-low,.072,-.12,SASH,label+'/Mullions')
        levels=[low+i*(sash_top-low)/rows for i in range(rows+1)]
        if transom: levels.append(high)
        for height in levels:
            rail=.049 if height in (low,sash_top,high) else .022
            face.box(mid,height,width,rail,.076,-.12,SASH,label+'/Glazing rails')
    overall=width+SASH_STUDY['centre_spacing']+.19
    face.box(0,low-.041,overall,.082,.30,.035,SILL,label+'/Projecting sill')
    face.box(0,high+.064,overall,.09,.31,.035,SILL,label+'/Stone head')


def roof_edge(b,lod):
    half=WIDTH/2
    xmin,xmax=-half-.10,half+.10
    front,back=-RETURN-.155,.16
    top=[(xx,yy,verge_height(xx)+.14)for xx,yy in [(xmin,front),(xmax,front),(xmax,back),(xmin,back)]]
    under=[(xx,yy,zz-.12)for xx,yy,zz in top]
    b.add(under+top,[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],CLAY,'Short slope above the jetty')
    for i in range(6 if lod else 11):
        t=(i+.4)/(6 if lod else 11)
        xx=xmin+t*(xmax-xmin);h=verge_height(xx)+.15
        b.tube([(xx,front,h),(xx,back,h)],.016,CLAY,5 if lod else 8,'Visible tile laps')

def add_building(b,lod):
    half=WIDTH/2
    front=Facade(b,(-half,-RETURN),(half,-RETURN),'East face of timber bay')
    end=Facade(b,(-half,0),(-half,-RETURN),'Garden return')
    lower_frame(front,7,True);lower_frame(end,3,False)
    upper_frame(front,True);upper_frame(end,False)
    floor_structure(b)
    roof_edge(b,lod)
    b.box((0,.14,BASE/2),(WIDTH+.05,.28,BASE),STONE,label='Pebble plaster below the projection')
    b.box((0,-.034,.087),(WIDTH+.07,.11,.174),SILL,label='Side wall plinth')
    # The photo gives three pairs on the adjacent wall. Only the near stack is included.
    # The datum crosses the joint without a return. Both photographs place the window stack on this plane.
    axis=SASH_STUDY['first_bay_axis_right_of_timber']
    side=Facade(b,(half,-RETURN),(half+2*axis,-RETURN),'Paired windows beside jetty')
    levels=SASH_STUDY['levels_sill_head']
    width=SASH_STUDY['window_width'];spacing=SASH_STUDY['centre_spacing']
    holes=[rectangle(cx-width/2,lo,cx+width/2,hi) for lo,hi in levels for cx in(-spacing/2,spacing/2)]
    h=BASE+STOREY+SASH_STUDY['upper_plate_above_storey_band']
    side.wall(0,h+.57,holes,.29,STONE)
    for i,(low,high) in enumerate(levels):
        window_pair(side,low,high,lod,'Pair '+str(i+1),i==1)
    side.box(0,h,2*axis,.115,.085,.045,RAIL,'Plate over adjacent paired windows')
    for u in (-axis+.18,-axis+.87,-axis+1.55):
        side.box(u,h+.288,.08,.57,.076,.041,POST,'Exposed studs over paired sashes')
    # The recessed wall below the jetty closes against the neighbouring masonry wall at the right-hand end.
    cheek=Facade(b,(half,0),(half,-RETURN),'Recess under jetty')
    cheek.wall(0,BASE,(),.12,STONE)
    # Terminate the clipped timber bay on its recessed side and opaque back.
    back=Facade(b,(half,0),(-half,0),'Back of modelled jetty')
    back.prism(Polygon([(-half,BASE),(half,BASE),(half,verge_height(-half)),(-half,verge_height(half))]),
               -.035,0,SHADOW,'Terminating wall')
    other=Facade(b,(half,-RETURN),(half,0),'Far cheek')
    other.prism(rectangle(-RETURN/2,BASE,RETURN/2,verge_height(half)),-.065,0,STONE,'Recessed end')
    texture_coordinates(b)


if __name__=='__main__':
    parser=argparse.ArgumentParser(add_help=False)
    parser.add_argument('--blender',default='blender')
    args,extra=parser.parse_known_args()
    os.environ['ANFU_JETTY_BLENDER']=args.blender
    sys.argv[1:]=[*extra,'--blender',str(SOURCE/'native_blender.py')]
    package.Builder=AggregateBuilder
    package.build(SOURCE,META,PALETTE,add_building)
