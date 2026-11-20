"""Bund 16, viewed in 2014 from the east and Jiujiang Road. Dimensions in metres."""
from math import cos, pi, sin
from pathlib import Path
import numpy as np
from shapely import union_all
from shapely.affinity import translate
from shapely.geometry import box, Polygon, Point
from photo_architecture import Facade
from sign_lettering import lettering_shapes

WIDTH = 18.11
LENGTH = 39.71
SKEW = -0.11189
PLINTH = 1.52
ORDER = 14.55
UPPER = 19.50
TOP = 23.60
FONT = Path(__file__).parent / 'fonts/BundSixteenSign.otf'
PALETTE = {name: {'color': color, 'roughness': roughness} for name, color, roughness in [
    ('silver grey granite', [.536,.543,.539], .90), ('sheltered stone', [.461,.472,.470], .91),
    ('honed bases', [.500,.515,.516], .80), ('pale carved stone', [.655,.654,.633], .86),
    ('limestone cornice', [.623,.625,.608], .87), ('mortar', [.431,.439,.427], .99),
    ('cut section', [.485,.484,.460], .97), ('dull roof flashing', [.329,.338,.321], .88),
    ('pressed dark frames', [.126,.138,.133], .69), ('green-grey glass', [.223,.274,.280], .32),
    ('bronze door', [.116,.104,.083], .67), ('smoked door panel',[.087,.098,.094],.62), ('polished brass', [.676,.529,.262], .48),
    ('dark sign backing', [.243,.242,.209],.79)]}
PALETTE['polished brass']['metallic'] = .37

def recessed_window(f,u,z,w,h,holes,lod,label,mullions=2):
    shape=box(u-w/2,z,u+w/2,z+h)
    holes.append(shape)
    edge=shape.difference(shape.buffer(-.072,join_style=2))
    bars=[box(u-w/2+w*j/mullions-.03,z,u-w/2+w*j/mullions+.03,z+h)
          for j in range(1,mullions)]
    for v in ((.68,) if lod else (.66,.81)):
        bars.append(box(u-w/2,z+h*v-.021,u+w/2,z+h*v+.021))
    f.prism(shape,-.305,-.285,'green-grey glass',label+'/glass')
    f.prism(edge.union(union_all(bars)),-.227,-.167,'pressed dark frames',label+'/sashes')
    f.box(u,z-.056,w+.19,.11,.23,-.008,'limestone cornice',label+'/stone sill')

def sign(f,text,u,z,width,height,d,lod):
    for i,(char,g) in enumerate(lettering_shapes(text,width,height,font=FONT)):
        p=translate(g.simplify(.0015 if lod else .0005),xoff=u,yoff=z)
        f.prism(p,d,d+.043,'polished brass',f'2014 gilded letters/{i:02d} {char}')

def bank_mark(f,u,z,r,d,lod):
    outline=Point(u,z).buffer(r,quad_segs=10 if lod else 20)
    ring=outline.difference(outline.buffer(-r*.105))
    mountain=Polygon([(u-.83*r,z-.40*r),(u-.15*r,z+.70*r),(u+.21*r,z+.04*r),
                      (u+.35*r,z+.31*r),(u+.78*r,z-.40*r),(u+.39*r,z-.40*r),
                      (u+.18*r,z-.05*r),(u-.05*r,z-.39*r),(u-.31*r,z+.03*r),(u-.56*r,z-.40*r)])
    f.prism(ring.union(mountain),d,d+.065,'polished brass','2014 circular bank mark with twin peaks')

def joints(f,stone,lod):
    if lod:return
    low,z0,high,z1=stone.bounds
    h=.635
    for i in range(int((z1-z0)/h)+1):
        z=z0+i*h
        g=stone.intersection(box(low,z,high,z+.014))
        if g.area>.005:f.prism(g,.002,.009,'mortar','ashlar bed joints')
        for j in range(int((high-low)/1.64)+2):
            x=low+(j+(i%2)*.5)*1.64
            g=stone.intersection(box(x,z+.018,x+.012,z+h-.01))
            if g.area>.002:f.prism(g,.002,.009,'mortar','staggered fine joints')

