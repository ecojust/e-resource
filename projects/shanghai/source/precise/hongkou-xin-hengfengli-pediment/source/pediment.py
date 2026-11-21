"""The upper part of the gateway at Lane 85 as photographed in 2015."""
from math import cos, sin, pi, hypot

def linear(v):
    a=v/255.0
    return a/12.92 if a<=.04045 else ((a+.055)/1.055)**2.4

COLORS={'grained stone':(191,186,166),'shaded aggregate':(162,157,142),
        'light stone':(207,202,183),'edge in shade':(147,145,133),
        'ornament stone':(193,187,165),'letter face':(65,58,48)}
PALETTE={mat:{'color':[linear(k) for k in color],'roughness':.68 if mat=='letter face' else .91}
         for mat,color in COLORS.items()}

def slab(b,name,mat,outline,front,back):
    """Extrude one convex part of a moulding or escutcheon."""
    if sum(x*v-u*z for (x,z),(u,v) in zip(outline,outline[1:]+outline[:1]))<0:
        outline=list(reversed(outline))
    n=len(outline);verts=[(x,y,z) for y in (front,back) for x,z in outline]
    faces=[(0,i,i+1) for i in range(1,n-1)]+[(n,n+i+1,n+i) for i in range(1,n-1)]
    for i in range(n):
        j=(i+1)%n;faces.extend([(i,n+i,n+j),(i,n+j,j)])
    b.add(verts,faces,mat,name)

def box(b,name,mat,x0,x1,y0,y1,z0,z1):
    b.box(((x0+x1)/2,(y0+y1)/2,(z0+z1)/2),(x1-x0,y1-y0,z1-z0),mat,label=name)

def trim(b,name,mat,x0,z0,x1,z1,width,front,back):
    dx=x1-x0;dz=z1-z0;l=hypot(dx,dz);a=-dz*width/(2*l);v=dx*width/(2*l)
    slab(b,name,mat,[(x0+a,z0+v),(x0-a,z0-v),(x1-a,z1-v),(x1+a,z1+v)],front,back)

def architrave(b):
    box(b,'Deep horizontal lintel','grained stone',-2.36,2.36,-.015,.535,.10,1.27)
    for edge,x,depth,z0,z1,mat in [('Soffit bead',2.37,-.092,0,.081,'light stone'),
             ('Recess above soffit',2.35,-.042,.080,.148,'shaded aggregate'),
             ('Lower drip',2.38,-.087,.145,.196,'light stone'),
             ('Pediment lower bed',2.40,-.088,1.13,1.195,'light stone'),
             ('Shadow below cornice',2.39,-.104,1.19,1.233,'edge in shade'),
             ('Projecting pediment bed',2.44,-.157,1.23,1.299,'light stone')]:
        box(b,edge,mat,-x,x,depth,.55,z0,z1)
    slab(b,'Triangular stone tympanum','grained stone',[(-2.22,1.294),(2.22,1.294),(0,2.41)],-.018,.51)
    for side in (-1,1):
        for dx,dz,width,depth,mat,name in [(2.255,2.437,.093,-.127,'light stone','Upper raking cornice'),
              (2.16,2.358,.050,-.095,'shaded aggregate','Raking fascia'),
              (1.99,2.25,.036,-.075,'light stone','Inner raking moulding')]:
            trim(b,name,mat,side*dx,1.297,0,dz,width,depth,.515)
    # The short horizontal lines, offsets and diamonds are visible in the upright's two end panels.
    for side in (-1,1):
        xx=lambda x:side*x
        for (x0,z0),(x1,z1) in zip([(.99,1.01),(1.17,1.01),(1.32,.83),(1.65,.83)],[(1.17,1.01),(1.32,.83),(1.65,.83),(1.85,.83)]):
            trim(b,'Stepped fascia line','shaded aggregate',xx(x0),z0,xx(x1),z1,.014,-.037,-.009)
        for (x0,z0),(x1,z1) in zip([(1.81,.81),(2.06,.52),(2.29,.81),(2.06,1.08)],[(2.06,.52),(2.29,.81),(2.06,1.08),(1.81,.81)]):
            trim(b,'Incised lozenge line','shaded aggregate',xx(x0),z0,xx(x1),z1,.016,-.039,-.009)
    for z in (.33,.966):
        box(b,'Rectangular inscription surround','light stone',-1.13,1.13,-.045,-.009,z,z+.019)
    for x in (-1.126,1.126):
        box(b,'Tablet end edge','light stone',x-.009,x+.009,-.045,-.009,.345,.979)

