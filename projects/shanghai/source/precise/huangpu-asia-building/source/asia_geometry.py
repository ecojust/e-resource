"""Street elevations reconstructed from the 2011 corner and 2021/2025 frontal photographs."""
import math
import numpy as np
from shapely.geometry import Polygon, box
from shapely.ops import unary_union
from photo_architecture import Facade, opening

GRANITE='sand granite'; ASHLAR='pale banded masonry'; CARVED='carved warm limestone'
LIGHT='pale cornice stone'; GLASS='smoky blue glazing'; SASH='dark bronze sash'
METAL='black balcony iron'; ROOF='weathered roof'; DOOR='dark timber'; SKY='green roof glass'
PALETTE = {
    GRANITE:{'color':[.57,.45,.34],'roughness':.91}, ASHLAR:{'color':[.71,.69,.60],'roughness':.86},
    CARVED:{'color':[.72,.65,.52],'roughness':.78}, LIGHT:{'color':[.81,.76,.65],'roughness':.78},
    GLASS:{'color':[.105,.16,.17],'roughness':.24,'metallic':.22}, SASH:{'color':[.086,.090,.077],'roughness':.47,'metallic':.4},
    METAL:{'color':[.085,.089,.08],'roughness':.53,'metallic':.45}, ROOF:{'color':[.25,.25,.225],'roughness':.9},
    DOOR:{'color':[.17,.092,.060],'roughness':.63}, SKY:{'color':[.16,.285,.285],'roughness':.27,'metallic':.2}}
ANGLE=math.atan2(11.732,37.743)
SW=(-19.25,-19.72); SE_S=(15.67,-19.72); SE_E=(19.34,-16.05)
NE=(19.34,19.37); NW=(-19.25,19.37)
# The photographed concave junction has its own single window axis set back from the corner.
C1=(16.42,-18.53); C2=(18.15,-16.80)
RING=[SW,SE_S,C1,C2,SE_E,NE,NW]
PLAN=Polygon(RING)
UP=31.27
FLOORS=[(.55,3.23),(5.05,3.52),(10.38,2.84),(14.46,2.82),(18.57,2.86),(23.47,2.83),(27.62,2.53)]


def pane(f,shape,lod,label,arch=False,material=GLASS):
    left,bottom,right,top=shape.bounds
    f.prism(shape.buffer(.014,join_style='mitre'),-.39,-.35,material,label+' inset')
    inner=shape.buffer(-.082,join_style='mitre')
    lines=[box((left+right)/2-.036,bottom,(left+right)/2+.036,top)]
    rows=[.46] if lod else ([.32,.64] if not arch else [.35,.67])
    for ratio in rows:
        level=bottom+(top-bottom)*ratio
        lines.append(box(left,level-.034,right,level+.034))
    frame=shape.buffer(-.016,join_style='mitre').difference(inner.difference(unary_union(lines)))
    f.prism(frame,-.31,-.22,SASH,label+' mullions')
    f.box((left+right)/2,bottom-.065,right-left+.18,.13,.22,.035,CARVED,label+' sill')


def belt(f,z,h,projection,material=LIGHT):
    f.box(0,z,f.length+.035,h,.22+projection,(projection-.22)/2,material,'continuous cornice')


def column(f,u,lo,hi,d,r,lod,label):
    pos=f.point(u,lo,d)
    profile=[(lo,r*1.26),(lo+.12,r*1.26),(lo+.20,r*.98),(lo+.34,r*1.10),
             (lo+.47,r),(hi-.54,r*.82),(hi-.44,r*.99),(hi-.34,r*1.08),(hi-.18,r*1.20)]
    f.builder.lathe(pos[:2],profile,CARVED,10 if lod else 20,f.label+'/'+label+' shaft and torus')
    f.box(u,hi-.095,r*3.08,.19,r*2.66,d,LIGHT,label+' abacus')
    for sign in [-1,1]:
        cu=u+sign*r*.88
        f.prism(opening(cu,hi-.51,r*.70,r*.36,r*.16,6 if lod else 14),d+r*.67,d+r*1.02,CARVED,label+' Ionic volute')
        if not lod:
            p=f.point(cu,hi-.35,d+r*1.03)
            pts=[p+f.t*(r*.23*math.cos(a))+np.array([0,0,r*.23*math.sin(a)]) for a in np.linspace(0,math.tau,15)]
            f.builder.tube(pts,.028,CARVED,5,f.label+'/'+label+' volute bead')


