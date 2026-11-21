"""Garden face of the thirteen-storey 1935 Gascogne Apartments on Huaihai Middle Road."""
import math
import sys
from pathlib import Path

from shapely.geometry import Polygon,box
from shapely.ops import unary_union

HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[3]
sys.path.insert(0,str(PROJECT/'source/precise/hongkou-general-post-office/source/common'))
from photo_architecture import Facade

TILE='honey buff facing tile'
GAP='fine sandy joints'
PALE='ivory balcony concrete'
WHITE='light cement fins'
DARK='polished charcoal stone'
STONE='pale granite steps'
METAL='steel sash and railing'
GLASS='smoky blue-green glass'
TOPLIGHT='frosted canopy glass'
GILT='brass emblem'
WELL='balcony recess'
CUT='neutral cut'
ROOF='flat grey roof'
def mat(col,rough=.8,metal=0):
    return dict(color=list(col),roughness=rough,metallic=metal)
PALETTE={TILE:mat((.673,.479,.304)),GAP:mat((.543,.422,.300)),PALE:mat((.846,.804,.715)),WHITE:mat((.853,.838,.771)),
    DARK:mat((.089,.103,.102),.40,.15),STONE:mat((.701,.675,.610)),METAL:mat((.128,.140,.141),.46,.38),
    GLASS:mat((.236,.329,.364),.27,.30),TOPLIGHT:mat((.551,.688,.701),.39,.23),GILT:mat((.714,.530,.222),.44,.53),
    WELL:mat((.589,.505,.419)),CUT:mat((.580,.555,.499)),ROOF:mat((.448,.438,.421))}
FRONT=-1.32
REAR=3.65
BASE=4.18
PITCH=3.79
WIDE=24.53
BALCONIES=[(-14.65,-10.16),(-10.16,-5.60),(5.60,10.16),(10.16,14.65)]
def sash(f,x,z,w,h,reduced,depth=.175,cols=4,group='casement'):
    f.box(x,z+h/2,w,h,.043,-depth,GLASS,group+' glass')
    count=max(2,cols-1) if reduced else cols
    for k in range(count+1):
        f.box(x-w/2+k*w/count,z+h/2,.054,h+.045,.065,-depth+.054,METAL,group+' steel mullions')
    for y in ([0,.73,1.0] if reduced else [0,.40,.755,1.0]):
        f.box(x,z+y*h,w+.044,.045,.065,-depth+.055,METAL,group+' horizontal sash')
    return box(x-w/2,z,x+w/2,z+h)

def front_panel(f,x0,x1,z,h,holes,material,reduced,group):
    face=box(x0,z,x1,z+h)
    if holes:face=face.difference(unary_union(holes))
    if face.area<=0:return
    f.prism(face,-.305,0,material,group)
    if material!=TILE:return
    # Narrow banded joints express the light face tile. Coarser LOD retains the larger floor seams.
    step=.36 if not reduced else 1.085
    for j in range(1,math.ceil(h/step)):
        y=z+j*step
        joints=face.intersection(box(x0,y-.0035,x1,y+.0035))
        if not joints.is_empty and joints.area>0:f.prism(joints,.0008,.0022,GAP,group+' tile bed joints')

def capsule(cx,cy,w,depth,n=10):
    # Long oval-ended garden steps, visible in both the frontal photograph and doorway close-up.
    r=depth*.5;left=cx-w*.5+r;right=cx+w*.5-r
    return Polygon([(right+r*math.cos(-math.pi/2+math.pi*j/n),cy+r*math.sin(-math.pi/2+math.pi*j/n))for j in range(n+1)]
        +[(left+r*math.cos(math.pi/2+math.pi*j/n),cy+r*math.sin(math.pi/2+math.pi*j/n))for j in range(n+1)])

