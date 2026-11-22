"""Gardenside window and exposed aggregate on the residence at 28 Gaolan Road, after Antigng's 2018 image."""
from math import sin,cos,pi
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFilter
from shapely.geometry import Polygon,box
ID='huangpu-gaolan-28-aggregate-casement'
WALL='Pale roughcast with dark pebbles';STONE='Warm stone sill';DRIP='Shadow below sill';WOOD='Reddish brown sash';EDGE='Light worn edge of sash'
FRAME='Shaded brown outer frame';GLASS='Shaded garden glazing';SKY='Cool sky and foliage reflection';EAVE='Dark outer eave board';SOFFIT='Shadowed soffit';TIP='Pale rafter ends';ROOF='Dark grey tiled eave'
PALETTE={m:dict(color=c,roughness=r)for m,c,r in [(WALL,[1,1,1],.99),(STONE,[.55,.492,.403],.95),(DRIP,[.34,.302,.25],.94),
(WOOD,[.251,.155,.121],.85),(EDGE,[.34,.235,.189],.83),(FRAME,[.198,.135,.111],.91),(GLASS,[.174,.200,.200],.34),(SKY,[.24,.285,.293],.31),(EAVE,[.19,.14,.11],.91),(SOFFIT,[.272,.227,.18],.93),(TIP,[.61,.59,.52],.93),(ROOF,[.21,.215,.205],.96)]}
F=lambda x,z,d:(x,-d,z)
def texture():
    file=Path(__file__).with_name('garden-pebbledash.png')
    if not file.exists():
        # Random dark mineral chips in lighter mortar, with a narrow light upper edge.
        rng=np.random.default_rng(523);w,h=700,488
        yy,xx=np.indices((h,w));patch=np.asarray(Image.fromarray(rng.integers(0,255,(29,42),dtype=np.uint8)).resize((w,h),Image.Resampling.BICUBIC),float)
        shade=(patch-127)*.093+rng.normal(0,3.6,(h,w));rgb=np.array([190,186,172])[None,None,:]+shade[:,:,None]
        im=Image.fromarray(np.clip(rgb,0,255).astype('u1'));d=ImageDraw.Draw(im)
        for i in range(10800):
            x,y=rng.uniform(-3,w+3),rng.uniform(-3,h+3);r=rng.uniform(.75,2.95);ratio=rng.uniform(.43,1.0);a=rng.uniform(0,pi)
            outline=[]
            for t in np.linspace(0,2*pi,7)[:-1]:
                k=rng.uniform(.78,1.12);u,v=r*k*cos(t),r*ratio*k*sin(t);outline.append((x+u*cos(a)-v*sin(a),y+u*sin(a)+v*cos(a)))
            v=int(rng.uniform(53,135));d.polygon(outline,fill=(v+5,v+4,v))
            if r>1.8:d.line(outline[:3],fill=(min(219,v+54),min(215,v+48),min(207,v+45)))
        im.quantize(180).save(file)
    PALETTE[WALL]['texture']=str(file)
def slab(b,p,fr,back,m,name):b.prism(p,back,fr,F,m,name)
def rect(b,l,r,z0,z1,fr,back,m,name):slab(b,box(l,z0,r,z1),fr,back,m,name)
def trace(b):
    p=Polygon([(-.19,.80),(.106,.80),(.164,.834),(.164,.894),(.083,.927),(-.19,.927)])
    b.prism(p,-1.024,1.024,lambda d,z,v:(-v,-d,z),STONE,'Projecting deep stone window sill with a sloping top')
    rect(b,-.973,.973,.775,.806,.093,-.17,DRIP,'Dark shadow line under the garden window')
