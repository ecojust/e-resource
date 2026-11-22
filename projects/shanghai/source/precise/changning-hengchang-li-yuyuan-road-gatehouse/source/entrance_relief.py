"""Model the later street entrance from the surveyed floral relief and open gates."""
from math import cos, pi, sin
from pathlib import Path

import numpy as np
from shapely import affinity
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union

from sign_lettering import lettering_shapes


def _paint(rgb, roughness, metallic=0):
    values = [v / 255 for v in rgb]
    return {"color": [v / 12.92 if v < .04045 else ((v + .055) / 1.055) ** 2.4 for v in values],
            "roughness": roughness, "metallic": metallic}


FIELD = "Hengchang portal | cast reddish field"
CARVE = "Hengchang portal | raised russet foliage"
CROWN = "Hengchang portal | cornice arris"
PANEL = "Hengchang portal | grey bronze tablet"
TEXT = "Hengchang portal | raised bronze characters"
IRON = "Hengchang portal | dark iron"
PALETTE = {
    FIELD: _paint((159, 99, 71), .83), CARVE: _paint((182, 122, 85), .76),
    CROWN: _paint((168, 105, 72), .8), PANEL: _paint((144, 150, 139), .70, .18),
    TEXT: _paint((156, 102, 67), .58, .33), IRON: _paint((51, 49, 47), .62, .38),
}

# Cubic control points traced on the private rectified photograph. The full panel
# has two sprays whose footstalks cross below the central empty oval.
STEMS = {
    'crossed stalk': ((392,231), (346,211,308,180,277,165), (247,149,214,146,179,155),
                      (145,163,117,185,84,195)),
    'ascending stalk': ((340,202), (321,186,300,163,285,149), (270,130,265,112,272,100),
                        (279,89,290,87,301,89)),
    'upright volute': ((286,153), (278,126,282,103,294,96), (309,90,319,93,324,101)),
    'large lower scroll': ((279,165),(250,148,216,146,191,158),(175,168,174,186,184,201),
                            (196,218,223,227,249,216),(257,212,261,207,260,202)),
    'outward undercurl': ((187,157),(166,165,172,185,158,208),(148,224,134,226,126,221),
                           (119,215,119,207,124,205)),
    'outer upper scroll': ((187,156),(164,171,135,164,132,149),(126,132,139,121,153,122),
                            (166,122,169,131,162,136)),
    'inner feather': ((323,188),(312,175,301,155,298,136),(298,121,304,109,319,112)),
    'upper inward spiral': ((303,96),(313,84,329,81,331,69),(332,58,349,54,354,63),
                             (360,72,350,80,345,74),(342,71,343,68,346,68)),
    'lower inward scroll': ((356,210),(343,202,337,196,328,197),(317,198,317,206,323,208),
                             (329,211,332,208,333,205)),
}

# Each midrib starts on a recorded stem. A leaf has a pointed outline and a
# pitched median ridge, with both margins returning to the casting bed.
LEAVES = (
    ((86,194),(65,185),(51,194),5), ((100,188),(80,176),(65,183),6),
    ((108,185),(105,162),(86,170),7), ((120,179),(120,155),(108,159),6),
    ((124,176),(107,188),(86,187),6), ((137,163),(130,139),(145,136),7),
    ((148,134),(167,135),(171,122),6), ((140,123),(151,110),(170,112),5),
    ((158,115),(165,109),(184,103),5), ((187,155),(199,139),(215,140),7),
    ((203,150),(212,126),(193,131),7), ((221,151),(219,136),(243,140),5),
    ((249,154),(239,126),(220,120),9), ((270,153),(250,113),(215,106),9),
    ((265,131),(240,94),(210,93),8), ((254,112),(245,86),(231,85),7),
    ((276,129),(272,109),(291,103),6), ((286,107),(292,81),(315,84),7),
    ((270,102),(263,85),(284,76),6), ((279,83),(292,79),(310,69),5),
    ((295,83),(305,61),(321,63),5), ((303,147),(313,125),(325,127),7),
    ((314,166),(318,147),(324,146),6), ((324,178),(335,173),(339,184),6),
    ((156,213),(163,226),(158,237),7), ((170,194),(166,218),(172,239),8),
    ((174,204),(181,217),(182,236),7), ((129,222),(112,222),(97,232),6),
    ((132,224),(114,235),(90,236),5), ((250,215),(266,204),(279,205),7),
    ((244,223),(256,220),(272,235),5), ((246,200),(260,181),(274,188),6),
    ((276,186),(292,178),(303,185),6),
)


