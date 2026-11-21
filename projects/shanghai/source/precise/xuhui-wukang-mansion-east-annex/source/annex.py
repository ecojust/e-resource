"""The five-storey east annex observed from Huaihai Middle Road."""
import math
import sys
from pathlib import Path

from shapely.affinity import translate
from shapely.geometry import Polygon, box
from shapely.ops import unary_union

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[3]
sys.path.insert(0, str(PROJECT/'source/precise/hongkou-general-post-office/source/common'))
from photo_architecture import Builder, Facade
from sign_lettering import lettering_shapes

B = 'russet face brick'
M = 'brick bed and perp joints'
W = 'off-white render'
C = 'pale concrete edge'
S = 'dark painted window steel'
G = 'blue-grey window glass'
G2 = 'shop display glass'
L = 'ochre louvres'
L2 = 'brick red louvres'
PL = 'green civic enamel'
IV = 'ivory lettering'
R = 'lead grey roof'
BACK = 'cut surface'
def tone(rgb, rough=.78, metallic=0):
    return dict(color=list(rgb),roughness=rough,metallic=metallic)
PALETTE = {B:tone((.465,.196,.145)),M:tone((.331,.186,.151)),W:tone((.807,.813,.798)),
    C:tone((.749,.732,.647)),S:tone((.141,.146,.147),.55,.30),G:tone((.205,.286,.328),.35,.35),
    G2:tone((.090,.128,.133),.29,.30),L:tone((.552,.401,.239),.70,.19),
    L2:tone((.445,.229,.154),.72,.17),PL:tone((.019,.295,.220),.49,.19),IV:tone((.91,.88,.75)),
    R:tone((.40,.402,.41)),BACK:tone((.58,.583,.566))}

HALF = 12.075
BASE = 6.14
TOP = 18.48
DEPTH = 3.64
# The 1834 entrance and adjacent reduced-height display opening follow the 2024 photograph.
STREET_OPENINGS = [
    ('west grille',-11.35,.70,.82,1.05), ('service door',-10.16,.18,.83,2.13),
    ('canopied west shop',-6.64,.13,3.55,2.68), ('1834 bookshop entrance',-2.78,.09,2.12,2.72),
    ('1834 display',.00,.62,2.10,2.19), ('narrow center door',2.37,.09,.95,2.58),
    ('east shop window',5.62,.30,3.52,2.40),('east end shop window',9.89,.30,3.63,2.40)]
UPPER = [(6.84,9.47),(10.85,13.50),(14.87,17.52)]
SCREENS = [[-4.83,-3.64,4.06],[-4.69,-3.47,4.55,5.71],[-7.31,-4.68,-3.49,-.36,6.12]]
LOW = [(-9.31,2.22),(-5.50,2.46),(-.80,2.02),(3.72,2.45),(8.83,2.19)]
FONT = HERE/'fonts/AnnexStreetSubset.otf'

def pane(f, center, bottom, width, height, count, reduced, display=False, door=False):
    depth = .22 if display else .19
    f.box(center,bottom+height/2,width,height,.042,-depth,G2 if display else G,'recessed glazing')
    for j in range(count+1):
        u = center-width/2+j*width/count
        f.box(u,bottom+height/2,.043,height,.042,-depth+.055,S,'steel uprights')
    for frac in ((0,1) if reduced and display else (0,.77,1)):
        f.box(center,bottom+frac*height,width,.05,.052,-depth+.055,S,'steel horizontals')
    if door:
        f.box(center+.31,bottom+1.04,.035,.40,.09,-depth+.13,IV,'door pull')
    return box(center-width/2,bottom,center+width/2,bottom+height)