def wall(f,z0,z1,holes,material,lod,outline=None):
    area=f.wall(z0,z1,holes,.42,material,outline)
    joints(f,area,lod)

def profile(f,levels,label):
    for z,h,depth,mat in levels:
        f.box(0,z,f.length,h,depth+.34,(depth-.34)/2,mat,label)

def upper(f,centers,side,lod):
    holes=[]
    for u in centers:
        for z,h in [(15.50,2.65),(20.22,2.47)]:
            wide=2.04 if abs(u)<.02 and not side else 1.62
            if side:
                # Deep tripartite office window, with two narrow sidelights.
                for dx,w in [(-1.27,.58),(0,1.53),(1.27,.58)]:
                    recessed_window(f,u+dx,z,w,h,holes,lod,'upper three-part window',2 if dx==0 else 1)
            else:recessed_window(f,u,z,wide,h,holes,lod,'upper east casements',3 if wide>2 else 2)
    roof=[(-f.length/2,TOP),(f.length/2,TOP)] if side else [
        (f.length*t/12,TOP+.45*(1+cos(t*pi/6))/2) for t in range(-6,7)]
    shell=Polygon([(-f.length/2,ORDER),(f.length/2,ORDER),*reversed(roof)])
    wall(f,ORDER,TOP,holes,'silver grey granite',lod,shell)
    profile(f,[(UPPER-.50,.13,.26,'limestone cornice'),(UPPER-.22,.19,.37,'limestone cornice'),
               (UPPER+.09,.20,.61,'pale carved stone'),(UPPER+.26,.115,.47,'limestone cornice')],'projecting upper cornice')
    n=round(f.length/.32)
    for j in range(n):f.box((j+.5)*f.length/n-f.length/2,UPPER-.086,.139,.19,.206,.19,'pale carved stone','individual cornice dentils')
    for offset,h,d,mat in [(-.27,.115,.13,'limestone cornice'),(-.05,.17,.21,'pale carved stone')]:
        poly=Polygon([(x,z+offset-h/2) for x,z in roof]+[(x,z+offset+h/2) for x,z in reversed(roof)])
        f.prism(poly,-.29,d,mat,'shallow parapet coping')

def round_order(f,u,lod):
    center=f.point(u,0,-.87)[:2]
    radius=.732
    b=f.builder
    b.lathe(center,[(PLINTH,.96),(1.71,.96),(1.78,.80),(1.84,.85),(1.98,.85),
                    (2.07,.72),(2.17,.70),(5.0,radius),(9.8,.702),(13.10,.624),
                    (13.27,.644),(13.30,.715),(13.42,.72)],'silver grey granite',18 if lod else 38,
                    'Bund colonnade/round shafts with entasis')
    for z,r in [(1.80,.85),(2.04,.765),(13.02,.645),(13.36,.745)]:
        b.lathe(center,[(z-.039,r-.038),(z-.014,r),(z+.014,r),(z+.044,r-.045)],
                'pale carved stone',18 if lod else 32,'Bund colonnade/column neckings')
    count=10 if lod else 18
    for j in range(count):
        a=2*pi*j/count
        wallpoint=lambda v,r,z:(center[0]+cos(a)*r-sin(a)*v,center[1]+sin(a)*r+cos(a)*v,z)
        verts=[wallpoint(0,.71,13.27),wallpoint(-.092,.72,13.48),wallpoint(0,.767,13.61),wallpoint(.092,.72,13.48),wallpoint(0,.805,13.47)]
        b.add(verts,[(0,1,4),(1,2,4),(2,3,4),(3,0,4)],'pale carved stone','Bund colonnade/carved leaf collar')
    capital(f,u,-.87,1.63,lod)

