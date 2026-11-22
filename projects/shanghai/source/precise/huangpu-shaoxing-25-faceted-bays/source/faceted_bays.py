"""Art Deco twin bays and centre spandrels at the Shaoxing Road courtyard."""
from math import pi,cos,sin
from pathlib import Path
from shapely.geometry import box,Polygon,Point
from shapely.ops import unary_union
import numpy as np
from PIL import Image
ID='huangpu-shaoxing-25-faceted-bays'
WALL='Light straw roughcast';CAP='Pale cement cap';FASCIA='Dark sheet fascia';RIM='Grey steel window rim';BAR='Dark steel glazing bar';GLASS='Grey upper window glass';SKY='Cooler blue reflection';REVEAL='Deep slot backing';LIGHT='Pale centre sash';BOX='Weathered metal enclosure';FAN='Outer fan louvres';SOFFIT='Shaded eaves soffit';SOIL='Runoff just below the sill'
PALETTE={m:dict(color=c,roughness=r)for m,c,r in [(WALL,[1,1,1],.97),(CAP,[.722,.699,.594],.91),(FASCIA,[.224,.210,.185],.88),(RIM,[.293,.285,.261],.77),(BAR,[.125,.148,.151],.69),(GLASS,[.277,.335,.354],.37),(SKY,[.387,.439,.459],.34),(REVEAL,[.240,.230,.190],.92),(LIGHT,[.775,.777,.732],.75),(BOX,[.785,.776,.701],.81),(FAN,[.521,.533,.517],.85),(SOFFIT,[.491,.475,.395],.94),(SOIL,[.528,.512,.428],.98)]}
def texture():
    p=Path(__file__).with_name('plaster.png')
    if not p.exists():
        g=np.random.default_rng(547);base=np.asarray(Image.fromarray(g.integers(0,255,(38,78),dtype='u1')).resize((502,512),Image.Resampling.BICUBIC),float)
        a=(base-126)*.046+g.normal(0,2.5,base.shape);Image.fromarray(np.clip([190,183,155]+a[:,:,None],0,255).astype('u1')).quantize(128).save(p)
    PALETTE[WALL]['texture']=str(p)
def plate(b,poly,d0,d1,m,name):
    b.prism(poly,d0,d1,lambda x,z,d:(x,-d,z),m,name)
def rect(b,l,r,lo,hi,d0,d1,m,n):plate(b,box(l,lo,r,hi),d0,d1,m,n)
def horizontal(b,poly,z0,z1,m,name):
    b.prism(poly,z0,z1,lambda x,y,z:(x,y,z),m,name)
OUTER=(-3.03,3.03);INNER=(-.696,.696);FLOORS=[(1.03,2.59),(4.10,5.57)]
def grid(b,c,hw,low,high,front,ncols,light):
    m=LIGHT if light else BAR;back=front-.242
    for a in range(ncols):
        x0=c-hw+2*hw*a/ncols;x1=c-hw+2*hw*(a+1)/ncols
        for j in range(4):
            z0=low+(high-low)*j/4;z1=low+(high-low)*(j+1)/4
            rect(b,x0+.009,x1-.009,z0+.009,z1-.009,back-.012,back,SKY if (2*a+j)%5==1 else GLASS,'Glazing rectangle in two storeys of steel sash')
    for x in np.linspace(c-hw,c+hw,ncols+1):
        rect(b,x-.017,x+.017,low,high,back-.002,back+.029,m,'Narrow vertical glazing bar')
    for z in np.linspace(low,high,5):
        rect(b,c-hw,c+hw,z-.014,z+.014,back+.004,back+.025,m,'Continuous horizontal glazing bar')
    rect(b,c-hw-.053,c+hw+.053,low-.102,low-.020,front-.27,front+.07,CAP,'Thin sill with a short projecting drip')
def plan(c,pad=0):
    return Polygon([(c-1.56-pad,.272),(c+1.56+pad,.272),(c+1.56+pad,-.286),(c+1.09+pad,-.756-pad),(c-1.09-pad,-.756-pad),(c-1.56-pad,-.286)])
def outdoor(b,c,z,far):
    rect(b,c-.318,c+.318,z-.212,z+.212,.82,1.092,BOX,'Later external air conditioning unit at window')
    plate(b,Point(c-.011,z).buffer(.164,resolution=7 if far else 16),1.089,1.104,FAN,'Circular fan grille')
    for dz in np.arange(-.12,.142,.047):
        width=(.162**2-dz**2)**.5
        rect(b,c-width,c+width,z+dz-.006,z+dz+.006,1.103,1.112,RIM,'Horizontal louvre across circular grille')
    for x in (c-.20,c+.197):
        b.tube([(x,-.758,z-.37),(x,-1.055,z-.219)],.017,BAR,6 if far else 10,'Oblique supporting angle beneath casing')
def add_building(b,far=False):
    texture()
    center=box(-1.50,.04,1.50,6.09)
    gaps=[box(c-.588,lo,c+.588,hi)for c in INNER for lo,hi in FLOORS]
    grooves=[box(c-.577,z-.049,c+.577,z+.049)for c in INNER for z in (3.022,3.294,3.569)]
    plate(b,center.difference(unary_union(gaps+grooves)),-.38,0,WALL,'Recessed central wall with six genuine spandrel grooves')
    for c in INNER:
        for lo,hi in FLOORS:grid(b,c,.586,lo,hi,0.,4,light=(c>0 and lo<2))
        for z in (3.022,3.294,3.569):
            rect(b,c-.578,c+.578,z-.049,z+.049,-.148,-.135,REVEAL,'Shadow at the back of one horizontal groove')
    horizontal(b,box(-1.56,-.25,1.56,.44),6.025,6.145,SOFFIT,'Flat central soffit between raised corner bays')
    horizontal(b,box(-1.56,-.284,1.56,.44),6.14,6.255,FASCIA,'Dark central roof edge set back between wings')
    for c in OUTER:
        wall=box(c-1.085,.04,c+1.085,6.47)
        span=wall.difference(unary_union([box(c-.876,lo,c+.876,hi)for lo,hi in FLOORS]))
        plate(b,span,.475,.756,WALL,'Straight front of the faceted outer wing')
        for sign in (-1,1):
            outer=c+sign*1.555;inner=c+sign*1.078
            poly=Polygon([(inner,-.755),(outer,-.279),(outer,.23),(outer-sign*.135,.23),(outer-sign*.135,-.215),(inner,-.561)])
            horizontal(b,poly,.04,6.51,WALL,'Splayed side and returning wall behind the projected window')
        for lo,hi in FLOORS:grid(b,c,.874,lo,hi,.756,6,False)
        horizontal(b,plan(c,.19),6.46,6.575,SOFFIT,'Broad projecting soffit, cut to the bay angles')
        horizontal(b,plan(c,.217),6.569,6.657,CAP,'Concrete cap around the faceted wing')
        horizontal(b,plan(c,.25),6.648,6.778,FASCIA,'Dark continuous outer fascia along bevel and front')
        if not far:
            for s in (-1,1):
                x=c+s*1.017
                for z in (2.712,5.692):rect(b,x-.013,x+.013,z-.102,z+.043,.754,.760,SOIL,'Narrow rain streak below outside edge')
        for dc in ([-.49]if c<0 else[-.46,.30]):outdoor(b,c+dc,4.026,far)
    for p in b.parts:
        if p['material']==WALL:p['texcoords']=[[(x+4.88)/9.76,(z+.01)/6.79]for x,y,z in p['vertices']]
