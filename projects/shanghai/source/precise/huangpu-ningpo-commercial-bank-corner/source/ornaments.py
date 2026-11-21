"""Carved details of the Beijing Road / Jiangxi Road corner as photographed in 2014."""
from math import asin, cos, pi, sin, tau

from shapely.geometry import Polygon, box
from shapely.ops import unary_union


def ellipse_shape(cx, cz, rx, rz, lod):
    """Clear masonry opening in the vertical X/Z plane, matching the glazing."""
    steps = 32 if lod else 72
    return Polygon([(cx + rx * cos(tau * i / steps), cz + rz * sin(tau * i / steps))
                    for i in range(steps)])


def _oculus(b, lod, wall_y, z, rx, rz, m):
    shape = ellipse_shape(0, z, rx, rz, lod)
    def prism(outline, near, far, material, name):
        b.prism(outline, near, far, lambda x, h, d: (x, wall_y - d, h), m[material], name)

    prism(shape, -.248, -.224, 'glass', 'Oculus / inset glass')
    inner = ellipse_shape(0, z, rx - .054, rz - .061, lod)
    bars = [box(x - .017, z-rz, x + .017, z+rz) for x in (-rx*.38, rx*.38)]
    bars.extend(box(-rx, z+dy-.020, rx, z+dy+.020) for dy in (-rz*.29, rz*.23))
    frame = shape.difference(inner).union(unary_union(bars).intersection(shape))
    prism(frame, -.211, -.145, 'metal', 'Oculus / sash and glazing bars')
    for width, low, high in ((.16, -.018, .059), (.115, .044, .099)):
        prism(ellipse_shape(0, z, rx+width, rz+width, lod).difference(shape),
              low, high, 'trim', 'Oculus / continuous rim')

    # The original oval has a relief ring and a separate tapered top key.
    count = 22
    for i in range(count):
        t = tau * i / count
        if abs(t - pi/2) < .21:
            continue
        cx, cz = (rx+.086)*cos(t), z+(rz+.086)*sin(t)
        norm = (cos(t)/rx, sin(t)/rz)
        length = (norm[0]**2 + norm[1]**2)**.5
        nx, nz = norm[0]/length, norm[1]/length
        def point(s, n, d):
            return (cx - s*nz + n*nx, wall_y-d, cz + s*nx + n*nz)
        b.add([point(-.083,-.026,.089), point(-.011,-.047,.096),
               point(.085,.021,.094), point(.003,.053,.095),
               point(.002,.011,.132)],
              [(4,1,0),(4,2,1),(4,3,2),(4,0,3),(0,1,2,3)],
              m['trim'], 'Oculus / wreath relief')
    key = Polygon([(-.072,z+rz-.010),(.072,z+rz-.010),
                   (.13,z+rz+.31),(-.13,z+rz+.31)])
    prism(key, -.010, .155, 'trim', 'Oculus / crown key')


def _capital(b, lod, x, y, r, top, m):
    base = top - .64
    rings = [(0,1.00),(.040,1.03),(.069,1.12),(.103,1.12),(.125,1.03),
             (.21,1.06),(.30,1.17),(.40,1.29),(.48,1.31),(.506,1.34)]
    b.lathe((x,y), [(base+h,r*rad) for h,rad in rings],
            m['stone'], 16 if lod else 32, 'Upper capital / neck and bell')

    # The photograph shows two small scroll faces below the square abacus.
    for side in (-1,1):
        cx, cz = x+side*r*.89, base+.34
        scroll_radius = r*.45
        steps = 12 if lod else 26
        disc = ellipse_shape(cx, cz, scroll_radius, scroll_radius*.92, lod)
        b.prism(disc, r*.76, r*1.065, lambda u,h,d:(u,y-d,h),
                m['stone'], 'Upper capital / volute face')
        spiral = []
        for i in range(steps+1):
            f=i/steps
            a = pi/2 - side*f*2.56*pi
            radius = scroll_radius*(.91-.76*f)
            spiral.append((cx+radius*cos(a), y-r*1.075, cz+radius*sin(a)*.92))
        b.tube(spiral, .016 if lod else .019, m['trim'],
               5 if lod else 8, 'Upper capital / spiral roll')
    # Small pendant folds below the stone roll appear in both street views.
    for t in (-.92,-.52,-.17,.17,.52,.92):
        nr = (sin(t),-cos(t))
        tangent = (cos(t),sin(t))
        def point(s,rad,h):
            return (x+nr[0]*rad+tangent[0]*s, y+nr[1]*rad+tangent[1]*s, base+h)
        b.add([point(-.058,1.22*r,.35),point(0,1.03*r,.13),
               point(.058,1.22*r,.35),point(0,1.31*r,.39),point(0,1.30*r,.28)],
              [(0,1,4),(1,2,4),(2,3,4),(3,0,4),(3,2,1,0)],
              m['trim'], 'Upper capital / carved fold')
    for h, dz, width in ((.525,.071,2.69*r),(.599,.082,2.81*r)):
        b.box((x,y,base+h),(width,width,dz),m['trim'],label='Upper capital / abacus')