def _bezier(control, steps):
    p = np.asarray(control[0], float)
    points = [p]
    for row in control[1:]:
        a, b, end = np.asarray(row, float).reshape(3, 2)
        for t in np.linspace(0, 1, steps + 1)[1:]:
            points.append((1-t)**3*p + 3*(1-t)**2*t*a + 3*(1-t)*t*t*b + t**3*end)
        p = end
    return points


def _ridged_leaf(builder, world, spec, material, label, lod, base=.067, lift=.042):
    start, middle, tip, width = spec
    a, b, c = (np.asarray(v, float) for v in (start, middle, tip))
    steps = 5 if lod else 9
    rim, ridge = [], []
    for i in range(steps + 1):
        t = i/steps
        center = (1-t)**2*a + 2*t*(1-t)*b + t*t*c
        direction = (1-t)*(b-a)+t*(c-b)
        normal = np.array([-direction[1], direction[0]]) / np.linalg.norm(direction)
        w = width * sin(pi*t)**.76 * (1.14-.30*t)
        if i in (0, steps):
            rim.append([world(center, base)])
        else:
            rim.append([world(center + normal*w, base), world(center-normal*w, base)])
            ridge.append(world(center,base+lift*sin(pi*t)**.68))
    perimeter = [rim[0][0], *[r[0] for r in rim[1:-1]], rim[-1][0],
                 *[r[1] for r in reversed(rim[1:-1])]]
    n = len(perimeter)
    bottom = [np.asarray(v)+[0,.022,0] for v in perimeter]
    verts = [*perimeter, *bottom, *ridge]
    faces = []
    for i in range(n):
        j=(i+1)%n
        faces.append((i,j,n+j,n+i))
    # Left and right edges are paired by equal parameter, bounding a strip.
    def row(i):
        if i == 0: return [0]
        if i == steps: return [steps]
        return [i, 2*n+i-1, n-i]
    for i in range(steps):
        one,two=row(i),row(i+1)
        if len(one)==1:
            faces.extend([(one[0],two[0],two[1]),(one[0],two[1],two[2])])
        elif len(two)==1:
            faces.extend([(one[0],two[0],one[1]),(one[1],two[0],one[2])])
        else:
            faces.extend([(one[0],two[0],two[1],one[1]),(one[1],two[1],two[2],one[2])])
        edge1=[one[0],one[-1]];edge2=[two[0],two[-1]]
        face=[edge1[0],edge1[1],edge2[1],edge2[0]]
        faces.append(tuple(n+j for j in dict.fromkeys(face)))
    # The reflected spray reverses handedness. Orient every surface consistently.
    for i in range(n):
        faces[i]=tuple(reversed(faces[i]))
    verts=np.asarray(verts)
    volume=sum(np.dot(verts[f[0]], np.cross(verts[f[k]],verts[f[k+1]]))
               for f in faces for k in range(1,len(f)-1))
    if volume<0: faces=[tuple(reversed(f)) for f in faces]
    builder.add(verts,faces,material,label)


def _arc(left,right,base,top,n):
    # Circular segment from measured span and sagitta.
    cx=(left+right)/2
    rise=top-base
    radius=((right-left)**2/4+rise**2)/(2*rise)
    return [(x,top-radius+max(0,radius**2-(x-cx)**2)**.5)
            for x in np.linspace(left,right,n)]


