"""Stepped street tower on the southwest side of the Fuzhou Road plaza."""
import numpy as np
from shapely.geometry import box, Polygon, LineString
from shapely.ops import unary_union
from photo_architecture import Facade

RENDER='warm washed aggregate'
RIB='ochre cement rib'
STONE='buff granite blocks'
JOINT='recessed stone joint'
DARK='black granite portal'
SPANDREL='dark bronze spandrel'
SASH='black steel sash'
GLASS='cool steel window glass'
DOOR='bronze entrance glazing'
CUT='plain cut surface'
PALETTE={name:{'color':rgb,'roughness':rough,'metallic':metal}for name,rgb,rough,metal in [
    (RENDER,[.50,.409,.321],.86,0),(RIB,[.61,.51,.397],.83,0),(STONE,[.573,.51,.42],.79,0),
    (JOINT,[.36,.325,.278],.86,0),(DARK,[.13,.128,.123],.43,.08),(SPANDREL,[.249,.210,.17],.61,.24),
    (SASH,[.105,.122,.127],.56,.28),(GLASS,[.195,.270,.306],.34,.20),(DOOR,[.34,.286,.207],.31,.32),
    (CUT,[.393,.35,.293],.92,0)]}
# The present source follows the recessed arc with eleven segments. The photographs
# show planar window walls and a pronounced change of plane at each end.
EDGE=np.array([[-17.67,-.39],[-12.06,-5.70],[-5.16,-.66],[-3.23,-.14],[1.83,-.15],
               [3.87,-1.12],[9.83,-5.70],[16.18,1.02]])
COUNTS=(3,2,1,3,1,2,3)
ROWS=(8,8,14,16,14,8,8)
HEIGHT=(39.12,39.12,60.19,66.89,60.19,39.12,39.12)
BASE=9.72
DEPTHS=(4.35,4.85,3.55,2.78,2.78,3.55,4.85,4.35)
FIRST=10.84
STOREY=3.49
WINDOW=2.20


def rect(u,z,w,h):
    return box(u-w/2,z,u+w/2,z+h)


def window(f,u,z,w,h,base=False,lod=False):
    shape=rect(u,z,w,h)
    f.prism(shape.buffer(.01,join_style=2),-.306,-.283,GLASS,'recessed glass')
    frame=shape.difference(shape.buffer(-.063,join_style=2))
    bars=[frame,rect(u,z+h*.72,w,.065)]
    if base:
        bars.extend(rect(u,z+h*i/4,w,.075)for i in [1,2])
    if not lod or base:
        bars.append(rect(u,z,.063,h*.72))
    f.prism(unary_union(bars).intersection(shape),-.247,-.172,SASH,'window frame and transom')
    f.prism(rect(u,z-.045,w+.095,.08),-.025,.085,SPANDREL,'thin window sill')
    return shape


def central_portal(f,half):
    width=3.59;high=9.24;u=0
    opening=rect(u,0,width,high)
    surround=box(-half-.39,.02,half+.39,9.91).difference(opening)
    f.prism(surround,-.055,.275,DARK,'outer black granite entrance')
    for x in [-1,1]:
        at=x*(width/2+.14)
        f.prism(rect(at,.1,.20,9.25),.276,.355,DARK,'stepped black granite jamb')
        f.prism(rect(x*(width/2-.073),.01,.145,high),-1.12,-.035,DARK,'polished portal reveal')
    f.prism(rect(0,high-.13,width,.13),-1.12,.011,DARK,'deep entrance soffit')
    f.prism(rect(0,3.20,width-.21,5.59),-.92,-.865,DOOR,'tall transom in the recessed doorway')
    f.prism(rect(0,.16,width-.21,3.04),-1.08,-1.02,GLASS,'recessed outer doors')
    for x in [-1.05,0,1.05]:
        f.prism(rect(x,.15,.068,3.08),-1.01,-.952,SASH,'door stiles')
    f.prism(rect(0,3.07,width-.14,.15),-.92,-.827,DARK,'entrance crossbar')
    for x in [-.84,.84]:
        f.prism(rect(x,3.21,.042,5.58),-.861,-.821,SASH,'tall entrance transom division')
    f.prism(rect(0,0,width-.20,.13),-1.09,-.12,STONE,'single entrance threshold')
    return opening


