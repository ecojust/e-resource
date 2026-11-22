"""The left stone capital and circular panel on the Lane 22 entrance, photographed by Gaocan 88."""
from math import sin,cos,pi
from pathlib import Path
from PIL import Image
from shapely.geometry import Polygon,box
import numpy as np
ID='jingan-qingyunli-no22-leaf-capital'
STONE='Grey cast stone';TRIM='Light stone edges';BED='Recessed stone';LEAF='Raised leaf';RIB='Fluting on the leaves';DISC='Round medallion';SOFFIT='Underside of cornice'
PALETTE={k:dict(color=c,roughness=.94) for k,c in [(STONE,[1,1,1]),(TRIM,[.55,.52,.455]),(BED,[.42,.40,.34]),(LEAF,[.51,.505,.433]),(RIB,[.58,.56,.49]),(DISC,[.52,.515,.455]),(SOFFIT,[.405,.39,.335])]}
def texture():
    path=Path(__file__).with_name('coarse-grey-stone.png')
    if not path.exists():
        rng=np.random.default_rng(627)
        coarse=Image.fromarray(rng.integers(92,165,(25,25),dtype='uint8')).resize((384,384),Image.Resampling.BICUBIC)
        detail=.32*(np.array(coarse,dtype=float)-128)+rng.normal(0,4.8,(384,384))
        pixels=np.array([154,152,138])+detail[:,:,None]
        Image.fromarray(pixels.clip(0,255).astype('uint8')).quantize(128).save(path)
    PALETTE[STONE]['texture']=str(path)

def build_leaf(b,cx,zbase,sgn,far,side=False):
    def vertex(x,z,depth):
        return (.395+depth,cx+x,z) if side else (cx+x,-.255-depth,z)
    # Opposed lancet-shaped leaves spring from a short common stem. The ridge is built in relief.
    segments=3 if far else 7
    for tier in range(3):
        z=zbase+.12+tier*.079
        width=.055-tier*.005
        for handed in (-1,1):
            length=.112-tier*.013
            points=[];faces=[]
            for i in range(segments+1):
                t=i/segments
                px=handed*(.006+.036*t);pz=z+length*t
                half=width*(max(0.,sin(pi*t))**.8)*.54
                bump=.011+.019*sin(pi*t)
                points += [vertex(sgn*(px-half),pz,.009),vertex(sgn*px,pz,bump),vertex(sgn*(px+half),pz,.009)]
                if i:
                    k=i*3
                    for j in (0,1):
                        q=(k-3+j,k-2+j,k+j+1,k+j)
                        if sgn<0:q=q[::-1]
                        faces.append(q)
            b.add(points,faces,LEAF,'Paired pointed leaves on the capital')
    points=[vertex(0,zbase+.025,.02),vertex(.002*sgn,zbase+.157,.031),vertex(-.004*sgn,zbase+.287,.035)]
    b.tube(points,.007 if far else .008,RIB,sides=5 if far else 8,label='Narrow upright stem on each leaf group')
    for flip in (-1,1):
        pts=[]
        for t in np.linspace(0,1,8 if far else 16):
            angle=(-.57+1.92*t)*pi
            pts.append(vertex(flip*(.041+.026*cos(angle)),zbase+.332+.029*sin(angle),.017+.009*t))
        b.tube(pts,.009,LEAF,sides=5 if far else 8,label='Curl at the capital head')

def add_building(b,far=False):
    texture()
    def front(x,z,d):return x,-d,z
    def rectangle(x0,x1,z0,z1,y0,y1,mat,name):b.prism(box(x0,z0,x1,z1),y0,y1,front,mat,name)
    def tier(x,z0,z1,y0,y1,mat,name):rectangle(-x,x,z0,z1,y0,y1,mat,name)
    # The photographed lower shaft is only included to the top of its long recessed panel.
    tier(.367,0,.96,-.30,.178,STONE,'Rectangular shaft, left of gate')
    opening=box(-.116,-.01,.116,.679)
    b.prism(box(-.367,0,.367,.96).difference(opening),.176,.214,front,STONE,'Shallow vertical recess in the shaft')
    for low,high,half,depth,m in [(.94,.972,.385,.229,BED),(.972,1.01,.408,.258,TRIM),(1.01,1.038,.398,.245,TRIM),
                                     (1.038,1.421,.395,.255,STONE),(1.421,1.45,.405,.26,TRIM)]:
        tier(half,low,high,-.31,depth,m,'Capital body and stepped neck mouldings')
    for x in (-.265,-.004,.258):build_leaf(b,x,1.048,1,far)
    # Photographic oblique shows the same foliage turning the corner.
    for y in (-.142,.112):build_leaf(b,y,1.048,1,far,side=True)
    tier(.359,1.45,2.216,-.295,.222,STONE,'Square panel below the cornice')
    # Convex circular boss, projected in the middle of a flat square stone.
    count=28 if far else 60;z0=1.823
    rings=[(.204,.224),(.198,.244),(.185,.261),(.148,.273),(.095,.279),(.035,.282)]
    verts=[(r*cos(t),-d,z0+r*sin(t)) for r,d in rings for t in np.linspace(0,2*pi,count,endpoint=False)]
    faces=[]
    for i in range(len(rings)-1):
        for j in range(count):
            k=(j+1)%count;faces.append((i*count+j,i*count+k,(i+1)*count+k,(i+1)*count+j))
    verts.append((0,-.284,z0))
    for j in range(count):faces.append(((len(rings)-1)*count+j,(len(rings)-1)*count+(j+1)%count,len(verts)-1))
    b.add(verts,faces,DISC,'Shallow round stone boss with a rounded rim')
    for half,low,high,depth,mat,name in [(.375,2.213,2.247,.24,TRIM,'Stone bed above circular panel'),(.416,2.247,2.28,.276,TRIM,'Stepped cornice bed'),(.515,2.32,2.43,.377,SOFFIT,'Underside of projecting cornice'),(.565,2.427,2.493,.417,TRIM,'Flat leading edge of the projecting cap')]:
        tier(half,low,high,-.33,depth,mat,name)
    for x in (-.287,.25):
        rectangle(x-.061,x+.061,2.275,2.327,.187,.329,STONE,'Square projecting block under the top lip')
    for p in b.parts:
        if p['material']==STONE:p['texcoords']=[[(x+.53+.4*y)/1.15,z/2.5]for x,y,z in p['vertices']]
