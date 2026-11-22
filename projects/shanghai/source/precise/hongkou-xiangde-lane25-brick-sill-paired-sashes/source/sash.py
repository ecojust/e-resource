"""The photographed outer pair of red-framed windows at Lane 25, Xiangde Road."""
from pathlib import Path
import numpy as np
from PIL import Image
from shapely.geometry import box
ID='hongkou-xiangde-lane25-brick-sill-paired-sashes'
MORTAR='Pale recessed lime joints';RED='Warm red facing brick';DARK='Darker fired edges';PALE='Light orange brick';SILL='Weathered vertical sill bricks';FRAME='Red-brown perimeter frame';MULL='Red painted glazing bars';TEAL='Mottled blue-green behind glazing';REVEAL='Shaded brick reveal'
PALETTE={n:dict(color=c,roughness=r)for n,c,r in [(MORTAR,[.57,.49,.36],.94),(RED,[.63,.265,.132],.91),(DARK,[.447,.18,.10],.91),(PALE,[.723,.379,.201],.91),(SILL,[.46,.289,.187],.9),(FRAME,[.335,.134,.077],.65),(MULL,[.428,.202,.112],.65),(TEAL,[1,1,1],.42),(REVEAL,[.29,.14,.094],.94)]}
def texture():
    p=Path(__file__).with_name('turquoise-interior.png')
    if not p.exists():
        rng=np.random.default_rng(651)
        wash=np.array(Image.fromarray(rng.integers(0,255,(35,52),dtype='uint8')).resize((360,256),Image.Resampling.BICUBIC),float)/255
        grit=rng.normal(0,3.2,(256,360,1));rgb=np.array([33,97,106])+wash[:,:,None]*[40,65,53]+grit
        Image.fromarray(np.clip(rgb,0,255).astype('uint8')).save(p)
    PALETTE[TEAL]['texture']=str(p)
def add_building(b,far=False):
    texture()
    def rect(x0,x1,z0,z1,d0,d1,mat,label):
        b.prism(box(x0,z0,x1,z1),d0,d1,lambda x,z,d:(x,-d,z),mat,label)
    for lo,hi,z,h in [(-1.17,1.17,0,.34),(-1.17,-.843,.339,1.90),(.843,1.17,.339,1.90)]:
        rect(lo,hi,z,h,-.27,0,MORTAR,'Cut section of bonded brick wall')
    for j in range(20):
        z=j*.095+.004
        for i in range(-4,5):
            a=i*.357+(j%2)*.1785;mat=(RED,DARK,RED,PALE,RED)[(i+2*j)%5]
            for lo,hi in([(-1.17,1.17)]if z<.335 else[(-1.17,-.843),(.843,1.17)]):
                l=max(lo,a+.004);r=min(hi,a+.351)
                if l+.006<r:rect(l,r,z,min(z+.086,1.90),-.005,.016 if far else .016+(.002*((j+i)%3)),mat,'Individual brick with setback mortar joints')
    for x0,x1 in [(-.844,-.816),(.816,.844)]:
        rect(x0,x1,.364,1.90,-.179,.018,REVEAL,'Reveal between the wall and wooden-looking surround')
    for i in range(19):
        x=-.929+i*.098
        rect(x+.002,x+.095,.235,.367,-.133,.120,SILL if i%4 else DARK,'Upright brick in projecting continuous sill')
        if not far:
            rect(x+.004,x+.093,.356,.370,.012,.120,SILL,'Weathered leading edge of each vertical brick')
    for a,c in [(-.811,-.028),(.028,.811)]:
        rect(a,c,.387,1.90,-.204,-.178,TEAL,'Blue-green field seen through the sash')
        for z in [.388,.825,1.267,1.710]:
            rect(a,c,z,z+.020,-.160,-.124,MULL,'Slim horizontal glazing bars')
        x=(a+c)/2
        rect(x-.012,x+.012,.387,1.90,-.162,-.121,MULL,'One fine central bar in each sash')
    for x in(-.82,0,.82):
        width=.038 if x==0 else .025
        rect(x-width,x+width,.369,1.90,-.186,-.092,FRAME,'Central meeting stile and side jambs')
    rect(-.842,.842,.367,.399,-.173,-.090,FRAME,'Bottom rail seated immediately above sill')
    for p in b.parts:
        if p['material']==TEAL:p['texcoords']=[[(x+.845)/1.69,(z-.385)/1.52]for x,y,z in p['vertices']]
