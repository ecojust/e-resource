"""Photo-based detail of the numbered red-brick street entrance, No. 100 Wuyi Road."""
from pathlib import Path
import numpy as np
import json
from PIL import Image
from shapely.geometry import box,shape,Point
from shapely.affinity import translate,scale
ID='changning-wuyi-100-numbered-door-and-mailbox'
BRICK='Red brickwork';SAND='Pale cement reveal';STONE='Grey base and threshold';RED='Soldier course';DOOR='Dark recessed leaf';GREEN='Green enamel address';WHITE='Off-white enamel lettering';MAIL='Deep green mailbox';EDGE='Green mailbox rim';BRASS='Brass-coloured lock';LIGHT='Warm porch lamps';PIPE='Pale downpipe'
PALETTE={k:dict(color=c,roughness=r)for k,c,r in [(BRICK,[1.,1.,1.],.95),(SAND,[.627,.586,.52],.91),(STONE,[.54,.532,.489],.90),(RED,[.505,.297,.218],.90),(DOOR,[.128,.113,.107],.79),(GREEN,[.097,.31,.215],.67),(WHITE,[.841,.842,.72],.68),(MAIL,[.142,.237,.173],.72),(EDGE,[.214,.303,.216],.73),(BRASS,[.57,.47,.289],.60),(LIGHT,[.94,.82,.52],.46),(PIPE,[.77,.78,.73],.82)]}
def save_mapped_texture(tile, path):
    """Store the material pattern 2 by 3 times inside one clamp-to-edge image."""
    atlas=Image.new('P',(tile.width*2,tile.height*3))
    atlas.putpalette(tile.getpalette())
    for row in range(3):
        for col in range(2):
            atlas.paste(tile,(col*tile.width,row*tile.height))
    atlas.save(path,optimize=True)

def texture():
    f=Path(__file__).with_name('red-stretcher-course.png')
    if not f.exists():
        y,x=np.indices((512,512));row=y//19;col=(x+27*(row%2))//54;g=np.random.default_rng(703)
        a=np.array([135,73,55])+g.normal(0,7,(30,12))[row,col,None]+g.normal(0,3.5,x.shape)[:,:,None]
        mask=(y%19<=1)|((x+27*(row%2))%54<2);a[mask]=[170,145,125];save_mapped_texture(Image.fromarray(a.clip(0,255).astype('uint8')).quantize(108),f)
    PALETTE[BRICK]['texture']=str(f)
def words(string,cx,cz,hw,hh):
    o=json.loads(Path(__file__).with_name('number-and-street.json').read_bytes())
    for idx,ch in enumerate(string):
        p=shape(o[ch]);x,y,r,t=p.bounds;p=scale(p,hw*.81/(r-x),hh/(t-y),origin=(0,0));x,y,r,t=p.bounds
        yield ch,translate(p,cx+(idx-(len(string)-1)/2)*hw-(x+r)/2,cz-(y+t)/2)
def texts():
    return [(words('100',.758,1.820,.074,.101),.049,WHITE),(words('武夷路',.758,1.747,.047,.032),.049,WHITE),(words('100',.758,1.251,.040,.036),.128,BRASS)]
def add_building(b,far=False):
    texture()
    def panel(poly,a,c,m,desc):b.prism(poly,a,c,lambda x,z,d:(x,-d,z),m,desc)
    def block(l,r,lo,hi,a,c,m,desc):panel(box(l,lo,r,hi),a,c,m,desc)
    l,r=-.685,.400;opening=box(l,-.018,r,2.038)
    panel(box(-1.19,0,1.23,2.43).difference(opening),-.245,0,BRICK,'Red running-bond masonry surrounding the street door')
    block(-1.19,l,0,.198,-.18,.009,STONE,'Cement base left of entrance');block(r,1.23,0,.198,-.18,.009,STONE,'Cement base right of entrance')
    block(l,r,0,.038,-.25,.015,STONE,'Threshold of recessed opening')
    block(l,l+.105,.038,2.038,-.261,-.004,SAND,'Deep rendered left jamb and return')
    block(r-.046,r,.038,2.038,-.261,-.008,SAND,'Narrow cement-lined right jamb')
    block(l+.099,r-.045,.038,2.038,-.30,-.25,DOOR,'Dark recessed door visible from pavement')
    block(l,r,1.989,2.038,-.25,-.010,SAND,'Sheltered soffit in porch')
    for i in range(18):
        x0=l-.024+(r-l+.048)*i/18;x1=l-.024+(r-l+.048)*(i+1)/18
        block(x0+.002,x1-.002,2.038,2.177,-.01,.009,RED,'Vertical red brick at head of opening')
    plate=box(.630,1.710,.885,1.895).buffer(.012,resolution=5)
    panel(plate,-.006,.040,GREEN,'Green enamel number and street plate')
    for x in [.632,.883]:
        for z in [1.719,1.885]:panel(Point(x,z).buffer(.0034,resolution=5),.040,.044,BRASS,'Number-plate corner fixing')
    block(.613,.902,1.176,1.557,.003,.085,MAIL,'Separate green street mailbox')
    block(.631,.883,1.205,1.516,.084,.104,EDGE,'Fine outline of mailbox door')
    block(.641,.871,1.215,1.503,.103,.122,MAIL,'Inset mailbox front')
    block(.604,.910,1.544,1.587,.027,.143,EDGE,'Overhanging top of mailbox')
    block(.835,.851,1.357,1.384,.122,.135,BRASS,'Small mailbox catch')
    for it,base,mat in texts():
        for char,poly in it:panel(poly.simplify(.00045 if far else .0001,preserve_topology=True),base-.011,base,mat,'Visible address character '+char)
    for x in [l+.187,r-.102]:
        panel(Point(x,1.965).buffer(.034,resolution=7 if far else 18),-.127,-.097,LIGHT,'Two sheltered round porch lights')
    for part in b.parts:
        if part['material']==BRICK:part['texcoords']=[[(x+1.19)/(2*1.77),z/(3*1.155)]for x,y,z in part['vertices']]
