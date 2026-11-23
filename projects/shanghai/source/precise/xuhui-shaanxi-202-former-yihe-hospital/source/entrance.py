"""Entrance of the former Yihe Hospital, recovered from the 2015–18 courtyard and door photographs."""
from pathlib import Path
import json
import math

import numpy as np
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union

HERE=Path(__file__).absolute().parent
ASH='Yihe | grey granite ashlar'
JOINT='Yihe | recessed grey joints'
CREAM='Yihe | pale canopy moulding'
SOFFIT='Yihe | warm ivory vault'
CAP='Yihe | grey metal barrel roof'
OAK='Yihe | dark stained surround'
IRON='Yihe | pierced ornamental gate'
BRASS='Yihe | aged lamp metal'
LAMP='Yihe | amber opal glass'
GLOBE='Yihe | illuminated vestibule globe'
SHADOW='Yihe | shaded vestibule'
PAVER='Yihe | grey step granite'
RUNNER='Yihe | muted red mat'
INLAY='Yihe | dark threshold inlay'
PALETTE={ASH:('#b5ada0',.9),JOINT:('#898577',.92),CREAM:('#ddcaae',.85),
         SOFFIT:('#d7cbb6',.92),CAP:('#90918c',.7),OAK:('#50372d',.64),
         IRON:('#372a25',.63),BRASS:('#786858',.55),LAMP:('#d0c9a9',.44),GLOBE:('#ffdb8c',.34),
         SHADOW:('#53483a',.97),PAVER:('#aca69c',.93),RUNNER:('#805046',.97),INLAY:('#68675e',.83)}
def material(hexcolor,roughness):
    rgb=np.asarray(list(bytes.fromhex(hexcolor.lstrip('#'))),dtype=float)/255.
    return dict(color=np.where(rgb<.04045,rgb/12.92,((rgb+.055)/1.055)**2.4).tolist(),roughness=roughness)
PALETTE={k:material(v,r) for k,(v,r) in PALETTE.items()}

def solid(b,x0,x1,y0,y1,z0,z1,mat,label):
    b.box(((x0+x1)/2,(y0+y1)/2,(z0+z1)/2),(x1-x0,y1-y0,z1-z0),mat,label=label)
def face(b,polygon,y0,y1,mat,label):
    if not polygon.is_empty:
        b.prism(polygon,-y1,-y0,lambda x,z,d:(x,-d,z),mat,label)
def circular_segment(x,half,h):
    radius=(half*half+h*h)/(2*h)
    return np.sqrt(np.maximum(0,radius*radius-np.asarray(x)**2))-(radius-h)
def cap_profile(cx,half,rise,spring,n,drop,wing):
    xx=np.linspace(-half,half,n)
    return [(cx-half-wing,spring-drop),*zip(cx+xx,spring-drop+circular_segment(xx,half,rise)),
            (cx+half+wing,spring-drop)]
def ribbon(top,bottom):
    return Polygon([*top,*reversed(bottom)])
def downlight(b,x,y,z,r,mat,lod,name):
    b.lathe((x,y),[(z-.75*r,.22*r),(z-.63*r,.66*r),(z-.27*r,.94*r),(z,r),(z+.06*r,r)],mat,14 if lod else 28,name)
def hood(b,record,lod):
    cx,a,y,s,h=(record[k] for k in ('center_x','radius_x','front_y','spring_z','rise_z'))
    def shape(drop,wing=.22,half=a):
        return cap_profile(cx,half,h,s,21 if lod else 45,drop,wing)
    rear=-.33
    face(b,ribbon(shape(0),shape(.095)),y,rear,CAP,'Entrance | rolled barrel sheet and two side wings')
    face(b,ribbon(shape(.092),shape(.15)),y+.02,rear,SOFFIT,'Entrance | cream cylindrical soffit')
    for i,(dz,depth,wing) in enumerate([(0,.055,.3),(.044,.088,.29),(.085,.052,.24),(.125,.04,.21)]):
        face(b,ribbon(shape(dz,wing),shape(dz+.045,wing)),y-depth,y+.055,CREAM,'Entrance | stepped cornice lip '+str(i+1))
    for yp in np.linspace(y+.2,rear-.1,4):
        if lod and yp<y+.3:continue
        face(b,ribbon(shape(-.011,.212),shape(.003,.212)),yp,yp+.021,CAP,'Entrance | rolled sheet transverse seam')
    # These back stones are visible through the open vault.
    top=shape(.16,0)
    face(b,Polygon([*top,(top[-1][0],4.185),(top[0][0],4.185)]),-1.08,rear,ASH,'Entrance | stone tympanum above lintel')
    for x in (cx-.84,cx-.20,cx+.60):
        local=x-cx;zt=s-.16+float(circular_segment(local,a,h))
        solid(b,x-.004,x+.004,-1.083,-1.075,4.19,zt,JOINT,'Entrance | tympanum ashlar break')
    downlight(b,cx,-1.75,s+h-.153,.142,BRASS,lod,'Entrance | round canopy downlight bezel')
    downlight(b,cx,-1.75,s+h-.210,.104,LAMP,lod,'Entrance | canopy opal lens')

