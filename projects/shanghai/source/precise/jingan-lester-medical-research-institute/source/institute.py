"""The grass-facing south front, two end elevations and U-shaped rear of the 2024 institute."""
import numpy as np
from shapely.geometry import Polygon, box
from photo_architecture import Facade
from front import (BASE, COPPER, DOOR, FLAT, GLASS, PALETTE, RED, STEEL, STONE,
                   lamp, lobby, steel_window, stone_wall, strip)

PEBBLE='washed stone rear render'
PALETTE[PEBBLE]={'color':[.534,.518,.477],'roughness':.93}
PLAN=[(-33.712,0),(33.712,0),(33.658,28.066),(15.917,28.237),
      (16.006,20.655),(-16.900,20.647),(-17.139,29.360),(-33.917,29.198)]
AXES=[9.172,13.093,16.916,20.934,24.995,28.986]
EAVE=15.333


def terrace(b,shape,z,thickness,material,label):
    b.prism(shape,z-thickness,z,lambda x,y,h:(x,y,h),material,label)


def grass_front(b,lod):
    # Separate the widths at each change in height and depth of the granite parapet.
    sections=[(-33.712,-7.02,0,EAVE),(-7.02,-4.07,-.24,17.224),
              (-4.07,4.07,-.71,19.744),(4.07,7.02,-.24,17.224),(7.02,33.712,0,EAVE)]
    for lo,hi,y,h in sections:
        mid=(lo+hi)/2
        f=Facade(b,(lo,y),(hi,y),'South/grass elevation')
        if abs(mid)<1:
            holes=lobby(f,lod)
            for sign in (-1,1):
                f.box(sign*2.38,12.13,.15,13.68,.18,.047,STONE,'stepped tower pilaster')
                f.box(sign*2.23,12.41,.10,13.08,.10,.032,STONE,'pilaster nested arris')
        elif abs(mid)<7:
            holes=[strip(f,np.sign(mid)*5.867-mid,1.12,lod,h=14.90,narrow=True)]
        else:
            holes=[strip(f,np.sign(mid)*axis-mid,2.24,lod,h=13.233)for axis in AXES]
            for axis in AXES:
                for offset in (-1.25,1.25):
                    f.box(np.sign(mid)*axis-mid+offset,7.06,.105,12.73,.15,.04,STONE,'vertical granite arris')
        stone_wall(f,0,h,holes,lod)
        if y<0:
            # The stepped frontal parapets return into the roof behind them.
            depth=3.32 if abs(mid)<1 else 2.64
            terrace(b,box(lo,y,hi,depth),h-.12,.15,FLAT,'Roof/front tower cap')
            for side in (-1,1):
                xx=lo if side<0 else hi
                fside=Facade(b,(xx,y if side>0 else depth),(xx,depth if side>0 else y),'South/tower return')
                fside.wall(0,h,[],.20,STONE)
            back=Facade(b,(hi,depth),(lo,depth),'Roof/tower terrace wall')
            back.wall(EAVE-.49,h,[],.20,STONE)


def west_portal(f,x,lod):
    # The 2024 secondary entrance has a narrower brown door, light surround and tablet.
    hole=box(x-1.0,.10,x+1.0,3.52)
    door=box(x-.70,.10,x+.70,2.73)
    f.prism(door.buffer(.012,join_style=2),-.46,-.418,COPPER,'west timber-coloured double door')
    f.prism(hole.difference(door),-.33,.105,STONE,'west pale stone door surround')
    f.box(x,1.43,.040,2.60,.07,-.377,STEEL,'west door centre seam')
    f.box(x,3.14,1.58,.46,.12,.101,FLAT,'tablet above west entrance')
    for sign in (-1,1):
        lamp(f.builder,f,x+sign*1.66,.88,0,lod)
    for k in range(2):
        depth=1.15-k*.33;height=.095*(k+1)
        f.box(x,height/2,2.48,height,depth,depth/2+.15,BASE,'west entry steps')
    return hole


def end_wall(f,lod,western):
    holes=[]
    if western:
        for x in (-11.6,11.5):
            holes.append(strip(f,x,1.04,lod,narrow=True))
        for x in (-8.33,-.94,.94,4.95,8.26):
            holes.append(strip(f,x,1.76 if abs(x)>1.0 else 1.24,lod))
        # The end elevation has a paired narrow strip beside the secondary entrance.
        # The measured secondary door is beneath the wide strip left of the pair.
        x=-4.24
        holes.append(west_portal(f,x,lod))
        for a,c in ((5.40,8.28),(10.38,13.23)):
            holes.append(steel_window(f,x,a,1.76,c-a,lod,cols=2))
        for lo,hi in ((3.76,5.40),(8.28,10.38)):
            panel=box(x-.88,lo,x+.88,hi)
            holes.append(panel)
            f.prism(panel,-.34,-.14,STEEL,'west dark window spandrels')
    else:
        for x in np.linspace(-f.length*.344,f.length*.344,6):
            holes.append(strip(f,x,1.82,lod))
    stone_wall(f,0,EAVE,holes,lod)


def rear_wall(f,lod,bays):
    # Northern windows are set in washed-stone walls, as specified by the project architect.
    holes=[]
    for x in np.linspace(-f.length/2+f.length/(2*bays),f.length/2-f.length/(2*bays),bays):
        for i,z in enumerate((.87,5.64,10.24)):
            holes.append(steel_window(f,x,z,1.58,2.36 if i==0 else 2.55,lod,cols=2))
    f.wall(0,EAVE,holes,.35,PEBBLE)
    f.beam(EAVE-.06,.12,.10,PEBBLE)


def model(b,lod):
    plan=Polygon(PLAN)
    terrace(b,plan,.11,.11,BASE,'Base/original U-shaped building')
    grass_front(b,lod)
    end_wall(Facade(b,PLAN[1],PLAN[2],'East/side elevation'),lod,False)
    end_wall(Facade(b,PLAN[-1],PLAN[0],'West/side elevation'),lod,True)
    for i,count in [(2,4),(3,2),(4,8),(5,2),(6,4)]:
        rear_wall(Facade(b,PLAN[i],PLAN[i+1],'North/washed stone walls'),lod,count)
    terrace(b,plan.buffer(-.15,join_style=2),EAVE-.39,.20,FLAT,'Roof/flat main terrace')
    # The 2024 high oblique records a low glazed penthouse and dark linear equipment bank.
    for x in (-14.1,13.9):
        b.box((x,10.00,EAVE+.57),(9.65,5.77,1.94),STONE,label='Roof/low screened penthouse')
        b.box((x,10.00,EAVE+1.61),(9.92,6.03,.18),FLAT,label='Roof/penthouse slab')
        top=Facade(b,(x-4.82,7.105),(x+4.82,7.105),'Roof/clerestory')
        for xx in np.linspace(-3.76,3.76,6):
            top.box(xx,EAVE+.63,1.05,1.17,.082,.07,GLASS,'penthouse lights')
    b.box((-.17,12.18,EAVE+.86),(16.38,3.40,2.23),STEEL,label='Roof/long dark service enclosure')
    b.box((-.17,12.18,EAVE+2.00),(16.55,3.54,.12),FLAT,label='Roof/service enclosure cap')
    assert all(len(part['label'].encode('utf-8')) <= 63 for part in b.parts), 'Blender object labels must retain their full names.'
