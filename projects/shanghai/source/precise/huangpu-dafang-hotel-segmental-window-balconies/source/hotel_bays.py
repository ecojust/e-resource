"""Two successive pairs of the segmental window heads above the hotel entrance."""
from math import pi,sin,cos
from pathlib import Path
import numpy as np
from PIL import Image
from shapely.geometry import box,Polygon
from shapely.ops import unary_union
ID='huangpu-dafang-hotel-segmental-window-balconies'
WALL='Warm ivory mineral render';HEAD='Weathered cream window head';LIP='Pale outer hood moulding';SHADOW='Inner head shadow';EDGE='Bevel at slab edge';PANE='Green blue glass';REFLECTION='Muted glass reflection';FRAME='Pale metal sash';INSIDE='Dark inner reveal';BAND='Raised stepped ornament';PATINA='Pale weather trace'
PALETTE={key:{'color':col,'roughness':rough}for key,col,rough in [(WALL,[1,1,1],.96),(HEAD,[.73,.699,.602],.92),(LIP,[.827,.802,.704],.93),(SHADOW,[.347,.332,.273],.94),(EDGE,[.546,.529,.451],.93),(PANE,[.278,.381,.404],.35),(REFLECTION,[.359,.447,.456],.37),(FRAME,[.713,.725,.684],.67),(INSIDE,[.152,.162,.156],.87),(BAND,[.735,.713,.622],.96),(PATINA,[.543,.534,.449],.96)]}
def texture():
    p=Path(__file__).with_name('plaster.png')
    if not p.exists():
        rng=np.random.default_rng(543);v=np.asarray(Image.fromarray(rng.integers(0,255,(18,110),dtype='u1')).resize((512,476),Image.Resampling.BICUBIC),float)
        granular=(v-127)*.067+rng.normal(0,1.9,v.shape);Image.fromarray(np.clip([191,184,163]+granular[:,:,None],0,255).astype('u1')).quantize(128).save(p)
    PALETTE[WALL]['texture']=str(p)
def section(b,shape,back,front,mat,name):
    b.prism(shape,back,front,lambda x,z,d:(x,-d,z),mat,name)
def slab(b,l,r,lo,hi,back,front,m,n):
    section(b,box(l,lo,r,hi),back,front,m,n)
CS=(-1.51,1.51)
def arc(x,r):return .176*(1-(x/r)**2)
def head_outline(c,w,z,t,far):
    xx=np.linspace(-w,w,11 if far else 27)
    return Polygon([(c+x,z+arc(x,w)) for x in xx]+[(c+x,z+arc(x,w)+t) for x in xx[::-1]])
def add_building(b,far=False):
    texture()
    holes=[box(c-.957,lo+.40,c+.957,lo+2.60)for c in CS for lo in (0,3.17)]
    field=box(-3,0,3,6.46).difference(unary_union(holes))
    section(b,field,-.32,0,WALL,'Wall between the two storeys and two window axes')
    for c in CS:
        for lo in (0,3.17):
            for a,g in enumerate([(-.934,-.325),(-.305,.188),(.213,.934)]):
                slab(b,c+g[0],c+g[1],lo+.45,lo+2.54,-.179,-.175,PANE if a!=1 else REFLECTION,'Recessed glass behind balcony')
            for x in (-.948,-.312,.202,.946):
                slab(b,c+x-.017,c+x+.017,lo+.395,lo+2.590,-.178,-.141,FRAME,'Vertical sash and jamb')
            for z in (.414,2.562):slab(b,c-.963,c+.963,lo+z-.026,lo+z+.026,-.171,-.136,FRAME,'Rectangular sash head and bottom rail')
            for x in (-.98,.98):
                slab(b,c+x-.023,c+x+.023,lo+.398,lo+2.61,-.174,-.024,INSIDE,'Dark inner return beside window')
            for offset,width,height,front,mat in [(0,1.132,.051,.054,SHADOW),(.047,1.148,.065,.100,HEAD),(.108,1.173,.037,.169,LIP)]:
                section(b,head_outline(c,width,lo+2.595+offset,height,far),-.022,front,mat,'Three narrow curved courses above straight sash')
            slab(b,c-1.262,c+1.262,lo+.245,lo+.326,-.04,.868,EDGE,'Exposed flat soffit of projecting balcony')
            slab(b,c-1.25,c+1.25,lo+.316,lo+.375,-.014,.855,HEAD,'Balcony floor and thin front edge')
            slab(b,c-1.25,c+1.25,lo+.342,lo+1.311,.739,.855,WALL,'Flat projecting balcony front with returned parapets')
            for x in (-1.25,1.154):slab(b,c+x,c+x+.096,lo+.34,lo+1.31,-.013,.84,WALL,'Deep balcony parapet return')
            outline=Polygon([(c-.856,lo+.568),(c+.783,lo+.568),(c+.783,lo+.629),(c+.842,lo+.629),(c+.842,lo+.693),(c+.759,lo+.693),(c+.759,lo+.619),(c-.808,lo+.619),(c-.808,lo+.690),(c-.856,lo+.690)])
            section(b,outline,.850,.886,BAND,'Slender raised rule with stepped ends')
            if not far:
                for dx in (-.76,-.47,.51):
                    slab(b,c+dx,c+dx+.012,lo+.349,lo+.453,.854,.857,PATINA,'Short weather streak beneath front moulding')
    for part in b.parts:
        if part['material']==WALL:part['texcoords']=[[(x+3.01)/6.03,z/6.47]for x,y,z in part['vertices']]
