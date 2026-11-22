"""Four recessed panels in the gateway heading at No. 19 Wujiazhai, Dahong Village."""
from pathlib import Path
import math,numpy as np
from PIL import Image
from shapely.geometry import Polygon,box
ID='pudong-wujiazhai-no19-four-gate-panels'
LIME='Pale gate wall';FRAME='Lighter projecting frame';FIELD='Weathered grey recessed faces';FINE='Grey inward bevels';STONE='Grey lower carved beam'
PALETTE={k:dict(color=c,roughness=r) for k,c,r in ((LIME,[1,1,1],.94),(FRAME,[.780,.748,.660],.91),(FIELD,[1,1,1],.92),(FINE,[.524,.512,.445],.90),(STONE,[1,1,1],.92))}
OPEN=[(-.79,-.47,.54,1.20),(-.375,.375,.57,1.20),(.47,.79,.54,1.20),(-.68,.68,1.43,1.68)]
def texture():
    p=Path(__file__).with_name('plaster-grey-fields-and-stone.png')
    if not p.exists():
        g=np.random.default_rng(887);h,w=250,256
        noise=lambda hh,ww:np.asarray(Image.fromarray(g.integers(0,255,(hh,ww),dtype='uint8')).resize((w,h),Image.Resampling.BILINEAR),float)-127
        f=noise(20,23);mid=noise(70,90);grain=g.normal(0,3.6,(h,w))
        pale=np.array([210,202,179])+(.10*f+.04*mid+grain*.7)[:,:,None]
        grey=np.array([149,148,128])+(.20*f+.22*mid+grain)[:,:,None]
        st=np.array([156,149,128])+(.17*f+.19*mid+grain*.8)[:,:,None]
        Image.fromarray(np.concatenate((pale,grey,st),axis=1).clip(0,255).astype('uint8')).quantize(160).save(p)
    for k in (LIME,FIELD,STONE):PALETTE[k]['texture']=str(p)
def add_building(b,far=False):
    texture()
    def front(poly,lo,hi,m,name):b.prism(poly,lo,hi,lambda x,z,t:(x,-t,z),m,name)
    def block(x,y,z,w,d,h,mat,name):b.box((x,y,z),(w,d,h),mat,label=name)
    body=box(-.99,.426,.99,1.78)
    for x0,x1,z0,z1 in OPEN:body=body.difference(box(x0,z0,x1,z1))
    front(body,-.178,.149,LIME,'Plaster heading with four actual recesses')
    for i,(x0,x1,z0,z1) in enumerate(OPEN):
        ww=x1-x0;hh=z1-z0;surface=box(x0,z0,x1,z1)
        # Two narrow moulded slopes and a recessed flat. Motifs within the relief field are illegible in the photograph.
        front(surface,-.177,.097,FIELD,'Recessed grey face '+str(i+1))
        steps=[(0.,.142),(.009,.148),(.014,.139),(.028,.108),(.035,.105)]
        if not far:steps=[(0,.142),(.006,.146),(.009,.148),(.012,.145),(.014,.139),(.019,.126),(.028,.108),(.031,.106),(.035,.105)]
        for (d0,h0),(d1,h1) in zip(steps,steps[1:]):
            points=[]
            for d,z in ((d0,h0),(d1,h1)):
                points.extend([(x0+d,-z,z0+d),(x1-d,-z,z0+d),(x1-d,-z,z1-d),(x0+d,-z,z1-d)])
            b.add(points,[(k,(k+1)%4,4+(k+1)%4,4+k) for k in range(4)],FINE,'Fine stepped edges of inset '+str(i+1))
        front(surface.difference(surface.buffer(-.035,join_style=2)),.095,.105,FINE,'Seat to the recessed face')
    for zmid,d,w,h,m,name in ((.406,.445,2.09,.046,FRAME,'Lower projecting gate band'),(1.325,.390,2.03,.040,FRAME,'Two levels of relief divided by a projecting band'),(1.76,.405,2.05,.042,FRAME,'Top heading band'),(1.812,.459,2.11,.060,FINE,'Grey recessed edge under cornice'),(1.867,.475,2.14,.052,FRAME,'Intermediate projecting cornice'),(1.928,.50,2.19,.080,FINE,'Wide stepped cornice'),(1.99,.535,2.23,.051,FRAME,'Upper edge of gate head')):
        block(0,-.006,zmid,w,d,h,m,name)
    for side in (-1,1):
        block(side*.813,.031,.028,.293,.31,.736,LIME,'Short sampled length of gate pier')
        # Raised stone ears flanking the bearer turn down and project beyond the opening.
        points=[(.62,.201),(.755,.195),(.795,.174),(.899,.174),(.932,.236),(.914,.304),(.868,.356),(.722,.369)]
        front(Polygon([(side*x,z)for x,z in points]),-.12,.228,STONE,'Lower projecting stone ear')
    under=Polygon([(-.780,.374),(.780,.374),(.702,.319),(.656,.238),(.634,.215),(-.634,.215),(-.656,.238),(-.702,.319)])
    front(under,-.149,.183,STONE,'Trapezoidal stone beam above open doorway')
    for p in b.parts:
        m=p['material']
        if m in (LIME,FIELD,STONE):
            i=(LIME,FIELD,STONE).index(m)
            p['texcoords']=[((i+.025+.947*min(1,max(0,(x+1.12)/2.24)))/3,.985-.960*min(1,max(0,(z+.34)/2.40)))for x,y,z in p['vertices']]
