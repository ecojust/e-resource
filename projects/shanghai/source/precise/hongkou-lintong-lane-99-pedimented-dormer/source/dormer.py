"""The photographed dormer of the registered Lane 99 dwellings."""
from pathlib import Path
from random import Random
import math
from PIL import Image
from shapely.geometry import Polygon, box

PLASTER='Sand coloured render'
FASCIA='Weathered red fascia'
WORN='Muted exposed wood in the painted verge'
COPING='Dull brown coping'
ROOF='Dark warm tiled return'
HOOD='Folded charcoal hood'
IRON='Hood ironwork'
FRAME='Off white window frame'
SHADE='Dark glazing rebate'
GLASS='Grey blue glazing'
FLASH='Folded dark flashing'
PALETTE={label:dict(color=colour,roughness=roughness) for label,colour,roughness in [
 (PLASTER,[.94,.94,.94],.97),(FASCIA,[.45,.255,.20],.94),
 (WORN,[.393,.295,.24],.95),(COPING,[.53,.46,.37],.90),(ROOF,[.320,.19,.145],.93),
 (HOOD,[.245,.235,.21],.62),(IRON,[.17,.15,.13],.75),
 (FRAME,[.82,.81,.76],.66),(SHADE,[.16,.169,.161],.72),
 (GLASS,[.32,.365,.38],.28),(FLASH,[.235,.23,.215],.71)]}

def texture(path):
    if path.exists():return
    rng=Random(427)
    w,h=148,164
    image=Image.new('RGB',(w,h))
    pixels=[]
    for y in range(h):
        for x in range(w):
            k=round(2.6*math.sin(x/17+.5*math.sin(y/21))+2.6*math.cos(y/18+x/44))+rng.randrange(-5,6)
            pixels.append((175+k,158+k,135+k))
    image.putdata(pixels)
    image.save(path,optimize=True)

def face(b,poly,d0,d1,material,label):
    b.prism(poly,d0,d1,lambda x,z,d:(x,-d,z),material,label)

def solid(b,profile,x0,x1,mat,label):
    b.prism(Polygon(profile),x0,x1,lambda y,z,x:(x,y,z),mat,label)

def add_building(b,lod):
    shoulder=1.95
    apex=3.04
    wall=Polygon([(-1.11,-.10),(1.11,-.10),(1.11,shoulder),(0,apex),(-1.11,shoulder)])
    opening=box(-.814,-.005,.814,1.375)
    face(b,wall.difference(opening),-.18,0,PLASTER,'Rendered dormer wall and window reveal')
    for side in (-1,1):
        ends=sorted([side*.95,side*1.11])
        solid(b,[(.16,-.10),(1.06,1.53),(1.06,1.94),(.16,1.94)],*ends,PLASTER,'Short plaster cheek truncated by main roof')
    # The bands mitre at the apex along the two gable slopes.
    for s,leftside in [(-1,'left'),(1,'right')]:
        end=s*1.25
        def run(low,high):
            return Polygon([(0,apex+low),(end,shoulder-.135+low),(end,shoulder-.135+high),(0,apex+high)])
        face(b,run(-.01,.047),-1.09,.04,ROOF,'Visible '+leftside+' tiled return')
        face(b,run(-.065,.106),-.078,.089,FASCIA,'Red '+leftside+' barge fascia')
        face(b,run(.105,.197),-.093,.105,COPING,'Stone coloured '+leftside+' coping')
        # The close view shows irregular weathering in the red facing.
        for k in range(27):
            rng=Random(4270+k+(37 if s>0 else 0))
            u=rng.uniform(.055,1.19)
            z=apex-(apex-shoulder+.135)*u/1.25
            half=rng.uniform(.012,.039)
            off=rng.uniform(-.048,.078)
            patch=Polygon([(s*(u-half),z+off),(s*(u+half*.13),z+off+.019),
                (s*(u+half),z+off-.008),(s*(u+half*.22),z+off-.014)])
            face(b,patch,.0891,.0904,WORN,'Irregular worn flakes in bargeboard paint')
    # The small rounded rise touches both pieces of coping.
    cap=Polygon([(-.10,3.067),(-.09,3.157),(-.06,3.218),(-.015,3.253),(.021,3.256),(.068,3.205),(.088,3.153),(.093,3.08)])
    face(b,cap,-.092,.107,COPING,'Low terminal rise at the ridge')
    for side in (-1,1):
        x=side*.846
        face(b,box(x-.031,-.014,x+.031,1.678),.0005,.023,FASCIA,'Narrow weathered red jamb')
    face(b,opening,-.120,-.105,SHADE,'Recess behind the replacement window')
    for label,poly in [('left jamb',box(-.814,.004,-.738,1.37)),
                       ('right jamb',box(.738,.004,.814,1.37)),
                       ('centre meeting stile',box(-.044,.039,.043,1.332)),
                       ('head',box(-.814,1.294,.814,1.372)),
                       ('bottom rail',box(-.814,.004,.814,.094))]:
        face(b,poly,-.097,-.037,FRAME,'Painted '+label)
    for i,(l,r) in enumerate([(-.738,-.045),(.044,.738)]):
        face(b,box(l,.094,r,1.294),-.096,-.089,GLASS,'Plain glass light '+str(i+1))
        if not lod:
            reveal=box(l,.094,r,1.294).difference(box(l+.015,.111,r-.015,1.280))
            face(b,reveal,-.089,-.078,SHADE,'Narrow gasket '+str(i+1))
    face(b,box(-.84,-.026,.84,.011),-.055,.054,FRAME,'Inclined light bottom lip')
    # A continuous sheet folds down at the front nosing, with a narrow rear upstand.
    solid(b,[(.025,1.61),(.025,1.705),(-.016,1.705),(-.016,1.642),(-.377,1.581),(-.397,1.55),(-.385,1.536),(-.357,1.559)],
          -.891,.891,HOOD,'Shallow folded metal canopy sheet and nosing')
    for side in (-1,1):
        x=side*.859
        face(b,box(x-.027,1.30,x+.027,1.664),.025,.052,IRON,'Canopy wall strap')
        solid(b,[(-.055,1.339),(-.354,1.566),(-.305,1.566),(-.055,1.385)],x-.014,x+.014,IRON,'Canopy side bracket')
        b.tube([(x,-.055,1.324),(x,-.055,1.399)],.022,IRON,sides=7 if lod else 14,label='Canopy bracket foot')
    if not lod:
        for x in (-.556,0,.556):
            solid(b,[(-.012,1.621),(-.354,1.568),(-.354,1.552),(-.012,1.606)],x-.006,x+.006,IRON,'Narrow folded underside seam')
    face(b,box(-1.14,-.16,1.14,-.108),-.10,.073,FLASH,'Dark lower weathering strip')
    b.palette[PLASTER]['texture']=str(Path(__file__).with_name('weathered-render.png'))
    for part in b.parts:
        if part['material']==PLASTER:
            part['texcoords']=[[(x+.39*y+1.18)/2.52,1-(z+.16)/3.45] for x,y,z in part['vertices']]