def balcony(f,center,width,z,lod,curve=False):
    count=7 if curve else 1
    points=[]
    for j in range(count+1):
        u=center-width/2+width*j/count
        d=(-.29+.36*math.sin(math.pi*j/count)) if curve else .05
        points.append((u,d))
    xy=lambda u,d: tuple(f.point(u,0,d)[:2])
    floor=Polygon([xy(center-width/2,-2.38),xy(center+width/2,-2.38),*reversed([xy(u,d) for u,d in points])])
    f.builder.plan_prism(floor,z-.20,z,CARVED,f.label+'/loggia floor')
    if curve:
        for height in [.08,.82]:
            f.builder.tube([f.point(u,z+height,d) for u,d in points],.055,METAL,5 if lod else 8,f.label+'/bowed balcony rail')
        n=7 if lod else 15
        for j in range(n+1):
            u=center-width/2+width*j/n;d=-.29+.36*math.sin(math.pi*j/n)
            f.box(u,z+.45,.045,.74,.046,d,METAL,'bowed balcony upright')
    else:
        f.box(center,z+.81,width,.14,.25,.045,LIGHT,'balustrade coping')
        n=5 if lod else 10
        for j in range(n):
            u=center-width/2+(j+.5)*width/n
            w=.12
            bal=Polygon([(u-w,z),(u+w,z),(u+w*.57,z+.15),(u+w*.87,z+.38),(u+w*.55,z+.62),(u+w*.80,z+.75),
                         (u-w*.80,z+.75),(u-w*.55,z+.62),(u-w*.87,z+.38),(u-w*.57,z+.15)])
            f.prism(bal,-.06,.13,CARVED,'shaped stone baluster')


def fan(f,center,z,width,rise,thick,d,label,lod):
    n=12 if lod else 26
    outer=[(center+(width/2)*math.cos(a),z+rise*math.sin(a)) for a in np.linspace(0,math.pi,n+1)]
    inner=[(center+(width/2-thick)*math.cos(a),z+(rise-thick)*math.sin(a)) for a in np.linspace(math.pi,0,n+1)]
    f.prism(Polygon([*outer,*inner]),d-.13,d+.19,LIGHT,label)
    if not lod:
        for a in np.linspace(.18,math.pi-.18,13):
            x=center+(width/2-thick*.47)*math.cos(a);y=z+(rise-thick*.47)*math.sin(a)
            f.box(x,y,.080,.12,.12,d+.21,CARVED,label+' voussoir')


def portal(f,lod):
    for sign in [-1,1]:
        for u in [2.23,2.92]:
            column(f,sign*u,.16,8.61,.54,.32,lod,'paired portal column')
        f.box(sign*2.58,8.83,1.95,.41,1.36,.33,CARVED,'broken portal entablature')
        f.box(sign*2.58,9.11,2.08,.17,1.52,.35,LIGHT,'portal cornice')
    fan(f,0,9.12,7.24,2.10,.36,.37,'segmental door pediment',lod)
    f.prism(Polygon([(-1.38,7.61),(0,8.39),(1.38,7.61),(1.27,7.43),(0,8.13),(-1.27,7.43)]),.02,.35,CARVED,'central aedicule')
    for u in [-1.22,1.22]:
        f.box(u,3.8,.21,7.35,.34,.06,CARVED,'portal jamb')
    f.box(0,4.39,2.93,.36,.47,.09,CARVED,'portal lintel')
    f.box(0,4.78,1.36,.60,.30,.11,LIGHT,'carved door cartouche')


