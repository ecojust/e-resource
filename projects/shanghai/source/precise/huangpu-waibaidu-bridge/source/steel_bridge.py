"""Photograph-informed exterior of Shanghai's two-span Waibaidu Bridge.

Local X runs across the road, Y north along the road, and Z up from the deck.
Member profiles and joint detailing describe the visible silhouette.
"""
import math
from functools import lru_cache
import numpy as np
from shapely.geometry import Polygon

SPAN = 52.12
WIDTH = 18.4
ROAD = 11.2
STEEL = 'soft grey bridge steel'
EDGE = 'pale painted steel edge'
DARK = 'shaded ironwork'
METAL = 'river-side railing'
STONE = 'weathered pier stone'
PALETTE = {
    STEEL: {'color':[.24,.29,.30], 'roughness':.73,'metallic':.30},
    EDGE: {'color':[.41,.46,.46], 'roughness':.72,'metallic':.24},
    DARK: {'color':[.15,.18,.19], 'roughness':.82,'metallic':.25},
    METAL: {'color':[.39,.42,.40], 'roughness':.75,'metallic':.16},
    STONE: {'color':[.42,.39,.33], 'roughness':.94},
    'road surface': {'color':[.19,.20,.20], 'roughness':.98},
    'pedestrian paving': {'color':[.55,.50,.44], 'roughness':.96},
    'stone curb': {'color':[.65,.64,.59], 'roughness':.96},
    'lane paint': {'color':[.80,.80,.75], 'roughness':.92},
    'yellow center marking': {'color':[.78,.62,.26], 'roughness':.92},
}

def member(b, start, end, width, depth, material, name, face_axis=(1,0,0)):
    p=np.asarray(start,float);q=np.asarray(end,float);axis=q-p
    length=np.linalg.norm(axis);axis/=length
    axis0=np.asarray(face_axis,float)
    if abs(np.dot(axis0,axis))>.985:
        axis0=np.array((0.,0.,1.))
    wide=np.cross(axis,axis0);wide/=np.linalg.norm(wide);normal=np.cross(wide,axis)
    b.box((p+q)/2,(depth,width,length),material,basis=[normal,wide,axis],label=name)

@lru_cache(maxsize=8)
def circle(segments):
    return [(math.cos(i*math.tau/segments),math.sin(i*math.tau/segments)) for i in range(segments)]

def rivet(b, x, y, z, side, radius, name):
    ring=circle(8);vertices=[(x,y+radius*cy,z+radius*cz)for cy,cz in ring]+[(x+side*.023,y,z)]
    faces=[(i,(i+1)%len(ring),len(ring))if side>0 else (i,len(ring),(i+1)%len(ring))for i in range(len(ring))]
    b.add(vertices,faces,DARK,name)

def upper_height(pos):
    # The two gently crowned upper chords return to the same height over the central pier.
    t=(pos-1)/9
    return 7.30+1.90*(1-(2*t-1)**2)

def side_truss(b, y0, direction, lod, name):
    x=direction*(ROAD/2+.20);spacing=SPAN/11
    joins={i:(x,y0+i*spacing,upper_height(i)) for i in range(1,11)}
    lower=lambda i:(x,y0+i*spacing,.30)
    def bar(a,c,w,d,label):
        member(b,a,c,w,d,STEEL,name+'/'+label)
    bar(lower(0),lower(11),.43,.36,'continuous lower chord')
    for i in range(1,10):
        bar(joins[i],joins[i+1],.34,.40,'faceted upper chord')
    for i in (1,10):
        base=0 if i==1 else 11
        bar(lower(base),joins[i],.54,.40,'sloped portal end posts')
    for i,top in joins.items():
        bar(lower(i),top,.27,.30,'panel uprights')
        if not lod:
            for h in (.54,top[2]-.32):
                b.box((x,y0+i*spacing,h),(.349,.55,.63),EDGE,label=name+'/upright splice plates')
                for shift in (-.17,.17):
                    for rise in (-.18,.18):
                        rivet(b,x+direction*.177,y0+i*spacing+shift,h+rise,direction,.038,name+'/visible plate fasteners')
    for i in range(1,10):
        bar(lower(i),joins[i+1],.20,.23,'street-side diagonal lattice')
        bar(joins[i],lower(i+1),.20,.19,'crossed panel diagonals')
    return joins

