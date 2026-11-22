"""Two side-by-side hipped dormers in the long tiled range on Baoding Road."""
from pathlib import Path
from math import floor,ceil
import numpy as np
from PIL import Image
from shapely.geometry import box,Polygon
ID='hongkou-baoding-road-twin-hipped-dormers'
BED='Bed under the roof tiles';FIELD='Dark main roof clay';FRONT='Dusky red dormer tile';SIDE='Weathered brown dormer tile';HIP='Lightly weathered hip caps';WALL='Pale dormer cheeks';FRAME='Grey window surround';GLASS='Dark steel-window glass';MULL='Mullions';SILL='Pale sill'
PALETTE={k:dict(color=c,roughness=r)for k,c,r in [(BED,[.19,.157,.141],.91),(FIELD,[1,1,1],.94),(FRONT,[.433,.228,.176],.92),(SIDE,[.357,.241,.193],.92),(HIP,[.544,.448,.353],.91),(WALL,[.558,.515,.418],.92),(FRAME,[.322,.335,.30],.76),(GLASS,[.197,.232,.232],.38),(MULL,[.511,.53,.483],.68),(SILL,[.58,.55,.466],.88)]}
CENTRES=(-.77,.77);XH=.571;YF=-.395;YB=1.255;APEX=.274;REAR=.957;EAVE=1.402;RISE=.577
def main(x,y):return .51+.65*y
def texture():
    p=Path(__file__).with_name('weathered-grey-tiles.png')
    if not p.exists():
        rng=np.random.default_rng(659);rag=np.array(Image.fromarray(rng.integers(0,255,(25,36),dtype='uint8')).resize((335,240),Image.Resampling.BICUBIC),float)
        image=np.clip([102,91,86]+(.16*(rag-128)+rng.normal(0,4,(240,335)))[:,:,None],0,255).astype('uint8');Image.fromarray(image).save(p)
    PALETTE[FIELD]['texture']=str(p)
def add_building(b,far=False):
    texture()
    def roof(poly,z,mat,name,axis,course,pitch):
        def pos(x,y,h):return x,y,z(x,y)+h
        b.prism(poly,-.050,-.001,pos,BED,name+' bedding')
        # Courses alternate a half-tile and end at the actual hip line.
        x0,y0,x1,y1=poly.bounds
        across=(y0,y1) if axis=='x' else (x0,x1);up=(x0,x1)if axis=='x'else(y0,y1)
        for j in range(floor(up[0]/course),ceil(up[1]/course)):
            u=j*course;shift=pitch*(j%2)/2
            for i in range(floor((across[0]-shift)/pitch),ceil((across[1]-shift)/pitch)):
                v=i*pitch+shift;g=.0037
                tile=box(u+g,v+g,u+course-g,v+pitch-g) if axis=='x'else box(v+g,u+g,v+pitch-g,u+course-g)
                cell=poly.intersection(tile)
                if cell.geom_type!='Polygon' or cell.area<.00017:continue
                b.prism(cell,-.002,.016 if far else .016+((i+2*j)%3)*.0009,pos,mat,name+' individual tile')
    roof(box(-1.81,-.85,1.81,1.79),main,FIELD,'Long dark roof', 'y',.180,.258)
    for c in CENTRES:
        def rect(a,d,z0,z1,back,front,mat,r):
            b.prism(box(a,z0,d,z1),back,front,lambda x,z,y:(x,-y,z),mat,r)
        face=box(c-.503,.268,c+.503,EAVE).difference(box(c-.354,.451,c+.354,1.168))
        b.prism(face,.215,.295,lambda x,z,d:(x,-d,z),WALL,'Front of the dormer with open rectangular window')
        for sign in (-1,1):
            a=c+sign*.492
            b.prism(box(a-.018,-.270,a+.018,1.165),0,EAVE,lambda x,y,z:(x,y,max(z,main(x,y)-.017)),WALL,'Side return into the pitched roof')
        rect(c-.369,c+.369,.430,1.188,.158,.176,GLASS,'Dark inset glazing')
        for x in(c-.358,c-.123,c+.122,c+.358):
            rect(x-.013,x+.013,.447,1.174,.180,.219,MULL,'Four narrow steel uprights delimiting three lights')
        for z in(.454,1.012,1.154):
            rect(c-.355,c+.355,z,z+.022,.181,.217,FRAME,'Window horizontal frame')
        rect(c-.387,c+.387,.408,.450,.226,.318,SILL,'Short sill beneath inset glass')
        xf=lambda x,y:EAVE+RISE*(y-YF)/(APEX-YF)
        xl=lambda x,y:EAVE+RISE*(x-c+XH)/XH
        xr=lambda x,y:EAVE+RISE*(c+XH-x)/XH
        xb=lambda x,y:EAVE+RISE*(YB-y)/(YB-REAR)
        lf=(c-XH,YF);rf=(c+XH,YF);lb=(c-XH,YB);rb=(c+XH,YB);f=(c,APEX);back=(c,REAR)
        for verts,fn,mat,axis,course,pitch in [([lf,rf,f],xf,FRONT,'y',.109,.199),([lf,f,back,lb],xl,SIDE,'x',.119,.204),([rf,rb,back,f],xr,SIDE,'x',.119,.204),([lb,back,rb],xb,FRONT,'y',.087,.192)]:
            roof(Polygon(verts),fn,mat,'Hipped dormer roof plane',axis,course,pitch)
        for pt,end in [(lf,f),(rf,f),(lb,back),(rb,back)]:
            divisions=3 if far else 7
            for j in range(divisions):
                points=[]
                for t in (j/divisions,(j+1)/divisions):
                    points.append((pt[0]+(end[0]-pt[0])*t,pt[1]+(end[1]-pt[1])*t,EAVE+t*RISE+.023))
                b.tube(points,.026 if far else .026+.001*(j%2),HIP,sides=5 if far else 10,label='Ridged hip running from each roof corner')
        b.tube([(c,APEX,EAVE+RISE+.024),(c,REAR,EAVE+RISE+.024)],.030,HIP,sides=6 if far else 12,label='Short longitudinal ridge')
    for p in b.parts:
        if p['material']==FIELD:p['texcoords']=[[(x+1.81)/3.62,(y+.85)/2.64]for x,y,z in p['vertices']]
