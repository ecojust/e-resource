"""Gabled attic balcony photographed at Lane 949, West Yan'an Road."""
from math import cos, pi, sin
from pathlib import Path

import numpy as np
from PIL import Image
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union

HERE=Path(__file__).resolve().parent
TIMBER='Red painted balcony boards'
EDGE='Worn crimson edging'
GRAIN='Dark exposed wood'
WALL='Pale textured infill'
GREEN='Dark green soffit boards'
FLOOR='Pale balcony soffit'
CAME='Ivory casement wood'
GLASS='Recessed charcoal glass'
METAL='Thin iron railing'
TILE='Weathered clay tile'
PALETTE={n:dict(color=c,roughness=r) for n,c,r in [
    (TIMBER,[.43,.105,.095],.83),(EDGE,[.51,.15,.115],.85),(GRAIN,[.24,.081,.064],.85),
    (WALL,[.83,.78,.67],.95),(GREEN,[.085,.157,.134],.91),(FLOOR,[.72,.67,.57],.93),
    (CAME,[.88,.82,.68],.81),(GLASS,[.11,.16,.15],.40),(METAL,[.20,.11,.088],.64),
    (TILE,[.35,.17,.105],.96)]}
SLOTS=np.linspace(-2.99,2.99,51)
JOISTS=np.linspace(-2.80,2.80,9)
WIDTH=3.23

def texture():
    path=HERE/'painted-wood.png'
    if not path.exists():
        rng=np.random.default_rng(467)
        yy,xx=np.mgrid[:176,:288]
        long=(np.sin(yy*.32+np.sin(xx*.019)*.85)+.33*np.sin(yy*.76))
        grain=229+4*long+rng.normal(0,2.2,xx.shape)
        image=np.stack((grain+.8,grain,grain-.5),axis=-1)
        Image.fromarray(np.uint8(np.clip(image,0,255))).quantize(80).save(path)
    PALETTE[TIMBER]['texture']=str(path)

def prism(b,outline,y0,y1,material,label):
    b.prism(outline,-y1,-y0,lambda x,z,d:(x,-d,z),material,label)
    if material==TIMBER:
        part=b.parts[-1]
        part['texcoords']=[[(x+3.8)/7.6,z/3.15] for x,y,z in part['vertices']]

def rect(b,l,r,bottom,top,y0,y1,material,label):
    prism(b,box(l,bottom,r,top),y0,y1,material,label)

def bar(b,a,c,width,y0,y1,material,label):
    prism(b,LineString([a,c]).buffer(width/2,cap_style=2),y0,y1,material,label)

def return_board(b,side,y0,y1,x_at_wall,x_at_front,low,high,material,label):
    x0,x1=x_at_front*side,x_at_wall*side
    b.add([(x0,y0,low),(x1,y1,low),(x1,y1,high),(x0,y0,high),
           (x0+side*.045,y0,low),(x1+side*.045,y1,low),(x1+side*.045,y1,high),(x0+side*.045,y0,high)],
          [[0,1,2,3],[4,7,6,5],[0,4,5,1],[3,2,6,7],[0,3,7,4],[1,5,6,2]],material,label)

    part=b.parts[-1]
    part['texcoords']=[[(y+.15)/1.3,z/3.15] for x,y,z in part['vertices']]

