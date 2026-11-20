"""Holy Trinity Cathedral, rotated from the east garden toward the west chancel."""
from math import cos,sin,pi
from shapely.geometry import Polygon,Point,box
from shapely.ops import unary_union
from photo_architecture import Facade
from gothic import RED,DARK,BASE,PALE,GLASS,FRAME,arch,light,colonnade,voussoirs
from roofs import (add_roofs,CROSS_Y,TRANSVERSE_HALF,NAVE_END,HALF,EAVE,PEAK,RIDGE,
                   APSE_START,APSE_TANGENT,APSE_RADIUS,APSE_HALF,APSE_EAVE)

PALETTE={
    RED:{'color':[.50,.208,.128],'roughness':.82},DARK:{'color':[.30,.163,.139],'roughness':.86},
    BASE:{'color':[.46,.405,.345],'roughness':.82},PALE:{'color':[.59,.53,.465],'roughness':.83},
    GLASS:{'color':[.18,.235,.24],'roughness':.34,'metallic':.19},
    FRAME:{'color':[.12,.115,.105],'roughness':.55,'metallic':.20},
    'rose glazing':{'color':[.39,.21,.17],'roughness':.34,'metallic':.12},
    'slate roof':{'color':[.26,.28,.29],'roughness':.82},
    RIDGE:{'color':[.41,.40,.38],'roughness':.79},'oak door':{'color':[.225,.125,.073],'roughness':.68},
    'porch pavement':{'color':[.47,.438,.39],'roughness':.88}}


def rose(f,z,lod):
    r=1.35;circle=Point(0,z).buffer(r,quad_segs=12 if lod else 24)
    floral=Point(0,z).buffer(.34,quad_segs=12)
    for k in range(6):
        a=pi/2+k*pi/3
        petal=Point(.55*cos(a),z+.55*sin(a)).buffer(.305,quad_segs=8 if lod else 15)
        floral=floral.union(petal)
    f.prism(circle,-.26,-.23,'rose glazing','traceried rose glass')
    f.prism(circle.difference(floral),-.15,-.08,PALE,'six-lobed circular tracery')
    for i in range(26):
        a=2*pi*i/26;c=2*pi*(i+1)/26
        seg=Polygon([(r*cos(a),z+r*sin(a)),((r+.20)*cos(a),z+(r+.20)*sin(a)),
                     ((r+.20)*cos(c),z+(r+.20)*sin(c)),(r*cos(c),z+r*sin(c))])
        f.prism(seg,-.05,.105,DARK if i%2 else RED,'rose ring segments')
    return circle


def gable(f,top,eaves,holes,lod,front=False):
    a=f.length/2
    shape=Polygon([(-a,0),(a,0),(a,eaves),(0,top),(-a,eaves)])
    f.wall(0,top,holes,.45,RED,shape)
    for side in (-1,1):
        f.line((0,top+.04,.02),(side*a,eaves+.04,.02),.13,RIDGE,8,'sloping gable coping')
        for j in range(1,10 if front else 7):
            t=j/(10 if front else 7);u=side*a*t;z=top+(eaves-top)*t-.46
            f.box(u,z,.19,.38,.22,.04,RED,'stepped brick gable dentils')
    for u in (-a+.18,a-.18):
        f.box(u,eaves*.49,.43,eaves*.98,.40,.05,RED,'gable angle buttress')
        for h in (4.1,8.45,eaves-.70):f.box(u,h,.59,.13,.52,.09,PALE,'buttress stone string')
    f.beam(.20,.38,.10,BASE,width=f.length,label='stone foot')


