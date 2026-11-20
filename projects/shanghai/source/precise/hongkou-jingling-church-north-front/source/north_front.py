"""Model the triple north gable and the 2025 restored leaded window at 135 Kunshan Road."""
from math import atan2, ceil, cos, pi, sin
from shapely.affinity import rotate, scale, translate
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union
from photo_architecture import Facade

BRICK='red fair-faced brick'
JOINT='recessed bed joint'
ARCH='red arch courses'
STONE='warm grey granite'
PALE='pale concrete coping'
WOOD='dark walnut frames'
LEAD='leaded came'
BLUE='indigo architectural glass'
AQUA='blue green glass'
CYAN='pale blue glass'
GOLD='honey glass'
RUBY='muted ruby glass'
ROOF='grey roof tile'
METAL='aged rainwater iron'
SHADE='shadow in recess'
PALETTE={}
for name,rgb,rough in [
    (BRICK,(.565,.305,.226),.88),(JOINT,(.441,.312,.248),.9),
    (ARCH,(.41,.21,.165),.89),(STONE,(.526,.492,.423),.86),
    (PALE,(.703,.677,.602),.88),(WOOD,(.246,.160,.139),.74),
    (LEAD,(.14,.139,.153),.59),(BLUE,(.17,.215,.34),.38),
    (AQUA,(.204,.332,.365),.39),(CYAN,(.338,.445,.479),.40),
    (GOLD,(.523,.408,.243),.40),(RUBY,(.402,.224,.238),.42),
    (ROOF,(.329,.316,.305),.92),(METAL,(.214,.200,.169),.66),
    (SHADE,(.115,.106,.106),.81)]:
    PALETTE[name]=dict(color=list(rgb),roughness=rough)
WIDTH=25.40
SILL=7.72
MAIN_TOP=SILL+10.56
MAIN_WIDTH=5.44
SPRING=14.72
GABLE=[(-WIDTH/2,15.52),(-9.64,18.10),(-7.15,15.84),(0,23.48),
       (7.15,15.84),(9.64,18.10),(WIDTH/2,15.52)]
DEPTH=1.18


def disc(x,z,r,res=24):
    return Point(x,z).buffer(r,quad_segs=res)


def pointed(x,z0,w,top,rise,seg=32):
    r=w/2
    spring=top-rise
    offset=(rise*rise-r*r)/(2*r)
    radius=offset+r
    angle=atan2(rise,offset)
    right=[(x-offset+radius*cos(angle*i/seg),spring+radius*sin(angle*i/seg)) for i in range(seg+1)]
    left=[(2*x-a,b)for a,b in reversed(right[0:seg])]
    return Polygon([(x-r,z0),(x+r,z0),*right,*left])


def low_arch(x,z0,w,top,rise,seg=30):
    r=w/2
    # A low, flattened center head is visible over the double door.
    curve=[(x+r*cos(pi*i/seg),top-rise+rise*sin(pi*i/seg)) for i in range(seg+1)]
    return Polygon([(x-r,z0),(x+r,z0),*curve])


def strip(points,width):
    return LineString(points).buffer(width/2,cap_style=2,join_style=2)


def glazed(f,opening,label,rows=2,mat=BLUE):
    x0,z0,x1,z1=opening.bounds
    f.prism(opening.buffer(.012),-.285,-.255,mat,label+' glazing')
    rails=[box(x0,z0+(z1-z0)*i/rows-.028,x1,z0+(z1-z0)*i/rows+.028)for i in range(1,rows)]
    inner=opening.buffer(-.075)
    frame=opening.difference(inner)
    if rails:frame=frame.union(inner.intersection(unary_union(rails)))
    f.prism(frame,-.17,-.092,WOOD,label+' sash')


def arch_rim(f,shape,spring,label):
    outline=LineString(list(shape.exterior.coords)[2:-1])
    upper=box(-WIDTH,spring-.015,WIDTH,28)
    core=strip(outline.coords,.29).intersection(upper)
    f.prism(core,.03,.095,ARCH,label+' brick arch')
    rim=shape.buffer(.29,join_style=2).difference(shape.buffer(.155,join_style=2)).intersection(upper)
    f.prism(rim,.015,.16,PALE,label+' pale archivolt')
    for u in [shape.bounds[0]-.215,shape.bounds[2]+.215]:
        f.box(u,spring-.028,.295,.125,.23,.087,STONE,label+' hood stop')