def linework(f, surface, reduced):
    for n in range(1, int(BASE/.088)):
        if reduced and n%4:continue
        h=n*.088
        line=surface.intersection(box(-HALF,h-.004,HALF,h+.004))
        if not line.is_empty and line.area>0:f.prism(line,.0008,.0025,M,'bed joints')
        if reduced:continue
        for j in range(89):
            x=-HALF+j*.283+(n%2)*.1415
            if x<-HALF or x>HALF:continue
            joint=box(x,h+.004,min(x+.008,HALF),min(h+.083,BASE))
            if joint.area>0 and surface.contains(joint):
                f.builder.add([f.point(x0,z,.002)for x0,z in list(joint.exterior.coords)[:4]],[(0,1,2,3)],M,f.label+'/staggered head joints')

def letters(f, text, x, z, width, height, outward, material, group):
    for char,g in lettering_shapes(text,width,height,font=FONT):
        f.prism(translate(g,xoff=x,yoff=z),outward,outward+.004,material,group+' '+char)

def louvre(f, x, center, width, height, base, out, reduced):
    depth=.39 if out==L else .47
    f.box(x,center,width-.075,height-.07,.08,base+.035,S,'equipment recess')
    levels=5 if reduced else max(6,round(height/.087))
    for j in range(levels):
        h=center-height/2+(j+.5)*height/levels
        f.box(x,h,width,height/levels*.53,.074,base+depth,out,'front louvre slats')
        for side in (-1,1):f.box(x+side*(width/2-.026),h,.050,height/levels*.53,depth,base+depth/2,out,'side louvre slats')
    f.box(x,center+height/2,width+.033,.040,depth+.04,base+depth/2,out,'hood caps')

def first_and_second(builder, reduced):
    f=Facade(builder,(-HALF,.15),(HALF,.15),'Huaihai brick shop base')
    holes=[]
    for name,x,z,w,h in STREET_OPENINGS:
        is_door='door' in name or 'entrance' in name
        if name=='1834 bookshop entrance':
            # The 2024 photograph shows the door standing open. Model the entrance
            # reveals and a short patch of visible floor, with a neutral cut beyond.
            holes.append(box(x-w/2,z,x+w/2,z+h))
            for side in (-1,1):
                f.box(x+side*(w/2-.028),z+h/2,.056,h,1.58,-.80,W,'visible bookshop entry reveal')
            f.box(x,z-.045,w,.090,1.60,-.80,C,'threshold and visible entry floor')
            f.box(x,z+h+.025,w,.050,1.60,-.80,W,'bookshop entrance soffit')
            f.box(x,z+h/2,w,h,.08,-1.61,BACK,'neutral cut behind public entry')
        else:
            holes.append(pane(f,x,z,w,h,1 if w<1.2 or name.startswith('1834') else (2 if reduced else 3),
                              reduced,display=True,door=is_door))
        # A continuous slim black reveal frames the 2024 doorway and display.
        if name.startswith('1834'):
            for side in (-1,1):f.box(x+side*w/2,z+h/2,.078,h+.08,.145,.028,S,'bookshop opening frame')
            f.box(x,z+h+.018,w+.10,.097,.145,.028,S,'bookshop frame head')
    for x,w in LOW:holes.append(pane(f,x,4.66,w,1.16,4 if not reduced else 2,reduced))
    face=f.wall(.04,BASE,holes,.51,B)
    linework(f,face,reduced)
    base_shape=face.intersection(box(-HALF,.04,HALF,.24))
    f.prism(base_shape,-.015,.049,C,'granite base')
    f.box(-6.64,3.16,3.82,.20,.98,.43,S,'western shop canopy')
    for x in (-8.37,-4.92):
        f.builder.tube([f.point(x,3.69,.02),f.point(x,3.22,.78)],.024,S,6,'Huaihai shop/canopy supports')
    for x,w,h,z in [(-9.09,.75,.87,3.65),(-4.14,1.14,.88,5.10),(.77,1.10,1.10,5.00),
                       (7.10,1.24,1.22,4.98),(10.96,1.18,1.38,4.28)]:
        louvre(f,x,z,w,h,.045,L2,reduced)
    # The address and signs are separate meshes. Their lettering is an original typeset approximation.
    f.box(-1.30,2.91,.35,.24,.026,.041,PL,'1834 civic number plaque')
    letters(f,'1834',-1.30,2.938,.278,.116,.057,IV,'1834 numerals')
    letters(f,'淮海中路',-1.30,2.848,.251,.045,.057,IV,'street-name line')
    f.box(-1.30,2.60,.78,.20,.027,.042,IV,'bookshop placard')
    letters(f,'印象武康主题店',-1.30,2.613,.70,.093,.058,S,'bookshop placard type')
    letters(f,'大隐书局',-2.78,3.30,1.83,.34,.046,S,'bookshop sign')
    return f

