"""Brick entrance of the former Western Girls' School, surveyed from Fayhoo's courtyard view."""
from math import cos, sin, pi
from pathlib import Path
from random import Random
from PIL import Image, ImageDraw
from shapely.affinity import affine_transform, scale, translate
from shapely.geometry import Polygon, LineString, box
from shapely.ops import unary_union

BRICK='Charcoal running-bond brick'
RED='Red rubbed brick'
GABLE='Red running-bond gable courses'
ARCH='Warm red arch voussoirs'
BLUE='Dark arch voussoirs'
BED='Pale lime joints'
DARK='Dark blue brick stringcourse'
BUFF='Weathered buff render'
PANEL='Incised red terracotta'
SCROLL='Raised terracotta scroll'
DATES='Raised red date figures'
STONE='Stone thresholds'
PALETTE={m:dict(color=c,roughness=.91) for m,c in [
    (BRICK,[.94,.94,.94]),(GABLE,[.95,.93,.88]),(RED,[.50,.22,.15]),(ARCH,[.59,.30,.205]),(BLUE,[.21,.245,.238]),
    (BED,[.61,.58,.46]),(DARK,[.19,.204,.199]),(BUFF,[.84,.80,.65]),(PANEL,[.54,.27,.195]),
    (SCROLL,[.66,.33,.215]),(DATES,[.60,.257,.160]),(STONE,[.59,.60,.55])]}
UNIT=.0155
def xyz(x,z,d):return ((x-132)*UNIT,-d,(540-z)*UNIT)
def face(b,g,back,front,mat,label):
    # The image plane has its origin at the upper left. Flip the vertical axis before extrusion.
    g=affine_transform(g,[UNIT,0,0,-UNIT,-132*UNIT,540*UNIT])
    b.prism(g,back,front,lambda x,z,d:(x,-d,z),mat,label)
def strip(b,x1,y1,x2,y2,back,front,mat,label):
    face(b,box(x1,y1,x2,y2),back,front,mat,label)
def curve(b,pts,width,back,front,mat,label):
    f=LineString(pts).buffer(width/2,cap_style='flat',join_style='round',quad_segs=2)
    face(b,f,back,front,mat,label)
def opening(steps):
    return Polygon([(73,542),(73,360)]+[(132+59*cos(t*pi/steps),360-66*sin(t*pi/steps))for t in range(steps,-1,-1)]+[(191,542)])
def ring(angle,half1,half2,steps):
    t1,t2=angle
    return Polygon([(132+radius*cos(t*pi/180),360-(radius+7)*sin(t*pi/180)) for radius,sequence in
                    [(half2,range(steps+1)),(half1,range(steps,-1,-1))] for k in sequence for t in [t1+(t2-t1)*k/steps]])
def texture(path):
    random=Random(403);w,h=640,1024;im=Image.new('RGB',(w,h),(164,152,129));pen=ImageDraw.Draw(im)
    for row,y in enumerate(range(-6,h,11)):
        for x in range(-20 if row%2 else -3,w,34):
            light=random.randrange(-18,18)
            color=tuple(v+light for v in (97,104,99))
            pen.rectangle((x+1,y+1,x+32,y+9),fill=color)
            for _ in range(23):
                px,py=x+random.randint(1,32),y+random.randint(1,9);off=random.randint(-9,10)
                pen.point((px,py),fill=tuple(v+off for v in color))
    red=Image.new('RGB',(w,h),(156,118,91));pen=ImageDraw.Draw(red)
    for row,y in enumerate(range(-6,h,11)):
        for x in range(-20 if row%2 else -3,w,34):
            light=random.randrange(-15,16);c=tuple(v+light for v in (170,94,65))
            pen.rectangle((x+1,y+1,x+32,y+9),fill=c)
            for _ in range(15):
                px,py=x+random.randint(1,32),y+random.randint(1,9);off=random.randint(-11,10)
                pen.point((px,py),fill=tuple(v+off for v in c))
    atlas=Image.new('RGB',(2*w,h));atlas.paste(im,(0,0));atlas.paste(red,(w,0));atlas.save(path)
