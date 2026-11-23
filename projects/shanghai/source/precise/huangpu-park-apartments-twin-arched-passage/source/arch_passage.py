"""Paired entrances photographed on the north front of 455 Middle Fuxing Road.

X follows the facade westward, Y runs into the threshold, Z above the paving.
The center line is the photographed brick pier. Only the visible passage mouth
is reconstructed. The U-shaped apartment and the garden house stay separate.
"""
from math import pi, sin, cos, sqrt
from shapely.geometry import Polygon, LineString, box
from shapely.ops import unary_union
from photo_architecture import Facade

PALETTE = {
    'grey limestone': {'color':[.595,.575,.541], 'roughness':.91},
    'soffit plaster': {'color':[.454,.44,.41], 'roughness':.94},
    'limestone drip': {'color':[.669,.647,.609], 'roughness':.82},
    'brick bed joints': {'color':[.358,.270,.233], 'roughness':.97},
    'burnt red brick': {'color':[.445,.265,.212], 'roughness':.93},
    'dark red brick': {'color':[.396,.225,.191], 'roughness':.94},
    'granite plinth': {'color':[.334,.348,.349], 'roughness':.88},
    'painted iron': {'color':[.107,.125,.130], 'metallic':.27,'roughness':.66},
    'raised inscription': {'color':[.287,.291,.272], 'roughness':.85},
    'green lane sign': {'color':[.115,.318,.258], 'roughness':.66},
    'enamel lettering': {'color':[.86,.875,.805], 'roughness':.62},
    'bronze plate': {'color':[.46,.335,.179], 'metallic':.3,'roughness':.64}
}
HALF=4.08
ARCHES=[(-1.91,2.72,2.70,3.27),(1.73,2.61,2.64,3.20)]
TOP=4.02
DEPTH=1.20

def strip(points,width):
    return LineString(points).buffer(width/2,cap_style=2,join_style=2)

def aperture(center,width,spring,crown,steps):
    rise=crown-spring
    radius=width*width/(8*rise)+rise/2
    arc=[]
    for index in range(steps+1):
        x=-width/2+width*index/steps
        arc.append((center+x,crown-radius+sqrt(max(0,radius*radius-x*x))))
    return Polygon([(center-width/2,-.05),*arc,(center+width/2,-.05)])

def escutcheons(face,detail):
    for index,x in enumerate([-3.62,0,3.68]):
        # The stone drip edge opens over each brick pier in a small round-headed notch.
        shape=box(x-.30,2.34,x+.30,2.79)
        arch=aperture(x,.26,2.44,2.55,16 if detail else 8)
        face.prism(shape.difference(arch),-.04,.060,'grey limestone','pier return '+str(index))
        for dz,depth in [(0,.105),(.068,.08)]:
            line=box(x-.30,2.37+dz,x+.30,2.409+dz)
            face.prism(line.difference(arch),.038,depth,'limestone drip','pier moulding '+str(index))

def wall(builder,lod):
    face=Facade(builder,(-HALF,0),(HALF,0),'street entry')
    holes=unary_union([aperture(*a,14 if lod else 44)for a in ARCHES]);extent=box(-HALF,0,HALF,TOP)
    front=extent.difference(holes)
    # The projecting header and the two arched soffits are open geometry.
    face.prism(front.intersection(box(-HALF,2.35,HALF,TOP)),-DEPTH,0,'soffit plaster','curving soffits')
    face.prism(front.intersection(box(-HALF,2.32,HALF,TOP)),-.025,.012,'grey limestone','stone spandrels')
    jambs=front.intersection(box(-HALF,0,HALF,2.35))
    face.prism(jambs,-DEPTH,0,'brick bed joints','pier cores')
    face.prism(jambs.intersection(box(-HALF,0,HALF,.37)),-DEPTH-.004,.024,'granite plinth','stone feet')
    brickface=jambs.intersection(box(-HALF,.37,HALF,2.36))
    if lod:face.prism(brickface,-.01,.012,'burnt red brick','brick faces')
    else:
        for course in range(23):
            z=.37+.090*course
            for j in range(34):
                x=-HALF-.31+.277*j+(course%2)*.1385
                clipped=brickface.intersection(box(x+.004,z+.003,x+.273,z+.086))
                if clipped.area>1e-5:face.prism(clipped,-.003,.014,'dark red brick' if(j*7+course)%9==0 else 'burnt red brick','paired brick piers')
    face.box(0,3.97,2*HALF,.105,.31,.055,'limestone drip','continuous balcony cap')
    for z in [3.393,3.456]:
        face.box(0,z,2*HALF,.052,.20,.027,'limestone drip','inscription ledge')
    escutcheons(face,not lod)
    return face

