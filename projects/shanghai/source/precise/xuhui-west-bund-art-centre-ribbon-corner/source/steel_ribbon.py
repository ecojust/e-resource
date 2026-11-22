"""Perforated street front, continuous end glazing and raised clerestory in Fayhoo's 2015 view."""
from pathlib import Path
import numpy as np
from shapely.geometry import Polygon,box
from PIL import Image
ID='xuhui-west-bund-art-centre-ribbon-corner'
PANELS='Light grey facing panels';STEEL='Recessed charcoal steel';GLASS='Grey-green industrial glass';HEAVY='Substantial painted meeting bar';CAP='Light folded roof capping';DARK='Shadow in the raised clerestory';JOINT='Fine grey cladding joint'
PALETTE={m:dict(color=c,roughness=r)for m,c,r in [(PANELS,[1,1,1],.83),(GLASS,[1,1,1],.43),(STEEL,[.138,.164,.150],.70),(HEAVY,[.114,.145,.128],.78),(CAP,[.755,.759,.735],.69),(DARK,[.240,.288,.263],.77),(JOINT,[.540,.554,.551],.88)]}
R=1.50;DEPTH=2.43;LOW=-.18;TOP=2.12
def texture():
    f=Path(__file__).with_name('paint-and-green-glazing.png')
    if not f.exists():
        g=np.random.default_rng(847)
        y,x=np.indices((180,256))
        facing=np.array([204,201,200])+np.cos(x*.023)[:,:,None]*1.6+g.normal(0,1.8,(180,256,1))
        sky=(np.cos(x*.023+y*.037)*3.2+np.sin(x*.055-y*.063)*1.6)[:,:,None]
        glass=np.array([145,163,153])+sky+g.normal(0,1.5,(180,256,1))
        Image.fromarray(np.concatenate([facing,glass],axis=1).clip(0,255).astype('uint8')).quantize(112).save(f)
    for kind in (PANELS,GLASS):PALETTE[kind]['texture']=str(f)
def add_building(b,far=False):
    texture()
    def section(side,shape,d0,d1,mat,name):
        if side:b.prism(shape,d0,d1,lambda u,z,d:(R+d,u,z),mat,name)
        else:b.prism(shape,d0,d1,lambda u,z,d:(u,-d,z),mat,name)
    def rect(side,u0,u1,z0,z1,d0,d1,mat,label):
        if far and mat in (STEEL,HEAVY):
            edges=[(u0,z0),(u1,z0),(u1,z1),(u0,z1)]
            points=[(R+d1,u,z) if side else (u,-d1,z) for u,z in edges]
            b.add(points,[(0,1,2,3)],mat,label)
        else:
            section(side,box(u0,z0,u1,z1),d0,d1,mat,label)
    def bank(side,u0,u1,z0,z1,blocks,halfrows=2):
        cells=blocks*3;h=halfrows*2
        rect(side,u0,u1,z0,z1,-.119,-.092,GLASS,'Continuous grey-green panes behind the grid')
        for i in range(cells+1):
            u=u0+i*(u1-u0)/cells
            span=.012 if i%3==0 else .0043
            rect(side,u-span,u+span,z0,z1,-.109,-.045 if i%3==0 else -.067,HEAVY if i%3==0 else STEEL,'Steel vertical sash or fine glazing bar')
        for j in range(h+1):
            z=z0+j*(z1-z0)/h
            span=.011 if j%2==0 else .004
            rect(side,u0,u1,z-span,z+span,-.110,-.043 if j%2==0 else -.066,HEAVY if j%2==0 else STEEL,'Horizontal steel bar')
    for side in (False,True):
        limits=(.165,DEPTH) if side else (-1.51,R)
        wall=box(-.018 if side else limits[0],LOW,limits[1],TOP)
        openings=[(.226,DEPTH)] if side else [(-1.385,-.181),(.059,1.264)]
        for left,right in openings:
            for low,high in ((.388,.841),(1.174,1.627)):
                wall=wall.difference(box(left,low,right,high))
                bank(side,left,right,low,high,6 if side else 3)
        section(side,wall,-.114,0,PANELS,'Pale cladding around the corresponding two levels of steel windows')
        for z in (.993,1.791):
            rect(side,limits[0],limits[1],z,z+.004,-.006,.001,JOINT,'Fine horizontal panel joint')
        if not side:
            for x in (-.071,1.409):
                rect(False,x,x+.004,LOW,TOP,-.006,.001,JOINT,'Fine joint at pier')
    # An inset front strip of daylighting is visible above the parapet. The return is a solid grey cheek.
    inner=R-.18
    b.box((-.013,.246,2.149),(2.662,.11,.083),DARK,label='Lower rail in front of the rooftop strip')
    b.prism(box(-1.365,2.172,inner,2.354),-.29,-.252,lambda u,z,d:(u,-d,z),GLASS,'Upper green clerestory glass')
    for k in range(25):
        x=-1.365+(inner+1.365)*k/24
        width=.014 if k%3==0 else .006
        b.box((x,.237,2.264),(width,.036,.197),HEAVY if k%3==0 else STEEL,label='Small divisions in rooftop glazing')
    b.box((-.023,.231,2.262),(inner+1.365,.041,.010),STEEL,label='Clerestory horizontal glazing bar')
    cheek=Polygon([(.215,TOP),(.215,2.380),(.49,2.376),(.843,2.178),(.843,TOP)])
    b.prism(cheek,inner-.025,inner+.029,lambda u,z,d:(d,u,z),PANELS,'Raised lantern with its shallow sloping solid cheek')
    b.box((-.02,.270,2.380),(2.750,.150,.035),CAP,label='Very shallow front coping above clerestory')
    # Bevel along the three exposed folds of the side roof capping; the far level uses a coarser curve.
    resolution=4 if far else 14
    d=.028
    for y0,z0,y1,z1 in ((.215,2.380,.49,2.376),(.49,2.376,.843,2.178)):
        verts=[];faces=[]
        for y,z in ((y0,z0),(y1,z1)):
            for j in range(resolution+1):
                theta=np.pi*j/resolution
                verts.append([inner+d*np.cos(theta),y,z+.009+d*.33*np.sin(theta)])
        for j in range(resolution):faces.append((j,j+resolution+1,j+resolution+2,j+1))
        b.add(verts,faces,CAP,'Fold over the sloping roof end')
    for part in b.parts:
        mat=part['material']
        if mat in (GLASS,PANELS):
            off=.510 if mat==GLASS else .013
            part['texcoords']=[(off+.47*min(1,max(0,(x+y+1.55)/5.55)),.98-.95*min(1,max(0,(z+.18)/2.59)))for x,y,z in part['vertices']]
