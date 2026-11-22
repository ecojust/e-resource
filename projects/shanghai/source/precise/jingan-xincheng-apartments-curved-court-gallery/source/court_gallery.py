"""One open gallery landing in the courtyard at 337 Chengdu North Road.

The undulating outer slab line and its rail follow the two published court views.
The wall thicknesses and dimensions are proportional estimates.
"""
from math import sin, pi
from pathlib import Path
import numpy as np
from PIL import Image
from shapely.geometry import Polygon, box

ID='jingan-xincheng-apartments-curved-court-gallery'
EDGE='Ochre painted slab edge'
DECK='Warm grey gallery paving'
SOFFIT='Pale grey painted soffit'
WALL='Apricot stair enclosure'
IRON='Dark painted top rail'
POST='Square guardrail uprights'
MESH='Galvanized diamond screen'
BASE='Steel base rail'
PALETTE={name:dict(color=color,roughness=rough,metallic=metal) for name,color,rough,metal in [
    (EDGE,[1,1,1],.90,0),(SOFFIT,[.72,.70,.65],.94,0),(DECK,[.48,.455,.413],.92,0),(WALL,[.76,.49,.29],.88,0),
    (IRON,[.079,.106,.126],.59,.45),(POST,[.105,.119,.13],.63,.36),
    (MESH,[.355,.365,.343],.70,.36),(BASE,[.144,.139,.128],.62,.29)]}

def texture():
    path=Path(__file__).with_name('ochre-slab-edge.png')
    if not path.is_file():
        rng=np.random.default_rng(635)
        grain=rng.normal(0,4.1,(100,320,1))
        pigment=rng.normal(0,1.2,(100,320,3))
        Image.fromarray(np.clip([184,119,72]+grain+pigment,0,255).astype('uint8')).save(path)
    PALETTE[EDGE]['texture']=str(path)

def curb(x):
    # A smooth re-entrant turn connects each straight gallery to the landing.
    d=abs(x)
    if d>=2.12:return -.43
    t=d/2.12
    return -.43-1.24*(1-t*t)**2.8

def add_building(b,far=False):
    texture()
    def xyz(x,y,h):return x,y,h
    def slab(poly,lo,hi,material,label):b.prism(poly,lo,hi,xyz,material,label)
    xs=np.linspace(-2.90,2.90,41 if far else 89)
    outline=[(x,curb(x)) for x in xs]+[(2.90,.84),(-2.90,.84)]
    slab(Polygon(outline),-.178,0,EDGE,'Continuous curved concrete edge and soffit')
    soffit=Polygon(outline).buffer(-.018,join_style=2)
    slab(soffit,-.182,-.177,SOFFIT,'Pale underside behind the ochre lip')
    walk=[(x,curb(x)+.029) for x in xs]+[(2.90,.84),(-2.90,.84)]
    slab(Polygon(walk),-.002,.013,DECK,'Exposed upper surface of the projecting landing')
    # A short wall segment behind the guard retains the visible return of the stair enclosure.
    poly=Polygon([(-.67,.8),(-.67,.01),(-.53,-.13),(.49,-.13),(.71,.025),(.71,.8)])
    slab(poly,0,1.77,WALL,'Partial ochre wall of the staircase behind the landing')
    nodes=np.linspace(-2.82,2.82,10)
    for h,r,material,label in [(1.032,.034,IRON,'Continuous rounded handrail'),(.907,.012,IRON,'Recessed upper wire border'),(.110,.017,BASE,'Lower steel edging')]:
        b.tube([(x,curb(x)+.047,h) for x in xs],r,material,sides=6 if far else 12,label=label)
    for x in nodes:
        y=curb(x)+.049
        slab(box(x-.018,y-.022,x+.018,y+.022),.014,1.039,POST,'Upright steel frame')
        slab(box(x-.036,y-.037,x+.036,y+.037),.014,.039,BASE,'Welded foot of upright')
    # Each mesh panel turns with the outside line. The holes are actual openings.
    for a,c in zip(nodes,nodes[1:]):
        lo,hi=.128,.897
        for grad in (1.62,-1.62):
            for intercept in np.arange(-1.0,2.01,.132):
                xa=a+(lo-intercept)/grad
                xb=a+(hi-intercept)/grad
                left=max(a+.019,min(xa,xb));right=min(c-.019,max(xa,xb))
                if right-left<.018:continue
                pts=[(x,curb(x)+.070,intercept+grad*(x-a)) for x in np.linspace(left,right,3 if far else 5)]
                b.tube(pts,.0034,MESH,sides=3 if far else 5,label='Woven diamond screen inside guardrail frame')
    for p in b.parts:
        if p['material']==EDGE:p['texcoords']=[[(x+2.90)/5.80,(z+.178)/.178] for x,y,z in p['vertices']]
