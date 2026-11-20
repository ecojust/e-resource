"""The seven-bay eastern office front built for Lieu-Ong-Kee on Middle Sichuan Road."""
from math import pi,cos,sin
from pathlib import Path
from shapely.geometry import box,Polygon,LineString
from shapely.ops import unary_union
from photo_architecture import Facade
from sign_lettering import add_facade_lettering

BRICK="golden brown facing brick"
UMBER="umber fired brick"
HONEY="ochre fired brick"
DARK="weathered mortar"
STONE="buff washed stone"
METAL="dark patinated metal"
GLASS="smoke green glass"
SASH="painted steel"
GOLD="gilded office name"
ROOF="flat roof membrane"
PALETTE={
 BRICK:dict(color=[.405,.246,.135],roughness=.88),UMBER:dict(color=[.312,.178,.091],roughness=.90),
 HONEY:dict(color=[.480,.299,.164],roughness=.87),DARK:dict(color=[.283,.194,.129],roughness=.9),
 STONE:dict(color=[.577,.499,.386],roughness=.84),METAL:dict(color=[.121,.142,.126],metallic=.45,roughness=.59),
 GLASS:dict(color=[.127,.156,.153],metallic=.17,roughness=.29),SASH:dict(color=[.205,.206,.176],metallic=.29,roughness=.54),
 GOLD:dict(color=[.696,.493,.196],metallic=.49,roughness=.48),ROOF:dict(color=[.392,.376,.324],roughness=.88)}
PITCH=5.36
HALF=18.76
WALLTOP=30.55
LEVELS=[8.42+3.58*n for n in range(6)]
FONT=Path(__file__).with_name("fonts")/"SichuanRoadPlaque.otf"
# Major front tower rises in five contiguous steps. Geometry below remains a single exterior shell.
CROWN=[(-18.76,30.62),(-18.76,31.02),(-16.09,31.02),(-16.09,31.52),(-14.11,31.52),
       (-14.11,30.70),(-8.31,30.70),(-8.31,31.63),(-7.72,31.63),(-7.72,30.83),
       (-3.49,30.83),(-3.49,32.95),(-2.89,32.95),(-2.89,33.64),(-2.17,33.64),
       (-2.17,34.23),(-1.43,34.23),(-1.43,34.87),(-.56,34.87),(-.56,35.28),
       (.56,35.28),(.56,34.87),(1.43,34.87),(1.43,34.23),(2.17,34.23),(2.17,33.64),
       (2.89,33.64),(2.89,32.95),(3.49,32.95),(3.49,30.83),(7.72,30.83),(7.72,31.63),
       (8.31,31.63),(8.31,30.70),(14.11,30.70),(14.11,31.52),(16.09,31.52),
       (16.09,31.02),(18.76,31.02),(18.76,30.62)]


def glazing(f,openings,depth):
    if not openings:return
    frames=[]
    for poly,columns,transoms in openings:
        l,b,r,t=poly.bounds;parts=[poly.difference(poly.buffer(-.062,join_style="mitre"))]
        for n in range(1,columns):
            x=l+(r-l)*n/columns;parts.append(box(x-.029,b,x+.029,t))
        for frac in transoms:
            y=b+(t-b)*frac;parts.append(box(l,y-.031,r,y+.031))
        frames.append(poly.intersection(unary_union(parts)))
    f.prism(unary_union([p.buffer(.01,join_style="mitre") for p,_,_ in openings]),-depth-.03,-depth,GLASS,"inset glazing")
    f.prism(unary_union(frames),-depth+.012,-depth+.056,SASH,"steel frames")


def arch(x,w,z,spring,rise):
    return Polygon([(x-w/2,z),(x+w/2,z),(x+w/2,spring)]+[
        (x+w/2*cos(t*pi/24),spring+rise*sin(t*pi/24)) for t in range(1,25)])