def frontage(b,start,end,name,lod):
    f=Facade(b,start,end,name);L=f.length;span=7.05
    mid=[-4.71,0,4.71];wings=[]
    for sign in [-1,1]:
        wings.extend([sign*(span+(L/2-span)*t) for t in (.29,.72)])
    levels=[(0,9.78,GRANITE),(9.78,22.61,ASHLAR),(22.61,UP,LIGHT)]
    holes=[[],[],[]]
    for u in wings:
        for i,(z,h) in enumerate(FLOORS):
            w=2.23 if i<2 else 1.83
            win=opening(u,z,w,h,.89 if i==1 else 0,10 if lod else 20)
            holes[0 if i<2 else 1 if i<5 else 2].append(win)
            pane(f,win,lod,'flanking window',i==1)
            if i==5:
                f.prism(Polygon([(u-1.25,z+h+.15),(u,z+h+.84),(u+1.25,z+h+.15),(u+1.13,z+h+.03),(u,z+h+.62),(u-1.13,z+h+.03)]),
                        .01,.20,CARVED,'triangular upper window pediment')
    for u in mid:
        for i in [0,1]:
            z,h=FLOORS[i];isdoor=u==0 and i==0
            w=2.34 if isdoor else 2.05;z=.05 if isdoor else z;h=4.26 if isdoor else h
            win=opening(u,z,w,h,.83 if i==1 and u!=0 else 0,10 if lod else 18)
            holes[0].append(win);pane(f,win,lod,'door' if isdoor else 'podium window',i==1,DOOR if isdoor else GLASS)
        for i in range(3):
            base=9.81+4.15*i;hole=opening(u,base,3.70,3.92,1.58 if i==2 else 0,10 if lod else 24)
            holes[1].append(hole);balcony(f,u,3.70,base+.16,lod)
        balcony(f,u,4.56,26.98,lod,curve=True)
    holes[2].append(box(-span,22.70,span,30.95))
    solids=[]
    for (bottom,top,mat),cut in zip(levels,holes):
        solids.append(f.wall(bottom,top,cut,thickness=.43,material=mat))
    # Actual walls at the backs of the three middle loggias and tall upper colonnade.
    rear=Facade(b,f.point(-span,0,-2.38)[:2],f.point(span,0,-2.38)[:2],name+'/inner loggia')
    inside=[]
    for u in mid:
        for z in [10.15,14.30,18.45,23.07,27.22]:
            opening_shape=opening(u,z,2.61,2.79);inside.append(opening_shape);pane(rear,opening_shape,lod,'deep bay sashes')
    rear.wall(9.75,31.05,inside,.31,ASHLAR)
    balcony(f,0,span*2,22.66,lod)
    for u in [-span+.06,-2.37-.39,-2.37+.39,2.37-.39,2.37+.39,span-.06]:
        column(f,u,22.73,30.93,-.27,.31,lod,'upper Ionic colonnade')
    if not lod:
        for z in np.arange(.39,22.5,.68):
            surface=solids[0 if z<9.78 else 1];line=surface.intersection(box(-L/2,z,L/2,z+.035))
            if line.area>.008:f.prism(line,.002,.020,CARVED,'incised ashlar horizontal')
        for z in np.arange(.27,9.45,.68):
            for u in np.arange(-L/2+(int(z/.68)%2)*.92,L/2,1.84):
                line=solids[0].intersection(box(u,z,u+.034,z+.61))
                if line.area>.004:f.prism(line,.002,.021,CARVED,'podium stone joint')
    for u in [-L/2+.24,-span-.26,span+.26,L/2-.24]:
        f.box(u,26.85,.38,7.88,.29,.06,CARVED,'upper end pilaster')
    for z,h,d in [(.17,.30,.09),(9.72,.20,.21),(22.55,.28,.34),(30.96,.28,.34),(31.25,.23,.60)]:
        belt(f,z,h,d)
    for u in np.linspace(-L/2+.22,L/2-.22,max(4,round(L/(1.05 if lod else .56)))):
        f.box(u,31.09,.19,.28,.35,.27,CARVED,'cornice modillion')
    portal(f,lod)


def simple_wall(b,a,c,name,lod,corner=False):
    f=Facade(b,a,c,name);n=1 if corner else 8;holes=[]
    for j in range(n):
        u=(j+.5)*f.length/n-f.length/2
        for i,(z,h) in enumerate(FLOORS):
            if not corner and lod and i in (1,3):continue
            w=min(f.length*.74,1.42) if corner else 1.55
            cut=opening(u,z,w,h*.86);holes.append(cut);pane(f,cut,lod,'return sash')
    for lo,hi,mat in [(0,9.78,GRANITE),(9.78,22.61,ASHLAR),(22.61,UP,LIGHT)]:
        f.wall(lo,hi,[h for h in holes if h.bounds[1]>=lo and h.bounds[3]<=hi],.39,mat)
    for z in [9.72,22.55,31.25]:belt(f,z,.16,.22)
    return f


