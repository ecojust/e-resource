"""The convex apartment and bank frontage between Nanjing West, Shimen First and Wujiang roads."""
from pathlib import Path
from functools import lru_cache
from math import pi,cos,sin
import numpy as np
from shapely.geometry import Polygon,box,Point
from shapely.ops import unary_union
from scipy.interpolate import PchipInterpolator
from photo_architecture import Facade
from sign_lettering import add_facade_lettering

BRICK='brown ceramic face brick';RED='umber facing tile';BUFF='ochre mottled tile';JOINT='recessed brown mortar'
BAND='aged concrete ribbon';STONE='granite bank base';GLASS='green grey apartment glass';SASH='steel casements'
GRILLE='dark metal grille';AW='weathered metal shades';ROOF='flat roof covering';GOLD='bronze name characters';SIGN='bank sign metal';LETTER='red bank marks'
PALETTE={BRICK:dict(color=[.366,.228,.140],roughness=.87),RED:dict(color=[.310,.179,.109],roughness=.86),BUFF:dict(color=[.463,.310,.184],roughness=.85),
 JOINT:dict(color=[.270,.205,.157],roughness=.89),BAND:dict(color=[.527,.478,.382],roughness=.79),STONE:dict(color=[.481,.440,.359],roughness=.81),
 GLASS:dict(color=[.173,.237,.232],metallic=.17,roughness=.29),SASH:dict(color=[.272,.277,.248],metallic=.33,roughness=.55),
 GRILLE:dict(color=[.114,.113,.091],metallic=.36,roughness=.55),AW:dict(color=[.495,.455,.372],metallic=.18,roughness=.69),ROOF:dict(color=[.365,.360,.311],roughness=.91),
 GOLD:dict(color=[.679,.526,.259],metallic=.48,roughness=.47),SIGN:dict(color=[.211,.204,.178],metallic=.25,roughness=.54),LETTER:dict(color=[.410,.075,.066],roughness=.6)}
FONT=Path(__file__).with_name('fonts')/'YatesStreetSigns.otf'
# Control points run from the Wujiang Road end to the Nanjing West Road end in the true owner frame.
ARC=np.array([(-17.40,6.73),(-17.57,.26),(-15.39,-4.50),(-11.26,-7.54),(-7.38,-8.70),(.85,-9.01),(9.48,-6.87),(13.94,-4.39),(17.19,-.83),(19.28,2.61),(19.55,6.70)])
PARAM=np.concatenate(([0.],np.cumsum(np.linalg.norm(np.diff(ARC,axis=0),axis=1))));SPLINE=PchipInterpolator(PARAM,ARC,axis=0);DERIV=SPLINE.derivative()
LENGTH=float(PARAM[-1]);START=1.12;FINISH=LENGTH-2.20;BAYS=17;PITCH=(FINISH-START)/BAYS;TOP=29.52
LEVELS=[4.68+3.02*j for j in range(8)]

@lru_cache(maxsize=45000)
def point_at(s,d=0):
    p=SPLINE(s);t=DERIV(s);n=np.array([t[1],-t[0]])/np.linalg.norm(t);return p+n*d


class Bay:
    def __init__(self,b,lo,hi,label):self.b=b;self.lo=lo;self.hi=hi;self.mid=(lo+hi)/2;self.w=hi-lo;self.label=label
    def pt(self,u,z,d=0):return (*point_at(self.mid+u,d),z)
    def prism(self,poly,back,front,material,label):self.b.prism(poly,back,front,self.pt,material,self.label+'/'+label)
    def box(self,u,z,width,height,thick,d,mat,label):
        # Long trim follows the street's curvature. A single chord sinks behind its brickwork at the tight ends.
        edges=np.linspace(u-width/2,u+width/2,max(1,int(np.ceil(width/.72)))+1)
        for left,right in zip(edges,edges[1:]):
            self.prism(box(left,z-height/2,right,z+height/2),d-thick/2,d+thick/2,mat,label)