def capital(f,u,d,w,lod):
    for z,h,ww,dep in [(13.55,.28,w*.88,w*.82),(13.76,.24,w,w*.98),(13.98,.18,w*1.17,w*1.08)]:
        f.box(u,z,ww,h,dep,d,'limestone cornice','geometric capitals and abaci')
    # Geometric fret panels at the two outside corners of each capital.
    for k in (-1,1):
        x=u+k*w*.385
        fret=Polygon([(x-.23,13.94),(x+.23,13.94),(x+.23,13.61),(x-.12,13.61),
                      (x-.12,13.83),(x+.10,13.83),(x+.10,13.75),(x-.032,13.75),
                      (x-.032,13.69),(x+.143,13.69),(x+.143,13.87),(x-.23,13.87)])
        f.prism(fret,d+w*.49,d+w*.49+.057,'pale carved stone','rectilinear fret relief')

def stone_door(f,lod):
    shape=box(-1.38,.52,1.38,5.72)
    f.prism(shape,-.53,-.49,'bronze door','recessed double entrance')
    for u in (-.67,.67):
        pane=box(u-.49,1.51,u+.49,5.45);f.prism(pane,-.465,-.427,'smoked door panel','entry glazing')
        f.box(u,.99,1.22,.57,.054,-.451,'bronze door','lower door panels')
    f.box(0,3.1,.079,5.04,.077,-.407,'bronze door','central door stile')
    for u in [-1.51,1.51]:f.box(u,3.22,.23,5.55,.36,.055,'limestone cornice','pilastered portal jambs')
    for z,w,h,d in [(5.97,3.40,.36,.34),(6.29,3.65,.29,.43),(6.51,3.85,.15,.53)]:
        f.box(0,z,w,h,d,.087,'pale carved stone','stepped portal lintel')
    return shape

def low_back(f,centers,east,lod):
    holes=[]
    for i,u in enumerate(centers):
        central=east and i==len(centers)//2
        if central:holes.append(stone_door(f,lod))
        else:recessed_window(f,u,2.20,2.23 if east else 2.02,4.86,holes,lod,'lower office glazing')
        recessed_window(f,u,10.8,2.29 if east else 2.08,2.52,holes,lod,'clerestory glazing')
    wall(f,0,ORDER,holes,'sheltered stone',lod)
    for z,h,depth,mat in [(PLINTH-.18,.21,.14,'honed bases'),(PLINTH+.004,.12,.21,'pale carved stone')]:
        if east:
            for side in (-1,1):
                left,right = 1.64,f.length/2
                f.box(side*(left+right)/2,z,right-left,h,depth+.34,(depth-.34)/2,mat,'interrupted entry base')
        else:
            profile(f,[(z,h,depth,mat)],'lower stone band')

