"""Surviving moulded brick arch at the former Li residence, Kangding East Road 85."""
import math


def pigment(rgb, roughness=.85):
    def linear(value):
        return value / 3294.6 if value <= 10 else ((value / 255 + .055) / 1.055) ** 2.4
    return {'color': [linear(c) for c in rgb], 'roughness': roughness}


PALETTE = {name: pigment(rgb) for name, rgb in {
    'grey mortar': (149, 131, 117), 'umber brick': (138, 90, 77),
    'russet brick': (155, 99, 81), 'fired rose brick': (164, 111, 91),
    'red moulded brick': (150, 100, 86), 'dark clay': (112, 76, 68),
    'burnished relief': (175, 125, 107), 'weathered terracotta': (167, 112, 93)
}.items()}
BRICK = ('umber brick', 'russet brick', 'fired rose brick', 'russet brick')


def plane(u, v, depth):
    """Full 600×400 photograph; level springing removes the coarse camera roll."""
    return ((u - 300) * .0107, depth, 1.05 + (242 + (u - 300) * .043 - v) * .0115)


def course(t, radius, depth):
    """Interpolate the two photographed soffit and outer curves including their different rises."""
    a = math.pi * t
    inner_u = 303 - 145 * math.cos(a)
    outer_u = 302 - 221 * math.cos(a)
    inner_v = 247 + (inner_u - 303) * .042 - 52 * math.sin(a)
    outer_v = 236.5 + (outer_u - 302) * .037 - 108.5 * math.sin(a)
    return plane(inner_u + (outer_u - inner_u) * radius,
                 inner_v + (outer_v - inner_v) * radius, depth)


def band(builder, begin, end, inner, outer, front, back, material, name, parts=3):
    if end <= begin:
        return
    vertices = []
    faces = []
    for i in range(parts + 1):
        t = begin + (end - begin) * i / parts
        vertices.extend([course(t,inner,front), course(t,outer,front),
                         course(t,outer,back), course(t,inner,back)])
        if i:
            j = 4 * (i - 1)
            for k in range(4):
                faces.append((j + k, j + (k + 1) % 4, j + (k + 1) % 4 + 4, j + k + 4))
    faces.extend([(3,2,1,0),tuple(range(parts*4,parts*4+4))])
    builder.add(vertices, faces, material, name)


def stone(builder, x0, x1, z0, z1, front, back, material, name):
    vertices = [(x,y,z) for z in (z0,z1) for y in (front,back) for x in (x0,x1)]
    faces = [(0,2,3,1),(4,5,7,6),(0,1,5,4),(2,6,7,3),(0,4,6,2),(1,3,7,5)]
    builder.add(vertices,faces,material,name)


