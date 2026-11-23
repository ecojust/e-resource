"""Courtyard side, external galleries and freestanding concrete stair towers."""
from pathlib import Path
from math import ceil
import numpy as np
from shapely.geometry import Polygon,box as rect
from shapely.ops import unary_union
S=Path(__file__).parent
C='Court | washed aggregate';B='Court | red brick';G='Court | grey coping'
SL='Court | floor concrete';D='Court | stained timber';V='Court | muted glazing'
I='Court | iron';F='Court | dark roof felt';P='Court | worn cream render';SH='Court | deep reveals'
def mat(rgb,r=.85):return {'color':[v/255 for v in rgb],'roughness':r}
PALETTE={C:{'texture':str(S/'courtyard-aggregate.png'),'color':[1,1,1],'roughness':.97},
 B:{'texture':str(S/'gallery-red-brick.png'),'color':[1,1,1],'roughness':.94},G:mat((143,140,129)),
 SL:mat((125,122,112)),D:mat((106,65,48)),V:mat((77,93,93),.35),
 I:mat((66,66,60),.54),F:mat((75,75,71)),P:mat((169,161,147)),SH:mat((62,64,60))}
UP=np.array([0.,0.,1.])
class Bay:
    def __init__(self,b,a,z,name):
        self.builder=b;self.a=np.array([*a,0.]);end=np.array([*z,0.]);self.length=float(np.linalg.norm(end-self.a));self.t=(end-self.a)/self.length;self.n=np.cross(UP,self.t);self.name=name
    def pt(self,s,d,z):return self.a+self.t*s+self.n*d+UP*z
    def box(self,s,d,z,w,depth,height,material,name):
        self.builder.box(self.pt(s,d,z),(w,depth,height),material,[self.t,self.n,UP],self.name+' '+name)
    def surface(self,poly,back,front,material,name):
        # Tangent cross up points away from the courtyard.
        self.builder.prism(poly,-front,-back,lambda u,z,nd:self.pt(u,-nd,z),material,self.name+' '+name)
    def section(self,poly,s0,s1,material,name):
        self.builder.prism(poly,s0,s1,lambda d,z,u:self.pt(u,d,z),material,self.name+' '+name)
    def tube(self,p,q,r,material,name,sides):
        self.builder.tube([self.pt(*p),self.pt(*q)],r,material,sides,self.name+' '+name)
def frame(b,layout,i):
    pts=layout['court_corners'];return Bay(b,pts[i],pts[(i+1)%4],layout['face_order'][i].replace('_',' '))
def parapet(w,a,b,level,z,L):
    if b-a<.1:return
    n=L['parapet_height'];w.box((a+b)/2,0,z+n/2,b-a,.14,n,C,f'gallery {level} parapet')
    w.box((a+b)/2,.015,z+n+.022,b-a,.20,.044,G,f'gallery {level} coping')
def gallery_wall(w,L,level,lod):
    h=L['storey_pitch'];z=level*h;depth=L['gallery_depth'];span=w.length;count=max(4,round(span/4.4));pitch=span/count
    holes=[];frames=[]
    for j in range(count):
        start=j*pitch;door=start+pitch*.28;window=start+pitch*.72
        openings=[(door,.88,.025,2.24,'door'),(window,1.16,.98,2.34,'window')]
        for x,width,bottom,top,kind in openings:
            frames.append((x,width,z+bottom,z+top,kind))
    if level==0 and w.name=='street' and L.get('public_entrance'):
        a,b=L['public_entrance']['inner_s'];holes.append(rect(a,z-.01,b,z+L['public_entrance']['height']))
        frames=[v for v in frames if v[0]+v[1]/2<a or v[0]-v[1]/2>b]
    holes.extend(rect(x-width/2,bot,x+width/2,top) for x,width,bot,top,kind in frames)
    wall=rect(0,z,span,z+h).difference(unary_union(holes))
    w.surface(wall,-depth-.29,-depth,B,f'inner wall level {level+1}')
    for x,width,bot,top,kind in frames:
        hi=top-bot;label=f'{kind} series {level+1}'
        w.box(x,-depth-.10,(top+bot)/2,width,.055,hi,D if kind=='door' else V,label)
        for s in (x-width/2+.025,x+width/2-.025):
            w.box(s,-depth-.044,(bot+top)/2,.05,.065,hi,D,label+' frame')
        w.box(x,-depth-.04,top-.038,width,.065,.076,D,label+' frame')
        if kind=='window':
            w.box(x,-depth-.046,(bot+top)/2,.042,.05,hi,D,label+' sash')
            if not lod:w.box(x,-depth-.037,bot+hi*.68,width,.05,.039,D,label+' sash')
            w.box(x,-depth+.01,bot-.025,width+.15,.24,.08,G,label+' sill')
