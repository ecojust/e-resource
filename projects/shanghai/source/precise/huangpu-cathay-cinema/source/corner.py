"""Documented southwest Art Deco corner of Shanghai's Cathay Cinema, 2024–25."""
import math
from pathlib import Path
import numpy as np
from shapely.geometry import box, Polygon
from shapely.ops import unary_union
from photo_architecture import Facade,opening
from sign_lettering import add_facade_lettering

PALE='carved pale stone'
GREY='silver grey render'
BED='cream mortar'
RED='claret face brick'
OCHRE='rust coloured face brick'
DARK='purple brown face brick'
BRONZE='patinated sign bronze'
FRAME='dark steel glazing bars'
GLASS='blue-grey smoked glass'
DOOR='brown glazed door frames'
ROOF='dark flat roof finish'
SOFFIT='ivory entrance soffit'
PALETTE={PALE:{'color':[.81,.76,.66],'roughness':.79},GREY:{'color':[.56,.58,.55],'roughness':.80},
         BED:{'color':[.52,.43,.36],'roughness':.91},RED:{'color':[.50,.221,.147],'roughness':.85},
         OCHRE:{'color':[.584,.289,.178],'roughness':.87},DARK:{'color':[.354,.163,.130],'roughness':.85},
         BRONZE:{'color':[.318,.26,.15],'metallic':.61,'roughness':.38},FRAME:{'color':[.103,.121,.126],'metallic':.48,'roughness':.56},
         GLASS:{'color':[.104,.195,.217],'metallic':.32,'roughness':.31},DOOR:{'color':[.153,.118,.081],'metallic':.23,'roughness':.62},
         ROOF:{'color':[.287,.267,.217],'roughness':.9},SOFFIT:{'color':[.73,.666,.542],'roughness':.72},
         'black entrance shadow':{'color':[.057,.062,.063],'roughness':.82},'warm downlights':{'color':[.94,.78,.46],'roughness':.41}}
FONT=Path(__file__).resolve().parent/'fonts/CathayCinemaSign.otf'
HALF=5.7545
DEPTH=9.
LEFT=-HALF-DEPTH*24.196/48.91
RIGHT=HALF+DEPTH*14.11/11.58


def bonds(f,surface,lod):
    """Recess mortar behind alternating courses and trim all bricks to the actual apertures."""
    import shapely
    shapely.prepare(surface)
    mats=(RED,OCHRE,DARK,RED,RED,OCHRE,RED,DARK)
    data={m:([],[]) for m in (RED,OCHRE,DARK)}
    left,bottom,right,top=surface.bounds
    width,height=(.78,.30) if lod else (.39,.137)
    row=0;z=bottom
    while z<top-.008:
        u=left-(width/2 if row%2 else 0);col=0
        while u<right-.008:
            x0,x1=max(left,u+.009),min(right,u+width-.009);z0,z1=z+.007,min(top,z+height-.007)
            if x1-x0>.015 and z1-z0>.014:
                piece=box(x0,z0,x1,z1);mat=mats[(row*3+col*5+row*col)%len(mats)]
                if surface.covers(piece):
                    vs,fs=data[mat];i=len(vs);vs.extend(f.point(x,h,.009)for x,h in ((x0,z0),(x1,z0),(x1,z1),(x0,z1)));fs.append((i,i+1,i+2,i+3))
                elif surface.intersects(piece):
                    cut=surface.intersection(piece)
                    if cut.area>.0008:f.prism(cut,-.002,.011,mat,'cut brick ends')
            u+=width;col+=1
        z+=height;row+=1
    for mat,(vs,fs) in data.items():
        if vs:f.builder.add(vs,fs,mat,f.label+'/staggered face tiles')


