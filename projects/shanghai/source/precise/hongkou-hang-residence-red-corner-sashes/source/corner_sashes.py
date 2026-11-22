"""Recessed red corner light at the former Hang residence on Zhoushan Road."""
from pathlib import Path
from math import cos, sin, radians
import numpy as np
from PIL import Image
from shapely.geometry import box, Polygon
ID='hongkou-hang-residence-red-corner-sashes'
WALL='Coarse shaded exterior render';GLASS='Soft grey sky in the recessed glass';POST='Oxide-red steel stiles';FINE='Red painted lower glazing bars';PUTTY='Narrow weathered glazing putty';STONE='Pale concrete sill';SHADOW='Dark inner reveal';GRAIN='Sill edge aggregate'
PALETTE={name:dict(color=color,roughness=rough) for name,color,rough in [(WALL,[.265,.238,.178],.94),(GLASS,[1,1,1],.36),(POST,[.36,.110,.065],.66),(FINE,[.425,.148,.082],.61),(PUTTY,[.51,.348,.235],.85),(STONE,[.603,.557,.45],.90),(SHADOW,[.156,.13,.102],.96),(GRAIN,[.38,.353,.294],.96)]}
def texture():
    image=Path(__file__).with_name('clouded-panes.png')
    if not image.is_file():
        random=np.random.default_rng(667)
        field=np.asarray(Image.fromarray(random.integers(0,256,(6,11),'uint8')).resize((320,224),Image.Resampling.BICUBIC),float)/255
        y=np.linspace(0,1,224)[:,None];values=np.array([157,163,160])+(field+.5*y)[:,:,None]*[34,28,32]+random.normal(0,1.7,(224,320,1))
        Image.fromarray(np.clip(values,0,255).astype('uint8')).save(image)
    PALETTE[GLASS]['texture']=str(image)

# Each run starts at the same corner post. The second face returns towards the back.
PLAN=(((-1.48,.38),(0.,-.21),2),((0.,-.21),(.91,.44),1))
def frame(i):
    a,b,count=PLAN[i];start=np.array(a);end=np.array(b);length=np.linalg.norm(end-start)
    u=(end-start)/length;out=np.array([u[1],-u[0]])
    a2,b2,_=PLAN[1-i];v=np.array(b2)-a2;v/=np.linalg.norm(v);other=np.array([v[1],-v[0]])
    miter=(out+other)/(1+np.dot(out,other))
    def xyz(t,z,depth):
        fraction=t/length if i==0 else 1-t/length
        xy=start+t*u+depth*(out+fraction*(miter-out))
        return (float(xy[0]),float(xy[1]),z)
    return length,count,xyz,out
def add_building(builder,far=False):
    texture()
    for i in range(2):
        length,count,xyz,out=frame(i)
        def cut(s,t,z,h,d,e,mat,label):
            builder.prism(box(s,z,t,h),d,e,xyz,mat,label)
        cut(0,length,0,.31,-.23,-.012,WALL,'Corner sill spandrel')
        cut(0,length,1.94,2.15,-.23,-.012,WALL,'Shaded underside and head')
        cut(0,length,.291,.358,-.235,.085,STONE,'Returning projected sill')
        cut(0,length,.344,.375,-.06,.067,STONE,'Sill wash')
        for s,t in [(0,.035),(length-.035,length)]:
            cut(s,t,.36,1.95,-.19,.022,POST,'Red perimeter or corner stile')
        for z,h in [(.376,.411),(1.285,1.33),(1.887,1.937)]:
            cut(0,length,z,h,-.131,.006,POST,'Three continuous rails around the corner')
        for bay in range(count):
            left=length*bay/count;right=length*(bay+1)/count;centre=(left+right)/2
            for lo,hi in ((.403,1.29),(1.326,1.895)):
                cut(left+.021,right-.021,lo,hi,-.17,-.151,GLASS,'Transom or vertical lower light')
            cut(centre-.013,centre+.013,.41,1.286,-.126,-.015,FINE,'Narrow lower vertical in each bay')
            if bay:
                cut(left-.018,left+.018,.391,1.913,-.137,.006,POST,'Continuous division between upper panes')
            if not far:
                for seam in (left+.024,right-.024):
                    cut(seam-.004,seam+.004,.412,1.282,-.145,-.10,PUTTY,'Glazing putty at the outer lights')
                cut(left+.024,right-.024,1.334,1.341,-.147,-.111,PUTTY,'Putty bedding above meeting rail')
        # Two short returns close the cut study without extending to adjacent openings.
        if i==0:cut(-.13,0.,0,2.15,-.23,-.006,WALL,'Left outer jamb')
        else:cut(length,length+.13,0,2.15,-.23,-.006,WALL,'Right outer jamb')
        for part in builder.parts:
            if part['material']==GLASS and 'texcoords' not in part:
                a=np.array(PLAN[i][0]);zdir=(np.array(PLAN[i][1])-a)/length
                part['texcoords']=[[float(np.dot(np.array([x,y])-a,zdir)/length),float((z-.38)/1.55)] for x,y,z in part['vertices']]