def add_building(builder, lod=False):
    segments = 60 if not lod else 36
    band(builder,0,1,0,1,.044,.37,'grey mortar','arched brick backing and exposed soffit',segments)
    for i in range(segments):
        for course_no,r0,r1,shift,front in [
                (0,.004,.142,.40,-.012),(1,.151,.292,0,-.011),
                (2,.299,.458,.44,-.013),(3,.844,.898,.50,-.009),(4,.907,.978,.02,-.011)]:
            l = max(0, (i + shift + .046) / segments)
            r = min(1, (i + 1 + shift - .046) / segments)
            if r <= l:
                continue
            material=BRICK[(i*7+course_no)%len(BRICK)]
            if i in (12,42,51) and course_no in (0,2):
                material='charred brick' if i==42 else 'ochre-fired brick'
            band(builder,l,r,r0,r1,front,.047,material,
                 f'brick arch course {course_no} voussoir {i+1:02}',2 if not lod else 1)
    for r0,r1,front,mat,name in [
        (.464,.492,-.040,'burnished relief','raised inner moulding'),
        (.495,.815,.008,'red moulded brick','carved foliage band'),
        (.516,.538,-.020,'dark clay','inner narrow lip'),
        (.796,.821,-.026,'burnished relief','outer narrow lip'),
        (.983,1.0,-.027,'weathered terracotta','outer brick pencil course')]:
        band(builder,0,1,r0,r1,front,.054,mat,name,segments)
    flowers = 16
    for k in range(flowers):
        left=k/flowers
        width=1/flowers
        n = 20 if not lod else 13
        spiral=[]
        mirrored = 1 if k<8 else -1
        for j in range(n):
            turn=j/(n-1)
            angle=.20+turn*math.pi*2.22
            rad=1-.88*turn
            t=left+width*(.50+mirrored*.41*rad*math.cos(angle))
            r=.666+.124*rad*math.sin(angle)
            spiral.append(course(t,r,-.027))
        builder.tube(spiral,.016 if not lod else .018,'burnished relief',7 if not lod else 5,f'clay scroll {k+1:02}')
        route=[(.01,.70),(.15,.73),(.30,.740),(.55,.710),(.78,.625),(.99,.598)]
        if mirrored<0: route=[(1-u,v) for u,v in route]
        builder.tube([course(left+width*u,r,-.024) for u,r in route],.010,'weathered terracotta',6,f'connecting stem {k+1:02}')
        for leaf,(u0,r0,u1,r1) in enumerate([(.03,.596,.29,.630),(.43,.768,.62,.723),(.76,.588,.94,.618)]):
            if mirrored<0: u0,u1=1-u0,1-u1
            pts=[course(left+width*u0,r0,-.011),course(left+width*(u0*.48+u1*.52),r0*.48+r1*.52+.029,-.017),course(left+width*u1,r1,-.013),course(left+width*(u0*.48+u1*.52),r0*.48+r1*.52-.025,-.014),course(left+width*(u0*.48+u1*.52),r0*.48+r1*.52,-.056)]
            builder.add(pts,[(0,1,4),(1,2,4),(2,3,4),(3,0,4),(0,3,2,1)],'weathered terracotta',f'scroll {k+1:02} floral leaf {leaf+1}')
    for side,sign in [('left',-1),('right',1)]:
        centre = sign*2.21
        stone(builder,centre-.64,centre+.64,-.65,.69,.052,.64,'grey mortar',side+' pier core')
        for j in range(12 if not lod else 9):
            count=12 if not lod else 9
            height=1.34/count
            x=centre-.64
            k=0
            while x < centre+.637:
                width=min(.45*(.5 if k==0 and j%2 else 1),centre+.64-x)
                if width>.02:
                    stone(builder,x+.008,x+width-.008,-.65+(j+.06)*height,-.65+(j+.95)*height,
                          .022,.058,BRICK[(j+2*k)%4],f'{side} pier row {j+1:02} brick {k+1}')
                x+=width;k+=1
        for z0,z1,width,front,mat,name in [
            (.68,.73,.69,-.02,'weathered terracotta','pier neck'),
            (.72,.79,.76,-.082,'burnished relief','lower moulding'),
            (.77,1.13,.76,-.105,'red moulded brick','leaf block'),
            (1.12,1.18,.79,-.15,'weathered terracotta','capital abacus')]:
            stone(builder,centre-width,centre+width,z0,z1,front,.64,mat,side+' '+name)
        for leaf_index in range(5):
            x=centre+(leaf_index-2)*.277
            for flip in (-1,1):
                for j in range(3):
                    u=(j+1)/3
                    start=(x,-.114,.792)
                    mid=(x+flip*(.014+.044*u),-.142-.018*u,.830+.086*u)
                    tip=(x+flip*(.038+.090*u),-.143,.877+.190*u)
                    eye=(mid[0],-.205,mid[2]+.027)
                    half=.016+.016*u
                    shape=[start,(mid[0]-half,-.12,mid[2]),tip,(mid[0]+half,-.12,mid[2]),eye]
                    builder.add(shape,[(0,1,4),(1,2,4),(2,3,4),(3,0,4),(0,3,2,1)],'weathered terracotta',
                                f'{side} capital carved acanthus {leaf_index+1} rib {j+1} {flip}')
            pts=[(x,-.13,.80),(x+.008,-.165,.875),(x+.020,-.207,.984),(x+.024,-.203,1.047)]
            builder.tube(pts,.025,'burnished relief',7,f'{side} capital stem {leaf_index+1}')
            mould=[(x+.018+.055*math.cos(t),-.170-.025*math.sin(t),1.035+.058*math.sin(t)) for t in [i*.25 for i in range(25)]]
            builder.tube(mould,.019,'burnished relief',6,f'{side} upper rolled bud {leaf_index+1}')
    add_spandrel(builder, lod)


def add_spandrel(builder, lod):
    """Fill the masonry above the surviving arch, following its outer curve."""
    cuts = 84 if not lod else 48
    lo, hi = -2.96, 2.93
    def bottom(x):
        u = x / .0107 + 300
        if 81 <= u <= 523:
            t = math.acos(max(-1, min(1, (302-u)/221))) / math.pi
            return course(t, 1., 0)[2] + .002
        return 1.16
    top = 2.93
    for k in range(cuts):
        l, r = lo + (hi-lo)*k/cuts, lo + (hi-lo)*(k+1)/cuts
        verts = [(x,y,z) for y in (.081,.48) for x,z in [(l,bottom(l)),(r,bottom(r)),(r,top),(l,top)]]
        faces=[(0,1,2,3),(7,6,5,4),(0,4,5,1),(2,6,7,3)]
        if k==0:faces.append((3,7,4,0))
        if k==cuts-1:faces.append((1,5,6,2))
        builder.add(verts,faces,'grey mortar','spandrel masonry backing')
    colors=['stone grey brick','grey violet brick','deep grey brick']
    rows=15 if not lod else 10
    height=(top-1.16)/rows
    for j in range(rows):
        z=1.16+j*height; upper=z+height-.009
        l=lo
        for k in range(22):
            if l>=hi-.02: break
            r=min(l+(.411 if j%2==0 or k else .202),hi)
            left, right=l+.006,r-.006
            l=r
            # Subdivide cut bricks near the soffit. No brick face crosses the opening.
            for s in range(2):
                x0=left+(right-left)*s/2; x1=left+(right-left)*(s+1)/2
                zl,zr=max(z+.005,bottom(x0)+.008),max(z+.005,bottom(x1)+.008)
                if max(zl,zr)>=upper: continue
                material='aged red header' if j in (4,5) else colors[(j*5+k*3+j//3+k//4)%3]
                verts=[(x,y,h) for y in (.058,.088) for x,h in [(x0,zl),(x1,zr),(x1,upper),(x0,upper)]]
                builder.add(verts,[(0,1,2,3),(7,6,5,4),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)],
                            material,f'spandrel row {j+1} brick {k+1}')


PALETTE.update({name:pigment(rgb) for name,rgb in {
    'stone grey brick':(115,108,104),'grey violet brick':(120,110,108),
    'deep grey brick':(102,98,96),'aged red header':(150,111,102),'charred brick':(93,79,78),'ochre-fired brick':(184,120,80)}.items()})
