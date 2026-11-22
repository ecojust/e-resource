"""Interleaved convex cap tiles and concave, pointed drip ends above the Zhonghua Lou river frontage."""
from pathlib import Path
import math,numpy as np
from PIL import Image
from shapely.geometry import Polygon
ID='pudong-zhonghua-lou-pointed-drip-tiles'
TILE='Moss-flecked upper tile';DARK='Dark underside of ceramic';LIP='Pointed drip end';WOOD='Old eaves timber';EDGE='Light weathered cap rim'
PALETTE={k:dict(color=c,roughness=r) for k,c,r in ((TILE,[1,1,1],.90),(DARK,[.27,.25,.194],.94),(LIP,[1,1,1],.91),(WOOD,[1,1,1],.88),(EDGE,[1,1,1],.90))}
PITCH=.236
COUNT=9
CENTRES=[(i-(COUNT-1)/2)*PITCH for i in range(COUNT)]
def texture():
    f=Path(__file__).with_name('clay-lichen-and-timber.png')
    if not f.exists():
        rng=np.random.default_rng(871);h,w=224,272
        field=lambda hw:np.asarray(Image.fromarray(rng.integers(0,255,hw,dtype='uint8')).resize((w,h),Image.Resampling.BILINEAR),float)-127
        moss=field((38,41));large=field((11,10));noise=rng.normal(0,5,(h,w))
        col=np.array([121,110,79])+(.20*large+.26*moss+noise)[:,:,None]+np.array([.01,.16,-.15])*np.maximum(0,moss)[:,:,None]
        wet=np.array([104,93,66])+(.21*moss+.23*large+noise)[:,:,None]
        grain=np.array([75,59,47])+(.18*field((65,10))+.12*large+noise*.54)[:,:,None]
        Image.fromarray(np.concatenate((col,wet,grain),axis=1).clip(0,255).astype('uint8')).quantize(192).save(f)
    for k in (TILE,LIP,WOOD,EDGE): PALETTE[k]['texture']=str(f)
def bed(y):return .62+.34*(y+.28)
def dome(dx,r):return math.sqrt(max(0,r*r-dx*dx))
def add_building(b,far=False):
    texture()
    seg=7 if far else 19
    def slab(c,y0,y1,r,up,offset,material,label):
        # Positive semicircle over the shared joint; the channel between adjacent joints is a shallow circular trough.
        points=[];faces=[]
        for y in (y0,y1):
            for thick in (0,.013):
                for j in range(seg+1):
                    theta=math.pi*j/seg;x=-r*math.cos(theta);rise=r*math.sin(theta) if up else -.58*r*math.sin(theta)
                    points.append((c+x,y,bed(y)+offset+rise-thick))
        s=seg+1
        for j in range(seg):
            faces.extend([(j,j+1,2*s+j+1,2*s+j),(s+j,3*s+j,3*s+j+1,s+j+1),(j,s+j,s+j+1,j+1),(2*s+j,2*s+j+1,3*s+j+1,3*s+j)])
        faces.extend([(0,2*s,3*s,s),(seg,s+seg,3*s+seg,2*s+seg)])
        b.add(points,faces,material,label)
    for c in CENTRES:
        for i,(y,far_y) in enumerate(((-.26,.02),(-.018,.262),(.224,.502),(.463,.731))):
            slab(c,y,far_y,.071,True,.019+.009*i,TILE,'One curved cap over two neighbouring pan tiles')
            slab(c,y-.004,y+.010,.073,True,.021+.009*i,EDGE,'Raised front rim on the cap')
        b.box((c,.018,.471),(.084,.665,.097),WOOD,label='Dark cut end of small eaves timber')
    # The drip tongues lie between cap centre lines and descend in a point at the centre of each channel.
    for left,right in zip(CENTRES,CENTRES[1:]):
        c=(left+right)/2
        for i,(y,far_y) in enumerate(((-.32,-.02),(-.057,.247),(.206,.511),(.467,.734))):
            slab(c,y,far_y,.121,False,.058+.010*i,TILE,'Concave channel running to pointed drip')
        half=.115
        xx=np.linspace(-half,half,11 if far else 33)
        top=lambda x:bed(-.32)+.063-.071*math.sqrt(max(0,1-(x/half)**2))
        profile=lambda x:top(x)-.024-.094*(1-abs(x/half))**1.45
        polygon=Polygon([(float(x),top(x))for x in xx]+[(float(x),profile(x))for x in xx[::-1]])
        # The drip face leans slightly forward at its centre and tapers below the pan tile.
        b.prism(polygon,.308,.334,lambda x,z,t:(c+x,-t-(.58-z)*.13,z),LIP,'Front apron of the pan tile tapering into a central point')
    b.box((0,.227,.43),(2.05,.151,.17),WOOD,label='Continuous timber immediately behind visible rafter ends')
    b.box((0,.25,.325),(2.04,.125,.042),WOOD,label='Horizontal eaves fascia below the tile line')
    for j,p in enumerate(b.parts):
        m=p['material'];s=2 if m==WOOD else 1 if m==LIP else 0
        p['texcoords']=[((s+.025+.947*min(1,max(0,(x+1.06)/2.12)))/3,.986-.949*min(1,max(0,(y+.39)/1.18+.05*z)))for x,y,z in p['vertices']]
