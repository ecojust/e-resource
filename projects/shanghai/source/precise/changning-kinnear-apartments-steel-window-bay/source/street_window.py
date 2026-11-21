"""One upper-floor bay of Kinnear Apartments, from Antigng's April 2014 street photograph."""
from pathlib import Path
from random import Random
from PIL import Image
from shapely.geometry import box, Polygon
from shapely.ops import unary_union

PLASTER = 'Warm pale roughcast'
MORTAR = 'Muted lime mortar'
BRICK = ['Light red face brick', 'Dark russet face brick', 'Warm brown face brick']
STEEL = 'Dark painted steel'
GASKET = 'Recessed glass bead'
GLASS = ['Smoky blue glass', 'Slate coloured glass', 'Muted green grey glass']
STONE = 'Grey stone sill and head'
GROOVE = 'Shadowed cornice groove'
PALETTE = {
    PLASTER: dict(color=[1,1,1],roughness=.93), MORTAR:dict(color=[.59,.52,.49],roughness=.95),
    STEEL:dict(color=[.21,.218,.213],roughness=.69), GASKET:dict(color=[.128,.137,.139],roughness=.8),
    STONE:dict(color=[.51,.505,.47],roughness=.84), GROOVE:dict(color=[.29,.29,.27],roughness=.92),
}
for label,rgb in zip(BRICK,[[.60,.44,.375],[.53,.365,.335],[.56,.41,.37]]):PALETTE[label]=dict(color=rgb,roughness=.92)
for label,rgb in zip(GLASS,[[.245,.278,.31],[.265,.29,.31],[.23,.26,.263]]):PALETTE[label]=dict(color=rgb,roughness=.36)
LEFT,RIGHT=-1.28,1.45
OPEN_LEFT,OPEN_RIGHT=-.79,1.15
SILL,HEAD=.51,1.93
TRANSOM=1.63
COLUMN=(OPEN_RIGHT-OPEN_LEFT)/12
BASE=SILL+.035
BRICK_H=(HEAD-SILL)/14

def texture(path):
    grain=path.with_name('brick-grain.png')
    if not grain.is_file() or not grain.stat().st_size:
        rng=Random(1932);image=Image.new('RGB',(256,256));pixels=[]
        for i in range(256*256):
            m=round(rng.gauss(0,13))
            if rng.random()<.022:m+=rng.randint(22,44)
            pixels.append(tuple(max(130,min(255,v+m)) for v in (224,215,207)))
        image.putdata(pixels);image.save(grain,'PNG')
    if path.is_file() and path.stat().st_size:return
    rng=Random(1375);out=Image.new('RGB',(128,128))
    out.putdata([tuple(c+n for c in (216,214,203))for n in [max(-9,min(9,round(rng.gauss(0,3)))) for _ in range(128**2)]])
    out.save(path,'PNG')

def add_building(builder,lod):
    def panel(shape,back,front,material,label):
        builder.prism(shape,back,front,lambda x,z,d:(x,-d,z),material,label)

    # White continuous spandrels and the terminal jamb are a single surface.
    plaster=unary_union([box(LEFT,0,RIGHT,SILL),box(LEFT,HEAD,RIGHT,2.34),box(OPEN_RIGHT, SILL,RIGHT,HEAD)])
    panel(plaster,-.25,0,PLASTER,'Pale spandrels and end reveal')
    panel(box(LEFT,SILL,OPEN_LEFT,HEAD),-.22,.001,MORTAR,'Bed below fourteen visible brick courses')
    # The photographed pier has staggered joints and small ledges at each bed joint.
    index=0
    for row in range(14):
        z=SILL+row*BRICK_H
        start=LEFT-.17*(row%2)
        while start<OPEN_LEFT:
            lo=max(LEFT,start+.004);hi=min(OPEN_LEFT,start+.312)
            if hi-lo>.015:
                shape=box(lo,z+.004,hi,z+BRICK_H-.004)
                if not lod:shape=shape.buffer(-.002,join_style=2).buffer(.002,quad_segs=1)
                panel(shape,-.005,.016,BRICK[(row+index)%3],f'Face bricks course {row+1:02d}')
                index+=1
            start+=.320
    # Mouldings have real stepped side profiles, visible in the oblique view.
    for z,label in ((SILL,'Sill'),(HEAD,'Window head')):
        profile=[(-.055,-.030,.054,STONE),(-.030,-.018,.071,STONE),(-.018,-.010,.047,GROOVE),
                 (-.010,.005,.092,STONE),(.005,.014,.060,GROOVE),(.014,.036,.097,STONE)]
        for lo,hi,depth,mat in profile:
            panel(box(LEFT+.003,z+lo,RIGHT-.085,z+hi),-.018,depth,mat,label+' profiled band')
    x0,x1=OPEN_LEFT,OPEN_RIGHT
    panel(box(x0,SILL,x1,HEAD),-.205,-.19,GASKET,'Dark backing behind glazing')
    edge=box(x0+.005,BASE,x1-.005,HEAD-.028)
    inner=box(x0+.038,BASE+.031,x1-.038,HEAD-.060)
    panel(edge.difference(inner),-.175,-.082,STEEL,'Outer painted steel frame')
    for course in range(5):
        z0,z1=(TRANSOM+.017,HEAD-.049) if course==4 else (BASE+course*(TRANSOM-BASE)/4+.007, BASE+(course+1)*(TRANSOM-BASE)/4-.007)
        for col in range(12):
            xlo=x0+col*COLUMN+.004;xhi=x0+(col+1)*COLUMN-.004
            panel(box(xlo,z0,xhi,z1),-.172,-.153,GLASS[(course//2+col//3)%3],f'Glazed lights row {course+1}')
    for i in range(1,12):
        x=x0+i*COLUMN
        # Three paired sash meetings stop at the transom; the thinner bar above continues its grid.
        main=i%3==0;wide=.020 if main else .007
        panel(box(x-wide,BASE,x+wide,TRANSOM),-.157,-.067 if main else -.11,STEEL,'Lower meeting stiles' if main else 'Slender lower glazing bars')
        panel(box(x-.007,TRANSOM+.010,x+.007,HEAD-.048),-.158,-.109,STEEL,'Bars across the top light')
        if main and not lod:
            panel(box(x+.011,BASE+.020,x+.017,TRANSOM-.020),-.065,-.061,GASKET,'Shadow line at the meeting stile')
    for n in range(1,4):
        z=BASE+n*(TRANSOM-BASE)/4
        for sash in range(4):
            lo=x0+sash*3*COLUMN+.008;hi=x0+(sash+1)*3*COLUMN-.008
            panel(box(lo,z-.008,hi,z+.008),-.154,-.111,STEEL,'Horizontal bars of four separate lower sashes')
    panel(box(x0+.005,TRANSOM-.017,x1-.005,TRANSOM+.017),-.165,-.065,STEEL,'Full width transom')
    builder.palette[PLASTER]['texture']=str(Path(__file__).with_name('roughcast.png'))
    for label in BRICK:builder.palette[label]['texture']=str(Path(__file__).with_name('brick-grain.png'))
    for p in builder.parts:
        if p['material'] in BRICK:p['texcoords']=[[(x-LEFT+.05*y)/.5,(z-SILL)/.49]for x,y,z in p['vertices']]
        if p['material']==PLASTER:p['texcoords']=[[(x-LEFT+.055*y)/(RIGHT-LEFT),(z+.021)/2.37] for x,y,z in p['vertices']]
