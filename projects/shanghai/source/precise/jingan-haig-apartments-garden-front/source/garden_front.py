"""South elevation surveyed in the June 2025 conservation photographs for Haig Court."""
import math
from pathlib import Path
import sys

from shapely.affinity import scale, translate
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[3]
sys.path.insert(0, str(PROJECT / 'source/precise/hongkou-general-post-office/source/common'))
from photo_architecture import Facade
from sign_lettering import add_facade_lettering

RENDER = 'warm sandy render'
FREESTONE = 'buff limestone'
PALE = 'pale coping'
FRAMES = 'dark bronze sashes'
GLASS = 'blue grey glass'
IRON = 'black forged iron'
BRASS = 'aged gold letters'
SHADOW = 'recess plaster'
PAVING = 'dark threshold stone'
BACK = 'neutral section'
ROOF = 'red tile'
JOINT = 'stone joint'
PALETTE = {
    k:dict(color=list(color), roughness=rough, metallic=metal)
    for k,color,rough,metal in [
        (RENDER,(.806,.740,.629),.91,0), (FREESTONE,(.668,.616,.528),.85,0),
        (PALE,(.853,.805,.706),.82,0), (FRAMES,(.124,.135,.129),.47,.27),
        (GLASS,(.259,.342,.374),.28,.26), (IRON,(.139,.145,.133),.59,.32),
        (BRASS,(.608,.465,.245),.37,.49), (SHADOW,(.461,.407,.335),.85,0),
        (PAVING,(.388,.374,.332),.79,0), (BACK,(.601,.583,.530),.90,0),
        (ROOF,(.531,.277,.194),.85,0), (JOINT,(.492,.452,.388),.89,0)]}

HALF = 26.37
REAR = 3.10
BASE = 7.23
FLOOR = 3.46
APEX = 38.00
FONT = HERE/'fonts/HaigGardenSubset.otf'

def arched(x, z, width, height, rise, n):
    """A curved head spanning two straight jambs, drawn in the elevation plane."""
    half = width/2
    spring = z + height-rise
    arc = [(x+half*math.cos(math.pi*k/n), spring+rise*math.sin(math.pi*k/n)) for k in range(n+1)]
    return Polygon([(x-half,z),(x+half,z),*arc])

def panel(f, outline, holes, material, name, face=0):
    solid=outline.difference(unary_union(holes)) if holes else outline
    f.prism(solid,face-.32,face,material,name)
    return solid

def casement(f,x,z,width,height,lod,holes,face=0,rows=3,cols=2,arched_head=0,depth=.19):
    opening=arched(x,z,width,height,arched_head,10 if lod else 20) if arched_head else box(x-width/2,z,x+width/2,z+height)
    holes.append(opening)
    f.prism(opening,face-depth-.025,face-depth,GLASS,'inset panes')
    inner=scale(opening,.965,.961,origin='center')
    f.prism(opening.difference(inner),face-depth+.004,face-depth+.047,FRAMES,'opening frames')
    for j in range(1,cols):
        x0=x-width/2+j*width/cols
        bar=opening.intersection(box(x0-.021,z,x0+.021,z+height))
        f.prism(bar,face-depth+.016,face-depth+.060,FRAMES,'vertical glazing bars')
    if not lod or rows==2:
        for j in range(1,rows):
            z0=z+height*j/rows
            f.box(x,z0,width-.025,.034,.056,face-depth+.044,FRAMES,'horizontal glazing bars')
    return opening

