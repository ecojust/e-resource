"""Centre bay of the garden elevation at 393 Yan’an Middle Road, in metres.

X runs east along the facade, Y runs into the building, Z is above the garden
threshold. Y=0 is the geometric front edge of the original city footprint.
"""
from math import cos, sin, pi
from shapely.geometry import LineString, Polygon, box, Point
from shapely.ops import unary_union
from photo_architecture import Facade

PALETTE = {
    'warm render': {'color':[.72,.66,.54],'roughness':.91},
    'dressed stone': {'color':[.64,.58,.46],'roughness':.85},
    'light stone': {'color':[.80,.75,.62],'roughness':.85},
    'lower stone': {'color':[.48,.45,.37],'roughness':.87},
    'wrought iron': {'color':[.095,.095,.084],'roughness':.64,'metallic':.43},
    'old brass': {'color':[.50,.39,.18],'roughness':.52,'metallic':.54},
    'dark joinery': {'color':[.19,.16,.12],'roughness':.68},
    'glass': {'color':[.23,.28,.26],'roughness':.27,'metallic':.15},
    'shadow glass': {'color':[.118,.134,.130],'roughness':.31,'metallic':.13},
    'red blossom': {'color':[.55,.16,.17],'roughness':.9},
    'leaves': {'color':[.23,.31,.16],'roughness':.94},
    'lamp glass': {'color':[.87,.83,.68],'roughness':.45},
}
HALF=3.24
COLUMN=2.58
COL_Y=1.04
GATE_Y=-.66
REAR_Y=3.98
LOWER=4.44
UPPER=8.78
TOP=12.80

def block(b,name,mat,x,y,z,w,d,h):
    b.box((x,y,z),(w,d,h),mat,label=name)

def surface(b,depth,label):
    return Facade(b,(-HALF,depth),(HALF,depth),label)

def strip(points,width):
    return LineString(points).buffer(width/2,cap_style=2,join_style=2)

def section(b,x,y,profile,material,name,sides):
    """Turn a measured axial profile; the orientation also supports square piers."""
    v=[(x+r*cos(2*pi*k/sides+pi/4),y+r*sin(2*pi*k/sides+pi/4),z)
       for z,r in profile for k in range(sides)]
    faces=[tuple(reversed(range(sides))),tuple(range(len(v)-sides,len(v)))]
    for i in range(len(profile)-1):
        for k in range(sides):
            a=i*sides+k;n=i*sides+(k+1)%sides
            faces.append((a,n,n+sides,a+sides))
    b.add(v,faces,material,name)

def scroll(x,z,r,turn,side,detail):
    pts=[]
    for i in range(21 if detail else 10):
        t=i/(20 if detail else 9)
        angle=turn+t*1.46*pi
        rr=r*(1-.79*t)
        pts.append((x+side*rr*cos(angle),z+rr*sin(angle)))
    return strip(pts,.026 if detail else .033)

def iron_gate(b,detail):
    gate=surface(b,GATE_Y,'garden gate')
    for s in (-1,1):
        left,right=.125,2.43
        top=lambda u:2.26+.40*(1+cos(pi*(u-.48)/2.22))+.11*cos(2*pi*u/2.23)
        beams=[]
        for z,h in [(.17,.06),(.72,.045),(1.16,.044),(2.26,.047)]:
            beams.append(box(left,z-h/2,right,z+h/2))
        beams.extend([box(left-.03,.12,left+.035,top(left)),box(right-.034,.16,right+.028,top(right))])
        count=10
        for i in range(1,count):
            x=left+(right-left)*i/count
            beams.append(box(x-.016,.16,x+.016,top(x)))
            if detail:
                beams.append(Polygon([(x-.05,top(x)-.035),(x,top(x)+.075),(x+.05,top(x)-.035)]))
        pts=[(left+(right-left)*i/30,top(left+(right-left)*i/30))for i in range(31)]
        beams.append(strip(pts,.084))
        for i in range(3 if detail else 2):
            center=left+(i+.52)*(right-left)/(3 if detail else 2)
            for sign in [-1,1]:
                beams.append(scroll(center+sign*.13,.39,.15,-pi/2,sign,detail))
                beams.append(scroll(center+sign*.13,top(center)-.31,.16,0,sign,detail))
                if detail:beams.append(scroll(center+sign*.123,1.26,.09,pi/3,sign,detail))
        if detail:
            arch=[(left,.3),(left+.21,.15),(left+.45,.24),(right-.54,.23),(right-.12,.18),(right,.38)]
            beams.append(strip(arch,.030))
            beams.append(strip([(left,2.38),(.47,2.58),(.81,2.76),(1.12,2.80),(1.52,2.75),(1.94,2.54),(right,2.54)],.038))
        from shapely.affinity import scale
        bars=scale(unary_union(beams),xfact=s,yfact=1,origin=(0,0))
        gate.prism(bars,-.034,.034,'wrought iron',('left' if s<0 else 'right')+' hinged leaf')
        gate.box(s*.24,1.58,.062,.12,.095,.049,'old brass','lock')
        for z in [.45,2.22]:
            gate.box(s*2.47,z,.18,.070,.12,0.,'wrought iron','strap hinge')
        x=s*2.75
        block(b,'garden gate pier','dressed stone',x,GATE_Y,1.50,.55,.61,3.00)
        for z,w,h in [(.14,.64,.23),(2.79,.66,.15),(3.03,.59,.11)]:
            block(b,'garden gate pier caps','light stone',x,GATE_Y,z,w,w,h)
    # Only the unobscured west gatepost in the cited photograph bears a readable globe.
    section(b,-2.75,GATE_Y,[(3.08,.09),(3.15,.11),(3.19,.08)],'old brass','left lamp collar',10)
    section(b,-2.75,GATE_Y,[(3.18,.04),(3.22,.12),(3.32,.17),(3.42,.14),(3.49,.06),(3.50,.01)],'lamp glass','left globe',16 if detail else 9)

