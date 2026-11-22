"""Street-photo study of the garden gable and its later louvred window enclosure."""
from math import sin,cos,pi
from pathlib import Path
import numpy as np
from PIL import Image
from shapely.geometry import box,Polygon,LineString
from shapely.ops import unary_union
ID='huangpu-fuxing-563-gable-timberwork'
WALL='Ochre roughcast';BEAM='Dark stained framing';EDGE='Weathered timber verge';UNDER='Deep eaves soffit';CASING='Light garden window frame';PANE='Leaf reflected in glass';SHADE='Unlit pane';LOUVRE='Cream painted metal louvres';SIDE='Louvre end frame';BRACKET='Grey metal strut';ROOF='Dark red roof edge';FLASH='Pale weathered roof lip'
PALETTE={k:dict(color=c,roughness=r)for k,c,r in [(WALL,[1,1,1],.99),(BEAM,[.179,.121,.103],.89),(EDGE,[.271,.170,.156],.89),(UNDER,[.117,.089,.086],.98),(CASING,[.718,.720,.661],.67),(PANE,[.256,.340,.292],.34),(SHADE,[.184,.239,.211],.36),(LOUVRE,[.712,.686,.563],.83),(SIDE,[.647,.624,.535],.83),(BRACKET,[.331,.342,.326],.77),(ROOF,[.377,.226,.188],.94),(FLASH,[.513,.464,.403],.81)]}
def texture():
    p=Path(__file__).with_name('plaster.png')
    if not p.exists():
        rng=np.random.default_rng(551);a=np.asarray(Image.fromarray(rng.integers(0,255,(81,86),dtype='u1')).resize((512,444),Image.Resampling.BICUBIC),float)
        v=(a-127)*.104+rng.normal(0,5.1,a.shape);Image.fromarray(np.clip([171,156,115]+v[:,:,None],0,255).astype('u1')).quantize(128).save(p)
    PALETTE[WALL]['texture']=str(p)
F=lambda x,z,d:(x,-d,z)
def fill(b,polygon,back,front,mat,label):
    b.prism(polygon,back,front,F,mat,label)
def rect(b,x0,x1,z0,z1,back,front,m,name):
    fill(b,box(x0,z0,x1,z1),back,front,m,name)
C=.08
def elevation(x):return 4.53-abs(x)*.730
def strip(b,pts,width,back,front,m,label):
    fill(b,LineString(pts).buffer(width/2,cap_style=2,join_style=2),back,front,m,label)
def add_building(b,far=False):
    texture()
    face=Polygon([(-2.96,0),(2.96,0),(2.96,elevation(2.96)),(0,4.53),(-2.96,elevation(-2.96))])
    opening=box(C-.463,2.30,C+.463,3.43)
    fill(b,face.difference(opening),-.314,0,WALL,'Ochre gable plane with recessed central opening')
    fill(b,box(-2.151,2.83,2.151,2.96).difference(opening),-.014,.063,BEAM,'Horizontal dark cross rail stops at the two sash jambs')
    for x in (-1.634,-1.188,-.74,.747,1.226,1.636):
        fill(b,box(x-.054,2.917,x+.055,4.55).intersection(face),-.012,.068,BEAM,'Vertical stud from cross rail to inclined verge')
    for x in (C-.524,C+.52):
        rect(b,x-.06,x+.06,2.80,elevation(x)-.048,-.018,.107,BEAM,'Dark post on either side of the white sash')
    rect(b,-.958,.936,3.47,3.600,-.015,.078,BEAM,'Short horizontal rail above window')
    # The left curved brace follows the visible arc before the upper tree canopy.
    points=[(-.58+.59*sin(q*pi*.48),3.912-.36*(1-cos(q*pi*.5)))for q in np.linspace(0,1,9 if far else 23)]
    strip(b,points,.096,-.012,.084,BEAM,'Single visible curved brace above the left sash')
    rect(b,-.05,.048,3.527,4.516,-.013,.078,BEAM,'Short central king post')
    for a,z in [(-1,'Left'),(1,'Right')]:
        ends=[(a*3.14,elevation(3.14)),(0,4.53)]
        strip(b,ends,.205,-.286,.289,UNDER,z+' deep roof soffit')
        strip(b,[(x,y+.014)for x,y in ends],.160,.287,.338,EDGE,z+' sloping front verge board')
        strip(b,[(x,y+.101)for x,y in ends],.068,-.295,.348,ROOF,z+' thin reddish roof covering')
        strip(b,[(x,y+.142)for x,y in ends],.031,-.286,.351,FLASH,z+' upper roof edge')
        if not far:
            strip(b,[(x,y-.053)for x,y in ends],.013,.336,.343,BEAM,z+' timber edge joint')
    for i,(l,r)in enumerate([(C-.424,C-.024),(C+.010,C+.423)]):
        rect(b,l,r,2.363,3.379,-.145,-.134,PANE if i else SHADE,'Separate panes of the photographed window')
    for x in (C-.45,C-.008,C+.45):
        rect(b,x-.023,x+.023,2.30,3.425,-.140,-.075,CASING,'Sash jamb and central white glazing bar')
    for z in (2.326,3.405):rect(b,C-.471,C+.475,z-.024,z+.024,-.148,-.079,CASING,'Sash rail')
    rect(b,C-.551,C+.545,2.236,2.304,-.116,.077,BEAM,'Dark timber window sill')
    # Folded blade sections are extruded across the face, leaving air between them.
    for j in range(8):
        z=1.664+j*.097
        yz=Polygon([(-.620,z+.050),(-.614,z+.065),(-.487,z+.002),(-.499,z-.007)])
        b.prism(yz,C-.552,C+.559,lambda y,z,x:(x,y,z),LOUVRE,'Sloping blade with an open gap behind it')
    for x in (C-.587,C+.591):
        rect(b,x-.025,x+.025,1.572,2.443,.560,.636,SIDE,'Vertical end of shallow projecting louvre cage')
        for z in (1.592,2.418):rect(b,x-.023,x+.023,z-.018,z+.018,.012,.63,SIDE,'Short horizontal side return')
        pts=[(x,-.02,1.37),(x,-.593,1.595)]
        b.tube(pts,.017,BRACKET,6 if far else 12,'Inclined strut from the wall to the louvre base')
    for z in (1.594,2.418):rect(b,C-.606,C+.615,z-.025,z+.025,.573,.644,LOUVRE,'Top or bottom front rail of the louvre cage')
    if not far:
        for x in (C-.45,C+.45):
            rect(b,x-.012,x+.012,1.634,2.390,.486,.492,SIDE,'Narrow support behind sloping blades')
    for part in b.parts:
        if part['material']==WALL:part['texcoords']=[[(x+3.1)/6.2,z/4.68]for x,y,z in part['vertices']]
