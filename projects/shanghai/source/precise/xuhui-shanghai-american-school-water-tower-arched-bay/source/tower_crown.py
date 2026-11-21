"""Build the photographed upper face of the former Shanghai American School water tower."""
from math import cos, sin, pi
from pathlib import Path
from random import Random
from shapely.geometry import box, Polygon
from photo_architecture import Facade

BRICK='Orange pressed brick'; TRIM='Red-brown cornice brick'; BED='Grey-red lime joints'
CREAM='Weathered stone surround'; IRON='Slate-grey louvres'; DARK='Louvre shadow'
PAINT='Blue-green lower frame'; GLASS='Faded blue-green lower panels'; ROOF='Warm roof plane'
METAL='Dark flashing'; CUT='Section back'
PALETTE={name:dict(color=color,roughness=value) for name,color,value in [
 (BRICK,[.77,.56,.45],.94),(TRIM,[.55,.32,.25],.91),(BED,[.54,.40,.34],.98),
 (CREAM,[.65,.60,.54],.93),(IRON,[.34,.37,.36],.85),(DARK,[.13,.17,.17],.91),
 (PAINT,[.19,.40,.44],.88),(GLASS,[.23,.48,.53],.52),(ROOF,[.58,.34,.26],.91),
 (METAL,[.32,.27,.23],.84),(CUT,[.50,.37,.30],.95)]}
WIDTH=4.4;HEIGHT=4.36;WINDOW_R=.395;SPRING=2.72;SILL=.50

def round_head(radius,base,spring,n):
    points=[(-radius,base),(radius,base)]
    points.extend((radius*cos(pi*i/n),spring+radius*sin(pi*i/n)) for i in range(n+1))
    return Polygon(points)

def add_building(builder,lod):
    facade=Facade(builder,(-WIDTH/2,0),(WIDTH/2,0),'Water tower crown')
    steps=18 if lod else 36
    inner=round_head(WINDOW_R,SILL,SPRING,steps)
    rim=round_head(WINDOW_R+.111,SILL-.059,SPRING,steps)
    facade.wall(0,4.045,[rim],thickness=.32,material=BRICK)
    facade.prism(rim.difference(inner),-.100,.036,CREAM,'Recessed arch and vertical jambs')
    # Some of the lightest voussoirs can be distinguished above the louvre.
    for i in range(11):
        a=pi*(i+.045)/11;b=pi*(i+.955)/11
        coords=[]
        for r,angles in [(WINDOW_R+.130,[a,(a+b)/2,b]),(WINDOW_R+.174,[b,(a+b)/2,a])]:
            coords.extend((r*cos(v),SPRING+r*sin(v)) for v in angles)
        facade.prism(Polygon(coords),-.005,.023,BRICK,'Upper brick arch')
    facade.prism(inner.buffer(.007),-.225,-.215,DARK,'Back of louvred window')
    # The straight projecting piers on both sides and their recessed center are visible.
    for sign,label in [(-1,'Left'),(1,'Right')]:
        facade.box(sign*(WIDTH/2-.352),2.01,.704,4.02,.167,.044,BRICK,label+' shallow pier')
        facade.box(sign*(WIDTH/2-.695),2.013,.055,4.026,.057,.047,TRIM,label+' inner brick arris')
    for bottom,top,w,back,front,mat,name in [
        (0,.085,4.56,-.36,.18,TRIM,'Lower projecting sill course'),
        (.085,.143,4.45,-.32,.085,BRICK,'Lower setback'),
        (3.92,4.035,4.49,-.42,.15,TRIM,'Lower cornice course'),
        (4.035,4.108,4.58,-.43,.22,BRICK,'Outward cornice step'),
        (4.108,4.185,4.75,-.46,.30,TRIM,'Cornice shadow and shelf'),
        (4.185,4.246,4.88,-.49,.365,BRICK,'Overhanging top course'),
        (4.246,4.295,4.92,-.49,.374,METAL,'Weathered cap edge')]:
        facade.prism(box(-w/2,bottom,w/2,top),back,front,mat,name)
    for pos in [-1.94,-1.48,-1.02,-.56,-.10,.36,.82,1.28,1.74]:
        facade.box(pos,4.028,.12,.13,.17,.135,TRIM,'Cornice soffit block')
    mid=1.57
    facade.prism(inner.intersection(box(-1,SILL,1,mid)), -.170,-.158,GLASS,'Glazed lower light')
    for pos in [-WINDOW_R+.025,WINDOW_R-.025,0]:
        facade.box(pos,(SILL+mid)/2,.038,mid-SILL,.048,-.123,PAINT,'Lower window stile')
    for z in [SILL+.025,SILL+.41,mid-.028]:
        facade.box(0,z,2*WINDOW_R-.037,.047,.052,-.119,PAINT,'Lower sash rails')
    facade.box(0,mid+.018,2*WINDOW_R,.077,.11,-.08,IRON,'Transom under louvres')
    z=mid+.087
    while z<SPRING+WINDOW_R-.012:
        blade=inner.intersection(box(-1,z,1,z+.080))
        if blade.area>.001:
            # Blades tilt out toward their lower edges, leaving air between slats.
            builder.prism(blade,0,.021,lambda u,v,d:facade.point(u,v,-.067+(z-v)*.67+d),IRON,'Sloped louvre blade')
        z+=.110
    facade.box(0,SILL-.063,2*WINDOW_R+.24,.092,.195,.029,CREAM,'Window sill')
    # Only the low triangular patch of roof above the parapet has a photographic outline.
    builder.add([(-1.94,.32,4.286),(1.94,.32,4.286),(0,.96,4.965),
                 (-1.94,.35,4.277),(1.94,.35,4.277),(0,.99,4.952)],
                [(0,1,2),(5,4,3),(0,3,4,1),(1,4,5,2),(2,5,3,0)],ROOF,'Visible roof slope')
    facade.prism(box(-WIDTH/2,.0,WIDTH/2,4.02),-.336,-.320,CUT,'Section back')
    tint=Path(__file__).with_name('brick-courses.png')
    for mat in (BRICK,TRIM):
        builder.palette[mat]['texture']=str(tint)
    for part in builder.parts:
        if part['material'] in (BRICK,TRIM):
            # The full elevation occupies one atlas. The viewer uses edge-clamped samplers.
            part['texcoords']=[[(x+2.55)/5.10,1.-(z+.10)/4.52] for x,y,z in part['vertices']]

def make_brick_texture(destination):
    from PIL import Image,ImageDraw
    size=384;rng=Random(375);im=Image.new('RGB',(size,size),(191,169,151));draw=ImageDraw.Draw(im)
    for row in range(48):
        for col in range(-1,25):
            x=col*16+(row%2)*8;y=row*8
            val=rng.randrange(-12,11);base=[226+val,199+val,180+val]
            draw.rectangle((x+1,y+1,x+15,y+7),fill=tuple(base))
    px=im.load()
    for y in range(size):
        for x in range(size):
            v=rng.randrange(-5,6);px[x,y]=tuple(max(0,min(255,c+v)) for c in px[x,y])
    im.save(destination)
