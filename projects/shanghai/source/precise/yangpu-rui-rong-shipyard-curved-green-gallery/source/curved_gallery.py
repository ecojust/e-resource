"""Two levels of a curved gallery on the street corner of the former Yangshupu Road shipyard."""
from pathlib import Path
from math import sin,cos,pi
import numpy as np
from PIL import Image
from shapely.geometry import box,LineString
from shapely.ops import unary_union
ID='yangpu-rui-rong-shipyard-curved-green-gallery'
WALL='Warm ivory outer wall';PIER='Cream banded pier';CAP='Pale balcony slab';BAR='Deep green iron railing'
GLASS='Cool dark window pane';SASH='Dark steel window sash';CORNICE='Grey cornice below parapet'
PALETTE={k:dict(color=c,roughness=r) for k,c,r in [(WALL,[1,1,1],.94),(PIER,[.76,.75,.68],.92),(CAP,[.52,.53,.49],.88),(BAR,[.111,.227,.157],.67),(GLASS,[.179,.219,.218],.35),(SASH,[.146,.161,.149],.70),(CORNICE,[.432,.435,.409],.90)]}
R=3.68;HALF=1.71;FLOORS=(0,1.67);WINDOWS=(-1.03,-.37,.37,1.03)
def texture():
 f=Path(__file__).with_name('shipyard-plaster.png')
 if not f.exists():
    yy,xx=np.indices((256,256));rng=np.random.default_rng(727)
    field=rng.normal(0,2.6,xx.shape)+2.7*np.sin(.029*xx+.016*yy)
    Image.fromarray((np.array([195,194,177])+field[:,:,None]).clip(0,255).astype('uint8')).quantize(92).save(f)
 PALETTE[WALL]['texture']=str(f)
def pos(u,z,d):
 a=u/R;return ((R+d)*sin(a),R-(R+d)*cos(a),z)
def add_building(b,far=False):
 texture()
 def form(poly,back,front,mat,name):
    if not poly.is_empty:b.prism(poly,back,front,pos,mat,name)
 def rect(l,r,z,t,back,front,m,n):form(box(l,z,r,t),back,front,m,n)
 def curved_rect(l,r,z,t,back,front,mat,name):
    n=max(1,int((r-l)/(.31 if far else .16)))
    cuts=np.linspace(l,r,n+1)
    for l0,r0 in zip(cuts[:-1],cuts[1:]):rect(l0,r0,z,t,back,front,mat,name)
 def rod(points,half,d,label):
    line=LineString(points).buffer(half,cap_style=2,join_style=2)
    form(line,d-.009,d+.009,BAR,label)
 for level in FLOORS:
    apertures=[box(u-.219,level+.32,u+.219,level+1.39) for u in WINDOWS]
    void=unary_union(apertures)
    splits=np.linspace(-HALF,HALF,25 if not far else 15)
    for l,r in zip(splits[:-1],splits[1:]):
        form(box(l,level,r,level+1.67).difference(void),-.15,0,WALL,'Curved cream wall between the windows')
    for u,opening in zip(WINDOWS,apertures):
        inner=opening.buffer(-.031,join_style=2)
        form(opening.difference(inner),-.12,-.055,SASH,'Inset steel sash around one tall light')
        form(inner,-.139,-.121,GLASS,'Recessed dark glazing at the corner')
        rect(u-.194,u+.194,level+1.135,level+1.16,-.120,-.077,SASH,'Horizontal transom')
        rect(u-.009,u+.009,level+.35,level+1.14,-.120,-.078,SASH,'Vertical glazing bar below the transom')
    for u in (-1.46,0,1.46):
        for j in range(6):
            rect(u-.058,u+.058,level+.279*j,level+.279*(j+1)-.009,-.016,.025,PIER,'One course at projecting pilaster')
    curved_rect(-HALF-.02,HALF+.02,level+.11,level+.17,-.02,.42,CAP,'Curved gallery floor and outer rim')
    for z,t in [(level+.175,level+.194),(level+.638,level+.667)]:
        curved_rect(-HALF,HALF,z,t,.391,.423,BAR,'Continuous green rail along the curved front')
    for u in (-1.70,-.845,0,.845,1.70):
        rect(u-.019,u+.019,level+.18,level+.68,.394,.426,BAR,'Square green railing post')
    for center in (-1.27,-.423,.423,1.27):
        for j in range(-3,4):
            u=center+j*.094
            rect(u-.006,u+.006,level+.194,level+.64,.39,.413,BAR,'Thin straight iron picket')
        t=np.linspace(-1,1,10 if not far else 6)
        rod([(center+.337*t0,level+.42+.209*t0*t0)for t0 in t],.009,.409,'Sagging iron curve between posts')
    for u in(-.845,.845):
        for scale in (.093,.061):
            rod([(u,level+.615),(u+scale,level+.417),(u,level+.208),(u-scale,level+.417),(u,level+.615)],.008,.432,'Narrow doubled diamond over the post')
 curved_rect(-HALF,HALF,3.285,3.363,-.10,.107,CORNICE,'Projecting curved cornice')
 for u in np.linspace(-1.60,1.60,20):
    rect(u-.038,u+.038,3.241,3.30,.032,.101,PIER,'Pale dentil below the eave')
 curved_rect(-HALF,HALF,3.363,3.46,-.15,.031,WALL,'Low restrained roof parapet')
 for g in b.parts:
    if g['material']==WALL:
        g['texcoords']=[[(np.arctan2(x,R-y)*R+HALF)/(2*HALF),z/3.46] for x,y,z in g['vertices']]