def east_end(b,lod):
    f=Facade(b,(-HALF,.0),(HALF,.0),'East nave gable')
    holes=[rose(f,14.25,lod)]
    for z,h in [(7.10,1.85),(9.65,2.36)]:
        for k in range(-3,4):
            holes.append(light(f,k*1.34,z,1.12,h,lod,columns=1))
        f.beam(z-.12,.14,.14,PALE,width=10.20,label='arcade sill band')
    central,curve,_=arch(0,.12,3.38,4.99,1.69,True,lod);holes.append(central)
    f.prism(central,-.61,-.55,'oak door','setback garden doors')
    voussoirs(f,curve,lod,.20)
    for u in (-3.24,3.24):holes.append(light(f,u,.51,1.49,3.68,lod))
    gable(f,PEAK,EAVE,holes,lod,True)
    f.line((0,PEAK,0),(0,PEAK+.90,0),.075,PALE,9,'gable cross upright')
    f.line((-.27,PEAK+.63,0),(.27,PEAK+.63,0),.073,PALE,8,'gable cross bar')
    # Garden portal with a broad round centre and two pointed side openings.
    front=Facade(b,(-5.60,-4.25),(5.60,-4.25),'Garden porch front')
    colonnade(front,[2.55,4.38,2.55],lod,top=5.68,spring=2.83,round_flags=(1,),end_piers=.48,shaft_radius=.34)
    for sign in (-1,1):
        x=sign*5.60;a=(x,-4.25);c=(x,0)
        if sign<0:a,c=c,a
        side=Facade(b,a,c,'Garden porch return')
        colonnade(side,[1],lod,top=5.68,spring=2.83,round_flags=(0,),end_piers=.57,shaft_radius=.32)
    b.plan_prism(box(-5.69,-4.33,5.69,.02),5.66,5.82,PALE,'Garden porch/flat roof slab')
    b.plan_prism(box(-5.60,-4.25,5.60,.03),.0,.115,'porch pavement','Garden porch/stone paving')
    for a,c in [((-5.60,-4.25),(5.60,-4.25)),((5.60,-4.25),(5.60,.05)),((-5.60,.05),(-5.60,-4.25))]:
        side=Facade(b,a,c,'Open stone parapet');hs=[];n=round(side.length/.52)
        for j in range(n):
            u=(j+.5)*side.length/n-side.length/2
            h,_,_=arch(u,5.96,.28,.40,.14,True,lod);hs.append(h)
        side.wall(5.82,6.48,hs,.25,RED)
        side.beam(6.48,.13,.11,PALE,width=side.length+.04,label='parapet coping')


def side_aisles(b,lod):
    for sign in (-1,1):
        # Positive directed x is toward the north when looking from the garden.
        if sign>0:
            fr=Facade(b,(HALF,0),(12.18,0),'North aisle east');long=Facade(b,(12.18,0),(12.18,29.78),'North open walk')
            inside=Facade(b,(9.51,.16),(9.51,29.76),'North aisle wall')
            cler=Facade(b,(5.65,.18),(5.65,29.77),'North clerestory')
        else:
            fr=Facade(b,(-12.18,0),(-HALF,0),'South aisle east');long=Facade(b,(-12.18,29.78),(-12.18,0),'South open walk')
            inside=Facade(b,(-9.51,29.76),(-9.51,.16),'South aisle wall')
            cler=Facade(b,(-5.65,29.77),(-5.65,.18),'South clerestory')
        colonnade(fr,[1,1,1],lod,top=5.91,spring=2.48,end_piers=.39,shaft_radius=.23)
        # Six arcade bays give a clear walk between the rear glazing and the stone columns.
        colonnade(long,[1]*6,lod,top=5.93,spring=2.90,end_piers=.48,shaft_radius=.32)
        crosssection=Polygon([(-fr.length/2,5.91),(fr.length/2,5.91),
                              (fr.length/2,6.05 if sign>0 else 10.10),
                              (-fr.length/2,10.10 if sign>0 else 6.05)])
        hs=[]
        for k in range(5):
            t=(k+.5)/5;u=(t-.5)*fr.length
            top=9.58-3.54*(t if sign>0 else 1-t)
            if top-6.10>.70:hs.append(light(fr,u,6.10,.70,top-6.10,lod,rise=.49,columns=1))
        fr.wall(5.91,10.14,hs,.32,RED,crosssection)
        hs=[]
        for j in range(6):
            u=(j+.5)*inside.length/6-inside.length/2
            hs.append(light(inside,u,1.1,1.78,3.75,lod))
        inside.wall(0,7.83,hs,.37,RED)
        hs=[]
        for j in range(5):
            center=(j+.5)*cler.length/5-cler.length/2
            for k in (-1,0,1):hs.append(light(cler,center+k*1.32,9.65,1.08,2.37,lod,columns=1))
        cler.wall(7.73,EAVE,hs,.40,RED)
        cler.beam(12.36,.13,.14,PALE,width=cler.length,label='clerestory eave')
        b.plan_prism(box(min(sign*12.17,sign*9.45),.05,max(sign*12.17,sign*9.45),29.75),
                     0,.105,'porch pavement','Side walks/paving')


