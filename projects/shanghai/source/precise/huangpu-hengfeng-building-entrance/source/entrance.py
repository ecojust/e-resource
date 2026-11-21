"""Number 452 of the Hengfeng Building, drawn from three public street images."""
from math import atan, cos, degrees, pi, sin, tau

from shapely import affinity
from shapely.geometry import LineString, Polygon, box
from shapely.ops import unary_union
from pathlib import Path
from photo_architecture import Facade
from stone import wall_uv

WALL='ashlar facing'; TRIM='buff stone trim'; LIGHT='capital stone'; DARK='deep portal shadow'
FRAME='painted sash metal'; GLASS='grey green glass'; COPPER='dark oxblood name'; METAL='door grille'
PALETTE={name:{'color':rgb,'roughness':rough} for name,rgb,rough in [
    (WALL,[.585,.585,.555],.94),(TRIM,[.675,.651,.579],.91),(LIGHT,[.729,.705,.630],.86),
    (DARK,[.15,.167,.159],.97),(FRAME,[.217,.247,.225],.83),(GLASS,[.37,.428,.412],.42),
    (COPPER,[.328,.156,.106],.78),(METAL,[.248,.261,.245],.8)]}
PALETTE[WALL]={'color':[1,1,1],'roughness':.94,'texture':str(Path(__file__).with_name('ashlar-grain.png'))}
HALF=4.18
TOP=13.65

def profile_curve(x,z,rw,rh,n):
    return [(x+rw*cos(tau*i/n),z+rh*sin(tau*i/n)) for i in range(n)]

def scroll(face,x,z,rad,mirror,lod,d,material,label):
    pts=[]
    for i in range(16 if lod else 37):
        t=i/(15 if lod else 36)
        a=.20+tau*1.29*t;r=rad*(1-.83*t)
        pts.append((x+mirror*r*cos(a),z+r*sin(a)))
    ribbon=LineString(pts).buffer(.033 if rad<.26 else .043,quad_segs=3,cap_style='round')
    face.prism(ribbon,d,d+.044,material,label)