def openings(b,detail):
    wall=surface(b,REAR_Y,'inner wall')
    entries=[]
    for x,width,z0,z1 in [(0,1.42,.18,3.66),(-1.53,.85,.42,3.60),(1.53,.85,.42,3.60),
                            (0,1.31,LOWER+.10,7.36),(-1.25,.62,LOWER+.12,7.32),(1.25,.62,LOWER+.12,7.32),
                            (0,1.46,UPPER+.13,11.77),(-1.31,.63,UPPER+.15,11.69),(1.31,.63,UPPER+.15,11.69)]:
        entries.append((x,width,z0,z1,box(x-width/2,z0,x+width/2,z1)))
    shell=box(-HALF,.05,HALF,TOP).difference(unary_union([e[-1]for e in entries]))
    wall.prism(shell,-.24,0,'warm render','pierced rear wall')
    for index,(x,width,z0,z1,hole) in enumerate(entries):
        label=['entrance','loggia','terrace'][index//3]+str(index%3)
        wall.prism(hole.buffer(.012,join_style=2),-.176,-.161,'glass' if index!=0 else 'shadow glass',label+' glazing')
        outline=hole.difference(hole.buffer(-.056,join_style=2))
        transoms=[box(x-width/2,z1-.48,x+width/2,z1-.42)]
        if index%3==0:transoms.append(box(x-.023,z0,x+.023,z1))
        if detail:
            transoms.append(box(x-width/2,z0+.69,x+width/2,z0+.75))
        wall.prism(unary_union([outline,*transoms]),-.11,-.065,'dark joinery',label+' leaves')
        if index//3==2:
            wall.box(x,z1+.12,width+.17,.12,.14,.033,'light stone',label+' lintel')
            if detail:
                arch=LineString([(x+(width*.52)*cos(t*pi/18),z1+.17+width*.25*sin(t*pi/18))for t in range(19)]).buffer(.027)
                wall.prism(arch,.007,.032,'dressed stone',label+' shallow arch mould')
        if index==0:
            for xx in [-.095,.095]:wall.box(xx,1.49,.025,.23,.047,-.035,'old brass','door pulls')
    for zz,depth,height in [(TOP-.22,.22,.18),(TOP-.05,.30,.10)]:
        wall.box(0,zz,HALF*2,height,depth,.042,'dressed stone','upper cornice')
    floor_y=(COL_Y+REAR_Y)/2
    for z,h,label in [(.10,.12,'threshold paving'),(LOWER-.15,.30,'first projecting balcony'),(UPPER-.18,.36,'terrace floor')]:
        y0=COL_Y-.26 if z>.2 else COL_Y-.04
        block(b,label,'light stone',0,(y0+REAR_Y)/2,z,2*HALF,REAR_Y-y0,h)

def columns(b,detail):
    for x in (-COLUMN,COLUMN):
        for floor,top,name in [(.14,LOWER-.26,'entrance'),(LOWER,UPPER-.23,'upper')]:
            block(b,name+' square shaft','warm render',x,COL_Y,(floor+top)/2,.55,.62,top-floor)
            for z,h,ww,mat in [(floor+.07,.14,.72,'dressed stone'),(floor+.17,.10,.62,'light stone'),
                                (top-.17,.19,.58,'dressed stone'),(top-.055,.075,.67,'light stone'),
                                (top+.055,.13,.76,'dressed stone')]:
                block(b,name+' post capital and base',mat,x,COL_Y,z,ww,ww+.04,h)
            if detail:
                face=surface(b,COL_Y-.313,name+' carved post')
                for side in (-1,1):
                    face.prism(strip([(x+side*.23,top-.20),(x+side*.16,top-.30),(x+side*.10,top-.72),(x+side*.06,top-.78)],.024),.004,.025,'dressed stone','foliate flutes')
    front=surface(b,COL_Y-.21,'balcony')
    for z,h,d in [(LOWER-.69,.14,.38),(LOWER-.49,.27,.32),(LOWER-.29,.10,.49),(LOWER-.15,.12,.54),
                   (UPPER-.31,.10,.43),(UPPER-.21,.11,.48),(UPPER-.058,.10,.55)]:
        front.box(0,z,2*HALF,h,d,.035,'dressed stone' if h>.14 else 'light stone','entablature')
    # The pendant is visible above the central double door in the 2017 front view.
    for z,h in [(8.18,.58),(7.85,.10)]:block(b,'pendant chain','wrought iron',0,2.43,z,.021,.021,h)
    section(b,0,2.43,[(7.67,.045),(7.69,.18),(7.76,.30),(7.8,.34),(7.84,.30)],'lamp glass','pendant bowl',20 if detail else 10)

def railings(b,detail):
    for z,layer in [(LOWER,'balcony'),(UPPER,'terrace')]:
        for x in (-COLUMN,COLUMN):
            block(b,layer+' rail square pedestal','dressed stone',x,COL_Y,z+.49,.51,.50,.98)
            block(b,layer+' pedestal cap','light stone',x,COL_Y,z+1.02,.64,.61,.13)
        block(b,layer+' sill','dressed stone',0,COL_Y,z+.11,2*HALF,.36,.20)
    for i in range(15):
        x=-2.44+i*.349
        profile=[(LOWER+.16,.075),(LOWER+.24,.084),(LOWER+.30,.060),(LOWER+.53,.046),
                 (LOWER+.68,.077),(LOWER+.78,.069),(LOWER+.82,.083)]
        section(b,x,COL_Y,profile,'light stone','turned balcony balusters',12 if detail else 6)
    block(b,'balcony coping','light stone',0,COL_Y,LOWER+.88,2*HALF,.34,.15)
    face=surface(b,COL_Y,'terrace iron')
    face.box(0,UPPER+.94,2*HALF,.049,.078,.0,'wrought iron','top rail')
    for n in range(12):
        x=(n-5.5)*.43;z=UPPER+.56
        p=[box(x-.014,z-.35,x+.014,z+.34)]
        if detail:
            p+=[scroll(x+.1,z+.09,.110,0,1,True),scroll(x-.1,z+.09,.110,0,-1,True)]
            p.append(strip([(x-.2,z-.2),(x,z-.31),(x+.20,z-.2)],.017))
        face.prism(unary_union(p),-.016,.017,'wrought iron','open ironwork')
    for floor,layer in [(LOWER,'lower'),(UPPER,'upper')]:
        for n in range(5):
            x=(n-2)*1.02;y=COL_Y-.25;z=floor+.24
            block(b,layer+' stone planter','light stone',x,y,z,.94,.33,.28)
            if detail:
                face=surface(b,y-.169,'planter relief')
                for k in [-1,0,1]:
                    a=x+k*.265
                    face.prism(strip([(a-.095,z),(a,z+.074),(a+.095,z),(a,z-.074),(a-.095,z)],.014),.001,.014,'dressed stone','lozenges')
            for k in range(8 if detail else 3):
                a=x+(.86*(k+.5)/(8 if detail else 3)-.43);zz=z+.17+.037*sin(k*2.48+n)
                block(b,layer+' planter foliage','leaves',a,y,zz,.14,.15,.095)
                section(b,a,y-.015,[(zz+.024,.035),(zz+.060,.079),(zz+.085,.045)],'red blossom',layer+' flower clusters',6 if detail else 4)

def inscription(b):
    # Geometry for the legible Latin lettering in the 2017 beam photograph.
    fonts={'M':[[(0,0),(0,1),(.5,.42),(1,1),(1,0)]],'A':[[(0,0),(.5,1),(1,0)],[(.20,.38),(.80,.38)]],
           'I':[[ (.5,0),(.5,1)]],'S':[[(1,.88),(.76,1),(.2,.94),(0,.74),(.10,.56),(.82,.47),(1,.3),(.86,.07),(.19,0),(0,.12)]],
           'O':[[ (.2,0),(0,.2),(0,.79),(.24,1),(.77,1),(1,.78),(1,.2),(.79,0),(.2,0)]],
           'N':[[ (0,0),(0,1),(1,0),(1,1)]],'D':[[ (0,0),(0,1),(.62,1),(1,.72),(1,.25),(.64,0),(0,0)]],
           'E':[[ (1,1),(0,1),(0,0),(1,0)],[(0,.50),(.74,.50)]],'L':[[ (0,1),(0,0),(1,0)]],
           "'":[[(.40,1),(.37,.79)]],'H':[[(0,0),(0,1)],[(1,0),(1,1)],[(0,.50),(1,.50)]],
           'U':[[(0,1),(0,.22),(.22,0),(.79,0),(1,.22),(1,1)]]}
    face=surface(b,COL_Y-.353,'beam lettering')
    x=-2.22;z=LOWER-.595;paths=[]
    for letter in "MAISON DE L'HUI":
        if letter==' ':x+=.102;continue
        for line in fonts[letter]:paths.append(strip([(x+.128*u,z+.176*v) for u,v in line],.018))
        x+=.167
    face.prism(unary_union(paths),.043,.062,'old brass','raised Latin letters')

def add_building(b,lod=False):
    detail=not lod
    openings(b,detail)
    columns(b,detail)
    railings(b,detail)
    iron_gate(b,detail)
    if detail:inscription(b)