def casement(b):
    for x in (-.907,.907):rect(b,x-.048,x+.048,.910,2.295,.004,-.18,FRAME,'Recessed timber master frame')
    for z in (.923,2.281):rect(b,-.955,.955,z-.042,z+.042,.004,-.179,FRAME,'Timber master frame head and sill')
    for side in (-1,1):
        c=side*.454
        for x in (c-.416,c+.416):rect(b,x-.025,x+.025,.952,2.241,-.018,-.145,WOOD,'Framed vertical casement stile')
        for z in (.978,2.216):rect(b,c-.432,c+.432,z-.033,z+.033,-.017,-.143,WOOD,'Upper and lower timber rails')
        for j in range(4):
            for i in range(2):
                x=c+(i-.5)*.39;z=1.011+(j+.5)*.294
                rect(b,x-.182,x+.182,z-.135,z+.135,-.107,-.15,GLASS if (i+j+(side>0))%3 else SKY,'Small garden-facing glass light')
        rect(b,c-.012,c+.012,1.010,2.183,-.059,-.143,EDGE,'Fine centre muntin in the casement')
        for j in range(1,4):
            z=1.011+j*.294
            rect(b,c-.390,c+.390,z-.013,z+.013,-.058,-.141,EDGE,'Fine sash bar between four rows of lights')
    rect(b,-.034,.034,.952,2.248,-.012,-.161,WOOD,'Meeting stile of the two timber casements')
def add_building(b,far=False):
    texture()
    wall=box(-1.86,0,1.86,2.80).difference(box(-.953,.884,.953,2.326))
    slab(b,wall,0.,-.228,WALL,'Mineral aggregate facing surrounding the courtyard window')
    slab(b,box(-.953,.884,.953,2.326),-.154,-.213,FRAME,'Shadow at the back of the true reveal')
    # A short portion of the left return is visible beside the principal wall.
    b.prism(box(-.48,0.,0.,2.80),-.228,0.,lambda u,z,d:(-1.86-d,-u,z),WALL,'Short left wall return at the window')
    casement(b);trace(b)
    for x in np.linspace(-1.58,1.58,6):
        # Light squared beam tips seen under the deep dark fascia.
        shape=Polygon([(0.,2.581),(.212,2.581),(.343,2.657),(.343,2.746),(0.,2.746)])
        b.prism(shape,-x-.058,-x+.058,lambda d,z,u:(-u,-d,z),TIP,'Pale beam end beneath the eave')
    rect(b,-1.91,1.91,2.722,2.762,.385,-.19,SOFFIT,'Soffit over the wood window')
    rect(b,-1.945,1.945,2.758,2.831,.402,.315,EAVE,'Dark outer fascia at the garden eave')
    roof=Polygon([(-.28,2.966),(.416,2.842),(.416,2.831),(-.28,2.933)])
    b.prism(roof,-1.946,1.946,lambda d,z,u:(-u,-d,z),ROOF,'Narrow visible edge of the garden-side roof')
    for part in b.parts:
        if part['material']==WALL:part['texcoords']=[[(x+.82*y+2.01)/4.18,(z+.04)/2.96]for x,y,z in part['vertices']]
    # A shallow scattering near the sill catches raking light on the coarser aggregate.
    rng=np.random.default_rng(528)
    vs=[];fs=[]
    for k in range(220 if far else 1100):
        x=rng.uniform(-1.84,1.84);z=rng.uniform(.02,2.71)
        if -.99<x<.99 and .76<z<2.37:continue
        a=rng.uniform(0,pi);rr=rng.uniform(.0048,.010);idx=len(vs)
        for j in range(5):vs.append((x+rr*cos(2*pi*j/5+a),-.001,z+.70*rr*sin(2*pi*j/5+a)))
        vs.append((x+.001,-.0053,z+.002))
        for j in range(5):fs.append((idx+j,idx+(j+1)%5,idx+5))
    b.add(vs,fs,WALL,'Scattered raised pebble faces around the plastered window')
    b.parts[-1]['texcoords']=[[(x+.82*y+2.01)/4.18,(z+.04)/2.96]for x,y,z in b.parts[-1]['vertices']]
