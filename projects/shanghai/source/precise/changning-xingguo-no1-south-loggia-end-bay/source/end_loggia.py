"""Open end bay of the garden-facing loggia of Xingguo House One, Shanghai."""
from math import cos,sin,pi
from pathlib import Path
import numpy as np
from PIL import Image
from shapely.geometry import Polygon,box

ID='changning-xingguo-no1-south-loggia-end-bay'
WALL='Pale limewashed pier';STONE='Carved light stone';SEAT='Grey moulded coping';ROOF='Green-grey seamed roof';INNER='Sheltered wall';DARK='Shaded rear opening';FRAME='Painted dark reveal';FLOOR='Stone gallery floor'
PALETTE={k:dict(color=c,roughness=r)for k,c,r in [(WALL,[1.,1.,1.],.97),(STONE,[1.,1.,1.],.85),(SEAT,[.65,.65,.59],.88),(ROOF,[1.,1.,1.],.71),(INNER,[.56,.56,.49],.9),(DARK,[.19,.22,.215],.59),(FRAME,[.27,.28,.26],.75),(FLOOR,[.56,.54,.51],.92)]}
# Measured proportions of the visible face. The gallery return is estimated in depth.
FRONT=-.04;BACK=2.15;COLUMNS=(-.97,.97)
BALUSTERS=tuple(np.linspace(-1.64,1.64,19))
def texture():
    p=Path(__file__).with_name('limewashed-loggia-and-roof.png')
    if not p.is_file() or Image.open(p).width!=672:
        rng=np.random.default_rng(711);n=224
        def cloud(w,h):
            return np.asarray(Image.fromarray(rng.integers(0,255,(h,w),dtype='uint8')).resize((n,n),Image.Resampling.BICUBIC),float)-128
        plaster=cloud(14,9)*.041+rng.normal(0,2.5,(n,n));metal=cloud(6,4)*.12+cloud(40,35)*.026+rng.normal(0,2.,(n,n))
        panels=[rgb+field[:,:,None] for rgb,field in [(np.array([214,213,203]),plaster),(np.array([144,157,125]),metal),(np.array([214,210,199]),cloud(20,15)*.045+rng.normal(0,3.,(n,n)))]]
        Image.fromarray(np.concatenate(panels,axis=1).clip(0,255).astype('uint8')).quantize(208).save(p)
    for m in (WALL,ROOF,STONE):PALETTE[m]['texture']=str(p)
