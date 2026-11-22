"""Rusticated alley arch with a scroll-shaped keystone, after the numbered 2019 Guangdong Road photo."""
from math import pi,cos,sin
import os
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from shapely.geometry import Polygon,box
ID='huangpu-guangdong-131-scroll-keystone'
ASHLAR='Weathered grey ashlar';WARM='Light banded ashlar';JOINT='Recessed grey joint';DARK='Shade within the arch reveal'
STONE='Paler sculpted keystone';RIDGE='Lit arris of carved scroll';RECESS='Shadow in recessed flutes'
PLAQUE='Enamel number plate';EDGE='Edge of enamel plaque'
PALETTE={m:dict(color=c,roughness=r)for m,c,r in [
 (ASHLAR,[1,1,1],.95),(WARM,[.373,.361,.318],.92),(JOINT,[.36,.365,.35],.96),(DARK,[.40,.395,.36],.93),
 (STONE,[.463,.437,.379],.89),(RIDGE,[.52,.49,.425],.9),(RECESS,[.364,.344,.290],.91),(PLAQUE,[1,1,1],.56),(EDGE,[.16,.21,.18],.72)]}
F=lambda x,z,d:(x,-d,z)
R=1.17;SPRING=2.20;RY=1.13;RING=.342;TOP=4.24
def texture():
    p=Path(__file__).with_name('grey-tooling.png')
    if not p.exists():
        rng=np.random.default_rng(511);H,W=288,448
        coarse=np.asarray(Image.fromarray(rng.integers(0,255,(19,31),dtype=np.uint8)).resize((W,H),Image.Resampling.BICUBIC),float)
        grain=(coarse-127)*.105+rng.normal(0,3.,(H,W))
        rgb=np.array([157,156,146])[None,None,:]+grain[:,:,None]
        Image.fromarray(np.clip(rgb,0,255).astype('u1')).quantize(140).save(p)
    PALETTE[ASHLAR]['texture']=str(p)
    plate=Path(__file__).with_name('number-131.png')
    if not plate.exists():
        f=Path(os.environ.get('SHANGHAI_CJK_FONT','/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'))
        im=Image.new('RGB',(224,98),(48,82,72));d=ImageDraw.Draw(im)
        font=ImageFont.truetype(str(f),65,index=2);d.text((9,2),'131弄',font=font,fill=(224,229,214),stroke_width=0);im.save(plate)
    PALETTE[PLAQUE]['texture']=str(plate)
def slab(b,poly,d,back,m,name):b.prism(poly,back,d,F,m,name)
def rect(b,l,r,lo,hi,d,back,m,name):slab(b,box(l,lo,r,hi),d,back,m,name)
def curve(a,thick=0.):return ((R+thick)*cos(a),SPRING+(RY+thick)*sin(a))
def arch(t,n):
    return Polygon([(-R-t,-.15),(R+t,-.15)]+[curve(v,t)for v in np.linspace(0,pi,n+1)])
def ring(b,far):
    inc=pi/13
    # The top block is the projecting scroll carrier. Adjacent stones have deep open joints.
    for i in range(13):
        a0,a1=i*inc+.0054,(i+1)*inc-.0054
        v=np.linspace(a0,a1,4 if far else 9)
        poly=Polygon([curve(t)for t in v]+[curve(t,RING) for t in v[::-1]])
        slab(b,poly,.103,-.54,ASHLAR if i not in (1,5,7,11) else WARM,'Radiating dressed voussoir and intrados')
        if i%2==0 and not far:
            line=[F(*curve(t,.019),.109) for t in v]
            b.tube(line,.0055,WARM,5,'Fine raised arris to intrados stone')
def scroll(b,far):
    # Projected S-shaped profile; both turns survive in the field photograph.
    npart=9 if far else 18
    z=np.linspace(3.325,4.08,npart)
    def depth(zz):
        t=(zz-3.325)/.755
        return .154+.34*t*t*(3-2*t)-.065*sin(2*pi*t)
    shape=Polygon([(.03,3.316),(.03,4.08)]+[(depth(i),i)for i in reversed(z)])
    for x0,x1 in [(-.175,.175)]:
        b.prism(shape,-x1,-x0,lambda y,z,u:(-u,-y,z),STONE,'Bending scroll corbel at the crown of the arch')
    for side in (-1,1):
        # Large lateral spiral, carried along its full side, and smaller reverse curl at the heel.
        for zz,yy,rad in [(4.007,.426,.107),(3.404,.173,.057)]:
            b.tube([(side*.181,-yy,zz),(side*.197,-yy,zz)],rad,STONE,14 if far else 28,'Round eye of the scroll')
            angles=np.linspace(0.,pi*2.65,15 if far else 39);radial=np.linspace(rad*.93,rad*.15,len(angles))
            b.tube([(side*.199,-(yy+r*cos(t)),zz+r*sin(t))for r,t in zip(radial,angles)],.009,RIDGE,5 if far else 8,'Coiled spiral in the eye of the volute')
    for x in (-.125,-.063,0.,.063,.125):
        path=[F(x,zz,depth(zz)+.006)for zz in z[1:-1]]
        b.tube(path,.009,RIDGE if x!=0 else RECESS,5 if far else 7,'Narrow flute following the bent face')
    rect(b,-.192,.192,3.294,3.341,.189,.024,STONE,'Heel under volute');rect(b,-.219,.219,4.087,4.145,.501,-.013,STONE,'Shallow cap over the upper curl')
def add_building(b,far=False):
    texture();width=1.94
    # Joints are a genuinely recessed backing, and the hood is open through the wall.
    slab(b,box(-width,0.,width,TOP).difference(arch(-.004,37 if far else 79)),-.017,-.46,JOINT,'Backing in the deeply rusticated joints')
    rshape=arch(RING+.012,37 if far else 79)
    for i in range(10):
        base=i*.438
        for l,r in [(-width,0.),(0.,width)]:
            face=box(l,base+.014,r,min(base+.430,TOP))
            remain=face.difference(rshape)
            if remain.area>1e-7:slab(b,remain,.047,-.465,ASHLAR,'Coursed wall either side of warehouse entrance')
    # Jamb blocks continue the lines of the radial voussoirs.
    for s in (-1,1):
        l,r=sorted([s*R,s*(R+RING)])
        for j in range(5):
            lo=j*SPRING/5;hi=(j+1)*SPRING/5
            rect(b,l,r,lo+.012,hi-.010,.101,-.53,ASHLAR if j%3 else WARM,'Deep block in the portal jamb')
    ring(b,far);scroll(b,far)
    for lo,hi,proj,mat in [(4.144,4.184,.164,WARM),(4.184,4.211,.234,STONE),(4.211,4.24,.222,WARM)]:
        rect(b,-width,width,lo,hi,proj,-.46,mat,'Upper horizontal moulding above the carved stone')
    # Retain the clearly legible 131弄 as an on-object address cue; the tiny lower text is indistinct.
    rect(b,1.498,1.858,2.49,2.655,.095,.047,EDGE,'Metal lip of address plate')
    rect(b,1.502,1.854,2.495,2.651,.098,.092,PLAQUE,'Legible part of the 131 lane number')
    for part in b.parts:
        if part['material']==ASHLAR:
            part['texcoords']=[[(x+2.05+.07*y)/4.12,(z+.08)/4.49]for x,y,z in part['vertices']]
        if part['material']==PLAQUE:
            part['texcoords']=[[(x-1.502)/.352,1.-(z-2.495)/.156]for x,y,z in part['vertices']]
