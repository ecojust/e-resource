"""Brick and pantile surrounds of the two openings at 63 Gao'an Road.

X runs across the opening, Y along the passage, Z up. Pass the outer surface of
each wall as y. The surrounding wall and the soffit inside the passage are
supplied by the caller. All dimensions below are in metres.
"""
from collections import defaultdict
from math import cos, pi, radians, sin

INNER = 2.05
SPRING = 1.45
OUTER = 2.917
CAP_LIMIT = radians(64)
CAP_TILES = 36
BRICKS = ('Burnished red arch brick', 'Muted russet arch brick', 'Deep red arch brick')
MORTAR = 'Silver grey lime joint'
STONE = 'Grey dressed pier base'
CLAY = 'Weathered pantile'
CLAY_END = 'Fired tile cut edge'
BED = 'Dark red eaves bed'

def _tone(rgb, roughness):
    rgb = [c / 255 for c in rgb]
    linear = [c / 12.92 if c <= .04045 else ((c + .055) / 1.055) ** 2.4 for c in rgb]
    return dict(color=linear, roughness=roughness, metallic=0.)

ARCH_PALETTE = {
    BRICKS[0]: _tone((153, 76, 61), .85), BRICKS[1]: _tone((137, 72, 60), .90),
    BRICKS[2]: _tone((126, 60, 49), .88), MORTAR: _tone((162, 151, 138), .95),
    STONE: _tone((153, 149, 135), .95), CLAY: _tone((163, 90, 67), .84),
    CLAY_END: _tone((133, 68, 50), .89), BED: _tone((92, 51, 41), .93),
}
# Radii, outward depth at the two sides of the course, nominal joint interval,
# and the fraction of a brick used to offset the next set of radial joints.
RINGS = (
    ('intrados', INNER, 2.135, .041, .046, 90, .00),
    ('inner roll', 2.135, 2.218, .073, .100, 90, .04),
    ('first rebate', 2.218, 2.309, .106, .134, 90, .05),
    ('deep soldier', 2.309, 2.654, .075, .078, 90, .05),
    ('outer roll', 2.654, 2.734, .119, .149, 90, .05),
    ('narrow cornice', 2.734, 2.802, .160, .178, 90, .05),
    ('outer headers', 2.802, OUTER, .078, .080, 52, .47),
)