def rose(f,lod):
    x,z,r=0,16.54,1.13
    n=16 if lod else 28
    f.prism(disc(x,z,r+.117,n),-.19,-.14,WOOD,'rose timber perimeter')
    f.prism(disc(x,z,r,n),-.134,-.127,BLUE,'rose blue backing')
    for i in range(12):
        angle=(i+.5)*30
        # The twelve radial scallops and their nested colored roundels are legible in the installation photograph.
        petal=disc(0,.738,.275,n).union(Polygon([(-.235,.66),(-.105,.18),(.105,.18),(.235,.66)]))
        shape=translate(rotate(petal,angle,origin=(0,0)),xoff=x,yoff=z)
        f.prism(shape,-.123,-.114,LEAD,'rose lead petals')
        f.prism(shape.buffer(-.035),-.110,-.103,GOLD,'rose amber petals')
        cx=x-.813*sin(angle*pi/180);cz=z+.813*cos(angle*pi/180)
        f.prism(disc(cx,cz,.133,n),-.098,-.09,RUBY,'rose red roundel surrounds')
        f.prism(disc(cx,cz,.089,n),-.087,-.081,CYAN,'rose pale roundels')
        if not lod:
            f.prism(disc(cx,cz,.039,n),-.079,-.071,BLUE,'rose roundel centers')
            sliver=translate(rotate(Polygon([(-.069,.32),(0,.56),(.069,.32),(0,.23)]),angle,origin=(0,0)),xoff=x,yoff=z)
            f.prism(sliver,-.098,-.090,RUBY,'rose tapered ruby inserts')
    for rad,mat,d in [(.195,WOOD,-.066),(.151,GOLD,-.058),(.065,AQUA,-.052)]:
        f.prism(disc(x,z,rad,n),d-.006,d,mat,'rose center '+mat)
    for side in [-1,1]:
        sx=side*1.49;sz=15.81
        for rad,mat,d in [(.209,WOOD,-.148),(.154,CYAN,-.133),(.093,GOLD,-.114),(.044,RUBY,-.100)]:
            f.prism(disc(sx,sz,rad,n),d-.008,d,mat,'paired lateral roundels '+mat)