def _gates(b,lod,p):
    width=p['right']-p['left']
    length=(width-.12)/2
    z0=p.get('bottom',0)+.055
    h=(p['head']-z0)*.565
    for end, name, angle in ((p['left']+.065,'west',86.),(p['right']-.065,'east',88.)):
        sign=1 if name=='west' else -1
        run=np.array([sign*cos(angle*pi/180),sin(angle*pi/180)])
        normal=np.array([run[1],-run[0]])
        def at(s,z,d=0):
            xy=[end,.20]+s*run+d*normal
            return (xy[0],xy[1],z0+z)
        def line(points,r):
            return LineString(points).buffer(r,cap_style=2,join_style=2)
        top=lambda s:h+.09*cos(pi*s/length)
        rails=[line([(0,0),(length,0)],.027),line([(0,0),(0,top(0))],.028),
               line([(length,0),(length,top(length))],.028)]
        ss=np.linspace(0,length,12)
        rails.append(line([(s,top(s)) for s in ss],.029))
        for z in (.20,.36,.47,h-.32):
            rails.append(line([(0,z),(length,z)],.018))
        for s in np.linspace(0,length,7)[1:-1]:
            rails.append(line([(s,0),(s,.21)],.013))
        for k in range(4):
            center=length*(k+.5)/4
            half=length*.105
            for side in (-1,1):
                # Long pointed loops form the two open ranks of ironwork.
                for lo,hi in ((.48,h*.55),(h*.55,h-.33)):
                    zmid=(lo+hi)/2
                    path=[(center,lo),(center+side*.36*half,lo+.11),
                          (center+side*half,zmid),(center+side*.65*half,hi-.12),(center,hi)]
                    rails.append(line(path,.014))
            for z in (.39,h-.23):
                ts=np.linspace(0,pi*1.78,14 if lod else 24)
                curl=[(center+.13*(1-.63*t/ts[-1])*cos(t),z+.084*(1-.63*t/ts[-1])*sin(t)) for t in ts]
                rails.append(line(curl,.012))
        b.prism(unary_union(rails),-.018,.018,at,IRON,'later gate | '+name+' leaf welded grille')
        for z in (.31,h-.32):
            a=at(0,z-.055);c=at(0,z+.055)
            b.tube([a,c],.042,IRON,sides=6 if lod else 10,label='later gate | '+name+' hinge')