def pavilion(b,poly,front_edges,lod):
    for index,(a,c) in enumerate(zip(poly,poly[1:]+poly[:1])):
        f=Facade(b,a,c,'attic pavilion')
        holes=[]
        if index in front_edges:
            w=min(f.length*.61,5.2);cut=opening(0,31.67,w,1.63,1.19,12 if lod else 26)
            holes=[cut];pane(f,cut,lod,'semicircular attic light',True);fan(f,0,32.11,w+.50,1.45,.20,.065,'attic voussoirs',lod)
        f.wall(31.17,34.08,holes,.33,ASHLAR)
        belt(f,34.13,.19,.19)
        if f.length>3.1 and index in front_edges:
            crown=Polygon([(-f.length/2,34.05),(f.length/2,34.05),(f.length/2,34.24),(f.length*.35,34.34),(f.length*.30,34.85),(-f.length*.30,34.85),(-f.length*.35,34.34),(-f.length/2,34.24)])
            f.prism(crown,-.25,.07,CARVED,'stepped pavilion parapet')
    b.plan_prism(Polygon(poly),33.98,34.13,ROOF,'pavilion/flat roof')


def add_building(b,lod):
    frontage(b,SW,SE_S,'Yanan Road south',lod)
    frontage(b,SE_E,NE,'Bund east',lod)
    simple_wall(b,NE,NW,'north service return',lod)
    simple_wall(b,NW,SW,'west service return',lod)
    simple_wall(b,C1,C2,'southeast splay',lod,True)
    for a,c in [(SE_S,C1),(C2,SE_E)]:
        f=Facade(b,a,c,'southeast return')
        for lo,hi,mat in [(0,9.78,GRANITE),(9.78,22.61,ASHLAR),(22.61,UP,LIGHT)]:f.wall(lo,hi,(),.35,mat)
        for z in [9.72,22.55,31.25]:belt(f,z,.16,.24)
    well=box(-6.8,-9.7,6.8,9.7)
    b.plan_prism(PLAN,0,.13,GRANITE,'ground footprint')
    b.plan_prism(PLAN.difference(well),31.10,31.30,ROOF,'perimeter roof around covered lightwell')
    b.plan_prism(well,30.76,30.88,SKY,'approximate central glazed lightwell')
    for a,c in zip(list(well.exterior.coords)[:-1],list(well.exterior.coords)[1:]):
        f=Facade(b,a,c,'lightwell roof kerb');f.wall(30.75,31.35,(),.12,CARVED)
    for x in np.linspace(-6.7,6.7,6 if lod else 11):
        b.box((x,0,30.94),(.075,19.28,.13),SASH,label='lightwell longitudinal roof bar')
    for y in np.linspace(-9.6,9.6,6 if lod else 12):
        b.box((0,y,30.96),(13.5,.07,.12),SASH,label='lightwell glazing transom')
    for poly,edges in [([(-19.12,-19.57),(-8.53,-19.57),(-8.53,-11.13),(-19.12,-11.13)],{0,3}),
                       ([(8.35,-19.57),SE_S,C1,C2,SE_E,(19.20,-9.95),(8.35,-9.95)],{0,4}),
                       ([(8.92,9.63),(19.20,9.63),(19.20,19.21),(8.92,19.21)],{1,2}),
                       ([(-19.12,10.78),(-9.37,10.78),(-9.37,19.21),(-19.12,19.21)],{2,3})]:
        pavilion(b,poly,edges,lod)
    for a,c in [(SW,SE_S),(SE_E,NE)]:
        f=Facade(b,a,c,'open central roof rail')
        for z in [31.55,32.03]:f.box(0,z,13.8,.065,.075,-.43,METAL,'top rail')
        for u in np.linspace(-6.85,6.85,12 if lod else 27):f.box(u,31.72,.045,.72,.048,-.43,METAL,'rail picket')
    # Keep all public assets in the true map frame. The coordinate rotation is constant across LODs.
    co,si=math.cos(ANGLE),math.sin(ANGLE)
    for item in b.parts:item['vertices']=[(x*co-y*si,x*si+y*co,z) for x,y,z in item['vertices']]
