"""The three-bay brick portico, flanking timber gables and garden steps at 263 Lane, No. 7."""
import math
from shapely.geometry import Polygon, box
from shapely.ops import unary_union
from photo_architecture import Facade, opening

CENTER_WIDTH = 6.12
WING_WIDTH = 4.67
WING_CENTER = 5.75
BACK = 9.65
LANDING = 1.50
PALETTE = {
    'red face brick': {'color':[.47,.184,.115],'roughness':.87},
    'dark red headers': {'color':[.346,.136,.090],'roughness':.85},
    'terracotta relief': {'color':[.586,.265,.175],'roughness':.81},
    'weathered mortar': {'color':[.359,.272,.235],'roughness':.87},
    'moulded red stone': {'color':[.516,.269,.195],'roughness':.78},
    'grey stone caps': {'color':[.52,.508,.457],'roughness':.75},
    'ivory stone finials': {'color':[.73,.695,.583],'roughness':.79},
    'grey brick screen': {'color':[.36,.343,.326],'roughness':.86},
    'dark gallery timber': {'color':[.131,.116,.104],'roughness':.66},
    'white gable plaster': {'color':[.762,.728,.660],'roughness':.82},
    'sash glazing': {'color':[.177,.206,.196],'roughness':.37,'metallic':.12},
    'dark painted iron': {'color':[.089,.086,.079],'roughness':.57,'metallic':.25},
    'red clay roof': {'color':[.406,.178,.118],'roughness':.88},
    'gallery floor': {'color':[.312,.274,.242],'roughness':.8},
    'quiet section': {'color':[.447,.374,.328],'roughness':.92},
}

def sash(face, shape, columns, rows, name, lod):
    left,bottom,right,top=shape.bounds
    inner=shape.buffer(-.07,join_style='mitre')
    bars=[box(left+(right-left)*i/columns-.023,bottom,left+(right-left)*i/columns+.023,top)
          for i in range(1,columns)]
    bars.extend(box(left,z-.023,right,z+.023)for z in rows)
    cells=inner.difference(unary_union(bars))
    face.prism(shape.buffer(.005,join_style='mitre'),-.285,-.262,'sash glazing',name+' glass')
    face.prism(shape.difference(cells),-.254,-.147,'dark gallery timber',name+' sash bars')
    if not lod:
        face.prism(cells.difference(cells.buffer(-.018,join_style='mitre')),-.257,-.239,'grey stone caps',name+' glazing beads')

def joints(face, area, material, lod):
    face.prism(area,-.24,0,material,'masonry wall and reveals')
    if lod:return
    # Fine mortar on the planar brickwork stops at the real apertures.
    l,b,r,t=area.bounds
    for j in range(1,int((t-b)/.105)+1):
        z=b+j*.105
        course=area.intersection(box(l,z-.004,r,z+.004))
        if course.area>.001:face.prism(course,.001,.007,'weathered mortar','thin horizontal bed joints')
    for j in range(int((t-b)/.21)+1):
        z=b+j*.21
        for phase in [0,1]:
            xs=[l+.135*phase+i*.275 for i in range(int((r-l)/.275)+2)]
            perps=unary_union([box(x,z+phase*.105+.006,x+.006,z+phase*.105+.10)for x in xs])
            cut=area.intersection(perps)
            if cut.area>.0005:face.prism(cut,.001,.006,'weathered mortar','staggered brick perpends')

def column(builder,x,y,foot,top,slim,lod):
    h=top-foot
    r=.12 if slim else .164
    profile=[(foot,r*1.30),(foot+.063,r*1.32),(foot+.08,r*1.08),(foot+.145,r*1.12),
             (foot+.18,r),(foot+h*.71,r*.90),(top-.22,r*.86),(top-.16,r*1.22),
             (top-.098,r*1.12),(top-.052,r*1.32),(top,r*1.30)]
    builder.lathe((x,y),profile,'moulded red stone',8 if lod else 18,'central portico/shaped brick shaft')
    builder.box((x,y,top+.035),(r*3.1,r*2.9,.08),'terracotta relief',label='central portico/square abacus')

