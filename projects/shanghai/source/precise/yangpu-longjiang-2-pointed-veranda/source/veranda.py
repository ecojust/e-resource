"""Three narrow pointed openings in the short face of the veranda at 2 Longjiang Road."""
from pathlib import Path
import numpy as np
from PIL import Image
from shapely.geometry import Polygon,box
from shapely.ops import unary_union

ID='yangpu-longjiang-2-pointed-veranda'
CREAM='Warm cream mineral render';STONE='Pale projecting surround';BASE='Cool grey pier courses'
FRAME='Brown-black painted steel';GLASS='Grey-blue glazing';BRICK='Red brick sill';JOINT='Grey horizontal joint'
PALETTE={name:dict(color=color,roughness=r) for name,color,r in [
    (CREAM,[1,1,1],.94),(STONE,[.76,.73,.64],.90),(BASE,[.519,.536,.540],.95),
    (FRAME,[.115,.116,.107],.63),(GLASS,[.204,.244,.246],.47),(BRICK,[.384,.177,.119],.92),(JOINT,[.63,.63,.60],.94)]}
X=(-.63,0,.63)
PROFILE=[(0,.050),(.04,.052),(.07,.036),(.13,.026),(.21,.047),(.26,.052),(.32,.042),(.38,.027),(.44,.030),(.47,.043)]
def texture():
    f=Path(__file__).with_name('veranda-render.png')
    if not f.exists():
        yy,xx=np.indices((256,256));r=np.random.default_rng(715)
        speck=r.normal(0,3.5,xx.shape)+1.5*np.sin(yy*.024+xx*.01)
        Image.fromarray((np.array([202,197,176])+speck[:,:,None]).clip(0,255).astype('uint8')).quantize(110).save(f)
    PALETTE[CREAM]['texture']=str(f)

def opening(x,r=.253,bot=.32,shoulder=2.13,ridge=2.29):
    return Polygon([(x-r,bot),(x+r,bot),(x+r,shoulder),(x,ridge),(x-r,shoulder)])

def add_building(b,far=False):
    texture()
    def form(poly,back,front,material,name):
        b.prism(poly,back,front,lambda x,z,d:(x,-d,z),material,name)
    outside=unary_union([opening(x) for x in X])
    for bottom,top,mat,label in [(0,1.87,BASE,'Continuous grey coursed piers'),(1.87,2.64,CREAM,'Rendered pointed heads and spandrel')]:
        form(box(-1.031,bottom,1.031,top).difference(outside),-.195,0,mat,label)
    for n in range(1,6):
        z=.31*n
        form(box(-1.031,z,1.031,z+.008).difference(outside),-.003,.002,JOINT,'Thin horizontal joint continuing between the openings')
    for x in X:
        outer=opening(x,.270,.299,2.144,2.321)
        inner=opening(x,.215,.347,2.111,2.244)
        form(outer.difference(inner),-.105,.036,STONE,'Pale projecting trim following the shallow pointed head')
        pane=opening(x,.196,.368,2.091,2.216)
        form(inner.difference(pane),-.130,-.077,FRAME,'Narrow inset sash perimeter')
        form(pane,-.163,-.139,GLASS,'Recessed grey glazing')
        form(box(x-.009,.368,x+.009,2.206),-.142,-.102,FRAME,'Central dark vertical glazing bar')
        for z in (.82,1.28,1.73):
            form(box(x-.196,z-.007,x+.196,z+.007),-.140,-.105,FRAME,'Horizontal steel glazing bar')
        for j in range(3):
            z=.045+j*.086
            for k in range(3):
                u=x-.248+k*.165
                form(box(u+.002,z,u+.163,z+.079),-.028,.021,BRICK,'Brick below the narrow light')
    for z,t,d,mat,label in [(2.52,2.60,.065,STONE,'Shadow line below the parapet'),(2.60,2.76,.095,CREAM,'Broad sill of the balustrade'),(3.225,3.273,.08,STONE,'Upper rail fascia'),(3.273,3.315,.10,CREAM,'Projecting balustrade coping')]:
        form(box(-1.05,z,1.05,t),-.21,d,mat,label)
    for side in (-1,1):
        x=side*.986
        form(box(x-.057,2.74,x+.057,3.25),-.164,.032,CREAM,'Square terrace end pier')
    for x in np.linspace(-.87,.87,15):
        b.lathe((x,-.006),[(2.755+z,r) for z,r in PROFILE],STONE,8 if far else 16,'Turned stone baluster in the short terrace return')
    for g in b.parts:
        if g['material']==CREAM:g['texcoords']=[[(x+1.08)/2.16,z/3.33] for x,y,z in g['vertices']]