def strip(f,lod,side=False):
    H=f.length/2
    depth=1.95 if not side else 1.22
    # Inner street-facing wall is set behind the colonnade and holds real window openings.
    rear=Facade(f.builder,f.point(-H,0,-depth)[:2],f.point(H,0,-depth)[:2],f.label+'/recess')
    if side:
        edge=2.06;step=(f.length-2*edge)/7
        centers=[(j-3)*step for j in range(7)]
    else:centers=[-5.04,0,5.04]
    low_back(rear,centers,not side,lod)
    for u in (-H+.38,H-.38):f.box(u,ORDER/2,.76,ORDER,depth,-depth/2,'silver grey granite','end return stones')
    if side:
        for j in range(6):
            u=(j-2.5)*step
            for z,h,w,deep in [(PLINTH/2,PLINTH,1.60,1.46),(PLINTH+.14,.28,1.66,1.42),(7.40,11.56,1.28,1.19),(13.28,.25,1.41,1.32)]:
                f.box(u,z,w,h,deep,-.67,'silver grey granite','six square order piers')
            capital(f,u,-.67,1.53,lod)
        # Ashlar dado visible along Jiujiang Road, uninterrupted under the side windows.
        f.box(0,PLINTH/2,f.length,PLINTH,depth,-depth/2,'honed bases','continuous street plinth')
        profile(f,[(PLINTH-.15,.13,.12,'limestone cornice'),(PLINTH+.017,.1,.16,'pale carved stone')],'dado coping')
        u=H-1.19
        f.box(u,7.32,2.28,14.55,1.45,-.71,'silver grey granite','Bund corner sign pier')
        f.box(u,8.83,1.92,8.83,.12,.037,'pale carved stone','inset sign field')
        bank_mark(f,u,11.97,.74,.107,lod)
        for j,ch in enumerate('招商银行'):sign(f,ch,u,10.31-j*1.38,.88,.99,.105,lod)
    else:
        for u in [-7.56,-2.52,2.52,7.56]:
            f.box(u,PLINTH/2,1.95,PLINTH,1.95,-.88,'honed bases','four square column plinths')
            round_order(f,u,lod)
        for k in (-1,1):
            edge,outer=1.88,H-.05
            u=k*(edge+outer)/2
            f.box(u,PLINTH/2,outer-edge,PLINTH,1.91,-1.03,'honed bases','continuous plinth beside steps')
            f.box(u,PLINTH-.02,outer-edge,.10,1.98,-.995,'limestone cornice','slab on entrance plinth')
        for i in range(4):f.box(0,.07*(i+1),3.35,.14*(i+1),.35,-.75-i*.32,'honed bases','four recessed entrance steps')
        sign(f,'CHINA MERCHANTS BANK',0,14.51,13.15,.51,.213,lod)
        sign(f,'招商银行',0,20.66,12.23,1.15,.171,lod)
        bank_mark(f,0,22.84,.73,.078,lod)
    profile(f,[(14.18,.20,.17,'limestone cornice'),(14.55,.58,.18,'silver grey granite'),
               (14.88,.12,.32,'pale carved stone'),(15.00,.10,.23,'limestone cornice')],'colonnade entablature')
    upper(f,centers,side,lod)
    for z,w,h in [(14.11,depth+.3,.28),(TOP-.23,depth+.46,.25)]:
        f.box(0,z,f.length,h,w,-(w-.30)/2,'cut section' if z<15 else 'dull roof flashing','section soffit and roof ledge')
    # Close section ends and back only within the documented narrow street strip.
    f.box(0,(TOP+ORDER)/2,f.length,TOP-ORDER,.10,-depth-.43,'cut section','neutral upper cut')
    for u in (-H+.027,H-.027):f.box(u,(TOP+ORDER)/2,.054,TOP-ORDER,depth+.43,-(depth+.43)/2,'cut section','neutral upper end')

def bank(b,lod):
    east=Facade(b,(-WIDTH/2,0),(WIDTH/2,0),'East Bund')
    side=Facade(b,(-WIDTH/2+SKEW*LENGTH,LENGTH),(-WIDTH/2,0),'South Jiujiang')
    strip(east,lod)
    strip(side,lod,True)
    corner=np.array([-WIDTH/2,0.0])
    # Continue each moulding around the convex intersection of the two exterior planes.
    # Its two straight runs stop at their endpoints; the fourth point is the miter.
    normals=np.stack([east.n[:2],side.n[:2]])
    corner_point=np.linalg.solve(normals,np.ones(2))
    for z,h,d,mat in [(14.18,.20,.17,'limestone cornice'),(14.55,.58,.18,'silver grey granite'),
                      (14.88,.12,.32,'pale carved stone'),(15,.10,.23,'limestone cornice'),
                      (UPPER-.50,.13,.26,'limestone cornice'),(UPPER-.22,.19,.37,'limestone cornice'),
                      (UPPER+.09,.20,.61,'pale carved stone'),(UPPER+.26,.115,.47,'limestone cornice'),
                      (TOP-.27,.115,.13,'limestone cornice'),(TOP-.05,.17,.21,'pale carved stone')]:
        area=Polygon([corner,corner+east.n[:2]*d,corner+corner_point*d,corner+side.n[:2]*d])
        b.plan_prism(area,z-h/2,z+h/2,mat,'Stone courses/mitered street corner')
