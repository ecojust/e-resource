"""Yuecun gate pier visible at the left edge of WQL's January 2018 photograph."""
from pathlib import Path
from math import cos,sin,pi
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from shapely.geometry import Polygon,box
HERE=Path(__file__).parent
STONE='Speckled grey green stone'; CAP='Darkened cap stone'; JOINT='Recessed stone joint'; PLINTH='Weathered foot'
BRASS='Ochre address panel'; RIM='Green patinated bronze'; INK='Dark numeral relief'; BLUE='Blue tenant board'; EDGE='Painted board edge'
PALETTE={k:dict(color=c,roughness=r)for k,c,r in [(STONE,[.68,.71,.64],.93),(CAP,[.36,.39,.35],.91),(JOINT,[.115,.136,.119],.95),(PLINTH,[.84,.88,.79],.94),(BRASS,[1,.99,.95],.75),(RIM,[.20,.30,.235],.82),(INK,[.031,.033,.022],.84),(BLUE,[1,1,1],.69),(EDGE,[.12,.15,.16],.71)]}
PAPER='Pale adhesive and paper residue'
PALETTE[PAPER]=dict(color=[.78,.79,.75],roughness=.96)
HEIGHT=2.58
def z(line):return (510-line)*HEIGHT/(510-95)
# Image coordinates are based on a 680-pixel-wide readout of the full 4160x3120 original.
WIDTH=.652;DEPTH=.640;JOINT_Z=[z(y)for y in (467,424,376,329,284,241)]
TOP_RECT=(-.260,z(166),.260,z(134))
BLUE_RECT=(-.214,z(241),.219,z(203))
ATLAS=(768,640);STONE_PATCH=(3,3,356,635);BRASS_PATCH=(364,4,763,240);BLUE_PATCH=(364,252,763,477)
def _font(candidates,size,index=0):
    for name in candidates:
        path=Path(name)
        if path.is_file():return ImageFont.truetype(str(path),size,index=index)
    raise FileNotFoundError('Missing font for reconstructing the visible plate lettering')
def make_texture(path):
    if path.is_file() and path.stat().st_size:return
    rng=np.random.default_rng(20180125)
    image=Image.new('RGB',ATLAS,(95,105,93));a=np.asarray(image).copy()
    y,x=np.mgrid[0:636,0:357]
    noise=rng.normal(0,10,x.shape)+3*np.sin(x*.034+y*.026)
    stone=np.array([177,183,173])+noise[:,:,None]+rng.normal(0,2.0,(636,357,3))
    pits=rng.random(x.shape)<.026;stone[pits]-=rng.integers(18,52,(pits.sum(),1))
    a[:636,:357]=np.clip(stone,30,235)
    x0,y0,x1,y1=BRASS_PATCH;Y,X=np.mgrid[0:(y1-y0+1),0:(x1-x0+1)]
    u=X/(x1-x0);v=Y/(y1-y0)
    d=np.minimum.reduce([u,1-u,.63*v,.63*(1-v)])
    coarse=np.asarray(Image.fromarray(rng.integers(0,255,(17,30),dtype=np.uint8)).resize((X.shape[1],X.shape[0]),Image.Resampling.BICUBIC))/255
    brass=np.array([197,165,87]);oxide=np.array([75,109,86])
    patina=np.clip((.088-d)*8+(coarse-.42)*.38+rng.normal(0,.056,d.shape),0,1)
    surface=brass*(1-patina[:,:,None])+oxide*patina[:,:,None]+rng.normal(0,4.5,(Y.shape[0],Y.shape[1],1))
    a[y0:y1+1,x0:x1+1]=np.clip(surface,0,255)
    x0,y0,x1,y1=BLUE_PATCH
    a[y0:y1+1,x0:x1+1]=np.clip(np.array([56,78,94])+rng.normal(0,2,(y1-y0+1,x1-x0+1,1)),0,255)
    Y,X=np.mgrid[:145,:398]
    smoothed=np.asarray(Image.fromarray(rng.integers(0,255,(16,45),dtype=np.uint8)).resize((398,145),Image.Resampling.BICUBIC))/255
    local=np.linspace(.8,1.12,398)+.19*np.sin(np.arange(398)*.10)+.10*np.cos(np.arange(398)*.33)
    damp=np.clip(.20+(Y/145)*1.25*local[None,:]+smoothed*.43+rng.normal(0,.055,smoothed.shape),0,1)
    highlight=np.array([163,177,157]);dark=np.array([52,65,54])
    a[490:635,364:762]=np.clip(highlight*(1-damp[:,:,None])+dark*damp[:,:,None]+rng.normal(0,4.2,(*Y.shape,1)),0,255)
    image=Image.fromarray(a,'RGB');draw=ImageDraw.Draw(image)
    def line(text,projection,font,fill):
        x0,y0,x1,y1=projection;bounds=font.getbbox(text)
        layer=Image.new('L',(bounds[2]-bounds[0]+4,bounds[3]-bounds[1]+4));p=ImageDraw.Draw(layer);p.text((2-bounds[0],2-bounds[1]),text,fill=255,font=font)
        image.paste(fill,(x0,y0,x1,y1),layer.resize((x1-x0,y1-y0),Image.Resampling.LANCZOS))
    han=_font(['/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'],52,2)
    line('江苏路480弄',(418,187,716,224),han,(46,42,27))
    line('童感儿童摄影',(408,308,716,353),han,(206,214,212))
    line('江苏路480弄66号',(390,374,746,421),han,(225,230,225))
    # The principal two figures have their own modeled outline.
    image.quantize(128,method=Image.Quantize.MEDIANCUT).save(path,'PNG',optimize=True)
