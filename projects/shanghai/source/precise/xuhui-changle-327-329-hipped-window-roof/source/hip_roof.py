"""Front three planes of the tiled window hood photographed on Changle Road in 2017."""
from pathlib import Path
import math
import numpy as np
from PIL import Image
from shapely.geometry import box
ID='xuhui-changle-327-329-hipped-window-roof'
TILE='Weathered brown roof tile';RIDGE='Overlapping light brown hip caps';CAP_EDGE='Weathered dark lip on each cap';WOOD='Dark ochre fascia';WALL='Rough ochre stucco';FRAME='Dark painted steel';GLASS='Dull blue-grey glass';SILL='Pale grey projecting sill';DARK='Window recess'
PALETTE={name:dict(color=rgb,roughness=r) for name,rgb,r in ((TILE,[1,1,1],.93),(RIDGE,[.492,.358,.287],.93),(CAP_EDGE,[.335,.258,.206],.94),(WOOD,[.148,.140,.124],.88),(WALL,[.687,.647,.567],.96),(FRAME,[.17,.184,.168],.68),(GLASS,[.28,.337,.357],.31),(SILL,[.593,.607,.596],.79),(DARK,[.101,.112,.112],.82))}
def texture():
    p=Path(__file__).with_name('brown-roof-tile.png')
    if not p.exists():
        rng=np.random.default_rng(831);yy,xx=np.indices((192,192));coarse=np.asarray(Image.fromarray(rng.integers(0,255,(12,12),dtype='uint8')).resize((192,192),Image.Resampling.BILINEAR)).astype(float)
        weather=(coarse-125)*.18+4.4*np.sin(xx*.098+yy*.04)+rng.normal(0,5,xx.shape)
        Image.fromarray((np.array([145,111,92])+weather[:,:,None]).clip(0,255).astype('uint8')).quantize(100).save(p)
    PALETTE[TILE]['texture']=str(p)
RADIUS=2.24;DEPTH=1.52;EAVE=1.62;RISE=1.10
def roof_point(side,u,t):
    if side=='front':return ((2*u-1)*RADIUS*(1-t),DEPTH*t,EAVE+RISE*t)
    sign=1 if side=='right' else -1
    return (sign*RADIUS*(1-t), DEPTH*(t+(1-t)*(u if sign<0 else 1-u)), EAVE+RISE*t)
def add_building(b,far=False):
    texture()
    def rect(name,material,x0,x1,y0,y1,z0,z1):
        b.box(((x0+x1)/2,(y0+y1)/2,(z0+z1)/2),(x1-x0,y1-y0,z1-z0),material,label=name)
    for side in ('front','left','right'):
        corners=[roof_point(side,u,t) for u,t in ((0,0),(1,0),(.5,1))]
        backing=[(x,y,z-.014) for x,y,z in corners]
        b.add(backing,[(0,1,2) if side=='front' else (2,1,0)],WOOD,side.title()+' timber beneath the tile joints')
        verts=[];faces=[];uv=[]
        for row in range(16):
            start=row/16;end=min(.999,(row+1.16)/16)
            count=max(1,round((39 if side=='front' else 14)*(1-start)))
            for col in range(count):
                base=len(verts);segments=4 if far else 10
                for t,h in [(start,-.01),(start,0),(end,0)]:
                    for j in range(segments+1):
                        f=j/segments;u=(col+.007+.986*f)/count
                        x,y,z=roof_point(side,u,t)
                        roll=(1+math.cos(math.tau*(f-.29)))/2
                        z+=.004*(1+math.sin(.71*col+1.37*row))+.026*roll**1.4+.016*(end-t)/(end-start)+h
                        verts.append((x,y,z));uv.append((f,1-(t-start)/(end-start)))
                n=segments+1
                for j in range(segments):
                    a=base+j
                    for q in ((a,a+1,a+1+n,a+n),(a+n,a+1+n,a+1+2*n,a+2*n)):
                        faces.append(q if side=='front' else q[::-1])
        b.add(verts,faces,TILE,side.title()+' pitch with individually rolled tile pans');b.parts[-1]['texcoords']=uv
    for sign in [-1,1]:
        for row in range(14):
            lo=row/14;hi=min(.998,(row+1.16)/14);points=[];faces=[]
            seg=5 if far else 12
            tangent=np.array([-sign*RADIUS,DEPTH,0]);cross=np.array([tangent[1],-tangent[0],0])/np.linalg.norm(tangent)
            for t in (lo,hi):
                x,y,z=roof_point('front',1 if sign>0 else 0,t);center=np.array([x,y,z+.026])
                for j in range(seg+1):
                    a=j*math.pi/seg
                    points.append(center+cross*.065*math.cos(a)+np.array([0,0,.075*math.sin(a)+.008*(hi-t)/(hi-lo)]))
            for j in range(seg):
                q=(j,j+1,j+seg+2,j+seg+1);faces.append(q[::-1])
            b.add(points,faces,RIDGE,'Overlapping curved cap along diagonal hip')
            lip=[]
            for t in (lo,lo+.013):
                x,y,z=roof_point('front',1 if sign>0 else 0,t)
                center=np.array([x,y,z+.033])
                for j in range(seg+1):
                    a=j*math.pi/seg
                    lip.append(center+cross*.068*math.cos(a)+np.array([0,0,.083*math.sin(a)]))
            b.add(lip,faces,CAP_EDGE,'Exposed weathered nose of this individual ridge cap')
    rect('Front timber fascia',WOOD,-2.248,2.248,-.036,.055,1.487,1.621)
    for side in [-1,1]:
        x=side*2.206;rect('Returning timber edge',WOOD,x-.044,x+.044,0,1.52,1.487,1.621)
    for x in np.linspace(-2.03,2.03,14):rect('Dark exposed rafter end',WOOD,x-.032,x+.032,.03,.295,1.433,1.5)
    centers=[-.95,.96];wall=box(-2.095,-.05,2.095,1.515)
    for center in centers:wall=wall.difference(box(center-.405,.155,center+.405,1.185))
    b.prism(wall,-.43,-.255,lambda x,z,depth:(x,-depth,z),WALL,'Stucco front with two separate window openings')
    for center in centers:
        rect('Shadow in window reveal',DARK,center-.41,center+.41,.43,.462,.152,1.19)
        rect('Projecting light sill',SILL,center-.457,center+.457,.195,.435,.092,.155)
        for base,angle in ((center-.39,-.85),(center+.005,0)):
            c,s=math.cos(angle),math.sin(angle)
            def leaf(u,v,z):return (base+c*u-s*v,.265+s*u+c*v,z)
            def member(l,r,n,f,bottom,top,mat,name):b.prism(box(l,n,r,f),bottom,top,leaf,mat,name)
            member(.016,.363,.005,.017,.194,1.146,GLASS,'Opened or closed blue-grey glazed leaf')
            for u in (0,.365,.18):member(u,u+.016,-.012,.018,.166,1.165,FRAME,'Painted vertical steel strip')
            for z in (.17,.427,.681,.927,1.145):member(0,.38,-.015,.019,z,z+.014,FRAME,'Horizontal steel window bar')
