"""Entrance facing the circular garden of the former Gongda cotton mill residence."""
from pathlib import Path
from math import cos, sin, pi
import json
from shapely.geometry import Polygon, box
from shapely.ops import unary_union

STONE="sandstone tread"; RISER="grey step riser"; CREAM="cream plaster"; SHADE="warm shade"; DASH="grey pebble render"; GRIT="granite flecks"; TIMBER="umber door frame"; DARK="shadowed door"; IRON="iron stair rail"; RED="oxide rail finish"; GREEN="deep green enamel"; YELLOW="yellow enamel"; WHITE="ivory enamel"; GLASS="stairwell glass"; STEEL="oxide steel window"; SEAM="fine stone joint"
PALETTE={name:dict(color=value,roughness=r) for name,value,r in [
    (STONE,[.40,.385,.345],.93),(RISER,[.282,.290,.267],.94),(SEAM,[.235,.225,.207],.94),
    (CREAM,[.759,.704,.577],.86),(SHADE,[.565,.508,.407],.94),(DASH,[.209,.213,.189],.96),(GRIT,[.306,.294,.25],.99),
    (TIMBER,[.154,.072,.045],.82),(DARK,[.027,.033,.030],.81),(IRON,[.135,.105,.081],.76),(RED,[.397,.137,.084],.72),
    (GREEN,[.037,.145,.101],.53),(YELLOW,[.92,.63,.078],.59),(WHITE,[.806,.793,.636],.56),
    (GLASS,[.181,.244,.233],.44),(STEEL,[.262,.106,.066],.69)]}

def piece(b,x,y,z,w,d,h,mat,name):
    b.box((x,y,z),(w,d,h),mat,label=name)

def facade(b,poly,front,back,mat,name):
    if not poly.is_empty:
        b.prism(poly,-back,-front,lambda x,z,t:(x,-t,z),mat,label=name)

def shaft(b,x,y,rise,lod,side):
    """Three long cut grooves terminate below a separate shallow capital."""
    width=.38;foot=rise+.138;top=rise+2.615;lower=.119
    core=box(x-width/2,y-width/2,x+width/2,y+width/2)
    flute=[]
    for offset in (-.105,0,.105):
        radius=.022 if lod else .026
        from shapely.geometry import Point
        flute.append(Point(x+offset,y-width/2-.006).buffer(radius,quad_segs=3 if lod else 5))
        flute.append(Point(x+side*width/2+side*.006,y+offset).buffer(radius,quad_segs=3 if lod else 5))
    shank=core.difference(unary_union(flute))
    piece(b,x,y,rise+.045,.435,.435,.09,SHADE,'Square plinth')
    piece(b,x,y,rise+.114,.406,.407,.050,CREAM,'Second plinth course')
    b.plan_prism(core,foot,foot+lower,CREAM,'Plain foot of shaft')
    b.plan_prism(shank,foot+lower,top-.29,CREAM,'Fluted square shaft')
    b.plan_prism(core,top-.29,top-.24,CREAM,'Shaft neck')
    for dz,s,h in [(-.207,.410,.064),(-.112,.449,.128),(-.014,.484,.071)]:
        piece(b,x,y,top+dz,s,s,h,CREAM,'Stepped square capital')
    for dx in (-.126,-.065,.065,.126):
        piece(b,x+dx,y-.2265,top-.117,.021,.011,.115,SHADE,'Capital vertical cuts')

