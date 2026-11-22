"""The arched transom, paired consoles and stepped hood at 2305 North Sichuan Road."""
from pathlib import Path
from math import pi,cos,sin
import numpy as np
from PIL import Image
from shapely.geometry import Polygon,box,LineString
ID='hongkou-north-sichuan-2305-arched-hood'
WALL='Pebbled grey render';TRIM='Cream arch and hood';EDGE='Lighter stepped lip';SHADOW='Shadow in arch reveal';IRON='Black transom grille';WOOD='Brown rail over the doorway';STONE='Warm grey spring blocks';BODY='Carved white console';FLANK='Worn return at bracket cheek';GLASS='Dark opening behind grille'
PALETTE={name:dict(color=c,roughness=r) for name,c,r in [(WALL,[1,1,1],.95),(TRIM,[.79,.745,.644],.90),(EDGE,[.879,.836,.746],.85),(SHADOW,[.29,.262,.22],.96),(IRON,[.134,.119,.093],.73),(WOOD,[.33,.202,.147],.72),(STONE,[.676,.643,.54],.92),(BODY,[.795,.757,.661],.93),(FLANK,[.70,.66,.55],.94),(GLASS,[.089,.087,.075],.45)]}
def texture():
    p=Path(__file__).with_name('grey-roughcast.png')
    if not p.is_file():
        rng=np.random.default_rng(671);n=rng.normal(0,9,(256,384,1));m=np.array(Image.fromarray(rng.integers(0,255,(37,59),'uint8')).resize((384,256),Image.Resampling.BICUBIC),float)/255
        arr=[110,119,112]+n+22*m[:,:,None];Image.fromarray(np.clip(arr,0,255).astype('uint8')).save(p)
    PALETTE[WALL]['texture']=str(p)
def arch(r,z,n):
    return [(r*cos(t),z+r*sin(t)) for t in np.linspace(pi,0,n+1)]
def curve(p0,p1,p2,p3,n=12):
    return [tuple((1-t)**3*np.array(p0)+3*t*(1-t)**2*np.array(p1)+3*t*t*(1-t)*np.array(p2)+t**3*np.array(p3)) for t in np.linspace(0,1,n,endpoint=False)]
def add_building(b,far=False):
    texture()
    def form(shape,d,e,mat,name):b.prism(shape,d,e,lambda x,z,k:(x,-k,z),mat,name)
    def rect(x,y,z,h,d,e,mat,name):form(box(x,z,y,h),d,e,mat,name)
    count=26 if far else 58
    inner=Polygon(arch(.862,.50,count)+[(.862,0),(-.862,0)])
    form(box(-1.62,0,1.62,2.46).difference(inner),-.30,-.002,WALL,'Cut grey roughcast around the entry head')
    form(inner,-.275,-.255,GLASS,'Recessed opening behind the fan grille')
    form(Polygon(arch(1.032,.50,count)+list(reversed(arch(.854,.50,count)))),-.13,.090,TRIM,'Semi-circular moulded band following the opening')
    form(Polygon(arch(.873,.50,count)+list(reversed(arch(.842,.50,count)))),-.14,.003,SHADOW,'Inner reveal below the white arch')
    for x in(-1.,1.):
        rect(x-.135,x+.135,.418,.57,-.02,.145,STONE,'Impost block at arch spring')
        rect(x-.151,x+.151,.530,.566,.014,.158,EDGE,'Thin moulding at the spring')
    for x in np.arange(-.8,.81,.11):
        maxz=.50+(.84**2-x**2)**.5
        rect(x-.007,x+.007,.50,maxz-.008,-.221,-.188,IRON,'Vertical bar in the dark transom')
    for z in(.50,.69,.9,1.09):
        extent=max(0,.84**2-max(0,z-.50)**2)**.5
        rect(-extent,extent,z-.006,z+.006,-.218,-.186,IRON,'Transom horizontal cross ties')
    rect(-.86,.86,.443,.505,-.197,-.092,WOOD,'Horizontal wooden head of doorway')
    for i,x in enumerate(np.linspace(-1.13,1.13,11)):
        rect(x-.041,x+.041,1.876,1.955,-.02,.19,TRIM,'Square dentils beneath projecting lintel')
    for a,h,d,e,mat in [(1.946,2.014,-.035,.311,TRIM),(2.014,2.047,-.035,.359,EDGE),(2.047,2.103,-.035,.338,TRIM),(2.103,2.144,-.035,.399,EDGE),(2.144,2.194,-.035,.38,TRIM),(2.194,2.232,-.035,.425,EDGE)]:
        rect(-1.39-(e-.3)*.54,1.39+(e-.3)*.54,a,h,d,e,mat,'Stepped cap over both consoles')
    for x in(-1.177,1.177):
        # A side silhouette runs from the toe at the wall to the rounded upper nose.
        joints=[((.035,.95),(.083,.966),(.225,.986),(.225,1.063)),((.225,1.063),(.218,1.16),(.089,1.216),(.094,1.421)),((.094,1.421),(.101,1.641),(.186,1.75),(.29,1.699)),((.29,1.699),(.415,1.656),(.456,1.774),(.384,1.869)),((.384,1.869),(.36,1.909),(.29,1.925),(.288,1.954))]
        profile=[p for segment in joints for p in curve(*segment,n=5 if far else 13)]+[(.288,1.954),(-.018,1.954),(-.018,.95)]
        b.prism(Polygon(profile),-x-.115,-x+.115,lambda d,z,t:(-t,-d,z),BODY,'S-profile of scroll console')
        for lo,hi,dep in [(.904,.947,.176),(.947,.976,.188),(1.865,1.904,.382),(1.904,1.949,.414)]:
            rect(x-.139,x+.139,lo,hi,-.015,dep,TRIM,'Upper and lower cushion of stone bracket')
        if not far:
            for xx in (x-.116,x+.116):
                b.tube([(xx,-(.291+.062*cos(t)),1.789+.069*sin(t)) for t in np.linspace(-pi*.58,pi*.99,18)],.0065,FLANK,7,'Fine lip on rounded cheek')
    for p in b.parts:
        if p['material']==WALL:p['texcoords']=[[(x+1.63)/3.26,z/2.47]for x,y,z in p['vertices']]
