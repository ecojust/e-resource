"""Street-facing tower, entrance and curved shoulders of the former China State Bank."""
from math import cos,sin,pi
from pathlib import Path
import numpy as np
from shapely.affinity import translate
from shapely.geometry import box,Point,Polygon,LineString
from shapely.ops import unary_union
from photo_architecture import Facade
from sign_lettering import lettering_shapes

STONE='weathered grey granite';EDGE='light grey cut granite';BAND='dark granite course';RENDER='grey render';REED='grey spandrel';GLASS='smoky blue glass';FRAME='dark steel sash';IRON='black patinated iron';GOLD='aged brass';CUT='plain section'
PALETTE={STONE:{'color':[.47,.45,.42],'roughness':.81},EDGE:{'color':[.63,.60,.54],'roughness':.76},BAND:{'color':[.337,.331,.31],'roughness':.80},RENDER:{'color':[.565,.54,.49],'roughness':.89},REED:{'color':[.494,.48,.45],'roughness':.87},GLASS:{'color':[.181,.24,.28],'metallic':.19,'roughness':.34},FRAME:{'color':[.153,.164,.17],'metallic':.26,'roughness':.51},IRON:{'color':[.128,.129,.122],'metallic':.49,'roughness':.46},GOLD:{'color':[.64,.505,.307],'metallic':.54,'roughness':.51},CUT:{'color':[.394,.381,.353],'roughness':.91}}
HALF=4.57
DEPTH=2.75
# Interpolated street-edge tangents. The mapped entrance has a separate ground-level recess.
LEFT=((-9.96,4.56),(-8.22,.74),(-HALF,0.0))
RIGHT=((HALF,0.0),(8.02,-.94),(10.66,2.00))
FLOORS=[11.85,15.87,19.89,23.91,27.93,31.95,35.97]


def bezier(curve,t):
    a,b,c=map(np.array,curve)
    return (1-t)**2*a+2*t*(1-t)*b+t*t*c


def arch(x,z,w,top,steps=32):
    r=w/2;spring=top-r
    return Polygon([(x-r,z),(x+r,z),*[(x+r*cos(pi*i/steps),spring+r*sin(pi*i/steps))for i in range(steps+1)]])


def light(f,x,z,w,h):
    q=box(x-w/2,z,x+w/2,z+h);f.prism(q.buffer(.009,join_style=2),-.31,-.29,GLASS,'recessed steel window')
    sash=unary_union([q.difference(q.buffer(-.049,join_style=2)),box(x-w/2,z+h*.72-.024,x+w/2,z+h*.72+.024),box(x-.032,z,x+.032,z+h*.72)])
    f.prism(sash,-.278,-.233,FRAME,'mullions and transoms');f.prism(box(x-w/2-.047,z-.058,x+w/2+.047,z+.03),-.012,.072,BAND,'shallow stone sills');return q


def spandrel(f,x,w,z,h,lod):
    f.prism(box(x-w/2,z,x+w/2,z+h),-.015,.015,REED,'inset spandrel panels')
    if not lod:
        edge=.086;lines=[box(x-w/2+edge,z+.06,x-w/2+edge+.023,z+h-.07),box(x+w/2-edge-.023,z+.06,x+w/2-edge,z+h-.07)]
        f.prism(unary_union(lines),.019,.034,BAND,'paired vertical spandrel incisions')


def z_range(f,wall_top,base_x,width,upper_rows,lod):
    holes=[]
    for z in upper_rows:
        holes.append(light(f,base_x,z,width,2.12))
        if z!=upper_rows[-1]:spandrel(f,base_x,width,z+2.18,1.65,lod)
    return holes


