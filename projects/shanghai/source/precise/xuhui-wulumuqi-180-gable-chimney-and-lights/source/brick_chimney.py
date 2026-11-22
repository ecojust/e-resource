"""Street-facing gable, tall brick stack and paired attic lights in the No. 180 street photograph."""
from pathlib import Path
import numpy as np
from PIL import Image
from shapely.geometry import Polygon,box,LineString
ID='xuhui-wulumuqi-180-gable-chimney-and-lights'
BRICK='Weathered red brick';GLASS='Grey attic glazing';FRAME='Pale painted sash';ROOF='Charcoal roof verge';SILL='Grey sill stone';CAP='Dark fired cap course'
PALETTE={k:dict(color=c,roughness=r) for k,c,r in [(BRICK,[1,1,1],.94),(GLASS,[.287,.315,.313],.40),(FRAME,[.715,.692,.633],.76),(ROOF,[.25,.254,.257],.82),(SILL,[.479,.456,.407],.91),(CAP,[.465,.31,.239],.94)]}
CH=.442
def texture():
    f=Path(__file__).with_name('weathered-red-brick.png')
    if not f.exists():
        y,x=np.indices((512,512));row=y//16;col=(x+32*(row%2))//64;rng=np.random.default_rng(771)
        v=np.array([140,90,63])+rng.normal(0,8.7,(33,10))[row,col,None]+rng.normal(0,4,x.shape)[:,:,None]
        mortar=(y%16<1)|((x+32*(row%2))%64<1);v[mortar]=np.array([158,133,111])+rng.normal(0,3,(int(mortar.sum()),1))
        Image.fromarray(v.clip(0,255).astype('uint8')).quantize(131).save(f)
    PALETTE[BRICK]['texture']=str(f)
def roofheight(x):return 2.34-1.11*abs(x)
def add_building(b,far=False):
    texture()
    def wall(poly,back,front,mat,label):b.prism(poly,back,front,lambda x,z,d:(x,-d,z),mat,label)
    def bar(l,r,low,hi,back,front,mat,label):wall(box(l,low,r,hi),back,front,mat,label)
    triangle=Polygon([(-1.86,0),(1.86,0),(1.86,roofheight(1.86)),(0,2.34),(-1.86,roofheight(1.86))])
    for sign in [-1,1]:
        x=sign*.84;outer=box(x-.145,.215,x+.145,.93);pane=box(x-.115,.252,x+.115,.896);triangle=triangle.difference(outer)
        wall(outer.difference(pane),-.09,-.018,FRAME,'Recessed pale window frame')
        wall(pane,-.136,-.105,GLASS,'Small attic glazing')
        for z in [.455,.675]:bar(x-.113,x+.113,z-.009,z+.009,-.095,-.043,FRAME,'Two horizontal glazing bars')
        bar(x-.008,x+.008,.254,.895,-.094,-.038,FRAME,'Narrow upright sash bar')
        bar(x-.184,x+.184,.177,.216,-.03,.033,SILL,'Thin sill projecting beyond jamb')
    wall(triangle,-.32,0,BRICK,'Red brick gable interrupted by attic lights')
    bar(-CH,CH,0,3.20,-.60,.071,BRICK,'Rectangular brick shaft carried above the gable')
    for sign in [-1,1]:
        x1,x2=sign*.427,sign*1.894
        pts=[(x1,roofheight(x1)),(x2,roofheight(x2)),(x2,roofheight(x2)+.076),(x1,roofheight(x1)+.076)]
        wall(Polygon(pts),-.422,.062,ROOF,'Narrow diagonal dark roof verge at edge of gable')
    for i in range(3):
        w=CH+.021*(i+1);bar(-w,w,3.12+.056*i,3.176+.056*i,-.601-.008*i,.091+i*.012,CAP if i==2 else BRICK,'Three projecting head courses of the stack')
    # Segmented repairs and individual courses below the cap mark the stack as a separate masonry body.
    for z in np.arange(.103,3.10,.126 if far else .063):
        for x in np.arange(-CH+.064+(int(round(z/.063))%2)*.112,CH-.012,.225):
            bar(x-.0023,x+.0023,z-.033,z+.022,.072,.074,SILL,'Short mortar joint on chimney face')
    for part in b.parts:
        if part['material']==BRICK:
            verts=np.array(part['vertices']);span=np.ptp(verts,axis=0);uv=[]
            for x,y,z in verts:
                u=x if span[0]>=span[1] else y
                uv.append([(u+2.1)/2.15,z/1.06])
            part['texcoords']=uv
