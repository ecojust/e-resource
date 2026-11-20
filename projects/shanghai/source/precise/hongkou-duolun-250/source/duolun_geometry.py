"""Two-story curved street front, based on 2014 daytime and 2024 evening photographs."""
import math
import numpy as np
from shapely.geometry import Polygon, box, Point
from shapely.ops import unary_union
from photo_architecture import Facade

WALL='pale grey dressed stone'; BASE='ash grey plinth'; CARVE='warm carved stone'
TRIM='light stone moulding'; FRAME='brown wood sash'; GLASS='smoked window glass'
DOOR='dark entrance timber'; ROOF='grey flat roof'; METAL='black iron'; PANEL='ochre relief ground'
PALETTE={WALL:{'color':[.66,.65,.615],'roughness':.85},BASE:{'color':[.38,.38,.34],'roughness':.91},
    CARVE:{'color':[.71,.64,.52],'roughness':.87},TRIM:{'color':[.79,.76,.67],'roughness':.79},
    FRAME:{'color':[.19,.12,.074],'roughness':.58},GLASS:{'color':[.095,.142,.152],'roughness':.27,'metallic':.2},
    DOOR:{'color':[.19,.125,.095],'roughness':.72},ROOF:{'color':[.26,.26,.235],'roughness':.92},
    METAL:{'color':[.12,.116,.10],'roughness':.52,'metallic':.36},PANEL:{'color':[.55,.46,.36],'roughness':.85}}
# Rotate the source plan so the central portal looks toward native -Y. Map heading 137.18° restores the observed WGS84 alignment.
ROT=math.radians(135.0); R=12.34; CX=4.03; CY=-2.05; SIDE=R*math.pi/4
WEST=CX-R; NORTH=CY+R; EAST=8.22; SOUTH=-10.17
START=-SIDE-(EAST-CX); END=SIDE+(CY-SOUTH); TOP=8.27

def locus(s):
    if s< -SIDE:return (CX-s-SIDE,NORTH),(-1.,0.),(0.,1.)
    if s> SIDE:return (WEST,CY-(s-SIDE)),(0.,-1.),(-1.,0.)
    a=math.radians(135)+s/R;ca,sa=math.cos(a),math.sin(a)
    return (CX+R*ca,CY+R*sa),(-sa,ca),(ca,sa)

def point(s,z,d=0):
    p,t,n=locus(s)
    return (p[0]+d*n[0],p[1]+d*n[1],z)

class Front:
    def __init__(self,b,lod):self.b=b;self.lod=lod
    def prism(self,poly,inner,outer,material,label):
        if poly.is_empty or poly.area<1e-7:return
        lo,bottom,hi,top=poly.bounds
        n=max(1,math.ceil((hi-lo)/(.87 if self.lod else .48)))
        for a,c in zip(np.linspace(lo,hi,n+1)[:-1],np.linspace(lo,hi,n+1)[1:]):
            section=poly.intersection(box(a,bottom-.01,c,top+.01))
            if section.area>1e-7:self.b.prism(section,inner,outer,point,material,label)
    def rect(self,l,r,b,t,d0,d1,material,label):
        self.prism(box(l,b,r,t),d0,d1,material,label)
    def rod(self,coords,radius,material,label):
        self.b.tube([point(*p) for p in coords],radius,material,5 if self.lod else 8,label)

def horseshoe(s,z,w,h,lod,upper=False):
    n=9 if lod else 20
    if upper:
        pts=[(-.44,0),(.44,0),(.44,.55),(.40,.60),(.26,.65),(.23,.69)]
        for a in np.linspace(-math.pi/4,math.pi*1.25,n+1):
            pts.append((.33*math.cos(a),.825+.175*math.sin(a)))
        pts.extend([(-.23,.69),(-.26,.65),(-.40,.60),(-.44,.55)])
    else:
        # Horseshoe profile narrows below the haunches while the upper arch springs wider.
        pts=[(-.433,0),(.433,0)]
        for a in np.linspace(-math.pi/6,math.pi*7/6,n+1):
            pts.append((.50*math.cos(a),.77+.23*math.sin(a)))
    return Polygon([(s+w*x,z+h*y) for x,y in pts])