def date_mesh(b,year,left,right,lod):
    # A widely available serif outline supplies a legible approximation of the historic numerals.
    from matplotlib.textpath import TextPath
    from matplotlib.font_manager import FontProperties
    letters=TextPath((0,0),year,size=10,prop=FontProperties(family='DejaVu Serif',weight='bold'))
    rings=[Polygon(v)for v in letters.to_polygons()if len(v)>3];shape=Polygon()
    for item in rings:shape=shape.symmetric_difference(item)
    x0,y0,x1,y1=shape.bounds
    shape=affine_transform(shape,[(right-left)/(x1-x0),0,0,-18/(y1-y0),left-x0*(right-left)/(x1-x0),248+y0*18/(y1-y0)])
    if lod:shape=shape.simplify(.18,preserve_topology=True)
    for i,part in enumerate(shape.geoms if shape.geom_type=='MultiPolygon'else [shape]):
        face(b,part,.090,.120,DATES,f'{year} raised date numeral {i+1}')
def add_building(b,lod):
    n=26 if lod else 55
    aperture=opening(n)
    skin=box(22,205,242,540).difference(aperture)
    face(b,skin,-.57,0,BRICK,'Coursed masonry with full-depth round portal')
    # Each inner return terminates at the same visible arch profile, leaving an open passage.
    for left,right in [(22,73),(191,242)]:
        strip(b,left,398,right,406,.001,.012,DARK,'Impost level dark brick line')
    face(b,ring((0,180),59,83,n),.003,.023,BED,'Recessed mortar bed behind arch rings')
    for i in range(41):
        angle=i*180/41
        for level,(lo,hi) in enumerate([(59,68),(68.8,82.7)]):
            mat=ARCH if ((i//5+level)%2==0)else BLUE
            face(b,ring((angle+.32,angle+180/41-.32),lo,hi,1 if lod else 3),.023,.064,mat,f'Arch ring {level+1}, brick {i+1}')
    for s in [-1,1]:
        for row in range(8):
            left=49 if s<0 else 191
            strip(b,left,360+row*5,left+24,364.5+row*5,.011,.048,ARCH if row%4 else RED,'Banded springing jamb')
        x=33 if s<0 else 230
        strip(b,x-6,208,x+6,501,.012,.045,GABLE,'Flanking brick pilaster')
        strip(b,x-8,496,x+8,536,.008,.063,STONE,'Pilaster foot')
    for top,bottom,mat,depth in [(201,209,BUFF,.115),(209,215,DARK,.120),(215,220,RED,.083),(252,257,RED,.075),(257,261,DARK,.072)]:
        strip(b,20,top,244,bottom,.005,depth,mat,'Cornice and horizontal date frieze course')
    for year,left,right in [('1893',51,126),('1894',146,224)]:
        strip(b,left-3,223,right+3,252,.03,.069,DARK,'Dark surround to date tablet')
        strip(b,left,226,right,250,.069,.090,BUFF,'Cream stone date tablet')
        date_mesh(b,year,left+9,right-7,lod)
    face(b,Polygon([(123,219),(143,219),(141,266),(136,283),(126,283),(122,263)]),.045,.122,RED,'Key block and brick mullion between date tablets')
    for x in (126,130,134,138):
        strip(b,x,259,x+.9,278,.123,.129,ARCH,'Flute at arch head')
    outline=Polygon([(22,203),(22,82),(34,79),(38,71),(60,71),(86,71),(133,-25),(137,-25),(180,64),(230,62),(238,72),(242,74),(242,203)])
    gable=Polygon([(67,202),(67,123),(136,-25),(207,124),(207,202)])
    face(b,outline,-.42,-.004,BUFF,'Cream shoulder blocks and gable backing')
    face(b,gable,-.006,.036,GABLE,'Narrow peaked brick gable')
    for top,bottom in [(149,154),(154,160),(72,78),(45,52)]:
        shape=gable.intersection(box(0,top,266,bottom))
        face(b,shape,.036,.079,DARK,'Dark gable stringcourse')
    for l,r in [(70,126),(149,203)]:
        strip(b,l,162,r,192,.036,.079,DARK,'Dark surround of blank upper tablet')
        strip(b,l+4,166,r-4,188,.079,.083,BUFF,'Blank recessed pale upper tablet')
    strip(b,130,-15,138,201,.036,.061,GABLE,'Brick central spine of gable')
    for s in (-1,1):
        def pts(q):return [(134+s*x,y)for x,y in q]
        plaque=Polygon(pts([(6,87),(43,87),(68,132),(68,143),(6,143)]))
        face(b,plaque,.044,.074,PANEL,'Trapezoidal relief panel')
        face(b,plaque.boundary.buffer(1.35,join_style='mitre'),.073,.09,SCROLL,'Raised relief panel border')
        # The two panels carry foliate relief. Only its larger lobes can be read in the source.
        for dx,dy,rad,turn in [(26,112,12,-1),(48,127,9,1),(48,104,5.5,-1)]:
            points=[]
            count=12 if lod else 31
            for j in range(count):
                t=j/(count-1);theta=(-.62+turn*t*1.65)*pi;r1=rad*(1-.76*t)
                points.append((dx+r1*cos(theta),dy+.74*r1*sin(theta)))
            curve(b,pts(points),1.45,.074,.103,SCROLL,'Coiled relief stem')
        curve(b,pts([(11,133),(18,129),(25,121),(30,109),(37,102),(47,98)]),2.1,.075,.10,SCROLL,'Swept diagonal relief stem')
        if s<0:
            for j in range(5):
                ox=20+5*j;oy=130-5*j
                curve(b,pts([(ox,oy),(ox+3,oy-6),(ox+4,oy-10),(ox+7,oy-13)]),1.15,.076,.106,SCROLL,'Feathered leaves of left relief')
        else:
            for j in range(4):
                ox=37+5*j;oy=123-1.6*j
                curve(b,pts([(ox,oy),(ox+2,oy-4),(ox+4,oy-4),(ox+5,oy-2)]),1.15,.076,.106,SCROLL,'Short curling lobes of right relief')
        for dx,dy,a in [(15,129,-2),(19,124,1),(26,115,2),(36,105,2),(44,101,-3),(55,128,-1)]:
            leaf=Polygon(pts([(dx-3.5,dy+1.8),(dx-.5,dy-2.8),(dx+4.5,dy-2+a),(dx+2,dy+.4)]))
            face(b,leaf,.08,.108,SCROLL,'Low relief leaf')
        curve(b,pts([(2,-25),(72,124)]),3.1,.038,.113,ARCH,'Pitched rubbed-brick coping')
        strip(b,23 if s<0 else 204,72,63 if s<0 else 241,77,-.44,.065,BUFF,'Capped shoulder pier')
    for z0,z1,d in [(539,544,.39),(544,550,.69),(550,557,.98)]:
        strip(b,30,z0,233,z1,-.53,d,STONE,'Broad entrance tread')
    for x in (37,226):
        profile=Polygon([(0,0),(0,.60),(.09,.60),(.20,.55),(.35,.40),(.55,.23),(.75,.13),(.98,.10),(.98,0)])
        # Swept pale parapets on both sides of the steps.
        b.prism(profile,-(x-132+4)*UNIT,-(x-132-4)*UNIT,lambda d,z,negx:(-negx,-d,(540-549)*UNIT+z),BUFF,'Swan-neck curb at steps')
    b.palette[BRICK]['texture']=b.palette[GABLE]['texture']=str(Path(__file__).with_name('charcoal-bond.png'))
    for p in b.parts:
        if p['material'] in (BRICK,GABLE):
            xoff=0 if p['material']==BRICK else .5
            p['texcoords']=[[xoff+(.04+.92*(x/UNIT+132)/266)/2+y*.012,1-(z/UNIT+17)/610] for x,y,z in p['vertices']]
