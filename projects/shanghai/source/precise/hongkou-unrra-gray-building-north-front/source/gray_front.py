"""Huangpu Road elevation of the former United Nations building, in metres."""
from math import cos, pi
from shapely.geometry import Polygon, box
from shapely.ops import unary_union
from photo_architecture import Facade

ASHLAR = 'warm grey masonry'
STONE = 'light grey fluted stone'
BASE = 'dark grey base stone'
TRIM = 'grey cornice stone'
GLASS = 'smoky blue glass'
METAL = 'dark grey window metal'
DOOR = 'shadowed timber door'
ROOF = 'dark coping'
PALETTE = {name: {'color': color, 'roughness': roughness} for name,color,roughness in [
    (ASHLAR,[.54,.51,.47],.89),(STONE,[.69,.65,.57],.86),(BASE,[.37,.36,.33],.9),
    (TRIM,[.62,.59,.53],.86),(GLASS,[.16,.24,.27],.26),(METAL,[.13,.15,.15],.50),
    (DOOR,[.16,.13,.115],.78),(ROOF,[.30,.31,.30],.88)]}

HALF = 19.64
FACE = 1.30
BACK = 3.33
PILASTERS = tuple((index-2.5)*4.80 for index in range(6))
BAYS = tuple((index-2)*4.80 for index in range(5))
WINGS = (-17.77,-15.47,15.47,17.77)
WINDOW_ROWS = (7.76,12.03,16.29)

def aperture(x,z,width,height):
    return box(x-width/2,z,x+width/2,z+height)

def shaft(section_x, level, face=FACE):
    """Extrude a rectangular engaged pilaster with six concave channels across its face."""
    half=.748
    left,right=section_x-half,section_x+half
    points=[(left,face+.09),(right,face+.09),(right,face-.49)]
    segments=4 if level else 10
    groove_half=.074
    for index in range(5,-1,-1):
        center=section_x+(index-2.5)*.228
        for arc in range(segments+1):
            t=arc/segments
            points.append((center+groove_half*(1-2*t),face-.49+.10*(1-cos(2*pi*t))/2))
    points.append((left,face-.49))
    return Polygon(points)

def pilaster(b,f,x,lod):
    f.box(x,.73,1.75,.37,.88,.24,BASE,'pilaster square plinth')
    f.box(x,1.00,1.60,.19,.81,.21,STONE,'pilaster base fillet')
    profile=shaft(x,lod)
    starts=[1.07,19.43] if lod else [1.07,3.15,5.24,7.29,9.35,11.43,13.53,15.62,17.55,19.43]
    for bottom,top in zip(starts,starts[1:]):
        b.plan_prism(profile,bottom,top-(.016 if not lod else 0),STONE,'giant pilaster / fluted shaft')
    for z,wd,ht,depth in [(19.50,1.59,.18,.83),(19.70,1.70,.22,.94),(19.89,1.79,.16,1.00)]:
        f.box(x,z,wd,ht,depth,.25,TRIM,'pilaster stepped cap')

def window(f,h,columns,lod,category):
    f.window(h,columns=columns if not lod else min(columns,2),rows=2 if not lod else 1,
             frame=METAL,glass=GLASS,trim=False,label=category)
    f.builder.parts.pop()
    left,low,right,_=h.bounds
    f.box((left+right)/2,low-.055,right-left+.16,.10,.31,.025,BASE,category+' sill')

def door(f,h,lod):
    mid=h.centroid.x; left,bottom,right,top=h.bounds
    f.prism(h.buffer(.012,join_style=2),-.80,-.76,DOOR,'recessed street door')
    f.prism(h.buffer(.17,join_style=2).difference(h),-.035,.075,TRIM,'plain portal surround')
    if not lod:
        for sign in (-1,1):
            leaf=aperture(mid+sign*.39,bottom+.42,.61,2.28)
            f.prism(leaf.buffer(.035,join_style=2).difference(leaf),-.755,-.716,BASE,'door leaf beading')
        f.box(mid,(bottom+top)/2,.048,top-bottom,.048,-.717,METAL,'door meeting stile')
    f.box(mid,top-.54,right-left,.10,.12,-.63,METAL,'rectangular overlight rail')