def spandrel(f,x,z,width,low):
    f.box(x,z,width,.89,.12,.125,METAL,"dark metal spandrel")
    zigs=[]
    for k in range(2 if low else 3):
        line=[(x-width*.42+i*width*.105,z-.23+k*.18+(.13 if i%2 else 0)) for i in range(9)]
        zigs.append(LineString(line).buffer(.030,cap_style="flat",join_style="mitre"))
    f.prism(unary_union(zigs),.188,.231,STONE,"chevron relief")


def courses(f,x,width,z0,z1,low,index):
    # Horizontal bedding and staggered vertical joints are actual shallow relief.
    # The LOD keeps the principal pilaster and terminal strips of the brickwork.
    f.box(x,(z0+z1)/2,width,z1-z0,.29,.12,DARK,"continuous engaged pier")
    divisions=1 if low else 3
    dz=.61 if low else .34
    pieces={k:[] for k in [BRICK,UMBER,HONEY]}
    for k in range(int((z1-z0)/dz)+1):
        b=z0+dz*k+.012;t=min(z1,b+dz-.032)
        if t<=b:continue
        step=width/divisions;l=x-width/2
        joints=[l,l+width]
        joints.extend(l+(i+.5*(k%2))*step for i in range(divisions+1) if l<l+(i+.5*(k%2))*step<l+width)
        joints=sorted(set(joints))
        for i,(left,right) in enumerate(zip(joints,joints[1:])):
            if right-left<=.025:continue
            c=(k*17+i*13+index*23)%19;mat=HONEY if c in [3,12] else UMBER if c in [1,7,14] else BRICK
            pieces[mat].append(box(left+.013,b,right-.013,t))
    for mat,tiles in pieces.items():
        if tiles:f.prism(unary_union(tiles),.267,.294,mat,"bonded brown brick steps")
    f.box(x-width*.41,(z0+z1)/2,.085,z1-z0,.11,.276,BRICK,"prismatic pier arris")
    f.box(x+width*.41,(z0+z1)/2,.085,z1-z0,.11,.276,BRICK,"prismatic pier arris")


def street(builder,low):
    f=Facade(builder,(-HALF,0),(HALF,0),"Middle Sichuan Road")
    windows=[];large=[];doors=[];cut=[];sills=[]
    for bay in range(-3,4):
        x=bay*PITCH
        for z in LEVELS:
            for offset in [-1.22,0,1.22]:
                u=x+offset;op=box(u-.447,z+.11,u+.447,z+2.41);cut.append(op);windows.append((op,1,[.68]))
                sills.append(box(u-.475,z-.056,u+.475,z+.052))
            spandrel(f,x,z-.48,3.38,low)
        if bay:
            op=arch(x,3.54,.29,6.66,.79);cut.append(op);large.append((op,3,[.39,.52,.78]))
            f.box(x,3.53,3.56,.82,.15,.094,METAL,"metal band across double-height hall")
        else:
            portal=box(-1.47,.12,1.47,3.08);cut.append(portal);doors.append((portal,2,[.77]))
            transom=box(-1.65,5.02,1.65,7.22);cut.append(transom);large.append((transom,3,[.69]))
            for u in [-1.71,1.71]:
                f.box(u,1.77,.40,3.54,.53,.098,STONE,"paired entrance jamb")
                f.box(u,.23,.52,.46,.59,.103,STONE,"entrance plinth")
            f.box(0,3.62,3.96,.28,.69,.13,STONE,"portal lintel")
            f.box(0,4.24,4.28,.88,.22,.137,METAL,"contemporary entrance nameboard")
            add_facade_lettering(f,"创业大楼",0,4.27,3.34,.56,.251,.308,GOLD,label="observed plaque",font=FONT)
            f.box(0,.054,3.23,.108,.73,.068,STONE,"front threshold")
    outline=Polygon([(-HALF,0),(HALF,0)]+list(reversed(CROWN)))
    f.prism(outline.difference(unary_union(cut)),-.34,.0,BRICK,"seven-bay continuous exterior")
    f.prism(unary_union(sills),.004,.106,STONE,"sill courses")
    for i,x in enumerate([-18.29,-13.40,-8.04,-2.68,2.68,8.04,13.40,18.29]):
        courses(f,x,.64 if abs(x)>15 else .84,.2,32.90 if abs(x)<3 else 31.41 if abs(x)==8.04 else 30.59,low,i)
    # Closely spaced reeds on the crown make its raised, stepped centre visible from the street.
    for u,h in [(-2.24,33.31),(-1.52,33.86),(-.79,34.53),(0,35.21),(.79,34.53),(1.52,33.86),(2.24,33.31)]:
        f.box(u,(30.44+h)/2,.23,h-30.44,.21,.098,STONE,"central stepped parapet reed")
    crown_coping=[]
    for (u,z),(v,t) in zip(CROWN,CROWN[1:]):
        if v>u and abs(z-t)<.001:crown_coping.append(box(u,z-.13,v,z+.02))
    f.prism(unary_union(crown_coping),-.21,.137,STONE,"washed-stone parapet cap")
    glazing(f,windows,.395);glazing(f,large,.44);glazing(f,doors,.84)
    return f