def add_building(b,far=False):
    texture()
    front=-.14
    # The balcony floor projects from the wall, exposing pale panels between dark joists.
    rect(b,-WIDTH,WIDTH,-.01,.15,front,1.18,FLOOR,'Projecting gallery floor')
    rect(b,-WIDTH,WIDTH,.11,.19,front-.040,1.08,EDGE,'Balcony front fascia')
    for i,x in enumerate(JOISTS):
        rect(b,x-.063,x+.063,-.105,.052,front,1.19,GRAIN,'Exposed joist '+str(i+1))
    # Tall lower slots and the smaller upper drillings leave genuine gaps in the red board.
    outline=box(-WIDTH,.22,WIDTH,.80)
    voids=[]
    for i,x in enumerate(SLOTS):
        voids.append(box(x-.019,.35,x+.019,.62))
        if i%4!=2:
            voids.append(Point(x,.722).buffer(.019,resolution=4 if far else 9))
    prism(b,outline.difference(unary_union(voids)),front-.010,front+.049,TIMBER,'Slotted timber railing')
    for z,d,h,mat,label in [(.177,.094,.079,EDGE,'Lower rail bead'),(.783,.085,.047,GRAIN,'Upper rail bead'),(.831,.094,.043,EDGE,'Board capping')]:
        rect(b,-WIDTH-.03,WIDTH+.03,z,z+h,front-.023,front+d,mat,label)
    for j,z in enumerate([.88,1.012,1.152]):
        rect(b,-WIDTH-.018,WIDTH+.018,z,z+.019,front+.013,front+.036,METAL,'Slim upper horizontal '+str(j+1))
    for i,x in enumerate([-WIDTH+.02,-2.13,-1.04,.03,1.09,2.16,WIDTH-.02]):
        rect(b,x-.015,x+.015,.845,1.169,front+.005,front+.038,METAL,'Balcony rail upright '+str(i+1))
    # The knee wall is recessed. The camera sees the sloping timber frame in front of its pale infill.
    side_height=1.10;peak=2.48
    trap=Polygon([(-WIDTH,.10),(WIDTH,.10),(WIDTH,side_height),(1.64,peak),(-1.64,peak),(-WIDTH,side_height)])
    casement=box(-.805,.36,.805,1.79)
    prism(b,trap.difference(casement),1.17,1.38,WALL,'Attic infill with actual paired window opening')
    rect(b,-.80,.80,.35,1.80,1.24,1.27,GLASS,'Attic glazing')
    for i,x in enumerate((-.785,-.063,.063,.785)):
        rect(b,x-.030,x+.030,.34,1.803,1.127,1.248,CAME,'Casement jamb '+str(i+1))
    rect(b,-.058,.058,.33,1.80,1.105,1.24,TIMBER,'Central exposed timber')
    for x in (-.424,.424):
        for dx in (-.178,0,.178):rect(b,x+dx-.015,x+dx+.015,.37,1.78,1.15,1.244,CAME,'Small-pane vertical')
        for z in (.79,1.27,1.53,1.78):rect(b,x-.351,x+.351,z-.019,z+.019,1.145,1.247,CAME,'Small-pane rail')
    for side in (-1,1):
        bar(b,(side*1.28,.23),(side*.87,1.96),.094,1.122,1.228,TIMBER,'Sloping timber brace')
        rect(b,side*1.69-.045,side*1.69+.045,.17,2.43,1.113,1.230,TIMBER,'Attic upright')
    rect(b,-1.70,1.70,1.837,1.912,1.119,1.235,TIMBER,'Upper transom timber')
    # Deep green soffit and red verge follow both the sloping sides and the flat clipped summit.
    roof=[(-3.69,.67),(-1.85,2.57),(1.85,2.57),(3.69,.67)]
    for i,(p,q) in enumerate(zip(roof,roof[1:])):
        bar(b,p,q,.082,-.31,1.39,GREEN,'Green under-eave '+str(i))
        front_profile=LineString([p,q]).buffer(.058,cap_style=2)
        prism(b,front_profile,-.350,-.304,TIMBER,'Painted verge '+str(i))
        moved=[(x,z+.076) for x,z in [p,q]]
        prism(b,LineString(moved).buffer(.042,cap_style=2),-.355,1.35,TILE,'Clay roof edge '+str(i))
        bar(b,*( (x,z+.019) for x,z in [p,q]),.018,-.365,-.350,EDGE,'Raised verge moulding '+str(i))
        if i!=1:
            for j in range(1,14 if far else 25):
                t=j/(14 if far else 25);x=p[0]+t*(q[0]-p[0]);z=p[1]+t*(q[1]-p[1])
                rect(b,x-.011,x+.011,z-.044,z+.016,-.29,1.34,GREEN,'Visible soffit board joint')
    for side in (-1,1):
        bar(b,(side*1.66,.90),(side*1.51,2.54),.083,.147,.265,GRAIN,'Outer roof strut')
        return_board(b,side,front+.05,1.07,3.12,3.19,.24,.79,TIMBER,'Balcony railing return')