def pane(f,poly,s,z,w,h,door=False):
    f.prism(poly.buffer(.009),-.34,-.31,DOOR if door else GLASS,'Windows/recessed glazing and door leaves')
    border=poly.difference(poly.buffer(-.059,join_style='mitre'))
    lines=[box(s-.026,z,s+.026,z+h)]
    for ratio in ([.26,.67] if not f.lod else [.50]):
        lines.append(box(s-w/2,z+h*ratio-.023,s+w/2,z+h*ratio+.023))
    frame=border.union(poly.intersection(unary_union(lines)))
    f.prism(frame,-.29,-.23,FRAME,'Windows/sash and transom')
    surround=poly.buffer(.10,join_style='round').difference(poly)
    f.prism(surround,.005,.085,CARVE,'Street front/horseshoe archivolts')
    if door:
        for off in [-.31,.31]:
            for height in [z+.52,z+1.48]:
                f.rect(s+off-.22,s+off+.22,height-.30,height+.30,-.30,-.27,DOOR,'Door raised panels')
    else:f.rect(s-w*.53,s+w*.53,z-.085,z+.012,-.04,.11,TRIM,'Windows/stone sill')

def column(f,s,z0,z1,r,d):
    x,y,_=point(s,z0,d)
    profile=[(z0,r*1.32),(z0+.10,r*1.32),(z0+.17,r*.91),(z0+.27,r*1.09),(z0+.36,r),
             (z1-.38,r*.77),(z1-.30,r*.95),(z1-.24,r*1.21),(z1-.11,r*1.36)]
    f.b.lathe((x,y),profile,CARVE,9 if f.lod else 18,'Arcades/stone shafts and ring bases')
    f.rect(s-r*1.48,s+r*1.48,z1-.12,z1,.01+d-r*1.21,d+r*1.21,TRIM,'Arcades/square capitals')

