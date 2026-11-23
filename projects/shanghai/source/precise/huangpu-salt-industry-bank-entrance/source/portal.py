"""South-facing stone porch at the Salt Industry Bank, Beijing East Road 280."""
from math import cos, sin, tau, pi
from pathlib import Path
from shapely.geometry import Polygon, box
from shapely.ops import unary_union
from photo_architecture import Facade
from stone import wall_uv
from repeat import repeat_only_texture

STONE='granite facing'
MOULD='warm cornice stone'
LIGHT='pale carved granite'
DOOR='bronze door metal'
GLASS='smoky green panes'
DARK='shadowed window recess'
PALETTE={STONE:{'color':[1.,1.,1.],'roughness':.94,'texture':str(Path(__file__).with_name('salt-granite.png'))},MOULD:{'color':[.642,.615,.550],'roughness':.89},LIGHT:{'color':[.715,.704,.655],'roughness':.88},DOOR:{'color':[.178,.185,.155],'roughness':.76},GLASS:{'color':[.302,.363,.327],'roughness':.3},DARK:{'color':[.101,.120,.113],'roughness':.94}}
HALF=4.14
TOP=6.87

def oval(x,z,a,b,n):
    return Polygon([(x+a*cos(tau*i/n),z+b*sin(tau*i/n)) for i in range(n)])

def arched(x,half,spring,rise,steps):
    crown=[(x+half*cos(pi*i/steps),spring+rise*sin(pi*i/steps)) for i in range(steps+1)]
    return Polygon([(x-half,.06),(x+half,.06),*crown])

def doors(front,far):
    openings=[]
    n=15 if far else 28
    for cx,hw,spring,rise in [(-1.67,.57,2.70,.54),(0,.77,2.88,.62),(1.67,.57,2.70,.54)]:
        shape=arched(cx,hw,spring,rise,n);openings.append(shape)
        front.prism(shape,-.06,-.01,DARK,'Recesses / shadow behind the glazing')
        front.prism(shape.buffer(-.04),.00,.025,GLASS,'Recesses / arch head glazing')
        frame=shape.difference(shape.buffer(-.064))
        front.prism(frame,.028,.12,DOOR,'Recesses / arched bronze jambs')
        for station in [-.52,0,.52]:
            front.prism(box(cx+hw*station-.020,.08,cx+hw*station+.020,spring+rise).intersection(shape),.03,.095,DOOR,'Recesses / double leaf and muntins')
        for height in [.28,.59,1.17,1.72,2.24,spring]:
            front.box(cx,height,2*hw-.045,.035,.062,.064,DOOR,'Recesses / glazing rail')
        front.box(cx,.185,2*hw-.08,.23,.08,.08,DOOR,'Recesses / kick panels')
        front.prism(Polygon([(cx-.086,spring+rise+.03),(cx+.086,spring+rise+.03),(cx+.14,spring+rise+.22),(cx-.14,spring+rise+.22)]),.30,.365,MOULD,'Recesses / stone keystones')
    wall=box(-3.28,0,3.28,4.59).difference(unary_union(openings))
    front.prism(wall,-.98,.30,STONE,'Recesses / triple arched wall')

