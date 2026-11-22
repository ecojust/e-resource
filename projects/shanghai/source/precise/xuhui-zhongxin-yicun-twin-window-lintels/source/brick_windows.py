"""Two neighbouring sash openings with white pale hood and aprons, Zhongxin Yicun street front."""
from pathlib import Path
import math
import numpy as np
from PIL import Image,ImageDraw
from shapely.geometry import Point,Polygon,box
ID='xuhui-zhongxin-yicun-twin-window-lintels'
BRICK='Red stretcher brick';TRIM='Warm cream cut and painted trim';EDGE='Light projecting sill edge';FRAME='Black-brown sash';REVEAL='Warm grey interior reveal';GLASS='Dark reflecting glass'
PALETTE={m:dict(color=c,roughness=r) for m,c,r in [(BRICK,[1,1,1],.94),(TRIM,[.855,.833,.755],.86),(EDGE,[.815,.830,.793],.82),(FRAME,[.136,.147,.140],.65),(REVEAL,[.256,.228,.216],.88),(GLASS,[.364,.416,.419],.38)]}
CENTERS=(-.82,.82)
def texture():
    atlas=Path(__file__).with_name('alternating-red-bricks.png')
    if not atlas.exists():
        rng=np.random.default_rng(843);height,width=512,1024
        img=Image.new('RGB',(width,height),(186,170,158));draw=ImageDraw.Draw(img)
        for row in range(33):
            off=-18 if row%2 else 0
            for start in range(off,width,36):
                jitter=rng.integers(-12,13,3);color=np.array([145,84,70])+jitter
                draw.rectangle((start+1,row*16+1,start+34,row*16+14),fill=tuple(map(int,color)))
        pixels=np.asarray(img).astype(float)+rng.normal(0,3.1,(height,width,1))
        Image.fromarray(pixels.clip(0,255).astype('uint8')).quantize(144).save(atlas)
    PALETTE[BRICK]['texture']=str(atlas)
def add_building(b,far=False):
    texture();seg=9 if far else 31
    def face(poly,back,front,mat,title):b.prism(poly,back,front,lambda x,z,d:(x,-d,z),mat,title)
    def rect(lo,hi,bot,top,back,outer,material,label):face(box(lo,bot,hi,top),back,outer,material,label)
    area=box(-1.53,0,1.53,2.07)
    for x in CENTERS:area=area.difference(box(x-.458,.365,x+.458,1.604))
    face(area,-.234,0,BRICK,'Red wall with two separately recessed openings')
    for part in b.parts:
        if part['material']==BRICK:part['texcoords']=[(.01+.979*(x+1.53)/3.06,.984-.968*z/2.07) for x,y,z in part['vertices']]
    for z0,z1,d in [(1.785,1.817,.059),(1.811,1.842,.078),(1.838,1.878,.098),(1.876,1.909,.123)]:
        rect(-1.53,1.53,z0,z1,-.012,d,TRIM,'Continuous returning head moulding')
    for mx in CENTERS:
        rect(mx-.455,mx+.455,.366,1.606,-.228,-.115,REVEAL,'Depth of the sash reveal')
        for off in (-.219,.219):
            xc=mx+off
            rect(xc-.201,xc+.201,.388,1.579,-.13,-.1,GLASS,'Reflecting pane in dark sash')
            for x in (xc-.209,xc+.197):rect(x,x+.018,.37,1.60,-.12,-.065,FRAME,'Sash side upright')
            for z in (.381,1.258,1.569):rect(xc-.208,xc+.210,z,z+.027,-.12,-.061,FRAME,'Midrail and the upper and lower sash rails')
        rect(mx-.016,mx+.016,.361,1.602,-.13,-.056,FRAME,'Meeting stile')
        for sign in (-1,1):
            pos=mx+.49*sign
            rect(pos-.039,pos+.039,.30,1.61,-.04,.036,TRIM,'Slender cream window surround')
            face(Point(pos,.391).buffer(.024,resolution=seg),.036,.042,EDGE,'Round field ornament at sill height')
            crown=[]
            for k in range(seg+1):
                t=k/seg;out=.047+.116*(1-math.cos(t*math.pi/2))
                crown.append((mx+sign*(.455+out),1.59+.199*t))
            shape=Polygon([(mx+sign*.414,1.59)]+crown+[(mx+sign*.414,1.789)])
            face(shape,-.008,.064,TRIM,'Cut curved shoulder beneath the shared head')
        rect(mx-.505,mx+.505,1.600,1.787,-.012,.057,TRIM,'Individual lintel beneath the common cornice')
        face(Polygon([(mx-.083,1.767),(mx+.083,1.767),(mx+.060,1.643),(mx-.062,1.643)]),.055,.069,EDGE,'Small rectangular dropped keystone field')
        rect(mx-.539,mx+.539,.290,.365,-.012,.116,EDGE,'Wide independent projecting sill')
        rect(mx-.485,mx+.485,.250,.293,-.012,.087,TRIM,'Lower band of the stepped sill')
        face(Polygon([(mx-.384,.257),(mx+.384,.257),(mx+.384,.145),(mx-.384,.135)]),-.007,.053,TRIM,'Long plain rectangular apron below sill')
    # Lower horizontal stone band is visible through each clear interval between trees.
    rect(-1.53,1.53,.026,.056,-.012,.036,EDGE,'Narrow string course below the two aprons')
