"""The broad and narrow garden arches of Residence A, Dongping Road."""
import math
import sys
from pathlib import Path
from shapely.geometry import box, Polygon, LineString
from shapely.ops import unary_union

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[3]/'source/precise/hongkou-general-post-office/source/common'))
from photo_architecture import Facade, opening

WALL,STONE,TOP,FRAME,GLASS,ROOF,EDGE,SHADE,PIPE=(
 'pebbled grey render','dressed grey stone','weathered coping','dark timber sash',
 'cool window glass','muted clay tile','dark timber eaves','sheltered render','aged rainwater pipe')
PALETTE={k:dict(color=list(c),roughness=r,metallic=m)for k,c,r,m in [
 (WALL,(.556,.535,.478),.95,0),(STONE,(.713,.705,.651),.85,0),(TOP,(.615,.602,.554),.83,0),
 (FRAME,(.117,.122,.109),.61,0),(GLASS,(.248,.322,.348),.29,.17),(ROOF,(.459,.396,.346),.88,0),
 (EDGE,(.231,.169,.139),.91,0),(SHADE,(.478,.462,.418),.93,0),(PIPE,(.251,.259,.246),.69,.22),('amber fanlight',(.61,.423,.126),.35,.08)]}
WEST,SMALL,BIG,EAST=-11.74,-5.40,1.48,11.74
EAVE,DECK=8.65,4.52

def strip(f,u,z,w,h,back,front,mat,label):
    f.box(u,z,w,h,front-back,(front+back)/2,mat,label)

