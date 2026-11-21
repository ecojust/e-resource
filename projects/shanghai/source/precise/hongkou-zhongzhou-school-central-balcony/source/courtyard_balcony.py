"""The old Zhongzhou Road school's raised central balcony, based on its courtyard photographs."""
from math import sin, pi
from pathlib import Path
from random import Random
from PIL import Image, ImageDraw
from shapely.geometry import Polygon, box
from shapely.ops import unary_union

WALL = 'Pale mineral render'
CORNICE = 'Off-white cornice'
ROOF = 'Weathered gray roof tiles'
FLASH = 'Dark edge flashing'
GLASS = 'Dark window glass'
FRAME = 'Painted steel frame'
REVEAL = 'Recessed reveal'
RAIL = 'Pale balcony rail'
FASCIA = 'Reddish balcony fascia'
HOOD = 'Weathered lintel'
SILL = 'Painted sill'
PALETTE = {name: {'color': rgb, 'roughness': rough} for name, rgb, rough in [
    (WALL,[.89,.875,.83],.94), (CORNICE,[.95,.94,.90],.93),
    (ROOF,[.97,.97,.97],.94), (FLASH,[.255,.254,.26],.79),
    (GLASS,[.242,.281,.292],.35), (FRAME,[.405,.418,.415],.70),
    (REVEAL,[.475,.465,.435],.93), (RAIL,[.69,.69,.65],.66),
    (FASCIA,[.47,.359,.323],.88), (HOOD,[.53,.492,.46],.90), (SILL,[.74,.725,.68],.91)]}
UNIT = .0205
WINDOWS = [(79,127),(160,208),(340,386),(422,469)]
def xcoord(u):
    return (u-274)*UNIT
def zcoord(v):
    return (340-v)*UNIT
def xyz(u,v,forward):
    return xcoord(u),-forward,zcoord(v)
def rect(b,l,t,r,bottom,back,front,material,label):
    b.prism(box(xcoord(l),zcoord(bottom),xcoord(r),zcoord(t)),back,front,
            lambda x,z,d:(x,-d,z),material,label)

def texture(path):
    """Draw staggered courses, fine granular tile colour and transverse tile joints."""
    rng=Random(407)
    im=Image.new('RGB',(512,256),(83,82,82))
    pen=ImageDraw.Draw(im)
    for row,v in enumerate(range(-8,256,15)):
        for u in range(-19 if row%2 else -3,512,30):
            tone=rng.randint(-10,9)
            color=tuple(c+tone for c in (103,101,102))
            pen.rectangle((u+1,v+1,u+29,v+14),fill=color)
            pen.line((u+2,v+14,u+28,v+14),fill=tuple(c+5 for c in color))
            for _ in range(45):
                shift=rng.randint(-9,8)
                pen.point((u+rng.randint(2,28),v+rng.randint(2,13)),fill=tuple(c+shift for c in color))
    im.save(path)

def tile_strip(b,left,right,front_y,front_z,back_y,back_z,lod,label):
    """Slope toward the field. Close the underside and expose modeled, lapped course noses."""
    count=max(3,round((back_y-front_y)/.185))
    profile=lambda t: (front_y+(back_y-front_y)*t, front_z+(back_z-front_z)*t)
    for i in range(count):
        y0,z0=profile(i/count)
        y1,z1=profile((i+1)/count)
        outline=Polygon([(y0-.026,z0-.050),(y1,z1-.014),(y1,z1+.016),(y0-.026,z0+.024)])
        b.prism(outline,xcoord(left),xcoord(right),lambda y,z,x:(x,y,z),ROOF,label+' tile courses')
        if not lod:
            # The small staggered joints subdivide the surface without changing the course profile.
            pitch=.285
            offset=(i%2)*pitch*.5
            x=xcoord(left)+.10+offset
            while x<xcoord(right)-.035:
                joint=Polygon([(y0+.010,z0+.026),(y1-.008,z1+.019),(y1-.008,z1+.026),(y0+.010,z0+.033)])
                b.prism(joint,x,x+.009,lambda y,z,x:(x,y,z),FLASH,label+' tile joints')
                x+=pitch
    b.prism(Polygon([(front_y,front_z-.10),(back_y,back_z-.10),(back_y,back_z-.014),(front_y,front_z-.044)]),
            xcoord(left),xcoord(right),lambda y,z,x:(x,y,z),FLASH,label+' underside')
