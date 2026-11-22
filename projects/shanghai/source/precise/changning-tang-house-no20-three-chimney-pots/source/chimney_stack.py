"""Tang family house at Yuyuan Road, the tall gable flue with three short pots photographed in 2018."""
from math import cos,sin,pi
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
from shapely.geometry import Polygon,box
ID='changning-tang-house-no20-three-chimney-pots'
BRICK='Warm ochre brick with buff pointing';LIGHT='Weathered limestone-colour coping';LIP='Brown shadow line';POT='Pale grey clay pots';MOUTH='Soot-dark flue interior'
PALETTE={k:dict(color=c,roughness=r) for k,c,r in [(BRICK,[1,1,1],.91),(LIGHT,[.739,.700,.589],.93),(LIP,[.384,.357,.316],.90),(POT,[.690,.666,.571],.94),(MOUTH,[.094,.088,.081],.99)]}
def texture():
    f=Path(__file__).with_name('yellow-brown-brick.png')
    if not f.exists():
        rng=np.random.default_rng(691);im=Image.new('RGB',(600,520),(214,184,145));draw=ImageDraw.Draw(im)
        for row in range(37):
            for column in range(-1,16):
                x=column*41+(row%2)*20;y=row*15
                rgb=np.array([184,127,78])+rng.integers(-15,15)+rng.integers(-3,4,3)
                draw.rectangle((x+1,y+1,x+39,y+13),fill=tuple(rgb.tolist()))
        a=np.array(im,dtype=float)+rng.normal(0,4,(520,600,1))
        Image.fromarray(a.clip(0,255).astype('uint8')).quantize(160).save(f)
    PALETTE[BRICK]['texture']=str(f)
def disk(radius,segments):
    return Polygon([(radius*cos(2*pi*i/segments),radius*sin(2*pi*i/segments)) for i in range(segments)])
def add_building(b,far=False):
    texture()
    def form(poly,back,front,mat,label):b.prism(poly,back,front,lambda x,z,d:(x,-d,z),mat,label)
    def segment(a,c,width):
        return Polygon([a,c,(c[0],c[1]-width),(a[0],a[1]-width)])
    # The left pitch climbs to a shoulder immediately against the broad stack.
    # The opposite parapet meets the side of the chimney lower down.
    left=[(-2.30,.28),(-1.02,2.12),(-.73,2.05)]
    right=[(.73,1.76),(2.28,.67)]
    form(Polygon([(-2.30,0),(-.73,0),*reversed(left)]),-.13,.012,BRICK,'Steep gable slope rising to chimney')
    # This side plane is set back from the face of the chimney, as the photographed return shows.
    form(Polygon([(.73,0),(2.28,0),*reversed(right)]),-.40,-.24,BRICK,'Recessed gable against the right return')
    for line,back,front in ((left,-.18,.055),(right,-.44,-.205)):
        for a,c in zip(line,line[1:]):
            form(segment(a,c,.077),back,front,LIGHT,'Stepped light edge capping the brick slope')
    def block(width,depth,z0,z1,mat,label):
        b.prism(box(-width/2,-depth/2, width/2,depth/2),z0,z1,lambda x,y,z:(x,y-.10,z),mat,label)
    block(1.46,.67,0,2.61,BRICK,'Rectangular yellow-brick flue rising through both walls')
    block(1.49,.70,2.61,2.78,LIGHT,'Broad flat stone-coloured band')
    block(1.56,.74,2.78,2.815,LIP,'Dark shadow below cap moulding')
    block(1.63,.78,2.815,2.85,LIGHT,'Lower projecting cap')
    if not far:block(1.65,.79,2.85,2.875,LIP,'Recessed joint below top edge')
    block(1.70,.82,2.875 if not far else 2.85,2.915,LIGHT,'Thin projecting top cap')
    n=18 if far else 40
    for cx in (-.49,0,.49):
        def xy(x,y,z):return(cx+x,y-.10,z)
        bore=disk(.091,n);outer=disk(.134,n)
        b.prism(outer.difference(bore),2.90,3.105,xy,POT,'Short round pot with a real aperture')
        b.prism(disk(.149,n).difference(bore),3.075,3.123,xy,LIGHT,'Distinct rim of one chimney pot')
        b.prism(bore,2.918,2.924,xy,MOUTH,'Depth shade beneath the actual opening')
    for part in b.parts:
        if part['material']!=BRICK:continue
        uv=[]
        for x,y,z in part['vertices']:uv.append([(x+2.31+(y+.1)*1.0)/4.65,z/2.63])
        part['texcoords']=uv
