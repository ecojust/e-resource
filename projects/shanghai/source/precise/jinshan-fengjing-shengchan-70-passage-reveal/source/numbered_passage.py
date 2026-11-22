"""No. 70 Shengchan Street: photographed passage and exposed masonry at the jamb."""
from pathlib import Path
import json,math,numpy as np
from PIL import Image
from shapely.geometry import box,shape,Polygon
from shapely.affinity import scale,translate
ID='jinshan-fengjing-shengchan-70-passage-reveal'
LIME='Mottled grey lime plaster';BRICK='Dark exposed bricks';MORTAR='Dark mortar bed';NUMBER='Green enamel address plate';LETTER='Pale green-white inscription';FLOOR='Rough grey passage paving';SHADE='Unresolved shadow behind observed passage'
PALETTE={m:dict(color=c,roughness=r)for m,c,r in ((LIME,[1,1,1],.95),(BRICK,[1,1,1],.91),(MORTAR,[.34,.32,.28],.98),(NUMBER,[.10,.29,.22],.65),(LETTER,[.79,.84,.66],.71),(FLOOR,[.49,.46,.40],.96),(SHADE,[.125,.123,.107],.98))}
def texture():
    f=Path(__file__).with_name('mottled-limework-and-exposed-grey-brick.png')
    if not f.exists():
        rng=np.random.default_rng(919);h,w=450,250;y,x=np.indices((h,w))
        def field(a,b):return np.asarray(Image.fromarray(rng.integers(0,255,(a,b),dtype='uint8')).resize((w,h),Image.Resampling.BICUBIC),float)-127
        low=field(8,10);grain=field(23,28);stain=np.maximum(0,low+grain*.32-18)
        lime=np.array([193,189,171])+(.12*grain+.07*field(7,72)-.54*stain+rng.normal(0,4,(h,w)))[:,:,None]
        brick=np.array([93,91,81])+(.27*field(45,18)+.15*grain+rng.normal(0,7,(h,w)))[:,:,None]
        Image.fromarray(np.concatenate((lime,brick),axis=1).clip(0,255).astype('uint8')).quantize(195).save(f)
    for m in (LIME,BRICK):PALETTE[m]['texture']=str(f)
def glyphs():
    source=json.loads(Path(__file__).with_name('green-numberplate.json').read_bytes())
    for line,z,w,h in [('70',2.21,.077,.118),('生产街',2.095,.046,.044)]:
        for i,ch in enumerate(line):
            p=shape(source[ch]);a,b,c,d=p.bounds;p=scale(p,.82*w/(c-a),h/(d-b),origin=(0,0));a,b,c,d=p.bounds
            yield translate(p,-.535+(i-(len(line)-1)/2)*w-(a+c)/2,z-(d+b)/2)
def add_building(b,far=False):
    texture()
    def face(p,front,back,m,label):b.prism(p,-back,-front,lambda x,z,d:(x,-d,z),m,label)
    def plate(x,y,z,w,d,h,m,n):b.box((x,y,z),(w,d,h),m,label=n)
    extent=box(-1.15,.01,1.13,2.85);mouth=box(-.31,-.02,.55,2.179)
    weather=Polygon([(.55,0),(1.13,0),(1.13,.48),(.99,.48),(.99,.55),(.89,.57),(.87,.64),(.79,.64),(.78,.67),(.70,.64),(.69,.60),(.58,.61),(.55,.57)])
    lowleft=Polygon([(-1.15,0),(-.31,0),(-.31,.13),(-.48,.142),(-.53,.10),(-.73,.11),(-.83,.165),(-.93,.14),(-1.15,.19)])
    head=Polygon([(-.10,2.178),(.37,2.178),(.39,2.222),(.28,2.239),(.23,2.264),(.154,2.239),(.066,2.23),(.03,2.249),(-.075,2.229)])
    patch=weather.union(lowleft).union(head)
    face(extent.difference(mouth).difference(patch),-.055,.27,LIME,'Street plaster with irregular edges where the brick core is exposed')
    face(patch,.014,.27,MORTAR,'Bedding behind the exposed face')
    for j in range(22):
        z=j*.111
        for i in range(-5,6):
            x=i*.292+(j%2)*.146
            p=box(x+.004,z+.004,x+.285,z+.104).intersection(patch)
            if not p.is_empty and p.area>.00015:face(p,-.036,.026,BRICK,'Visible staggered street brick')
    # Two complete returns, with patchy exposed lower courses and a lit sliver of paving.
    for side,left,right in ((-1,-.402,-.31),(1,.55,.639)):
        plate((left+right)/2,.728,1.085,right-left,1.26,2.17,LIME,'Wall return inside the rectangular passage')
        for j in range(4 if side<0 else 6):
            for i in range(5):
                yy=.26+i*.226+(j%2)*.073
                if yy>1.34 or (i+j)%8==5:continue
                xx=right+.004 if side<0 else left-.004
                plate(xx,yy,.059+j*.109,.014,.223,.101,BRICK,'Exposed staggered course returning along the passage')
    plate(.123,.724,.009,.875,1.45,.033,FLOOR,'Paving through the photographed opening')
    plate(.118,.747,2.205,.865,1.32,.06,LIME,'Underside of rectangular entrance head')
    # A shaded view plane records the darkness visible beyond the surveyed jambs.
    # It is set behind both returns and cropped free of the exterior wall silhouette.
    pts=[(-.32,1.47,.025),(.57,1.60,.025),(.57,1.60,2.19),(-.32,1.47,2.19)]
    b.add(pts,[(0,1,2,3)],SHADE,'Photographic shadow beyond the dimensioned returns')
    plate(-.535,-.069,2.165,.259,.027,.241,NUMBER,'Green enamel plate on left jamb')
    for p in glyphs():face(p.simplify(.0006) if far else p,-.088,-.082,LETTER,'Number or street name in light enamel')
    if not far:
        for x in (-.649,-.419):
            for z in (2.06,2.271):
                plate(x,-.086,z,.007,.006,.009,NUMBER,'Small raised fastening at a plate corner')
    for part in b.parts:
        if part['material'] not in (LIME,BRICK):continue
        idx=int(part['material']==BRICK)
        part['texcoords']=[((idx+.012+.975*(x+1.18+.16*y)/2.55)/2,.99-.973*z/2.88)for x,y,z in part['vertices']]
