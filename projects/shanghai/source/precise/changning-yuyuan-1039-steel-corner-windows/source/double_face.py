"""Two adjacent upper windows and the iron grilles below, at 1039 Yuyuan Road."""
from math import sin,cos,pi
from pathlib import Path
from PIL import Image
import numpy as np
from shapely.geometry import box,Polygon,LineString
ID='changning-yuyuan-1039-steel-corner-windows'
YELLOW='Golden ochre rendered wall';LIGHT='Pale window surround';STEEL='Black-painted steel frame'
PANE='Dark grey window glass';IRON='Black lower grille';SILL='Pale grey projecting belt';EAVE='Dark metal eave';SHADOW='Shadow at the glazing rebate'
PALETTE={k:dict(color=c,roughness=r) for k,c,r in [(YELLOW,[.71,.57,.37],.92),(LIGHT,[.713,.707,.653],.88),(STEEL,[.103,.103,.094],.64),(PANE,[.187,.221,.222],.38),(IRON,[.155,.136,.108],.68),(SILL,[.549,.554,.530],.9),(EAVE,[.164,.155,.140],.91),(SHADOW,[.23,.195,.141],.94)]}
def texture():
    f=Path(__file__).with_name('ochre-plaster.png')
    if not f.exists():
        r=np.random.default_rng(707)
        row,col=np.indices((320,320))
        grain=r.normal(0,2.3,row.shape)
        joints=np.where(row%40<=1,-23,0)
        colours=np.array([190,164,120])+grain[:,:,None]+joints[:,:,None]
        Image.fromarray(colours.clip(0,255).astype('uint8')).quantize(95).save(f)
    PALETTE[YELLOW].update(color=[1,1,1],texture=str(f))
EDGE=.92
def place(side,u,d,z):return (EDGE+d,u+EDGE,z) if side else (u,-d,z)
def add_building(b,far=False):
    texture()
    for side in [False,True]:
        start=len(b.parts)
        def form(shape,d,e,material,name):b.prism(shape,d,e,lambda u,z,v:place(side,u,v,z),material,name)
        def part(l,r,z,t,d,e,m,n):form(box(l,z,r,t),d,e,m,n)
        aperture=box(-.60,.99,.60,2.24);rail=box(-.61,.26,.61,.89)
        wall=box(-EDGE,0,EDGE,2.65).difference(aperture.union(rail))
        form(wall,-.19,0,YELLOW,'Ochre corner pier and edges of the two upper openings')
        part(-.61,.61,.26,.89,-.177,-.155,YELLOW,'Recessed yellow panel behind vertical ironwork')
        frame_outer=box(-.61,.98,.61,2.25);inner=box(-.564,1.035,.564,2.195)
        if side:form(box(-.651,.948,.651,2.295).difference(frame_outer),-.039,.029,LIGHT,'Pale band framing the return window')
        form(frame_outer.difference(inner),-.15,-.089,STEEL,'Deep perimeter of steel window')
        form(inner,-.169,-.145,PANE,'Inset plane behind the steel lights')
        part(-.564,.564,1.904,1.938,-.146,-.086,STEEL,'Broad transom below upper hopper')
        for x in(-.282,0,.282):
            half=.017 if x==0 else .010
            part(x-half,x+half,1.035,2.195,-.145,-.088,STEEL,'Long muntin dividing the vertical rows')
        for z in(1.254,1.477,1.698):
            part(-.564,.564,z-.009,z+.009,-.143,-.090,STEEL,'Narrow rail across two steel casements')
        for i in range(-4,5):
            x=i*.128
            if side and abs(i)<=1:continue
            part(x-.009,x+.009,.26,.89,-.063,-.042,IRON,'Straight square lower iron bar')
        if side:
            curveN=13 if not far else 5
            for i in range(4):
                # Concave arc with its ends meeting the next arc at the four points.
                a=i*pi/2;t=(i+1)*pi/2
                p=np.array([.174*cos(a),.23*sin(a)]);q=np.array([.174*cos(t),.23*sin(t)])
                mid=(p+q)*.22
                points=[]
                for f in np.linspace(0,1,curveN):
                    v=(1-f)**2*p+2*f*(1-f)*mid+f*f*q;points.append((v[0],v[1]+.575))
                band=LineString(points).buffer(.013,cap_style=1,join_style=2,quad_segs=5 if not far else 3)
                form(band,-.060,-.036,IRON,'One of four inward-curved arms in the return grille')
        for z,t,e,mat in [(0,.092,.093,SILL),(.092,.156,.119,SILL),(.156,.210,.072,SILL),(2.56,2.65,.107,EAVE)]:
            part(-EDGE,EDGE,z,t,-.19,e,mat,'Projecting horizontal line at the base or eave')

        for group in b.parts[start:]:
            if group['material']==YELLOW:group['texcoords']=[[((y if side else x)+EDGE)/(2*EDGE),z/2.65]for x,y,z in group['vertices']]

    # At the outside corner the photographed sill and eave turn without a notch.
    for z,t,e,mat in [(0,.092,.093,SILL),(.092,.156,.119,SILL),(.156,.210,.072,SILL),(2.56,2.65,.107,EAVE)]:
        b.prism(box(EDGE,z,EDGE+e,t),0,e,lambda x,z,d:(x,-d,z),mat,'Corner return closing the projecting horizontal trim')
