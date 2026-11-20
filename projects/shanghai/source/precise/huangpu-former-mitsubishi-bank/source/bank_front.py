"""The south portico and street wall of 36 Jiujiang Road as published in 2024."""
from pathlib import Path
import math
import numpy as np
from shapely import affinity
from shapely.geometry import box,LineString
from shapely.ops import unary_union
from photo_architecture import Facade,opening
from sign_lettering import add_facade_lettering
from bank_portico import columns,lions,GRANITE,CUT,BASE,BRONZE

IRON='dark metal window grilles';GLASS='smoky bronze glass';SHADOW='recessed metal spandrels'
GOLD='gold bank sign';JOINT='shadow in ashlar joints';DOOR='dark bronze entrance';ROOF='neutral rear roof'
PALETTE={GRANITE:{'color':[.58,.568,.526],'roughness':.85},CUT:{'color':[.68,.657,.595],'roughness':.83},
 BASE:{'color':[.355,.347,.317],'roughness':.91},BRONZE:{'color':[.165,.136,.096],'metallic':.48,'roughness':.51},
 IRON:{'color':[.101,.105,.099],'metallic':.46,'roughness':.48},GLASS:{'color':[.174,.211,.209],'metallic':.19,'roughness':.34},
 SHADOW:{'color':[.131,.135,.123],'metallic':.29,'roughness':.55},GOLD:{'color':[.71,.44,.107],'metallic':.63,'roughness':.39},
 JOINT:{'color':[.369,.361,.322],'roughness':.88},DOOR:{'color':[.163,.125,.073],'metallic':.34,'roughness':.53},ROOF:{'color':[.333,.346,.344],'roughness':.93}}
HALF=14.193;TOP=20.71;COLUMNS=(-6.55,-2.19,2.19,6.55);TALL=12.65
FONT=Path(__file__).resolve().parent/'fonts/BankFrontLetters.otf'
def panel(f,x,z,w,h,back,front,material,label):
    f.box(x,z,w,h,front-back,(back+front)/2,material,label)

def iron_window(f,x,bottom,width,height,lod,label,decorated=False):
    q=opening(x,bottom,width,height);frame=.060 if decorated else .047
    f.prism(q,-.27,-.241,GLASS,label+'/glazing')
    f.prism(q.difference(q.buffer(-frame,join_style=2)),-.245,-.095,IRON,label+'/frame')
    for dx in (-width/6,width/6):
        panel(f,x+dx,bottom+height/2,frame*.76,height-.075,-.24,-.105,IRON,label+'/upright')
    if not decorated:
        panel(f,x,bottom+height*.68,width,.042,-.241,-.13,IRON,label+'/transom')
        return q
    # Front photographs show raised scroll bands between stacked dark glazing fields.
    for ratio in (.35,.74):
        z=bottom+height*ratio;h=height*.128
        panel(f,x,z,width-.108,h,-.24,-.105,SHADOW,label+'/spandrel')
        for edge in (-1,1):panel(f,x,z+edge*h/2,width-.085,.057,-.13,-.037,IRON,label+'/raised rail')
        if not lod:
            for idx in range(4):
                ux=x+(idx-1.5)*width*.202
                for zsg in (-1,1):
                    ring=[f.point(ux+.137*math.sin(t),z+zsg*(.064+.088*math.cos(t)),-.028)for t in np.linspace(0,math.tau,13)]
                    f.builder.tube(ring,.017,BRONZE,6,label+'/spandrel scrolls')
    if not lod:
        for ux in np.linspace(x-width*.43,x+width*.43,9):
            panel(f,ux,bottom+height*.328,.018,height*.58,-.115,-.087,IRON,label+'/ground security grille')
    return q

def entrance(f,lod):
    x=0;z=.79;w=2.23;height=2.8
    sh=opening(x,z,w,height);q=sh.buffer(.26,join_style=2).difference(sh)
    f.prism(q.intersection(box(-2,z,2,5)),.016,.248,CUT,'central door frame')
    for dx in (-.564,.564):
        panel(f,dx,z+1.36,1.118,2.72,-.48,-.42,DOOR,'bronze door leaf')
        panel(f,dx,z+1.74,.94,1.50,-.413,-.389,GLASS,'bronze door recessed light')
        panel(f,dx,z+.49,.91,.47,-.411,-.387,SHADOW,'bronze door lower panel')
    panel(f,0,3.91,2.88,.42,.025,.215,GRANITE,'historic entrance inscription tablet')
    panel(f,0,4.19,3.02,.12,.015,.279,CUT,'tablet hood')
    if not lod:
        for x0 in np.linspace(-.89,.89,8):
            panel(f,x0,3.90,.070,.105,.216,.235,BASE,'small inset inscription marks')
    return sh

def signage(f,lod):
    panel(f,0,13.08,15.65,.82,-.22,.20,CUT,'bank name lintel')
    add_facade_lettering(f,'中国邮政储蓄银行',.72,13.09,10.70,.66,.215,.269,GOLD,label='gold bank name',font=FONT)
    for j in range(3):
        line=LineString([(-6.39+.14*j,13.24-.14*j),(-5.84+.08*j,13.24-.14*j),(-5.59+.09*j,13.40-.14*j)])
        f.prism(line.buffer(.047,cap_style=2,join_style=2),.215,.276,GOLD,'three wings of postal mark')
    f.prism(LineString([(-5.92,12.83),(-5.37,13.29),(-5.60,13.37)]).buffer(.052,cap_style=2),.215,.275,GOLD,'postal mark diagonal')