def portico(front,builder,far):
    rings=[(.10,.365),(.17,.365),(.20,.34),(.246,.358),(.29,.348),(.324,.302),(.39,.288),(.48,.274),(3.89,.235),(3.92,.251),(3.967,.251),(4.00,.24),(4.04,.256),(4.09,.282),(4.15,.323),(4.20,.342),(4.24,.342)]
    for sign in [-1,1]:
        x=2.34*sign
        front.box(x,.065,.82,.13,.81,.98,MOULD,'Columns / square plinths')
        builder.lathe((x,-.98),rings,MOULD,24 if far else 48,'Columns / Tuscan drums and echinus')
        front.box(x,4.30,.77,.14,.74,.98,MOULD,'Columns / square abaci')
        front.box(x,4.45,.85,.18,.88,1.02,STONE,'Beam / blocks over inner columns')
        outer=3.48*sign
        front.box(outer,.11,.98,.22,1.12,.65,MOULD,'Outer piers / squared base')
        front.box(outer,2.15,.82,3.86,2.075,.0575,STONE,'Outer piers / plain square shaft')
        front.box(outer,.11,.82,.22,1.95,-.005,STONE,'Outer piers / returns to original wall')
        for z,h,width,depth in [(4.10,.14,.92,1.11),(4.23,.12,1.03,1.22),(4.40,.22,.94,1.15),(4.56,.09,1.06,1.28)]:
            front.box(outer,z,width,h,depth,.69,MOULD,'Outer piers / capitals under side blocks')
        front.box(outer,4.825,1.15,.40,1.35,.70,STONE,'Beam / outer stone blocks')
        front.box(x,5.29,.60,.34,1.02,1.14,MOULD,'Beam / recessed bracket block')
        for z,width,depth in [(5.12,.49,1.66),(5.20,.54,1.74),(5.40,.62,1.86)]:
            front.box(x,z,width,.10,depth-.40,(depth+.40)/2,LIGHT,'Beam / bracket steps')
    for z,h,width,depth in [(4.49,.17,6.45,1.49),(4.66,.16,6.55,1.55),(4.995,.51,7.70,1.62),(5.33,.17,7.86,1.72),(5.46,.105,7.99,1.83),(5.56,.10,8.28,1.93)]:
        front.box(0,z,width,h,depth+1.06,(depth-.90)/2,MOULD if h<.24 else STONE,'Beam / cornice and frieze')

def guardrail(front,far):
    n=16 if far else 32
    for sign in (-1,1):
        # The 2013 and 2020 facades show two distinct recessed rail panels per side.
        for lo,hi,count,z in [(.53,2.70,5,6.02),(2.84,3.86,2,5.97)]:
            xa,xb=sorted([sign*lo,sign*hi]);panel=box(xa,z-.235,xb,z+.235)
            hslots=[]
            for i in range(count):
                x=xa+(i+.5)*(xb-xa)/count;radius=(xb-xa)/count*.315
                hole=oval(x,z,radius,.137,n);hslots.append(hole)
                ring=oval(x,z,radius+.027,.165,n).difference(hole)
                front.prism(ring,1.91,1.95,LIGHT,'Rail / pierced ring surrounds')
            front.prism(panel.difference(unary_union(hslots)),1.71,1.91,MOULD,'Rail / pierced stone panels')
            for height,h,ext,depth in [(z-.255,.089,.055,1.98),(z+.254,.089,.065,2.015)]:
                front.box((xa+xb)/2,height,xb-xa+ext,h,depth-1.65,(1.65+depth)/2,LIGHT,'Rail / panel caps and sills')
        for x,z,width in [(.515,6.04,.14),(2.77,6.04,.19),(3.93,5.99,.15)]:
            front.box(sign*x,z,width,.68,.35,1.82,MOULD,'Rail / intermediate stone uprights')
            front.box(sign*x,z+.345,width+.08,.09,.43,1.83,LIGHT,'Rail / square post caps')
    medallion=oval(0,6.255,.615,.615,28 if far else 56)
    front.prism(medallion,1.64,1.974,MOULD,'Rail / circular central shield')
    for a,b,d0,d1 in [(.604,.548,1.970,2.024),(.527,.497,1.974,2.002)]:
        front.prism(oval(0,6.255,a,a,n*2).difference(oval(0,6.255,b,b,n*2)),d0,d1,LIGHT,'Rail / shield concentric lips')
    # The shallow central relief is visible, but its identifying detail is indistinct.
    for side in (-1,1):
        ridge=Polygon([(side*.035,6.09),(side*.215,6.17),(side*.302,6.33),(side*.246,6.37),(side*.188,6.245),(side*.035,6.175)])
        front.prism(ridge,1.975,2.005,MOULD,'Rail / shallow relief contours')
    front.box(0,5.695,7.96,.16,.37,1.78,MOULD,'Rail / continuous stone curb')

def add_building(builder,distant=False):
    repeat_only_texture(builder,'salt-granite.png')
    front=Facade(builder,(-HALF,0),(HALF,0),'Salt Bank')
    doors(front,distant);portico(front,builder,distant);guardrail(front,distant)
    for part in builder.parts:
        if part['material']==STONE:
            part['texcoords']=[wall_uv(*v) for v in part['vertices']]