def fluted_shaft(builder,x,y,bottom,top,radius,lod):
    # Eighteen back-to-back concave channels on the photographed large order.
    flutes=18
    samples=3 if lod else 6
    ring=[]
    for i in range(flutes*samples):
        a=tau*i/(flutes*samples)
        r=radius*(1-.052*sin(pi*(i%samples)/samples)**2)
        ring.append((x+r*cos(a),y+r*sin(a)))
    vertices=[(u,v,height) for height in (bottom,top) for u,v in ring]
    n=len(ring)
    faces=[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    faces+=[tuple(reversed(range(n))),tuple(range(n,2*n))]
    builder.add(vertices,faces,WALL,'Large order / cut flutes')

def arc(zbase,rise,radius,n,shift=0):
    return [(radius*(i*2/n-1),zbase+shift+rise*(1-(i*2/n-1)**2)) for i in range(n+1)]

def frieze(face,lod):
    n=18 if lod else 48
    spring=7.13;rise=1.15;rw=3.38
    face.prism(Polygon([(-rw,spring),(rw,spring),*reversed(arc(spring,rise,rw,n))]),.57,1.015,TRIM,'Door hood / arc field')
    for h,thick,depth in [(0,.12,1.16),(.12,.105,1.26),(.225,.095,1.32)]:
        strip=Polygon([*arc(spring,rise,rw,n,h),*reversed(arc(spring,rise,rw,n,h+thick))])
        face.prism(strip,.92,depth,TRIM,'Door hood / projected mouldings')
    for i in range(39):
        x=-3.24+6.48*i/38
        z=spring+rise*(1-(x/rw)**2)
        slope=-2*rise*x/rw**2
        brick=affinity.rotate(box(x-.054,z-.112,x+.054,z+.006),degrees(atan(slope)),origin=(x,z))
        face.prism(brick,1.015,1.144,LIGHT,'Door hood / curved dentil band')
        egg=Polygon(profile_curve(x,z-.199,.063,.087,10 if lod else 16))
        egg=affinity.rotate(egg,degrees(atan(slope)),origin=(x,z))
        face.prism(egg,1.008,1.082,LIGHT,'Door hood / egg band')
    # Rounded double lobe and pointed base bound the center tile seen in each period.
    heart=[]
    for i in range(36 if lod else 68):
        t=tau*i/(36 if lod else 68)
        heart.append((.42*sin(t)**3,7.35+.021*(13*cos(t)-5*cos(2*t)-2*cos(3*t)-cos(4*t))))
    shape=Polygon(heart)
    face.prism(shape,1.002,1.054,WALL,'Door hood / central cartouche')
    face.prism(shape.difference(shape.buffer(-.037)),1.045,1.101,LIGHT,'Door hood / cartouche rim')
    for side in (-1,1):
        scroll(face,side*.797,7.34,.27,side,lod,1.008,LIGHT,'Door hood / inner foliage scroll')
        scroll(face,side*1.34,7.28,.215,-side,lod,1.009,LIGHT,'Door hood / outer foliage scroll')
        stem=LineString([(side*.32,7.23),(side*.50,7.10),(side*.68,7.10),(side*.94,7.17),(side*1.20,7.27),(side*1.53,7.33),(side*1.71,7.38)]).buffer(.038,quad_segs=3)
        face.prism(stem,1.009,1.084,LIGHT,'Door hood / carved stems')
    for x in (-2.37,2.37):
        for z,width,height,depth in [(6.87,1.49,.22,1.24),(7.02,1.63,.10,1.33),(7.11,1.74,.09,1.37)]:
            face.box(x,z,width,height,depth,depth/2,TRIM,'Door hood / broken bed mould')

def add_building(builder,distant=False):
    from repeat import repeat_only_texture
    repeat_only_texture(builder,'ashlar-grain.png')
    from sign_lettering import add_facade_lettering
    front=Facade(builder,(-HALF,0),(HALF,0),'Hengfeng entrance')
    doorway=box(-2.06,-.01,2.06,4.99)
    windows=[box(x-.85,z,x+.85,z+h) for z,h in [(7.53,1.84),(10.38,1.86)] for x in [-1.02,1.02]]
    wall=box(-HALF,0,HALF,TOP).difference(unary_union([doorway,*windows]))
    front.prism(wall,-.82,0,WALL,'Street wall / opening and four window voids')
    front.prism(doorway,-.69,-.65,DARK,'Portal / inner shadow surface')
    for i,x in enumerate([-1.75,-.875,0,.875,1.75]):
        front.box(x,3.70,.033,1.40,.055,-.557,METAL,'Portal / fanlight mullions')
    radius=2.02
    arch=[(radius*(2*i/24-1),3.66+.30*(1-(2*i/24-1)**2)) for i in range(25)]
    front.prism(LineString(arch).buffer(.026,quad_segs=2),-.595,-.51,METAL,'Portal / arched grille head')
    for height in (3.03,3.20,3.37,3.54,3.70):
        front.box(0,height,4.0,.028,.060,-.55,METAL,'Portal / horizontal grille')
    for i,opening in enumerate(windows):
        before_window=len(builder.parts)
        front.window(opening,columns=2,rows=1,trim=False,frame=FRAME,glass=GLASS,label='Paired upper glazing '+str(i+1))
        for part in builder.parts[before_window:]:
            if part['material']=='carved pale stone':
                part['material']=TRIM
        x1,z1,x2,_=opening.bounds
        front.box((x1+x2)/2,z1-.42,x2-x1-.26,.35,.10,.009,TRIM,'Window / projecting apron')
    for x in (-2.38,2.38):
        builder.lathe((x,-.80),[(0,.55),(.11,.55),(.14,.53),(.22,.54),(.29,.49),(.31,.45),(.40,.431),(4.80,.395),(4.89,.423),(4.99,.43)],WALL,24 if distant else 44,'Lower order / smooth shaft and base')
        front.box(x,5.12,1.01,.27,1.13,.65,TRIM,'Lower order / capital')
        for sign in (-1,1):
            loc=x+sign*.353
            front.prism(Polygon(profile_curve(loc,5.10,.16,.18,12 if distant else 28)),1.175,1.246,LIGHT,'Lower order / volute disc')
            scroll(front,loc,5.10,.126,sign,distant,1.247,TRIM,'Lower order / paired volutes')
        for z,width,thick,depth in [(5.32,1.19,.11,1.30),(5.44,1.14,.09,1.23),(6.03,.94,.99,1.15),(6.60,1.28,.16,1.25)]:
            front.box(x,z,width,thick,depth,depth/2,TRIM,'Lower order / upper neck and abacus')
        for t in range(6):
            front.box(x+(t-2.5)*.145,6.03,.044,.89,.080,1.185,WALL,'Lower order / die flutes')
    for side in (-1,1):
        x=side*3.05
        builder.lathe((x,-.105),[(0,.67),(.14,.67),(.20,.63),(.29,.64),(.40,.56)],TRIM,22 if distant else 42,'Large order / stepped base')
        fluted_shaft(builder,x,-.105,.39,12.18,.52,distant)
        builder.lathe((x,-.105),[(12.13,.51),(12.22,.55),(12.30,.535),(12.41,.54),(12.55,.58),(12.72,.655),(12.80,.67),(12.89,.66)],TRIM,24 if distant else 44,'Large order / round capital')
        for i in range(10):
            t=tau*i/10
            center=(x+.555*cos(t),-.105+.555*sin(t),12.44)
            builder.box(center,(.063,.06,.078),LIGHT,label='Large order / neck studs')
        front.box(x,13.04,1.13,.34,.54,.23,TRIM,'Large order / abacus')
    front.box(0,5.42,3.57,.66,.26,.27,TRIM,'Door / four-letter fascia')
    add_facade_lettering(front,'恆豐大樓',0,5.43,3.04,.409,.399,.457,COPPER,
        font=Path(__file__).with_name('HengfengSign.otf'),label='Door name')
    frieze(front,distant)
    for z,width,depth in [(13.24,.15,.27),(13.36,.10,.42),(13.47,.12,.51),(13.59,.12,.62)]:
        front.box(0,z,HALF*2,width,depth,depth/2,TRIM,'Upper cornice / stepped courses')
    for i in range(28):
        front.box((i-13.5)*.296,13.34,.147,.16,.45,.28,LIGHT,'Upper cornice / square dentils')
    for part in builder.parts:
        if part['material']==WALL:
            part['texcoords']=[wall_uv(*v) for v in part['vertices']]
