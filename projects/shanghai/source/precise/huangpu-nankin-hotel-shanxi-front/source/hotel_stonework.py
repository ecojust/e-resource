"""Model in metres along the west wall. The street is the positive Y side."""
from math import cos, hypot, pi, sin
from shapely.geometry import box as rectangle
from shapely.ops import unary_union

STONE = 'Warm ivory stucco'
TRIM = 'Light dressed projecting bands'
REVEAL = 'Warm grey recessed surrounds'
FRAME = 'Dark painted sash'
GLASS = 'Shaded upper glazing'
SHOP_GLASS = 'Street glazing'
METAL = 'Graphite balcony iron'
SILL = 'Limestone sill'
PLINTH = 'Grey stone shop base'
PALETTE = {k: {'color': c, 'roughness': r} for k,c,r in [
    (STONE,[.757,.715,.605],.90), (TRIM,[.842,.799,.687],.86),
    (REVEAL,[.541,.514,.448],.90), (FRAME,[.185,.171,.140],.54),
    (GLASS,[.294,.315,.297],.33), (SHOP_GLASS,[.166,.213,.202],.32),
    (METAL,[.108,.116,.111],.52), (SILL,[.710,.684,.590],.87),
    (PLINTH,[.398,.405,.389],.85)]}

class Frontage:
    def __init__(self, builder):
        self.builder = builder

    def box(self, name, material, x0, x1, y0, y1, z0, z1):
        assert x1 > x0 and y1 > y0 and z1 > z0, name
        self.builder.box(((x0+x1)/2,(y0+y1)/2,(z0+z1)/2),
                         (x1-x0,y1-y0,z1-z0),material,label=name)

    def mesh(self, name, material, vertices, faces):
        self.builder.add(vertices,faces,material,name)

    def punched_wall(self, name, limits, openings, back, face, material=STONE):
        left,bottom,right,top = limits
        wall = rectangle(left,bottom,right,top)
        holes = unary_union([rectangle(*o) for o in openings])
        wall = wall.difference(holes)
        self.builder.prism(wall,-face,-back,lambda x,z,d:(x,-d,z),material,name)

    def slab(self, name, material, outline, low, high):
        from shapely.geometry import Polygon
        self.builder.prism(Polygon(outline),low,high,lambda x,y,z:(x,y,z),material,name)

    def bars(self, name, paths, edge, material=METAL):
        """Give every railing strand a rectangular cross section normal to the guard."""
        vertices,faces = [],[]
        for points in paths:
            for a,b in zip(points,points[1:]):
                dx,dy,dz = (b[j]-a[j] for j in range(3))
                length = hypot(hypot(dx,dy),dz)
                if length < 1e-7:
                    continue
                along = (dx/length,dy/length,dz/length)
                flat = hypot(dx,dy)
                side = (-dy/flat,dx/flat,0) if flat > 1e-7 else (0,1,0)
                ax,ay,az = along
                sx,sy,sz = side
                up = (ay*sz-az*sy,az*sx-ax*sz,ax*sy-ay*sx)
                start = len(vertices)
                for center in (a,b):
                    for u,v in ((-1,-1),(1,-1),(1,1),(-1,1)):
                        vertices.append(tuple(center[j]+.5*edge*(u*side[j]+v*up[j]) for j in range(3)))
                for face in ((0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)):
                    faces.append(tuple(start+i for i in face))
        self.mesh(name,material,vertices,faces)

def sash(front, name, opening, face, detailed=True, glass=GLASS):
    x0,z0,x1,z1 = opening
    glass_front = face-.145
    front.box(name+' glass',glass,x0,x1,glass_front-.035,glass_front,z0,z1)
    w = x1-x0
    t = .048 if detailed else .065
    anchor = face-.08
    paths = [[(x0,anchor,z0),(x1,anchor,z0),(x1,anchor,z1),(x0,anchor,z1),(x0,anchor,z0)]]
    for x in ([x0+w*.5] if w < 1.85 else [x0+w/3,x0+2*w/3]):
        paths.append([(x,anchor,z0),(x,anchor,z1)])
    if detailed:
        transom = z1-(z1-z0)*.29
        paths.append([(x0,anchor,transom),(x1,anchor,transom)])
    front.bars(name+' sash',paths,t,FRAME)

def balcony(front, name, center, width, level, face, depth, shoulder, masonry_top, iron_top, detailed):
    half = width/2
    flank = shoulder
    points = [(center-half,face-.035),(center+half,face-.035),
              (center+half,face+flank),(center,face+depth),(center-half,face+flank)]
    front.slab(name+' deck',STONE,points,level-.20,level)
    nose = [(center+(x-center)*1.026,face+(y-face)*1.045) for x,y in points]
    front.slab(name+' nose',TRIM,nose,level-.16,level-.10)
    # Photographs show an opaque lower guard, then an open patterned iron strip.
    edge = [points[1],points[2],points[3],points[4],points[0]]
    paths = []
    for a,b in zip(edge,edge[1:]):
        dx,dy = b[0]-a[0],b[1]-a[1]
        length = hypot(dx,dy)
        normal = (-dy/length*.07,dx/length*.07)
        ring = [a,b,(b[0]+normal[0],b[1]+normal[1]),(a[0]+normal[0],a[1]+normal[1])]
        front.slab(name+' parapet',STONE,ring,level-.005,masonry_top)
        def point(t,z):
            height=masonry_top+(iron_top-masonry_top)*(z-.50)/.46
            return (a[0]+dx*t,a[1]+dy*t,height)
        paths.extend([[point(0,h),point(1,h)] for h in (.50,.57,.84,.96)])
        cells = max(1,round(length/.40))
        for j in range(cells):
            left,right = j/cells,(j+1)/cells
            mid=(left+right)/2
            paths.append([point(left,.50),point(left,.96)])
            paths.append([point(left,.57),point(mid,.84),point(right,.57)])
            if detailed:
                paths.append([point(left,.84),point(mid,.57),point(right,.84)])
                paths.append([point(mid+(right-left)*.27*cos(k*pi/4),.705+.088*sin(k*pi/4)) for k in range(9)])
    front.bars(name+' iron',paths,.028 if detailed else .040)