def railing(face,lod):
    for side in [-1,1]:
        lo,hi=sorted((side*.59,side*3.48))
        x=(lo+hi)/2
        for z in [4.06,4.45]:face.box(x,z,hi-lo,.034,.047,-.10,'painted iron','balcony rails')
        for i in range(7):
            pos=lo+(hi-lo)*i/6
            face.box(pos,4.255,.022,.42,.049,-.10,'painted iron','balcony uprights')
        wires=[]
        for i in range(6):
            a=lo+(hi-lo)*i/6;b=lo+(hi-lo)*(i+1)/6
            for flip in [-1,1]:
                pts=[(a+(b-a)*t/16,4.255+flip*.143*sin(pi*(t/16-.5)))for t in range(17)]
                wires.append(strip(pts,.017 if not lod else .023))
        face.prism(unary_union(wires),-.123,-.104,'painted iron','interwoven guard panels')

def right_gate(face,lod):
    x,w,s,h=ARCHES[1]
    bars=[]
    for i in range(11):
        dx=w*(i-5)/11
        top=h-.09-.49*(abs(dx)/(w/2))**2
        bars.append(box(x+dx-.018,.13,x+dx+.018,top))
    for z in [.22,1.04,2.40]:
        bars.append(box(x-w/2+.05,z-.021,x+w/2-.05,z+.021))
    for side in [-1,1]:
        c=x+side*w*.235
        for height,scale in [(.60,.365),(2.69,.135)]:
            # Opposed bent strapwork on the two actual gate leaves.
            for direction in [-1,1]:
                pts=[(c+direction*.47*t/24,height+scale*(sin(pi*t/24)-.40*t/24))for t in range(25 if not lod else 9)]
                if lod:pts=[(c+direction*.47*t/8,height+scale*(sin(pi*t/8)-.40*t/8))for t in range(9)]
                bars.append(strip(pts,.022 if not lod else .033))
    face.prism(unary_union(bars),-.363,-.316,'painted iron','closed arched grille')
    face.box(x,.99,.52,.14,.041,-.286,'bronze plate','small gate plate')

# Original stroke drawings from the spelling on the facade. No photo pixels or font outlines.
STROKES={
 '花': [[(.08,.78),(.91,.83)],[(.34,.97),(.32,.64)],[(.69,.98),(.66,.64)],[(.39,.63),(.13,.31)],[(.29,.48),(.27,.07)],[(.58,.63),(.55,.14),(.63,.07),(.86,.10),(.92,.23)],[(.89,.58),(.72,.40),(.57,.34)]],
 '園': [[(.10,.91),(.10,.09)],[(.10,.89),(.88,.93),(.86,.10),(.14,.07)],[(.48,.81),(.48,.65)],[(.30,.74),(.68,.77)],[(.24,.64),(.74,.66)],[(.32,.57),(.33,.41),(.66,.42),(.68,.57),(.32,.55)],[(.49,.40),(.27,.24)],[(.42,.34),(.41,.18),(.56,.24)],[(.63,.39),(.72,.34),(.61,.28)],[(.54,.37),(.66,.24),(.76,.17)]],
 '公': [[(.39,.85),(.29,.70),(.10,.58)],[(.62,.90),(.73,.76),(.90,.66)],[(.49,.62),(.40,.45),(.24,.25),(.69,.29)],[(.61,.45),(.72,.32),(.81,.17)]],
 '寓': [[(.49,.98),(.56,.89)],[(.11,.76),(.17,.85),(.85,.87),(.81,.75)],[(.28,.70),(.28,.47),(.72,.49),(.72,.71),(.29,.69)],[(.30,.59),(.71,.61)],[(.50,.68),(.48,.24)],[(.16,.40),(.16,.09)],[(.17,.42),(.82,.44),(.80,.10),(.71,.14)],[(.33,.22),(.65,.26)],[(.59,.33),(.69,.19)]]}

def letters(face,lod):
    for i,ch in enumerate('花園公寓'):
        c=(i-1.5)*1.13
        paths=[strip([(c+(x-.5)*.43,3.695+(z-.5)*.405)for x,z in line],.024 if not lod else .031)for line in STROKES[ch]]
        face.prism(unary_union(paths),.014,.042,'raised inscription','lane character '+str(i+1))
    face.box(.04,2.77,.54,.19,.032,.040,'green lane sign','lane 455 enamel address')
    digits={'4':[(.80,1),(.15,.38),(.92,.38),(.74,.38),(.74,0)],'5':[(.87,.96),(.23,.96),(.17,.55),(.66,.58),(.89,.39),(.74,.10),(.15,.04)]}
    for i,d in enumerate('455'):
        pts=[(-.15+i*.081+x*.055,2.727+z*.077)for x,z in digits[d]]
        face.prism(strip(pts,.0065 if not lod else .009),.055,.063,'enamel lettering','address digits')

def add_building(builder,lod=False):
    face=wall(builder,lod)
    railing(face,lod)
    right_gate(face,lod)
    letters(face,lod)
