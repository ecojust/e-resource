"""The patterned upper frieze and its two rendered corner piers at Xiangyang Apartments."""
from pathlib import Path
import numpy as np
from PIL import Image
from shapely.geometry import Polygon, box
ID='xuhui-xiangyang-apartments-chevron-frieze'
WALL='Buff textured stucco';FILLET='Cut pale stucco fillet';RECESS='Recessed frieze bed'
SHADOW='Deep shadow in the soffit';EPS=.001
PALETTE={WALL:dict(color=[1,1,1],roughness=.96),FILLET:dict(color=[.781,.722,.627],roughness=.85),RECESS:dict(color=[.644,.585,.503],roughness=.98),SHADOW:dict(color=[.355,.325,.287],roughness=.97)}
CENTERS=[(i-3.5)*.389 for i in range(8)]
def texture():
    path=Path(__file__).with_name('sandy-render.png')
    if not path.exists():
        y,x=np.indices((320,320));r=np.random.default_rng(739)
        value=r.normal(0,4.5,x.shape)+1.8*np.sin(x*.044+np.sin(y*.051))
        Image.fromarray(np.clip(np.array([194,181,157])+value[:,:,None],0,255).astype('uint8')).quantize(90).save(path)
    PALETTE[WALL]['texture']=str(path)
def add_building(b,far=False):
    texture()
    def raised(shape,back,front,material,name):
        b.prism(shape,back,front,lambda x,z,d:(x,-d,z),material,name)
    def rect(left,right,bottom,top,back,front,material,name):
        raised(box(left,bottom,right,top),back,front,material,name)
    rect(-1.94,1.94,0,.96,-.19,-.045,WALL,'Underlying rendered masonry')
    rect(-1.61,1.61,.45,.66,-.11,-.016,SHADOW,'Recessed horizontal strip below the frieze')
    for a in [-1.40+i*.350 for i in range(9)]:
        rect(a-.036,a+.036,.456,.644,-.095,.054,FILLET,'Short squared support inside the dark strip')
    for z,size,d in [(.42,.038,.092),(.466,.027,.063),(.635,.038,.073),(1.118,.044,.074),(1.168,.043,.102)]:
        rect(-1.64,1.64,z,z+size,-.10,d,FILLET,'Continuous stepped edge')
    rect(-1.59,1.59,.657,1.121,-.13,.012,RECESS,'Frieze backing between vertical ribs')
    for c in CENTERS:
        for j in range(5):
            mid=.715+j*.076
            v=Polygon([(c-.172,mid+.083),(c,mid),(c+.172,mid+.083),(c+.172,mid+.104),(c,mid+.022),(c-.172,mid+.104)])
            raised(v,-.005,.040,FILLET,'V-shaped relief strip on one repeated panel')
        rect(c-.190,c-.178,.664,1.121,.003,.048,FILLET,'Upright fillet marking one panel')
    for c in (-1.74,1.74):
        outline=[(c-.21,0),(c+.21,0),(c+.21,1.24),(c+.10,1.24),(c+.10,1.37),(c+.064,1.42),(c,1.447),(c-.066,1.42),(c-.10,1.37),(c-.10,1.24),(c-.21,1.24)]
        raised(Polygon(outline),-.175,.093,WALL,'Projecting pier with a raised rounded middle')
        for z,d in [(1.072,.125),(1.115,.157)]:
            rect(c-.19,c+.19,z,z+.030,.082,d,FILLET,'Projecting moulding on the pier')
        for dx,z0 in [(-.076,.535),(0,.43),(.076,.535)]:
            curve=[(c+dx-.021,1.069),(c+dx+.021,1.069),(c+dx+.021,z0+.054),(c+dx+.026,z0+.037),(c+dx,z0),(c+dx-.026,z0+.037),(c+dx-.021,z0+.054)]
            raised(Polygon(curve),.084,.122,FILLET,'Slender relief with a hanging point')
            if not far:
                rect(c+dx-.005,c+dx+.005,z0+.068,1.051,.115,.135,FILLET,'Narrow center ridge on a pendant')
        if not far:
            for dx in (-.136,.136):
                rect(c+dx-.006,c+dx+.006,.12,1.057,.085,.102,FILLET,'Outer scribed arris of the wall pier')
    for part in b.parts:
        if part['material']==WALL:part['texcoords']=[[(x+1.95)/3.9,z/1.45]for x,y,z in part['vertices']]