def pierced_parapet(builder,z=9.64):
    w=CENTER_WIDTH+.18;front=Facade(builder,(-w/2,2.43),(w/2,2.43),'roof parapet')
    apertures=[]
    for x in [-2.17,-1.77,-.64,-.25,.16,.56,1.64,2.04]:
        apertures.append(opening(x,z+.12,.238,.31,.105,segments=10))
    front.prism(box(-w/2,z,w/2,z+.63).difference(unary_union(apertures)),-.32,0,'red face brick','arcaded parapet')
    for zz,hh,proj in [(z-.028,.10,.10),(z+.625,.08,.14)]:
        front.beam(zz,hh,proj,'moulded red stone',w+.07,'parapet and coping')
    for x in [-w/2+.14,-1.12,1.03,w/2-.14]:
        builder.box((x,2.53,z+.35),(.21,.32,.72),'moulded red stone',label='roof parapet/stops')
        builder.lathe((x,2.53),[(z+.675,.088),(z+.73,.107),(z+.795,.078),(z+.824,.025)],
                      'grey stone caps',12,'roof parapet/small finial')

def brick_portico(builder,lod):
    w=CENTER_WIDTH;front=Facade(builder,(-w/2,2.5),(w/2,2.5),'brick portico')
    left=-w/2;right=w/2
    ground=[opening(x,LANDING+.15,width,3.27,.20,segments=12 if lod else 24)
            for x,width in [(-1.90,1.02),(0,1.56),(1.90,1.02)]]
    upper=[opening(x,6.03,width,1.98)for x,width in [(-1.90,.95),(0,1.50),(1.90,.95)]]
    area=box(left,.025,right,9.48).difference(unary_union(ground+upper))
    joints(front,area,'red face brick',lod)
    for i,hole in enumerate(ground):
        sash(front,hole,3 if i==1 else 2,[3.93,4.40],'lower centre bay' if i==1 else 'lower side bay',lod)
        ar=hole.buffer(.13,join_style='mitre').difference(hole)
        front.prism(ar,.012,.082,'moulded red stone','splayed brick heads')
    for hole in upper:
        sash(front,hole,3,[6.45,7.70,7.85],'upper sash',lod)
        front.prism(hole.buffer(.104,join_style='mitre').difference(hole),.018,.081,'moulded red stone','upper architrave')
    for z,h,d,mat in [(1.38,.12,.12,'grey stone caps'),(5.12,.16,.12,'moulded red stone'),
                       (5.39,.12,.18,'terracotta relief'),(5.56,.09,.14,'moulded red stone'),
                       (8.27,.11,.13,'terracotta relief'),(8.50,.10,.19,'moulded red stone'),
                       (9.26,.12,.17,'moulded red stone'),(9.49,.14,.23,'terracotta relief')]:
        front.beam(z,h,d,mat,w+.07,'projecting horizontal stringcourse')
    for x in [-2.85,-1.14,1.14,2.85]:
        front.box(x,3.34,.38,3.61,.29,.035,'moulded red stone','lower channelled pier')
        for z in [1.62,2.2,2.85,3.5,4.15,4.80]:
            front.box(x,z,.42,.08,.30,.056,'terracotta relief','lower pier joint')
        column(builder,x,2.385,5.65,8.21,False,lod)
    for x in [-1.89,0,1.89]:
        width=1.47 if x==0 else 1.04
        for z in [5.75,8.72]:
            front.prism(box(x-width/2,z-.14,x+width/2,z+.14).difference(
                box(x-width/2+.055,z-.084,x+width/2-.055,z+.084)),.013,.09,'terracotta relief','sunk terracotta rectangle')
    # The upper brick frieze has diagonal lozenge ornament, visible in the 2022 front photograph.
    if not lod:
        for i in range(17):
            x=-2.79+i*.346;z=9.035
            diamond=Polygon([(x-.16,z),(x,z+.105),(x+.16,z),(x,z-.105)])
            front.prism(diamond.difference(diamond.buffer(-.026,join_style='mitre')),.012,.071,'terracotta relief','linked diamond frieze')
    for x,side in [(left,-1),(right,1)]:
        points=((x,BACK),(x,2.51))if side<0 else ((x,2.51),(x,BACK))
        sideface=Facade(builder,*points,'central portico return')
        sideface.wall(.015,9.44,[],.17,'red face brick')
    builder.box((0,(BACK+2.50)/2,9.53),(w+.045,BACK-2.50,.18),'grey stone caps',label='central roof/flat platform')
    builder.box((0,BACK-.08,4.72),(w,.16,9.44),'quiet section',label='portico rear section')
    pierced_parapet(builder)

