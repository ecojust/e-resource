"""Perforated ridge, curled ends and upper grey tile courses of the assembly hall in Xishi Street."""
from pathlib import Path
import math
import numpy as np
from PIL import Image
from shapely.geometry import box,Polygon,LineString
ID='pudong-xishi-street-guandi-hall-pierced-ridge'
TILE='Weathered blue-grey fired tile';RIDGE='Grey brick ridge';LIP='Layered grey cap moulding';BAR='Diagonal grey lattice';CARVED='Recessed leaf-shaped traces';DARK='Grey ridge underlayer'
PALETTE={m:dict(color=c,roughness=r) for m,c,r in ((TILE,[1,1,1],.92),(RIDGE,[.322,.341,.345],.94),(LIP,[.275,.297,.310],.89),(BAR,[.311,.337,.345],.91),(CARVED,[.344,.368,.368],.95),(DARK,[.193,.219,.23],.9))}
LATTICE=[(-1.077,-.442),(.436,1.070)]
CUTS=[(-1.702,-1.184),*LATTICE,(1.181,1.701)]
def texture():
    f=Path(__file__).with_name('grey-ceramic-roof.png')
    if not f.exists():
        g=np.random.default_rng(851);small=Image.fromarray(g.integers(0,255,(18,27),dtype='uint8')).resize((252,186),Image.Resampling.BILINEAR)
        surface=(np.asarray(small).astype(float)-127)*.23+g.normal(0,4,(186,252))
        Image.fromarray((np.array([104,104,96])+surface[:,:,None]).clip(0,255).astype('uint8')).quantize(110).save(f)
    PALETTE[TILE]['texture']=str(f)
def crown(x):return .041*(abs(x)/2.02)**2
def roof(y):return .145+.485*y
def add_building(b,far=False):
    texture();n=4 if far else 11
    def facade(poly,back,front,material,name):b.prism(poly,back,front,lambda x,z,d:(x,-d,z),material,name)
    backing=box(-2.042,.132,2.042,.519)
    for left,right in CUTS:backing=backing.difference(box(left,.263,right,.397))
    facade(backing,-.142,-.012,RIDGE,'Brick ridge with two diagonal panels and two smaller pierced panels')
    for upper,lower,mat,proj,name in [(.224,.169,DARK,.040,'Shadow under the lower lip'),(.256,.219,LIP,.054,'Lower plinth'),(.433,.408,LIP,.036,'Rail above the openings'),(.482,.456,RIDGE,.044,'Cap moulding'),(.518,.478,LIP,.060,'Up-swept top edge')]:
        xx=np.linspace(-2.053,2.053,11 if far else 29)
        shape=Polygon([(x,upper+crown(x))for x in xx]+[(x,lower+crown(x))for x in xx[::-1]])
        facade(shape,-.186,proj,mat,name)
    for left,right in LATTICE:
        clip=box(left+.001,.263,right-.001,.397)
        for sign in [-1,1]:
            for i in range(-4,18):
                x=left+i*.074
                strip=LineString([(x,.255),(x+sign*.119,.409)]).buffer(.0073,cap_style=2).intersection(clip)
                if not strip.is_empty and strip.area>.00003:facade(strip,-.100,-.024,BAR,'Intersecting diagonal lattice rib')
    for left,right in (CUTS[0],CUTS[-1]):
        mid=(left+right)/2
        facade(box(mid-.013,.256,mid+.013,.404),-.094,-.025,RIDGE,'Bar between paired small openings')
        for j in range(2):
            x=left+.111+j*.257
            stem=LineString([(x-.047,.260),(x+.028,.307),(x+.055,.342),(x+.031,.391)]).buffer(.012,cap_style=2)
            leaf=Polygon([(x-.040,.286),(x-.081,.308),(x-.059,.329),(x-.023,.324),(x+.009,.306)])
            facade(stem.union(leaf),-.102,-.056,CARVED,'Abstract visible contour in the small end panel')
    for sign in [-1,1]:
        path=LineString([(sign*x,z) for x,z in [(1.965,.474),(2.002,.520),(2.054,.545),(2.085,.582),(2.076,.621),(2.046,.648),(2.023,.654),(2.014,.669)]])
        facade(path.buffer(.022,resolution=n,cap_style=1,join_style=1),-.156,.017,LIP,'Curled tip of the ridge')
        # Sloping edge tile below each crest curves outward as the roof descends.
        coords=[(sign*(2.013+.203*((i/28)**1.64)),-.99*i/28,.502-.663*(i/28)**.66)for i in range(29)]
        pts=[];faces=[];count=4 if far else 9
        for x,y,z in coords:
            for i in range(count+1):
                a=np.pi*i/count;pts.append((x+.042*math.cos(a),y,z+.034*math.sin(a)))
        for k in range(28):
            for j in range(count):
                a=k*(count+1)+j;faces.append((a,a+count+1,a+count+2,a+1))
        b.add(pts,faces,LIP,'Curved side tiles descending from the end crest')
        wall=[];surfaces=[]
        for x,y,z in coords:
            lower=roof(y)-.028
            wall.extend([(x-.032,y,lower),(x+.032,y,lower),(x+.032,y,z+.008),(x-.032,y,z+.008)])
        for k in range(len(coords)-1):
            start=k*4
            for j in range(4):
                nxt=(j+1)%4;surfaces.append((start+j,start+nxt,start+4+nxt,start+4+j))
        surfaces.extend([(3,2,1,0),tuple(range(len(wall)-4,len(wall)))])
        b.add(wall,surfaces,RIDGE,'Masonry rising from the roof to support each curved verge')
    b.prism(box(-2.185,-.99,2.185,-.018),-.026,0,lambda x,y,d:(x,y,roof(y)+d),DARK,'Upper slope below the ridge')
    pts=[];faces=[];uv=[];cols=42;rows=7
    for c in range(cols):
        for r in range(rows):
            y0=-.99+r*.139;y1=min(-.018,y0+.157)
            base=len(pts)
            for y,h in [(y0,-.009),(y0,0),(y1,0)]:
                for j in range(n+1):
                    f=j/n;x=-2.185+(c+.008+.982*f)*4.37/cols
                    zz=roof(y)+.010+.027*((1+math.cos(2*math.pi*(f-.22)))/2)**1.28+.010*(y1-y)/(y1-y0)+h
                    pts.append((x,y,zz));uv.append((f,(y-y0)/(y1-y0)))
            stride=n+1
            for j in range(n):
                a=base+j;faces.extend([(a,a+1,a+1+stride,a+stride),(a+stride,a+1+stride,a+1+2*stride,a+2*stride)])
    b.add(pts,faces,TILE,'Individually rolled grey tile courses on the visible front slope')
    b.parts[-1]['texcoords']=uv