def back(b,lod):
    ymin,ymax=CROSS_Y-TRANSVERSE_HALF,CROSS_Y+TRANSVERSE_HALF
    for sign,end in [(-1,13.88),(1,12.98)]:
        x=sign*end
        face=Facade(b,(x,ymin),(x,ymax),'North transept') if sign>0 else Facade(b,(x,ymax),(x,ymin),'South transept')
        holes=[]
        for u in (-3.65,-2.24,2.24,3.65):
            holes.append(light(face,u,8.65,1.18,2.90,lod))
        for u in (-2.9,0,2.9):holes.append(light(face,u,2.00,1.63,3.94,lod))
        gable(face,PEAK,EAVE,holes,lod)
        for y in (ymin,ymax):
            a,c=(sign*HALF,y),(x,y)
            if (y==ymin and sign<0) or (y==ymax and sign>0):a,c=c,a
            f=Facade(b,a,c,'Transept return')
            hs=[]
            for k in (-.25,.25):
                hs.append(light(f,k*f.length,9.05,1.48,2.74,lod))
            f.wall(0,EAVE,hs,.35,RED)
            f.beam(.2,.4,.08,BASE,width=f.length,label='plinth')
    n=14 if lod else 32
    apse=[(-APSE_HALF,APSE_START),(-APSE_HALF,APSE_TANGENT)]
    apse += [(APSE_HALF*cos(pi-pi*i/n),APSE_TANGENT+APSE_RADIUS*sin(pi-pi*i/n)) for i in range(1,n+1)]
    apse.append((APSE_HALF,APSE_START))
    for a,c in zip(apse,apse[1:]):
        f=Facade(b,c,a,'West sanctuary')
        f.wall(0,APSE_EAVE,(),.22,RED)
        f.beam(.21,.39,.06,BASE,width=f.length,label='stone base')
    for sign in (-1,1):
        outer=10.25 if sign>0 else 11.17
        section=[(sign*5.44,39.19),(sign*outer,39.19),(sign*outer,44.20),(sign*5.44,44.20)]
        for i in [1,2,3]:
            a,c=section[i],section[(i+1)%4]
            if sign<0:a,c=c,a
            f=Facade(b,a,c,'Chancel side annex');f.wall(0,5.74,(),.28,RED)
        b.plan_prism(Polygon(section),0,.108,BASE,'Chancel annex/paving')
    rear=Facade(b,(HALF,NAVE_END),(-HALF,NAVE_END),'West nave roof end')
    roofend=Polygon([(-HALF,APSE_EAVE),(HALF,APSE_EAVE),(HALF,EAVE),(0,PEAK),(-HALF,EAVE)])
    rear.wall(APSE_EAVE,PEAK,(),.34,RED,roofend)
    # The closed nave and cross arm are occupied. Exterior porch paving
    # remains separate so bounding boxes need never close the side walks.
    b.plan_prism(box(-9.50,.18,9.50,29.77),0,.108,BASE,'Main church/closed nave paving')
    b.plan_prism(box(-13.82,ymin+.03,12.93,ymax-.03),0,.108,BASE,'Transept/floor')
    b.plan_prism(Polygon(apse),0,.108,BASE,'West chancel/floor')


def add_cathedral(b,lod):
    east_end(b,lod)
    side_aisles(b,lod)
    back(b,lod)
    add_roofs(b,lod)
