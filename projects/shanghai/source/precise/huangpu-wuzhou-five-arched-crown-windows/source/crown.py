"""Five round-headed windows below the stepped crown of the Wuzhou Building photographed in 2015."""
from math import pi,cos,sin
from pathlib import Path
import numpy as np
from PIL import Image
from shapely.geometry import Polygon,box
from shapely.ops import unary_union
ID='huangpu-wuzhou-five-arched-crown-windows'
WALL='Buff grey tower facing';PIER='Pale dressed pier face';FLUTE='Darker incised strip';APRON='Light panel below the windows'
SASH='Deep metal frame';PANE='Grey blue glass';SKY='Cooler reflected glass';JAMB='Dark recessed jamb';EDGE='Narrow cap of the parapet';GRILLE='Shaded horizontal slots'
PALETTE={m:dict(color=c,roughness=r)for m,c,r in [
    (WALL,[1,1,1],.95),(PIER,[.68,.65,.575],.94),(FLUTE,[.465,.453,.413],.91),(APRON,[.78,.753,.643],.92),
    (SASH,[.125,.13,.117],.75),(PANE,[.22,.30,.34],.33),(SKY,[.35,.45,.48],.34),(JAMB,[.285,.27,.24],.88),
    (EDGE,[.61,.592,.521],.88),(GRILLE,[.198,.207,.198],.76)]}
F=lambda x,z,d:(x,-d,z)
CENTERS=(-3.46,-1.73,0.,1.73,3.46)
HALF=4.96
levels=[(-4.96,-4.67,5.84),(-4.67,-4.24,5.70),(-4.24,-3.96,5.8),(-3.96,-3.31,5.65),(-3.31,-3.04,5.82),(-3.04,-2.51,5.69),(-2.51,-2.24,5.85),(-2.24,-1.39,5.78),(-1.39,-1.12,6.43),(-1.12,-.73,6.31),(-.73,-.49,6.48),(-.49,-.252,6.39),(-.252,.252,6.91)]
levels+= [(-r,-l,h)for l,r,h in reversed(levels[:-1])]
def texture():
    p=Path(__file__).with_name('buff-aggregate.png')
    if not p.exists():
        rng=np.random.default_rng(515);w,h=640,432;x,y=np.meshgrid(np.arange(w),np.arange(h));broad=np.asarray(Image.fromarray(rng.integers(0,255,(18,40),dtype=np.uint8)).resize((w,h),Image.Resampling.BICUBIC),float)
        val=(broad-127)*.063+rng.normal(0,2.6,(h,w))
        rgb=np.array([167,165,150])[None,None,:]+val[:,:,None]
        Image.fromarray(np.clip(rgb,0,255).astype('u1')).quantize(160).save(p)
    PALETTE[WALL]['texture']=str(p)
def profile(b,shape,front,back,m,name):b.prism(shape,back,front,F,m,name)
def rect(b,l,r,lo,hi,d,back,m,name):profile(b,box(l,lo,r,hi),d,back,m,name)
def arch(c,far):
    return Polygon([(c-.38,2.79),(c+.38,2.79)]+[(c+.38*cos(t),3.65+.359*sin(t))for t in np.linspace(0,pi,13 if far else 33)])
def tower_top(x):
    return max(h for l,r,h in levels if l-1e-7<=x<=r+1e-7)
def glazed_window(b,c,far,upper):
    hole=arch(c,far) if upper else box(c-.38,.35,c+.38,1.543)
    profile(b,hole,-.21,-.241,JAMB,'Dark recess behind window joinery')
    profile(b,hole.buffer(-.028),-.185,-.213,PANE,'Glass behind slim sash')
    z0,z1=(2.81,3.627) if upper else (.375,1.52)
    for i in range(2):
        for j in range(2):
            l=c-.334+i*.334;r=l+.334;lo=z0+(z1-z0)*j*.5;hi=lo+(z1-z0)*.5
            rect(b,l+.016,r-.016,lo+.018,hi-.018,-.168,-.192,SKY if (i+j)%3==0 else PANE,'Rectangular light in one of five windows')
    rect(b,c-.346,c+.346,z0-.018,z0+.015,-.101,-.20,SASH,'Dark lower rail')
    rect(b,c-.352,c+.352,z1-.020,z1+.02,-.094,-.202,SASH,'Impost rail below the glazed arch' if upper else 'Upper lintel rail')
    for x in (c-.351,c+.351,c):
        rect(b,x-.015,x+.015,z0,z1,-.112,-.202,SASH,'Metal window stile')
    if upper:
        # The five fan heads each have their own softly rounded perimeter.
        rim=hole.difference(hole.buffer(-.031))
        profile(b,rim,-.088,-.194,SASH,'Window frame following the curved head')
    else:
        rect(b,c-.35,c+.35,1.215,1.247,-.099,-.20,SASH,'Shallow transom on the lower window')
    rect(b,c-.417,c+.417,z0-.07,z0-.029,.03,-.22,EDGE,'Fine sill across the window recess')
def add_building(b,far=False):
    texture()
    roof=unary_union([box(l,0.,r,h)for l,r,h in levels])
    openings=unary_union([arch(c,far)for c in CENTERS]+[box(c-.38,.35,c+.38,1.543) for c in CENTERS])
    profile(b,roof.difference(openings),0.,-.335,WALL,'Stepped crown of the central five-bay tower')
    for l,r,h in levels:
        rect(b,l,r,h-.03,h,.023,-.337,EDGE,'Individual cap at each level of the skyline')
    for c in CENTERS:
        glazed_window(b,c,far,True);glazed_window(b,c,far,False)
        for dx in (-.246,0.,.246):
            rect(b,c+dx-.076,c+dx+.076,1.682,2.595,.028,-.05,APRON,'Pale strip in the spandrel between the two windows')
        if c:
            for dx in (-.178,.178):
                rect(b,c+dx-.092,c+dx+.092,4.20,min(tower_top(c+dx)-.28,5.46),.027,-.04,PIER,'Paired short ribs above the arched window')
    for x in (-4.58,-2.59,-.85,.85,2.59,4.58):
        width=.115 if abs(x)>4 else .082
        rect(b,x-width,x+width,0.,tower_top(x)-.055,.034,-.08,PIER,'Unbroken fin between the vertically stacked windows')
        rect(b,x+width,x+width+.034,0.,tower_top(x)-.093,.013,-.055,FLUTE,'Parallel shadow line')
    # A single slotted central blade rises above the other fins.
    rect(b,-.22,.22,4.19,6.88,.061,-.09,PIER,'Central upright from the crown')
    for j in range(9):
        h=4.49+j*.158
        for lo,hi,m,d in [(h,h+.070,GRILLE,.073),(h+.073,h+.111,EDGE,.087)]:
            rect(b,-.168,.168,lo,hi,d,.034,m,'Horizontal slots and bars on the central rooftop blade')
    for i,part in enumerate(b.parts):
        if part['material']==WALL:part['texcoords']=[[(x+5.10)/10.20,(z+.06)/7.03]for x,y,z in part['vertices']]