def flight(w, profile, low, high, cross, material, label):
    if cross:
        w.surface(profile,low,high,material,label)
    else:
        w.section(profile,low,high,material,label)

def stair_run(w, l0, l1, z0, z1, edge, inside, cross, level, number, lod):
    # Tread and soffit form one closed prism; the parapet remains an independent sloped plate.
    count=max(4,round(abs(z1-z0)/.17));along=np.linspace(l0,l1,count+1);heights=np.linspace(z0,z1,count+1)
    plus=z1>z0;tread=[(l0,z0)]
    for k in range(count):
        z=heights[k+1 if plus else k]
        if abs(z-tread[-1][1])>1e-7:tread.append((along[k],z))
        tread.append((along[k+1],z))
    if abs(tread[-1][1]-z1)>1e-7:tread.append((l1,z1))
    name=f'flight {level+1}.{number}'
    flight(w,Polygon(tread+[(l1,z1-.19),(l0,z0-.19)]),min(edge,inside),max(edge,inside),cross,SL,name)
    for dz,thickness,mat,tag in [(0,.8,C,' spandrel'),(.8,.055,G,' coping')]:
        poly=Polygon([(l0,z0+dz),(l1,z1+dz),(l1,z1+dz+thickness),(l0,z0+dz+thickness)])
        at=edge+(.13 if inside>edge else -.13)
        flight(w,poly,min(edge,at),max(edge,at),cross,mat,name+tag)
    if not lod:
        mapping=lambda l,z:(l,inside,z) if cross else (inside,l,z)
        w.tube(mapping(l0,z0+.86),mapping(l1,z1+.86),.024,I,name+' rail',8)
        for k in range(4):
            r=k/3;u,d,z=mapping(l0+(l1-l0)*r,z0+(z1-z0)*r+.42)
            w.box(u,d,z,.036,.036,.84,I,name+' rail post')

