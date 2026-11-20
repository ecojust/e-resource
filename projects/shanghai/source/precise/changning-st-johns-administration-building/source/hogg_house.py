"""South veranda and lookout of Hogg's House, using ECUPL's historic and modern views."""
from math import cos, pi, sin
import numpy as np
from shapely import union_all
from shapely.geometry import box, Polygon
from photo_architecture import Facade, opening

WIDTH=26.6
BACK=9.8
RED='lacquered red timber'
DARK='oxblood trim'
IRON='black sheet iron'
GLASS='grey blue glass'
YELLOW='buff plaster'
STONE='veranda granite'
PALETTE={k:{'color':v,'roughness':h} for k,v,h in [
 (RED,[.48,.094,.056],.72),(DARK,[.27,.075,.055],.82),
 (IRON,[.143,.148,.157],.74),('folded iron seams',[.235,.234,.234],.72),
 (GLASS,[.244,.298,.294],.25),('high lights',[.345,.385,.358],.29),
 (YELLOW,[.882,.685,.407],.91),('light plaster',[.910,.848,.727],.90),
 (STONE,[.55,.536,.482],.94),('door wood',[.236,.101,.061],.70),
 ('shadowed opening',[.121,.122,.109],.91),('iron bracket',[.19,.139,.097],.72),
 ('ridge terminals',[.19,.169,.156],.74),('neutral section',[.547,.495,.414],.95)]}

def strip(builder,center,size,mat,name):
    builder.box(center,size,mat,label=name)

def glass(f,u,z,w,h,nx,ny,lod,name):
    shape=box(u-w/2,z,u+w/2,z+h)
    f.prism(shape,-.167,-.143,GLASS,name+'/glass')
    border=shape.difference(shape.buffer(-.062,join_style=2))
    bars=[box(u-w/2+w*i/nx-.023,z,u-w/2+w*i/nx+.023,z+h) for i in range(1,nx)]
    bars+=[box(u-w/2,z+h*i/ny-.022,u+w/2,z+h*i/ny+.022) for i in range(1,ny)]
    f.prism(union_all([border,*bars]),-.109,-.041,RED,name+'/wooden sash')
    if not lod:
        for i in range(nx):
            x=u-w/2+w*(i+.5)/nx
            p=box(x-w/nx*.43,z+h*.805,x+w/nx*.43,z+h*.95)
            f.prism(p,-.141,-.135,'high lights',name+'/transom reflections')
    return shape

def fret(f,u,z,w,h,lod,label):
    """Repeated angular Chinese fret enclosed by a frame. Real open spaces between strips."""
    x=u-w/2;stroke=.043 if not lod else .059
    pattern=[(0,.52),(.10,.52),(.10,.22),(.73,.22),(.73,.76),(.31,.76),(.31,.47),(.54,.47),(.54,.60),(.47,.60)]
    n=max(2,round(w/(.61 if not lod else .86)));step=w/n
    from shapely.geometry import LineString
    parts=[]
    for i in range(n):
        ox=x+i*step
        trace=[(ox+v*step,z+y*h)for v,y in pattern]
        parts.append(LineString(trace).buffer(stroke,cap_style=3,join_style=2))
        parts.append(box(ox+step*.87-stroke,z+h*.19,ox+step*.87+stroke,z+h*.79))
    frame=box(x,z,x+w,z+h).difference(box(x+.055,z+.064,x+w-.055,z+h-.064))
    f.prism(union_all([*parts,frame]),.017,.095,RED,label+'/pierced fret')
    f.box(u,z+h+.035,w+.10,.076,.19,.047,DARK,label+'/cap rail')

def porch_column(b,x,y,z0,z1,r,lod,label):
    strip(b,(x,y,z0+.10),(r*2.6,r*2.6,.20),STONE,label+'/plinth')
    b.tube([(x,y,z0+.20),(x,y,z1-.12)],r,RED,sides=12 if lod else 20,label=label+'/round lacquered post')
    strip(b,(x,y,z1-.11),(r*2.45,r*2.45,.22),DARK,label+'/head')

