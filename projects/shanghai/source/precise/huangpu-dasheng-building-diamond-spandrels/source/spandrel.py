"""A two-bay portion of Dasheng Company's geometric street facade, after the numbered 2019 field photograph."""
from math import pi,cos,sin
from pathlib import Path
import numpy as np
from PIL import Image
from shapely.geometry import Polygon,box
from shapely.ops import unary_union
ID='huangpu-dasheng-building-diamond-spandrels'
WALL='Cool grey rendered wall';TRIM='Projecting edge of spandrel';FIELD='Recessed panel field';LINES='Raised lozenge ribs';REVEAL='Shadowed opening';WINDOW='Dark reddish brown sash';PANE='Deep grey glass';SKY='Pale reflected glass';SOFFIT='Shadow beneath projecting eave'
PALETTE={m:dict(color=c,roughness=r)for m,c,r in [(WALL,[1,1,1],.95),(TRIM,[.626,.64,.604],.92),(FIELD,[.506,.516,.478],.92),(LINES,[.678,.691,.647],.89),
(REVEAL,[.29,.301,.28],.94),(WINDOW,[.205,.141,.108],.81),(PANE,[.153,.177,.178],.35),(SKY,[.244,.286,.278],.34),(SOFFIT,[.382,.399,.385],.91)]}
F=lambda x,z,d:(x,-d,z)
CENTERS=(-1.20,1.20);W=.953;H=.413;Z=2.155
def texture():
    p=Path(__file__).with_name('grey-stucco.png')
    if not p.exists():
        rng=np.random.default_rng(527);sz=(528,420)
        rough=np.asarray(Image.fromarray(rng.integers(0,255,(28,42),dtype=np.uint8)).resize(sz,Image.Resampling.BICUBIC),float)
        v=(rough-127)*.039+rng.normal(0,1.5,sz[::-1]);field=np.array([165,170,161])[None,None,:]+v[:,:,None]
        Image.fromarray(np.clip(field,0,255).astype('u1')).quantize(144).save(p)
    PALETTE[WALL]['texture']=str(p)
def slab(b,p,d,back,m,label):b.prism(p,back,d,F,m,label)
def rect(b,l,r,z0,z1,d,back,m,label):slab(b,box(l,z0,r,z1),d,back,m,label)
def relief(b,c,far):
    p=box(c-W,Z-H,c+W,Z+H);slab(b,p,.049,-.065,FIELD,'Recessed field behind diamond relief')
    inset=.044
    for k in range(2):
        g=p.buffer(-k*.062,join_style=2);band=g.difference(g.buffer(-.022,join_style=2))
        slab(b,band,.086-k*.008,.045,TRIM,'Fine double border of street-facing spandrel')
    clip=p.buffer(-.099,join_style=2)
    for scale,width,fr in [(1.00,.020,.102),(.68,.018,.091),(.49,.017,.087)]:
        # A set of long, narrow lozenges is clipped into the inner rectangular border.
        # Remaining edge strips form the four short corner triangles seen in the field photograph.
        w=1.24*scale;h=.49*scale
        form=Polygon([(c-w,Z),(c,Z+h),(c+w,Z),(c,Z-h)])
        band=form.boundary.buffer(width,cap_style=2,join_style=2).intersection(clip)
        slab(b,band,fr,.046,LINES,'Raised intersecting lines of three nested lozenges')
        if not far:
            cap=band.buffer(-.005,join_style=2)
            if cap.area>1e-6:slab(b,cap,fr+.007,fr-.001,LINES,'Narrow crest on the face of the relief')
    for side in (-1,1):
        x=c+side*W;rect(b,x-.023,x+.023,Z-H-.014,Z+H+.017,.096,-.032,TRIM,'Vertical edge of panel at jamb')
    for z in (Z-H-.01,Z+H+.01):
        rect(b,c-W-.023,c+W+.023,z-.025,z+.025,.115,-.043,TRIM,'Upper and lower ledges raking along the street')
def win(b,c,bottom,top,far,opened=False):
    half=.873
    rect(b,c-half,c+half,bottom,top,-.187,-.236,REVEAL,'Recess behind the two-leaf windows')
    for idx in range(4):
        cx=c+(idx-1.5)*.417
        for j,(z0,z1) in enumerate([(bottom+.037,top-.326),(top-.299,top-.045)]):
            rect(b,cx-.193,cx+.193,z0,z1,-.148,-.182,SKY if (idx+j)%3==0 else PANE,'Tall casement or rectangular transom glass')
    for x in np.linspace(c-.833,c+.833,5):
        rect(b,x-.018,x+.018,bottom+.018,top-.02,-.089,-.18,WINDOW,'Dark vertical wooden sash')
    for z in (bottom+.025,top-.312,top-.022):
        rect(b,c-.85,c+.85,z-.018,z+.018,-.087,-.177,WINDOW,'Horizontal bar of rectangular overlight')
    if opened:
        # One of the photographed lower lights stands open; approximate only the projected leaf.
        a=.53;length=.405
        def wing(u,z,d):return (c-.415+u*cos(a)-d*sin(a),-u*sin(a)-d*cos(a)-.018,z)
        b.prism(box(0.,bottom+.046,length,top-.33),-.040,-.036,wing,PANE,'Glazing in outward-opening leaf')
        rim=box(-.015,bottom+.032,length+.016,top-.314).difference(box(.019,bottom+.07,length-.017,top-.356))
        b.prism(rim,-.064,-.012,wing,WINDOW,'Dark edge of slightly open casement')
def bracket(b,c,far):
    # Coved plaster profile below the overhanging street cornice.
    sh=Polygon([(0.,4.14),(.096,4.15),(.114,4.26),(.160,4.354),(.227,4.436),(.333,4.506),(.443,4.537),(.443,4.61),(0.,4.61)])
    for off in (-.067,.067):
        p=c+off;b.prism(sh,-p-.042,-p+.042,lambda d,z,u:(-u,-d,z),TRIM,'Curved paired bracket supporting the main cornice')
def add_building(b,far=False):
    texture()
    holes=unary_union([box(c-.876,lo,c+.876,hi)for c in CENTERS for lo,hi in ((.11,1.714),(2.609,4.115))])
    slab(b,box(-2.52,0.,2.52,4.715).difference(holes),0.,-.232,WALL,'Two adjacent street bays with three deep wall piers')
    for c in CENTERS:
        win(b,c,.11,1.714,far,opened=c<0);win(b,c,2.609,4.115,far,opened=c>0)
        relief(b,c,far)
    for x in (-2.39,0.,2.39):
        for s in (-.106,.106):
            rect(b,x+s-.017,x+s+.017,.015,4.44,.022,-.03,TRIM,'Thin continuous raised line at the outer pilaster')
        bracket(b,x,far)
    for lo,hi,d,m in [(4.585,4.632,.45,SOFFIT),(4.632,4.680,.495,TRIM),(4.680,4.715,.483,WALL),(.046,.094,.082,TRIM)]:
        rect(b,-2.52,2.52,lo,hi,d,-.242,m,'Horizontal cornice or lower sill across the bays')
    for part in b.parts:
        if part['material']==WALL:part['texcoords']=[[(x+2.60)/5.20,(z+.043)/4.86]for x,y,z in part['vertices']]