def uv_face(part,rect,patch):
    left,bottom,right,top=rect;x0,y0,x1,y1=patch
    return [[(x0+(x-left)/(right-left)*(x1-x0))/ATLAS[0],(y0+(top-z)/(top-bottom)*(y1-y0))/ATLAS[1]]for x,y,z in part['vertices']]
def _profile(builder,label,levels,material,lod):
    """Closed square section with chamfered arrises and discrete projecting courses."""
    count=1 if lod else 3; rings=[]
    for width,depth,height,radius in levels:
        points=[]
        for cx,cy,start in ((width/2-radius,-depth/2+radius,-90),(width/2-radius,depth/2-radius,0),(-width/2+radius,depth/2-radius,90),(-width/2+radius,-depth/2+radius,180)):
            for k in range(count+1):
                angle=(start+k*90/count)*pi/180;points.append((cx+radius*cos(angle),cy+radius*sin(angle),height))
        rings.append(points)
    n=len(rings[0]);faces=[list(range(n-1,-1,-1)),list(range(n*(len(rings)-1),n*len(rings)))]
    for i in range(len(rings)-1):
        for j in range(n):
            t=(j+1)%n;faces.append([i*n+j,i*n+t,(i+1)*n+t,(i+1)*n+j])
    builder.add(sum(rings,[]),faces,material,label)
    part=builder.parts[-1]
    if material in (STONE,CAP,PLINTH):
        x0,y0,x1,y1=STONE_PATCH;lo,hi=levels[0][2],levels[-1][2];zrange=max(.25,hi-lo)
        if material==PLINTH:x0,y0,x1,y1=(364,490,761,634)
        part['texcoords']=[[(x0+(.5+.51*x+.42*y)*(x1-x0))/ATLAS[0],(y0+(.95-.89*(h-lo)/zrange)*(y1-y0))/ATLAS[1]]for x,y,h in part['vertices']]
def _front(builder,shape,d0,d1,mat,label):
    builder.prism(shape,d0,d1,lambda x,z,d:(x,-d,z),mat,label)
def _number_shapes():
    from sign_lettering import lettering_shapes
    from shapely.ops import unary_union
    from shapely import affinity
    font=Path('/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf')
    letters=lettering_shapes('68',.263,.097,font=font)
    return affinity.translate(unary_union([p for _,p in letters]),-.0025,z(154)+.0485)
