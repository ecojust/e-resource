"""Garden wall and front roof slope of 1110 Huaihai Middle Road, facing the lawn.

The glazed extension and three dormer windows represent the photographed facade.
The east-side vehicle porch and the roof of the rear wing lie outside this model.
"""
import math

from shapely.geometry import LineString, Polygon, box
from shapely.ops import unary_union

from photo_architecture import Facade, opening

STONE = 'light granite'
TRIM = 'pale carved granite'
JOINT = 'recessed joint'
BRICK = 'side wall red brick'
IRON = 'dark steel'
GLASS = 'garden window glass'
CANOPY = 'reflective canopy glass'
TIMBER = 'brown canopy frame'
ROOF = 'terracotta'
RIDGE = 'tile edge'
SLATE = 'dormer metal'
PAVING = 'garden steps'

PALETTE = {k: dict(color=v, roughness=r, metallic=m) for k,v,r,m in [
    (STONE,[.60,.565,.496],.82,0), (TRIM,[.74,.69,.596],.76,0),
    (JOINT,[.37,.342,.294],.86,0), (BRICK,[.44,.187,.113],.87,0),
    (IRON,[.125,.135,.127],.42,.42), (GLASS,[.17,.239,.248],.25,.22),
    (CANOPY,[.41,.52,.515],.22,.20), (TIMBER,[.271,.151,.081],.67,.08),
    (ROOF,[.411,.166,.086],.90,0), (RIDGE,[.53,.25,.128],.80,0),
    (SLATE,[.231,.201,.181],.75,.15), (PAVING,[.48,.467,.411],.83,0)]}


def steel_window(face, shape, columns, transom, label):
    left,low,right,high = shape.bounds
    bars = [box(left,transom-.035,right,transom+.035)]
    for i in range(1,columns):
        x = left+(right-left)*i/columns
        bars.append(box(x-.032,low,x+.032,high))
    inner = shape.buffer(-.078,join_style=2)
    grid = shape.difference(inner.difference(unary_union(bars)))
    face.prism(grid,-.205,-.12,IRON,label+' steel sashes')
    face.prism(shape.buffer(.008,join_style=2),-.267,-.243,GLASS,label+' panes')


def balcony_rail(face, width, lod):
    bottom,top = 4.73,5.47
    for z in (bottom,top):
        face.line((-width/2,z,.145),(width/2,z,.145),.031,IRON,8,'iron rails')
    for i in range(15):
        x=(i/14-.5)*width
        face.line((x,bottom,.145),(x,top,.145),.018,IRON,5 if lod else 8,'iron balusters')
    for i in (-1,0,1):
        x=i*width*.315
        path=[face.point(x+.114*math.cos(math.tau*j/20),5.10+.171*math.sin(math.tau*j/20),.173) for j in range(21)]
        face.builder.tube(path,.020,IRON,5 if lod else 8,'upper windows/ironwork rings')


def swag(face,lod):
    """Mirrored festoons droop between the keystone and the two outer stops."""
    face.prism(Polygon([(-.19,7.50),(.19,7.50),(.12,8.21),(-.12,8.21)]),
               .026,.230,TRIM,'keystone')
    for sign in (-1,1):
        count=10 if lod else 20
        chain=[]
        for i in range(count+1):
            t=i/count
            x=sign*(.13+1.30*t)
            z=8.06-.28*math.sin(math.pi*t)-.11*t
            chain.append(face.point(x,z,.175))
        face.builder.tube(chain,.079,TRIM,7 if lod else 10,'wing reliefs/floral swags')
        if not lod:
            for i in range(1,11):
                t=i/11
                x=sign*(.13+1.30*t)
                z=8.06-.28*math.sin(math.pi*t)-.11*t
                leaf=Polygon([(x-.046,z+.085),(x+.063,z+.035),(x+.128,z-.067),(x+.052,z-.084)])
                face.prism(leaf,.226,.252,TRIM,'overlapping carved leaves')
        for x in (sign*1.44,):
            face.prism(Polygon([(x-.069,7.99),(x+.067,7.99),(x+.048,7.60),(x,7.49),(x-.044,7.60)]),.06,.17,TRIM,'hanging tassel')