def glazing_picture(f,opening,lod):
    # The transmitted-light photograph shows blue and cyan water at the foot, pale-gold sky,
    # a robed central figure and shorter ochre figures. Shapes are redrawn directly in model
    # space. Looking from Kunshan Road reverses the interior photograph's left–right order.
    inner=opening.buffer(-.115)
    def piece(points,mat,label,d=-.253):
        shape=Polygon(points).intersection(inner)
        if not shape.is_empty:
            f.prism(shape,d-.012,d-.006,LEAD,'leaded scene outlines')
            inset=shape.buffer(-(.018 if lod else .012),join_style=2)
            if not inset.is_empty:f.prism(inset,d-.004,d,mat,label)
    # Continuous current and cloud bands cross the multiple panes behind the structural sash.
    steps=15 if lod else 31
    def band(z,a,w,phase,mat):
        points=[]
        for i in range(steps):
            x=-2.78+5.56*i/(steps-1)
            y=z+a*sin(x*1.45+phase)+.47*a*sin(x*2.64-phase)
            points.append((x,y))
        top=[(x,y+w*(.75+.25*cos(x*1.2+phase)))for x,y in reversed(points)]
        piece(points+top,mat,'curving sky and water pieces')
    for z,a,w,phase,mat in [(7.94,.18,.18,.55,AQUA),(8.25,.19,.14,2.45,CYAN),
                              (8.56,.23,.25,.18,AQUA),(9.01,.25,.12,2.0,CYAN),
                              (10.18,.26,.11,-.7,AQUA),(11.58,.20,.21,2.5,CYAN),
                              (11.88,.24,.13,.2,GOLD),(12.32,.30,.20,3.6,CYAN),
                              (12.85,.31,.12,.12,GOLD),(13.29,.27,.16,3.2,AQUA),
                              (13.65,.28,.15,1.4,CYAN)]:
        band(z,a,w,phase,mat)
    # Outline and sash cross the same contiguous drawing. No photograph is used as material.
    cx=-.39
    for dx,dz,sz in [(1.03,8.62,.58),(-1.09,8.85,.50)]:
        px=cx+dx
        piece([(px-.40*sz,dz),(px+.47*sz,dz+.05),(px+.29*sz,dz+.73),(px+.03*sz,dz+1.35),(px-.25*sz,dz+.94)],GOLD,'side figure ochre garments',-.234)
        head=disc(px,dz+1.43,.105).intersection(inner)
        f.prism(head,-.245,-.234,GOLD,'side figure head panes')
    robe=[(cx-.54,8.72),(cx-.17,8.48),(cx+.36,8.69),(cx+.23,9.56),(cx+.43,10.21),
          (cx+.31,10.88),(cx-.06,11.11),(cx-.42,10.69),(cx-.29,9.85)]
    piece(robe,RUBY,'central figure red robe',-.229)
    piece([(cx-.37,10.52),(cx-.94,10.92),(cx-1.00,11.27),(cx-.51,11.04),
           (cx-.20,11.27),(cx+.20,11.27),(cx+.77,11.59),(cx+.86,11.46),
           (cx+.42,10.88),(cx+.25,10.47),(cx-.02,10.65)],CYAN,'pale central mantle and raised arm',-.215)
    piece([(cx-.22,10.51),(cx+.02,10.61),(cx+.13,10.11),(cx+.24,9.28),(cx+.26,8.79),
           (cx+.05,8.64),(cx-.09,9.06),(cx-.14,9.60)],CYAN,'pale robe folds',-.212)
    for dx,dz,r,mat,depth in [(0,11.36,.171,GOLD,-.203),(.016,11.36,.110,STONE,-.197)]:
        f.prism(disc(cx+dx,dz,r,10 if lod else 19),depth-.007,depth,mat,'central head and nimbus')
    if not lod:
        for k in range(9):
            a=.20+(pi-.40)*k/8
            start=(cx+.22*cos(a),11.37+.22*sin(a));end=(cx+(1.07+.12*(k%2))*cos(a),11.37+1.26*sin(a))
            f.prism(strip([start,end],.027).intersection(inner),-.260,-.251,GOLD,'fine rays in sky')


def main_light(f,opening,lod):
    f.prism(opening.buffer(.018),-.318,-.285,BLUE,'whole restored lancet glazing')
    xs=[-2.72,-1.91,-1.17,0,1.17,1.91,2.72]
    # The stepped head of each light lies below the large rosette. Keep the central sash continuous through the area of the removed tablet.
    peaks=[15.55,15.65,15.32,15.32,15.65,15.55]
    rails=[]
    glazing_picture(f,opening,lod)
    for i,(a,b)in enumerate(zip(xs,xs[1:])):
        cx=(a+b)/2;peak=peaks[i];rise=.78 if i in (2,3) else .63
        light=pointed(cx,SILL+.13,b-a-.09,peak,rise,16 if lod else 28)
        rails.append(light.difference(light.buffer(-.056,join_style=2)))
        for level in range(1,6):
            zh=SILL+level*1.15
            rails.append(box(a,zh-.037,b,zh+.037))
    # Blue spandrels surround the rose above the paired central lancets.
    for side in [-1,1]:
        panels=[[(.04,17.79),(.04,18.01),(.67,17.54),(.93,17.27),(.62,17.49)],
                [(.10,15.34),(.58,15.03),(1.07,15.60),(.61,15.35)],
                [(1.37,15.47),(1.83,15.56),(1.58,15.14)]]
        for points in panels:
            geom=Polygon([(side*x,z)for x,z in points]).intersection(opening.buffer(-.12))
            if not geom.is_empty:f.prism(geom,-.264,-.253,AQUA,'colored tracery infill')
    for i in [-1,1]:
        conn=strip([(i*.32,17.64),(i*.61,17.53),(i*.93,17.31),(i*1.23,17.03)],.073)
        f.prism(conn.intersection(opening),-.20,-.144,WOOD,'upper rose connections')
    for u in xs[1:-1]:
        limit=15.18 if abs(u)<.01 else (15.82 if abs(u)>1.55 else 16.23)
        rails.append(box(u-.051,SILL,u+.051,limit))
    f.prism(opening.difference(opening.buffer(-.115)).union(unary_union(rails).intersection(opening)), -.212,-.13,WOOD,'six lights and timber transoms')
    rose(f,lod)
    arch_rim(f,opening,SPRING,'main lancet')
    f.box(0,SILL-.067,5.90,.14,.43,.10,STONE,'projecting main sill')


