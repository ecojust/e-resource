"""Terminal three-facet bay of the former Guangdong Bank, Ningbo Road, as photographed in November 2014."""
from math import pi,cos,sin
from pathlib import Path
import numpy as np
from PIL import Image
from shapely.geometry import Polygon,box
from shapely.ops import unary_union
ID='huangpu-guangdong-bank-three-faceted-windows'
FACING='Fine aggregate facing';EDGING='Warm grey window sill';DARK='Shadow under sill';ACCENT='Pale facing strip'
JOIN='Dark steel frame';GLASS='Cool shaded glass';SKY='Glass reflecting sky';SHADE='Deep window reveal';HIGHLIGHT='Light splice at the frame';LATER='Light lower window frame'
PALETTE={m:dict(color=c,roughness=r)for m,c,r in [(FACING,[1,1,1],.95),(EDGING,[.43,.414,.38],.91),(DARK,[.256,.249,.232],.95),(ACCENT,[.717,.705,.663],.92),(JOIN,[.108,.117,.115],.72),(GLASS,[.18,.22,.24],.35),(SKY,[.29,.354,.395],.33),(SHADE,[.25,.247,.227],.96),(HIGHLIGHT,[.43,.44,.42],.73),(LATER,[.64,.648,.635],.68)]}
A=pi/7.2;W=1.20
FACE=lambda u,z,d:(u,-d,z)
L=lambda u,z,d:(-W+u*cos(A)-d*sin(A),-u*sin(A)-d*cos(A),z)
R=lambda u,z,d:(W+u*cos(A)+d*sin(A),u*sin(A)-d*cos(A),z)
FACES=[(L,-2.48,0.,-1.20),(FACE,-W,W,0.),(R,0.,2.48,1.20)]
def texture():
    path=Path(__file__).with_name('fine-taupe-facing.png')
    if not path.exists():
        rng=np.random.default_rng(519);w,h=608,448
        cloud=np.asarray(Image.fromarray(rng.integers(0,255,(21,33),dtype=np.uint8)).resize((w,h),Image.Resampling.BICUBIC),float)
        tonal=(cloud-127)*.043+rng.normal(0,2.5,(h,w))
        rgb=np.array([169,162,151])[None,None,:]+tonal[:,:,None]
        Image.fromarray(np.clip(rgb,0,255).astype('u1')).quantize(144).save(path)
    PALETTE[FACING]['texture']=str(path)
def slab(b,f,p,d,back,m,label):b.prism(p,back,d,f,m,label)
def rect(b,f,x,y,z,h,d,back,m,label):slab(b,f,box(x,z,y,h),d,back,m,label)
def upper_hole(c):
    return Polygon([(c-.435,2.35),(c+.435,2.35),(c+.435,3.848),(c+.277,4.135),(c+.123,4.36),(c-.115,4.36),(c-.273,4.133),(c-.435,3.843)])
def window(b,f,c):
    shape=upper_hole(c)
    slab(b,f,shape,-.183,-.22,SHADE,'Deep recess within the shouldered opening')
    slab(b,f,shape.buffer(-.031),-.163,-.194,GLASS,'Base glazing in clipped pointed head')
    slab(b,f,shape.difference(shape.buffer(-.034)), -.074,-.182,JOIN,'Steel sash following angular head')
    for col in range(3):
        for row in range(3):
            l=c-.390+col*.26;z=2.405+row*.433
            rect(b,f,l+.011,l+.249,z+.012,z+.426,-.159,-.18,SKY if (col+row)%3==0 else GLASS,'Rectangular steel-light glazing')
    for i in (-1,1):
        x=c+i*.130;rect(b,f,x-.012,x+.012,2.38,4.304,-.096,-.178,JOIN,'Two mullions dividing the three narrow lights')
    for z in (2.824,3.26,3.707):
        rect(b,f,c-.408,c+.408,z-.016,z+.016,-.093,-.179,JOIN,'Horizontal steel transom')
    for z,d,m in [(2.259,.126,DARK),(2.295,.164,EDGING)]:
        rect(b,f,c-.545,c+.545,z,z+.054,d,-.18,m,'Projecting sill following one face of the tower')
    lower=box(c-.49,.11,c+.49,1.52);slab(b,f,lower,-.17,-.201,SHADE,'Window below the striped spandrel')
    for side in (-1,1):
        x=c+side*.221;rect(b,f,x-.196,x+.197,.16,1.453,-.145,-.171,SKY if side==-1 else GLASS,'Two plain lower casements')
    for x in (-.457,0.,.457):rect(b,f,c+x-.019,c+x+.019,.107,1.48,-.10,-.183,LATER,'Light frame of rectangular lower opening')
    for z in (.119,1.291,1.472):rect(b,f,c-.473,c+.473,z-.018,z+.018,-.093,-.166,LATER,'Lower horizontal sash rail')
def top_shape(l,r,center,outer=False):
    if not outer:
        return Polygon([(l,0.),(r,0.),(r,5.67),(.877,5.67),(.877,5.86),(.553,5.86),(.553,6.07),(.203,6.07),(.203,6.36),(-.202,6.36),(-.202,6.08),(-.54,6.08),(-.54,5.86),(-.872,5.86),(-.872,5.68),(l,5.68)])
    if center<0:
        return Polygon([(l,0.),(r,0.),(r,5.68),(l+.18,5.08),(l,4.965)])
    return Polygon([(l,0.),(r,0.),(r,4.965),(r-.18,5.08),(l,5.67)])
def add_building(b,far=False):
    texture()
    for f,l,r,c in FACES:
        holes=unary_union([upper_hole(c),box(c-.49,.11,c+.49,1.52)])
        slab(b,f,top_shape(l,r,c,f is not FACE).difference(holes),0.,-.243,FACING,'Three contiguous faces of the street-corner tower')
        window(b,f,c)
        for dx in (-.22,.22):
            rect(b,f,c+dx-.075,c+dx+.075,1.524,2.268,.0125,-.022,ACCENT,'Pale vertical stripes under the dark steel window')
        # Inverted wedge with a short narrow lower face, sitting on the top of each opening.
        top=5.62 if f is FACE else 5.426
        wedge=Polygon([(c-.15,4.354),(c+.15,4.354),(c+.368,top),(c-.368,top)])
        slab(b,f,wedge,.038,-.062,ACCENT,'Pale downward-tapering stone above the head')
        # Faceted collar meets the two shoulders on either side of the dark steel opening.
        for side in (-1,1):
            strip=Polygon([(c+side*.435,3.845),(c+side*.118,4.36),(c+side*.156,4.393),(c+side*.473,3.89)])
            slab(b,f,strip,.027,-.131,EDGING,'Clipped shoulder of window surround')
        if not far:
            for side in (-1,1):
                x=c+side*.408
                for z in (2.59,3.05,3.49):b.tube([f(x,z,.002),f(x,z,-.063)],.018,JOIN,7,'Small dark metal fixing inside the jamb')
    for part in b.parts:
        if part['material']==FACING:part['texcoords']=[[(x+.23*y+3.65)/7.30,(z+.035)/6.49]for x,y,z in part['vertices']]