def curved_wing(b,curve,lod):
    # Each of the three lights follows its own tangent. The parapet and base rails
    # use additional facets to follow the curved face between those windows.
    for i in range(3):
        a,c=bezier(curve,i/3),bezier(curve,(i+1)/3);f=Facade(b,a,c,'curved shoulder');half=f.length/2
        holes=z_range(f,40.54,0,1.38,FLOORS,lod)
        f.prism(box(-half,10.68,half,40.69).difference(unary_union(holes)),-.38,0,RENDER,'curve of upper storeys')
        for sign in [-1,1]:f.prism(box(sign*half-.038,10.7,sign*half+.038,40.55),.005,.082,STONE,'joint of curved window bays')
        # Stone-framed rectangular lights on the two-storey granite base.
        bays=[light(f,0,1.18,1.43,3.63),light(f,0,6.30,1.43,2.79)]
        f.prism(box(-half,0,half,10.75).difference(unary_union(bays)),-.38,0,STONE,'granite shoulder')
        q=box(-.56,38.65,.56,39.97);f.prism(q,.004,.027,REED,'ornamental square above wing window')
        cx=0;cz=39.30
        emblem=Polygon([(cx,cz+.43),(cx+.24,cz+.10),(cx+.32,cz-.04),(cx+.18,cz-.018),(cx+.25,cz-.25),(cx+.06,cz-.13),(cx,cz-.38),(cx-.06,cz-.13),(cx-.25,cz-.25),(cx-.18,cz-.018),(cx-.32,cz-.04),(cx-.24,cz+.10)])
        f.prism(emblem,.033,.089,EDGE,'geometric bas-relief panel')
    # One mitered rear edge joins all three curved bays and the straight tower.
    # Independent perpendicular returns at every bay would leave fissures between them.
    frontage=[bezier(curve,t/12)for t in range(13)]
    rear=[]
    for i,q in enumerate(frontage):
        t=i/12;a,m,c=map(np.array,curve)
        tangent=(1-t)*(m-a)+t*(c-m);tangent/=np.linalg.norm(tangent)
        rear.append(q+DEPTH*np.array([-tangent[1],tangent[0]]))
    if curve==LEFT:rear[-1]=np.array([-HALF,DEPTH])
    else:rear[0]=np.array([HALF,DEPTH])
    outline=Polygon([*frontage,*reversed(rear)])
    assert outline.is_valid
    b.plan_prism(outline,0,.05,CUT,'continuous floor section')
    b.plan_prism(outline,40.48,40.62,CUT,'continuous curved roof section')
    for a,c in zip(rear,rear[1:]):
        b.add([(*a,0),(*a,40.56),(*c,40.56),(*c,0)],[(0,1,2,3)],CUT,'continuous curved rear section')
    for j in range(12):
        a,c=bezier(curve,j/12),bezier(curve,(j+1)/12);f=Facade(b,a,c,'curved cornices');r=f.length/2
        for z,h,d,m in [(0,.46,.09,BAND),(5.25,.15,.095,EDGE),(9.50,.95,.11,EDGE),(10.54,.19,.17,BAND),(40.05,.48,.11,EDGE),(40.51,.22,.15,BAND)]:f.prism(box(-r-.005,z,r+.005,z+h),-.035,d,m,'curved belt and coping')
        for x in [-r*.57,0,r*.57]:
            if not lod:f.prism(box(x-.023,9.65,x+.023,10.25),.113,.135,STONE,'fluted belt')


def entrance(f,b,lod):
    r=2.64;top=9.64;spring=top-r;hole=arch(0,0,r*2,top,26 if lod else 44)
    # Continuous stepped granite archivolts with vertical jambs.
    for offset,depth,height,m in [(.47,.14,.12,STONE),(.31,.20,.10,EDGE),(.16,.245,.070,STONE)]:
        outer=hole.buffer(offset,join_style=2).difference(hole.buffer(max(0,offset-height),join_style=2));outer=outer.intersection(box(-4.10,.08,4.10,10.38));f.prism(outer,.008,depth,m,'granite archivolt and jamb')
    frame=hole.difference(hole.buffer(-.17,join_style=2));f.prism(frame,-.19,-.09,IRON,'wrought iron entrance frame')
    fan=hole.intersection(box(-r,spring,r,top));f.prism(fan,-.30,-.27,GLASS,'fanlight glazing')
    spider=[]
    for i in range(1,18):
        a=i*pi/18;spider.append(LineString([(cos(a)*.58,spring+sin(a)*.58),(cos(a)*(r-.11),spring+sin(a)*(r-.11))]).buffer(.034,cap_style='flat'))
    for radius in [.58,1.64,2.22]:spider.append(Point(0,spring).buffer(radius,quad_segs=18 if lod else 33).boundary.buffer(.044).intersection(fan))
    f.prism(unary_union(spider).intersection(fan),-.212,-.094,IRON,'radial iron fanlight')
    f.prism(box(-r+.07,spring-.37,r-.07,spring+.035),-.20,-.045,IRON,'entrance transom')
    inner=Facade(b,(-HALF,1.62),(HALF,1.62),'inner glazing');inner.prism(box(-r+.19,1.12,r-.19,spring-.37),-.065,-.04,GLASS,'recessed entrance glazing')
    bars=[box(-r+.18,4.28,r-.18,4.41)]
    for x in [-1.66,-.03,1.66]:bars.append(box(x-.047,1.11,x+.047,spring-.37))
    inner.prism(unary_union(bars),-.025,.034,FRAME,'entrance glazing bars')
    for side in [-1,1]:b.box((side*(r-.13),.83,(spring-.37)/2),(.17,1.59,spring-.37),STONE,label='stone portal returns')
    for j in range(8):
        y=.03+j*.196;h=.142*(j+1);b.box((0,(y+1.63)/2,h/2),(4.86,1.63-y,h),EDGE,label='granite entrance steps')
    f.prism(box(-2.87,10.40,2.87,10.58),-.045,.24,BAND,'stone tablet shelf')
    font=Path(__file__).with_name('fonts')/'GuohuaPortal.otf'
    for x,ch in zip([-2.04,-.68,.68,2.04],'樓大華國'):
        f.prism(box(x-.61,10.62,x+.61,11.71),.008,.142,EDGE,'individual plaque block')
        f.prism(box(x-.54,10.70,x+.54,11.64),.145,.175,STONE,'inset tablet panel')
        for _,shape in lettering_shapes(ch,.84,.71,font=font):f.prism(translate(shape,xoff=x,yoff=11.18),.179,.219,GOLD,'restored raised tablet '+ch)
    return hole