def cut_gate(b,side,back,lod):
    # Open leaves turn into the courtyard. A pierced metal scroll fills each section.
    hinge=np.array([side,back]); hand=1 if side<0 else -1
    length=1.13;angle=math.radians(61)
    axis=np.array([hand*math.cos(angle),-math.sin(angle)])
    outward=np.array([axis[1],-axis[0]])
    def mapper(u,z,d):
        a=hinge+u*axis+outward*d
        return (a[0],a[1],z)
    zb,zt=.59,3.39
    frame=box(0,zb,length,zt).difference(box(.045,zb+.045,length-.045,zt-.045))
    def lineset(shape,thick,label):
        b.prism(shape,0,thick,mapper,IRON,label)
    lineset(frame,.042,'Entrance | opened metal leaf frame')
    strips=[]
    for u in (.2*length,.5*length,.80*length):
        strips.append(LineString([(u,zb+.04),(u,zt-.04)]).buffer(.009))
    for cell in range(3):
        bottom=zb+.06+cell*((zt-zb-.12)/3)
        high=(zt-zb-.12)/3
        for hand2 in (-1,1):
            t=np.linspace(0,1,13 if lod else 25)
            xs=length*.5+hand2*length*(.055+.36*np.sin(t*np.pi)**1.15)
            zs=bottom+t*high
            strips.append(LineString(list(zip(xs,zs))).buffer(.014,quad_segs=2))
            if not lod:
                for z in (bottom+.19*high,bottom+.78*high):
                    t=np.linspace(0,1.56*np.pi,22);rad=.10*(1-.67*t/(1.56*np.pi))
                    pts=list(zip(length*(.5+hand2*.24)+hand2*rad*np.cos(t),z+rad*np.sin(t)))
                    strips.append(LineString(pts).buffer(.010,quad_segs=2))
    lineset(unary_union(strips),.023,'Entrance | pierced scrolling metalwork')