def front(b,lod):
    ground=Facade(b,(-WIDTH/2,3.0),(WIDTH/2,3.0),'South veranda wall')
    holes=[]; centers=np.linspace(-11.35,11.35,7)
    for i,x in enumerate(centers):
        if i in (2,5):
            door=opening(x,.29,1.54,2.68);holes.append(door)
            ground.prism(door,-.237,-.19,'door wood','double entrance')
            for u in (x-.36,x+.36):
                glass(ground,u,1.75,.52,.91,2,2,lod,'door upper lights')
                ground.box(u,.97,.52,.92,.075,-.14,DARK,'paired raised door panels')
            ground.box(x,3.01,1.72,.16,.19,.015,DARK,'head over entrance')
        else:
            w=1.66;holes.append(glass(ground,x,1.03,w,1.96,3,3,lod,'ground windows'))
            ground.box(x,.99,w+.20,.105,.19,.02,DARK,'lower sash sill')
    ground.wall(.30,4.26,holes,.27,YELLOW)
    b.plan_prism(box(-WIDTH/2,-.12,WIDTH/2,3.08),.17,.30,STONE,'South veranda/raised stone floor')
    for i,z in enumerate([.065,.145,.221]):
        b.plan_prism(box(-5.20,-1.12+i*.32,-1.9,-.10),z-.065,z,STONE,'South veranda/three steps')
    posts=np.arange(-13.05,13.20,3.27)
    for x in posts:porch_column(b,x,.12,.30,4.31,.125,lod,'South veranda')
    strip(b,(0,.12,4.25),(WIDTH,.31,.32),DARK,'South veranda/continuous timber girder')
    b.plan_prism(box(-WIDTH/2,.03,WIDTH/2,3.21),4.30,4.50,'light plaster','South veranda/soffit and upper floor')
    f=Facade(b,(-13.29,-.015),(13.29,-.015),'South upper gallery')
    for j,(a,e) in enumerate(zip(posts,posts[1:])):
        x=(a+e)/2;w=e-a
        fret(f,x,4.54,w-.16,.71,lod,'low gallery railing')
        f.box(x,5.35,w,.18,.19,.03,RED,'sash sill beam')
        for n in range(3):
            u=a+w*(n+.5)/3;glass(f,u,5.48,w/3-.098,1.69,2,2 if lod else 3,lod,'balcony lights')
            glass(f,u,7.25,w/3-.10,.46,2,1,lod,'toplight')
        f.box(x,7.19,w,.105,.21,.042,RED,'transom lintel')
        f.box(x,7.80,w,.16,.23,.04,DARK,'eaves beam')
        if j in (2,3,4):
            f.box(x,8.14,w,.52,.16,-.095,YELLOW,'high plaster frieze')
            for v in (a+.09,x,e-.09):f.box(v,8.16,.085,.57,.19,.03,RED,'frieze uprights')
    for x in posts:f.box(x,6.21,.145,3.59,.20,.05,RED,'gallery uprights')
    for side in (-1,1):
        # Cream end panels bound the red window gallery.
        x=side*13.11
        strip(b,(x,1.56,4.18),(.25,3.07,7.86),YELLOW,'South veranda/end wall')
    strip(b,(0,3.23,6.1),(26.47,.16,3.28),'shadowed opening','Upper gallery/back wall')
    # The uncovered section of the old floor is below the visible roof.
    strip(b,(0,(BACK+3.36)/2,3.93),(26.55,BACK-3.36,7.86),'neutral section','Rear section/supported roof')

def raised_roof(b,x0,x1,y0,y1,z,rise,flare,lod,label):
    """Hipped iron skin, slender folds and rising tips at four convex corners."""
    center=((x0+x1)/2,(y0+y1)/2);hx=(x1-x0)/2;hy=(y1-y0)/2
    dx=max(0.12,hx-hy*.78);dy=max(.095,hy-hx*.78)
    corners=np.array([(x0,y0),(x1,y0),(x1,y1),(x0,y1)])
    top=np.array([(-dx,-dy),(dx,-dy),(dx,dy),(-dx,dy)])+center
    def surface(side,s,t):
        a=corners[side]*(1-s)+corners[(side+1)%4]*s
        c=top[side]*(1-s)+top[(side+1)%4]*s
        xy=(1-t)*a+t*c
        return [*xy,z+rise*t**.84+flare*abs(2*s-1)**4*(1-t)**2]
    for side in range(4):
        n=6 if lod else 16;depth=3 if lod else 5
        pts=[surface(side,i/n,j/depth) for j in range(depth+1) for i in range(n+1)]
        ids=[(j*(n+1)+i,j*(n+1)+i+1,(j+1)*(n+1)+i+1,(j+1)*(n+1)+i)for j in range(depth)for i in range(n)]
        b.add(pts,ids,IRON,label+'/folded iron hip')
        lip=np.array([surface(side,i/n,0)for i in range(n+1)])
        lower=lip.copy();lower[:,2]-=.125
        b.add(np.concatenate([lower,lip]),[(i,i+1,n+2+i,n+1+i)for i in range(n)],RED,label+'/painted fascia')
        b.tube(lip,.055,IRON,sides=6,label=label+'/black eave lip')
        for i in range(1,n,2 if lod else 1):
            curve=np.array([surface(side,i/n,t)for t in np.linspace(.025,.98,depth+1)]);curve[:,2]+=.018
            b.tube(curve,.018,'folded iron seams',sides=4 if lod else 6,label=label+'/standing folded seams')
        b.tube([surface(side,0,t)for t in np.linspace(0,1,depth+1)],.067,IRON,sides=8,label=label+'/hip ridge')
        tip=np.array(surface(side,0,0));a=corners[side]-center;a/=np.linalg.norm(a)
        mid=tip+[a[0]*.16,a[1]*.16,.16*flare];peak=mid+[a[0]*.14,a[1]*.14,.32*flare]
        b.tube([tip,mid,peak],.046,'ridge terminals',sides=7,label=label+'/upturned corner')
    b.add([[x,y,z+rise]for x,y in top],[(0,1,2,3)],IRON,label+'/summit')