def lattice(f,center,z,w,h,count_x,count_y,d=.061):
    # The model simplifies the photograph's fine pierced arabesques into separate layered rosettes.
    f.rect(center-w/2,center+w/2,z,z+h,.008,.038,PANEL,'Ornament/recessed panel ground')
    nx=max(1,count_x//2) if f.lod else count_x
    dx=w/nx;dy=h/count_y;motifs=[]
    for j in range(count_y):
        for i in range(nx):
            sx=center-w/2+(i+.5)*dx;zy=z+(j+.5)*dy
            petals=8 if not f.lod else 4
            ring=[]
            for k in range(2*petals):
                a=k*math.pi/petals
                rad=.46 if k%2==0 else .25
                ring.append((sx+dx*rad*math.cos(a),zy+dy*rad*math.sin(a)))
            motif=Polygon(ring)
            motifs.append(motif.difference(motif.buffer(-.030,join_style='mitre')))
    f.prism(unary_union(motifs),.039,d,CARVE,'Ornament/star lattice panels')

def balustrade(f,s,z,w,d):
    f.rect(s-w/2,s+w/2,z-.13,z+.03,d-.30,d+.18,TRIM,'Balconies/lower rail')
    f.rect(s-w/2,s+w/2,z+.58,z+.70,d-.24,d+.16,TRIM,'Balconies/top rail')
    n=max(4,round(w/(.31 if f.lod else .21)))
    for j in range(n):
        u=s-w/2+(j+.5)*w/n;x,y,_=point(u,z,d)
        r=.052
        f.b.lathe((x,y),[(z,r*1.35),(z+.08,r),(z+.20,r*.62),(z+.35,r*1.2),(z+.51,r*.63),(z+.60,r*1.3)],CARVE,6 if f.lod else 9,'Balconies/turned balusters')

def add_building(b,lod):
    f=Front(b,lod);holes=[]
    def aperture(s,z,w,h,upper=False,door=False):
        poly=horseshoe(s,z,w,h,lod,upper)
        holes.append(poly);pane(f,poly,s,z,w,h,door)
    for s in [-1.30,0,1.30]:
        aperture(s,.10 if s==0 else .89,1.46 if s==0 else .80,3.02 if s==0 else 2.20,door=s==0)
        aperture(s,5.04,1.17 if s==0 else .89,2.24 if s==0 else 2.02,upper=True)
    for side in [-1,1]:
        off=side*5.04
        aperture(off,.95,1.11,2.10)
        for h in [-.55,.55]:aperture(off+h,5.07,.80,1.94,upper=True)
        # Outer groups run along the straight portions, with five smaller openings above three broad lower arches.
        pos=side*10.35
        for j in range(-2,3):aperture(pos+j*.91,5.03,.76,1.98,upper=True)
        for j in [-1,0,1]:aperture(pos+j*1.40,.90,1.30,2.21)
        lattice(f,off,3.12,2.26,.70,5,2)
        lattice(f,off,4.18,2.30,.64,5,2)
        lattice(f,pos,3.33,4.72,.55,9,2)
        lattice(f,pos,4.18,4.78,.65,9,2)
        for j in [-.85,.85]:column(f,off+j,.12,2.95,.12,.045)
        for j in [-2.25,-.73,.73,2.25]:column(f,pos+j,.14,3.04,.106,.05)
    for u in [-1.96,-.76,.76,1.96]:
        column(f,u,.11,3.36,.142,.21)
        column(f,u,4.92,6.71,.105,.16)
    for s in [-2.19,2.19]:
        column(f,s,.08,3.40,.15,.07)
        f.rect(s-.155,s+.155,4.00,7.87,.012,.12,TRIM,'Central portal/upper pilasters')
    for s in [-1.29,0,1.29]:
        lattice(f,s,3.19,1.18,.67,4,2,.12)
        lattice(f,s,7.29,1.14,.47,4,2,.087)
    facade=box(START,0,END,TOP).difference(unary_union(holes))
    f.prism(facade,-.37,0,WALL,'Exterior/curving cut stone street wall')
    if not lod:
        coursing=[]
        for z in np.arange(.34,8.13,.38):
            coursing.append(box(START,z,END,z+.015))
        for j,z in enumerate(np.arange(.34,8.00,.76)):
            for u in np.arange(START+(j%2)*.5,END,1.10):
                coursing.append(box(u,z,u+.012,z+.35))
        f.prism(facade.intersection(unary_union(coursing)),.001,.011,TRIM,'Exterior/horizontal and staggered joints')
    for z,h,d,m in [(0,.13,.09,BASE),(3.81,.13,.14,TRIM),(4.00,.12,.17,TRIM),(7.70,.12,.11,CARVE),(8.13,.12,.20,TRIM),(8.28,.13,.29,TRIM)]:
        f.prism(box(START,z,END,z+h).difference(unary_union(holes)),-.08,d,m,'Exterior/curved stringcourses and eave')
    lattice(f,0,7.83,END-START-8,.28,42,1)
    # Projecting central balcony, carved brackets, and a smaller balustrade within each single ground bay.
    f.rect(-1.02,1.02,4.00,4.17,-.02,.76,CARVE,'Central portal/projecting balcony slab')
    balustrade(f,0,4.15,1.86,.62)
    for u in [-.78,.78]:
        f.prism(Polygon([(u-.12,3.66),(u+.12,3.66),(u+.12,4.03),(u-.12,4.03)]),.06,.50,CARVE,'Central portal/stone brackets')
    for s in [-1.3,1.3,-5.04,5.04]:balustrade(f,s,.25,.85,.07)
    outline=[locus(s)[0] for s in np.unique([START,*np.linspace(-SIDE,SIDE,13 if lod else 31),END])]
    outline += [(EAST,SOUTH)]
    plan=Polygon(outline)
    b.plan_prism(plan,-.04,.085,BASE,'Ground/curved footprint')
    b.plan_prism(plan,8.14,8.26,ROOF,'Roof/main flat deck')
    for a,c in [(outline[-2],outline[-1]),(outline[-1],outline[0])]:
        rear=Facade(b,a,c,'Rear and east return');cuts=[]
        for j in range(1,5):
            u=rear.length*(j/5-.5)
            for z in [1.08,5.08]:
                cut=box(u-.48,z,u+.48,z+1.50);cuts.append(cut)
                rear.prism(cut,-.25,-.19,GLASS,'estimated window')
                rear.box(u,z+.72,.058,1.45,.08,-.13,FRAME,'vertical sash')
        rear.wall(0,8.20,cuts,.32,WALL)
        rear.box(0,8.26,rear.length,.19,.32,0,TRIM,'roof cap')
    # Rooftop screen above the center door; its three panels are visible in both dated frontal photographs.
    f.rect(-2.19,2.19,8.18,9.54,-.42,-.057,WALL,'Roof/central raised parapet')
    f.rect(-2.27,2.27,9.48,9.64,-.49,.04,TRIM,'Roof/parapet cap')
    for u in [-2.10,-.72,.72,2.10]:f.rect(u-.065,u+.065,8.36,9.49,-.08,-.015,TRIM,'Roof/parapet panel border')
    for s in [START+.12,END-.12,-7.02,7.02]:
        f.rect(s-.14,s+.14,.09,8.22,.005,.09,CARVE,'Exterior/facade piers')
    co,si=math.cos(ROT),math.sin(ROT)
    for part in b.parts:part['vertices']=[(x*co-y*si,x*si+y*co,z) for x,y,z in part['vertices']]
