"""The soldier-brick octagon and dark cross bar at 154 Wuyi Road, from the 2018 street photograph."""
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
from shapely.geometry import Polygon,box
ID='changning-wuyi-154-octagonal-brick-light'
WALL='Terracotta wall in running bond';BRICK='Russet soldier brick';VAR='Brick fired to a deeper colour';JOINT='Recessed pale joint'
REVEAL='Dark red reveal';DARK='Shaded rear of octagonal light';BAR='Brown horizontal rail';EDGE='Top edge of rail'
PALETTE={k:dict(color=c,roughness=r) for k,c,r in [(WALL,[1,1,1],.94),(BRICK,[.501,.244,.169],.92),(VAR,[.447,.195,.143],.94),(JOINT,[.635,.419,.332],.97),(REVEAL,[.259,.142,.109],.92),(DARK,[.022,.033,.039],.71),(BAR,[.136,.103,.090],.74),(EDGE,[.235,.180,.153],.68)]}
CZ=1.12
def texture():
    f=Path(__file__).with_name('red-running-bond.png')
    if not f.exists():
        rng=np.random.default_rng(695);im=Image.new('RGB',(500,400),(185,130,105));draw=ImageDraw.Draw(im)
        for row in range(23):
            for col in range(-1,10):
                x=col*57+(row%2)*28;y=row*18
                c=np.array([135,68,50])+rng.integers(-14,14)+rng.integers(-2,3,3)
                draw.rectangle([x+1,y+1,x+55,y+16],fill=tuple(c.tolist()))
        a=np.asarray(im,dtype=float)+rng.normal(0,3,(400,500,1));Image.fromarray(a.clip(0,255).astype('uint8')).quantize(140).save(f)
    PALETTE[WALL]['texture']=str(f)
def octagon(r):
    short=r*(2**.5-1)
    return np.array([[-short,CZ-r],[short,CZ-r],[r,CZ-short],[r,CZ+short],[short,CZ+r],[-short,CZ+r],[-r,CZ+short],[-r,CZ-short]])
def add_building(b,far=False):
    texture()
    def form(p,d,e,m,name):b.prism(p,d,e,lambda x,z,y:(x,-y,z),m,name)
    outer=octagon(.707);inner=octagon(.556)
    form(box(-1.30,0,1.30,2.44).difference(Polygon(outer)),-.28,0,WALL,'Red running-bond wall')
    ring=Polygon(outer).difference(Polygon(inner))
    form(ring,-.254,-.014,JOINT,'Mortar bed around the eight flat sides')
    for j in range(8):
        k=(j+1)%8
        for brick in range(6):
            a=(brick+.024)/6;c=(brick+.976)/6
            p=[inner[j]*(1-a)+inner[k]*a,inner[j]*(1-c)+inner[k]*c,outer[j]*(1-c)+outer[k]*c,outer[j]*(1-a)+outer[k]*a]
            form(Polygon(p),-.251,.013,VAR if (brick+j)%8==0 else BRICK,'Radiating rectangular brick at one octagon facet')
    form(Polygon(inner).difference(Polygon(octagon(.535))),-.288,-.002,REVEAL,'Shallow octagonal inside edge')
    form(Polygon(octagon(.535)),-.301,-.287,DARK,'Dark field behind the horizontal divider')
    form(box(-.54,CZ-.023,.54,CZ+.023),-.189,-.124,BAR,'Single unbroken dark horizontal bar across opening')
    if not far:form(box(-.538,CZ+.012,.538,CZ+.022),-.130,-.118,EDGE,'Light-catching upper face of rail')
    count=24 if not far else 15
    form(box(-1.3,2.00,1.3,2.29),-.02,.002,JOINT,'Mortar bed for the soldier course below the eave')
    for i in range(count):
        l=-1.30+2.60*i/count;r=-1.30+2.60*(i+1)/count
        form(box(l+.004,2.005,r-.004,2.284),-.014,.017,VAR if i%5==0 else BRICK,'Upright brick in the upper course')
    for part in b.parts:
        if part['material']==WALL:part['texcoords']=[[(x+1.30)/2.60,z/2.44] for x,y,z in part['vertices']]
