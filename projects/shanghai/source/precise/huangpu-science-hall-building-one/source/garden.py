"""South garden wall, galleries and clock terrace of the former French municipal college."""
import math
import numpy as np
from shapely.geometry import box, Point, LineString, Polygon
from shapely.ops import unary_union
from photo_architecture import Facade, opening

PEBBLE='grey pebble dash'
CREAM='ivory render'
WOOD='dark brown timber'
GLASS='warm garden glazing'
BRICK='red brick band'
STONE='garden stair stone'
TILE='red French clay tile'
CAP='red tile ridge'
CUT='plain rear section'
DIAL='cream clock face'
METAL='dark bronze pointers'
LIGHT_STONE='pale exposed pebbles'
DARK_STONE='dark exposed pebbles'
PALETTE={name:dict(color=rgb,roughness=rough,metallic=metal)for name,rgb,rough,metal in [
    (PEBBLE,[.32,.31,.29],.92,0),(CREAM,[.76,.72,.61],.75,0),
    (WOOD,[.19,.125,.082],.73,0),(GLASS,[.226,.284,.257],.28,.18),
    (BRICK,[.423,.255,.178],.84,0),(STONE,[.575,.541,.45],.81,0),
    (TILE,[.59,.218,.106],.83,0),(CAP,[.428,.139,.065],.84,0),
    (CUT,[.44,.418,.35],.91,0),(DIAL,[.80,.77,.64],.65,.06),
    (METAL,[.155,.155,.127],.48,.34),(LIGHT_STONE,[.53,.51,.45],.93,0),
    (DARK_STONE,[.207,.204,.18],.95,0)]}

# Positions are measured along the roof and frontage. Each end terminates at
# its historic red-roofed pavilion. The later flat-ended extensions stay outside.
FIELDS=[(-51.05,-42.90,'end'),(-42.90,-29.34,'range'),(-29.34,-19.93,'inner'),
        (-19.93,-6.06,'range'),(-6.06,6.06,'clock'),(6.06,19.93,'range'),
        (19.93,29.34,'inner'),(29.34,42.90,'range'),(42.90,51.05,'end')]
DECK=5.27
EAVE=11.50
BACK=14.27


def slab(b,x,y,z,w,d,h,material,label):
    b.box((x,y,z+h/2),(w,d,h),material=material,label=label)


def window(f,u,bottom,width,height,rise,lod):
    shape=opening(u,bottom,width,height,rise,12 if lod else 22)
    f.prism(shape.buffer(.007),-.297,-.278,GLASS,'recessed glazing')
    surround=shape.buffer(.115,join_style=2).difference(shape)
    f.prism(surround,-.013,.068,CREAM,'pale arched surround')
    frame=shape.difference(shape.buffer(-.083,join_style=2))
    bars=[frame,box(u-.052,bottom,u+.052,bottom+height)]
    if not lod:
        for dx in [-.25,.25]:
            bars.append(box(u+dx*width-.024,bottom,u+dx*width+.024,bottom+height))
    at=bottom+height-rise-.13 if rise>.15 else bottom+height*.76
    for z in [bottom+height*.36,at]:
        bars.append(box(u-width/2,z-.045,u+width/2,z+.045))
    f.prism(unary_union(bars).intersection(shape),-.206,-.146,WOOD,'timber sash and transoms')
    return shape


def pebble_insets(f,wall,lod):
    if lod:return
    # Small irregular pieces represent the restored exposed aggregate in the grey
    # facade. Geometry stays on the solid walls and off sash, frames and balconies.
    rng=np.random.default_rng(int(round((f.center[0]+67)*79+f.center[1]*13)))
    x0,z0,x1,z1=wall.bounds
    for material in (LIGHT_STONE,DARK_STONE):
        vertices=[];faces=[]
        for _ in range(round(wall.area*6)):
            u=rng.uniform(x0,x1);z=rng.uniform(z0,z1)
            if not wall.contains(Point(u,z)):continue
            w=rng.uniform(.026,.053);h=rng.uniform(.024,.047)
            i=len(vertices);vertices.extend([f.point(u-w,z,.008),f.point(u,z-h,.010),f.point(u+w,z+.002,.010),f.point(u+.004,z+h,.009),f.point(u,z,.021)])
            faces.extend([(i,i+1,i+4),(i+1,i+2,i+4),(i+2,i+3,i+4),(i+3,i,i+4)])
        if faces:f.builder.add(vertices,faces,material,'exposed pebbles')

