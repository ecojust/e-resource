"""The three attic lights in the high red brick gable of the Nie family garden."""
from pathlib import Path
from math import sin,cos,pi
import numpy as np
from PIL import Image
from shapely.geometry import Polygon,box
from shapely.ops import unary_union
ID='yangpu-nie-garden-triple-attic-light'
BRICK='Dark red running-bond brick';EDGE='Weathered brick at the eave';SURROUND='Dark red window jamb'
FRAME='Dark painted wood';GLASS='Shadowed blue-grey glass';STONE='Pale keystone and stone sill'
PALETTE={k:dict(color=c,roughness=r) for k,c,r in [(BRICK,[1,1,1],.96),(EDGE,[.30,.211,.196],.91),(SURROUND,[.410,.240,.225],.91),(FRAME,[.135,.125,.116],.70),(GLASS,[.148,.16,.164],.48),(STONE,[.58,.556,.517],.87)]}
def texture():
    f=Path(__file__).with_name('measured-red-brick.png')
    if not f.exists():
        rng=np.random.default_rng(719);im=np.zeros((768,960,3),dtype=float)
        for j in range(48):
            for x in range(-16,960,32):
                l=x+16*(j%2);r=l+32
                if l>=960 or r<=0:continue
                im[j*16:(j+1)*16,max(l,0):min(r,960)]=np.array([141,84,83])+rng.normal(0,7)
                im[(j+1)*16-1:(j+1)*16,max(l,0):min(r,960)]=[153,122,115]
                if 0<=l<960:im[j*16:(j+1)*16,l:l+1]=[131,107,101]
        im+=rng.normal(0,3.5,im.shape[:2])[:,:,None]
        Image.fromarray(im.clip(0,255).astype('uint8')).quantize(128).save(f)
    PALETTE[BRICK]['texture']=str(f)
def crown(x,r,bottom,shoulder,count):
    return Polygon([(x-r,bottom),(x+r,bottom)]+[(x+r*cos(pi*i/count),shoulder+r*sin(pi*i/count))for i in range(count+1)])
def add_building(b,far=False):
    texture();steps=12 if far else 32
    def form(poly,back,front,mat,label):b.prism(poly,back,front,lambda x,z,d:(x,-d,z),mat,label)
    def rect(l,r,bot,top,back,front,mat,label):form(box(l,bot,r,top),back,front,mat,label)
    gable=Polygon([(-1.67,0),(1.67,0),(1.67,1.59),(0,2.94),(-1.67,1.59)])
    holes=[crown(0,.252,.535,1.446,steps),box(-.637,.535,-.304,1.425),box(.304,.535,.637,1.425)]
    form(gable.difference(unary_union(holes)),-.255,0,BRICK,'Red brick gable surrounding three attic openings')
    for sign in(-1,1):
        form(Polygon([(0,2.91),(sign*1.69,1.54),(sign*1.69,1.595),(0,2.97)]),-.266,.037,EDGE,'Dark narrow barge edge on the gable slope')
    for j,outer in enumerate(holes):
        inner=outer.buffer(-.028,join_style=2)
        glass=inner.buffer(-.020,join_style=2)
        form(outer.difference(inner),-.133,-.018,SURROUND,'Deep brick return at the attic opening')
        form(inner.difference(glass),-.157,-.101,FRAME,'Sash edging around the recessed pane')
        form(glass,-.166,-.153,GLASS,'Shadowed recessed attic light')
        if j:
            x=(-.471 if j==1 else .471)
            rect(x-.010,x+.010,.575,1.38,-.153,-.125,FRAME,'Fine vertical bar in a side light')
    # Narrow voussoirs are individually expressed around the round central head.
    for j in range(11):
        a=pi*j/11+.003;v=pi*(j+1)/11-.003
        def arc(r):
            return [(r*cos(t),1.446+r*sin(t)) for t in np.linspace(a,v,3 if far else 6)]
        form(Polygon(arc(.256)+list(reversed(arc(.304)))),-.062,.011,SURROUND,'Radial brick above the central arch')
    form(Polygon([(-.047,1.716),(.047,1.716),(.074,1.81),(-.067,1.81)]),-.055,.036,STONE,'Light wedge at the top of the central arch')
    rect(-.676,.676,.462,.512,-.112,.063,STONE,'Continuous sill under the three openings')
    rect(-.699,.699,.514,.544,-.118,.088,STONE,'Projecting lip of the common sill')
    for g in b.parts:
        if g['material']==BRICK:g['texcoords']=[[(x+1.67)/3.34,z/2.97] for x,y,z in g['vertices']]