def gallery_rail(builder, x1, x2, y, floor, lod):
    width=x2-x1
    builder.box(((x1+x2)/2,y,floor+.94),(width,.079,.074),'dark gallery timber',label='garden loggias/rail cap')
    builder.box(((x1+x2)/2,y,floor+.11),(width,.056,.048),'dark painted iron',label='garden loggias/rail foot')
    count=round(width/(.23 if lod else .132))
    for i in range(count+1):
        x=x1+width*i/count
        builder.tube([(x,y,floor+.11),(x,y,floor+.91)],.017,'dark painted iron',4 if lod else 6,'garden loggias/iron balusters')
    if not lod:
        for i in range(1,count,2):
            x=x1+width*i/count;r=min(.102,width/count*.74)
            points=[(x+r*math.sin(j*math.tau/12),y,floor+.52+r*1.6*math.cos(j*math.tau/12))for j in range(13)]
            builder.tube(points,.013,'dark painted iron',5,'garden loggias/oval railing panels')

def gabled_gallery(builder,side,lod):
    cx=side*WING_CENTER;w=WING_WIDTH;left=cx-w/2;right=cx+w/2
    front_y=2.94;rear_y=5.66;upper_floor=5.26;eave=7.95;ridge=9.96
    outer=Facade(builder,(left,front_y),(right,front_y),'timber garden gable')
    back=Facade(builder,(left,rear_y),(right,rear_y),'gallery rear')
    lower=opening(0,LANDING+.16,1.17,2.78,.13,segments=12)
    upper=opening(0,upper_floor+.10,1.11,2.50,.20,segments=12)
    side_windows=[opening(x,LANDING+.56,.61,1.9)for x in [-1.46,1.46]]
    outlets=[lower,upper,*side_windows]
    back.wall(.04,eave-.08,outlets,.22,'white gable plaster')
    sash(back,lower,3,[3.46,3.94],'gallery ground door',lod)
    sash(back,upper,3,[7.29],'door to upper gallery',lod)
    for win in side_windows:sash(back,win,2,[3.18],'small side sash',lod)
    basement=opening(0,.34,1.46,.45)
    outer.wall(.025,LANDING-.14,[basement],.23,'grey brick screen')
    outer.prism(basement,-.25,-.22,'dark gallery timber','recessed basement opening')
    for floor in [LANDING,upper_floor]:
        builder.box((cx,(rear_y+front_y)/2,floor-.115),(w+.02,rear_y-front_y+.05,.23),'gallery floor',label='garden loggias/gallery platform')
        outer.box(0,floor-.045,w+.065,.14,.25,.03,'dark gallery timber','moulded edge of gallery floor')
        gallery_rail(builder,left+.13,right-.13,front_y+.015,floor,lod)
    for x in [left+.12,right-.12]:
        builder.box((x,front_y+.085,(LANDING+eave)/2),(.17,.19,eave-LANDING),'dark gallery timber',label='garden loggias/two-storey timber posts')
        builder.box((x,front_y+.085,LANDING+.25),(.23,.24,.51),'dark gallery timber',label='garden loggias/square post base')
        builder.box((x,front_y+.085,eave-.1),(.253,.235,.23),'dark gallery timber',label='garden loggias/capped post top')
    # The timber fret under the eave is visible above the dark, recessed second-floor gallery.
    for u in range(8):
        x=-w/2+.16+u*(w-.32)/8;span=(w-.32)/8
        outer.line((x,eave-.55,.03),(x+span,eave-.16,.03),.038,'dark gallery timber',6,'diagonal lattice')
        outer.line((x,eave-.16,.03),(x+span,eave-.55,.03),.038,'dark gallery timber',6,'diagonal lattice')
    outer.box(0,eave-.59,w,.11,.16,.014,'dark gallery timber','horizontal lintel under lattice')
    gable=Polygon([(-w/2-.10,eave),(0,ridge),(w/2+.10,eave)])
    outer.prism(gable,-.14,0,'white gable plaster','infilled front gable')
    for x in [-1.60,-.83,0,.83,1.60]:
        rake=ridge-(ridge-eave)*abs(x)/(w/2+.10)
        outer.box(x,(eave+rake)/2,.095,rake-eave,.085,.044,'dark gallery timber','exposed gable stud')
    outer.box(0,eave,w+.28,.16,.20,.065,'dark gallery timber','gable base')
    for x in [-w/2-.18,w/2+.18]:
        outer.line((x,eave-.035,.09),(0,ridge+.04,.09),.111,'dark gallery timber',6,'raking bargeboard')
        ridge_line=Polygon([(x,eave+.065),(0,ridge+.11),(0,ridge-.045),(x,eave-.09)])
        outer.prism(ridge_line,-(BACK-front_y),.08,'red clay roof','pitched clay roof band')
        # Spaced dark tile channels are readable at oblique angles.
        for j in range(8 if lod else 20):
            y=front_y+.035+j*(BACK-front_y-.07)/(7 if lod else 19)
            builder.tube([(cx+x,y,eave+.071),(cx,y,ridge+.125)],.025,'red clay roof',5 if lod else 7,'garden gables/rounded red tile upstands')
    section_y=rear_y+.39
    builder.box((cx,(BACK+section_y)/2,(eave+.04)/2),(w,BACK-section_y,eave-.04),'quiet section',label='cut rear of garden gallery')
    # The slim connecting bay is set farther back from each projecting timber gable.
    gap_left=min(side*CENTER_WIDTH/2,cx-side*w/2);gap_right=max(side*CENTER_WIDTH/2,cx-side*w/2)
    center=(gap_left+gap_right)/2;gw=gap_right-gap_left
    if gw>.05:
        builder.box((center,5.76,4.44),(gw,.24,8.80),'red face brick',label='recessed link behind portico')
        builder.box((center,5.58,6.75),(gw*.70,.08,1.42),'sash glazing',label='recessed link window')
        gallery_rail(builder,gap_left,gap_right,front_y+.31,upper_floor,lod)

