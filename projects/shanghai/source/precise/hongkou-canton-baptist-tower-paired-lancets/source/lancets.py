"""The pair of tall lights on the tower of the Canton Baptist Church, photographed in 2015."""
from pathlib import Path
from math import sqrt
import numpy as np
from shapely.geometry import Polygon,box
from PIL import Image
ID='hongkou-canton-baptist-tower-paired-lancets'
PAINT='Ochre-yellow wall finish';BLUE='Weathered ultramarine border';BACK='Slate glazing in recess';DARK='Shaded edges inside opening';BARS='Dark steel horizontal and vertical bars';CREAM='Light spandrel below the twin lights';SILL='Upper blue edge of sill';ACCENT='Bright blue edge at upper opening';CENTRE='Dark charcoal middle panes'
PALETTE={k:dict(color=c,roughness=r) for k,c,r in [(PAINT,[1,1,1],.94),(BLUE,[.054,.183,.341],.85),(BACK,[.110,.126,.131],.47),(CENTRE,[.022,.030,.038],.60),(DARK,[.074,.075,.066],.95),(BARS,[.059,.054,.040],.67),(CREAM,[.821,.735,.438],.92),(SILL,[.083,.288,.472],.86),(ACCENT,[.115,.321,.512],.86)]}
def texture():
    p=Path(__file__).with_name('warm-plaster.png')
    if not p.exists():
        r=np.random.default_rng(675);wash=np.asarray(Image.fromarray(r.integers(0,240,(22,16),'uint8')).resize((256,384),Image.Resampling.BICUBIC),float)/255
        arr=[192,174,115]+17*wash[:,:,None]+r.normal(0,3.8,(384,256,1));Image.fromarray(np.clip(arr,0,255).astype('uint8')).save(p)
    PALETTE[PAINT]['texture']=str(p)
def pointed(cx,hw,bottom,spring,segments):
    points=[]
    for x in np.linspace(-hw,hw,2*segments+1):
        center=hw*.45
        z=spring+sqrt(max(0,(hw+center)**2-(abs(x)+center)**2))
        points.append((cx+float(x),z))
    return Polygon([(cx-hw,bottom),(cx+hw,bottom)]+list(reversed(points)))
def add_building(b,far=False):
    texture();n=11 if far else 32
    def form(poly,back,front,mat,name):b.prism(poly,back,front,lambda x,z,d:(x,-d,z),mat,name)
    def rect(x0,x1,z0,z1,d,e,mat,name):form(box(x0,z0,x1,z1),d,e,mat,name)
    outer=pointed(0,.72,.26,4.32,n);inner=pointed(0,.605,.335,4.294,n)
    form(box(-1.15,0,1.15,5.60).difference(outer),-.27,0,PAINT,'Yellow frontage around a tall pointed aperture')
    form(outer.difference(inner),-.26,.054,BLUE,'Blue outer hood and jambs')
    openings=[pointed(x,.263,.94,4.37,n) for x in(-.308,.308)]
    tracery=inner
    for void in openings:tracery=tracery.difference(void)
    form(tracery,-.23,-.065,PAINT,'Yellow face above the paired openings and behind sill')
    rect(-.052,.052,.28,4.39,-.174,.021,BLUE,'Tall blue central mullion')
    for side,c in enumerate((-.308,.308)):
        aperture=openings[side]
        form(aperture,-.276,-.250,BACK,'Shadowed glazing behind one pointed opening')
        rect(c-.260,c+.260,1.90,3.815,-.252,-.242,CENTRE,'Deep shadow in the middle compartment')
        for z in(1.20,1.54,1.88,3.84,4.061):
            rect(c-.260,c+.260,z-.010,z+.010,-.234,-.201,BARS,'Visible upper and lower horizontal divisions')
        for z,h in((.956,1.88),(3.84,4.35)):
            rect(c-.009,c+.009,z,h,-.242,-.202,BARS,'Slim vertical within the upper and lower glazed fields')
        rect(c-.267,c+.267,.344,.946,-.15,-.024,CREAM,'Pale opaque panel below the glazing')
        form(pointed(c,.273,.942,4.371,n).difference(aperture),-.25,-.085,DARK,'Dark narrow reveal of individual lancet')
    diamond=Polygon([(0,4.643),(.116,4.796),(0,4.946),(-.116,4.796)])
    form(diamond,-.125,-.004,BLUE,'Blue lozenge in the spandrel over the central mullion')
    rect(-.73,.73,.238,.316,-.035,.099,SILL,'Projecting blue sill across both bays')
    if not far:
        form(outer.difference(pointed(0,.708,.272,4.32,n)),-.005,.059,ACCENT,'Hairline on outer arch cut edge')
        for c in(-.308,.308):
            for z in (1.206,1.546,1.886,3.846,4.067):
                rect(c-.258,c+.258,z,z+.004,-.203,-.198,BARS,'Outer lip on transom')
    for part in b.parts:
        if part['material']==PAINT:part['texcoords']=[[(x+1.16)/2.32,z/5.61]for x,y,z in part['vertices']]