def granite(f,holes):
    half=f.length/2;face=f.wall(0,BASE,holes,.40,STONE)
    joints=[]
    for i,z in enumerate([.67,1.74,2.87,4.00,5.12,6.25,7.38,8.51,9.36]):
        joints.append(box(-half,z,half,z+.035))
        n=max(1,int(f.length/1.32));step=f.length/n
        for k in range(n):
            x=-half+(k+.50*(i%2))*step
            joints.append(box(x-.015,z+.025,x+.015,min(BASE,z+1.11)))
    f.prism(unary_union(joints).intersection(face),.002,.008,JOINT,'masonry joint courses')
    for z,h,depth in [(8.83,.105,.08),(9.13,.132,.12),(9.47,.18,.16)]:
        f.prism(box(-half,z,half,z+h).intersection(face),.010,depth,STONE,'three granite head courses')


def bay_wall(b,i,lod):
    f=Facade(b,EDGE[i],EDGE[i+1],'plaza central tower' if i==3 else 'plaza wing '+str(i+1))
    half=f.length/2;count=COUNTS[i];n=ROWS[i];top=HEIGHT[i]
    # Broad aggregate piers frame the three central ribbons or the side windows.
    if count==1:
        centers=[0.];w=min(1.08,f.length*.54)
    elif i==3:
        centers=[-1.54,0.,1.54];w=1.17
    else:
        centers=np.linspace(-half+f.length/(count*2),half-f.length/(count*2),count);w=1.11 if i in (1,5) else 1.04
    holes=[];basement=[]
    for u in centers:
        if i!=3:
            basement.append(window(f,u,.93,w+.21,7.26,True,lod))
        for j in range(n):
            z=FIRST+STOREY*j;holes.append(window(f,u,z,w,WINDOW,lod=lod))
            if j:
                panel=rect(u,z-1.10,w,1.035)
                f.prism(panel,-.036,.023,SPANDREL,'metal panel beneath window')
                if not lod:
                    f.prism(rect(u,z-.97,w-.10,.038),.027,.061,SPANDREL,'pressed metal top bead')
                    f.prism(rect(u,z-.22,w-.10,.037),.027,.061,SPANDREL,'pressed metal bottom bead')
    if i==3:
        basement.append(central_portal(f,half))
    granite(f,basement)
    f.wall(BASE,top,holes,.40,RENDER)
    positions=[-half+.20,half-.20]
    if i==3:
        positions.extend([-.77,.77])
    for u in positions:
        w=.32 if i==3 else .29
        f.prism(rect(u,BASE,w,top-BASE-.28),.007,.16,RIB,'continuous exposed aggregate pier')
        if not lod:
            f.prism(rect(u+.11,BASE+.05,.040,top-BASE-.40),.161,.20,RIB,'striated edge of pier')
    f.prism(box(-half+.02,top-.20,half-.02,top),-.08,.11,RIB,'stone parapet lip')
    if i==3:
        for x in [-half+.14,-1.47,-.49,.49,1.47,half-.14]:
            f.prism(rect(x,top-.20,.18,1.28),-.93,.14,RIB,'six short raised crown piers')
        f.prism(box(-half+.20,top-.025,half-.20,top+.30),-.97,-.08,RENDER,'recessed crest beneath the fins')
    elif i in (0,1,5,6):
        # Flat-topped interruptions in the shoulder parapets are visible in the 2013 oblique.
        for u in centers:
            f.prism(rect(u,top-.01,.82,.30),-.49,-.065,RENDER,'short stepped shoulder parapet')
    return f


def section_back(b):
    ds=np.diff(EDGE,axis=0);ds/=np.linalg.norm(ds,axis=1)[:,None]
    normals=np.column_stack([-ds[:,1],ds[:,0]])
    rear=[EDGE[0]+DEPTHS[0]*normals[0]]
    for i in range(1,len(EDGE)-1):
        m=normals[i-1]+normals[i]
        rear.append(EDGE[i]+DEPTHS[i]*m/np.dot(m,normals[i]))
    rear.append(EDGE[-1]+DEPTHS[-1]*normals[-1])
    for i,top in enumerate(HEIGHT):
        a,c=EDGE[i:i+2];d,e=rear[i:i+2]
        poly=Polygon([a,c,e,d]);assert poly.is_valid
        b.plan_prism(poly,0,.045,CUT,'ground within street section')
        b.plan_prism(poly,top-.07,top,CUT,'top of street section')
        b.add([(*e,0),(*e,top),(*d,top),(*d,0)],[(0,1,2,3)],CUT,'rear cut of the street section')
    for i,(a,d) in enumerate(zip(EDGE,rear)):
        before=HEIGHT[i-1] if i else 0;after=HEIGHT[i] if i<len(HEIGHT) else 0
        if before==after:continue
        low,high=sorted([before,after])
        b.add([(*a,low),(*a,high),(*d,high),(*d,low)],[(0,1,2,3)],CUT if low==0 else RENDER,'end or step between the tower tiers')


def add_plaza(b,lod):
    for i in range(len(COUNTS)):
        bay_wall(b,i,lod)
    section_back(b)
