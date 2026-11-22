"""The central projecting entrance of Building 1 at 601 Jiaozhou Road."""
from math import cos, pi, sin
from shapely.geometry import Polygon, box
from shapely.ops import unary_union
from photo_architecture import Facade

PALETTE = {
    'red field brick': {'color': [.65,.36,.26], 'roughness': .93},
    'dark fired brick': {'color': [.50,.26,.19], 'roughness': .96},
    'salmon brick': {'color': [.71,.43,.32], 'roughness': .92},
    'sandstone': {'color': [.75,.66,.52], 'roughness': .86},
    'stone reveal': {'color': [.63,.55,.44], 'roughness': .91},
    'cap stone': {'color': [.67,.63,.55], 'roughness': .84},
    'granite base': {'color': [.51,.49,.45], 'roughness': .91},
    'dark timber': {'color': [.23,.19,.15], 'roughness': .86},
    'painted steel': {'color': [.20,.21,.20], 'metallic': .35, 'roughness': .69},
    'window glass': {'color': [.38,.44,.44], 'roughness': .32},
    'balcony iron': {'color': [.20,.21,.19], 'metallic': .49, 'roughness': .62},
}
HALF_WIDTH = 2.20
SHOULDER = 16.09
APEX = 17.94
ARCH_SPRING = 2.02
ARCH_RADII = (1.29,1.12,.97,.80)
STONE_HEAD = 5.06
BALCONY_SLAB = 13.48

def arch(radius, base=.04, samples=36):
    pts=[(-radius,base),(radius,base)]
    pts.extend((radius*cos(pi*i/samples),ARCH_SPRING+radius*sin(pi*i/samples)) for i in range(samples+1))
    return Polygon(pts)

def glazed_opening(face, x, width, bottom, top, label, lod):
    hole=box(x-width/2,bottom,x+width/2,top)
    frame=hole.buffer(-.026,join_style=2)
    inner=frame.buffer(-.050,join_style=2)
    face.prism(hole.buffer(.008,join_style=2),-.252,-.241,'window glass',label+' glass')
    bars=[]
    if not lod or width>.69:
        bars.append(box(x-.014,bottom,x+.014,top))
    for frac in ([.48] if lod else [.24,.48,.72,.88]):
        z=bottom+(top-bottom)*frac
        bars.append(box(x-width/2,z-.017,x+width/2,z+.017))
    panes=inner.difference(unary_union(bars))
    face.prism(frame.difference(panes),-.204,-.176,'painted steel',label+' sashes')

def portal(f,lod):
    rings=[arch(r,samples=16 if lod else 44) for r in ARCH_RADII]
    stone=box(-HALF_WIDTH,.04,HALF_WIDTH,STONE_HEAD)
    f.prism(stone.difference(rings[0]),-.22,.04,'sandstone','squared stone front')
    for i,(outer,inner) in enumerate(zip(rings,rings[1:])):
        f.prism(outer.difference(inner),-.23-.083*i,.035-.087*i,'sandstone' if i%2==0 else 'stone reveal','receding archivolt '+str(i+1))
    inner=rings[-1]
    lining=inner.difference(arch(ARCH_RADII[-1]-.032,samples=16 if lod else 44))
    f.prism(lining,-.66,-.205,'stone reveal','inner arch soffit')
    for side in [-1,1]:
        x=side*(HALF_WIDTH+ARCH_RADII[-1])/2
        f.box(x,.448,HALF_WIDTH-ARCH_RADII[-1],.80,.09,.085,'granite base','base course '+str(side))
        f.box(x,.886,HALF_WIDTH-ARCH_RADII[-1]+.015,.067,.115,.084,'cap stone','base molding '+str(side))
        for j in ([0] if lod else [0,1]):
            f.box(x+(j-.38)*.42,.425,.016,.73,.014,.138,'stone reveal','ashlar joint '+str(side)+str(j))
    f.prism(inner,-.725,-.69,'dark timber','recessed entrance closure')
    if not lod:
        for x in [-.67,-.45,.45,.67]:
            f.box(x,1.14,.035,2.07,.033,-.661,'dark timber','door upright '+str(x))
        for z in [1.0,2.33,3.68,4.29]:
            cut=box(-HALF_WIDTH,z-.011,HALF_WIDTH,z+.011).difference(rings[0])
            f.prism(cut,.042,.047,'stone reveal','stone bed '+str(z))
        key=Polygon([(-.09,3.37),(.09,3.37),(.13,3.64),(-.13,3.64)])
        f.prism(key,.048,.077,'sandstone','central keystone')
    f.box(0,.047,1.67,.074,.96,-.21,'granite base','door threshold')
    f.box(0,STONE_HEAD,4.49,.15,.38,.036,'cap stone','window apron cornice')

