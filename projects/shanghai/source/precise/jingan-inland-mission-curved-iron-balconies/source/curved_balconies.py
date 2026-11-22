"""Two levels of the middle balcony on the five-storey north building, after Fayhoo's 2016 photograph."""
from math import cos, sin, pi
from pathlib import Path
from PIL import Image
from shapely.geometry import Polygon, box
from shapely.ops import unary_union
import numpy as np

ID = 'jingan-inland-mission-curved-iron-balconies'
WALL = 'Light grey plaster'
RIM = 'Pale balcony edge'
SHADE = 'Grey slab and soffit'
DARK = 'Blue black window frames'
GLASS = 'Lower glass in shade'
SKY = 'Sky reflected in upper windows'
IRON = 'Dark painted balcony rail'
PALETTE = {key:dict(color=colour,roughness=rough) for key,colour,rough in [
    (WALL,[1,1,1],.95),(RIM,[.77,.75,.68],.87),(SHADE,[.47,.46,.42],.91),
    (DARK,[.075,.085,.081],.7),(GLASS,[.105,.157,.164],.41),
    (SKY,[.354,.493,.511],.4),(IRON,[.069,.071,.063],.69)]}

def texture():
    path=Path(__file__).with_name('balcony-plaster.png')
    if not path.exists():
        rng=np.random.default_rng(623)
        fine=rng.normal(0,2.4,(512,512))
        coarse=np.asarray(Image.fromarray((rng.random((33,33))*28+104).astype('uint8')).resize((512,512),Image.Resampling.BICUBIC),dtype=float)-118
        base=np.array([197,191,179])+(.33*coarse+fine)[:,:,None]
        Image.fromarray(base.clip(0,255).astype('uint8')).quantize(96).save(path)
    PALETTE[WALL]['texture']=str(path)

CENTRES=(-1.01,1.01)
DECKS=(.24,2.95)
R=1.68
def rail_y(x):
    return -.945+.535*(x/R)**2

def arched_opening(cx,z0,shoulder,rise,segments):
    r=.714
    return Polygon([(cx-r,z0),(cx+r,z0)]+[(cx+r*cos(t),shoulder+rise*sin(t)) for t in np.linspace(0,pi,segments+1)])

def add_building(b,far=False):
    texture()
    n=12 if far else 28
    def front(x,z,d):return x,-d,z
    def rectangle(x0,x1,z0,z1,d0,d1,m,name):
        b.prism(box(x0,z0,x1,z1),d0,d1,front,m,name)
    def curve(x0,x1,fn,h,mat,label):
        b.tube([(x,rail_y(x),fn(x)) for x in np.linspace(x0,x1,n+1)],h,mat,sides=6 if far else 10,label=label)
    def stroke(coords,rad,name):
        b.tube([(x,rail_y(x),z) for x,z in coords],rad,IRON,sides=5 if far else 8,label=name)
    holes=[]
    for x in CENTRES:
        holes += [box(x-.58,.283,x+.58,2.284), arched_opening(x,3.00,4.63,.50,n)]
    b.prism(box(-1.94,0,1.94,5.41).difference(unary_union(holes)),-.39,0,front,WALL,'Recessed wall around the two pairs of windows')
    for side in (-1,1):
        x=side*1.86
        rectangle(x-.065,x+.065,.04,2.82,-.04,.057,RIM,'Plain pier at outside edge of bay')
        for z in (2.66,2.71):
            rectangle(x-.074,x+.074,z,z+.025,.056,.088,RIM,'Pair of flat bands at the pier head')
    for x in CENTRES:
        lower=box(x-.58,.283,x+.58,2.284)
        upper=arched_opening(x,3.0,4.63,.50,n)
        for poly,mat in [(lower,GLASS),(upper,SKY)]:
            b.prism(poly,-.253,-.210,front,mat,'Reflected glazing in the window recess')
            ring=poly.difference(poly.buffer(-.043,join_style='mitre'))
            b.prism(ring,-.211,-.144,front,DARK,'Sash following the outline of the window')
        for z0,z1,width,steps in [(.29,2.28,.58,2),(3.00,4.63,.714,3)]:
            for j in range(1,steps):
                mid=x-width+2*width*j/steps
                for label,d,thick in [('Moulded vertical window bar',-.153,.027),('Inner stile on opening light',-.134,.011)]:
                    rectangle(mid-thick,mid+thick,z0+.03,z1-.03,-.212,d,DARK,label)
            for frac,thick in [(.43,.010),(.77,.022)]:
                z=z0+frac*(z1-z0)
                rectangle(x-width+.032,x+width-.032,z-thick,z+thick,-.212,-.154,DARK,'Horizontal division in the sash')
        rectangle(x-.696,x+.696,4.603,4.656,-.212,-.144,DARK,'Straight transom under lunette')
        rectangle(x-.019,x+.019,4.637,5.095,-.212,-.155,DARK,'Central bar of the arched upper light')
    for base in DECKS:
        for low,high,edge,material,name in [(-.188,-.126,-.056,SHADE,'Recessed underside'),(-.126,-.074,-.02,RIM,'Lower bead'),(-.074,-.051,-.039,SHADE,'Shadow groove'),(-.051,0,0,RIM,'Upper balcony nosing')]:
            xs=np.linspace(-R-.036,R+.036,n+1)
            plan=Polygon([(xs[0],.049),(xs[-1],.049)]+[(x,rail_y(x)-.067-edge) for x in reversed(xs)])
            b.prism(plan,base+low,base+high,lambda x,y,h:(x,y,h),material,name)
        for offset,radius in [(.032,.015),(.68,.015),(.757,.024)]:
            curve(-R,R,lambda x:base+offset,radius,IRON,'Curved upper, lower and secondary horizontal rails')
        # In the photograph a circle crossed by two diagonals separates paired strips of fine scrollwork.
        for sign in (-1,1):
            for x in np.linspace(.54,1.57,10):
                stroke([(sign*x,base+.039),(sign*x,base+.68)],.0105,'Straight bar in the flanking field')
            for x in (R,.508,.312):
                stroke([(sign*x,base+.008),(sign*x,base+.75)],.016,'Edge stile or jamb of the narrow scroll panel')
            for zmid in (.139,.276,.416,.552,.638):
                for hand in (-1,1):
                    xc=.407*sign+hand*.034
                    omega=np.linspace(-.9*pi,.78*pi,11 if far else 19)
                    points=[(xc+hand*.029*cos(t),base+zmid+.044*sin(t)) for t in omega]
                    stroke(points,.005,'Small opposing C scrolls in the two narrow panels')
            # Short returns to the wall are visible past the end posts.
            for h in (.035,.679,.753):
                b.tube([(sign*R,rail_y(R),base+h),(sign*R,-.025,base+h)],.016,IRON,sides=6 if far else 9,label='Side return to wall')
        for s in (-1,1):
            stroke([(-.31,base+.059 if s<0 else base+.666),(.31,base+.666 if s<0 else base+.059)],.012,'Two diagonals across the round central panel')
        ts=np.linspace(0,2*pi,25 if far else 45)
        stroke([(.298*cos(t),base+.361+.298*sin(t)) for t in ts],.012,'Circular ornament between the diagonals')
    for part in b.parts:
        if part['material']==WALL:
            part['texcoords']=[[(x+1.97+.12*y)/4.05,z/5.45] for x,y,z in part['vertices']]