def walls(b,lod):
    front=Facade(b,(-HALF,0),(HALF,0),'Street / main face')
    recessed=Facade(b,(-7.9,1.82),(7.9,1.82),'Street / portico recess')
    # Five very tall window bays. The three at centre share the recessed vestibule.
    lower=[box(-7.90,-.08,7.90,TALL)]
    for x in (-11.22,11.22):
        bottom=3.71 if x<0 else 1.00
        lower.append(iron_window(front,x,bottom,2.53,TALL-bottom-.08,lod,'end window',True))
    side_door=opening(-11.22,0,2.10,2.94);lower.append(side_door)
    panel(front,-11.22,1.47,2.08,2.92,-.52,-.47,DOOR,'west secondary door')
    panel(front,-11.22,3.13,2.48,.27,.002,.126,GRANITE,'secondary lintel')
    # Three central triplets have broad middle lights and narrower flanking casements.
    upper1=[(-11.22,1.36),(11.22,1.36)]+[(x+dx,w)for x in (-4.85,0,4.85)for dx,w in [(-1.43,.60),(0,1.37),(1.42,.60)]]
    for x,w in upper1:lower.append(iron_window(front,x,14.25,w,1.62,lod,'upper street casements'))
    wall=front.wall(0,16.68,lower,.31,GRANITE)
    if not lod:
        for z in np.arange(1.04,16.5,.79):
            course=box(-HALF,z-.010,HALF,z+.010).intersection(wall)
            if course.area>.001:front.prism(course,.001,.007,JOINT,'horizontal dressed granite joints')
        for k in range(11):
            z=2.08+k*1.23
            for x in np.arange(-HALF+(.88 if k%2 else 1.73),HALF,2.78):
                joint=box(x-.009,z,x+.009,z+.70).intersection(wall)
                if joint.area>.001:front.prism(joint,.001,.006,JOINT,'vertical masonry joints')
    bays=[entrance(recessed,lod)]
    for x in (-4.36,0,4.36):
        bottom=4.43 if x==0 else 1.14
        bays.append(iron_window(recessed,x,bottom,3.08,TALL-bottom-.28,lod,'tall window',True))
    recessed.wall(.79,TALL,bays,.28,GRANITE)
    for x in (-7.90,7.90):
        b.box((x,.91,(TALL+.74)/2),(.22,1.82,TALL-.74),GRANITE,label='Portico / deep reveals')
    b.box((0,.91,TALL+.08),(15.80,1.82,.16),GRANITE,label='Portico / soffit')
    for z,h,out in [(13.72,.10,.12),(16.52,.13,.20),(16.68,.13,.30),(16.81,.17,.44),(17.01,.16,.57),(17.11,.08,.62)]:
        panel(front,0,z,2*HALF+.06,h,-.27,out,CUT,'stepped main cornice')
    for x in np.arange(-HALF+.18,HALF-.1,.38 if not lod else .76):
        panel(front,x,16.72,.141,.14,.10,.32,CUT,'dentil block')
    upper=Facade(b,(-HALF+.20,.57),(HALF-.20,.57),'Setback top storey')
    holes=[iron_window(upper,x,17.55,w,1.31,lod,'attic casements')for x,w in upper1]
    upper.wall(17.11,TOP,holes,.32,GRANITE)
    for z,h,projection in [(TOP-.14,.21,.11),(TOP,.08,.16)]:
        panel(upper,0,z,upper.length+.03,h,-.24,projection,CUT,'flat roof coping')
    # Close only the short modelled street slab at its rear and ends.
    b.box((0,1.86,TOP-.09),(upper.length,2.59,.18),ROOF,label='Top / short front roof strip')
    b.box((0,1.52,17.03),(2*HALF,3.04,.20),ROOF,label='Cornice / existing front slab')
    b.box((0,3.06,TOP/2),(2*HALF-.40,.21,TOP),GRANITE,label='Rear / interior edge at cut')
    for x in (-HALF+.10,HALF-.10):
        b.box((x,1.52,8.52),(.20,3.04,17.04),GRANITE,label='Return / narrow end')
        b.box((x+(.10 if x<0 else -.10),1.79,18.86),(.20,2.44,3.57),GRANITE,label='Return / upper end')
    signage(front,lod)
    columns(b,front,lod,COLUMNS)
    for x in (-5.00,5.00):
        b.box((x,-.02,.40),(6.92,2.15,.80),BASE,label='Stair / raised side platform')
    b.box((0,.87,.40),(3.10,1.10,.80),BASE,label='Stair / top landing')
    for i in range(5):
        z=.15*(i+1);b.box((0,-1.07+i*.292,z/2),(3.06,.308,z),BASE,label='Stair / five stone treads')
    lions(b,front,lod)
    b.tube([(0,1.72,TOP),(0,1.72,TOP+2.22)],.035,BASE,8,'Roof / flagstaff')