def glazed(f,ap,lod,rows):
    f.window(ap,1 if lod else 2,rows if not lod else max(2,rows//2),frame=FRAME,trim=False,glass=GLASS,label='deep strip windows')


def flutes(f,u,z,h,w,lod):
    f.box(u,z,w,h,.16,.063,PALE,'cream vertical mullion piers')
    for delta in (-.3,.3) if lod else (-.32,.0,.32):
        f.box(u+delta*w,z,.025,h-.14,.09,.135,GREY,'relief lines on piers')


def street_wing(f,bays,lod):
    half=f.length/2; pitch=f.length/bays
    stations=[-half+(i+.5)*pitch for i in range(bays)]
    # The upper ribbon is slit by tall masonry piers; its lower arcade is a separate rhythm.
    ground=[opening(u,.48,pitch*.65,2.42)for u in stations]
    strips=[opening(u,4.20,min(1.06,pitch*.43),8.43)for u in stations]
    wall=f.wall(0,13.17,[*ground,*strips],thickness=.39,material=BED)
    bonds(f,wall,lod)
    for u,gl,sl in zip(stations,ground,strips):
        glazed(f,gl,lod,3);glazed(f,sl,lod,6)
        a=sl.bounds[2]-sl.bounds[0]
        for direction in (-1,1):flutes(f,u+direction*(a/2+.118),8.43,8.65,.178,lod)
    f.beam(13.18,.16,.20,PALE,label='horizontal coping')
    f.beam(12.91,.12,.13,GREY,label='roof shoulder')
    f.beam(3.34,.18,.49,PALE,label='shopfront lintel')
    f.beam(.24,.32,.075,GREY,label='grey street plinth')


def frontage(f,lod):
    outline=Polygon([(-HALF,0),(HALF,0),(HALF,14.05),(3.82,14.05),(3.82,16.15),(1.88,16.15),
                     (1.88,17.30),(.91,17.30),(.91,18.57),(-.91,18.57),(-.91,17.30),(-1.88,17.30),
                     (-1.88,16.15),(-3.82,16.15),(-3.82,14.05),(-HALF,14.05)])
    stripes=[(u,opening(u,4.06,.65 if abs(u)<3. else .77,11.43 if abs(u)<3. else 9.47))for u in (-4.41,-2.04,2.04,4.41)]
    front=opening(0,.11,6.38,2.77)
    exhibits=[opening(u,.74,1.11,1.76)for u in (-4.51,4.51)]
    holes=[front,*exhibits,*[sl for _,sl in stripes]]
    visible=f.wall(0,18.57,holes,thickness=.39,material=BED,outline=outline)
    bonds(f,visible,lod)
    for sl in exhibits:glazed(f,sl,lod,2)
    for u,sl in stripes:
        glazed(f,sl,lod,8)
        x0,b,x1,t=sl.bounds
        for x in (x0-.118,x1+.118):flutes(f,x,(b+t)/2,t-b+.24,.167,lod)
    # The strip windows, brick piers and projecting pale jambs step down towards each wing.
    for x,w,h in ((4.80,1.92,14.05),(2.85,1.93,16.15),(1.41,.93,17.3)):
        for side in (-1,1):f.box(side*x,h,w,.17,.45,.015,PALE,'stepped shoulder coping')
    # Return the recessed entrance several steps behind the 2024 marquee instead of
    # putting a false pane on the street plane. The doors and glazed transoms are visible inside.
    f.prism(front,-1.17,-1.12,'black entrance shadow','dark entrance back wall')
    for u in (-2.28,-.76,.76,2.28):
        f.box(u,1.28,1.42,2.29,.105,-1.007,DOOR,'recessed entrance door leaves')
        f.box(u,1.57,1.20,1.41,.055,-.94,GLASS,'recessed entrance glazing')
        f.box(u,2.58,1.24,.30,.059,-.96,GLASS,'entrance transoms')
        f.box(u,1.48,.035,1.55,.07,-.90,BRONZE,'door middle bars')
    f.box(0,2.74,6.53,.22,1.28,-.59,SOFFIT,'deep vestibule overhead')
    for side in (-1,1):
        f.box(side*3.19,1.43,.15,2.64,1.05,-.55,PALE,'marble entrance reveals')
    f.box(0,.085,6.52,.17,1.61,-.44,GREY,'threshold leading into vestibule')


def sign_tower(b,f,lod):
    # The pale sign blade, narrow upstand and metal pole are distinct solid forms.
    for u in (-1.13,1.13):
        f.box(u,11.46,.31,12.85,.42,.106,RED,'stepped red flanks around central blade')
    for w,z0,z1,d,mat in ((1.40,5.10,18.58,.28,GREY),(1.10,5.44,18.48,.39,PALE),
                           (.84,18.48,18.94,.39,GREY),(.56,18.95,21.06,.34,PALE),(.29,21.06,21.44,.26,GREY)):
        f.box(0,(z0+z1)/2,w,z1-z0,.36,d,mat,'stepped central sign tower')
    for u in (-.55,.55):
        f.box(u,11.9,.048,12.94,.10,.575,GREY,'raised sign edge reeds')
    for n,w in enumerate((1.62,1.50,1.39,1.29)):
        f.box(0,5.03+n*.155,w,.12,.58,.265,GREY if n%2 else PALE,'four projecting sign foot ledges')
    # Each upright letter is an independent extrusion. The tall, narrow typography
    # approximates the photographed metal lettering without incorporating a photograph.
    for j,char in enumerate('CATHAY'):
        add_facade_lettering(f,char,0,16.93-j*1.67,.48,1.16,.582,.65,BRONZE,
                             font=FONT,label='Vertical CATHAY/'+str(j))
    b.tube([(0,-.31,21.34),(0,-.31,22.04)],.041,GREY,6 if lod else 10,'Flagstaff/slender bare mast')


def marquee(b,f,lod):
    w=2*HALF+.40
    b.box((0,-.78,3.66),(w,1.70,.83),BED,label='Marquee/brick fascia core')
    panel=Facade(b,(-w/2,-1.63),(w/2,-1.63),'Marquee')
    bonds(panel,box(-w/2,3.37,w/2,3.96),lod)
    for z,h,t,mat in ((3.20,.115,1.82,PALE),(3.29,.10,1.85,GREY),(4.045,.13,1.86,PALE),(4.16,.079,1.90,GREY)):
        b.box((0,-.78,z),(w+.17,t,h),mat,label='Marquee/slim projecting metal trims')
    b.box((0,-.80,3.13),(w-.17,1.66,.10),SOFFIT,label='Marquee/ivory soffit')
    for u in np.linspace(-HALF+.45,HALF-.45,8 if lod else 15):
        b.box((u,-1.38,3.068),(.074,.074,.026),'warm downlights',label='Marquee/recessed downlights')
    add_facade_lettering(panel,'CATHAY',0,3.68,5.68,.51,.025,.103,BRONZE,font=FONT,label='Marquee/CATHAY')
    # The five Chinese characters rise above the forward edge of the canopy.
    for x in np.linspace(-2.38,2.38,5):
        panel.box(x,4.27,.04,.24,.04,.01,FRAME,'slim sign supports')
    add_facade_lettering(panel,'国泰电影院',0,4.59,5.65,.54,.004,.065,BRONZE,font=FONT,label='Marquee/Chinese letters')


def build_at_corner(b,lod):
    footprint=[(-HALF,0),(HALF,0),(RIGHT,DEPTH),(LEFT,DEPTH)]
    left=Facade(b,(LEFT,DEPTH),(-HALF,0),'Maoming Road')
    front=Facade(b,(-HALF,0),(HALF,0),'Corner entrance')
    right=Facade(b,(HALF,0),(RIGHT,DEPTH),'Middle Huaihai Road')
    street_wing(left,4,lod);frontage(front,lod);street_wing(right,5,lod)
    # The cropped roof stops at the same transverse section as the retained
    # coarse cinema. The tower and front shoulder have shallow independent returns.
    b.plan_prism(Polygon(footprint),12.95,13.12,ROOF,'Roof/short corner roof section')
    steps=[(-HALF,HALF,14.05,.74),(-3.82,3.82,16.15,1.20),(-1.88,1.88,17.30,1.10),(-.91,.91,18.57,.84)]
    for a,c,h,depth in steps:
        b.box(((a+c)/2,depth/2,h-.065),(c-a,depth,.13),GREY,label='Roof/capped stepped shoulders')
        # The sides and inner face of this increasingly tall shoulder stop at its
        # local roof plane. They are visible from oblique and overhead viewpoints.
        if h>13.2:
            for x in (a+.061,c-.061):
                b.box((x,depth/2,(13.12+h)/2),(.122,depth,h-13.12),RED,label='Roof/stepped side returns')
            b.box(((a+c)/2,depth-.067,(13.12+h)/2),(c-a,.134,h-13.12),RED,label='Roof/stepped rear return')
    sign_tower(b,front,lod);marquee(b,front,lod)


# The two photographed street portions have different lengths. The asset origin is
# at their transverse centre; the surveyed chamfer midpoint is 3.27 m to its left.
ORIGIN_X = 3.27


def add_geometry(b,lod):
    build_at_corner(b,lod)
    for part in b.parts:
        part['vertices']=[(x-ORIGIN_X,y,z) for x,y,z in part['vertices']]