def canopy(b,lod):
    cx=9.12;half=2.84;y0=-5.66;y1=.32
    for x in [cx-half+.30,cx+half-.30]:
        for y in [y0+.36,y1-.40]:porch_column(b,x,y,.08,3.86,.145,lod,'Carriage porch')
        strip(b,(x,(y0+y1)/2,3.78),(.23,y1-y0,.26),DARK,'Carriage porch/side architraves')
    n=10 if lod else 20;pt=[];faces=[]
    for y in [y0-.16,y1+.09]:
        for i in range(n+1):
            t=i/n;pt.append((cx+(2*t-1)*half,y,3.93+.74*(max(0.,1-(2*t-1)**2))**.58))
    b.add(pt,[(i,i+1,n+i+2,n+i+1)for i in range(n)],IRON,'Carriage porch/barrel iron cover')
    for i in range(1,n,2 if lod else 1):
        b.tube([pt[i],pt[n+i+1]],.023,'folded iron seams',sides=4,label='Carriage porch/roof folds')
    for y in [y0-.16,y1+.09]:
        cure=[(x,y,z)for x,_,z in pt[:n+1]]
        b.tube(cure,.077,IRON,sides=7,label='Carriage porch/curved front rim')
    # Pierced brackets span the heads of the two open carriage entrances.
    side=Facade(b,(cx-half+.28,y0+.32),(cx+half-.28,y0+.32),'Carriage porch fascia')
    side.box(0,3.57,side.length,.21,.14,0,DARK,'crossbeam')
    for sign in (-1,1):
        for s in np.linspace(.10,1.01,5 if lod else 10):
            u=sign*(side.length/2-s)
            side.line((u,3.55,.05),(u,3.11+.42*s,.05),.027,'iron bracket',6,'scalloped open bracket')
    for x in [cx-half+.3,cx+half-.3]:
        side=Facade(b,(x,y0+.32),(x,y0+1.56),'Carriage porch guard')
        fret(side,0,.20,1.14,.82,lod,'short end screen')

def tower(b,lod):
    cx=-.79;cy=6.05;wx=3.00;wy=2.62;z=9.06
    for a,e in zip([(-wx/2,-wy/2),(wx/2,-wy/2),(wx/2,wy/2),(-wx/2,wy/2)],[(wx/2,-wy/2),(wx/2,wy/2),(-wx/2,wy/2),(-wx/2,-wy/2)]):
        face=Facade(b,(cx+a[0],cy+a[1]),(cx+e[0],cy+e[1]),'Glazed lookout')
        holes=[]
        for j in range(3):
            u=face.length*(j-1)/3
            holes.append(glass(face,u,z+.28,face.length/3-.12,1.24,2 if not lod else 1,3,lod,'red lookout lights'))
        face.wall(z,z+1.67,holes,.17,RED)
    raised_roof(b,cx-2.19,cx+2.19,cy-1.82,cy+1.82,z+1.74,.76,.65,lod,'Lookout roof')
    for x,y,h in [(-8.75,6.80,10.18),(4.25,7.36,11.20),(10.52,5.84,10.32)]:
        strip(b,(x,y,(h+8.1)/2),(.57,.64,h-8.1),'light plaster','White stacks/brick shaft')
        for k,(w,deep) in enumerate([(.65,.72),(.78,.85),(.68,.75)]):
            strip(b,(x,y,h+.10*k),(w,deep,.105),'light plaster','White stacks/corbels')

def building(b,lod):
    front(b,lod)
    canopy(b,lod)
    # The upper roof is cut behind the photographed lookout. The north rooms remain native to the city.
    raised_roof(b,-13.64,-6.47,-.46,9.62,7.86,1.42,.40,lod,'West wing roof')
    raised_roof(b,3.17,13.64,-.46,9.62,7.86,1.42,.40,lod,'East wing roof')
    raised_roof(b,-7.10,3.72,-.57,9.62,8.49,1.24,.97,lod,'Central swept pavilion')
    tower(b,lod)