def transverse(b, xhalf, y, h, i, span_name, lod):
    name=span_name+'/over-road frames'
    member(b,(-xhalf,y,h),(xhalf,y,h),.31,.44,STEEL,name,face_axis=(0,1,0))
    bearing=h-.68
    member(b,(-xhalf,y,bearing),(xhalf,y,bearing),.115,.17,DARK,name+'/lower frame edge',face_axis=(0,1,0))
    count=10 if not lod else 6
    for j in range(count):
        x1=(j/count*2-1)*xhalf;x2=((j+1)/count*2-1)*xhalf
        a,bh=(bearing,h-.12)if j%2==0 else(h-.12,bearing)
        member(b,(x1,y,a),(x2,y,bh),.095,.10,EDGE,name+'/open triangular fascia',face_axis=(0,1,0))
    # Visible corner brackets curve into the cross-frame. Roadway stays open beneath them.
    for sign in (-1,1):
        x=sign*xhalf
        curve=[(x-sign*1.32*(1-math.cos(a)),y,bearing-1.50+1.50*math.sin(a))for a in np.linspace(0,math.pi/2,5 if lod else 10)]
        for start,end in zip(curve,curve[1:]):
            member(b,start,end,.13,.16,STEEL,name+'/curved corner brackets',face_axis=(0,1,0))

def footway(b, sign, lod):
    outer=WIDTH/2;inner=ROAD/2
    name=('east' if sign>0 else 'west')+' walkway'
    b.box((sign*(outer+inner)/2,0,.025),(outer-inner,2*SPAN,.25),'pedestrian paving',label=name+'/sidewalk')
    b.box((sign*(inner+.065),0,.14),(.13,2*SPAN,.16),'stone curb',label=name+'/raised curb')
    x=sign*(outer-.10)
    for z,w,h in [(1.36,.072,.10),(.44,.047,.07),(1.19,.044,.052)]:
        b.box((x,0,z),(w,2*SPAN,h),METAL,label=name+'/open handrails')
    n=84;pitch=2*SPAN/n
    for i in range(n+1):
        y=-SPAN+i*pitch
        b.box((x,y,.79),(.078,.082,1.19),METAL,label=name+'/slender balusters')
        if i<n:
            sign0=-1 if i%2 else 1
            z1,z2=(.43,1.19)if sign0<0 else(1.19,.43)
            member(b,(x,y,z1),(x,y+pitch,z2),.041,.045,METAL,name+'/diagonal pedestrian railing')
    k=104 if not lod else 52;interval=2*SPAN/k
    for z in (-.53,-.17):
        b.box((x,0,z),(.23,2*SPAN,.103),EDGE,label=name+'/pierced fascia borders')
    for i in range(k):
        y0=-SPAN+interval*i;y1=y0+interval
        for a,c in [((x,y0,-.35),(x,(y0+y1)/2,-.18)),((x,y0,-.35),(x,(y0+y1)/2,-.52)),((x,(y0+y1)/2,-.18),(x,y1,-.35)),((x,(y0+y1)/2,-.52),(x,y1,-.35))]:
            member(b,a,c,.060 if not lod else .082,.12,EDGE,name+'/open diamond fascia')
    for i in range(23):
        y=-SPAN+i*SPAN/11
        member(b,(sign*(inner+.08),y,-1.03),(x,y,-.29),.17,.26,DARK,name+'/visible sidewalk brackets',face_axis=(0,1,0))

def build_bridge(b,lod):
    b.box((0,0,-.25),(ROAD,2*SPAN,.48),'road surface',label='shared deck/road surface')
    b.box((0,0,.002),(.064,2*SPAN,.015),'yellow center marking',label='shared deck/paint')
    for x in [-ROAD/4,ROAD/4]:
        for i in range(17):
            b.box((x,-SPAN+3.1+6.15*i,.002),(.12,2.72,.015),'lane paint',label='shared deck/paint')
    for sign in (-1,1):footway(b,sign,lod)
    # Model the part of the center pier visible above the river.
    pier=Polygon([(-8.22,-1.78),(8.22,-1.78),(9.32,-.83),(9.55,0),(9.32,.83),(8.22,1.78),(-8.22,1.78),(-9.32,.83),(-9.55,0),(-9.32,-.83)])
    b.plan_prism(pier,-4.72,-1.08,STONE,'central pier/body')
    b.plan_prism(pier.buffer(.20,join_style=2),-1.33,-.87,STONE,'central pier/stepped coping')
    xhalf=ROAD/2+.20
    for y0,name in [(-SPAN,'south span'),(0.,'north span')]:
        for side in (-1,1):side_truss(b,y0,side,lod,name+('/east'if side>0 else'/west'))
        for i in range(1,11):
            y=y0+i*SPAN/11;h=upper_height(i)
            transverse(b,xhalf,y,h,i,name,lod)
            if i<10:
                yn=y+SPAN/11;hn=upper_height(i+1)
                for side in (-1,1):
                    member(b,(side*xhalf,y,h+.04),(-side*xhalf,yn,hn+.04),.12,.13,STEEL,name+'/overhead diagonal lattice',face_axis=(0,0,1))
        for j in range(12):
            y=y0+j*SPAN/11
            b.box((0,y,-.66),(2*xhalf,.20,.69),DARK,label=name+'/visible deck cross beams')