def bay_rail(b,f,x,z,width,lod,face,small=False):
    """The center rail bows beyond the straight iron balcony edge."""
    side=width*.5; projection=.37 if small else .49; n=8 if lod else 14
    points=[]
    for j in range(n+1):
        u=-side+width*j/n
        bulge=projection*max(0.,math.cos(math.pi*u/width))**2
        points.append((x+u,face+.13+bulge))
    ellipse=Polygon([(x-side,face+.035),*points,(x+side,face+.035)])
    b.prism(scale(ellipse,1,-1,origin=(0,0)),z-.105,z+.045,lambda u,y,h:(u,y,h),PALE,'Balconies/curved sill')
    for dz in (.10,.79):
        b.tube([f.point(u,z+dz,d)for u,d in points],.023 if dz<.2 else .034,IRON,5 if lod else 7,'Balconies/handrails')
    bars=7 if lod else 16
    for j in range(bars+1):
        u=-side+width*j/bars
        d=face+.13+projection*max(0.,math.cos(math.pi*u/width))**2
        f.box(x+u,z+.43,.026,.66,.032,d,IRON,'rail balusters')
    # A pale scallop rests below the middle of the railing.
    shell=Polygon([(x-.50,z-.02),(x-.34,z-.23),(x,z-.38),(x+.34,z-.23),(x+.50,z-.02)])
    f.prism(shell,face+.11,face+.31,PALE,'balcony shell consoles')

def large_balcony(b,f,x,z,lod,holes):
    opening=casement(f,x,z+.16,4.20,2.38,lod,holes,cols=3,rows=1,arched_head=.36,depth=.38)
    rim=opening.buffer(.065,quad_segs=3).difference(opening)
    f.prism(rim,-.015,.092,FREESTONE,'balcony reveal')
    bay_rail(b,f,x,z+.18,3.97,lod,.025)

def grouped_sash(f,x,z,lod,holes,count=3,glass_width=.66,height=1.67,face=0):
    spacing=glass_width+.14
    for j in range(count):
        casement(f,x+(j-(count-1)/2)*spacing,z,glass_width,height,lod,holes,face=face,rows=3,cols=2)

def garden_portal(b,f,lod,wall_holes):
    hole=arched(0,.03,3.90,4.66,1.55,18 if lod else 32)
    wall_holes.append(hole)
    # The door is set behind the vestibule, independently of the pierced garden gate.
    door=arched(0,.03,3.01,3.91,1.23,18)
    f.prism(door,-1.36,-1.29,PAVING,'recessed arched doors')
    frame=arched(0,.07,2.75,3.61,1.09,18)
    f.prism(frame,-1.285,-1.24,GLASS,'vestibule glazing')
    f.box(0,1.38,.091,2.57,.09,-1.18,FRAMES,'paired door stiles')
    f.box(0,2.61,2.78,.09,.11,-1.18,FRAMES,'fanlight transom')
    for side in (-1,1):
        for off in (.3,.78):
            f.box(side*off,1.37,.042,2.38,.075,-1.19,FRAMES,'paired door stiles')
        for theta in (.54,1.03):
            b.tube([f.point(0,2.63,-1.16),f.point(side*1.25*math.sin(theta),2.63+1.04*math.cos(theta),-1.16)],.027,FRAMES,6,'Door/fanlight spokes')
    shoulder=[(-3.53,.02),(3.53,.02),(3.53,5.94),(3.13,5.94),(3.09,6.12),
              (2.64,6.14),(2.46,6.25),(2.10,6.33),(1.70,6.42),(1.28,6.66),
              (.87,6.94),(.52,7.12),(.19,7.20),(0,7.20),(-.19,7.20),(-.52,7.12),(-.87,6.94),
              (-1.28,6.66),(-1.70,6.42),(-2.10,6.33),(-2.46,6.25),(-2.64,6.14),(-3.13,6.12),(-3.15,5.94),(-3.53,5.94)]
    outer=Polygon(shoulder)
    gate=outer.difference(hole)
    f.prism(gate,-.06,2.12,FREESTONE,'stone portal and vaulted soffit')
    f.prism(outer.difference(outer.buffer(-.092)).difference(hole),2.121,2.21,PALE,'curved coping')
    ring=hole.buffer(.22,quad_segs=5).difference(hole).intersection(outer)
    f.prism(ring,2.122,2.20,PALE,'stone arch surround')
    for side in (-1,1):
        b.lathe((side*3.00,-2.02),[(5.94,.22),(6.05,.30),(6.13,.22),(6.22,.12),(6.35,.27),(6.48,.29),(6.60,.18),(6.73,.10),(6.78,.035)],PALE,12 if lod else 22,'Portal/urns')
    for text,z,w,h in [('海格公寓',5.15,1.98,.40),('HAIG COURT',4.81,1.87,.20)]:
        add_facade_lettering(f,text,0,z,w,h,2.22,2.258,BRASS,label='cast sign',font=FONT)
    oval=scale(Point(0,6.20).buffer(.35,quad_segs=10),.79,1.08,origin='center')
    f.prism(oval.difference(oval.buffer(-.063)),2.125,2.22,PALE,'portal crest')
    f.box(0,.040,3.89,.080,3.47,.445,PAVING,'portal threshold')