def glazing(f,window,depth,cols,rows):
    l,b,r,t=window.bounds;bars=[window.difference(window.buffer(-.048,join_style='mitre'))]
    for i in range(1,cols):
        u=l+(r-l)*i/cols;bars.append(box(u-.021,b,u+.021,t))
    for i in range(1,rows):
        z=b+(t-b)*i/rows;bars.append(box(l,z-.022,r,z+.022))
    f.prism(window.buffer(.013,join_style='mitre'),-depth-.025,-depth,GLASS,'recessed glazing');f.prism(unary_union(bars).intersection(window),-depth+.012,-depth+.067,SASH,'steel casements')


def facing(f,wall,low,idx):
    w=f.w;batch={BRICK:[],RED:[],BUFF:[]};dt=.52 if low else .31;pitch=1.37 if low else .81
    for k in range(int((TOP-4.4)/dt)+1):
        z=4.4+k*dt;t=min(TOP,z+dt-.021)
        if t<=z:continue
        x=-w/2-pitch*(k%2)*.5;i=0
        while x<w/2:
            l=max(x,-w/2)+.009;r=min(x+pitch,w/2)-.009
            if r-l>.05:
                tile=wall.intersection(box(l,z+.014,r,t));tone=(k*11+i*13+idx*7)%29
                if tile.area>.003:batch[RED if tone in (4,11,19)else BUFF if tone in (2,7,17,23)else BRICK].append(tile)
            x+=pitch;i+=1
    for mat,shapes in batch.items():
        if shapes:f.prism(unary_union(shapes),.001,.031,mat,'mottled bonded tiles')


def equipment(f,u,z,low):
    f.box(u,z,.63,.46,.35,.22,AW,'apartment condenser cabinet');f.box(u,z,.49,.32,.035,.405,GRILLE,'vent screen')
    if not low:
        for j in range(5):f.box(u,z-.11+j*.055,.45,.018,.022,.430,AW,'vent screen fins')


def front_bay(b,idx,low):
    s=START+idx*PITCH;f=Bay(b,s,s+PITCH,'street bay '+str(idx+1));w=f.w;holes=[];glist=[]
    for floor,z in enumerate(LEVELS):
        ww=w*(.72 if floor else .66);op=box(-ww/2,z+.40,ww/2,z+1.78);holes.append(op);glist.append((op,.21,3 if low else 5,2))
        # Ribbons continue through piers, with two distinct edges bounding each horizontal casement band.
        for level in (z+.315,z+1.87):f.box(0,level,w,.085,.18,.065,BAND,'continuous horizontal sill and lintel')
        if idx not in (0,16)and (floor*7+idx*3)%9 in (0,2,3,6):equipment(f,w*.37,z+.11,low)
    portal=idx in (13,16);gw=w*(.65 if portal else .71);op=box(-gw/2,.10 if portal else .55,gw/2,3.19 if portal else 2.85)
    holes.append(op);glist.append((op,.70 if portal else .29,2 if portal else 3,2));wall=box(-w/2,.02,w/2,TOP).difference(unary_union(holes))
    f.prism(wall,-.37,0,JOINT,'brick wall and cut reveals');plinth=wall.intersection(box(-w/2,.02,w/2,4.35));f.prism(plinth,.002,.053,STONE,'fine-grain stone bank base');facing(f,wall,low,idx)
    for window,d,cols,rows in glist:glazing(f,window,d,cols,rows)
    for z,h,extension in [(4.28,.16,.12),(TOP-.58,.14,.20),(TOP-.19,.31,.36)]:f.box(0,z,w,h,extension,.09,BAND,'bank and roof cornices')
    if portal:
        for u in (-gw*.5-.13,gw*.5+.13):f.box(u,1.82,.235,3.61,.24,.09,STONE,'entrance jamb')
        f.box(0,3.60,gw+.49,.68,.16,.085,SIGN,'bank or apartment transom plaque')
        if idx==16:add_facade_lettering(f,'同孚大楼',0,3.64,gw+.11,.39,.17,.21,GOLD,label='apartment sign',font=FONT)
    if idx==12:
        f.box(0,3.68,w-.03,.70,.13,.084,STONE,'bank name fascia');add_facade_lettering(f,'中国工商银行',0,3.71,w-.30,.39,.16,.20,GRILLE,label='bank name',font=FONT)
    if idx==11:
        f.box(w*.23,3.70,.52,.52,.14,.085,STONE,'bank emblem mount');ring=Point(w*.23,3.70).buffer(.205,quad_segs=16).difference(Point(w*.23,3.70).buffer(.141,quad_segs=16));f.prism(ring,.16,.205,LETTER,'circular bank mark')
    if idx not in (13,16):
        for i in range(4 if low else 7):f.box(-gw*.43+gw*.86*i/(3 if low else 6),1.59,.034,1.92,.045,-.13,GRILLE,'street bank window bars')


