"""Visible gates, openings and exposed reveal of the riverside curtain wall at Qianjin Street 77."""
from pathlib import Path
from math import sin
import numpy as np
from PIL import Image
from shapely.geometry import box,Polygon
from shapely.ops import unary_union
ID='qingpu-liantang-lu-rice-house-riverside-gate'
LIME='Old white limewashed masonry';STONE='Grey stone surround'; SILL='Worn weathering stone'; DAMP='Dark base of the render'; CAP='Dark mineral wall cap'; INSIDE='Shadow in the photographed opening'
PALETTE={k:dict(color=c,roughness=r) for k,c,r in [(LIME,[1,1,1],.96),(STONE,[1,1,1],.94),(SILL,[.46,.46,.423],.91),(DAMP,[1,1,1],.95),(CAP,[.30,.31,.29],.93),(INSIDE,[.088,.094,.084],.97)]}
GATE=(.58,0.,1.49,1.77);LEFT=(-2.82,1.22,-2.31,1.744);RIGHT=(1.79,1.35,2.29,1.691)
def texture():
    f=Path(__file__).with_name('lime-plaster-and-doorstone.png')
    if not f.exists():
        rng=np.random.default_rng(911);h,w=350,384;y,x=np.indices((h,w))
        def field(dims):return np.asarray(Image.fromarray(rng.integers(0,255,dims,dtype='uint8')).resize((w,h),Image.Resampling.BICUBIC),float)-124
        fine=rng.normal(0,2.6,(h,w));cloud=.205*field((11,13))+.115*field((31,90))+.085*field((6,104))
        lower=np.clip((y-h*.72)/(h*.28),0,1);worn=lower*(8+.062*field((17,48)))
        colors=[np.array([190,193,185])+(cloud+fine-worn)[:,:,None],np.array([123,124,112])+(.18*field((22,38))+1.55*fine)[:,:,None],np.array([104,107,96])+(.26*field((19,45))+fine)[:,:,None]]
        Image.fromarray(np.concatenate(colors,axis=1).clip(0,255).astype('uint8')).quantize(224).save(f)
    for m in (LIME,STONE,DAMP):PALETTE[m]['texture']=str(f)
def add_building(b,far=False):
    texture()
    def extrude(shape,front,back,mat,name):
        start=len(b.parts);b.prism(shape,-back,-front,lambda x,z,d:(x,-d,z),mat,name)
        if mat in (LIME,STONE,DAMP):
            band=(LIME,STONE,DAMP).index(mat)
            for p in b.parts[start:]:
                p['texcoords']=[((band+.01+.98*max(0,min(1,(xx+3.35)/6.7)))/3,.992-.985*max(0,min(1,zz/5.)))for xx,yy,zz in p['vertices']]
    openings=[box(*coords) for coords in (GATE,LEFT,RIGHT)]
    face=box(-3.22,.0,3.22,4.82).difference(unary_union(openings))
    extrude(face,0,.44,LIME,'High limewashed courtyard wall pierced by the three verified openings')
    for title,coords,depth,outer in [('Entrance',GATE,.292,.08),('Left opening',LEFT,.250,.047),('Right opening',RIGHT,.251,.040)]:
        x,z,r,t=coords;opened=box(x,z,r,t)
        name='Grey stone around the gate' if title=='Entrance' else 'Limewash turning at the small opening'
        mat=STONE if title=='Entrance' else LIME
        def surround(off):
            return box(x-off,max(0,z-off),r+off,t+off).difference(opened)
        extrude(surround(outer),-.018,.05,mat,name)
        step_count=2 if far else 5
        for k in range(step_count):
            dist=.022*(k+1)/step_count
            inner=box(x+dist,z if title=='Entrance' else z+dist,r-dist,t-dist)
            outer_box=opened if k==0 else previous
            extrude(outer_box.difference(inner),.013+k*.009,.013+(k+1)*.009+.019,mat,'Shallow reveal into the masonry: '+title)
            previous=inner
        if title!='Entrance':extrude(box(x-.024,z-.044,r+.024,z),-.055,.31,SILL,'Shallow sill below '+title)
        else:extrude(box(x,-.025,r,.006),-.075,.34,SILL,'Threshold at the riverside walkway')
        extrude(box(x+.021,z+.002,r-.021,t-.02),depth,depth+.009,INSIDE,'Visible dark field beyond '+title)
    # Only the irregular, visible wall base is represented. Its profile is an approximation.
    for j,(a,c) in enumerate([(-3.22,-2.5),(-2.45,-1.58),(-1.55,-.56),(-.52,.53),(1.56,2.04),(2.09,2.76),(2.78,3.22)]):
        n=11 if far else 29;top=[(a+(c-a)*i/n,.068+.025*sin(1.9*i/n+2*j)+.019*sin(1.5*j+11*i/n))for i in range(n+1)]
        extrude(Polygon([(a,.001),(c,.001),*reversed(top)]),-.005,.005,DAMP,'Discontinuous dark skirt along the pavement')
    # A single cap with a projecting lip is the only defensible top edge at the resolution of the source.
    lip=[(-3.255,4.799),(3.255,4.799),(3.255,4.894),(-3.255,4.894)]
    extrude(Polygon(lip),-.069,.503,CAP,'Dark continuous projecting wall cap')
    for x in np.linspace(-3.25,3.25,24 if far else 48):
        width=6.5/(23 if far else 47)
        if x+width>3.251:continue
        z1=4.91+.009*sin(3.1*x)+.004*sin(13*x);z2=4.91+.009*sin(3.1*(x+width))+.004*sin(13*(x+width))
        extrude(Polygon([(x,4.892),(x+width,4.892),(x+width,z2),(x,z1)]),-.05,.485,CAP,'Slightly irregular top bed of the coping')