def loggia(b,f,x,lod,holes):
    w=5.15;bottom=2.12;top=5.80
    openings=[]
    for j in (-1,0,1):
        openings.append(arched(x+j*1.55,bottom,1.52,top-bottom,.39,8 if lod else 16))
    big=unary_union(openings).union(box(x-2.305,bottom,x+2.305,top-.62));holes.append(big)
    f.prism(box(x-2.30,bottom,x+2.30,top-.32),-1.64,-1.56,SHADOW,'loggia back')
    f.box(x,bottom-.045,w,.10,1.63,-.80,FREESTONE,'loggia floor')
    for side in (-1,1):
        f.box(x+side*2.30,(bottom+top)/2,.13,top-bottom,1.59,-.78,FREESTONE,'loggia returns')
        cx=x+side*.775
        b.lathe((cx,-.055),[(bottom,.18),(bottom+.08,.20),(bottom+.17,.146),(top-.67,.12),(top-.54,.16),(top-.40,.225),(top-.27,.25)],PALE,10 if lod else 18,'Loggia/Corinthian columns')
        for k in range(4 if lod else 8):
            phi=k*math.tau/(4 if lod else 8)
            v=cx+.15*math.cos(phi);y=-.055+.15*math.sin(phi)
            b.tube([(v,y,top-.65),(cx+.205*math.cos(phi),-.055+.205*math.sin(phi),top-.48)],.042,FREESTONE,5,'Loggia/capital leaves')
    for lift in (.11,1.03):
        f.box(x,bottom+lift,4.63,.035,.066,-.27,IRON,'loggia horizontal railing')
    for j in range(15 if lod else 27):
        count=14 if lod else 26;f.box(x-2.25+j*4.50/count,bottom+.57,.031,.88,.043,-.27,IRON,'loggia iron rods')

def garden_base(b,f,lod):
    holes=[]
    garden_portal(b,f,lod,holes)
    for side in (-1,1):
        loggia(b,f,side*23.34,lod,holes)
        for x in (5.05,9.32,14.52,18.95):
            grouped_sash(f,side*x,4.05,lod,holes,count=2 if x==5.05 else 3,glass_width=.68,height=2.10)
        for x in (5.05,9.32,14.52,18.95):
            grouped_sash(f,side*x,.76,lod,holes,count=2 if x in (5.05,9.32) else 1,glass_width=.74,height=1.38)
    face=panel(f,box(-HALF,.013,HALF,BASE),holes,FREESTONE,'two-storey stone base')
    for j in range(1,10):
        z=j*.745
        joint=face.intersection(box(-HALF,z-.012,HALF,z+.012))
        if joint.area>0:f.prism(joint,.002,.009,JOINT,'limestone bed joints')
    f.box(0,BASE-.07,HALF*2,.18,.29,.13,PALE,'prominent stone base cap')