def add_relief(b,lod,layout):
    """Add the later portal. X increases east, Y north into the open passage."""
    year=str(layout.get('period','2022'))[:4]
    if year.isdigit() and int(year)<2022:
        return
    p=layout['portal']
    width=p['width'];head=p['head']
    cy=layout.get('front_y',{}).get('tower',0)
    # Survey grid derives from the rectified district photograph, not an image texture.
    def xz(x,y):
        return (p.get('origin',0)+(x-8.5)*width/535., head+(222.5-.013*(x-8.5)-y)*width/488.)
    def depth(x,z,d):
        return (x,cy-d,z)
    def front(poly,back,face,mat,name):
        b.prism(poly,back,face,depth,mat,'later portal | '+name)
    def rect(x0,y0,x1,y1):
        return Polygon([xz(x0,y0),xz(x1,y0),xz(x1,y1),xz(x0,y1)])
    # Both ledge returns are lower than the arched moulding. Its segment rises
    # smoothly from the two ends and has a separate recessed inner field.
    xl,zbase=xz(31,185);xr,_=xz(533,178.5);_,ztop=xz(278,64.5)
    curve=_arc(xl,xr,zbase,ztop,34 if lod else 67)
    zfoot=head+.012
    front(Polygon([(xl,zfoot),(xr,zfoot),*reversed(curve)]),-.015,.054,FIELD,'pediment body')
    for i,(inset,w,back,face) in enumerate(((0,.083,.049,.101),(.102,.053,.050,.121),(.171,.031,.052,.096))):
        arc=_arc(xl+inset,xr-inset,zbase+.008,ztop-inset,34 if lod else 67)
        path=LineString(arc).buffer(w/2,cap_style=2,join_style=1)
        front(path,back,face,CROWN,'arched moulding '+str(i+1))
    for side,a,c in (('west',-2,113),('east',463,549)):
        for i,(y0,y1,back,face,extra) in enumerate(((184,190,0,.252,1.5),(190,199,0,.217,0),
                                                   (199,207,0,.173,-2),(207,217,0,.136,-4))):
            drop=.014*(a-5)
            front(rect(a-extra,y0-drop,c+extra,y1-drop),back,face,CROWN,side+' cornice '+str(i+1))
    # Use the common foliage detail grid for the two sprays and the empty boss.
    def world(q,d,mirror=False):
        u,v=q
        if mirror: u=740-u
        x,z=xz(50+u/1.626,63+v/1.626)
        return (x,cy-d,z)
    for mirrored,name in ((False,'left'),(True,'right')):
        def transform(q,dep):
            return world(q,dep,mirrored)
        for key,path in STEMS.items():
            raise_by=.076 if key=='crossed stalk' else .067
            pts=[transform(q,raise_by) for q in _bezier(path,5 if lod else 9)]
            b.tube(pts,.023 if key=='crossed stalk' else .015,CARVE,sides=6 if lod else 9,
                   label='later portal | '+name+' '+key)
        for i,spec in enumerate(LEAVES):
            _ridged_leaf(b,transform,spec,CARVE,name+' foliage '+str(i+1),lod)
        for i in range(5):
            angle=2*pi*i/5
            start=np.array([212.,188.])
            direction=np.array([cos(angle),sin(angle)])
            _ridged_leaf(b,transform,(start,start+9*direction,start+18*direction,6.4),
                         CARVE,name+' rosette petal '+str(i+1),lod,.069,.047)
    cx,_,cz=world((370,139),.05)
    oval=affinity.scale(Point(cx,cz).buffer(1,quad_segs=11 if lod else 20),
                        xfact=.241,yfact=.341,origin=(cx,cz))
    # A shallow convex face and a flat back form the unlettered medallion.
    n=24 if lod else 48
    rings=[(.241,.341,.050),(.241,.341,.097),(.219,.311,.113),(.143,.207,.134)]
    verts=[(cx+rx*cos(i*2*pi/n),cy-d,cz+rz*sin(i*2*pi/n))
           for rx,rz,d in rings for i in range(n)]
    verts.append((cx,cy-.143,cz))
    faces=[tuple(reversed(range(n)))]
    for row in range(len(rings)-1):
        a=row*n
        for i in range(n):
            j=(i+1)%n
            faces.append((a+i,a+j,a+j+n,a+i+n))
    faces.extend((3*n+i,3*n+(i+1)%n,4*n) for i in range(n))
    b.add(verts,faces,FIELD,'later portal | unlettered central oval')
    front(oval.boundary.buffer(.016),.092,.125,CARVE,'oval raised rim')
    # In the oblique photograph the recessed grey field has a visible red reveal.
    # The upper and lower horizontal string courses run through the full facade.
    for k,(y0,y1,back,face) in enumerate(((-71,-63,.002,.147),(-63,-57,.002,.098),
                                           (35,44,.0,.152),(44,55,.0,.108),(55,62,.0,.070))):
        front(rect(7,y0,544,y1-13),back,face,CROWN,'tablet string course '+str(k+1))
    outer=rect(151,-59,401,36);inner=rect(160,-49,391,26)
    front(outer.difference(inner),-.008,.165,CROWN,'tablet moulded surround')
    front(inner,-.013,.015,PANEL,'recessed bronze tablet')
    tx,tz=xz(274,-9)
    for char,shape in lettering_shapes('里昌亨',1.69,.326,font=Path(__file__).with_name('entrance-name.otf')):
        front(affinity.translate(shape,xoff=tx,yoff=tz),.014,.040,TEXT,'tablet character '+char)
    _gates(b,lod,p)
