"""Curved roughcast bay photographed in the side lane of Lane 365 West Jianguo Road."""
from pathlib import Path
import numpy as np
from PIL import Image
from shapely.geometry import box,Polygon,Point,LineString
from shapely.ops import unary_union
ID='xuhui-tailaxincun-curved-bay-and-arched-window'
PLASTER='Ochre roughcast on cylindrical bay';GLASS='Deep grey window glass';WHITE='Chalk white cornice';FRAME='Dark painted steel';CLAY='Weathered terracotta ridge tiles';LIP='Sunlit terracotta nose'
PALETTE={k:dict(color=c,roughness=r) for k,c,r in [(PLASTER,[1.,1.,1.],.96),(GLASS,[.22,.248,.246],.32),(WHITE,[.88,.851,.775],.85),(FRAME,[.185,.183,.164],.63),(CLAY,[.535,.249,.151],.88),(LIP,[.638,.321,.197],.87)]}
R=1.40;LIMIT=R*.99
def texture():
    f=Path(__file__).with_name('ochre-roughcast.png')
    if not f.exists():
        rng=np.random.default_rng(755)
        grains=rng.normal(0,9,(384,384,1))
        values=np.array([195,160,105])+grains
        Image.fromarray(np.clip(values,0,255).astype('uint8')).quantize(112).save(f)
    PALETTE[PLASTER]['texture']=str(f)
def arch(r,bottom=.67,spring=1.51,n=36):
    return Polygon([(-r,bottom),(r,bottom),(r,spring),*[(r*np.cos(t),spring+r*np.sin(t))for t in np.linspace(0,np.pi,n+1)],(-r,bottom)])
def pos(u,z,d):
    theta=u/R
    return ((R+d)*np.sin(theta),R-(R+d)*np.cos(theta),z)
def add_building(b,far=False):
    texture();n=28 if far else 58
    opening=arch(.292);inner=arch(.266,.697)
    def skin(poly,a,c,mat,text,lo=-LIMIT,hi=LIMIT):
        for l,r in zip(np.linspace(lo,hi,n+1)[:-1],np.linspace(lo,hi,n+1)[1:]):
            part=poly.intersection(box(l,-.1,r,3.7))
            if part.area>1e-9:b.prism(part,a,c,pos,mat,text)
    def belt(z0,z1,d,mat,name):
        skin(box(-LIMIT,z0,LIMIT,z1),-.035,d,mat,name)
    skin(box(-LIMIT,0,LIMIT,3.05).difference(opening),-.175,0,PLASTER,'Ochre curved wall and window reveal')
    skin(opening.difference(inner),-.08,-.032,FRAME,'Outer steel surround and sill')
    skin(inner,-.105,-.085,GLASS,'Recessed window panes')
    for z in [.953,1.219,1.484]:
        skin(inner.intersection(box(-.28,z-.010,.28,z+.010)),-.083,-.045,FRAME,'Three horizontal glazing bars')
    skin(box(-.011,.694,.011,1.482),-.085,-.044,FRAME,'Central rectangular sash mullion')
    fan=arch(.155,1.49,1.488,24).boundary.buffer(.009).intersection(box(-.265,1.493,.265,1.80))
    skin(fan,-.084,-.045,FRAME,'Semicircular inner fanlight rib')
    for sign in [-1,1]:
        spoke=LineString([(sign*.115,1.598),(sign*.19,1.688)]).buffer(.007)
        skin(spoke,-.084,-.048,FRAME,'Diagonal fanlight spokes')
    belt(.11,.185,.039,WHITE,'White lower stringcourse following the bay')
    belt(.18,.23,.052,WHITE,'Upper projecting lip on lower stringcourse')
    belt(2.562,2.61,.019,WHITE,'Frieze head below crowning cornice')
    fingers=[box(t-.044,2.473,t+.044,2.57).union(Point(t,2.473).buffer(.044,resolution=7))for t in np.arange(-1.37,1.39,.159)]
    skin(unary_union(fingers),-.015,.016,WHITE,'Round-ended white dentils against yellow render')
    for a,c,d in [(2.607,2.651,.033),(2.651,2.684,.064),(2.684,2.713,.084),(2.713,2.755,.053),(2.755,2.806,.093),(2.806,2.847,.108)]:
        belt(a,c,d,WHITE,'Stepped white cornice molding')
    belt(2.848,2.91,.055,CLAY,'Fascia underneath terracotta tiles')
    for u in np.arange(-1.385,1.39,.145):
        num=8 if far else 14
        for j in range(num):
            angle=np.array([j,j+1])*np.pi/num
            x=.076*np.cos(angle);z=.048*np.sin(angle)
            verts=[pos(u+v,base+h,d)for base,d in [(2.90,.099),(3.035,-.20)]for v,h in zip(x,z)]
            b.add(verts,[(0,1,3),(0,3,2)],CLAY,'Curved terracotta pantile')
            nose=[pos(u+v,2.90+h,d)for d in [.099,.11]for v,h in zip(x,z)]
            b.add(nose,[(0,1,3),(0,3,2)],LIP,'Roof tile projecting nose')
    for part in b.parts:
        if part['material']==PLASTER:part['texcoords']=[[(np.arctan2(x,R-y)*R+LIMIT)/1.3,z/1.4]for x,y,z in part['vertices']]
