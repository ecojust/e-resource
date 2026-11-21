"""Garden stair of Sande Hall at the former Jewish Hospital in Shanghai.

X follows the south wall from west to east. D increases towards the garden.
The front landing stops at the fanlight wall. Each upper return turns back
toward the central upper terrace, as shown in the two opposing photographs.
"""
from math import cos, pi, sin
from shapely.geometry import LineString, Polygon, box
from shapely.ops import unary_union
from photo_architecture import Facade

PALETTE = {
    'speckled tread': {'color':[.59,.577,.532],'roughness':.92},
    'stone riser': {'color':[.52,.507,.467],'roughness':.96},
    'light coping': {'color':[.757,.733,.668],'roughness':.89},
    'washed concrete': {'color':[.69,.665,.610],'roughness':.97},
    'mineral base': {'color':[.551,.544,.506],'roughness':.97},
    'baluster granite': {'color':[.683,.674,.625],'roughness':.91},
    'fluted edge': {'color':[.605,.595,.555],'roughness':.94},
    'slate joint': {'color':[.374,.364,.332],'roughness':.93},
    'steel edge': {'color':[.107,.114,.107],'roughness':.62,'metallic':.46},
    'charcoal glazing bar': {'color':[.150,.146,.132],'roughness':.64,'metallic':.36},
    'garden glass': {'color':[.186,.237,.230],'roughness':.36,'metallic':.13},
    'recess plaster': {'color':[.62,.594,.547],'roughness':.92},
}
RISES=7
RISE=.166
HALF=RISES*RISE
UPPER=3*HALF
DECK_HALF=2.56
TURN_IN=4.34
TURN_OUT=5.16
GARDEN_HALF=1.51
REAR=0.0
DIVIDER=1.51
WALK_FRONT=2.77
GARDEN_FRONT=4.91
RADIUS=.81
FAN_SILL=HALF+.55
FAN_SPRING=HALF+1.16
ARCH_PLANE=DIVIDER

def block(b,label,mat,x0,x1,d0,d1,z0,z1):
    x0,x1=sorted((x0,x1));d0,d1=sorted((d0,d1))
    b.box(((x0+x1)/2,-(d0+d1)/2,(z0+z1)/2),
          (x1-x0,d1-d0,z1-z0),mat,label=label)

def cross_section(b,label,material,shape,back,front):
    face=Facade(b,(-.5,0),(.5,0),'Sande garden')
    face.prism(shape,back,front,material,label)

def offset_strip(points,width):
    return LineString(points).buffer(width/2,cap_style='flat',join_style='mitre')

def profile_segment(x0,x1,z0,z1,height):
    return Polygon([(x0,z0),(x1,z1),(x1,z1+height),(x0,z0+height)])

