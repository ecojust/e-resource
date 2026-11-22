"""Rendered projecting porch over the entrance at No. 10, Lane 18 Yanqing Road."""
from pathlib import Path
import numpy as np
from PIL import Image
from shapely.geometry import box, Polygon, Point, LineString
PEBBLE='Pebble-textured grey render';EDGE='Darker edge of console';SOFFIT='Slate-grey canopy soffit'
WALL='Sand-coloured facade';BAND='Lines in facade render';WOOD='Dark red-brown entrance door';PANEL='Inset door panel'
EYE='Circular end of console';LINE='Narrow raised console moulding';REVEAL='Recessed shaded reveal'
ID='xuhui-yanqing-lane18-curved-entrance-canopy'
PALETTE={name:dict(color=colour,roughness=roughness) for name,colour,roughness in [
 (PEBBLE,[1,1,1],.93),(EDGE,[.39,.375,.35],.94),(SOFFIT,[.50,.483,.458],.91),
 (WALL,[.685,.648,.598],.94),(BAND,[.54,.511,.466],.96),(WOOD,[.235,.139,.126],.79),
 (PANEL,[.196,.113,.111],.82),(EYE,[.37,.381,.37],.87),(LINE,[.581,.554,.516],.89),(REVEAL,[.385,.352,.307],.94)]}
CENTRES=(-.779,.779)
def texture():
    p=Path(__file__).with_name('speckled-grey-render.png')
    if not p.exists():
        g=np.random.default_rng(783);arr=np.array([143,140,130])+g.standard_t(5,(320,320,1))*7
        Image.fromarray(arr.clip(0,255).astype('uint8')).quantize(112).save(p)
    PALETTE[PEBBLE]['texture']=str(p)
def curve(points,count):
    a,b,c,d=np.asarray(points,float);t=np.linspace(0,1,count)[:,None]
    return list(map(tuple,(1-t)**3*a+3*(1-t)**2*t*b+3*(1-t)*t*t*c+t**3*d))
def outline(far):
    n=13 if far else 34
    bottom=curve([(.06,.87),(.09,1.42),(.12,1.83),(.43,2.028)],n)
    bottom+=curve([(.43,2.028),(.71,2.182),(1.054,2.164),(1.194,2.279)],n)[1:]
    bottom+=curve([(1.194,2.279),(1.296,2.367),(1.263,2.515),(1.159,2.559)],n)[1:]
    return Polygon([(-.057,.87),*bottom,(0,2.56),(-.057,2.56)]),bottom
def add_building(b,far=False):
    texture()
    def front(poly,lo,hi,material,name):
        b.prism(poly,lo,hi,lambda x,z,d:(x,-d,z),material,name)
    def rect(l,r,z,t,lo,hi,mat,name):front(box(l,z,r,t),lo,hi,mat,name)
    opening=box(-.584,-.01,.584,2.15)
    front(box(-1.2,0,1.2,2.91).difference(opening),-.193,0,WALL,'Visible strip of roughcast facade')
    for z in [.52,1.05,1.60,2.12,2.67]:
        front(box(-1.2,z,1.2,z+.011).difference(opening),0,.005,BAND,'Horizontal line in rendered wall')
    rect(-.584,-.513,0,2.15,-.168,.001,REVEAL,'Shadowed left door reveal')
    rect(.513,.584,0,2.15,-.168,.001,REVEAL,'Shadowed right door reveal')
    rect(-.584,.584,2.05,2.15,-.158,-.002,REVEAL,'Entrance lintel soffit')
    rect(-.516,.516,0,2.061,-.20,-.145,WOOD,'Portion of red-brown door seen behind supports')
    for x in [-.253,.253]:
        rect(x-.204,x+.204,1.45,1.92,-.144,-.140,PANEL,'Inset top panel')
    body,bottom=outline(far)
    for x in CENTRES:
        # Profile in projection and height. Its normal points toward negative X.
        def side(poly,xmin,xmax,material,name):
            b.prism(poly,-xmax,-xmin,lambda p,z,t:(-t,-p,z),material,name)
        side(body,x-.095,x+.095,PEBBLE,'Curved console thickening into the entrance pier')
        for sign in [-1,1]:
            lo,hi=sorted([x+sign*.097,x+sign*.110])
            shape=body.intersection(LineString(bottom).buffer(.033,resolution=4 if far else 8))
            side(shape,lo,hi,LINE,'Raised moulding tracing the curved lower edge')
            eye=Point(1.096,2.402).buffer(.096,resolution=9 if far else 22)
            side(eye,lo,hi,EDGE,'Circular end relief at canopy')
            lo,hi=sorted([x+sign*.110,x+sign*.120])
            side(Point(1.096,2.402).buffer(.071,resolution=8 if far else 20),lo,hi,EYE,'Circular recessed face')
        rect(x-.112,x+.112,0,.966,-.036,.070,PEBBLE,'Lower part of vertical support')
    deck=box(-.946,-1.27,.946,.04).buffer(.045,resolution=3 if far else 12)
    b.plan_prism(deck,2.556,2.602,SOFFIT,'Underside of projecting roof')
    b.plan_prism(deck.buffer(.015,resolution=3 if far else 10),2.602,2.704,PEBBLE,'Heavy flat edge of projecting roof')
    b.plan_prism(deck.buffer(.009,resolution=3 if far else 10),2.704,2.725,EDGE,'Top weathering surface')
    for p in b.parts:
        if p['material']==PEBBLE:
            p['texcoords']=[[(x+.69*y)/.53,(z+.33*y)/.53] for x,y,z in p['vertices']]