def stone_ball(builder,x,y,floor,r,lod):
    profile=[(floor,r*.49),(floor+.042,r*.66),(floor+.08,r*.51)]
    for j in range(1,9):
        ang=-math.pi/2+j*math.pi/9;profile.append((floor+.08+r*(1+math.sin(ang)),r*math.cos(ang)))
    profile.append((floor+.08+2*r,.018))
    builder.lathe((x,y),profile,'ivory stone finials',10 if lod else 20,'garden wall/stone ball finials')

def garden_steps(builder,lod):
    # The photographed terraced wall stands before the raised portico. Short flights approach from both ends.
    front=Facade(builder,(-4.86,.29),(4.86,.29),'garden stair enclosure')
    builder.box((0,1.66,LANDING/2),(6.44,2.12,LANDING),'grey brick screen',label='raised entry/stone landing')
    for s in (-1,1):
        for j in range(8):
            h=LANDING*(j+1)/8;cx=s*(3.23+(7-j)*.282)
            builder.box((cx,1.35,h/2),(.287,1.77,h),'grey stone caps',label='raised entry/lateral stone stair treads')
    edge=[(-4.84,.71),(-3.79,.75),(-3.63,1.10),(-3.01,1.23),(-2.48,1.55),
          (-2.15,1.91),(-1.88,2.39),(-1.70,2.55),(1.70,2.55),(1.88,2.39),
          (2.15,1.91),(2.48,1.55),(3.01,1.23),(3.63,1.10),(3.79,.75),(4.84,.71)]
    form=Polygon([(-4.84,.03),(4.84,.03),*reversed(edge)])
    recess=[opening(x,.16,w,1.10 if x==0 else .90,.42,segments=12 if lod else 22)
            for x,w in [(-2.15,.7),(0,1.30),(2.15,.7)]]
    plaque=opening(0,1.66,.92,.53,.13,segments=14)
    joints(front,form.difference(unary_union(recess+[plaque])),'grey brick screen',lod)
    for i,r in enumerate(recess):
        front.prism(r,-.16,-.14,'red face brick','blind brick recess')
        front.prism(r.buffer(.095,join_style='mitre').difference(r),.011,.057,'terracotta relief','arched red brick recess surround')
    front.prism(plaque,-.085,-.07,'red face brick','recessed plaque field')
    front.prism(plaque.buffer(.11,join_style='mitre').difference(plaque),.014,.081,'terracotta relief','brick plaque moulding')
    for x,h in [(-4.83,.91),(-3.71,1.19),(-1.68,2.70),(1.68,2.70),(3.71,1.19),(4.83,.91)]:
        front.box(x,h/2,.39,h,.44,0,'red face brick','garden wall square brick piers')
        front.box(x,h+.035,.49,.09,.5,-.006,'grey stone caps','post cap and square neck')
        stone_ball(builder,x,.29,h+.08,.16 if abs(x)>4 else .20,lod)
    coping=Polygon([*edge,*[(x,z-.08)for x,z in reversed(edge)]])
    front.prism(coping,-.21,.095,'grey stone caps','curved stone coping on the stair walls')

def garden_elevation(builder,lod):
    brick_portico(builder,lod)
    for side in [-1,1]:gabled_gallery(builder,side,lod)
    garden_steps(builder,lod)