# Stroke skeletons were drawn from the photographed relief. Coordinates are in the glyph cell.
STROKES={
'里': [[(.17,.88),(.18,.43),(.80,.43),(.82,.86),(.16,.88)],
       [(.21,.66),(.78,.66)],[(.50,.85),(.50,.115)],[(.15,.29),(.82,.30)],[(.02,.105),(.94,.12)]],
'豐': [[(.07,.67),(.07,.89)],[(.93,.69),(.93,.91)],[(.50,.68),(.50,.94)],
       [(.14,.82),(.43,.84)],[(.16,.74),(.40,.76)],[(.28,.68),(.28,.95)],
       [(.58,.84),(.86,.85)],[(.58,.75),(.86,.77)],[(.72,.68),(.72,.95)],
       [(.07,.67),(.93,.68)],[(.18,.55),(.83,.56)],
       [(.22,.45),(.23,.29),(.78,.29),(.79,.45),(.22,.45)],
       [(.31,.22),(.38,.105)],[(.72,.23),(.62,.10)],[(.10,.075),(.90,.085)]],
'恒': [[(.19,.08),(.19,.91)],[(.105,.73),(.04,.47)],[(.235,.72),(.31,.56)],
       [(.34,.83),(.94,.84)],[(.40,.68),(.41,.31),(.83,.31),(.84,.67),(.40,.68)],
       [(.43,.49),(.82,.49)],[(.30,.15),(.97,.17)]]}

def raised_line(b,name,mat,path,front,radius,far=False,taper=None):
    # Elliptical continuous sweep, with the base embedded in the substrate.
    sides=5 if far else 9;verts=[];faces=[]
    for i,(x,z) in enumerate(path):
        pre=path[max(0,i-1)];nxt=path[min(len(path)-1,i+1)]
        dx=nxt[0]-pre[0];dz=nxt[1]-pre[1];l=hypot(dx,dz) or 1
        radial=radius*(taper[i] if taper else 1)
        for j in range(sides):
            t=2*pi*j/sides
            verts.append((x-radial*dz/l*cos(t),front-radial*.70*sin(t),z+radial*dx/l*cos(t)))
    for i in range(len(path)-1):
        for k in range(sides):
            a=i*sides+k;c=i*sides+(k+1)%sides;faces.extend([(a,c,c+sides),(a,c+sides,a+sides)])
    for j in range(1,sides-1):faces.extend([(0,j+1,j),((len(path)-1)*sides,(len(path)-1)*sides+j,(len(path)-1)*sides+j+1)])
    b.add(verts,faces,mat,name)

def lettering(b,far):
    for name,cx,width in [('里',-.65,.40),('豐',0,.40),('恒',.65,.41)]:
        for path in STROKES[name]:
            placed=[(cx+(x-.5)*width,.444+z*.405) for x,z in path]
            raised_line(b,'Raised inscription '+name,'letter face',placed,-.054,.022,far)

def cubic(p0,p1,p2,p3,n):
    return [tuple((1-u)**3*a+3*(1-u)**2*u*b+3*(1-u)*u*u*c+u**3*d for a,b,c,d in zip(p0,p1,p2,p3)) for u in (i/n for i in range(n+1))]

def relief(b,far):
    # The oval shield has an unlettered face and a smaller stepped stone lip.
    shield=[(-.21,1.89),(0,1.962),(.21,1.89),(.197,1.72),(.117,1.59),(0,1.52),(-.117,1.59),(-.197,1.72)]
    slab(b,'Escutcheon perimeter','shaded aggregate',shield,-.116,-.015)
    slab(b,'Plain unlettered shield face','light stone',[(x*.80,1.757+(z-1.757)*.84) for x,z in shield],-.154,-.111)
    traces=[
      ((.08,1.55),(.18,1.53),(.29,1.68),(.25,1.72)),
      ((.18,1.53),(.47,1.51),(.58,1.68),(.55,1.76)),
      ((.25,1.55),(.39,1.78),(.48,1.84),(.51,1.76)),
      ((.43,1.58),(.55,1.67),(.68,1.62),(.66,1.57)),
      ((.49,1.52),(.61,1.52),(.68,1.42),(.62,1.40)),
      ((.36,1.47),(.43,1.31),(.54,1.41),(.50,1.45)),
      ((.16,1.47),(.22,1.36),(.32,1.37),(.35,1.44)),
      ((.49,1.54),(.62,1.49),(.76,1.36),(.87,1.53))]
    for sign in (-1,1):
        for i,control in enumerate(traces):
            pts=cubic(*control,7 if far else 17);path=[(sign*x,z) for x,z in pts];count=len(pts)
            taper=[.28+.83*sin(pi*j/(count-1))**.72 for j in range(count)]
            raised_line(b,'Scrolls beside escutcheon','ornament stone',path,-.094,.053 if i in (1,2,7) else .039,far,taper)
    for i in range(5):
        x=(i-2)*.048;z=1.952+.029*(2-abs(i-2));path=cubic((x*.3,1.91),(x*.65,1.976),(x,z+.058),(x*1.28,z+.094),6 if far else 12)
        raised_line(b,'Foliate crest above shield','light stone',path,-.086,.027,far)
    small=[(-.075,1.51),(0,1.46),(.075,1.51),(0,1.40)]
    slab(b,'Leaf tip beneath shield','ornament stone',small,-.098,-.014)

def add_building(builder,lod=False):
    architrave(builder);lettering(builder,lod);relief(builder,lod)