def glazed_window(b,l,r,index,lod):
    name=f'Classroom window {index}'
    t,base=222,275
    rect(b,l-.8,t-1.5,r+.8,base+1,-.145,-.115,REVEAL,name+' recessed return')
    # Three narrow lights and an upper row can be read in the 2017 image.
    rect(b,l+1.25,t+1.1,r-1.25,base-.8,-.108,-.099,GLASS,name+' glazing')
    for u in [l+1,l+(r-l)*.35,l+(r-l)*.68,r-1]:
        rect(b,u-.55,t+.45,u+.55,base-.3,-.107,-.058,FRAME,name+' vertical bars')
    for v in [t+.7,t+18.1,base-.9]:
        rect(b,l+.6,v-.65,r-.6,v+.65,-.105,-.052,FRAME,name+' horizontal bars')
    if not lod:
        for u in [l+.48,r-.48]:
            rect(b,u-.20,t,u+.20,base,-.067,-.043,REVEAL,name+' frame rebate')
    rect(b,l-2,base,r+2,base+2.3,-.11,.050,SILL,name+' projecting sill')
def add_building(b,lod):
    # The four fenestration bays and central opening are subtracted through the wall.
    wall=box(xcoord(66),zcoord(292),xcoord(480),zcoord(194)).difference(unary_union([
        box(xcoord(l),zcoord(275),xcoord(r),zcoord(222)) for l,r in WINDOWS]+[
        box(xcoord(235),zcoord(301),xcoord(311),zcoord(234))]))
    b.prism(wall,-.22,0.,lambda x,z,d:(x,-d,z),WALL,'Rendered wall with classroom and balcony recesses')
    for idx,(l,r) in enumerate(WINDOWS,1):
        glazed_window(b,l,r,idx,lod)
    for l,r in [(66,228),(319,480)]:
        rect(b,l,195,r,202,-.13,.118,FLASH,'Eaves shadow line')
        rect(b,l,201,r,208,-.15,.099,CORNICE,'Field-facing eaves fascia')
        tile_strip(b,l,r,-.118,zcoord(195),1.77,zcoord(117),lod,'Main pitched roof')
    # In the elevated photograph the long gray roof continues visibly behind
    # the small projecting cap. Its higher center ridge is distinct from that cap.
    tile_strip(b,227,320,.57,zcoord(166),1.77,zcoord(117),lod,'Roof behind central cap')
    rect(b,212,110,337,119,-1.86,-1.69,CORNICE,'Raised rear ridge undercap')
    tile_strip(b,214,335,1.65,zcoord(111),2.04,zcoord(99),lod,'Rear ridge cap')
    # The raised rectangular front meets each lower roof at its two shoulders.
    rect(b,211,166,337,214,-.33,.022,WALL,'Raised white central head')
    rect(b,201,160,347,170,-.42,.15,CORNICE,'Central cornice with underside')
    tile_strip(b,204,344,-.14,zcoord(160),.78,zcoord(136),lod,'Central short pitched cap')
    for l,r in [(201,206),(342,347)]:
        rect(b,l,135,r,161,-.76,-.48,FLASH,'Short cap edge return')
    # A shallow cap and projecting shelf frame a recessed pair of glazed leaves.
    rect(b,222,219,325,231,-.12,.205,HOOD,'Broad weathered door head')
    rect(b,225,229,322,232,-.115,.144,SILL,'Door-head underside')
    rect(b,235,234,311,300,-.27,-.22,REVEAL,'Paired doorway rear reveal')
    for l,r in [(236,272.9),(274.1,310)]:
        rect(b,l,236,r,298,-.212,-.18,GLASS,'Balcony door glazed leaf')
    for u in [235.5,273.5,310.5]:
        rect(b,u-.63,234,u+.63,300,-.182,-.128,FRAME,'Balcony door meeting stiles')
    for v in (235.5,296.5):
        rect(b,235,v-.65,311,v+.65,-.18,-.128,FRAME,'Door rails')
    rect(b,222,299,325,321,-.205,.570,FASCIA,'Red brown balcony front edge')
    rect(b,222,320,325,325,-.197,.536,FLASH,'Balcony underside')
    rect(b,223,325,324,328,-.11,.508,CORNICE,'Pale lower balcony edging')
    for v in [281.8,288,295.7]:
        rect(b,226,v-.57,321,v+.57,.535,.558,RAIL,'Balcony horizontal rails')
    for u in [226.4,320.6]:
        rect(b,u-.75,281,u+.75,299,.51,.56,RAIL,'Balcony end posts')
        for v in [282,288,295.7]:
            rect(b,u-.53,v-.51,u+.53,v+.51,-.004,.54,RAIL,'Short side rail return')
    b.palette[ROOF]['texture']=str(Path(__file__).with_name('gray-tiles.png'))
    for p in b.parts:
        if p['material']==ROOF:
            p['texcoords']=[[(x+4.70)/9.60,.97-(y+.18)/2.42]for x,y,z in p['vertices']]
