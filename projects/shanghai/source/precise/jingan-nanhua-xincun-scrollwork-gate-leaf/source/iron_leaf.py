"""Upper panel of the street-facing iron gate photographed at Lane 774, Changle Road."""
from pathlib import Path
from math import sin,cos,pi
from shapely.geometry import box,Polygon
from PIL import Image
import numpy as np
ID='jingan-nanhua-xincun-scrollwork-gate-leaf'
FRAME='Painted iron frame'; PICKET='Rectangular pickets'; SCROLL='Bent flat iron'; PEAK='Spear points'; PIN='Rivet heads'
PALETTE={k:dict(color=v,metallic=m,roughness=.65) for k,v,m in [(FRAME,[1,1,1],.29),(PICKET,[.108,.115,.111],.30),(SCROLL,[.12,.125,.119],.28),(PEAK,[.16,.163,.147],.27),(PIN,[.19,.192,.173],.34)]}
def texture():
    f=Path(__file__).with_name('graphite-iron.png')
    if not f.exists():
        rng=np.random.default_rng(639);noise=rng.normal(0,3.0,(176,176))
        pixels=(np.array([43,46,44])+noise[:,:,None]).clip(0,255).astype('uint8')
        Image.fromarray(pixels).quantize(64).save(f)
    for mat,tint in [(FRAME,1.),(PICKET,.94),(SCROLL,.98),(PEAK,1.),(PIN,.96)]:
        PALETTE[mat].update(texture=str(f),color=[tint,tint,tint])
def profile(x):
    t=(x+.845)/1.69
    return 1.935-.325*(3*t*t-2*t*t*t)
def at(x,z,d):return x,-d,z
def curve(x,z,far):
    # Two opposed open scrolls pass each other beside the lozenge spine.
    points=[]
    for t in np.linspace(0.,1.,6 if far else 14):
        u=1.-t; points.append((u**3*.006+3*u*u*t*.165+3*u*t*t*.173+t**3*.111,u**3*(-.209)+3*u*u*t*(-.117)+3*u*t*t*.041+t**3*.084))
    for a in np.linspace(pi*.23,pi*1.99,9 if far else 22):
        q=(a-pi*.23)/(pi*1.76);radius=.054*(1.-.60*q)
        points.append((.070+radius*cos(a),.050+radius*sin(a)))
    return [(x+a,z+b)for a,b in points]
def add_building(b,far=False):
    texture()
    def panel(p,d0,d1,m,name):b.prism(p,d0,d1,at,m,name)
    def rect(x0,x1,z0,z1,d0,d1,m,name):panel(box(x0,z0,x1,z1),d0,d1,m,name)
    def flat(points,radius,depth,m,name):
        from shapely.geometry import LineString
        shape=LineString(points).buffer(radius,cap_style=2,join_style=2)
        panel(shape,depth,depth+.012,m,name)
    for x in(-.865,0,.865):
        rect(x-.018,x+.018,0,profile(np.clip(x,-.845,.845))+.012,-.030,.028,FRAME,'Outer stiles and central divider')
    for z,t in [(0,.019),(.092,.013),(.967,.022)]:
        rect(-.88,.88,z-t,z+t,-.021,.032,FRAME,'Horizontal frame rail')
    for offset in (0.,-.253):
        pts=[(x,profile(x)+offset)for x in np.linspace(-.864,.864,13 if far else 29)]
        flat(pts,.018,.012,FRAME,'Shaped upper rail and parallel inner rail')
    locations=np.linspace(-.778,.778,11)
    for i,x in enumerate(locations):
        if i==5:continue
        top=profile(x)
        rect(x-.008,x+.008,0,top+.028,-.017,.003,PICKET,'Upright iron square bar')
        polygon=Polygon([(x-.011,top+.014),(x-.022,top+.055),(x,top+.127),(x+.022,top+.055),(x+.011,top+.014)])
        panel(polygon,-.018,.007,PEAK,'Flattened spearhead')
    for cx in(-.429,.429):
        for s in(-1.,1.):
            p=curve(0,0,far)
            flat([(cx+s*x,.58+z)for x,z in p],.009,.009,SCROLL,'Upper opposed scroll')
            flat([(cx-s*x,.45-z)for x,z in p],.009,.009,SCROLL,'Lower opposed scroll')
        flat([(cx,.765),(cx+.096,.594),(cx,.423),(cx-.096,.594),(cx,.765)],.008,.009,SCROLL,'Open lozenge within central scroll')
    for x in np.linspace(-.735,.735,9):
        y=profile(x)-.137
        flat([(x,y+.085),(x+.038,y),(x,y-.083),(x-.038,y),(x,y+.085)],.007,.008,SCROLL,'Small pointed grille in curved upper band')
    for x in(-.865,0,.865):
        for z in(.092,.967,profile(np.clip(x,-.845,.845))-.25):
            b.tube([(x,-.033,z),(x,-.042,z)],.012,PIN,sides=7 if far else 12,label='Rail fixing')
    for part in b.parts:
        part['texcoords']=[[(x+.9)/.43,z/.43]for x,y,z in part['vertices']]