def balcony(f,lod):
    width,reach=1.66,.79
    f.box(0,BALCONY_SLAB,width,.175,reach+.12,reach/2-.02,'cap stone','projecting balcony slab')
    f.box(0,BALCONY_SLAB+.86,width,.046,.046,reach-.04,'balcony iron','front handrail')
    f.box(0,BALCONY_SLAB+.20,width,.036,.036,reach-.04,'balcony iron','front low rail')
    count=7 if lod else 13
    for i in range(count):
        x=width*((i/(count-1))-.5)
        f.box(x,BALCONY_SLAB+.50,.025,.75,.027,reach-.04,'balcony iron','front bar '+str(i))
    for side in [-1,1]:
        x=side*width/2
        f.box(x,BALCONY_SLAB+.86,.048,.046,reach,reach/2-.04,'balcony iron','return rail '+str(side))
        for k in range(2 if lod else 4):
            y=(k+1)*reach/(3 if lod else 5)
            f.box(x,BALCONY_SLAB+.50,.025,.75,.027,y,'balcony iron','side bar '+str(side)+' '+str(k))
    for i in range(3):
        f.box(0,BALCONY_SLAB-.14-i*.059,width*(.55-i*.12),.065,reach*(.57-i*.09),.21-i*.06,'sandstone','stepped balcony underside '+str(i+1))

def add_building(builder,lod=False):
    f=Facade(builder,(-HALF_WIDTH,0),(HALF_WIDTH,0),'school entrance')
    outline=Polygon([(-HALF_WIDTH,.04),(HALF_WIDTH,.04),(HALF_WIDTH,SHOULDER),(.11,APEX),(-.11,APEX),(-HALF_WIDTH,SHOULDER)])
    windows=[];bays=[(-.88,.48),(0,.79),(.88,.48)]
    for row,(bottom,top) in enumerate([(5.22,8.27),(9.50,12.42)]):
        for col,(x,width) in enumerate(bays):
            windows.append((x,width,bottom,top,'s'+str(row+2)+' bay '+str(col+1)))
    windows.append((0,.88,BALCONY_SLAB+.07,15.63,'balcony door'))
    panes=[box(x-width/2,bottom,x+width/2,top) for x,width,bottom,top,_ in windows]
    central=box(-1.32,STONE_HEAD-.05,1.32,12.67)
    brick=outline.difference(unary_union([box(-HALF_WIDTH-.1,0,HALF_WIDTH+.1,STONE_HEAD),central,panes[-1]]))
    f.prism(brick,-.40,0,'red field brick','gable and red brick side piers')
    f.prism(central.difference(unary_union(panes[:-1])),-.27,.014,'sandstone','two floors continuous mullions')
    f.prism(panes[-1].buffer(.096,join_style=2).difference(panes[-1]),-.025,.063,'sandstone','balcony door stone frame')
    for x,width,bottom,top,label in windows:glazed_opening(f,x,width,bottom,top,label,lod)
    if not lod:
        for z in [8.79,.98+8.0]:
            for x in [-.87,0,.87]:f.box(x,z,.13,.075,.018,.026,'stone reveal','spandrel air slot '+str(x)+' '+str(z))
        # Small patches of darker fired bricks keep the photographed red-brick field continuous.
        for row in range(41):
            z=5.35+row*.286
            for side in [-1,1]:
                x=side*(1.55+.28*((row*7)%9)/8)
                piece=box(x-.114,z-.031,x+.114,z+.031).intersection(brick)
                if piece.area>.002:f.prism(piece,.001,.009,'dark fired brick' if row%3==0 else 'salmon brick','fired brick '+str(side)+' '+str(row))
    for sx in [-1,1]:
        side=Polygon([(0,APEX-.04),(sx*HALF_WIDTH,SHOULDER-.045),(sx*(HALF_WIDTH+.037),SHOULDER+.04),(0,APEX+.10)])
        f.prism(side,-.41,.085,'cap stone','gable coping '+str(sx))
        f.box(sx*(HALF_WIDTH-.07),SHOULDER+.02,.22,.12,.52,-.15,'cap stone','shoulder cap '+str(sx))
    for k in range(4):
        w=.19+.037*k
        f.box(0,APEX-.42-k*.207,w,.095,.109,.068,'sandstone','gable tab '+str(k))
    portal(f,lod)
    balcony(f,lod)
