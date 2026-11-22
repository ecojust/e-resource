"""Four tapered legs, arch portals, square beam rings and the exposed bracing."""
import math

from shapely.geometry import Polygon, box

MASONRY = 'Weathered cast concrete'
BORDER = 'Darker cement casting'
LIP = 'Worn cornice edge'
IRON = 'Iron diagonal stays'
PATINA = 'Inset moulding shadow'
ARCH, MIDDLE, GALLERY, CAB, EAVE = 9.173, 16.704, 24.063, 29.154, 33.294
FOOT_HALF = 7.200
TAPER = (FOOT_HALF - 2.111) / EAVE
SIDES = ('street', 'courtyard east', 'rear', 'courtyard west')


def half(z):
    return FOOT_HALF - TAPER * z


def face(side, u, z, d=0):
    """Face-local horizontal distance and outward depth; positive u × z points outward."""
    h = half(z) + d
    return ((u, -h, z), (h, u, z), (-u, h, z), (-h, -u, z))[side]


def skin(builder, side, polygon, back, front, mat, label):
    builder.prism(polygon, back, front, lambda u, z, d: face(side, u, z, d), mat, SIDES[side] + '/' + label)


def leg_width(z):
    return 1.12 - .0160 * z


def sloping_pier(b, sx, sy):
    levels = (.02, ARCH, MIDDLE, GALLERY, CAB, EAVE - .13)
    cross = [(0,.055), (.055,0), (.945,0), (1,.055),
             (1,.945), (.945,1), (.055,1), (0,.945)]
    vertices = []
    for z in levels:
        h, width = half(z), leg_width(z)
        for a, c in cross:
            vertices.append((sx * (h - a * width), sy * (h - c * width), z))
    n = len(cross)
    surfaces = [tuple(reversed(range(n))), tuple(range(len(vertices) - n, len(vertices)))]
    for row in range(len(levels)-1):
        for i in range(n):
            j = (i+1)%n
            surfaces.append((row*n+i, row*n+j, (row+1)*n+j, (row+1)*n+i))
    if sx*sy<0:
        surfaces = [tuple(reversed(f)) for f in surfaces]
    b.add(vertices, surfaces, MASONRY, 'four tapered piers/chamfered legs')


def beam_ring(b, bottom, top, width, depth, material, name):
    h = half((bottom+top)/2)+depth
    outer = box(-h,-h,h,h)
    inside = box(-h+width,-h+width,h-width,h-width)
    b.plan_prism(outer.difference(inside),bottom,top,material,name)


def arch_profile(width, spring, rise, segments):
    # A single void crosses the whole casting. The street and courtyard stay joined.
    stations = [(width*math.cos(t*math.pi/segments),spring+rise*math.sin(t*math.pi/segments))
                for t in range(segments+1)]
    return Polygon([(-width,-.05),(width,-.05),*stations])


def portal(b, side, lod):
    # Inner faces terminate against the beveled corner posts, which carry the load to grade.
    opening = arch_profile(5.74,1.14,6.49,18 if lod else 44)
    front = Polygon([(-half(0)+.41,0),(half(0)-.41,0),
                     (half(ARCH)-.38,ARCH),(-half(ARCH)+.38,ARCH)])
    skin(b,side,front.difference(opening),-.76,-.012,MASONRY,'deep ground arch')
    shoulder = opening.buffer(.38,quad_segs=6).difference(opening).intersection(front)
    skin(b,side,shoulder,-.012,.046,LIP,'cast archivolt')
    # The feet have long sunk panels and a raised surround below their springing.
    for direction in (-1,1):
        center=direction*(half(1.60)-.63)
        surround=box(center-.27,.28,center+.27,2.86)
        inset=surround.buffer(-.050,join_style=2)
        skin(b,side,surround.difference(inset),.007,.063,BORDER,'rectangular panel on lower footing')
    for step in range(1,18,1 if not lod else 2):
        angle=step*math.pi/18
        u=5.93*math.cos(angle); z=1.14+6.72*math.sin(angle)
        tangent=(-5.93*math.sin(angle),6.72*math.cos(angle))
        length=math.hypot(*tangent); ux,uz=tangent[0]/length,tangent[1]/length
        nx,nz=uz,-ux
        segments=5 if lod else 9
        # Small paired curves follow the springing of the arch in the close-up photograph.
        pts=[face(side,u+ux*t*.22+nx*(1-t*t)*.075,
                  z+uz*t*.22+nz*(1-t*t)*.075,.054) for t in [i*2/segments-1 for i in range(segments+1)]]
        b.tube(pts,.028,BORDER,5 if lod else 7,SIDES[side]+'/arch cast leaf')
        if not lod and 1 < step < 17:
            pts=[face(side,u+ux*t*.19+nx*(.19-(1-t*t)*.080),
                      z+uz*t*.19+nz*(.19-(1-t*t)*.080),.050)
                 for t in [i*2/segments-1 for i in range(segments+1)]]
            b.tube(pts,.022,BORDER,6,SIDES[side]+'/paired arch leaf edge')


def oval_band(b,side,z,depth,lod):
    margin=leg_width(z)*.76
    extent=half(z)-margin
    repeats=max(5,round(2*extent/.91))
    count=repeats*(5 if lod else 11)
    for sign in (-1,1):
        pts=[]
        for i in range(count+1):
            u=-extent+2*extent*i/count
            elevation=z+sign*.153*math.sin(math.pi*repeats*i/count)
            pts.append(face(side,u,elevation,depth))
        b.tube(pts,.022 if lod else .027,BORDER,5 if lod else 7,SIDES[side]+'/interlaced beam relief')


def braces(b,side,lod):
    for floor,ceiling in ((ARCH,MIDDLE),(MIDDLE,GALLERY),(GALLERY,CAB)):
        z0=floor+.13; z1=ceiling-.98
        for sign in (-1,1):
            u0=sign*(half(z0)-leg_width(z0)*.72)
            u1=-sign*(half(z1)-leg_width(z1)*.72)
            depth=-.25 if sign<0 else -.34
            b.tube([face(side,u0,z0,depth),face(side,u1,z1,depth)],.032 if lod else .041,IRON,6 if lod else 8,SIDES[side]+'/crossed iron stays')
            if not lod:
                for u,z in ((u0,z0),(u1,z1)):
                    skin(b,side,box(u-.075,z-.10,u+.075,z+.10),depth-.025,depth+.025,IRON,'stay anchor shoe')


def build_frame(b,lod):
    for sx in (-1,1):
        for sy in (-1,1):sloping_pier(b,sx,sy)
    for side in range(4):
        portal(b,side,lod)
        braces(b,side,lod)
    for top in (ARCH,MIDDLE,GALLERY,CAB):
        beam_ring(b,top-.83,top-.09,.63,.014,MASONRY,'four levels/cast beam web')
        beam_ring(b,top-.12,top+.018,.73,.115,LIP,'four levels/projecting belt cap')
        beam_ring(b,top-.86,top-.77,.62,.049,BORDER,'four levels/beam undersill')
        for side in range(4):oval_band(b,side,top-.47,.082,lod)