def end_wing(b,center,lod):
    half=2.13
    front=Facade(b,(center-half,-.42),(center+half,-.42),'projecting wing')
    upper=opening(0,4.63,2.81,2.94,.54,18 if lod else 36)
    lower=box(-1.38,1.01,1.38,3.46)
    outline=box(-half,.42,half,8.40)
    surface=front.wall(.42,8.40,[upper,lower],thickness=.35,material=STONE)
    for i in range(13):
        z=.65+.595*i
        ledge=surface.intersection(box(-half,z,half,z+.024))
        front.prism(ledge,.003,.025,JOINT,'horizontal ashlar joints')
    steel_window(front,upper,4,6.72,'arched window')
    steel_window(front,lower,3,2.95,'lower window')
    balcony_rail(front,2.76,lod)
    for z,h,projection in ((4.53,.19,.24),(8.43,.15,.20),(8.61,.12,.32)):
        front.beam(z,h,projection,TRIM)
    arch=upper.buffer(.185,join_style=2).difference(upper).intersection(box(-1.9,6.88,1.9,7.80))
    front.prism(arch,.004,.105,TRIM,'segmental arch surround')
    for i in (-3,-2,-1,1,2,3):
        angle=math.pi/2+i*.285
        x=1.405*math.cos(angle);z=7.03+.54*math.sin(angle)
        strip=LineString([(x,z),(x+.17*math.cos(angle),z+.18*math.sin(angle))]).buffer(.013,cap_style=2)
        front.prism(strip,.110,.119,JOINT,'arch wedge joints')
    swag(front,lod)
    parapet=Polygon([(-half,8.65),(half,8.65),(half,8.98),(1.55,8.98),(1.37,9.12),
                    (1.23,9.12),(1.23,9.49),(-1.23,9.49),(-1.23,9.12),(-1.37,9.12),
                    (-1.55,8.98),(-half,8.98)])
    front.prism(parapet,-.27,.035,STONE,'stepped attic parapet')
    front.prism(box(-1.32,9.42,1.32,9.55),-.32,.125,TRIM,'parapet coping')
    front.prism(box(-1.47,8.86,1.47,8.96),.037,.098,TRIM,'parapet tablet')
    # Short exposed shoulders join the recessed center on either side.
    x=center+half if center<0 else center-half
    b.box((x,.025,4.35),(.24,.90,7.80),STONE,label='wings/returns to recessed loggia')


def ionic_pilaster(b,x,lod):
    y=.29
    b.box((x,y,4.71),(.44,.42,.19),TRIM,label='upper orders/pilaster bases')
    b.box((x,y+.026,6.26),(.34,.32,2.96),STONE,label='upper orders/pilaster shafts')
    count=5 if lod else 7
    for i in range(count):
        xx=x+(.28*(i/(count-1)-.5))
        b.tube([(xx,y-.15,4.86),(xx,y-.15,7.65)],.016,TRIM,6,'upper orders/fluting arrises')
    b.box((x,y,7.79),(.47,.40,.15),TRIM,label='upper orders/capital abaci')
    for sign in (-1,1):
        points=[]
        for i in range(18 if lod else 32):
            t=i/(17 if lod else 31);ang=t*math.pi*2.3
            radius=.105*(1-.83*t)
            points.append((x+sign*(.13+radius*math.cos(ang)),y-.222,7.74+radius*math.sin(ang)))
        b.tube(points,.024,TRIM,6 if lod else 9,'upper orders/Ionic volutes')


