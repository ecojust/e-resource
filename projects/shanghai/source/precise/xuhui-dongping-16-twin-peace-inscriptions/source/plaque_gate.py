"""Twin vertical entrance inscriptions and dark bow-topped gates in the No. 16 Dongping Road photograph."""
from pathlib import Path
import json
import numpy as np
from PIL import Image
from shapely.geometry import box,Polygon,shape,LineString
from shapely.affinity import translate,scale
ID='xuhui-dongping-16-twin-peace-inscriptions'
BRICK='Red-brown glazed pier';CAP='Burnt umber masonry';PLAQUE='Dark green black plaques';EDGE='Bronze outer rule';GOLD='Aged light-gold characters';GATE='Dark green iron entrance';RIB='Painted raised gate ribs';STONE='Grey base course';LAMP='Ivory globe lamp';FIELD='Recessed iron panel'
PALETTE={k:dict(color=c,roughness=r)for k,c,r in [(BRICK,[1.,1.,1.],.89),(CAP,[.414,.252,.171],.92),(PLAQUE,[.101,.143,.127],.64),(EDGE,[.596,.44,.279],.67),(GOLD,[.816,.743,.571],.58),(GATE,[.119,.192,.169],.7),(RIB,[.189,.261,.222],.69),(STONE,[.457,.436,.401],.91),(LAMP,[.851,.834,.761],.56),(FIELD,[.102,.146,.135],.90)]}
def crown(x):return 2.02+.54*(1-(abs(x)/1.65)**1.65)**2
def texture():
    dest=Path(__file__).with_name('pier-brick.png')
    if not dest.exists():
        y,x=np.indices((256,256));rng=np.random.default_rng(735);seams=(y%17<1)|((x+((y//17)%2)*24)%48<1)
        a=np.array([161,104,75])+rng.normal(0,3.,x.shape)[:,:,None]+rng.normal(0,5,(17,7))[(y//17),((x+((y//17)%2)*24)//48),None]
        a[seams]=np.array([143,110,96]);Image.fromarray(a.clip(0,255).astype('uint8')).quantize(93).save(dest)
    PALETTE[BRICK]['texture']=str(dest)
def letters(cx):
    src=json.loads(Path(__file__).with_name('plaque-letter-outlines.json').read_bytes())
    for j,ch in enumerate('和平官邸'):
        top=1.72-j*.315;outline=shape(src[ch]);bounds=outline.bounds
        factor=.228/max(bounds[2]-bounds[0],bounds[3]-bounds[1]);poly=scale(outline,factor,factor,origin=(0,0));x0,y0,x1,y1=poly.bounds
        yield ch,translate(poly,cx-(x0+x1)/2,top-y1)
def add_building(b,far=False):
    texture()
    def skin(poly,a,c,m,label):b.prism(poly,a,c,lambda x,z,d:(x,-d,z),m,label)
    def block(l,r,lo,hi,a,c,m,label):skin(box(l,lo,r,hi),a,c,m,label)
    for sign in [-1,1]:
        x=sign*1.95
        for lo,hi,w,d,mat in [(0,.102,.348,.159,STONE),(.099,1.971,.307,.129,BRICK),(1.965,2.002,.329,.142,CAP),(2.0,2.050,.353,.169,BRICK),(2.05,2.103,.327,.142,CAP)]:
            block(x-w,x+w,lo,hi,-.335,d,mat,'Masonry pier and projecting cap')
        profile=[(2.101,.052),(2.119,.054),(2.127,.043),(2.137,.065),(2.166,.099),(2.209,.112),(2.251,.095),(2.282,.062),(2.296,.006)]
        b.lathe((x,-.02),profile,LAMP,14 if far else 34,'Small pale spherical pier lantern')
        block(x-.238,x+.238,.172,1.862,.129,.149,EDGE,'Fine outline around the name plaque')
        block(x-.228,x+.228,.183,1.852,.148,.159,PLAQUE,'Dark vertical inscribed panel')
        for ch,poly in letters(x):
            skin(poly.simplify(.0024 if far else .0005,preserve_topology=True),.158,.169,GOLD,'Raised inscription '+ch)
    for sign in [-1,1]:
        l,r=(-1.644,-.009) if sign<0 else(.009,1.644);samples=np.linspace(l,r,22 if far else 50)
        surface=Polygon([(l,.108),(r,.108),*[(x,crown(x))for x in samples[::-1]]])
        skin(surface,-.145,-.073,GATE,'One leaf of the central two-part iron gate')
        band=Polygon([*[(x,crown(x)-.045)for x in samples],*[(x,crown(x))for x in samples[::-1]]]);skin(band,-.074,-.040,RIB,'Curved top rail')
        for x in np.linspace(l+.068,r-.063,13):
            block(x-.008,x+.008,1.486,crown(x)-.046,-.074,-.051,RIB,'Tall vertical rib in upper panels')
        for z in [.291,.562,.981,1.364,1.477]:block(l,r,z-.012,z+.012,-.073,-.050,RIB,'Horizontal iron rail over recessed panels')
        for x in np.linspace(l+.135,r-.135,6):
            block(x-.008,x+.008,.11,1.457,-.074,-.047,RIB,'Thin lower panel divider')
        for x in np.linspace(l+.169,r-.169,5):
            poly=Polygon([(x,.635),(x+.103,.791),(x,.940),(x-.103,.791)])
            skin(poly.boundary.buffer(.007,join_style=2),-.073,-.058,FIELD,'Lozenge ornament in a lower panel')
    for part in b.parts:
        if part['material']==BRICK:part['texcoords']=[[(x+2.35)/1.4,z/1.4]for x,y,z in part['vertices']]