def entrance(b,f,reduced):
    doors=[(-4.00,2.33),(4.00,2.33)]
    holes=[]
    for x,width in doors:
        bottom=.72;top=3.65
        holes.append(box(x-width/2,bottom,x+width/2,top))
        for side in (-1,1):
            f.box(x+side*(width/2+.19),(bottom+top)/2,.38,top-bottom+.22,.25,.065,WHITE,'pale stone entry jambs')
            f.box(x+side*(width/2-.039),(bottom+top)/2,.077,top-bottom,1.65,-.83,WELL,'doorway side returns')
        f.box(x,top+.13,width+.72,.26,.26,.07,WHITE,'entry lintels')
        f.box(x,bottom-.05,width,.1,1.63,-.82,STONE,'public entry threshold')
        f.box(x,(bottom+top)/2,width,top-bottom,.11,-1.72,CUT,'neutral interior cutoff')
        f.box(x,top+.004,width,.085,1.64,-.83,WHITE,'entry soffit')
    for x in [-20.4,-16.2,-12.05,-8.10,8.10,12.05,16.2,20.4]:
        holes.append(sash(f,x,1.36,3.37,1.97,reduced,cols=4,group='dark base window'))
    front_panel(f,-WIDE,WIDE,.055,BASE-.055,holes,DARK,reduced,'charcoal stone entrance plinth')
    for z in [1.15,2.34,3.53]:
        for lo,hi in [(-WIDE,-21.99),(-18.67,-17.92),(-14.49,-13.8),(-6.26,-5.65),(-2.50,2.50),(5.65,6.26),(17.92,18.67),(21.99,WIDE)]:
            f.box((lo+hi)/2,z,hi-lo,.014,.012,.006,GAP,'stone panel joints')
    # A round brass garden-side emblem occupies the black panel between the two openings.
    ring=[]
    for j in range(33):
        angle=j*math.tau/32;ring.append(f.point(.42*math.cos(angle),2.56+.49*math.sin(angle),.026))
    b.tube(ring,.033,GILT,6,'Entrance/emblem ring')
    for side in [-1,1]:
        for j in range(7):
            z=2.19+j*.086;x=side*(.08+.255*math.sin(math.pi*(j+1)/9))
            b.tube([f.point(x,z,.045),f.point(x+side*.083,z+.08,.046)],.031,GILT,5,'Entrance/abstract brass leaves')
    # Three glazed lights are visible under the canopy. The opaque rim and soffit have three real openings.
    canopy=capsule(0,FRONT-1.54,13.4,4.08,12)
    roof_glass=[]
    for x in (-4.05,0,4.05):
        pane=box(x-1.46,FRONT-2.72,x+1.46,FRONT-1.05);roof_glass.append(pane)
        b.prism(pane,3.94,3.99,lambda x,y,z:(x,y,z),TOPLIGHT,'Entrance/three frosted skylights')
        for n in range(4):
            b.box((x-1.46+n*.973,FRONT-1.885,3.915),(.053,1.69,.072),METAL,label='Entrance/skylight glazing bars')
        for y in (FRONT-2.72,FRONT-1.885,FRONT-1.05):
            b.box((x,y,3.915),(2.93,.050,.072),METAL,label='Entrance/skylight crossbars')
    b.prism(canopy.difference(unary_union(roof_glass)),3.845,4.255,lambda x,y,z:(x,y,z),PALE,'Entrance/rounded canopy')
    for j in range(5):
        top=.15*(j+1);depth=3.82-j*.31;shape=capsule(0,FRONT-depth/2+.39,13.38-j*.31,depth,12)
        b.prism(shape,top-.15,top,lambda x,y,z:(x,y,z),STONE,'Entrance/five graduated stone treads')

