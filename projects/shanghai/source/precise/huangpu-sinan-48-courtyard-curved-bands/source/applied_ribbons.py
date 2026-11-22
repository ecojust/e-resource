"""Painted relief on a roughcast courtyard wall, Sinan Road 48 (2018)."""
from math import sin,cos,pi
from pathlib import Path
import numpy as np
from PIL import Image
from shapely.geometry import box,LineString,Polygon,Point
from shapely.ops import unary_union
ID='huangpu-sinan-48-courtyard-curved-bands'
WALL='Ochre textured wall';BATTEN='White painted applied trim';RAIL='Stone grey horizontal sill';FRAME='Dark red casement';PANE='Dark room beyond glass';MIRROR='Soft blue green reflection';AC='Warm white air conditioner';GRILL='Metal screen';DARK='Sill shadow';RUST='Weathered fixing'
PALETTE={key:{'color':v,'roughness':r}for key,v,r in [(WALL,[1,1,1],.99),(BATTEN,[.815,.806,.738],.83),(RAIL,[.603,.592,.531],.94),(FRAME,[.252,.168,.134],.78),(PANE,[.155,.198,.174],.41),(MIRROR,[.241,.289,.245],.42),(AC,[.736,.721,.645],.79),(GRILL,[.478,.489,.455],.81),(DARK,[.324,.312,.273],.95),(RUST,[.383,.294,.223],.91)]}
def texture():
    p=Path(__file__).with_name('plaster.png')
    if not p.exists():
        g=np.random.default_rng(555);v=np.asarray(Image.fromarray(g.integers(0,255,(128,148),dtype='u1')).resize((500,470),Image.Resampling.BICUBIC),float)
        grain=(v-128)*.18+g.normal(0,4.2,v.shape);Image.fromarray(np.clip([182,153,105]+grain[:,:,None],0,255).astype('u1')).quantize(128).save(p)
    PALETTE[WALL]['texture']=str(p)
def cast(b,poly,lo,hi,m,name):b.prism(poly,lo,hi,lambda x,z,d:(x,-d,z),m,name)
def rect(b,l,r,z0,z1,back,front,m,name):cast(b,box(l,z0,r,z1),back,front,m,name)
def bez(q,a,b,c,d):return np.array(a)*(1-q)**3+3*np.array(b)*(1-q)**2*q+3*np.array(c)*(1-q)*q*q+np.array(d)*q**3
def stroke(b,pts,far,name):
    curve=[tuple(bez(q,*pts)) for q in np.linspace(0,1,8 if far else 19)]
    cast(b,LineString(curve).buffer(.051,cap_style=2,join_style=2),.005,.050,BATTEN,name)
def add_building(b,far=False):
    texture()
    wall=box(-2.17,0,2.17,3.78)
    windows=[(-1.99,-.509,1.208,2.605),(1.114,1.971,1.218,2.65)]
    field=wall.difference(unary_union([box(*[l,z,r,top])for l,r,z,top in windows]));cast(b,field,-.30,0,WALL,'Continuous ochre roughcast behind raised white trim')
    for x in np.linspace(-2.11,2.11,8):
        rect(b,x-.050,x+.050,2.596,3.69,-.008,.056,BATTEN,'Seven narrow fields between vertical battens above the windows')
    for z in (2.622,3.698):rect(b,-2.174,2.174,z-.041,z+.041,-.01,.061,BATTEN,'Top and bottom border of upper frieze')
    for s in (-1,1):
        def mirror(points):return [(s*x,z)for x,z in points]
        for k,pts in enumerate([[(0.,3.664),(.064,3.32),(.323,3.224),(.584,3.05)],[(0.,2.656),(.278,2.788),(.499,2.891),(.584,3.05)],[(.606,2.674),(.781,3.019),(1.481,3.242),(1.977,3.643)]]):
            stroke(b,mirror(pts),far,'Upper pointed leaf' if k<2 else 'Outer curved ribbon joining the vertical strip')
    for x in (-2.13,-.491,.203,.773,2.132):rect(b,x-.046,x+.046,1.148,2.652,-.009,.053,BATTEN,'Vertical white framing beside window')
    for lo,hi,z,top in windows:
        rect(b,lo+.015,hi-.016,z+.016,top-.016,-.163,-.157,PANE,'Glass and deep inner shadow behind a narrow red casement')
        for x in [lo+.025,hi-.024]+([(lo+hi)/2]if hi<0 else[]):
            rect(b,x-.023,x+.023,z+.018,top-.021,-.158,-.101,FRAME,'Vertical timber window bar')
        for zz in (z+.02,top-.02):rect(b,lo,hi,zz-.026,zz+.026,-.157,-.104,FRAME,'Thin red window rail')
    rect(b,-2.175,2.166,1.071,1.142,-.04,.177,RAIL,'Long sill below both openings')
    rect(b,-2.159,2.16,.990,1.066,-.025,.069,DARK,'Shadowed edge beneath the common sill')
    for z in (.106,1.003):rect(b,-2.158,2.163,z-.045,z+.045,-.012,.067,BATTEN,'Edges of the lower panel below windows')
    for l,r in [(-2.11,-.39),(-.38,.379),(.38,2.11)]:
        rect(b,l-.042,l+.042,.097,1.02,-.011,.067,BATTEN,'Vertical strip separating lower panels')
        for x,mirror in [(l+.041,1),(r-.041,-1)]:
            for z,up in [(.157,1),(.947,-1)]:
                side=min(.386,(r-l)*.44)
                points=[(x,z+up*.212),(x+mirror*side*.72,z+up*.184),(x+mirror*side*.96,z+up*.089),(x+mirror*side,z)]
                stroke(b,points,far,'Curved applied sweep in an inner corner of the lower panel')
    rect(b,2.055,2.153,.112,1.02,-.012,.066,BATTEN,'Far right lower stile')
    rect(b,.382,1.679,1.175,1.852,.018,.418,AC,'Later outdoor unit on photographed window ledge')
    cast(b,Point(.815,1.51).buffer(.243,resolution=9 if far else 22),.417,.427,GRILL,'Circular fan behind pale grille')
    for y in np.arange(-.202,.219,.045):
        ww=(.235**2-y**2)**.5;rect(b,.815-ww,.815+ww,1.51+y-.005,1.51+y+.005,.426,.437,AC,'Thin lines over fan grille')
    if not far:
        for x in (1.193,1.31,1.427,1.544):rect(b,x,x+.007,1.23,1.76,.419,.421,GRILL,'Narrow vertical metal line beside fan')
    for p in b.parts:
        if p['material']==WALL:p['texcoords']=[[(x+2.2)/4.4,z/3.8]for x,y,z in p['vertices']]