def rectangular_tower(b,low):
    x,y=17.31,4.71
    for dims,z0,z1,mat,label in [((3.17,3.05),29.10,32.75,BRICK,'stair tower lower stage'),((2.64,2.64),32.75,34.23,BRICK,'stair tower upper stage'),((3.04,3.11),34.23,34.45,BAND,'cantilevered stair roof')]:
        wx,wy=dims;b.plan_prism(box(x-wx/2,y-wy/2,x+wx/2,y+wy/2),z0,z1,mat,label)
    for sign in (-1,1):
        b.plan_prism(box(x+sign*.93-.13,y-1.65,x+sign*.93+.13,y-.85),29.50,33.15,BUFF,'tower corner brick fins')
    for i in range(3):b.plan_prism(box(x-.85+.67*i,y-1.535,x-.63+.67*i,y-1.33),31.0,32.34,GRILLE,'upper tower vents')


def make_yates(b,low=False):
    for i in range(BAYS):front_bay(b,i,low)
    for l,r,label in [(0,START,'Wujiang rounded end'),(FINISH,LENGTH,'Nanjing stair spine')]:
        f=Bay(b,l,r,label);wall=box(-f.w/2,.02,f.w/2,TOP);f.prism(wall,-.36,0,BRICK,'blind corner pier');f.box(0,TOP-.20,f.w,.35,.35,.09,BAND,'edge of roof fascia')
        if l:
            for u in (-f.w*.24,.12):
                f.box(u,15.5,.26,25.62,.10,.037,GRILLE,'vertical stair window strips');f.box(u,15.5,.075,25.62,.16,.05,SASH,'stair window centre mullion')
                for z in LEVELS:f.box(u,z,.25,.075,.15,.05,SASH,'stair window transoms')
    arc=[tuple(point_at(float(x)))for x in np.linspace(0,LENGTH,81 if not low else 43)];back_y=6.73;floor=Polygon(arc+[(19.55,6.94),(-17.40,6.94)]);assert floor.is_valid
    b.plan_prism(floor,.01,.09,STONE,'ground floor of bank and apartments');b.plan_prism(floor,TOP-.27,TOP-.10,ROOF,'flat roof inside street parapet')
    back=Facade(b,(19.55,6.92),(-17.4,6.92),'rear service frontage');holes=[]
    for z in LEVELS:
        for k in range(5):holes.append(box(-14.8+k*6.14,z+.43,-11.14+k*6.14,z+1.78))
    back.wall(.08,TOP-.08,holes,thickness=.34,material=BRICK)
    for op in holes:glazing(back,op,.38,3,2)
    for sign,xx in [(-1,-17.30),(1,19.43)]:b.plan_prism(box(xx-.10,6.60,xx+.10,6.92),.08,TOP-.10,BRICK,'rear corner stop')
    rectangular_tower(b,low)
    # The account of the roof terrace describes two rows of eight round uprights and a round heating stack.
    for y in (2.13,4.67):
        for x in np.linspace(-8.40,9.20,8):b.lathe((x,y),[(TOP-.10,.22),(TOP+.12,.22),(TOP+.14,.17),(TOP+2.03,.17),(TOP+2.10,.21)],BAND,segments=10 if low else 18,label='sixteen terrace uprights')
    b.lathe((-16.38,4.75),[(TOP-.22,.79),(TOP+.40,.79),(TOP+.40+.015,.63),(TOP+2.43,.63),(TOP+2.53,.72)],BRICK,segments=15 if low else 32,label='Wujiang round roof stack')