def porch(f,lod):
    # The porched entrance has a shallow arch, three glazed fanlight sections, double leaves and sidelights.
    opening=low_arch(0,1.19,4.00,4.60,.53)
    f.prism(opening.buffer(.014),-.394,-.356,SHADE,'entrance recess')
    frame=opening.difference(opening.buffer(-.135,join_style=2))
    f.prism(frame,-.195,-.105,WOOD,'door outer casing')
    arch=opening.buffer(.19,join_style=2).difference(opening).intersection(box(-2.4,1.18,2.4,4.9))
    f.prism(arch,.007,.125,PALE,'stone door surround')
    fan=opening.buffer(-.146).intersection(box(-2,3.49,2,4.6))
    f.prism(fan,-.314,-.291,AQUA,'stained door fanlight')
    for x in [-.86,.86]:
        f.prism(box(x-.046,3.465,x+.046,4.62).intersection(fan),-.257,-.185,WOOD,'fanlight mullions')
    f.box(0,3.48,3.83,.14,.13,-.187,WOOD,'door head transom')
    for i,(lx,rx)in enumerate([(-1.88,-1.16),(-1.16,0),(0,1.16),(1.16,1.88)]):
        panel=box(lx,1.22,rx,3.41);light=box(lx+.085,2.23,rx-.085,3.28)
        f.prism(panel.difference(light),-.297,-.205,WOOD,'door leaves and sidelights')
        f.prism(light,-.315,-.304,BLUE,'door glass panels')
        for dz in (2.61,2.95):f.box((lx+rx)/2,dz,rx-lx-.11,.036,.035,-.247,WOOD,'door panel grilles')
        if not lod:
            for x in [(lx*2+rx)/3,(lx+rx*2)/3]:f.box(x,2.75,.033,1.04,.035,-.247,WOOD,'door grille uprights')
    width=8.69
    f.box(0,5.23,width+.29,.21,1.23,.39,PALE,'porch soffit')
    f.box(0,5.40,width+.18,.14,1.26,.38,STONE,'porch drip edge')
    back=box(-width/2,5.45,width/2,7.15)
    f.prism(back,.70,.739,STONE,'backing behind trefoils')
    openings=[]
    for j in range(11):
        x=(j-5)*.765
        lobes=[disc(x,6.75,.115),disc(x-.127,6.59,.115),disc(x+.127,6.59,.115)]
        stem=box(x-.107,5.50,x+.107,6.61)
        openings.append(unary_union([stem,*lobes]))
    f.prism(back.difference(unary_union(openings)),.753,1.027,PALE,'eleven recessed trefoil panels')
    f.box(0,7.20,width+.17,.14,1.21,.44,STONE,'trefoil coping')
    for x in [-4.62,4.62]:
        f.box(x,3.06,.73,4.53,.83,.218,BRICK,'porch brick buttress')
        f.box(x,5.40,.87,.18,.98,.23,STONE,'porch buttress cap')
    # Seven exposed rises in front of the closed entrance, with a plain retaining cheek each side.
    for j in range(7):
        z=(j+1)*.17;d=2.40-.30*j
        f.box(0,z/2,5.24,z,.319,d,STONE,'entrance granite risers')
        f.box(0,z-.009,5.28,.036,.091,d+.130,PALE,'rounded stair nosings')
    for direction in [-1,1]:
        f.box(direction*2.73,.73,.20,1.46,.58,.76,PALE,'stair cheek terminals')


