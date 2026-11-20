"""Street front and tower of Moore Memorial Church, based on 2010/2013 photographs."""
import math
import numpy as np
from shapely.geometry import Polygon,Point,box
from shapely.ops import unary_union
from photo_architecture import Facade

BRICK='dark red face brick'; SHADE='burnt brick'; STONE='pale limestone bands'; TERR='red clay tile'
GLASS='blue grey church glass'; DULL='metal belfry screens'; FRAME='dark iron sash'; OAK='wood door'; CROSS='painted red iron cross'
PALETTE={BRICK:{'color':[.39,.18,.135],'roughness':.88},SHADE:{'color':[.31,.125,.093],'roughness':.92},
 STONE:{'color':[.73,.67,.52],'roughness':.84},TERR:{'color':[.38,.205,.145],'roughness':.85},
 GLASS:{'color':[.16,.28,.30],'roughness':.31,'metallic':.10},DULL:{'color':[.072,.085,.087],'roughness':.79},
 FRAME:{'color':[.19,.17,.14],'roughness':.62},OAK:{'color':[.19,.11,.080],'roughness':.70},
 CROSS:{'color':[.42,.105,.089],'roughness':.54,'metallic':.35}}

def pointed(u,z,width,height,rise,lod):
    half=width/2;shift=(rise*rise-half*half)/(2*half);radius=half+shift
    angles=np.linspace(math.pi,math.acos(-shift/radius),7 if lod else 17)
    left=[(u+shift+radius*math.cos(t),z+height-rise+radius*math.sin(t)) for t in angles]
    edge=left+[(2*u-x,y) for x,y in reversed(left[:-1])]
    return Polygon([(u-half,z),(u+half,z),*reversed(edge)])

def panel(f,u,z,width,height,lod,kind='glass',lancets=0):
    if lancets:
        rise=min(.91*width,.47*height);gap=pointed(u,z,width,height,rise,lod)
    else:gap=box(u-width/2,z,u+width/2,z+height)
    material={'glass':GLASS,'screen':DULL,'door':OAK}[kind]
    f.prism(gap.buffer(.015,join_style=2),-.39,-.366,material,'recessed '+kind)
    f.prism(gap.buffer(.12 if lancets else .105,join_style=2).difference(gap),-.012,.14,STONE,'dressed window surrounds')
    f.box(u,z-.075,width+.30,.15,.52,-.035,STONE,'sill')
    if lancets:
        inner=gap.buffer(-.082,join_style=2)
        divisions=[box(u-width/2+width*i/lancets-.045,z,u-width/2+width*i/lancets+.045,z+height) for i in range(1,lancets)]
        for z0 in [z+height*.32,z+height*.61]:
            divisions.append(box(u-width/2,z0-.037,u+width/2,z0+.037))
        # Stone lobes spring from each lancet below the head; above them the central circular light is retained.
        for i in range(lancets):
            sub=width*.92/lancets;c=u-width*.46+(i+.5)*sub;h=height-rise*.55
            arch=pointed(c,z+.04,sub-.086,h,sub*.72,lod)
            divisions.append(arch.boundary.buffer(.055,cap_style=2,join_style=2))
        if kind!='door' and width>2.5:
            for px,pz,r in [(u,z+height-rise*.56,width*.115),(u-width*.17,z+height-rise*.84,width*.082),(u+width*.17,z+height-rise*.84,width*.082)]:
                a=Point(px,pz).buffer(r,quad_segs=6 if lod else 12);divisions.append(a.difference(a.buffer(-.064)))
        f.prism(gap.buffer(-.018,join_style=2).difference(inner).union(inner.intersection(unary_union(divisions))),-.295,-.185,STONE,'tracery and mullions')
        if kind=='screen' and not lod:
            ribs=[box(u-width/2,z+k*.30,u+width/2,z+k*.30+.045) for k in range(1,int(height/.30))]
            f.prism(gap.intersection(unary_union(ribs)),-.356,-.326,FRAME,'belfry louvers')
    else:
        bars=[box(u-.033,z,u+.033,z+height),box(u-width/2,z+.60*height-.027,u+width/2,z+.60*height+.027)]
        f.prism(gap.intersection(unary_union(bars)),-.315,-.26,FRAME,'sash')
    return gap