class _Meshes:
    def __init__(self, builder, y, normal, face):
        self.builder, self.y, self.n, self.face = builder, y, normal, face
        self.mesh = defaultdict(lambda: ([], []))

    def add(self, name, mat, verts, faces):
        # Face lists are outward for the street-side model. The courtyard copy is mirrored.
        points, polygons = self.mesh[name, mat]
        offset = len(points)
        points.extend((x, self.y + self.n * d, z) for x, z, d in verts)
        for poly in faces:
            ordered = poly if self.n < 0 else reversed(poly)
            polygons.append(tuple(i + offset for i in ordered))

    def solid(self, name, mat, front, back):
        # Both rings are CCW in the projected X/Z plane as seen from the street.
        n = len(front)
        side = [(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
        self.add(name, mat, back + front, [tuple(reversed(range(n))),tuple(range(n,2*n))]+side)

    def flush(self):
        for (name, material), (verts, faces) in self.mesh.items():
            self.builder.add(verts, faces, material, self.face + ' / ' + name)

def _polar(angle, radius, depth):
    return radius * sin(angle), SPRING + radius * cos(angle), depth

def _zone(m, name, mat, a, b, inner, outer, left_depth, right_depth, back):
    near = [_polar(a,inner,left_depth),_polar(b,inner,left_depth),
            _polar(b,outer,right_depth),_polar(a,outer,right_depth)]
    m.solid(name, mat, near, [(x,z,back) for x,z,d in near])

def _rect(m, name, material, lo, hi, z0, z1, d0, d1, back):
    front = [(lo,z0,d0),(hi,z0,d1),(hi,z1,d1),(lo,z1,d0)]
    m.solid(name, material, front, [(x,z,back) for x,z,d in front])

def _shade(i, j):
    k = (i * 17 + j * 43 + (i // 3) * 7) % 19
    return BRICKS[1] if k in (3, 8, 15, 17) else BRICKS[2] if k in (2, 11) else BRICKS[0]

def _continuous_joint(m, name, ri, ro, di, do, segments):
    """One continuous bedding shell avoids internal radial faces between neighboring bricks."""
    vertices=[]
    faces=[]
    for i in range(segments+1):
        t=-pi/2+pi*i/segments
        vertices.extend([_polar(t,ri,di),_polar(t,ro,do),_polar(t,ri,-.003),_polar(t,ro,-.003)])
        if i:
            k=(i-1)*4
            faces.extend([(k,k+4,k+5,k+1),(k+2,k+3,k+7,k+6),
                          (k+1,k+5,k+7,k+3),(k+2,k+6,k+4,k)])
    k=segments*4
    faces.extend([(0,1,3,2),(k+2,k+3,k+1,k)])
    m.add(name+' joints',MORTAR,vertices,faces)

def _brick_rings(m,lod):
    for j,(name, ri, ro, di, do, count, phase) in enumerate(RINGS):
        pitch = pi / count
        # Each wedge is a separate disconnected solid within its editable course.
        # A continuous mortar surface sits behind the radial and concentric joints.
        _continuous_joint(m,name,ri,ro,di-.016,do-.016,54 if lod else 126)
        half_joint = .0043 / ((ri+ro)*.5)
        for i in range(-1,count):
            a = max(-pi/2,-pi/2+(i+phase)*pitch+half_joint)
            b = min(pi/2,-pi/2+(i+1+phase)*pitch-half_joint)
            if b-a > .002:
                _zone(m, name, _shade(i,j), a,b,ri+.0038,ro-.0038,di,do,min(di,do)-.023)

def _piers(m):
    plinth = .65 if m.n < 0 else .74
    height = (SPRING-plinth)/9
    for sign, side in ((-1,'left'),(1,'right')):
        def block(label, mat, x0, x1, z0, z1, d0, d1, back):
            a,c=sorted((sign*x0,sign*x1));ld,rd=(d0,d1) if sign>0 else (d1,d0)
            _rect(m, side+' '+label, mat, a,c,z0,z1,ld,rd,back)
        block('stone shoe',STONE,INNER,OUTER+.005,.010,plinth,.090,.132,-.008)
        for row in range(9):
            z0,z1=plinth+row*height,plinth+(row+1)*height
            end=OUTER+(.067 if row%2==0 else .012)
            # Run the mouldings down the jamb. Horizontal and staggered head joints
            # remain visible on the wider soldier belt and the row ends.
            for j,(name,ri,ro,di,do,_,_) in enumerate(RINGS):
                if j==len(RINGS)-1: ro=end
                block('bed joints',MORTAR,ri,ro,z0,z1,di-.015,do-.015,-.005)
                boundaries=[ri,ro]
                if ro-ri>.22:
                    cut=ri+(.105 if row%2 else .222)
                    if cut<ro-.035: boundaries.insert(1,cut)
                for part,(u,v) in enumerate(zip(boundaries,boundaries[1:])):
                    d0=di+(do-di)*(u-ri)/(ro-ri);d1=di+(do-di)*(v-ri)/(ro-ri)
                    block('bonded jamb',_shade(3*row+part,j),u+.0039,v-.0039,
                          z0+.0039,z1-.0039,d0,d1,min(d0,d1)-.023)

def _tile_profile(t):
    # A low channel and a rounded overlap, with a steeper lip on one side.
    angle=2*pi*t
    return .5 + .44*cos(angle) + .08*sin(angle) + .06*cos(2*angle)

def _pantiles(m,lod):
    # The front eave descends towards the viewer. Both photos show the ripple
    # continuing only to the shoulder, where it changes to a short level return.
    pitch=2*CAP_LIMIT/CAP_TILES
    for i in range(CAP_TILES*2):
        a=-CAP_LIMIT+i*pitch/2
        _zone(m,'clay bedding',BED,a,a+pitch/2,OUTER-.004,3.023,.041,.075,-.004)
    samples=6 if lod else 12
    def shell(label, point):
        # Four surfaces around a thin clay section, including the visible open-ended lip.
        rings=[]
        for j in range(samples+1):
            t=j/samples
            rings.append([point(t, .007, 3.143+.086*_tile_profile(t)),
                          point(t, .319, 3.017+.097*_tile_profile(t)),
                          point(t, .320, 2.992+.097*_tile_profile(t)),
                          point(t, .006, 3.118+.086*_tile_profile(t))])
        for j in range(samples):
            a,b=rings[j:j+2]
            m.add(label,CLAY,[a[0],a[1],b[1],b[0],a[3],b[3],b[2],a[2]],
                  [(0,1,2,3),(4,5,6,7)])
            m.add(label+' lips',CLAY_END,[a[1],b[1],b[2],a[2],a[0],a[3],b[3],b[0]],
                  [(0,3,2,1),(4,7,6,5)])
        m.add(label+' ends',CLAY_END,rings[0]+rings[-1],[(3,2,1,0),(4,5,6,7)])
    for i in range(CAP_TILES):
        a=-CAP_LIMIT+i*pitch
        def on_curve(t, d, r):
            return _polar(a+pitch*(.002+.996*t),r,d)
        shell('corrugated pantiles',on_curve)
    for sign in (-1,1):
        x=sign*3.018*sin(CAP_LIMIT);z=SPRING+3.018*cos(CAP_LIMIT)
        for j in range(2):
            def tail(t,d,r):
                f=t if sign>0 else 1-t
                return x+sign*(j+f)*.145,z+r-3.018,d
            shell('level tile ends',tail)
        a,c=sorted((x,x+sign*.282))
        _rect(m,'level eave brick',BRICKS[1],a,c,z-.105,z-.018,.130,.130,-.004)

def build_arch(b,lod,y,normal,face):
    """Build one complete surround; the caller owns the through opening and the wall."""
    if normal not in (-1,1):
        raise ValueError('The face normal must be -1 or +1.')
    m=_Meshes(b,y,normal,face)
    _brick_rings(m,lod)
    _piers(m)
    _pantiles(m,lod)
    m.flush()