def vestibule(b,cx,l,r,lod):
    # Only the first shallow visible portion of the recessed entrance is represented.
    back=.10;bottom=.55;top=4.025;inner_l=l+.11;inner_r=r-.11
    frame=box(l,bottom,r,top).difference(box(inner_l,bottom,inner_r,top-.14))
    face(b,frame,back,back+.16,OAK,'Entrance | stepped dark wood doorway')
    for inset in [.0,.037,.07]:
        shape=box(l+inset,bottom,r-inset,top-inset).difference(box(l+inset+.019,bottom,r-inset-.019,top-inset-.019))
        face(b,shape,back-.021-inset*.20,back+.003,OAK,'Entrance | moulded wood architrave')
    solid(b,inner_l,inner_r,back-.045,back+.17,3.36,3.46,OAK,'Entrance | broad head over opened gates')
    upper=box(inner_l,3.46,inner_r,top-.14)
    divisions=np.linspace(inner_l,inner_r,5)
    scroll=[]
    for j,(x0,x1) in enumerate(zip(divisions,divisions[1:])):
        if j:solid(b,x0-.027,x0+.027,back-.014,back+.11,3.46,top-.14,OAK,'Entrance | four-light wood transom')
        for hand in (-1,1):
            c=(x0+x1)/2;w=(x1-x0)/2
            t=np.linspace(0,1,16 if lod else 33)
            pts=list(zip(c+hand*w*(.93-1.29*t+.28*t*t),3.49+.36*t+.05*np.sin(2*np.pi*t)))
            scroll.append(LineString(pts).buffer(.013))
            if not lod:
                ang=np.linspace(0,np.pi*1.75,20);rad=.066-.045*ang/(np.pi*1.75)
                scroll.append(LineString(list(zip(c+hand*w*.56+rad*np.cos(ang),3.73+rad*np.sin(ang)))).buffer(.01))
    face(b,unary_union(scroll).intersection(upper),back+.012,back+.038,IRON,'Entrance | scrollwork in four transom lights')
    for x in [inner_l,inner_r]:cut_gate(b,x,back+.02,lod)
    deep=6.70
    for x in [l,r]:
        solid(b,x-.06,x+.06,back,deep,.54,top,SHADOW,'Entrance | visible shaded side reveal')
        solid(b,x-.065,x+.065,back,deep,.55,1.69,OAK,'Entrance | darker vestibule dado')
    solid(b,l,r,back,deep,top,top+.11,SOFFIT,'Entrance | light vestibule ceiling')
    solid(b,l,r,back,deep,.51,.55,PAVER,'Entrance | threshold floor')
    # The 2018 close photograph resolves a red mat and a rectangular dark stone inlay in front of it.
    solid(b,cx-.61,cx+.61,-.105,.47,.551,.558,RUNNER,'Entrance | broad vermilion threshold mat')
    solid(b,cx-.49,cx+.49,.46,1.70,.552,.557,RUNNER,'Entrance | visible runner into recess')
    left,right=cx-.58,cx+.58
    mark=box(left,-.78,right,-.19).difference(box(left+.025,-.755,right-.025,-.215))
    center=Point(cx,-.49).buffer(.092,quad_segs=10 if lod else 22)
    loops=[mark,center]
    for x in (left+.065,right-.065):
        for y in (-.69,-.28):
            disc=Point(x,y).buffer(.052,quad_segs=6 if lod else 14)
            loops.append(disc.difference(Point(x,y).buffer(.034,quad_segs=6 if lod else 14)))
    b.plan_prism(unary_union(loops),.5505,.553,INLAY,'Entrance | dark stone threshold motif')
    solid(b,l,r,deep,deep+.08,.55,top,SHADOW,'Entrance | limit of photographically visible recess')
    # The photographs give image positions, not distances. Use a common hanging height
    # and intersect both observed globe centres with that plane in the frontal camera.
    for lx,y,z,rad in [(-1.099,.863,3.24,.134),(-1.142,6.155,3.24,.149)]:
        b.tube([(lx,y,z),(lx,y,top)],.011,BRASS,6,'Entrance | chain of pendant globe')
        b.lathe((lx,y),[(z-rad,.012),(z-rad*.72,rad*.72),(z,rad),(z+rad*.7,rad*.72),(z+rad,.018)],
                GLOBE,12 if lod else 24,'Entrance | warm opal globe visible through doorway')

def add_entrance(b,lod=False):
    m=json.loads((HERE.parent/'measurements/entrance-cameras.json').read_bytes())
    j=m['jamb'];cx=j['center_x'];l=cx-j['half_width'];r=cx+j['half_width']
    depth=j['front_y'];z=j['landing_z'];top=j['lintel_z']
    hood(b,m['arch'],lod)
    for x0,x1 in [(l-.52,l),(r,r+.52)]:
        solid(b,x0,x1,depth+.015,.10,z,top+.14,JOINT,'Entrance | stone pier substrate')
        levels=[z,1.37,2.22,3.14,top+.14]
        for i,(lo,hi) in enumerate(zip(levels,levels[1:])):
            solid(b,x0-.009,x1+.009,depth,.09,lo+.006,hi-.006,ASH,'Entrance | square granite pier course '+str(i+1))
    solid(b,l,r,depth,.10,top,top+.18,ASH,'Entrance | recessed square lintel')
    for i in range(4):
        front=-2.42+.3*i
        solid(b,l-.33,r+.33,front,.16,-.012,.1375*(i+1),PAVER,'Entrance | granite tread '+str(i+1))
        solid(b,l-.34,r+.34,front-.038,front+.13,.1375*(i+1)-.034,.1375*(i+1),ASH,'Entrance | projecting rounded nosing')
    solid(b,l-.12,r+.12,-1.22,.12,.51,.55,PAVER,'Entrance | top landing')
    vestibule(b,cx,l,r,lod)