def add_building(b,far=False):
    texture()
    def uv(start,mat):
        if mat not in (WALL,ROOF,STONE):return
        bank=(WALL,ROOF,STONE).index(mat)
        for part in b.parts[start:]:
            part['texcoords']=[((bank+.02+.96*((x+.27*y+2.56)/5.72%1))/3,.98-.96*((z+.19*y)/5.9%1))for x,y,z in part['vertices']]
    def block(x0,x1,y0,y1,z0,z1,m,n):
        start=len(b.parts);b.box(((x0+x1)/2,(y0+y1)/2,(z0+z1)/2),(x1-x0,y1-y0,z1-z0),m,label=n);uv(start,m)
    def rail(x,y):
        radius=.073
        profile=[(.347,.091),(.402,.091),(.43,.057),(.465,.054),(.50,.071),(.55,radius),(.615,.058),(.689,.042),(.737,.048),(.77,.064),(.809,.063)]
        b.lathe((x,y),profile,STONE,10 if far else 18,'Turned stone balusters')
    block(-2.4,2.4,-.31,2.25,.0,.18,SEAT,'Projecting sill with square edge')
    block(-2.36,2.36,-.24,2.21,.18,.253,FLOOR,'Upper gallery stone slab')
    for x in (-2.073,2.073):
        block(x-.274,x+.274,-.115,.395,.251,3.94,WALL,'Outer rendered pier')
        block(x-.30,x+.30,-.142,.41,.253,.39,SEAT,'Pier plinth projecting course')
        block(x-.30,x+.30,-.14,.413,3.77,3.93,STONE,'Pier head')
    # Continuous side return with a tall open round-headed arch.
    mid=1.09;radius=.663;spring=2.28
    arc=[(mid+radius*cos(t),spring+radius*sin(t))for t in np.linspace(0,pi,17 if far else 43)]
    opening=Polygon([(mid-radius,.23),(mid+radius,.23),*arc,(mid-radius,.23)])
    shape=box(.30,.24,2.20,3.91).difference(opening);start=len(b.parts)
    b.prism(shape,-2.34,-2.123,lambda y,z,x:(x,y,z),WALL,'Arched opening in return wall');uv(start,WALL)
    block(-2.30,2.29,BACK,BACK+.10,.24,3.92,INNER,'Rear wall in shade')
    block(-.62,.60,BACK-.055,BACK+.006,.254,2.94,DARK,'Tall dark opening behind columns')
    for x in (-.617,.601):block(x-.035,x+.035,BACK-.095,BACK-.047,.25,2.95,FRAME,'Rear opening jambs')
    block(-.65,.64,BACK-.093,BACK-.027,2.91,2.97,FRAME,'Rear opening head')
    for x in COLUMNS:
        block(x-.186,x+.186,-.185,.181,.251,.362,STONE,'Square post base')
        b.lathe((x,0),[(.36,.174),(.407,.173),(.441,.143),(.492,.133),(.532,.15),(.612,.137),(1.22,.139),(2.17,.135),(3.42,.114),(3.58,.114),(3.625,.137),(3.66,.141)],STONE,16 if far else 32,'Tapered straight column and base')
        b.lathe((x,0),[(3.65,.14),(3.686,.175),(3.733,.187),(3.787,.15),(3.815,.167)],STONE,12 if far else 28,'Rounded capital cushion')
        for side in (-1,1):
            xx=x+side*.162;points=[]
            for t in np.linspace(0,2.05*pi,12 if far else 32):
                radius=.058-.044*t/(2.05*pi);points.append([xx+side*radius*cos(t),-.139,3.725+radius*sin(t)])
            b.tube(points,.019,STONE,6 if far else 10,'Small scroll at capital')
        block(x-.228,x+.228,-.177,.177,3.79,3.851,STONE,'Square abacus')
    for x in BALUSTERS:
        if min(abs(x-c)for c in COLUMNS)>.125:rail(x,-.008)
    block(-1.82,1.82,-.128,.122,.25,.354,SEAT,'Stone plinth beneath balusters')
    block(-1.82,1.82,-.148,.129,.795,.866,STONE,'Continuous stone rail')
    block(-1.82,1.82,-.163,.14,.856,.901,SEAT,'Handrail cap')
    block(-2.34,2.34,-.115,2.26,3.85,3.985,WALL,'Entablature and gallery ceiling')
    for z,h,f,m in [(3.985,.053,-.158,STONE),(4.038,.145,-.099,INNER),(4.183,.055,-.155,STONE),(4.238,.066,-.245,SEAT),(4.304,.046,-.303,ROOF)]:
        block(-2.41,2.41,f,2.257,z,z+h,m,'Shadow and projecting courses of cornice')
    a=(-2.413,-.30,4.35);c=(2.413,-.30,4.35);d=(2.413,2.26,4.35);e=(-2.413,2.26,4.35);r=(-1.09,1.36,5.14);s=(1.09,1.36,5.14)
    start=len(b.parts);b.add([a,c,d,e,r,s],[(0,1,5,4),(1,2,5),(2,3,4,5),(3,0,4)],ROOF,'Four slopes of upper roof');uv(start,ROOF)
    def seam(p,q,thick=.014):
        b.tube([np.array(p)+[0,0,.006],np.array(q)+[0,0,.006]],thick,SEAT,5 if far else 8,'Raised roof seams')
    for p,q in ((a,r),(e,r),(c,s),(d,s),(r,s)):seam(p,q,.023)
    for t in np.linspace(.08,.92,13 if not far else 8):
        seam(np.array(a)*(1-t)+np.array(c)*t,np.array(r)*(1-t)+np.array(s)*t)

    for part in b.parts:
        if part['material']==STONE and not part.get('texcoords'):
            part['texcoords']=[((2.02+.96*((x+.32*y+2.56)/5.72%1))/3,.98-.96*((z+.19*y)/5.9%1))for x,y,z in part['vertices']]
