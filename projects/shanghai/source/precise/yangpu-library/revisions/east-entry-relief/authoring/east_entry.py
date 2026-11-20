"""Photo-observed outer east entrance. Dimensions in the existing façade u,z frame."""
import math
from shapely import affinity
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union

STONE='stone carved'
DOOR='old red door'
METAL='brass'


def sample_cubics(start, segments, steps=8):
    points=[start]
    for a,b,end in segments:
        x,y=points[-1]
        for i in range(1,steps+1):
            t=i/steps;s=1-t
            points.append((s**3*x+3*s*s*t*a[0]+3*s*t*t*b[0]+t**3*end[0],
                           s**3*y+3*s*s*t*a[1]+3*s*t*t*b[1]+t**3*end[1]))
    return points


def ribbon(points,width):
    return LineString(points).buffer(width/2,quad_segs=3)


def contour(f,c,points,depth,width,material,name):
    if material==STONE:
        raised=[f.point(c+x,z,depth[1]-width*.29) for x,z in points]
        f.builder.tube(raised,width*.55,material,7,f.label+'/'+name)
    else:
        f.prism(affinity.translate(ribbon(points,width),xoff=c),depth[0],depth[1],material,name)


def shell(c,rx,rz,spring,bottom,n):
    pts=[(c-rx,bottom),(c+rx,bottom)]
    for i in range(n+1):
        angle=math.pi*i/n
        pts.append((c+rx*math.cos(angle),spring+rz*math.sin(angle)))
    return Polygon(pts)


def upper_lattice(c,opening,lod):
    """Punch triangular scalloped lights in the two leaf plates."""
    top=opening.buffer(-.11).intersection(box(c-1.22,1.46,c+1.22,3.48))
    grate=[]
    for side in [-1,1]:
        area=top.intersection(box(c+.085 if side>0 else c-1.24,1.46,c+1.24 if side>0 else c-.085,3.50))
        lights=[]
        for col in range(3):
            u0=c+side*(.09+col*.355);u1=u0+side*.355
            for row in range(7):
                z=1.43+row*.361+(col%2)*.1805
                step=.1805 if col%2==0 else -.1805
                a=(u0,z);b=(u1,z+step);d=(u0,z+.361);e=(u1,z+step+.361)
                cells=([a,b,d],[b,e,d]) if step>0 else ([a,b,e],[a,e,d])
                for corners in cells:
                    poly=Polygon(corners)
                    inner=poly.buffer(-.025,join_style=2)
                    if inner.is_empty:continue
                    mid=inner.centroid;pts=list(inner.exterior.coords)[:-1]
                    # Three round lobes follow the floral holes visible within the
                    # triangular webs; their shared centre remains open through the plate.
                    circles=[]
                    for x,y in pts:
                        pos=(mid.x+(x-mid.x)*.53,mid.y+(y-mid.y)*.53)
                        circles.append(Point(pos).buffer(.057,quad_segs=3 if lod else 6))
                    cut=unary_union([inner.buffer(-.016),*circles]).intersection(inner)
                    lights.append(cut)
        grate.append(area.difference(unary_union(lights)))
    return unary_union(grate)


