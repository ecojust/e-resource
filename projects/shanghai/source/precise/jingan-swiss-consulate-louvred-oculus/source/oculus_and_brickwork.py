"""The masonry attic eye of the former Swiss consulate, from Fayhoo's April 2016 photograph."""
from math import cos,sin,pi
from pathlib import Path
from PIL import Image
from shapely.geometry import Polygon,LineString,box
import numpy as np

ID='jingan-swiss-consulate-louvred-oculus'
WALL='Blue-grey running-bond brick';STONE='Light ochre stone';MOULD='Rounded stone fillet'
KEY='Pale keystones';SHADE='Deep vent shadow';IRON='Dark louvre slats';STRIP='Attic geometric bands'
PALETTE={name:dict(color=color,roughness=roughness) for name,color,roughness in [
(WALL,[1.,1.,1.],.93),(STONE,[.66,.596,.474],.92),(MOULD,[.728,.653,.513],.85),
(KEY,[.734,.683,.543],.9),(SHADE,[.075,.086,.088],.92),(IRON,[.182,.18,.15],.72),(STRIP,[.684,.626,.486],.92)]}
CX=0.;CZ=1.15
def texture():
    path=Path(__file__).with_name('grey-brick-bond.png')
    if not path.exists():
        rng=np.random.default_rng(611);pixels=np.zeros((600,512,3))
        pixels[:]=[169.,159.,145.];pixels+=(rng.random((600,512,1))-.5)*27
        for row in range(25):
            for col in range(-1,9):
                x=col*64+(row%2)*32;y=row*24
                lo=max(x+2,0);hi=min(x+62,512)
                if hi<=lo:continue
                region=pixels[y+1:y+23,lo:hi];v=rng.uniform(-19,20)
                region[:]=np.array([113,111,108])+v+(rng.random(region.shape[:2]+(1,))-.5)*32
        Image.fromarray(pixels.clip(0,255).astype('u1')).quantize(130).save(path)
    PALETTE[WALL]['texture']=str(path)
def disk(radius,segments):
    return Polygon([(CX+radius*cos(2*pi*i/segments),CZ+radius*sin(2*pi*i/segments)) for i in range(segments)])
def add_building(b,far=False):
    texture();segments=40 if far else 88
    def xyz(x,z,d):return x,-d,z
    def slab(shape,back,front,material,name):
        b.prism(shape,back,front,xyz,material,name)
    def band(path,width,depth,name):
        slab(LineString(path).buffer(width/2,cap_style=2,join_style=2),-.003,depth,STRIP,name)
    opening=disk(.276,segments)
    slab(box(-1.23,0,1.23,2.52).difference(opening),-.36,0.,WALL,'Brick tympanum around the vent')
    slab(disk(.622,segments).difference(opening),-.035,.057,STONE,'Broad circular stone surround')
    for radius,thickness,front in [(.60,.024,.076),(.502,.015,.083),(.34,.02,.07)]:
        contour=[(radius*cos(2*pi*i/segments),-front,CZ+radius*sin(2*pi*i/segments)) for i in range(segments+1)]
        b.tube(contour,thickness,MOULD,sides=5 if far else 10,label='Turned concentric stone bead')
    for a in [pi/2,0,-pi/2,pi]:
        inner=.273;outer=.648 if a==pi/2 else .61
        # Each wedge is widest at the outer edge of the roundel.
        pts=[]
        for r,delta in [(inner,-.077),(outer,-.115),(outer,.115),(inner,.077)]:
            pts.append((r*cos(a+delta),CZ+r*sin(a+delta)))
        slab(Polygon(pts),.032,.107,KEY,'Projecting wedge across outer stone rings')
    slab(disk(.273,segments),-.36,-.287,SHADE,'Dark back of the vent')
    for n in range(-3,4):
        z=CZ+n*.071;swath=box(-.277,z-.021,.277,z+.009).intersection(opening)
        slab(swath,-.193,-.156,IRON,'Recessed horizontal louvre')
    band([(-1.23,1.805),(0.,2.26),(1.23,1.805)],.048,.039,'Low apex of the gable stone outline')
    band([(-.68,2.015),(-.104,2.365),(-.103,2.214)],.052,.05,'Left open triangular ornament')
    band([(.68,2.015),(.104,2.365),(.103,2.214)],.052,.05,'Right open triangular ornament')
    band([(0.,2.31),(0.,1.753)],.072,.068,'Short vertical stem down to the top key')
    for p in b.parts:
        if p['material']==WALL:p['texcoords']=[[(x+.64*y+1.24)/2.71,z/2.52]for x,y,z in p['vertices']]