def central_loggia(b,lod):
    half=5.30
    face=Facade(b,(-half,.48),(half,.48),'central garden loggia')
    centers=(-3.53,0,3.53)
    lower=[box(x-1.32,.76,x+1.32,3.60)for x in centers]
    upper=[box(x-1.47,4.62,x+1.47,7.74)for x in centers]
    face.wall(.41,8.27,[*lower,*upper],thickness=.29,material=STONE)
    for h in lower:steel_window(face,h,3,2.96,'ground-floor door')
    for x,h in zip(centers,upper):
        steel_window(face,h,3,7.01,'upper loggia window')
        bay=Facade(b,(x-1.49,.41),(x+1.49,.41),'recessed loggia railing')
        balcony_rail(bay,2.89,lod)
    for axis in (-4.90,-1.77,1.77,4.90):
        for off in (-.19,.19):
            x=axis+off;ionic_pilaster(b,x,lod)
            b.lathe((x,.22),[(.56,.174),(.64,.18),(.72,.137),(3.63,.118),(3.74,.175),(3.84,.18)],
                    TRIM,10 if lod else 18,'lower loggia/Tuscan order')
    for z,h,p in ((4.40,.23,.34),(8.16,.21,.23),(8.34,.15,.38)):
        face.beam(z,h,p,TRIM)
    for i in range(34):
        face.box(-5.09+i*.309,8.04,.139,.137,.187,.095,TRIM,'dentils')


def conservatory(b,lod):
    """Later glazed enclosure with three-sided pitched door canopy and stone stair."""
    half,back,front=9.44,-.68,-3.57
    # Continuous photographed glass is tinted. Leave the center doorway and its passage open.
    for x0,x1 in [(-half,-2.03),(2.03,half)]:
        face=Facade(b,(x0,front),(x1,front),'garden glass extension')
        pane=box(-face.length/2,.51,face.length/2,3.49)
        face.prism(pane,-.075,-.045,GLASS,'large glazed lights')
        for i in range(4):
            x=(i/3-.5)*face.length
            face.box(x,2.02,.096,3.12,.12,.036,TIMBER,'uprights')
    def roof(x,y,z):return(x,y,3.61+(y-front)*.205+z)
    b.prism(box(-half,front,half,back),-.088,0,roof,CANOPY,'sunroom/glazed lean-to roof')
    for i in range(13):
        x=-half+i*2*half/12
        b.prism(box(x-.043,front-.06,x+.043,back+.06),.005,.096,roof,TIMBER,'sunroom/roof glazing bars')
    for y in (front,front+1.35,back):
        b.prism(box(-half-.075,y-.05,half+.075,y+.05),.003,.096,roof,TIMBER,'sunroom/glazing crossbars')
    door=Facade(b,(-2.03,front),(2.03,front),'glazed entrance doors')
    for x in (-.83,.83):
        shape=box(x-.82,.655,x+.82,3.57)
        steel_window(door,shape,1,3.19,'paired doors')
        pull=x+(.65 if x<0 else -.65)
        door.line((pull,1.46,.05),(pull,1.96,.05),.028,IRON,8,'pull handles')
    for x in (-1.833,1.833):
        shape=box(x-.17,.655,x+.17,3.57)
        steel_window(door,shape,1,3.19,'narrow sidelight')
    for sign in (-1,1):
        x=sign*1.99
        b.box((x,-4.91,1.91),(.136,.15,3.77),TIMBER,label='entrance/outer porch posts')
        def pitch(u,v,z):return (u,v,4.42-.302*abs(u)+z)
        left,right=sorted((0,x+sign*.23))
        b.prism(box(left,-5.21,right,-3.27),-.060,0,pitch,CANOPY,'entrance/two roof panes')
        for y in (-5.18,-3.30):
            b.tube([(0,y,4.45),(sign*2.23,y,3.77)],.064,TIMBER,8,'entrance/gable rafters')
    b.box((0,-4.21,4.47),(.11,2.04,.11),TIMBER,label='entrance/ridge')
    for i in range(5):
        back_edge=-3.46
        edge=-5.87+i*.36
        h=.132*(i+1)
        b.box((0,(edge+back_edge)/2,h/2),(3.64,back_edge-edge,h),PAVING,label='entrance/five stone treads')
    for sign in (-1,1):
        b.box((sign*2.21,-5.38,.24),(.55,.58,.48),TRIM,label='entrance/stone plinths')
        b.lathe((sign*2.21,-5.38),[(.48,.09),(.57,.14),(.64,.10),(.72,.17),(.78,.20),(.82,.21)],
                PAVING,12 if lod else 20,'entrance/planter bowls')