def field(b,left,right,kind,lod):
    mid=(left+right)/2;length=right-left
    upper_y={'clock':6.95,'inner':7.14,'end':7.18,'range':8.07}[kind]
    lower_y=8.14 if kind!='clock' else 7.34
    lower=Facade(b,(left,lower_y),(right,lower_y),'ground garden openings')
    upper=Facade(b,(left,upper_y),(right,upper_y),kind+' upper wall')
    bottom_holes=[];top_holes=[]
    if kind=='range':
        centers=[-length/3,0,length/3];width=2.23
        for u in centers:
            top_holes.append(window(upper,u,5.74,width,3.94,1.14,lod))
            bottom_holes.append(window(lower,u,.19,length/3-.42,4.20,.18,lod))
        for u in [-length/6,length/6]:
            # Vertical brick strips are visible against the exposed pebble finish.
            for dx in [-.24,.0,.24]:
                upper.prism(box(u+dx-.048,DECK+.1,u+dx+.048,9.76),.005,.030,BRICK,'vertical red brick detail')
    elif kind=='clock':
        for u,w,h in [(-3.72,1.95,4.04),(0,2.88,4.77),(3.72,1.95,4.04)]:
            top_holes.append(window(upper,u,5.67,w,h,w*.51,lod))
            bottom_holes.append(window(lower,u,.25,w,3.98,w*.31,lod))
    else:
        # Three separately glazed French doors sit under one low segmental head.
        env=opening(0,5.75,length*.79,3.83,1.16,16 if lod else 28)
        gleaf=env.bounds[2]
        for j,(a,c) in enumerate([(-gleaf,-gleaf*.36),(-gleaf*.30,gleaf*.30),(gleaf*.36,gleaf)]):
            shape=env.intersection(box(a,5.72,c,10.1))
            top_holes.append(shape)
            upper.prism(shape.buffer(.007),-.30,-.278,GLASS,'three lights under segmental head')
            frame=shape.difference(shape.buffer(-.079,join_style=2))
            mull=box((a+c)/2-.039,5.72,(a+c)/2+.039,10.1)
            horizontal=unary_union([box(a,6.88,c,6.96),box(a,8.67,c,8.75)])
            upper.prism(unary_union([frame,mull,horizontal]).intersection(shape),-.211,-.152,WOOD,'three French window sashes')
            is_door=j==1
            bottom_holes.append(window(lower,(a+c)/2,.14 if is_door else .77,c-a,4.04 if is_door else 3.47,.12,lod))
            if is_door:
                lower.prism(box(a+.048,.15,c-.048,.87),-.14,-.094,WOOD,'raised dark lower door panels')
        upper.prism(env.buffer(.11,join_style=2).difference(env),-.008,.064,CREAM,'common segmental window head')
    lower.wall(.12,DECK-.20,bottom_holes,.39,PEBBLE)
    face=upper.wall(DECK,EAVE,top_holes,.37,PEBBLE)
    pebble_insets(upper,face,lod)
    for h in [0.13,.31]:
        lower.prism(box(-length/2,h,length/2,h+.11).difference(unary_union(bottom_holes)),.0,.085,CREAM,'low plinth moulding')
    for x in [left+.32,right-.32]:
        slab(b,x,upper_y-.10,DECK,.12,.14,EAVE-DECK-.28,CREAM,'pale pavilion corner quoin')
    slab(b,mid,(BACK+upper_y)/2,0,length,BACK-upper_y,.075,CUT,'ground of garden section')
    slab(b,mid,BACK-.05,.04,length,.1,EAVE-.04,CUT,'interior cut behind south range')
    for x in [left,right]:
        slab(b,x,(upper_y+BACK)/2,DECK,.065,BACK-upper_y,EAVE-DECK,PEBBLE if x in (-51.05,51.05)else CUT,'short pavilion return')
    landing_y=.06 if kind=='clock' else 6.39
    slab(b,mid,(landing_y+upper_y+.45)/2,DECK-.31,length,upper_y+.45-landing_y,.31,CREAM,'second storey gallery floor')
    slab(b,mid,landing_y+.11,DECK-.47,length,.22,.18,CREAM,'gallery beam')
    if kind!='clock':
        # The garden colonnade shades the recessed ground windows.
        for x in [left+.11,mid,right-.11]:
            slab(b,x,6.57,.16,.25,.29,DECK-.51,CREAM,'lower gallery support')
    return upper_y


def railing(b,a,c,y,lod,label):
    length=c-a;mid=(a+c)/2
    slab(b,mid,y,DECK+.01,length,.21,.12,CREAM,label+' foot rail')
    slab(b,mid,y,DECK+1.05,length,.23,.13,CREAM,label+' top rail')
    count=max(1,round(length/2.75))
    for u in np.linspace(a+.12,c-.12,count+1):
        slab(b,u,y,DECK+.03,.24,.25,1.12,CREAM,label+' square post')
        slab(b,u,y,DECK+1.14,.32,.31,.09,CREAM,label+' post cap')
    # Turned timber balusters stand individually clear of the lawn beyond.
    n=max(1,round(length/.46))
    for u in np.linspace(a+length/n/2,c-length/n/2,n):
        profile=[(DECK+.12,.055),(DECK+.24,.058),(DECK+.41,.094),(DECK+.66,.04),(DECK+.85,.058),(DECK+1.075,.049)]
        b.lathe((u,y),profile,CREAM,5 if lod else 9,label+' turned balusters')


def entry_terrace(b,lod):
    for sign in [-1,1]:
        for y in [.29,5.47]:
            slab(b,sign*5.65,y,.27,.33,.37,DECK-.62,CREAM,'free-standing square terrace column')
        slab(b,sign*5.73,3.19,DECK-.44,.28,6.21,.2,CREAM,'side architrave')
        for y in np.arange(.22,6.2,.51):
            b.lathe((sign*5.75,y),[(DECK+.10,.059),(DECK+.36,.094),(DECK+.63,.041),(DECK+1.055,.052)],CREAM,5 if lod else 8,'terrace side balusters')
        for z,h in [(DECK+.015,.12),(DECK+1.04,.14)]:
            slab(b,sign*5.75,3.27,z,.23,6.45,h,CREAM,'terrace side rails')
    for i,(front,top) in enumerate([(-1.07,.095),(-.76,.19),(-.45,.29)]):
        slab(b,0,(front+7.84)/2,0,12.08-(i*.08),7.84-front,top,STONE,'broad garden entrance steps')
    railing(b,-5.78,5.78,.16,lod,'terrace front')
    for x in [-3.16,0,3.16]:
        slab(b,x,.21,DECK+.22,1.26,.13,.31,CREAM,'solid panels in terrace parapet')


def add_garden(b,lod):
    from garden_roofs import add_roofs
    for x0,x1,kind in FIELDS:
        field(b,x0,x1,kind,lod)
        if kind!='clock':railing(b,x0,x1,6.46,lod,'long south gallery')
    entry_terrace(b,lod)
    add_roofs(b,lod)
