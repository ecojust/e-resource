from math import pi,sin,cos,radians
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
from shapely.geometry import Polygon,box
ID='hongkou-changzhi-135-canted-brick-arches'
BRICK='Red facing brick in stretcher courses';HOOD='Orange-brown brick moulding';TILE='Dark red weathered cornice edge'
STONE='Flared crown stone';GLASS='Grey-blue glass';TRANS='Dark glass in fanlight';WOOD='Charcoal sash and glazing bars'
REVEAL='Shaded brick reveal';LIGHT='Light red radial brick'
PALETTE={k:dict(color=c,roughness=r) for k,c,r in [(BRICK,[1,1,1],.90),(HOOD,[.466,.241,.156],.90),(TILE,[.348,.176,.117],.89),(STONE,[.572,.308,.204],.86),(LIGHT,[.650,.373,.254],.91),(GLASS,[.237,.271,.292],.48),(TRANS,[.128,.149,.163],.53),(WOOD,[.113,.113,.103],.73),(REVEAL,[.253,.155,.120],.94)]}
ANGLE=radians(17)
SIDE=1.92
CENTRE=.96
RADIUS=.393
SPRING=2.80
SILL=.84

def texture():
    target=Path(__file__).with_name('coursework.png')
    if not target.exists():
        rng=np.random.default_rng(679)
        img=Image.new('RGB',(704,704),(174,134,110));draw=ImageDraw.Draw(img)
        for j in range(55):
            for i in range(-1,19):
                x=i*42+(j%2)*21
                rgb=np.array([159,91,65])+rng.integers(-10,10)+rng.integers(-3,4,3)
                draw.rectangle([x+1,13*j+1,x+40,13*j+11],fill=tuple(rgb.tolist()))
        a=np.asarray(img).astype(float)+rng.normal(0,3,(704,704,1))
        Image.fromarray(a.clip(0,255).astype('uint8')).save(target)
    PALETTE[BRICK]['texture']=str(target)

def projected(u,z,depth):
    return (u*cos(ANGLE),abs(u)*sin(ANGLE)-depth,z)

def arch(c,r,bottom,spring,n):
    arc=[(c+r*cos(a),spring+r*sin(a)) for a in np.linspace(0,pi,n+1)]
    return Polygon([(c-r,bottom),(c+r,bottom)]+arc)

def wedge(c,r,R,a,b):
    return Polygon([(c+rad*cos(angle),SPRING+rad*sin(angle)) for angle,rad in [(a,r),(a,R),(b,R),(b,r)]])

def add_building(b,far=False):
    texture();n=18 if far else 52
    def form(p,back,front,mat,name):
        b.prism(p,back,front,projected,mat,name)
    def rect(x0,x1,z0,z1,back,front,mat,name):
        form(box(x0,z0,x1,z1),back,front,mat,name)
    for side in (-1,1):
        c=side*CENTRE;lo,hi=sorted([0,side*SIDE])
        opening=arch(c,RADIUS,SILL,SPRING,n)
        form(box(lo,0,hi,4.23).difference(opening),-.27,0,BRICK,'Corner bay in stretcher bond')
        form(arch(c,RADIUS-.014,SILL+.015,SPRING,n),-.284,-.263,GLASS,'Two recessed lower panes')
        form(arch(c,RADIUS-.025,SPRING-.012,SPRING,n),-.251,-.240,TRANS,'Semicircular glazed head')
        form(opening.difference(arch(c,RADIUS-.024,SILL+.015,SPRING,n)),-.267,-.051,REVEAL,'Brick reveal and sash border')
        rect(c-.019,c+.019,SILL+.015,SPRING,-.236,-.175,WOOD,'Central vertical sash')
        rect(c-RADIUS+.014,c+RADIUS-.014,SPRING-.041,SPRING+.024,-.236,-.162,WOOD,'Transom below fanlight')
        for a in (pi/4,3*pi/4):
            u=c+.35*cos(a);z=SPRING+.35*sin(a)
            b.tube([projected(c,SPRING,-.203),projected(u,z,-.203)],.013,WOOD,5 if far else 8,'Fanlight spoke')
        count=15 if far else 29
        for i in range(count):
            step=pi/count;gap=.004 if far else .002
            form(wedge(c,RADIUS+.012,.580,i*step+gap,(i+1)*step-gap),-.021,.034,LIGHT if i%4==0 else HOOD,'Radial brick above the round opening')
        form(arch(c,.636,SPRING-.008,SPRING,n).difference(arch(c,.582,SPRING-.010,SPRING,n)),.010,.064,TILE,'Outer rolled semicircular hood')
        form(Polygon([(c-.060,SPRING+.355),(c+.060,SPRING+.355),(c+.123,3.565),(c-.123,3.565)]),.010,.102,STONE,'Projecting flared crown stone')
        for dx in (-.050,.050):
            rect(c+dx-.008,c+dx+.008,3.277,3.532,.099,.111,HOOD,'Upright channel on crown stone')
        rect(c-.158,c+.158,3.530,3.574,.019,.121,TILE,'Keystone head')
        rect(c-RADIUS-.086,c+RADIUS+.086,SILL-.077,SILL+.012,-.051,.097,HOOD,'Projecting red sill')
        for u0,u1 in ((lo,lo+.18),(hi-.18,hi)):
            rect(u0,u1,.15,4.015,-.02,.043,BRICK,'Shallow upright brick pier')
            for base in (.54,2.57,2.82,3.71,3.99):
                rect(u0,u1,base,base+.046,.004,.079,HOOD,'Horizontal course on pier')
        for base,top,front,mat in ((.08,.149,.090,TILE),(.15,.196,.060,HOOD),(3.74,3.777,.062,HOOD),(4.000,4.071,.077,HOOD),(4.070,4.114,.137,TILE),(4.114,4.165,.166,HOOD),(4.166,4.20,.195,TILE)):
            rect(lo,hi,base,top,-.04,front,mat,'Returning cornice or string course')
    for part in b.parts:
        if part['material']==BRICK:
            part['texcoords']=[[(x/cos(ANGLE)+SIDE)/(2*SIDE),z/4.24] for x,y,z in part['vertices']]