def end_wall(builder,a,b,rooms,low,label):
    f=Facade(builder,a,b,label);holes=[];opening=[]
    for i in range(rooms):
        u=(i+.5-rooms/2)*f.length/rooms
        for z in LEVELS:
            shape=box(u-.66,z+.10,u+.66,z+2.27)
            holes.append(shape);opening.append((shape,2,[.68]))
    wall=box(-f.length/2,0,f.length/2,WALLTOP-.13)
    f.prism(wall.difference(unary_union(holes)),-.23,0,BRICK,"return brick wall")
    glazing(f,opening,.27)
    if holes:
        ledges=[box(o.bounds[0]-.05,o.bounds[1]-.101,o.bounds[2]+.05,o.bounds[1]-.012) for o in holes]
        f.prism(unary_union(ledges),.002,.093,UMBER,"brown-brick return sills")
        for k in range(1,rooms):
            u=(k-rooms/2)*f.length/rooms
            courses(f,u,.46,1.04,WALLTOP-.24,low,k)
    f.beam(WALLTOP-.17,.16,.126,STONE,label="side coping")


def make_enterprise(builder,low=False):
    street(builder,low)
    # The southern side jog begins beyond the exposed return. Shape is the frozen property boundary
    # inset by about 20cm. The north return is a narrow side lane, not the adjacent rental building.
    ring=[(-18.76,.0),(18.76,.0),(18.91,26.18),(-22.56,25.51),(-23.34,10.02),(-18.57,9.92)]
    builder.plan_prism(Polygon(ring),0,.13,STONE,"entry and retained office floor")
    for i,(a,b) in enumerate(zip(ring,ring[1:]+ring[:1])):
        if i==0:continue
        count=3 if i==5 else 1 if i==4 else 2 if i==1 else 0
        end_wall(builder,a,b,count,low,["","North lane","West return","South rear wall","Southern setback","Exposed south return"][i])
    builder.plan_prism(Polygon(ring),WALLTOP-.28,WALLTOP-.15,ROOF,"flat upper roof")
    for a,b in zip(CROWN,CROWN[1:]):
        x,z=a;X,Z=b
        if X<=x or z<=30.75:continue
        # The central crown backs onto a short projection, not an inferred extra office floor.
        depth=2.89 if abs(x+X)<7 else .68
        builder.plan_prism(box(x,.29,X,depth),30.40,z-.05,BRICK,"stepped parapet backing")
    # One long shallow raised roof zone is visible in all releases; the neighboring tower obstructs much of the rest.
    builder.plan_prism(box(-16.9,13.8,15.82,18.84),30.39,31.60,BRICK,"estimated rear roof service zone")
    builder.plan_prism(box(-17.0,13.70,15.92,18.94),31.60,31.74,ROOF,"service roof coping")
