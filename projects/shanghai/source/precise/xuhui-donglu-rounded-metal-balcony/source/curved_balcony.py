"""The small high balcony of Donglu, Yueyang Road. Local Z is up."""
from pathlib import Path
import math
import numpy as np
from PIL import Image
from shapely.geometry import Polygon,box
from shapely.geometry.polygon import orient
ID='xuhui-donglu-rounded-metal-balcony'
BRICK='Vertically aligned buff facing tiles';CONCRETE='Weathered concrete edge';UNDER='Sheltered underside';INSIDE='Light interior of balcony';BAND='Pale solid balcony band';RAIL='Painted silver grey rails';JOINT='Dark rail foot';SASH='Dark steel window frame';GLASS='Light reflecting window'
PALETTE={m:dict(color=c,roughness=r)for m,c,r in [(BRICK,[1,1,1],.93),(CONCRETE,[.551,.519,.463],.93),(UNDER,[.465,.444,.40],.91),(INSIDE,[.659,.629,.565],.9),(BAND,[.773,.779,.748],.62),(RAIL,[.665,.686,.662],.56),(JOINT,[.421,.429,.398],.80),(SASH,[.251,.229,.205],.73),(GLASS,[.673,.702,.686],.35)]}
def texture():
    f=Path(__file__).with_name('vertically-bonded-buff-tile.png')
    if not f.exists():
        rng=np.random.default_rng(815);height,width=564,752
        atlas=np.zeros((height,width,3),np.uint8)
        rows,cols=38,23
        for j in range(rows):
            for i in range(cols):
                y=j*height//rows;yn=(j+1)*height//rows;x=i*width//cols;xn=(i+1)*width//cols
                tint=np.array([164,133,107])+rng.normal(0,3.7,3);a=tint+rng.normal(0,2.0,(yn-y,xn-x,1))
                a[:1]=[132,119,99];a[:,:1]=[151,135,112];atlas[y:yn,x:xn]=a.clip(0,255).astype('uint8')
        Image.fromarray(atlas).quantize(96).save(f)
    PALETTE[BRICK]['texture']=str(f)
def rail_line(n=16,dx=0):
    # The returns meet the wall. Two rounded outer corners frame a nearly straight front.
    half=1.23+dx;radius=.294+dx
    pts=[(-half,.012),(-half,-.549)]
    for j in range(1,n+1):
        a=math.pi+j*math.pi/(2*n);pts.append((-(half-radius)+radius*math.cos(a),-.549+radius*math.sin(a)))
    pts.append((half-radius,-.549-radius))
    for j in range(1,n+1):
        a=-math.pi/2+j*math.pi/(2*n);pts.append(((half-radius)+radius*math.cos(a),-.549+radius*math.sin(a)))
    pts.append((half,.012))
    return pts
def add_building(b,far=False):
    texture()
    def wall(shape,back,front,mat,label):b.prism(shape,back,front,lambda x,z,d:(x,-d,z),mat,label)
    def slab(shape,bot,top,mat,label):b.prism(shape,bot,top,lambda x,y,z:(x,y,z),mat,label)
    a=box(-1.66,0,1.66,2.84).difference(box(-1.032,.63,1.032,2.55))
    wall(a,-.179,0,BRICK,'Bond of fine horizontal facing tiles around the window')
    for part in b.parts:
        if part['material']==BRICK:part['texcoords']=[[(x+1.66)/3.32,z/2.84]for x,y,z in part['vertices']]
    wall(box(-1.032,.63,1.032,2.55),-.180,-.149,GLASS,'Glazing set back behind the balcony')
    wall(box(-1.032,.63,1.032,2.55).difference(box(-.994,.666,.994,2.51)),-.155,-.074,SASH,'Visible sash border')
    for x in [-.505,.002,.510]:
        wall(box(x-.015,.659,x+.015,2.53),-.15,-.107,SASH,'Slender original window mullion')
    wall(box(-1.007,2.29,1.007,2.323),-.15,-.103,SASH,'Thin rail below upper lights')
    facets=7 if far else 19
    foot=orient(Polygon(rail_line(facets,.038)))
    slab(foot,.518,.638,CONCRETE,'Exposed edge of the rounded concrete balcony slab')
    slab(orient(Polygon(rail_line(facets,.015))),.508,.519,UNDER,'Underside return held back from slab edge')
    slab(orient(Polygon(rail_line(facets,-.026))),.636,.651,INSIDE,'Walking face inside the solid band')
    strip=Polygon(rail_line(facets,.004)+list(reversed(rail_line(facets,-.016))))
    slab(orient(strip),.787,.991,BAND,'Continuous wide painted metal strip with radiused corner returns')
    path=rail_line(facets)
    for z,r in [(1.018,.009),(1.166,.009),(1.323,.010),(1.482,.021)]:
        b.tube([(x,y,z)for x,y in path],r,RAIL,sides=7 if far else 12,label='Continuous rounded handrail' if z>1.4 else 'Thin intermediate horizontal rail')
    bars=[(-.523,-.843),(.506,-.843),(-1.228,-.409),(1.228,-.409),(-1.065,-.807),(1.065,-.807)]
    for x,y in bars:
        b.box((x,y-.013,1.063),(.027,.044,.844),RAIL,label='Upright continuing down over the solid band')
        b.box((x,y-.015,.663),(.051,.060,.044),JOINT,label='Balcony railing foot on the visible slab edge')