def residential(b,f,lod):
    for j in range(7):
        z=BASE+j*FLOOR;holes=[]
        for side in (-1,1):
            large_balcony(b,f,side*4.66,z+.27,lod,holes)
            large_balcony(b,f,side*23.40,z+.27,lod,holes)
            grouped_sash(f,side*.81,z+.67,lod,holes,count=1,glass_width=.92)
            grouped_sash(f,side*9.68,z+.63,lod,holes,count=3,glass_width=.73,height=1.93)
            if j%2==1:
                bay_rail(b,f,side*9.68,z+.64,1.23,lod,.018,small=True)
            for outer in (14.12,18.02):
                grouped_sash(f,side*outer,z+.64,lod,holes,count=3,glass_width=.69,height=1.83)
            grouped_sash(f,side*16.07,z+.78,lod,holes,count=1,glass_width=.32,height=1.50)
        panel(f,box(-HALF,z,HALF,z+FLOOR),holes,RENDER,'rendered apartment frontage')
    top=BASE+7*FLOOR
    # End loggia stacks stop below the taller main cornice, visible in the signed conservation image.
    mainhalf=20.74
    heights=[(-mainhalf,-12.07,35.89),(-12.07,-7.24,37.56),(-7.24,7.24,35.92),(7.24,12.07,37.56),(12.07,mainhalf,35.89)]
    for lo,hi,ceiling in heights:
        mid=(lo+hi)/2;apex=abs(mid)>7.24 and abs(mid)<12.07
        outline=box(lo,top,hi,ceiling) if not apex else Polygon([(lo,top),(hi,top),(hi,ceiling-.24),(mid,APEX),(lo,ceiling-.24)])
        holes=[]
        if apex:
            grouped_sash(f,mid,top+.55,lod,holes,count=3,glass_width=.70,height=1.55)
            grouped_sash(f,mid,35.55,lod,holes,count=3,glass_width=.66,height=1.18)
            bay_rail(b,f,mid,top+.53,1.28,lod,.03,small=True)
        elif lo<0<hi:
            for x in (-4.66,4.66):
                balcony=casement(f,x,top+.55,3.94,1.29,lod,holes,depth=.25,cols=4,rows=1)
                bay_rail(b,f,x,top+.55,3.80,lod,.035)
            oval=scale(Point(0,top+.72).buffer(.55,quad_segs=14),.78,1.08,origin='center')
            f.prism(oval,.02,.19,FREESTONE,'crown relief medallion')
            f.prism(oval.difference(oval.buffer(-.09)),.20,.26,PALE,'medallion rim')
            casement(f,0,34.47,13.9,.76,lod,holes,cols=18 if not lod else 10,rows=1)
        else:
            for x in (14.2,18.10):
                side=1 if mid>0 else -1
                grouped_sash(f,side*x,top+.57,lod,holes,count=3,glass_width=.59,height=1.35)
                grouped_sash(f,side*x,34.40,lod,holes,count=3,glass_width=.55,height=.77)
            f.box(mid,34.01,hi-lo+.13,.16,.45,.19,PALE,'exterior eave')
            for j in range(12 if not lod else 6):
                xx=lo+.25+(hi-lo-.50)*j/(11 if not lod else 5)
                b.tube([f.point(xx,33.74,.09),f.point(xx,33.84,.24),f.point(xx,33.98,.38)],.064,PALE,6,'Roof/eaves brackets')
        panel(f,outline,holes,RENDER,'upper registers')
        roof_top=APEX if apex else ceiling
        end=hi-lo
        if apex:
            for left,right in [(lo,mid),(mid,hi)]:
                zl=APEX if left==mid else ceiling-.25;zr=APEX if right==mid else ceiling-.25
                p=Polygon([(left,zl-.10),(right,zr-.10),(right,zr+.015),(left,zl+.015)])
                f.prism(p,-REAR,.14,ROOF,'sloping pediment roof')
        else:
            f.box(mid,ceiling-.08,end+.12,.16,REAR+.40,-REAR/2+.14,ROOF,'roof strip')
        f.box(mid,(roof_top+top)/2,end,.13+roof_top-top,.15,-REAR+.075,BACK,'upper rear section')
    for x in (-23.48,23.48):
        f.box(x,top-.06,5.77,.13,REAR+.20,-REAR/2+.04,PALE,'lower rooftop terrace cap')
    for x in (-20.72,20.72):
        f.box(x,(top+35.89)/2,.13,35.89-top,REAR,-REAR/2,RENDER,'upper outside returns')

def build_garden_front(b,lod):
    f=Facade(b,(-HALF,0),(HALF,0),'South front')
    garden_base(b,f,lod)
    residential(b,f,lod)
    middle=BASE+7*FLOOR
    for x in (-HALF,HALF):
        f.box(x,middle/2,.135,middle,REAR,-REAR/2,RENDER,'shallow end return')
    f.box(0,middle/2,2*HALF,middle,.15,-REAR+.075,BACK,'neutral back section')