def add_corner(b,lod):
    f=Facade(b,(-HALF,0),(HALF,0),'southeast entrance');holes=[entrance(f,b,lod)]
    upper=FLOORS+[39.99]
    for x in [-1.57,0,1.57]:holes.extend(z_range(f,48.34,x,1.25,upper,lod))
    for x in [-1.38,1.38]:
        q=box(x-.48,45.97,x+.48,46.82);holes.append(q);f.prism(q.buffer(.007,join_style=2),-.35,-.32,FRAME,'small recessed attic light')
    f.prism(box(-HALF,0,HALF,48.76).difference(unary_union(holes)),-.4,0,STONE,'street tower and granite portal wall')
    for x in [-4.22,4.22]:
        for w,d,top in [(.64,.09,48.16),(.38,.19,48.61),(.15,.24,48.85)]:f.prism(box(x-w/2,.12,x+w/2,top),.012,d,STONE,'rising stepped corner rib')
    for x in [-2.37,-.78,.78,2.37]:f.prism(box(x-.064,11.90,x+.064,44.02),.008,.108,EDGE,'three-bay tower mullion')
    f.prism(box(-2.52,44.02,2.52,44.24),.009,.15,BAND,'framed tower recess')
    for x in [-1.57,0,1.57]:
        q=box(x-.59,42.56,x+.59,43.69);rim=q.difference(q.buffer(-.085,join_style=2));f.prism(rim,.012,.09,REED,'framed attic spandrels')
    for h,w in [(48.32,8.75),(48.64,8.91),(48.80,8.4)]:f.prism(box(-w/2,h,w/2,h+.09),-.14,.16,EDGE,'stepped tower coping')
    curved_wing(b,LEFT,lod);curved_wing(b,RIGHT,lod)
    b.box((0,DEPTH/2,.026),(2*HALF,DEPTH,.052),CUT,label='continuous central floor section')
    b.box((0,DEPTH-.08,24.36),(2*HALF,.16,48.72),CUT,label='back of tower section');b.box((0,(.40+DEPTH)/2,48.69),(2*HALF,DEPTH-.40,.16),CUT,label='top of tower section')
    # The upper tower walls are visible above the curved shoulders on both sides.
    for x in [-HALF+.07,HALF-.07]:b.box((x,DEPTH/2,44.69),(.14,DEPTH,8.05),STONE,label='upper tower returns')
    for curve,t in [(LEFT,0),(RIGHT,1)]:
        u=bezier(curve,t);near=bezier(curve,.002 if t==0 else .998);v=near-u
        if t==1:v=-v
        v=v/np.linalg.norm(v);inward=np.array([-v[1],v[0]]);a=tuple(u);c=tuple(u+DEPTH*inward);side=Facade(b,a,c,'end section');side.prism(box(-DEPTH/2,0,DEPTH/2,40.5),-.05,.05,CUT,'plain end section')