def _balustrade(b, lod, halfwidth, sag, end_y, bottom, height, count, m, label):
    radius=(halfwidth*halfwidth+sag*sag)/(2*sag)
    center_y=end_y+radius-sag
    extent=asin(halfwidth/radius)
    def xy(a,r):
        return (r*sin(a),center_y-r*cos(a))
    steps=14 if lod else 32
    angles=[-extent+2*extent*i/steps for i in range(steps+1)]
    def band(depth,lo,hi,name):
        outer=[xy(a,radius+depth/2) for a in angles]
        inner=[xy(a,radius-depth/2) for a in reversed(angles)]
        b.plan_prism(Polygon(outer+inner),bottom+lo,bottom+hi,m['trim'],label+' / '+name)
    band(.27,0,.077,'foot')
    band(.24,height-.15,height-.089,'capping mould')
    band(.31,height-.09,height,'curved coping')
    for a in (-extent,extent):
        x,y=xy(a,radius)
        basis=((cos(a),sin(a),0),(-sin(a),cos(a),0),(0,0,1))
        b.box((x,y,bottom+height*.48),(.225,.25,height*.93),m['stone'],
              basis=basis,label=label+' / end piers')
    plinth=.076
    free=height-.145-plinth
    profile=[(0,.094),(.06,.098),(.12,.075),(.21,.052),(.32,.059),
             (.47,.094),(.55,.105),(.64,.092),(.75,.061),(.84,.055),
             (.90,.077),(1,.080)]
    for i in range(1,count+1):
        x,y=xy(-extent + 2*extent*i/(count+1),radius)
        b.lathe((x,y),[(bottom+plinth+free*h,r)for h,r in profile],
                m['trim'],8 if lod else 14,label+' / turned balusters')


def add_corner_ornaments(builder, lod, *, wall_y=0, axis_x=(-1.97,1.97), axis_y=-.26,
                         shaft_radius=.37, capital_z=16.10, oval_z=14.04,
                         oval_rx=.50, oval_rz=.85, roof_rail_z=17.66,
                         rail_halfwidth=1.23, rail_sag=.32, materials=None):
    """Add the oval, paired upper capitals and both open stone railings.

    Z is up. Positive Y runs into the building. capital_z is the top of the
    upper abacus; the adjoining main shaft should end 0.64 m below that height.
    For each curved rail the outward sag is measured from the chord at its ends.
    The main model supplies the solid balcony bases and the roof parapet ends.
    """
    m={'stone':'limestone','trim':'carved pale stone',
       'glass':'recessed glass','metal':'bronze window frame'}
    if materials:
        m.update(materials)
    _oculus(builder,lod,wall_y,oval_z,oval_rx,oval_rz,m)
    for x in axis_x:
        _capital(builder,lod,x,axis_y,shaft_radius,capital_z,m)
    _balustrade(builder,lod,rail_halfwidth,rail_sag,wall_y,roof_rail_z,.82,6,m,'Roof rail')
    _balustrade(builder,lod,1.70,.43,wall_y-.52,7.18,.78,9,m,'Balcony rail')