def roof(b,x0,x1,y0,y1,eave,ridge,lod,label):
    cy=(y0+y1)/2
    for j,y in enumerate((y0,y1)):
        vertices=[(x0,y,eave),(x1,y,eave),(x1,cy,ridge),(x0,cy,ridge)]
        if j==1:vertices.reverse()
        b.add(vertices+[(x,y,z-.18) for x,y,z in vertices],[(0,1,2,3),(7,6,5,4),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)],TERR,label+'/tile slope')
        if not lod:
            for w in np.arange(.07,.99,.065):
                yy=y*(1-w)+cy*w; zz=eave*(1-w)+ridge*w+.025
                b.tube([(x0,yy,zz),(x1,yy,zz)],.025,TERR,5,label+'/tile courses')
    b.tube([(x0,cy,ridge+.025),(x1,cy,ridge+.025)],.081,SHADE,8,label+'/ridge')

def gable(f,eave,peak,holes,lod,stepped=True):
    half=f.length/2
    outline=Polygon([(-half,0),(half,0),(half,eave),(0,peak),(-half,eave)])
    f.wall(0,peak,holes,.43,BRICK,outline)
    for side in (-1,1):
        f.line((side*half,eave,.04),(0,peak,.04),.10,STONE,6)
        if stepped:
            for q in np.linspace(.11,.90,7 if not lod else 4):
                x=side*half*q;z=peak-(peak-eave)*q
                f.box(x,z+.06,.35,.22,.46,-.02,STONE,'stepped gable coping')

def oriel(f,u,bottom,width,levels,lod):
    left,right=u-width/2,u+width/2
    # Project the two-tier window face out in front of the brickwork, with actual cut glazing.
    h=3.70;front=.45;holes=[]
    for row in range(levels):
        z=bottom+row*h+.41;w=(width-.65)/3
        for i in [-1,0,1]:
            c=u+i*(w+.07);gap=box(c-w/2,z,c+w/2,z+h-.75);holes.append(gap)
            f.prism(gap,front-.20,front-.17,GLASS,'oriel recessed glass')
            bars=[box(c-.025,z,c+.025,z+h),box(c-w/2,z+1.72,c+w/2,z+1.78)]
            f.prism(gap.intersection(unary_union(bars)),front-.14,front-.07,FRAME,'oriel sash')
    cut=unary_union(holes);wide=box(left,bottom,right,bottom+levels*h)
    f.prism(wide.difference(cut),-.012,front,STONE,'projecting oriel mullions')
    f.box(u,bottom-.15,width+.15,.30,.68,.15,STONE,'oriel plinth')
    for row in range(1,levels+1):f.box(u,bottom+row*h-.09,width+.17,.18,.73,.15,STONE,'oriel band')
    return wide.buffer(-.06,join_style=2)

def wing(b,label,x0,x1,y0,y1,eave,peak,lod):
    w=y1-y0
    front=Facade(b,(x0,y1),(x0,y0),label+'/street gable');holes=[]
    for u in [-w*.29,w*.29]:holes.append(panel(front,u,.82,1.75,2.68,lod))
    holes.append(oriel(front,0,4.63,w*.48,2,lod))
    for u in [-w*.114,0,w*.114]:holes.append(panel(front,u,12.62,1.25,2.21,lod))
    for u in [-.47,.47]:holes.append(panel(front,u,16.08,.63,1.14,lod))
    gable(front,eave,peak,holes,lod)
    for y,reverse in [(y0,False),(y1,True)]:
        pts=[(x0,y),(x1,y)]
        if reverse:pts.reverse()
        side=Facade(b,*pts,label+'/long return');cuts=[]
        cols=max(3,round(side.length/4.35))
        for i in range(cols):
            u=(i+.5-cols/2)*side.length/cols
            for z in [1.02,5.11,9.25]:
                width=2.39 if i not in (0,cols-1) else 1.72
                cuts.append(panel(side,u,z,width,2.32,lod))
        side.wall(0,eave,cuts,.40,BRICK)
        for z in [.44,4.34,8.55,eave-.11]:side.beam(z,.16,.08,STONE)
    rear=Facade(b,(x1,y0),(x1,y1),label+'/back gable')
    gable(rear,eave,peak,[],lod,False)
    roof(b,x0+.07,x1-.07,y0+.07,y1-.07,eave-.02,peak-.08,lod,label)
    b.plan_prism(box(x0,y0,x1,y1),0,.12,SHADE,label+'/ground slab')

