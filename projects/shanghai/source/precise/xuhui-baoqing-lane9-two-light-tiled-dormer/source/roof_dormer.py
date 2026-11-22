"""Red corrugated tile field and the projecting, dark-edged two-light dormer on Baoqing Road."""
from pathlib import Path
import math
import numpy as np
from shapely.geometry import box,Polygon
from PIL import Image,ImageDraw
ID='xuhui-baoqing-lane9-two-light-tiled-dormer'
TILE='Fired red interlocking tile';FLASH='Dark slate-like cheek';CAP='Dark metal hood edge';BATTEN='Dark apron beneath window';SASH='Pale grey sash';GLASS='Pale reflecting glass';JOINT='Shaded tile underlay';EAVE='Cream moulded eaves';TAN='Ochre wall strip';REVEAL='Dark inner reveal'
PALETTE={m:dict(color=c,roughness=r) for m,c,r in [(TILE,[1,1,1],.9),(FLASH,[.202,.218,.224],.8),(CAP,[.148,.163,.177],.66),(BATTEN,[.273,.284,.290],.76),(SASH,[.744,.744,.691],.68),(GLASS,[.547,.617,.625],.39),(JOINT,[.354,.263,.214],.93),(EAVE,[.676,.624,.478],.91),(TAN,[.701,.641,.456],.93),(REVEAL,[.288,.298,.286],.88)]}
def texture():
    p=Path(__file__).with_name('fired-clay.png')
    if not p.exists():
        g=np.random.default_rng(799)
        y,x=np.indices((256,256))
        a=np.array([162,99,72])+g.normal(0,5,(256,256,1))+6*np.sin((x*.05+y*.009)[:,:,None])
        Image.fromarray(a.clip(0,255).astype('uint8')).quantize(92).save(p)
    PALETTE[TILE]['texture']=str(p)
def roof_height(y):return .194+.79*y
def add_building(b,far=False):
    texture()
    def rect(l,r,z,t,ymin,ymax,material,label):b.box(((l+r)/2,(ymin+ymax)/2,(z+t)/2),(r-l,ymax-ymin,t-z),material,label=label)
    def roof(poly,lo,hi,m,label):b.prism(poly,lo,hi,lambda x,y,h:(x,y,roof_height(y)+h),m,label)
    open_space=box(-.548,.238,.548,1.416)
    roof(box(-1.50,0,1.5,1.76).difference(open_space),-.058,0,JOINT,'Continuous sloping roof cut around dormer')
    for z,t,y0 in [(-.127,-.092,-.059),(-.092,-.047,-.078),(-.047,-.017,-.112),(-.017,.012,-.140),(.012,.054,-.142),(.054,.093,-.121),(.093,.132,-.160),(.132,.171,-.174)]:
        rect(-1.5,1.5,z,t,y0,.071,EAVE,'Repeated mouldings along the lower eave')
    rect(-1.50,1.50,-.22,-.125,-.025,.096,TAN,'Narrow visible wall beneath roof')
    # Map each tile separately so its entire authored clay surface fits the sampler.
    verts=[];faces=[];uv=[]
    for j in range(16):
        y0=j*.111;y1=min(y0+.124,1.76)
        for i in range(28):
            x0=-1.50+i*3/28+.0012;x1=-1.50+(i+1)*3/28-.0012
            covers=x0<.548 and x1>-.548 and y0<1.416 and y1>.238
            xs=[x0]+([u for u in (-.548,.548) if x0<u<x1] if covers else [])+[x1]
            ys=[y0]+([u for u in (.238,1.416) if y0<u<y1] if covers else [])+[y1]
            for lo,hi in zip(xs,xs[1:]):
                for front,back in zip(ys,ys[1:]):
                    if -.548<(lo+hi)/2<.548 and .238<(front+back)/2<1.416:continue
                    n=6 if far else 12
                    start=len(verts)
                    for yy in [front,back]:
                        along=(yy-y0)/(y1-y0)
                        for hfrac in [0,1]:
                            for k in range(n+1):
                                xx=lo+(hi-lo)*k/n;frac=(xx-x0)/(x1-x0)
                                zz=roof_height(yy)+.010+.025*(.5+.5*math.cos(2*math.pi*(frac-.31)))**1.4
                                zz+=.005*(1-(j%3)*.12)+.014*(1-along)-(.016 if not hfrac else 0)
                                verts.append((xx,yy,zz));uv.append((.015+frac*.97,.99-.98*along))
                    w=n+1
                    for k in range(n):
                        a=start+w+k;c=start+3*w+k
                        faces.append((a,a+1,c+1,c));faces.append((start+k,start+k+1,a+1,a))
                        faces.append((start+2*w+k,c,c+1,start+2*w+k+1))
                    faces.extend([(start,start+w,start+3*w,start+2*w),(start+n,start+2*w+n,start+3*w+n,start+w+n)])
    b.add(verts,faces,TILE,'Individual curved and overlapping tiles on two sides of the dormer')
    b.parts[-1]['texcoords']=uv
    for side in [-1,1]:
        l,r=sorted((side*.533,side*.574))
        cross=Polygon([(.230,roof_height(.23)-.003),(1.435,roof_height(1.435)-.003),(1.435,1.454),(.230,1.340)])
        b.prism(cross,l,r,lambda y,z,x:(x,y,z),FLASH,'Sloping dark cheek against dormer')
        rect(l-.014,r+.014,roof_height(.23)-.02,1.33,.213,.238,FLASH,'Folded corner flashing at sill')
    rect(-.547,.547,roof_height(.23)-.016,.493,.222,.305,BATTEN,'Deep dark metal apron')
    rect(-.55,.55,.491,1.310,.286,.34,REVEAL,'Dark reveal surrounding two pale sashes')
    for mid in [-.239,.239]:
        rect(mid-.218,mid+.218,.536,1.266,.271,.298,GLASS,'Glazed light visible above the modern obstruction')
        for x in [mid-.213,mid+.202]:
            rect(x,x+.018,.52,1.274,.249,.274,SASH,'Slim painted upright of sash')
        for z in [.522,1.254]:
            rect(mid-.216,mid+.216,z,z+.022,.247,.278,SASH,'Horizontal painted sash rail')
    rect(-.012,.012,.519,1.28,.232,.275,SASH,'Centre sash meeting rail')
    b.prism(box(-.605,.102,.605,1.46),-.035,.034,lambda x,y,z:(x,y,1.356+.093*(y-.10)+z),CAP,'Single shallow sloping dormer cap')
    rect(-.623,.623,1.295,1.398,.092,.139,CAP,'Dark projecting front fascia')
