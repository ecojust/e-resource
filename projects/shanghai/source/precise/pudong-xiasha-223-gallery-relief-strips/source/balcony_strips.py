"""Tall reddish ornament boards of the upper gallery at 223 Xiasha Street, seen by Dragon in 2020."""
import math
from pathlib import Path
import numpy as np
from PIL import Image
from shapely.geometry import Polygon,LineString,box
from shapely.ops import unary_union
ID='pudong-xiasha-223-gallery-relief-strips'
BASE='Brown relief field';MOLD='Dark red raised mouldings';ORN='Worn reddish scroll relief';BEAM='Dark gallery beams';DEPTH='Deep brown grooves'
PALETTE={m:dict(color=c,roughness=r)for m,c,r in ((BASE,[1,1,1],.92),(MOLD,[1,1,1],.88),(ORN,[1,1,1],.90),(BEAM,[1,1,1],.88),(DEPTH,[.20,.145,.129],.93))}
C=[-.59,0,.59]
def texture():
    f=Path(__file__).with_name('brown-relief-and-timber.png')
    if not f.exists():
        rng=np.random.default_rng(879);h,w=236,212
        field=lambda a,b:np.asarray(Image.fromarray(rng.integers(0,255,(a,b),dtype='uint8')).resize((w,h),Image.Resampling.BILINEAR),float)-127
        n=field(11,90)*.14+field(34,36)*.13+rng.normal(0,4,(h,w))
        a=np.concatenate([np.array(rgb)+n[:,:,None]*s for rgb,s in (([112,79,69],1),([145,108,87],1.17),([67,53,47],.89))],axis=1)
        Image.fromarray(a.clip(0,255).astype('uint8')).quantize(144).save(f)
    for m in (BASE,MOLD,ORN,BEAM):PALETTE[m]['texture']=str(f)
def shape(cx,far,b):
    def front(p,lo,hi,m,name):b.prism(p,lo,hi,lambda x,z,d:(cx+x,-d,z),m,name)
    def plate(x,z,w,h,d0,d1,m,n):b.box((cx+x,-(d0+d1)/2,z),(w,d1-d0,h),m,label=n)
    def bar(points,r,lo,hi,m,label):front(LineString(points).buffer(r,resolution=2 if far else 6,cap_style=1,join_style=1),lo,hi,m,label)
    def oval(x,z,rx,rz):
        a=np.linspace(0,2*math.pi,18 if far else 41,endpoint=False)
        return Polygon([(x+rx*math.cos(t),z+rz*math.sin(t))for t in a])
    plate(0,.713,.228,1.13,-.039,.001,BASE,'Flat field of one narrow vertical relief')
    for x in (-.128,.128):
        plate(x,.78,.030,1.42,-.047,.022,MOLD,'Tall red-brown edging')
        plate(x,.78,.010,1.39,.022,.030,ORN,'Fine outside line of moulding')
    plate(0,1.476,.283,.029,-.042,.023,MOLD,'Short top bar above small open scrolls')
    plate(0,1.299,.251,.023,-.045,.026,MOLD,'Small horizontal divider below the crest')
    for sign in (-1,1):
        pts=[(-.110,1.470),(-.096,1.438),(-.081,1.431),(-.073,1.457),(-.052,1.451),(-.042,1.420),(-.062,1.397),(-.087,1.378),(-.092,1.344),(-.056,1.330),(-.032,1.335),(-.017,1.364),(0.,1.373)]
        bar([(sign*x,z) for x,z in pts],.008,.002,.025,ORN,'Paired open scroll in upper frieze')
        a=np.linspace(-math.pi/2,math.pi/2,12 if far else 24)
        # Long recessed inner border broadens at the upper cluster and narrows sharply below.
        curve=[(.085,.923),(.101,1.105),(.102,1.226),(.086,1.258),(.056,1.273),(.028,1.258),(.013,1.236)]
        bar([(sign*x,z)for x,z in curve],.0075,.002,.025,ORN,'Long relief border beside central ornament')
        bar([(sign*.084,.922),(sign*.067,.816),(sign*.038,.766),(0,.737)],.008,.002,.022,MOLD,'Pointed base of long upper frame')
    for z,rx,rz in ((1.217,.038,.033),(1.146,.043,.040),(1.067,.048,.044),(.977,.053,.050),(.878,.040,.045)):
        form=oval(0,z,rx,rz)
        front(form,.002,.013,ORN,'Soft rounded relief in upright sequence')
        ring=form.difference(oval(0,z+.004,rx*.68,rz*.67))
        front(ring,.013,.021,MOLD,'A raised rim to each rounded relief')
    for z in (.655,.437):
        # The two small angular motifs below the taper are largely blank in the middle.
        p=Polygon([(0,z+.069),(.063,z), (0,z-.072),(-.062,z)])
        frame=p.difference(Polygon([(0,z+.043),(.042,z),(0,z-.046),(-.041,z)]))
        front(frame,.002,.018,ORN,'Open-centred lozenge relief')
        for s in (-1,1):
            bar([(s*.060,z),(s*.079,z+.024),(s*.081,z+.051)],.004,.002,.014,ORN,'Upturned short terminal on lozenge')
    for z in (.224,.311):
        plate(0,z,.025,.018,.002,.010,MOLD,'Small surviving relief at lower end')
def add_building(b,far=False):
    texture()
    for c in C:shape(c,far,b)
    for z,w,d,h,n in ((.063,1.67,.117,.085,'Lower stepped rail'),(.116,1.65,.128,.031,'Upper ledge on bottom rail'),(1.515,1.68,.148,.077,'Continuous dark handrail'),(1.563,1.69,.163,.033,'Slight projection on upper rail')):
        b.box((0,0,z),(w,d,h),BEAM,label=n)
    for p in b.parts:
        m=p['material']
        strip=2 if m==BEAM else 1 if m==ORN else 0
        p['texcoords']=[((strip+.025+.949*min(1,max(0,(x+.851)/1.70)))/3,.985-.955*min(1,max(0,z/1.59)))for x,y,z in p['vertices']]