def nave(b,lod):
    label='Sanctuary';x0=-14.20;x1=16.86;y0=-7.36;y1=9.76;cy=(y0+y1)*.5
    f=Facade(b,(x0,y1),(x0,y0),label+'/west entrance');half=f.length/2
    holes=[panel(f,0,9.55,5.03,7.21,lod,lancets=3)]
    for u in [-half+.99,half-.99]:holes.append(panel(f,u,3.4,1.03,3.54,lod,lancets=1))
    door=pointed(0,.05,2.34,3.30,1.14,lod);holes.append(door);f.prism(door,-.51,-.466,OAK,'double door')
    outline=Polygon([(-half,0),(half,0),(half,9.60),(5.68,11.70),(5.68,15.05),(0,21.75),(-5.68,15.05),(-5.68,11.70),(-half,9.60)])
    f.wall(0,21.75,holes,.53,BRICK,outline)
    for sign in (-1,1):
        f.line((0,21.76,.005),(5.68*sign,15.05,.005),.085,STONE,6)
        for u in [3.16*sign,5.84*sign]:
            f.prism(Polygon([(u-.24,.20),(u+.24,.20),(u+.24,12.5),(u,13.15),(u-.24,12.5)]),-.08,.39,BRICK,'entrance buttress')
            f.box(u,12.52,.57,.15,.68,.12,STONE,'buttress coping')
    f.box(0,19.09,.20,1.32,.13,.068,STONE,'gable cross');f.box(0,19.29,.82,.17,.15,.07,STONE,'gable cross')
    # A separate porch in front of the red gable with its own open cream-coloured arch and a recessed door behind.
    apex=7.04;p=Facade(b,(x0-1.52,cy+2.89),(x0-1.52,cy-2.89),label+'/stone entry porch')
    opening=pointed(0,0,2.79,4.94,1.60,lod)
    poly=Polygon([(-2.89,0),(2.89,0),(2.89,4.54),(1.52,5.95),(0,apex),(-1.52,5.95),(-2.89,4.54)])
    p.prism(poly.difference(opening),-.37,0,STONE,'pointed portal')
    p.prism(opening.buffer(.20,join_style=2).difference(opening).intersection(poly),.015,.14,STONE,'portal moulding')
    for w in [-2.68,2.68]:
        p.box(w,1.96,.48,3.92,1.66,-.62,STONE,'porch return pier')
    b.plan_prism(box(x0-1.88,cy-2.90,x0+.02,cy+2.90),0,.13,STONE,'Porch/step')
    for y,rev in [(y0,False),(y1,True)]:
        pts=[(x0,y),(x1,y)]
        if rev:pts.reverse()
        side=Facade(b,*pts,label+'/side aisle');cuts=[]
        for i in range(5):
            u=(i-2)*5.72;cuts.append(panel(side,u,3.32,1.72,4.61,lod,lancets=2))
            side.box(u-1.58,4.35,.42,8.70,.48,.12,BRICK,'buttress')
        side.wall(0,9.64,cuts,.41,BRICK)
    for s in [-1,1]:
        y=cy+s*5.67
        b.box(((x0+x1)/2,y,13.34),(x1-x0,.36,4.64),BRICK,label='Sanctuary/clerestory wall')
        zy=cy+s*half
        verts=[(x0,zy,9.68),(x1,zy,9.68),(x1,y,11.83),(x0,y,11.83)]
        if s>0:verts.reverse()
        b.add(verts+[(x,y,z-.13) for x,y,z in verts],[(0,1,2,3),(7,6,5,4),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)],TERR,'Sanctuary/low aisle roof')
    roof(b,x0+.05,x1,cy-5.70,cy+5.70,15.04,21.66,lod,label)
    back=Facade(b,(x1,y0),(x1,y1),label+'/east wall')
    back.wall(0,21.75,[],.42,BRICK,outline)
    b.plan_prism(box(x0,y0,x1,y1),0,.105,SHADE,'Sanctuary/ground slab')