def tower(w,layout,register,lod):
    s=register['along'];width=register['width'];depth=register['projection'];h=layout['storey_pitch'];half=width/2
    left,right=s-half,s+half;t0=depth/3;t1=2*depth/3
    wing=min(2.25,depth*.26);cap=5*h+2.62
    for ix,x in enumerate([left,left+width/3,left+2*width/3,right]):
        for iy,y in enumerate([0,t0,t1,depth]):
            if ix in [1,2] and iy in [1,2]:continue
            w.box(x,y,cap/2,.30,.30,cap,C,f'stair pier {ix+1}-{iy+1}')
    def slab(x0,x1,y0,y1,z,label):
        w.box((x0+x1)/2,(y0+y1)/2,z-.095,x1-x0,y1-y0,.19,SL,label)
    def wall(x0,x1,y0,y1,z,label):
        w.box((x0+x1)/2,(y0+y1)/2,z+.40,x1-x0,y1-y0,.80,C,label)
        w.box((x0+x1)/2,(y0+y1)/2,z+.825,x1-x0,y1-y0,.05,G,label+' cap')
    for level in range(5):
        z=level*h;zl=z+.25*h;zr=z+.75*h;za=z+h
        # Photographs F07, F16 and F17 show the front sloping bay and the orthogonal side flights.
        stair_run(w,t0,t1,z,zl,left,left+wing,False,level,1,lod)
        stair_run(w,left+width/3,left+2*width/3,zl,zr,depth,depth-wing,True,level,2,lod)
        stair_run(w,t0,t1,za,zr,right,right-wing,False,level,3,lod)
        for x0,x1,edge,sign,inner,outer in [(left,left+wing,left,1,z,zl),(right-wing,right,right,-1,za,zr)]:
            slab(x0,x1,0,t0,inner,f'gallery-side stair landing {level+1}')
            slab(x0,x1,t1,depth,outer,f'outer stair landing {level+1}')
            for y0,y1,zp in [(0,t0,inner),(t1,depth,outer)]:
                wall(min(edge,edge+sign*.13),max(edge,edge+sign*.13),y0,y1,zp,f'side flat parapet {level+1}')
        for lo,hi,zp in [(left,left+width/3,zl),(left+width*2/3,right,zr)]:
            slab(lo,hi,depth-wing,depth,zp,f'cross landing {level+1}')
            wall(lo,hi,depth-.13,depth,zp,f'outer flat parapet {level+1}')
    w.box(s,t0/2,5*h-.1,width,t0,.2,SL,'roof access landing')
    w.box(s,depth/2,cap-.16,width+.75,depth+.75,.32,C,'stair canopy')
    w.box(s,depth/2,cap+.025,width+.77,depth+.77,.05,F,'stair cap flashing')
    # Recessed panels under the roof carry the stepped chevrons photographed in F17.
    for y in [0,depth]:
        w.box(s,y,cap-.73,width,.16,1.04,C,'stair frieze cross')
        if not lod and y==depth:
            for j in range(3):
                for k in range(3):
                    mid=left+(j+(k+.5)/3)*width/3;u=width/23.0
                    plane=depth+.087;base=cap-.92
                    w.tube((mid-u,plane,base),(mid,plane,base+.105),.034,G,'cross chevron',5)
                    w.tube((mid,plane,base+.105),(mid+u,plane,base),.034,G,'cross chevron',5)
    for side in [-1,1]:
        for d0,d1 in zip([0,t0,t1],[t0,t1,depth]):
            w.box(s+side*half,(d0+d1)/2,cap-.73,.16,d1-d0,1.04,C,'stair frieze side')
            if not lod and d1-d0>1.4:
                for k in range(3):
                    mid=d0+(k+.5)*(d1-d0)/3;u=(d1-d0)/7.5;edge=s+side*(half+.087);base=cap-.92
                    w.tube((edge,mid-u,base),(edge,mid,base+.105),.034,G,'pressed chevron',5)
                    w.tube((edge,mid,base+.105),(edge,mid+u,base),.034,G,'pressed chevron',5)
def add_court(b,lod,layout):
    pts=layout['court_corners'];outer=Polygon(layout['outer_corners']);court=Polygon(pts);depth=layout['gallery_depth'];behind=court.buffer(depth,join_style=2)
    h=layout['storey_pitch']
    b.plan_prism(court,-.16,.015,SL,'Central court paving')
    # The concrete deck ends inside the brick shell. The courtyard edge stays visible.
    floor_outline=outer.buffer(-.12,join_style=2).difference(court)
    for n in range(1,6):
        b.plan_prism(floor_outline,n*h-layout['slab_thickness'],n*h,SL,f'Housing floor {n}' if n<5 else 'Roof deck')
    b.plan_prism(outer.buffer(-.2,join_style=2).difference(court.buffer(.20,join_style=2)),5*h,5*h+.035,F,'Four wings roof felt')
    for i in range(4):
        w=frame(b,layout,i);reg=layout['stairs'].get(w.name);prof=layout['parapet_height']; gap=(reg['along']-reg['width']/2,reg['along']+reg['width']/2) if reg else (0,0)
        for n in range(5):gallery_wall(w,layout,n,lod)
        for n in range(1,5):
            parapet(w,0,gap[0],n,n*h,layout);parapet(w,gap[1],w.length,n,n*h,layout)
            if not lod:
                for s in np.arange(1.8,w.length-1.0,3.9):
                    if gap[0]-.5<s<gap[1]+.5:continue
                    w.tube((s,.08,n*h+.16),(s,.79,n*h+.82),.017,I,f'rail bracket {n}',6)
                    w.tube((s,.79,n*h+.82),(s,.08,n*h+.82),.017,I,f'rail bracket {n}',6)
        w.box(w.length/2,0,5*h+.33,w.length,.17,.66,G,'roof parapet')
        w.box(0,0,2.5*h+.40,.48,.48,5*h+.8,C,'corner column')
        if reg:tower(w,layout,reg,lod)
