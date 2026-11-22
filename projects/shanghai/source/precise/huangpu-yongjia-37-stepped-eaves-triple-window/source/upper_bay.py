"""Garden side of 37 Yongjia Road after Antigng's photograph of 9 September 2015."""
from math import sin, cos, radians
from pathlib import Path

import numpy as np
from PIL import Image
from shapely.geometry import box, Polygon
from shapely.ops import unary_union

ID = 'huangpu-yongjia-37-stepped-eaves-triple-window'
WALL = 'Warm garden-side roughcast'
ASHLAR = 'Cream staggered corner blocks'
HOOD = 'Pale shallow group hood'
STEEL = 'Dark weathered steel'
GLASS = 'Quiet blue-grey glazing'
SHADOW = 'Shadow behind opening lights'
EDGE = 'Cream fascia and soffit'
TILE = 'Dull dark roof tile'
JOINT = 'Roof edge and horizontal laps'
WATER = 'Painted square leader'
PALETTE = {
    name: dict(color=colour, roughness=roughness) for name, colour, roughness in (
        (WALL, [1,1,1], .97), (ASHLAR,[.83,.82,.72],.91),
        (HOOD,[.89,.87,.77],.88), (STEEL,[.28,.29,.25],.67),
        (GLASS,[.29,.35,.32],.39), (SHADOW,[.12,.14,.135],.75),
        (EDGE,[.75,.74,.66],.89), (TILE,[.30,.27,.245],.94),
        (JOINT,[.20,.19,.175],.92), (WATER,[.56,.57,.52],.71))
}
WINDOWS = [(-.58,-.13),(.085,.69),(.912,1.435)]
SILL, HEAD = .59,2.805

def texture():
    path=Path(__file__).with_name('plaster.png')
    if not path.exists():
        rng=np.random.default_rng(563)
        coarse=Image.fromarray(rng.integers(0,255,(46,53),dtype='u1')).resize((492,456),Image.Resampling.BICUBIC)
        variation=(np.asarray(coarse,float)-127)*.073 + rng.normal(0,2.2,(456,492))
        Image.fromarray(np.clip([195,192,160]+variation[:,:,None],0,255).astype('u1')).quantize(128).save(path)
    PALETTE[WALL]['texture']=str(path)

def panel(b, shape, back, front, material, name):
    b.prism(shape,back,front,lambda x,z,d:(x,-d,z),material,name)

def rect(b,x0,x1,z0,z1,back,front,mat,name):
    panel(b,box(x0,z0,x1,z1),back,front,mat,name)

def roof(b,x0,x1,front,back,z,name,low):
    slope=.48
    def surface(x,y,d):return (x,y,z+slope*(y-front)+d)
    b.prism(box(x0,front,x1,back),-.12,0,surface,TILE,name+' sloping roof plane')
    b.box(((x0+x1)/2,front+.03,z-.12),(x1-x0,.11,.13),EDGE,label=name+' pale fascia')
    for y in np.arange(front+.075,back-.04,.21):
        b.prism(box(x0,y-.018,x1,y+.018),-.006,.025,surface,JOINT,name+' staggered eave courses')
    if not low:
        for row,y in enumerate(np.arange(front+.08,back-.07,.21)):
            for x in np.arange(x0+.12+.105*(row%2),x1-.04,.254):
                b.prism(box(x-.007,y,x+.007,min(back,y+.17)),0,.011,surface,JOINT,name+' tile joint')

def add_building(b,far=False):
    texture()
    holes=[box(x0,SILL,x1,HEAD) for x0,x1 in WINDOWS]
    main=box(-1.21,0,1.82,3.82).difference(unary_union(holes))
    panel(b,main,-.42,0,WALL,'Three narrow openings in the raised bay')
    # The return and the lower eave are cut at the extent visible through the garden.
    b.box((-1.145,.65,1.9),(.13,1.29,3.80),WALL,label='Left return of the taller bay')
    b.box((-1.83,1.04,1.26),(1.3,.42,2.52),WALL,label='Wall behind the lower roof junction')
    for i in range(11):
        bottom=.025+i*.34
        length=.312 if i%2 else .445
        rect(b,-1.225,-1.225+length,bottom,bottom+.322,-.014,.046,ASHLAR,'Alternating front corner block')
        b.box((-1.237,length*.5-.009,bottom+.161),(.05,length,.322),ASHLAR,label='Corner block turned along return')
    arch_centre=.412
    edge=np.linspace(-.77,1.59,19 if far else 49)
    def spring(x): return 2.948+.329*(1-((x-arch_centre)/1.18)**2)
    apron=Polygon([(x,spring(x)) for x in edge]+[(x,spring(x)-.089) for x in edge[::-1]])
    panel(b,apron,-.021,.103,HOOD,'Shallow continuous curved lintel over all three windows')
    for x in (-.757,1.574):
        rect(b,x-.045,x+.045,.505,2.972,-.025,.082,HOOD,'Hood surround lowered to outer jamb')
    for i,(x0,x1) in enumerate(WINDOWS):
        mid=(x0+x1)/2
        rect(b,x0,x1,SILL,HEAD,-.189,-.175,GLASS,'Recessed glass between steel profiles')
        for x in (x0+.012,x1-.012):
            rect(b,x-.012,x+.012,SILL,HEAD,-.178,-.082,STEEL,'Steel outer glazing rebate')
        for z in (SILL+.019,1.294,2.111,HEAD-.02):
            rect(b,x0,x1,z-.018,z+.018,-.176,-.085,STEEL,'Horizontal steel glazing bar')
        rect(b,mid-.011,mid+.011,SILL,HEAD,-.175,-.097,STEEL,'Fine vertical glazing bar')
        if i in (1,2):
            # The two reflected highlights belong to short top-hung lights tilted out.
            angle=radians(18 if i==2 else 13)
            hinge=HEAD-.064
            def tilt(u,v,d):
                return (u,-.108+v*sin(angle)-d*cos(angle),hinge+v*cos(angle)+d*sin(angle))
            for shape,mat in [(box(x0+.035,-.58,x1-.035,0),GLASS),
                              (box(x0+.024,-.60,x1-.024,-.574),STEEL),
                              (box(x0+.024,-.6,x0+.046,0),STEEL),
                              (box(x1-.046,-.6,x1-.024,0),STEEL)]:
                b.prism(shape,0,.018 if mat==STEEL else .007,tilt,mat,'Outward projecting upper light')
        rect(b,x0-.036,x1+.036,.538,.592,-.04,.071,HOOD,'Pale sill beneath individual tall light')
    roof(b,-1.43,2.01,-.206,1.02,3.837,'Upper eave',far)
    roof(b,-2.79,-1.215,.31,1.42,2.547,'Lower junction',far)
    roof(b,-1.28,1.87,-.21,.002,.317,'Lower sill roof',far)
    b.box((-1.287,.16,1.242),(.068,.072,2.40),WATER,label='Painted rain leader at the eave junction')
    for part in b.parts:
        if part['material']==WALL:
            part['texcoords']=[[(x+y+2.8)/5.8,z/4.0] for x,y,z in part['vertices']]