def bell_tower(b,lod):
    # Square to the church grid, at the south edge of the sanctuary behind the southwest wing.
    cx,cy=-4.58,-10.66;dx,dy=3.72,3.64
    points=[(cx-dx,cy-dy),(cx+dx,cy-dy),(cx+dx,cy+dy),(cx-dx,cy+dy)]
    for i,p in enumerate(points):
        f=Facade(b,p,points[(i+1)%4],'Tower/'+['south','east','north','west'][i]);holes=[]
        for z,width,h,k in [(13.42,3.51,10.19,'glass'),(27.16,3.61,8.76,'screen')]:
            holes.append(panel(f,0,z,width,h,lod,k,2))
        f.wall(0,37.75,holes,.55,BRICK)
        for pos in [-f.length/2+.53,f.length/2-.53]:
            for low,top,w,d in [(.11,13.02,.82,.54),(13.02,24.83,.74,.40),(24.83,37.89,.59,.31)]:
                f.box(pos,(low+top)/2,w,top-low,d,.12,BRICK,'stepped buttress')
                if top<37:f.box(pos,top-.03,w+.16,.105,d+.16,.17,STONE,'buttress coping')
        for z,width in [(13.25,4.30),(26.95,4.41)]:f.box(0,z,width,.19,.57,.075,STONE,'lancet sill band')
        for pos in [-f.length*.38,f.length*.38]:
            f.box(pos,33.57,1.50,.46,.44,.10,STONE,'upper limestone belt')
        # The crown is flat and crenellated. The pictures show deep notches, with no spire.
        for pos in [-f.length*.39,0,f.length*.39]:
            f.box(pos,38.12,1.40,.74,.52,-.06,BRICK,'crown merlon')
            f.box(pos,38.51,1.49,.12,.58,-.05,STONE,'merlon cap')
    b.plan_prism(box(cx-dx,cy-dy,cx+dx,cy+dy),37.34,37.52,SHADE,'Tower/flat roof')
    b.box((cx,cy,40.28),(.39,.36,5.10),CROSS,label='Tower/red cross upright')
    b.box((cx,cy,41.29),(3.10,.40,.42),CROSS,label='Tower/red cross arm')
    # The street looks west, so the long arm lies north/south across that elevation.
    cross=b.parts[-1]
    cross['vertices']=[(cx-(y-cy),cy+(x-cx),z) for x,y,z in cross['vertices']]

def east_wing(b,lod):
    # OSM shows a second rear block separated from the main west court; ridge subdivision at the back is estimated.
    poly=Polygon([(15.61,-20.79),(37.94,-21.00),(38.29,-6.59),(24.14,-6.39),(24.18,3.38),(16.83,3.07),(16.83,-7.31),(15.61,-7.31)])
    pts=list(poly.exterior.coords)
    for i,(a,c) in enumerate(zip(pts,pts[1:])):
        f=Facade(b,a,c,'East annex/return '+str(i+1));cuts=[]
        if f.length>5:
            n=max(1,round(f.length/4))
            for j in range(n):
                u=(j+.5-n/2)*f.length/n
                for z in [1.15,4.93,8.80]:
                    cuts.append(panel(f,u,z,1.45,1.93,lod))
        f.wall(0,12.17,cuts,.36,BRICK)
        f.beam(12.10,.17,.08,STONE)
    b.plan_prism(poly,12.12,12.27,'roof zinc','East annex/estimated low roof')
    b.plan_prism(poly,0,.11,SHADE,'East annex/ground slab')
    # West-east connection just south of the main sanctuary, on the frozen ring's return.
    q=Polygon([(-8.03,-7.15),(-.63,-7.15),(-.70,-12.95),(-3.04,-14.97),(-7.40,-15.24),(-8.03,-15.24)])
    b.plan_prism(q,0,11.1,BRICK,'Tower base/low connecting return')

def add_building(b,lod):
    wing(b,'Northwest annex',-29.91,-.04,10.53,25.21,13.55,19.56,lod)
    wing(b,'Southwest annex',-25.15,-7.48,-21.42,-7.90,13.28,19.02,lod)
    nave(b,lod);east_wing(b,lod);bell_tower(b,lod)
    # The western forecourt stays open between the two projecting wings. Short roofs join the masonry at its inner corners.
    for label,plan,height in [('north',box(-14.18,9.68,-.06,10.59),9.46),('south',box(-14.14,-7.95,-7.52,-7.33),9.22)]:
        b.plan_prism(plan,0,height,BRICK,'Aisles/'+label+' masonry link')
        b.plan_prism(plan,height,height+.13,TERR,'Aisles/'+label+' roof link')
    # Rotate the metric source plan so that the standalone front camera faces the three western gables.
    for part in b.parts:part['vertices']=[(-y,x,z) for x,y,z in part['vertices']]