def frontage(b,f,reduced):
    for j in range(11):
        z=BASE+j*PITCH
        half=WIDE if j<8 else (21.68 if j<10 else 17.83)
        windows=[]
        for side in (-1,1):
            windows.append(sash(f,side*3.76,z+.90,2.75,1.80,reduced,cols=4))
            outer=side*(17.67 if j<10 else 16.24)
            width=3.12 if j<10 else 2.37
            windows.append(sash(f,outer,z+.90,width,1.80,reduced,cols=4))
            if j<8:windows.append(sash(f,side*22.09,z+1.02,1.88,1.65,reduced,cols=3))
        for k,(lo,hi) in enumerate(BALCONIES):
            cx=(lo+hi)*.5;width=hi-lo
            # Each pair has a full-depth pier, floor slab, open throat and recessed glass doors.
            opening=box(lo+.10,z+.125,hi-.10,z+PITCH-.10);windows.append(opening)
            f.box(cx,z+.09,width-.01,.18,1.79,-.69,PALE,'projecting balcony slab')
            f.box(cx,z+.33,width-.02,.49,.19,.16,PALE,'ivory solid balcony edge')
            for rail in (.68,.88,1.065):
                f.box(cx,z+rail,width-.06,.035,.065,.196,METAL,'horizontal balcony rails')
            for t in range(4 if reduced else 6):
                cnt=3 if reduced else 5
                x=lo+.09+(width-.18)*t/cnt
                f.box(x,z+.803,.026,.535,.048,.194,METAL,'balcony rail uprights')
            inner=Facade(b,(lo+.11,FRONT+1.68),(hi-.11,FRONT+1.68),'Loggia backing')
            back_open=sash(inner,.02,z+.32,width-1.0,2.22,reduced,depth=.105,cols=3)
            inner.wall(z+.13,z+PITCH-.08,[back_open],.18,WELL)
            for edge in (lo,hi):f.box(edge,z+PITCH*.50,.18,PITCH+.008,1.83,-.70,PALE,'deep white balcony piers')
        front_panel(f,-half,half,z,PITCH,windows,TILE,reduced,'residential tile panels')
        for side in (-1,1):
            side_x=side*half
            b.box((side_x,FRONT+1.63,z+PITCH/2),(.20,3.23,PITCH),TILE,label='Garden front/short return on end wing')
        b.box((0,REAR-.08,z+PITCH/2),(2*half-.1,.14,PITCH),CUT,label='Garden front/neutral back section')
        if j in (7,9,10):
            b.box((0,(FRONT+REAR)/2,z+PITCH-.065),(half*2,REAR-FRONT,.13),ROOF,label='Garden front/stepped terrace strip')
    roofbase=BASE+11*PITCH
    # The crown rises above the last occupied window strip and its narrow side terraces.
    for width,z,h,glazed in [(18.2,roofbase,3.44,True),(9.25,roofbase+3.44,2.62,False)]:
        holes=[]
        if glazed:
            for x in (-6.42,6.42):
                holes.append(sash(f,x,z+.88,3.73,1.55,reduced,cols=5,group='upper terrace band'))
        front_panel(f,-width/2,width/2,z,h,holes,TILE,reduced,'upper setback facing')
        b.box((0,(FRONT+REAR)/2,z+h-.1),(width,REAR-FRONT,.20),ROOF,label='Crown/flat roof')
        for side in (-1,1):
            b.box((side*width/2,FRONT+2.48,z+h/2),(.18,4.95,h),TILE,label='Crown/short end return')
        b.box((0,REAR-.08,z+h/2),(width,.15,h),CUT,label='Crown/neutral back cut')
    crown=roofbase+3.44+2.62
    for x in (-.91,0,.91):
        f.box(x,(BASE+crown+.58)/2,.40,crown+.58-BASE,.38,.17,WHITE,'three continuous central fins')
    for z in [crown-1.10,crown-.75,crown-.40]:
        f.box(0,z,4.04,.175,.66,.30,WHITE,'three projecting crown bands')
    for side in (-1,1):
        # The circular outline of the canopy and classic curved end-wall detail are visible from the court.
        f.box(side*15.00,BASE+PITCH*5.50,.26,PITCH*11,.32,.04,PALE,'outer balcony jamb')
    for x in (-17.0,17.):
        b.box((x,(FRONT+REAR)/2,BASE-.07),(12.0,REAR-FRONT,.15),ROOF,label='Garden front/ground floor slab')

def build_apartments(b,reduced):
    f=Facade(b,(-WIDE,FRONT),(WIDE,FRONT),'South elevation')
    entrance(b,f,reduced)
    frontage(b,f,reduced)
    for side in [-1,1]:
        b.box((side*WIDE,(FRONT+REAR)/2,BASE/2),(.15,REAR-FRONT,BASE),DARK,label='Entrance/short side return')
    b.box((0,REAR-.08,BASE/2),(2*WIDE,.16,BASE),CUT,label='Entrance/neutral back cut')
