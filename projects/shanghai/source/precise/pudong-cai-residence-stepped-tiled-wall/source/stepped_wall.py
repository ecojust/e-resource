"""Two visible stepped wall ends with triangular relief panels, Gaoqiao Cai residence."""
from pathlib import Path
import math
import numpy as np
from PIL import Image
from shapely.geometry import Polygon,LineString
from shapely.ops import unary_union
ID='pudong-cai-residence-stepped-tiled-wall'
LIME='Grey cream side plaster';END='Paler stepped end plaster';BAND='Grey undercourses';TILE='Dark fired end tile';TIP='Edge of black ridge';ORN='Pale relief below triangular cap'
PALETTE={m:dict(color=c,roughness=r) for m,c,r in ((LIME,[1,1,1],.94),(END,[1,1,1],.94),(BAND,[.52,.48,.395],.92),(TILE,[1,1,1],.91),(TIP,[.228,.219,.197],.93),(ORN,[.758,.707,.605],.93))}
def texture():
    f=Path(__file__).with_name('pale-mortar-and-black-caps.png')
    if not f.exists():
        g=np.random.default_rng(875);h,w=268,208
        layer=lambda a,b:np.asarray(Image.fromarray(g.integers(0,255,(a,b),dtype='uint8')).resize((w,h),Image.Resampling.BILINEAR),float)-127
        n=.16*layer(14,13)+.13*layer(5,65)+g.normal(0,3,(h,w))
        a=np.concatenate([np.array(c)+(n*s)[:,:,None]for c,s in (([177,164,137],1.2),([205,195,172],.78),([78,76,66],.95))],axis=1)
        Image.fromarray(a.clip(0,255).astype('uint8')).quantize(176).save(f)
    for m in (LIME,END,TILE):PALETTE[m]['texture']=str(f)

# Heights refer to the bottom of each triangular end moulding, with the two photographed end faces set back in succession.
ENDS=[(-.67,.98),(.12,1.92)]
def add_building(b,far=False):
    texture()
    def front(poly,y0,y1,m,n):
        b.prism(poly,-y1,-y0,lambda x,z,d:(x,-d,z),m,n)
    for index,(y,z) in enumerate(ENDS):
        end=.14 if index==0 else 1.04
        center=(y+end)/2;wide=.375
        b.box((0,center,z/2),(wide,end-y,z),LIME,label='Step in side wall')
        b.box((0,y-.004,(z-.20)/2),(wide+.001,.014,z-.20),END,label='Paler front edge of the step')
        for j,(dz,w,d,h,m) in enumerate(((-.202,.4,.051,.032,BAND),(-.164,.403,.059,.044,END),(-.105,.405,.066,.055,END),(-.060,.415,.079,.024,BAND),(-.028,.436,.096,.040,END),(.007,.46,.102,.030,END))):
            b.box((0,y-d/2,z+dz),(w,d,h),m,label='Layer of moulding below one triangular end')
        pediment=Polygon([(-.237,z),(.237,z),(.237,z+.097),(0,z+.278),(-.237,z+.097)])
        front(pediment,y-.103,y+.031,END,'Pale triangular relief panel')
        frame=LineString([(-.237,z+.091),(0,z+.274),(.237,z+.091)]).buffer(.012,cap_style=2,join_style=2)
        front(frame,y-.119,y-.104,BAND,'Fine grey sloping edge over the relief panel')
        # Shallow curved impressions are visible against the triangular face; record their scope without assigning a symbolic name.
        arcs=[]
        for lev,cxs in ((.101,[-.135,-.047,.046,.135]),(.157,[-.089,0,.089]),(.205,[0])):
            for c in cxs:
                ar=np.linspace(math.pi,2*math.pi,5 if far else 13)
                arcs.append(LineString([(c+.036*math.cos(t),z+lev+.020*math.sin(t))for t in ar]).buffer(.005,cap_style=1,resolution=2))
        for p in unary_union(arcs).geoms:
            front(p,y-.118,y-.103,ORN,'Small curved relief below triangular cap')
        # The cap spans the end thickness, climbs toward the stepped face and throws a small horn upward.
        rise=lambda distance:.147*math.exp(-3.7*(distance+.10))+.045*math.exp(-13*(distance+.10))
        starts=np.linspace(y-.157,end-.095,7 if index==0 else 9)
        for j,start in enumerate(starts):
            stop=min(end+.03,start+(starts[1]-starts[0])+.019)
            for side in (-1,1):
                pts=[];faces=[];sub=4 if far else 9
                for yy in np.linspace(start,stop,sub):
                    r=rise(yy-y)
                    high=z+.259+.65*r; low=z+.105+.07*r
                    for x,zz in ((0,high),(.235,low),(.250,low-.004),(.250,low-.032),(.236,low-.032),(0,high-.033)):
                        pts.append((side*x,yy,zz))
                for k in range(sub-1):
                    for c in range(6):faces.append((6*k+c,6*k+(c+1)%6,6*(k+1)+(c+1)%6,6*(k+1)+c))
                faces.extend([tuple(range(5,-1,-1)),tuple(range((sub-1)*6,sub*6))])
                if side>0:faces=[tuple(reversed(p))for p in faces]
                b.add(pts,faces,TILE,'Overlapping sloping dark tiles on each side')
        for j,(start,stop) in enumerate(zip(np.linspace(y-.18,end-.02,10)[:-1],np.linspace(y-.18,end-.02,10)[1:])):
            pts=[];faces=[];rad=.050;sub=6 if far else 17
            for yy in (start,stop+.014):
                h=z+.272+.65*rise(yy-y)
                for k in range(sub+1):
                    a=k*math.pi/sub;pts.append((rad*math.cos(a),yy,h+rad*math.sin(a)))
            for k in range(sub):faces.append((k,k+sub+1,k+sub+2,k+1))
            faces.extend([tuple(range(sub+1)),tuple(range(2*sub+1,sub,-1))])
            b.add(pts,faces,TIP,'Stacked dark ridge pieces rising at each end')
    for p in b.parts:
        mat=p['material']
        if mat not in (LIME,END,TILE):continue
        s=(LIME,END,TILE).index(mat)
        p['texcoords']=[((s+.025+.95*min(1,max(0,(.76+y)/1.85+.14*x)))/3,.986-.955*min(1,max(0,z/2.70))) for x,y,z in p['vertices']]