def install_fanlight(b,lod):
    # Radius and spring line are read from the actual central, half-level window.
    divisions=20 if lod else 44
    arc=[(RADIUS*cos(pi*k/divisions),FAN_SPRING+RADIUS*sin(pi*k/divisions)) for k in range(divisions+1)]
    aperture=Polygon([(-RADIUS,FAN_SILL),(RADIUS,FAN_SILL),*arc])
    field=box(-DECK_HALF,0,DECK_HALF,UPPER-.105)
    cross_section(b,'central pierced stair wall','washed concrete',field.difference(aperture),ARCH_PLANE-.23,ARCH_PLANE)
    cross_section(b,'inner splayed arch return','recess plaster',aperture.difference(aperture.buffer(-.049)),ARCH_PLANE-.124,ARCH_PLANE-.006)
    frame=aperture.buffer(-.05)
    cross_section(b,'outer steel arch and sill','steel edge',frame.difference(frame.buffer(-.028)),ARCH_PLANE-.108,ARCH_PLANE-.072)
    glass=frame.buffer(-.024)
    cross_section(b,'fixed fan glazing','garden glass',glass,ARCH_PLANE-.139,ARCH_PLANE-.128)
    for name,ratio in [('middle hoop',.652),('inner hoop',.36)]:
        pts=[(ratio*RADIUS*cos(pi*k/divisions),FAN_SPRING+ratio*RADIUS*sin(pi*k/divisions)) for k in range(divisions+1)]
        cross_section(b,name,'charcoal glazing bar',offset_strip(pts,.019),ARCH_PLANE-.121,ARCH_PLANE-.09)
    for k in range(1,8):
        angle=pi*k/8
        inner=0 if k==4 else (.36 if k%2==0 else .652)
        pts=[(r*RADIUS*cos(angle),FAN_SPRING+r*RADIUS*sin(angle)) for r in (inner,.94)]
        cross_section(b,'curved fan spoke '+str(k),'charcoal glazing bar',offset_strip(pts,.019),ARCH_PLANE-.119,ARCH_PLANE-.09)
    # Heavy central meeting stile and two bay subdivisions are independent of the arch bars.
    for i,x in enumerate([-.505,-.254,0,.257,.517]):
        w=.035 if i==2 else .019
        block(b,'rectangular light centre '+str(i),'charcoal glazing bar',x-w/2,x+w/2,ARCH_PLANE-.119,ARCH_PLANE-.083,FAN_SILL+.055,FAN_SPRING)
    for i,z in enumerate([FAN_SILL+.257,FAN_SPRING-.162,FAN_SPRING-.044,FAN_SPRING]):
        thick=.044 if i==2 else .024
        block(b,'steel glazing transom '+str(i),'charcoal glazing bar',-.748,.748,ARCH_PLANE-.12,ARCH_PLANE-.083,z-thick/2,z+thick/2)
    block(b,'projecting sill edge','mineral base',-.825,.825,ARCH_PLANE-.05,ARCH_PLANE+.035,FAN_SILL-.042,FAN_SILL-.009)

def upper_railing(b,lod):
    bases=[(-DECK_HALF,DECK_HALF,UPPER,UPPER)]
    bases.extend([(-TURN_IN,-DECK_HALF,2*HALF,UPPER),(DECK_HALF,TURN_IN,UPPER,2*HALF)])
    for label,(x0,x1,z0,z1) in enumerate(bases):
        for name,y0,y1,h,ht,m in [('kerb',DIVIDER-.155,DIVIDER+.059,0,.117,'mineral base'),
          ('lower sill',DIVIDER-.165,DIVIDER+.062,.118,.059,'light coping'),
          ('handrail body',DIVIDER-.188,DIVIDER+.078,.923,.069,'baluster granite'),
          ('handrail cap',DIVIDER-.203,DIVIDER+.094,.992,.041,'light coping')]:
            cross_section(b,f'{name} span {label}',m,profile_segment(x0,x1,z0+h,z1+h,ht),y0,y1)
        count=14 if label==0 else 5
        for i in range(count+1):
            if label==1 and i==count or label==2 and i==0:continue
            x=x0+(x1-x0)*i/count;floor=z0+(z1-z0)*i/count
            half=.082 if label or i not in (0,count) else .10
            # The photographed supports have straight shafts, with square foot and collar.
            block(b,f'baluster shaft {label}-{i}','baluster granite',x-half,x+half,DIVIDER-.09,DIVIDER+.018,floor+.145,floor+.952)
            block(b,f'baluster foot {label}-{i}','light coping',x-half-.02,x+half+.02,DIVIDER-.108,DIVIDER+.04,floor+.155,floor+.242)
            block(b,f'baluster collar {label}-{i}','light coping',x-half-.014,x+half+.014,DIVIDER-.104,DIVIDER+.033,floor+.842,floor+.918)
            if not lod:
                for k in (-1,1):
                    xx=x+k*half*.55
                    block(b,f'baluster reed {label}-{i} {k}','fluted edge',xx-.006,xx+.006,DIVIDER+.018,DIVIDER+.022,floor+.28,floor+.805)