def model(b,lod=False):
    n=7;r=.153;t=.297;landing=n*r;first=-2.88;width=3.06
    for i in range(n):
        front=first+i*t;top=(i+1)*r
        piece(b,0,front+t/2,(top-.032)/2,width,t,top-.032,RISER,'Seven stone risers')
        piece(b,0,front+t/2-.013,top-.016,width+.024,t+.026,.032,STONE,'Projecting tread edges')
        if not lod:
            for dx in (-.82,.26):
                piece(b,dx+(.13 if i%2 else 0),front+t/2,top+.0007,.004,t-.018,.0014,SEAM,'Stone slab joints')
    yfront=first+n*t; back=.97
    piece(b,0,(yfront+back)/2,(landing-.03)/2,width,back-yfront,landing-.03,RISER,'Landing stone base')
    piece(b,0,(yfront+back)/2,landing-.015,width+.025,back-yfront+.025,.030,STONE,'Upper landing')
    for side in (-1,1):
        x=side*1.48
        for i in (0,3,6):
            yy=first+(i+.52)*t;z=(i+1)*r
            b.tube([(x,yy,z),(x,yy,z+.71)],.025,RED,sides=8 if lod else 14,label='Step rail uprights')
        for dz in (.42,.83):
            b.tube([(x,first+.03,r+dz),(x,yfront-.025,landing+dz)],.029,RED,sides=8 if lod else 16,label='Two sloping pipe rails')
        shaft(b,side*1.247,-.59,landing,lod,side)
        piece(b,side*1.255,.661,landing+1.293,.339,.212,2.586,CREAM,'Rear engaged pier')
        piece(b,side*1.25,.646,landing+2.600,.423,.252,.094,CREAM,'Rear capital')
    fascia=landing+2.68
    for side in (-1,1):
        piece(b,1.244*side,.035,fascia,.343,1.77,.149,SHADE,'Porch side beams')
    for y in (-.605,.672):
        piece(b,0,y,fascia,2.87,.356,.158,SHADE,'Lintels')
    for z,ww,dd,hh,mat in [(fascia+.115,3.33,2.15,.124,CREAM),(fascia+.207,3.56,2.25,.072,SHADE),(fascia+.276,3.65,2.31,.066,CREAM)]:
        piece(b,0,.005,z,ww,dd,hh,mat,'Projecting flat canopy courses')
    for x in (-1.23,-.79,.83,1.24):
        piece(b,x,-.985,fascia+.075,.249,.29,.107,CREAM,'Four paired canopy brackets')
        for dx in (-.075,0,.075):
            piece(b,x+dx,-1.017,fascia+.052,.033,.252,.096,SHADE,'Bracket under-ribs')
    # Continuous plaster facade surrounding the recessed entrance and stairwell window.
    door=box(-.728,landing-.018,.728,landing+2.37)
    sill=4.49;head=5.54
    opening=box(-.535,sill,.535,head)
    panel=box(-1.586,0,1.586,5.78).difference(unary_union([door,opening]))
    facade(b,panel,.765,1.03,DASH,'Pebbled wall with two apertures')
    # Project the original aggregate finish on the wall at its own facade coordinates.
    b.photograph_parts(Path(__file__).with_name('pebble-finish.png'),
                       lambda v:((v[0]+1.586)/3.172,1-v[2]/5.78),
                       lambda part:part['label']=='Pebbled wall with two apertures',
                       name=DASH,roughness=.96)
    if not lod:
        for side in (-1,1):
            for layer in range(15):
                width=.57
                piece(b,side*1.286,.759,.047+layer*.069,width,.009,.005,SEAM,'Plinth joints behind the columns')
    frame=box(-.718,landing,.718,landing+2.361).difference(box(-.616,landing-.02,.616,landing+2.241))
    facade(b,frame,.844,.999,TIMBER,'Recessed brown door jamb')
    piece(b,0,.992,landing+1.114,1.235,.044,2.228,DARK,'Inner dark door')
    for x in (-.43,-.29,-.14,0,.14,.29,.43):
        piece(b,x,.957,landing+1.26,.021,.020,.77,DARK,'Set-back door bars')
    for z in (landing+.86,landing+1.64):
        piece(b,0,.957,z,1.11,.022,.032,DARK,'Grille rails in doorway')
    for z in (sill-.034,head+.025):
        piece(b,0,.718,z,1.20,.23,.083,CREAM,'Stair window head and sill')
    pane=box(-.533,sill+.006,.533,head-.006)
    inside=pane.buffer(-.040,join_style=2)
    facade(b,pane.difference(inside),.784,.858,STEEL,'Upper red steel frame')
    facade(b,inside,.869,.887,GLASS,'Stairwell glazing')
    for x in (-.252,0,.252):
        piece(b,x,.826,(sill+head)/2,.023,.052,head-sill-.068,STEEL,'Four vertical lights')
    for z in (sill+.339,sill+.675):
        piece(b,0,.826,z,1.011,.052,.023,STEEL,'Three pane rows')
    # Measured against the independent close photograph of the same green address plate.
    xc=-.915;zc=landing+2.267;ww=.310;hh=.202
    plate=box(xc-ww/2+.007,zc-hh/2+.007,xc+ww/2-.007,zc+hh/2-.007).buffer(.007,quad_segs=3)
    facade(b,plate,.741,.762,GREEN,'Green enamel address plate')
    rim=plate.buffer(-.008).difference(plate.buffer(-.011));facade(b,rim,.739,.742,GREEN,'Pressed border on address plate')
    for g in json.loads(Path(__file__).with_name('plate-letters.json').read_bytes()):
        for rings in g['polygons']:
            poly=Polygon(rings[0],rings[1:]);facade(b,poly,.737,.740,YELLOW if g['text']=='特号'else WHITE,'Raised address lettering')
    for x in (xc-.141,xc+.141):
        for z in (zc-.085,zc+.085):
            b.tube([(x,.743,z),(x,.736,z)],.0054,IRON,sides=6 if lod else 12,label='Four address plate screws')