def roof_slope(b,lod):
    half,y0,span=9.59,.06,5.42
    outside=[(-half,y0),(half,y0),(half-span,y0+span),(-half+span,y0+span)]
    plane=Polygon(outside)
    def main(x,y,z):return (x,y,8.46+.403*(y-y0)+z)
    b.prism(plane,-.16,0,main,ROOF,'roof/garden-facing hip slope')
    for sign in (-1,1):
        corner=Polygon([(sign*half,y0),(sign*half,7.65),(sign*(half-span),7.65),(sign*(half-span),y0+span)])
        def hip(x,y,z):return(x,y,8.46+.403*(half-sign*x)+z)
        b.prism(corner,-.155,0,hip,ROOF,'roof/hip returns')
        b.tube([(sign*half,y0,8.52),(sign*(half-span),y0+span,10.70)],.074,RIDGE,8,'roof/hip caps')
    crown=box(-half+span,y0+span,half-span,7.65)
    b.plan_prism(crown,10.47,10.65,ROOF,'roof/short ridge return')
    for i in range(1,13 if lod else 23):
        y=y0+i*span/(13 if lod else 23)
        strip=box(-half,y-.012,half,y+.021).intersection(plane)
        b.prism(strip,.002,.023,main,RIDGE,'roof/overlapping tile courses')
    dorm=Facade(b,(-3.65,2.42),(3.65,2.42),'continuous garden dormer')
    windows=[box(x-.72,9.49,x+.72,10.47) for x in (-2.38,0,2.38)]
    dorm.wall(9.37,10.60,windows,thickness=.20,material=TRIM)
    for win in windows:steel_window(dorm,win,2,10.30,'dormer casements')
    for side in (-1,1):
        b.box((side*3.56,3.10,10.00),(.18,1.36,1.18),SLATE,label='dormer/cheeks')
    b.box((0,3.15,10.67),(7.64,1.91,.16),SLATE,label='dormer/shallow roof')
    for x,y,z in [(-5.48,5.91,10.74),(5.72,6.08,10.94)]:
        b.box((x,y,z-.63),(.71,.52,1.26),BRICK,label='roof/brick chimney shafts')
        b.box((x,y,z),(.82,.66,.17),TRIM,label='roof/chimney caps')


def add_house(builder,lod):
    for x in (-7.43,7.43):end_wing(builder,x,lod)
    central_loggia(builder,lod)
    conservatory(builder,lod)
    roof_slope(builder,lod)
    # The two visible side-wall returns stop forward of the undocumented rear elevations.
    for x in (-9.51,9.51):
        outer=(x+.11 if x>0 else x-.11)
        ends=[(outer,-.23),(outer,7.47)]
        side=Facade(builder,*(ends if x>0 else ends[::-1]),'brick return')
        side.wall(.42,8.375,thickness=.22,material=BRICK)
        half=side.length/2
        start=-half if x>0 else half
        stop=start+(1.21 if x>0 else -1.21)
        left,right=sorted((start,stop))
        side.prism(box(left,.42,right,8.375),.0,.067,STONE,'rusticated corner return')
        for z in (.65+.595*i for i in range(13)):
            side.prism(box(left,z,right,z+.022),.068,.074,JOINT,'corner ashlar joints')
        for z,height,projection in ((4.53,.16,.17),(8.15,.16,.16),(8.36,.16,.25)):
            side.beam(z,height,projection,TRIM)
        if not lod:
            for row in range(46):
                z=.57+row*.167
                edge=right if x>0 else -half
                finish=half if x>0 else left
                side.prism(box(edge,z,finish,z+.011),.002,.010,JOINT,'brick bed joints')
                for j in range(14):
                    joint=edge+.18+(j+.5*(row%2))*.45
                    if joint<finish-.03:
                        side.prism(box(joint,z+.012,joint+.011,z+.166),.001,.008,JOINT,'staggered brick joints')
    builder.box((0,1.00,.33),(19.0,9.01,.66),PAVING,label='garden range/raised ground floor')
