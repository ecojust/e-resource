"""The eight numbered timber shutters to the right of the green No. 190 sign, Xinchang Street."""
from pathlib import Path
import math
import numpy as np
from PIL import Image
from shapely.geometry import Polygon,LineString
from shapely.ops import unary_union
ID='pudong-zheng-residence-numbered-shutters'
WOOD='Weathered brown vertical boards';FRAME='Darker rail and jamb timber';GUIDE='Worn grey front ledge';PLASTER='Pale wall below ledge';MARK='Old pale numbering';BACK='Shadow inside board joints'
PALETTE={k:dict(color=c,roughness=r) for k,c,r in ((WOOD,[1,1,1],.91),(FRAME,[1,1,1],.85),(GUIDE,[1,1,1],.86),(PLASTER,[.81,.77,.69],.94),(MARK,[.641,.573,.454],.90),(BACK,[.105,.072,.049],.95))}
PITCH=.229
TOTAL=PITCH*8
def texture():
    file=Path(__file__).with_name('vertical-grain-and-worn-sill.png')
    if not file.exists():
        r=np.random.default_rng(863);h,w=300,256;y,x=np.indices((h,w))
        streak=np.asarray(Image.fromarray(r.integers(0,255,(7,w),dtype='uint8')).resize((w,h),Image.Resampling.BILINEAR),float)-128
        knots=np.sin(x*.57+.85*np.sin(y*.024+x*.023))+.37*np.sin(x*1.81+.44*np.cos(y*.041))
        wear=np.maximum(0,np.asarray(Image.fromarray(r.integers(0,255,(14,34),dtype='uint8')).resize((w,h),Image.Resampling.BILINEAR),float)-150)
        n=streak*.17+knots*6+wear*.25+r.normal(0,3.2,(h,w))
        a=np.concatenate([np.array(c)+(n*f)[:,:,None] for c,f in (([110,78,59],1),([74,55,47],.8),([130,110,90],.9))],axis=1)
        Image.fromarray(a.clip(0,255).astype('uint8')).quantize(160).save(file)
    for k in (WOOD,FRAME,GUIDE): PALETTE[k]['texture']=str(file)

# Number paths redrawn as plain strokes. Coordinates are normalized character width and height.
DIGITS=[
 [[(.13,.76),(.53,1),(.53,0)],[(.20,0),(.85,0)]],
 [[(.04,.82),(.17,.97),(.54,1),(.86,.86),(.89,.66),(.73,.47),(.13,.02),(.91,.02)]],
 [[(.10,.86),(.39,1),(.72,.98),(.90,.78),(.79,.60),(.46,.51),(.76,.45),(.95,.23),(.81,.04),(.45,0),(.12,.09)]],
 [[(.64,0),(.64,1),(.02,.37),(.95,.37)]],
 [[(.89,.98),(.23,.98),(.16,.54),(.53,.63),(.82,.52),(.93,.28),(.81,.08),(.57,0),(.22,.04),(.05,.15)]],
 [[(.81,.94),(.52,1),(.20,.79),(.09,.46),(.12,.18),(.29,.03),(.62,0),(.85,.13),(.89,.34),(.76,.52),(.55,.58),(.29,.53),(.10,.35)]],
 [[(.04,.96),(.91,.96),(.42,.02)]],
 [[(.50,.51),(.20,.63),(.11,.83),(.26,.96),(.52,1),(.79,.95),(.89,.78),(.75,.61),(.50,.51),(.18,.39),(.09,.20),(.22,.05),(.50,0),(.79,.06),(.90,.24),(.80,.40),(.50,.51)]]]
def add_building(b,far=False):
    texture()
    def box(x,y,z,w,d,h,m,n):b.box((x,y,z),(w,d,h),m,label=n)
    box(0,.037,1.40,TOTAL,.028,1.46,BACK,'Dark joints at the back of the vertical shutters')
    box(0,.017,.287,TOTAL+.07,.129,.54,PLASTER,'White lower masonry beneath shop shutters')
    for i in range(8):
        c=(i-3.5)*PITCH
        box(c,0,1.48,PITCH-.006,.060,1.35,WOOD,f'Upper shutter board {i+1}')
        box(c,-.012,.666,PITCH-.006,.085,.21,WOOD,f'Lower panel {i+1} below the retaining ledge')
        pieces=[]
        for path in DIGITS[i]:
            line=[(c+(u-.50)*.042,.985+v*.080) for u,v in path]
            pieces.append(LineString(line).buffer(.0039,cap_style=1,join_style=1,resolution=2 if far else 5))
        b.prism(unary_union(pieces),.0304,.0328,lambda x,z,d:(x,-d,z),MARK,'Hand-shaped pale number '+str(i+1))
    for x in (-TOTAL/2-.042,TOTAL/2+.042):
        box(x,-.004,1.10,.080,.143,2.17,FRAME,'Full-height timber jamb')
    for z,w,y,d,h,n in ((2.174,TOTAL+.14,-.009,.145,.113,'Top lintel'),(1.890,TOTAL,-.051,.055,.058,'Upper horizontal shutter batten'),(.803,TOTAL,-.040,.102,.058,'Straight retaining strip below the ledge'),(.549,TOTAL,-.023,.121,.050,'Dark moulding above lower white wall')):
        box(0,y,z,w,d,h,FRAME,n)
    # Visible outer face is round above a flat fillet. The end stops project in front of the ledge.
    side=[(.04,.823),(.04,.932),(-.067,.932)]
    for a in np.linspace(math.pi/2,math.pi,4 if far else 12):
        side.append((-.067+.070*math.cos(a),.862+.070*math.sin(a)))
    side.extend([(-.137,.829),(-.117,.821)])
    b.prism(Polygon(side),-TOTAL/2+.015,TOTAL/2-.015,lambda y,z,x:(x,y,z),GUIDE,'Worn retaining ledge with rounded outer edge')
    for sign in (-1,1):
        x=sign*(TOTAL/2-.014)
        poly=Polygon([(.012,.790),(-.145,.790),(-.145,.919),(-.109,1.004),(-.057,1.035),(.012,1.035)])
        b.prism(poly,x-.026,x+.026,lambda y,z,x:(x,y,z),FRAME,'Raised stop at the end of the ledge')
    for j,p in enumerate(b.parts):
        m=p['material']
        if m not in (WOOD,FRAME,GUIDE): continue
        strip=(WOOD,FRAME,GUIDE).index(m)
        coords=[]
        for x,y,z in p['vertices']:
            if m==WOOD: u=((x+1.09)*.454+((j*29)%31)/155)%1;v=min(.99,max(.012,z/2.28))
            elif m==GUIDE or max(t[0] for t in p['vertices'])-min(t[0] for t in p['vertices'])>.50:
                u=min(.985,max(.012,(z%1.6)*.49+.07));v=(x+1.10)/2.23
            else:u=min(.98,max(.015,abs(x)*.64+(y+.2)*.6));v=z/2.26
            coords.append(((strip+.023+.954*u)/3,.99-.965*v))
        p['texcoords']=coords
