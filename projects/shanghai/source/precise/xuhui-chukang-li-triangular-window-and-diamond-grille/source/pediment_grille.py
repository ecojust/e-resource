"""Triangular fronton and glazed metal grille recorded in Chukang Li, Lane 401 Changle Road."""
from pathlib import Path
import numpy as np
from PIL import Image
from shapely.geometry import Polygon,Point,box
ID='xuhui-chukang-li-triangular-window-and-diamond-grille'
BRICK='Red alley brickwork';SAND='Granular brown stone dressings';RIDGE='Lighter moulding crest';SHADE='Recessed pediment panel';IRON='Grey painted iron';RING='Decorative iron rings and lozenges';GLASS='Dark reflecting upper glass';LOWER='Light lower glazing';FRAME='Pale old sash'
PALETTE={m:dict(color=c,roughness=r)for m,c,r in [(BRICK,[1,1,1],.94),(SAND,[.504,.481,.415],.94),(RIDGE,[.620,.589,.505],.88),(SHADE,[.407,.392,.344],.94),(IRON,[.544,.542,.487],.76),(RING,[.535,.508,.430],.72),(GLASS,[.213,.265,.259],.46),(LOWER,[.600,.635,.583],.59),(FRAME,[.657,.661,.575],.8)]}
def texture():
    p=Path(__file__).with_name('red-alley-bricks.png')
    if not p.exists():
        y,x=np.indices((748,620));row=y//26;run=x+33*(row%2);g=np.random.default_rng(795)
        a=np.array([119,77,65])+g.normal(0,7.5,(30,11))[row,run//68,None]+g.normal(0,4.2,x.shape)[:,:,None]
        mortar=(y%26<2)|(run%68<2);a[mortar]=[164,149,132];Image.fromarray(a.clip(0,255).astype('uint8')).quantize(128).save(p)
    PALETTE[BRICK]['texture']=str(p)
CENTRES=[-.282,.282]
def diamond(x,z,w,h):
    return Polygon([(x-w,z),(x,z+h),(x+w,z),(x,z-h)])
def add_building(b,far=False):
    texture()
    def front(poly,lo,hi,mat,label):b.prism(poly,lo,hi,lambda x,z,d:(x,-d,z),mat,label)
    def block(l,r,z,t,a,c,mat,label):front(box(l,z,r,t),a,c,mat,label)
    opening=box(-.544,-.01,.544,1.46)
    front(box(-.856,0,.856,2.177).difference(opening),-.173,0,BRICK,'Red brickwork around the window and its triangular stone head')
    outer=Polygon([(-.634,0),(.634,0),(.634,1.563),(0,2.027),(-.634,1.563)])
    front(outer.difference(opening),-.092,.061,SAND,'Continuous frame of the window and low triangular pediment')
    for x in [-.583,.583]:
        block(x-.021,x+.021,0,1.50,.058,.080,RIDGE,'Fine raised bead on the jamb')
    block(-.611,.611,1.479,1.501,.060,.091,RIDGE,'Moulding at top of jambs')
    def triangle(width,base,apex):
        return Polygon([(-width,base),(width,base),(0,apex)])
    for width,base,peak,inside,dep in [(.637,1.54,2.04,.029,.111),(.585,1.564,1.990,.020,.089),(.536,1.595,1.94,.016,.082)]:
        outer=triangle(width,base,peak)
        front(outer.difference(outer.buffer(-inside,join_style=2)),.057,dep,RIDGE,'Continuous triangular moulding')
    front(triangle(.472,1.626,1.892),.060,.063,SHADE,'Inset plain centre of the pediment')
    for x in [-.487,.487,0]:block(x-.017,x+.017,.014,1.440,-.140,-.103,FRAME,'Original glazed sash jamb and centre stile')
    block(-.531,.531,.02,.526,-.158,-.145,LOWER,'Light opaque lower portion of the sash')
    block(-.531,.531,.526,1.425,-.158,-.145,GLASS,'Upper darker glazing')
    block(-.533,.533,1.378,1.428,-.143,-.103,FRAME,'Upper sash rail')
    block(-.533,.533,.507,.541,-.143,-.103,FRAME,'Rail between panels of the sash')
    for x in np.linspace(-.44,.44,7):
        block(x-.010,x+.010,.025,1.419,.077,.102,IRON,'Slender square-section vertical of street grille')
    for h in [.232,.589,.739,1.144,1.422]:
        block(-.519,.519,h,h+.018,.099,.122,IRON,'Horizontal grille rail')
    for x in CENTRES:
        for rad,thick in [(.060,.0072),(.043,.005)]:
            shape=Point(x,.678).buffer(rad,resolution=9 if far else 20)
            front(shape.difference(Point(x,.678).buffer(rad-thick,resolution=9 if far else 20)),.107,.130,RING,'Concentric iron circle between the two rails')
        block(x-.004,x+.004,.599,.620,.107,.123,RING,'Lower link of ring to rail')
        block(x-.004,x+.004,.738,.752,.107,.123,RING,'Upper link of ring to rail')
    for x in [-.051,.051]:
        p=diamond(x,.678,.071,.061)
        front(p.difference(p.buffer(-.0075,join_style=2)),.109,.131,RING,'Two overlapping iron lozenges')
    for part in b.parts:
        if part['material']==BRICK:part['texcoords']=[[(x+.856)/1.712,z/2.177] for x,y,z in part['vertices']]