def add_north_front(builder,lod):
    f=Facade(builder,(-WIDTH/2,0),(WIDTH/2,0),'North gables')
    outline=Polygon([(-WIDTH/2,0),(WIDTH/2,0),*reversed(GABLE)])
    main=pointed(0,SILL,MAIN_WIDTH,MAIN_TOP,MAIN_TOP-SPRING,26 if lod else 52)
    door=low_arch(0,1.19,4.00,4.60,.53)
    side_small=[];side_tall=[];side_round=[]
    for s in [-1,1]:
        side_small.append(low_arch(s*6.32,1.15,.60,4.07,.31))
        side_tall.append(pointed(s*9.67,7.70,.91,11.53,.56))
        side_round.append(disc(s*9.64,15.64,.54,14 if lod else 27))
    wall=f.wall(0,25,[main,door,*side_small,*side_tall,*side_round],thickness=.52,material=BRICK,outline=outline)
    inner=wall.buffer(-.06)
    courses=[];pitch=.265 if lod else .153
    for i in range(1,ceil(24/pitch)):
        z=i*pitch;wire=box(-13,z-.006,13,z+.006).intersection(inner)
        if not wire.is_empty:courses.append(wire)
    f.prism(unary_union(courses),.001,.005,JOINT,'brick bed joints')
    for z in [4.87,7.42,14.64]:
        seg=box(-13,z-.047,13,z+.047).intersection(wall)
        if z>7:seg=seg.difference(box(-4.78,0,4.78,24))
        f.prism(seg,.008,.103,STONE,'granite string courses')
    main_light(f,main,lod);porch(f,lod)
    for side,small,tall,roundel in zip([-1,1],side_small,side_tall,side_round):
        glazed(f,small,'low round-headed sidelight',rows=3)
        glazed(f,tall,'side lancet',rows=3,mat=AQUA)
        glazed(f,roundel,'side gable circular light',rows=2)
        f.prism(roundel.buffer(.104).difference(roundel),.01,.10,ARCH,'oculus brick rim')
        f.prism(tall.buffer(.115,join_style=2).difference(tall).intersection(box(-14,10.95,14,11.9)),.01,.08,ARCH,'side lancet brick hood')
        x=side*4.72
        f.box(x,9.95,.47,8.98,.45,.11,BRICK,'slender central buttress')
        f.box(x,14.50,.69,.26,.63,.14,STONE,'buttress weathered cap')
        f.box(x,9.42,.59,.12,.56,.14,STONE,'buttress intermediate course')
        f.line((side*7.11,.41,.114),(side*7.11,15.50,.114),.071,METAL,8,'rainwater pipe')
        f.box(side*7.11,15.54,.26,.30,.19,.13,METAL,'rainwater hopper')
    path=LineString(GABLE)
    f.prism(path.buffer(.115,cap_style=2,join_style=2),.018,.155,STONE,'three raking gable copings')
    for (x,z),(x2,z2) in zip(GABLE,GABLE[1:]):
        band=Polygon([(x,z-.05),(x2,z2-.05),(x2,z2+.078),(x,z+.078)])
        f.prism(band,-DEPTH,-.012,ROOF,'short grey tile roof section')
    for x in [-WIDTH/2,WIDTH/2]:
        builder.box([x,.59,7.72],[.16,DEPTH,15.44],BRICK,label='Neutral north return')
    f.box(0,23.69,.28,.55,.31,.00,STONE,'cross plinth')
    f.box(0,24.23,.155,1.24,.172,.00,PALE,'stone cross upright')
    f.box(0,24.40,.79,.155,.172,.00,PALE,'stone cross arm')
    ring=disc(0,24.40,.25).difference(disc(0,24.40,.166))
    f.prism(ring,-.078,.078,PALE,'cross circular nimbus')