def add_building(builder,lod):
    tex=HERE/'pier-atlas.png';make_texture(tex)
    for name in (STONE,CAP,PLINTH,BRASS,BLUE):builder.palette[name]['texture']=str(tex)
    _profile(builder,'Dark base of pier',[(.684,.665,0,.008),(.686,.668,.054,.009),(.661,.647,z(467)-.003,.006)],PLINTH,lod)
    lower=JOINT_Z[0]
    for number,upper in enumerate(JOINT_Z[1:]+[z(198)]):
        _profile(builder,'Recessed horizontal joint '+str(number+1),[(WIDTH-.009,DEPTH-.009,lower-.004,.006),(WIDTH-.009,DEPTH-.009,lower+.004,.006)],JOINT,lod)
        _profile(builder,'Ashlar course '+str(number+1),[(WIDTH-.004,DEPTH-.004,lower+.001,.004),(WIDTH,DEPTH,lower+.004,.004),(WIDTH,DEPTH,upper-.004,.004),(WIDTH-.003,DEPTH-.003,upper-.001,.004)],STONE,lod);lower=upper
    # Torn pale remnants under the blue sign, placed from the 2018 image.
    fragments=[(-.226,251,.014,.018),(-.154,249,.021,.015),(-.083,249,.012,.024),(-.052,255,.023,.032),(.035,249,.031,.014),(.118,248,.028,.012),(.182,254,.016,.009),(-.105,262,.020,.043),(-.067,271,.011,.022),(.053,258,.012,.017),(.071,268,.019,.021),(.143,274,.013,.011),(.207,279,.010,.016),(-.175,292,.014,.028),(.204,301,.018,.019),(-.244,306,.006,.012)]
    from random import Random
    for i,(x,line,rx,rz) in enumerate(fragments):
        if lod and min(rx,rz)<.014:continue
        rng=Random(6680+i);outline=[]
        for j in range(12 if not lod else 7):
            a=2*pi*j/(12 if not lod else 7);deform=rng.uniform(.62,1.)
            outline.append((x+rx*deform*cos(a),z(line)+rz*deform*sin(a)))
        _front(builder,Polygon(outline),DEPTH/2-.0001,DEPTH/2+.0006,PAPER,'Trace of old adhesive '+str(i+1))
    _profile(builder,'Projecting belt below the upper plaque',[(.665,.653,z(198),.005),(.671,.661,z(196),.005),(.772,.757,z(195),.007),(.772,.757,z(185),.007),(.756,.741,z(183),.005)],CAP,lod)
    _profile(builder,'Recessed neck behind the number',[(.610,.607,z(183),.007),(.610,.607,z(128),.007)],STONE,lod)
    _profile(builder,'Underside mouldings',[(.640,.637,z(130),.006),(.661,.654,z(128),.007),(.661,.654,z(126),.008),(.740,.727,z(125),.008),(.767,.749,z(122),.010)],CAP,lod)
    _profile(builder,'Sloping weather cap',[(.801,.783,z(122),.006),(.816,.797,z(121),.008),(.816,.797,z(104),.009),(.799,.780,z(103),.005),(.150,.123,z(95),.004)],CAP,lod)
    l,b,r,t=TOP_RECT;k=.027
    outline=Polygon([(l+k,b),(r-k,b),(r-k+.010,b+.010),(r,b+.011),(r,t-.012),(r-.013,t-.012),(r-k,t),(l+k,t),(l+.013,t-.012),(l,t-.012),(l,b+.011),(l+k-.010,b+.010)])
    _front(builder,outline,.300,.326,RIM,'Bronze plaque curled corner rim')
    inner=outline.buffer(-.007,join_style=2);start=len(builder.parts)
    _front(builder,inner,.3258,.330,BRASS,'Worn ochre face and lane name')
    for part in builder.parts[start:]:part['texcoords']=uv_face(part,TOP_RECT,BRASS_PATCH)
    _front(builder,_number_shapes(),.3298,.332,INK,'Black address figures 68')
    from shapely.geometry import Point
    for x in (l+.021,r-.021):
        _front(builder,Point(x,(b+t)/2).buffer(.009,quad_segs=4 if lod else 12),.329,.336,RIM,'Round bronze fixings')
    l,b,r,t=BLUE_RECT
    _front(builder,box(l,b,r,t),.322,.338,EDGE,'Dark edge of second sign')
    start=len(builder.parts);_front(builder,box(l+.001,b+.002,r-.003,t-.001),.3378,.339,BLUE,'2018 blue address board 66')
    for part in builder.parts[start:]:part['texcoords']=uv_face(part,BLUE_RECT,BLUE_PATCH)