def add_building(b,lod=False):
    install_fanlight(b,lod)
    # A slab overhead, rather than a solid central block, leaves the fanlight recess open.
    block(b,'upper central landing soffit','washed concrete',-DECK_HALF,DECK_HALF,REAR, DIVIDER,UPPER-.145,UPPER-.034)
    block(b,'upper central landing surface','speckled tread',-DECK_HALF,DECK_HALF,REAR,DIVIDER+.027,UPPER-.035,UPPER)
    for side in (-1,1):
        x=side*DECK_HALF
        block(b,'enclosed central landing end '+str(side),'mineral base',x-.047,x+.047,REAR,DIVIDER,0,UPPER-.145)
    upper_railing(b,lod)
    for i in range(RISES):
        depth=(GARDEN_FRONT-WALK_FRONT)/RISES;front=GARDEN_FRONT-i*depth;top=(i+1)*RISE
        block(b,'entry riser '+str(i+1),'stone riser',-GARDEN_HALF,GARDEN_HALF,front-depth,front,0,top-.032)
        block(b,'entry tread '+str(i+1),'speckled tread',-GARDEN_HALF,GARDEN_HALF,front-depth,front+.012,top-.032,top)
    block(b,'half landing under arched window','speckled tread',-GARDEN_HALF,GARDEN_HALF,DIVIDER,WALK_FRONT,0,HALF)
    # Lower side flights climb away from the window, then return inward to the main terrace.
    for side in (-1,1):
        for direction,z0,a,bx,d0,d1 in [
                ('outer',HALF,GARDEN_HALF,TURN_IN,DIVIDER+.065,WALK_FRONT),
                ('inner',2*HALF,TURN_IN,DECK_HALF,REAR,DIVIDER-.169)]:
            for i in range(RISES):
                x0=side*(a+(bx-a)*i/RISES);x1=side*(a+(bx-a)*(i+1)/RISES)
                height=z0+(i+1)*RISE;tag=f'{side} {direction} {i+1}'
                block(b,'return riser '+tag,'stone riser',x0,x1,d0,d1,0,height-.034)
                block(b,'return tread '+tag,'speckled tread',x0,x1,d0,d1,height-.034,height)
        block(b,'outer turning landing '+str(side),'speckled tread',side*TURN_IN,side*TURN_OUT,REAR,WALK_FRONT,0,2*HALF)
        block(b,'turn landing end wall '+str(side),'washed concrete',side*(TURN_OUT-.13),side*TURN_OUT,REAR,WALK_FRONT,2*HALF,2*HALF+.72)
        block(b,'turn landing end coping '+str(side),'light coping',side*(TURN_OUT-.17),side*(TURN_OUT+.04),REAR,WALK_FRONT,2*HALF+.72,2*HALF+.80)
        # The two garden-level cheeks each have three stepped rectangular capstones.
        intervals=3
        for i in range(intervals):
            step=(GARDEN_FRONT-WALK_FRONT)/intervals;front=GARDEN_FRONT-i*step
            h=.81+i*.317;xx=side*(GARDEN_HALF+.165);t=.16 if i<2 else .18
            block(b,f'garden cheek {side} {i}','washed concrete',xx-t,xx+t,front-step,front,0,h)
            block(b,f'garden coping {side} {i}','light coping',xx-t-.055,xx+t+.055,front-step-.028,front+.034,h,h+.105)
        # Closely cropped upper return parapet, seen from both stair ends.
        for i in range(4):
            x0=GARDEN_HALF+(TURN_IN-GARDEN_HALF)*i/4;x1=GARDEN_HALF+(TURN_IN-GARDEN_HALF)*(i+1)/4
            level=HALF+(i+1)*HALF/4+.53
            block(b,f'outer stair parapet {side} {i}','washed concrete',side*x0,side*x1,WALK_FRONT-.11,WALK_FRONT+.08,0,level)
            block(b,f'outer stair caps {side} {i}','light coping',side*x0,side*x1,WALK_FRONT-.145,WALK_FRONT+.113,level,level+.082)