def masonry_joints(f,openings):
    clear=unary_union(openings).buffer(.10,join_style=2)
    strips=[]
    for k in range(1,31):
        z=.39+.78*k
        if any(lo<z<hi for lo,hi in [(6.07,6.72),(19.73,20.71),(24.48,26)]):continue
        strips.append(box(-HALF+.025,z-.009,HALF-.025,z+.009))
        for col in range(-9,10):
            x=col*2.22+(k%2)*1.11
            if abs(x)<HALF-.03: strips.append(box(x-.008,z+.03,x+.008,min(z+.74,24.63)))
    face=unary_union(strips).difference(clear)
    f.prism(face,.002,.011,BASE,'stone block joints')

def add_building(b,lod):
    f=Facade(b,(-HALF,FACE),(HALF,FACE),'Huangpu Road north facade')
    glazing=[];doors=[]
    for x in BAYS:
        if abs(x)<6:
            doors.append(aperture(x,.70,2.40,4.83))
        else:
            glazing.append((aperture(x,2.07,2.55,3.27),2,'ground floor end bay'))
        for z in WINDOW_ROWS:
            glazing.append((aperture(x,z,3.04,2.04),3,'central window'))
    for x in WINGS:
        for z in (1.83,*WINDOW_ROWS):
            glazing.append((aperture(x,z,1.19,2.66),1,'end pavilion single light'))
    for x in (*BAYS,-16.58,16.58):
        for dx in (-.70,.70):
            glazing.append((aperture(x+dx,21.45,1.05,2.10),1,'pair above entablature'))
    holes=doors+[w for w,_,_ in glazing]
    f.wall(.28,24.90,holes,thickness=.42,material=ASHLAR)
    for h,cols,category in glazing:window(f,h,cols,lod,category)
    for h in doors:door(f,h,lod)
    if not lod:masonry_joints(f,holes)
    for x in PILASTERS:pilaster(b,f,x,lod)
    for z,height,depth,mat in [(.24,.47,.40,BASE),(.53,.12,.18,TRIM),
            (6.11,.17,.20,BASE),(6.38,.27,.42,TRIM),(6.62,.12,.53,TRIM),
            (20.05,.22,.42,TRIM),(20.42,.37,.53,TRIM),(20.69,.10,.60,BASE),
            (24.55,.19,.32,TRIM),(24.84,.34,.66,TRIM),(25.12,.18,.82,ROOF)]:
        if 6<z<7:
            for bay in BAYS:
                f.box(bay,z,3.48,height,.58+depth*.35,.02,mat,'short stringcourse between pilasters')
        else:
            f.beam(z,height,depth,mat,width=2*HALF+(0.42 if z>24.5 else 0),label='running stone course')
    # The photograph shows a small stone relief above the central pair. Its inscription is unresolved.
    crest=Polygon([(-.27,24.10),(0,23.90),(.27,24.10),(0,24.32)])
    f.prism(crest,.035,.13,TRIM,'central diamond-shaped attic relief')
    if not lod:
        f.prism(crest.buffer(-.055).difference(crest.buffer(-.105)),.13,.17,STONE,'attic relief raised rim')
    for side in (-1,1):
        b.box((side*(HALF-.17),(FACE+BACK)/2,12.50),(.34,BACK-FACE,25),ASHLAR,label='short cut return')
    b.box((0,BACK-.06,12.48),(2*HALF,.12,24.96),ASHLAR,label='unornamented section back')
    b.box((0,(FACE+BACK)/2,24.96),(2*HALF,BACK-FACE,.21),ROOF,label='capped section')
    for k in range(3):
        step=box(-7.03,FACE-.79+.20*k,7.03,FACE+.16)
        b.plan_prism(step,k*.18,(k+1)*.18,BASE,'three front steps')