def ashlar_arch(f,u,z,w,h,rise,lod):
    spring=z+h-rise
    count=max(3,round((spring-z)/.44))
    step=(spring-z)/count
    thick=.33 if w>4 else .26
    for j in range(count):
        for side in (-1,1):
            strip(f,u+side*(w+thick)/2,z+(j+.5)*step,thick,step-.016,-.015,.12+.024*(j%2),STONE,'jamb courses')
    stones=17 if w>5 else 11
    for j in range(stones):
        lo,hi=math.pi*j/stones+.005, math.pi*(j+1)/stones-.005
        n=1 if lod else 3
        t=[lo+(hi-lo)*k/n for k in range(n+1)]
        add=thick+(.05 if j==stones//2 else 0)
        points=[(u+(w/2+add)*math.cos(a),spring+(rise+add)*math.sin(a))for a in t]
        points.extend((u+w/2*math.cos(a),spring+rise*math.sin(a))for a in reversed(t))
        f.prism(Polygon(points),-.012,.18 if j==stones//2 else .14,STONE,'separate wedge stones')

def glazing(f,u,z,w,h,lod,arch=0,cols=2,amber=False):
    shape=opening(u,z,w,h,arch,16 if lod else 30)
    f.prism(shape,-.14,-.105,GLASS,'recessed glazing')
    bars=[box(u-w/2+j*w/cols-.028,z,u-w/2+j*w/cols+.028,z+h)for j in range(1,cols)]
    levels=[.48] if lod else [.33,.66]
    if arch:
        spring=z+h-arch
        if amber:
            transom=shape.intersection(box(u-w/2,spring,u+w/2,z+h+.02))
            f.prism(transom,-.103,-.094,'amber fanlight','amber semicircular transom')
        levels=[.43,(spring-z)/h]
        for a in (-.67,0,.67):
            bars.append(LineString([(u,spring),(u+a*w/2,spring+arch*math.sqrt(1-a*a))]).buffer(.024,cap_style=2))
    for t in levels:
        bars.append(box(u-w/2,z+t*h-.027,u+w/2,z+t*h+.027))
    frame=shape.difference(shape.buffer(-.066,join_style=2).difference(unary_union(bars)))
    f.prism(frame,-.087,-.016,FRAME,'timber glazing bars')
    return shape

def run_balusters(f,left,right,z,d,lod):
    """Turned profiles remain open around the shaft and between each pair."""
    strip(f,(left+right)/2,z+.125,right-left,.25,d-.17,d+.17,TOP,'stone railing sill')
    strip(f,(left+right)/2,z+1.135,right-left,.17,d-.17,d+.17,STONE,'handrail')
    n=max(1,round((right-left)/.40))
    for j in range(n):
        u=left+(j+.5)*(right-left)/n
        x,y,_=f.point(u,z,d)
        profile=[(.245,.103),(.30,.108),(.39,.069),(.52,.099),(.63,.119),(.73,.113),(.88,.060),(1.00,.080),(1.055,.106)]
        use=[profile[k]for k in (0,2,4,6,8)]if lod else profile
        f.builder.lathe((x,y),[(z+h,r)for h,r in use],STONE,7 if lod else 12,f.label+'/turned balusters')

def balustrade(f,width,lod,project):
    z=DECK+.05
    if not project:
        run_balusters(f,-width/2,width/2,z,0,lod)
        return
    middle=width*.21
    shelf=.62
    footprint=Polygon([f.point(u,z,d)[:2]for u,d in [(-middle,0),(-middle,shelf+.17),(middle,shelf+.17),(middle,0)]])
    f.builder.plan_prism(footprint,z-.20,z+.08,TOP,f.label+'/central projecting balcony')
    for sign in (-1,1):
        u=sign*middle
        a=f.point(u,z,0);b=f.point(u,z,shelf)
        ret=Facade(f.builder,a[:2],b[:2],f.label+'/balustrade return')
        run_balusters(ret,-ret.length/2,ret.length/2,z,0,lod)
        strip(f,u,z+.56,.27,1.12,shelf-.18,shelf+.18,STONE,'square newel')
        strip(f,sign*.72*middle,z-.16,.34,.26,-.02,.51,STONE,'stone console')
    strip(f,0,z-.16,.33,.26,-.03,.51,STONE,'middle balcony console')
    for a,b,d in [(-width/2,-middle,0),(-middle,middle,shelf),(middle,width/2,0)]:
        run_balusters(f,a,b,z,d,lod)

def porch(f,width,lod,side=False,project=False):
    w=f.length
    rise=1.54 if width>5 else 1.00
    lower=opening(0,.34,width,3.63,rise,18 if lod else 38)
    top_h=3.45 if side else 3.62
    top_rise=1.06 if side else .18
    top=opening(0,DECK+.07,w-1.24,top_h,top_rise,18 if lod else 34)
    f.wall(.22,EAVE,[lower,top],.38,WALL)
    ashlar_arch(f,0,.34,width,3.63,rise,lod)
    if side: ashlar_arch(f,0,DECK+.07,w-1.24,top_h,top_rise,lod)
    for end in (-1,1):
        for j in range(8):
            strip(f,end*(w/2-.31),DECK+.35+j*.475,.47 if j%2 else .61,.457,-.015,.069,STONE,'rusticated pier')
    # The quoins run down to the plinth on the garden and east return.
    for end in (-1,1):
        for j in range(8):
            strip(f,end*(w/2-.22),.56+j*.46,.36 if j%2 else .49,.44,-.015,.058,STONE,'lower corner quoins')
    for z,h,d in [(DECK-.28,.13,.12),(DECK-.12,.105,.19),(EAVE-.16,.17,.16)]:
        strip(f,0,z,w,h,-.02,d,TOP,'continuous stone band')
    balustrade(f,w-1.18,lod,project)

def shelter_back(f,lod):
    w=f.length
    holes=[]
    for u,sz,ht,arc in [(-w*.31,w*.24,2.72,0),(0,w*.24,2.75,0),(w*.32,w*.25,3.15,.68)]:
        holes.append(glazing(f,u,.36,sz,ht,lod,arc,amber=bool(arc)))
    for u in (-w*.29,0,w*.29):
        holes.append(glazing(f,u,4.94,w*.22,2.4,lod))
    f.wall(.18,EAVE,holes,.32,SHADE)

def hip(b,x0,x1,y0,y1,z,h,name,lod,cut=False):
    w=x1-x0;d=y1-y0;cx=(x0+x1)/2;cy=(y0+y1)/2
    rim=[(x0,y0,z),(x1,y0,z),(x1,y1,z),(x0,y1,z)]
    if d>=w:
        a=(cx,y0+w*.42,h);c=(cx,y1 if cut else y1-w*.42,h)
        faces=[[rim[0],rim[1],a],[rim[1],rim[2],c,a],[rim[3],rim[0],a,c]]
        if not cut:faces.append([rim[2],rim[3],c])
        joints=(a,a,c,c)
    else:
        a=(x0+d*.41,cy,h);c=(x1-d*.41,cy,h)
        faces=[[rim[0],rim[1],c,a],[rim[1],rim[2],c],[rim[2],rim[3],a,c],[rim[3],rim[0],a]]
        joints=(a,c,c,a)
    for face in faces:b.add(face,[tuple(range(len(face)))],ROOF,name+'/pitched tiles')
    if cut:b.add([rim[2],rim[3],c],[(0,1,2)],SHADE,name+'/roof section')
    b.plan_prism(box(x0,y0,x1,y1),z-.18,z,EDGE,name+'/eaves')
    b.tube([a,c],.073,ROOF,5 if lod else 9,name+'/ridge')
    for j,pt in enumerate(rim):
        if not cut or j<2:b.tube([pt,joints[j]],.054,ROOF,5 if lod else 8,name+'/hip capping')

def add_ailu(b,lod):
    large=Facade(b,(BIG,0),(EAST,0),'great garden loggia')
    east=Facade(b,(EAST,0),(EAST,4.33),'narrow return arches')
    small=Facade(b,(SMALL,2.62),(BIG,2.62),'secondary garden loggia')
    west=Facade(b,(WEST,3.15),(SMALL,3.15),'west room')
    porch(large,8.12,lod,project=True)
    porch(east,2.65,lod,side=True)
    porch(small,4.88,lod)
    for name,x0,x1,y0,y1 in [('great',BIG,EAST,0,4.33),('small',SMALL,BIG,2.62,5.53)]:
        for z,t,mat in [(.15,.18,TOP),(DECK-.17,.25,TOP),(EAVE-.22,.18,SHADE)]:
            b.plan_prism(box(x0,y0,x1,y1+.08),z,z+t,mat,name+' portico/slab')
        shelter_back(Facade(b,(x0,y1),(x1,y1),name+' shaded sashes'),lod)
    ret=Facade(b,(BIG,2.62),(BIG,0),'inner return')
    ret.wall(.22,EAVE,[opening(0,.34,1.63,3.63,.82),opening(0,DECK+.07,1.63,3.54,.38)],.31,SHADE)
    holes=[glazing(west,-.74,.55,1.77,2.54,lod),glazing(west,-.67,4.96,2.04,2.42,lod)]
    west.wall(.17,7.74,holes,.32,WALL)
    # A narrow pitched tile awning separates the two western window tiers.
    x0,x1=WEST+.35,SMALL-.43
    yz=[(1.99,3.11),(3.14,4.05)]
    awning=[(x0,*yz[0]),(x1,*yz[0]),(x1,*yz[1]),(x0,*yz[1])]
    b.add(awning,[(0,1,2,3)],ROOF,'west window bay/lean-to canopy')
    b.tube([awning[0],awning[1]],.075,EDGE,6,'west window bay/awning eave')
    for j in range(1,14 if lod else 23):
        x=x0+(x1-x0)*j/(14 if lod else 23)
        b.tube([(x,y,z+.015)for y,z in yz],.027,ROOF,5,'west window bay/pantile channels')
    hip(b,WEST-.28,SMALL+.14,2.88,7.16,7.73,9.26,'west window bay',lod)
    hip(b,SMALL-.15,BIG+.21,2.22,8.40,EAVE+.08,10.47,'small loggia roof',lod)
    f=Facade(b,(SMALL+.78,2.63),(BIG-.84,2.63),'west dormer')
    outline=Polygon([(-1.4,EAVE+.15),(1.4,EAVE+.15),(0,EAVE+2.19)])
    hole=glazing(f,0,EAVE+.29,1.28,.88,lod)
    f.wall(EAVE+.15,EAVE+2.19,[hole],.21,WALL,outline)
    for k in (-1,1):
        b.tube([f.point(0,EAVE+2.21,.1),f.point(k*1.46,EAVE+.12,.1)],.11,EDGE,5 if lod else 8,'west dormer/bargeboards')
    hip(b,BIG-.43,EAST+.49,-.54,11.48,EAVE+.08,11.13,'main hip',lod,cut=True)
    side=Facade(b,(EAST,4.33),(EAST,11.1),'east return wall')
    holes=[glazing(side,u,z,w,h,lod)for u,z,w,h in [(-1.7,.64,.89,2.16),(-1.7,5.12,1.08,2.28),(2.37,5.36,.83,1.77)]]
    # The oblique source shows a small recessed ground-floor arch beyond the downpipe.
    door=opening(2.10,.22,1.35,2.55,.73,14 if lod else 28)
    holes.append(door)
    side.prism(door,-.62,-.59,SHADE,'east recess backing')
    side.wall(.18,EAVE,holes,.31,WALL)
    b.plan_prism(box(BIG,4.33,EAST,11.10),.06,.23,TOP,'partial east pavilion/plinth')
    for y in (6.08,10.13):
        for z,w,d,h,mat in [(9.79,.61,.76,2.54,STONE),(10.76,.71,.89,.14,TOP),(11.07,.77,.93,.17,STONE)]:
            b.box((EAST-1.82,y,z),(w,d,h),mat,label='east roof/stack and cap')
    b.tube([(EAST+.14,4.29,.36),(EAST+.14,4.29,EAVE-.35),(EAST+.19,4.0,EAVE+.03)],.085,PIPE,6 if lod else 10,'east return/downpipe')