def glazed_outline():
    # The street front wraps around both cheeks. The return terminates against the solid side blade.
    x=9.71;r=.92
    points=[(-x-r,.53)]
    for i in range(1,8):
        a=math.pi+math.pi/2*i/7;points.append((-x+r*math.cos(a),.53+r*math.sin(a)))
    points.append((x,-.39))
    for i in range(1,8):
        a=-math.pi/2+math.pi/2*i/7;points.append((x+r*math.cos(a),.53+r*math.sin(a)))
    return points

def ribbon_floors(b,reduced):
    pts=glazed_outline()
    for j,(a,c)in enumerate(zip(pts,pts[1:])):
        f=Facade(b,a,c,'Glazed ribbon '+('center'if j==7 else 'west curve'if j<7 else 'east curve'))
        length=f.length
        for storey,(low,high)in enumerate(UPPER):
            # The glass, infill below it and shallow continuous floor edges turn together at the ends.
            lower=BASE if storey==0 else UPPER[storey-1][1]
            f.box(0,(lower+low)/2,length+.002,low-lower,.32,-.158,W,'rendered spandrel')
            pane(f,0,low,length,high-low,22 if j==7 and not reduced else 15 if j==7 else 1,reduced)
            f.box(0,low-.08,length+.012,.140,.48,.015,C,'rounded sill')
            f.box(0,high+.075,length+.013,.145,.43,.009,W,'ribbon window head')
            if j==7:
                for x in SCREENS[storey]:louvre(f,x,low+.10,1.06,.91,.15,L,reduced)
        f.box(0,(TOP+UPPER[-1][1])/2,length+.002,TOP-UPPER[-1][1],.37,-.17,W,'parapet')
        f.box(0,TOP+.10,length+.016,.16,.56,.028,C,'parapet cap')
    for side in (-1,1):
        b.box((side*11.31,1.86,(TOP+BASE)/2),(1.48,3.32,TOP-BASE),W,label='Rendered side blade')
        b.box((side*11.31,1.80,TOP+.045),(1.55,3.44,.13),C,label='Side blade coping')
    # The neutral roof strip and two bounded returns stop ahead of the retained rear roof.
    plan=Polygon([*pts,(10.63,DEPTH),(-10.63,DEPTH)])
    b.prism(plan,TOP-.35,TOP-.18,lambda x,y,z:(x,y,z),R,'Shallow flat roof behind parapet')
    b.box((0,DEPTH-.12,(TOP+BASE)/2),(2*HALF-.12,.20,TOP-BASE),BACK,label='Neutral cut behind upper windows')
    for j,(p,q)in enumerate([((HALF,.15),(HALF,DEPTH)),((-HALF,DEPTH),(-HALF,.15))]):
        Facade(b,p,q,'Short return '+str(j)).wall(.04,BASE,(),.12,B)
    b.box((0,DEPTH-.11,BASE/2),(2*HALF-.24,.20,BASE),BACK,label='Neutral shop-depth cut')
    b.box((0,(DEPTH+.15)/2,BASE-.055),(2*HALF,DEPTH-.15,.11),C,label='Storey slab over shops')

def build_annex(b, reduced):
    first_and_second(b, reduced)
    ribbon_floors(b, reduced)