def stonework(f,c,door,lod):
    spring=2.22;n=24 if lod else 48
    inner=shell(c,1.47,1.46,spring,1.29,n)
    outer=shell(c,2.15,1.82,spring,1.29,n)
    jamb=shell(c,1.51,1.46,spring,.10,n).difference(door)
    f.prism(jamb,-.035,.17,STONE,'arched-entrance/profiled-door-jamb')
    f.prism(outer.difference(inner),.006,.104,'entrance stone recess','arched-entrance/carved-arch-band')
    rim=outer.difference(outer.buffer(-.046)).union(inner.buffer(.043).difference(inner)).intersection(outer.difference(inner))
    f.prism(rim,.101,.137,STONE,'arched-entrance/reeded-arch-edges')
    for theta in [8,48,90,132,172]:
        a=math.radians(theta);x=1.83*math.cos(a);z=spring+1.65*math.sin(a)
        for j in range(8):
            t=math.tau*j/8
            pts=[(x+(.122+.035*math.cos(8*v))*math.cos(v),z+(.122+.035*math.cos(8*v))*math.sin(v)) for v in [t+math.tau*k/(8*6)for k in range(7)]]
            contour(f,c,pts,(.105,.139),.030,STONE,'arched-entrance/flower-petals')
            if not lod:
                radial=[(x+.043*math.cos(t),z+.043*math.sin(t)),
                        (x+.114*math.cos(t+.18),z+.114*math.sin(t+.18))]
                contour(f,c,radial,(.105,.135),.021,STONE,'arched-entrance/flower-centres')
        rose=Point(x,z).buffer(.037,quad_segs=7)
        f.prism(affinity.translate(rose,xoff=c),.105,.139,STONE,'arched-entrance/flower-rosettes')
    for sign in [-1,1]:
        # Vine segments pass between raised rosettes in the radial band.
        for begin,end in [(9,47),(49,89)]:
            pts=[]
            for j in range(35 if not lod else 19):
                t=j/(34 if not lod else 18);a=math.radians(begin+(end-begin)*t)
                r=.080*math.sin(math.tau*t)
                pts.append((sign*(1.82+r)*math.cos(a),spring+(1.63+r)*math.sin(a)))
            contour(f,c,pts,(.105,.138),.031,STONE,'arched-entrance/arch-scroll')
        # Small curled leaves branch from the two vine runs around the
        # larger flower bosses, as visible on both sides of the arch.
        for theta,flip in [(19,1),(31,-1),(59,1),(72,-1)]:
            a=math.radians(theta)
            tangent=(-math.sin(a),math.cos(a));radial=(math.cos(a),math.sin(a))
            curve=sample_cubics((-.11,0),[((-.035,.015),(.055,.139),(.135,.118)),
                ((.228,.101),(.240,-.016),(.164,-.035)),((.113,-.041),(.101,.011),(.146,.018))],4 if lod else 7)
            pts=[]
            for t,r in curve:
                pts.append((sign*(1.82*math.cos(a)+t*tangent[0]+flip*r*radial[0]),
                            spring+1.63*math.sin(a)+t*tangent[1]+flip*r*radial[1]))
            contour(f,c,pts,(.105,.139),.025,STONE,'arched-entrance/foliate-arch-spirals')
        for z in [1.44,1.77,2.04]:
            pts=sample_cubics((1.62,z),[((1.67,z+.14),(1.95,z+.20),(1.94,z+.06)),
                         ((1.92,z-.038),(1.73,z-.03),(1.80,z+.056))],5 if lod else 8)
            contour(f,c,[(sign*x,y)for x,y in pts],(.105,.14),.032,STONE,'arched-entrance/jamb-scroll')
        start,end=1.43,3.00
        f.prism(box(c+min(sign*start,sign*end),.54,c+max(sign*start,sign*end),.99),.01,.085,'entrance stone recess','arched-entrance/side-frieze')
        for z in [.57,.958]:
            contour(f,c,[(sign*start,z),(sign*end,z)],(.083,.127),.043,STONE,'arched-entrance/frieze-edges')
        for j in range(3):
            x=1.47+j*.49;pts=sample_cubics((x,.76),[((x+.10,.58),(x+.33,.59),(x+.42,.76)),
                ((x+.53,.93),(x+.22,.93),(x+.21,.80)),((x+.20,.72),(x+.31,.72),(x+.31,.779))],5 if lod else 9)
            contour(f,c,[(sign*u,v)for u,v in pts],(.084,.127),.032,STONE,'arched-entrance/frieze-cloud')


def add_entry(model,f,c,door):
    lod=model.lod
    stonework(f,c,door,lod)
    opening=door.buffer(-.022)
    # Deep dark glass is visible through the open metalwork. The lower leaf
    # panels are opaque; their frame, mouldings and pulls sit farther forward.
    f.prism(opening,-.31,-.283,'glass grey','arched-entrance/glass')
    outer=opening.buffer(-.083);margin=opening.difference(outer)
    center=box(c-.083,.10,c+.083,3.55)
    lower=box(c-1.30,.10,c+1.30,1.46)
    frame=unary_union([margin,opening.intersection(center),opening.intersection(lower)])
    f.prism(frame,-.26,-.116,DOOR,'arched-entrance/frame')
    f.prism(upper_lattice(c,door,lod),-.211,-.109,DOOR,'arched-entrance/pierced-floral-lights')
    for side in [-1,1]:
        mid=side*.65
        for lo,hi in [(.55,1.075),(1.105,1.34)]:
            size=.97 if hi<1.09 else .93;outer=box(c+mid-size/2,lo,c+mid+size/2,hi)
            f.prism(outer.difference(outer.buffer(-.032)), -.116,-.055,DOOR,'arched-entrance/raised-leaf-mouldings')
        # Cloud-shaped escutcheon mirrored from the measured outline of each panel.
        half=sample_cubics((0,.895),[((.09,.817),(.24,.779),(.342,.845)),
                   ((.396,.770),(.415,.687),(.418,.599)),((.415,.514),(.291,.505),(.184,.51)),
                   ((.135,.533),(.129,.651),(.200,.67)),((.090,.64),(.04,.704),(0,.750))],5 if lod else 10)
        for reflect in [-1,1]:
            contour(f,c,[(mid+reflect*x,z+.135)for x,z in half],(-.113,-.060),.023,METAL,'arched-entrance/cloud-panel-motif')
        plaque=box(c+mid-.43,1.158,c+mid+.43,1.309).buffer(.027,join_style=3)
        f.prism(plaque.difference(plaque.buffer(-.018)), -.116,-.061,METAL,'arched-entrance/upper-panel-border')
        u=c+side*.069
        f.prism(box(u-.025,1.12,u+.025,1.61),-.11,-.039,METAL,'arched-entrance/pull-backplate')
        f.line((u,1.21,-.047),(u,1.51,.021),.021,METAL,6 if lod else 10,'arched-entrance/handle')
    model.mark('real_glazed_opening',f.label+'/arched-entrance',face_origin_enu=f.center.tolist(),
        tangent_enu=f.t.tolist(),outward_enu=f.n.tolist(),polygon_uz=list(door.exterior.coords),
        wall_depth_m=[-.42,0],glass_depth_m=[-.31,-.283])
