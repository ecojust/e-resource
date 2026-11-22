"""Clay tile roof, stepped timber/cement verges, shed lights and chimney of the replica.

The museum courtyard, local axes and provisional 1.75 m central-arch scale are
defined in villa-roof-interface.json. Roof points refer to the modern replica.
"""
import json
import math
from pathlib import Path

from PIL import Image, ImageDraw
from shapely import constrained_delaunay_triangles
from shapely.geometry import Polygon, box as rectangle
from shapely.geometry.polygon import orient

HERE = Path(__file__).resolve().parent
CLAY = 'Villa roof | interlocking clay tiles'
CAP = 'Villa roof | red ridge tile'
EDGE = 'Villa roof | weathered fascia'
LIGHT = 'Villa roof | pale verge soffit'
CHEEK = 'Villa roof | ochre dormer cheeks'
FRAME = 'Villa roof | stained casement'
PANE = 'Villa roof | courtyard glass'
FLASH = 'Villa roof | cap flashing'
FLUE = 'Villa roof | chimney brick'
MORTAR = 'Villa roof | chimney lip'


def linear(rgb):
    return [((v / 255 + .055) / 1.055) ** 2.4 if v > 10 else v / (255 * 12.92) for v in rgb]


PALETTE = {key: {'color': linear(rgb), 'roughness': rough} for key, rgb, rough in [
    (CAP, (155, 83, 63), .82), (EDGE, (129, 114, 104), .89),
    (LIGHT, (180, 162, 147), .87), (CHEEK, (140, 92, 71), .86),
    (FRAME, (63, 51, 46), .64), (PANE, (112, 117, 117), .31),
    (FLASH, (113, 99, 91), .67), (FLUE, (149, 85, 68), .87),
    (MORTAR, (116, 92, 82), .91)]}
PALETTE[PANE].update(metallic=.09, alpha=.89)
PALETTE[CLAY] = {'color': [1., 1., 1.], 'roughness': .87,
                 'texture': str(HERE / 'replica-roof-tiles.png')}


def create_tile_atlas():
    """Original schematic tile rolls, troughs and lapped noses. No image tracing."""
    path = HERE / 'replica-roof-tiles.png'
    if path.is_file():
        return
    image = Image.new('RGB', (704, 480))
    draw = ImageDraw.Draw(image)
    for row in range(40):
        for col in range(44):
            left, top = 16 * col, 12 * row
            v = ((col * 23 + row * 41 + col * row * 3) % 17) - 8
            for j in range(12):
                for i in range(16):
                    roll = int(7 * math.cos((i - 3) / 16 * math.tau))
                    seam = -12 if i == 13 else (-35 if j > 8 else 0)
                    lip = 15 if j == 7 else 0
                    variation = v + roll + seam + lip
                    color = tuple(max(0, min(255, round(c + variation * f))) for c, f in [(160, 1), (94, .86), (72, .74)])
                    draw.point((left + i, top + j), fill=color)
    image.quantize(92).save(path, optimize=True)


def _shell(b, polygon, delta, material, label, uv=None):
    """Extrude a convex 3D polygon. Duplicate vertices at UV seams only."""
    if len(polygon) < 3:
        return
    p = list(polygon)
    def sub(a, c):
        return [u - v for u, v in zip(a, c)]
    for j in range(1, len(p) - 1):
        a, c = sub(p[j], p[0]), sub(p[j + 1], p[0])
        normal = (a[1] * c[2] - a[2] * c[1], a[2] * c[0] - a[0] * c[2], a[0] * c[1] - a[1] * c[0])
        if abs(sum(t * v for t, v in zip(normal, delta))) > 1e-9:
            break
    else:
        return
    if sum(t * v for t, v in zip(normal, delta)) > 0:
        p.reverse()
    q = [tuple(a + d for a, d in zip(point, delta)) for point in p]
    facesets = [p, list(reversed(q))]
    for i in range(len(p)):
        j = (i + 1) % len(p)
        facesets.append([p[j], p[i], q[i], q[j]])
    vertices, faces, uvs = [], [], []
    for side, face in enumerate(facesets):
        index = len(vertices)
        vertices.extend(face)
        faces.append(tuple(range(index, index + len(face))))
        if uv:
            if side < 2:
                uvs.extend(uv(point) for point in face)
            else:
                uvs.extend([(.2, .1), (.4, .1), (.4, .108), (.2, .108)])
    b.add(vertices, faces, material, label)
    if uv:
        b.parts[-1]['texcoords'] = uvs


def _clip(points, field):
    """Keep the half-plane field(x,y)>=0, preserving polygon order."""
    out = []
    for a, c in zip(points, points[1:] + points[:1]):
        va, vc = field(*a), field(*c)
        if va >= -1e-8:
            out.append(a)
        if (va < -1e-8) != (vc < -1e-8):
            t = va / (va - vc)
            out.append(tuple(u + t * (v - u) for u, v in zip(a, c)))
    clean = []
    for p in out:
        if not clean or math.dist(p, clean[-1]) > 1e-6:
            clean.append(p)
    if len(clean) > 1 and math.dist(clean[0], clean[-1]) < 1e-6:
        clean.pop()
    return clean


def _roof_face(b, xy, level, name, across, openings=()):
    """Skin both sides and return the cut at every cheek, so no tile crosses a casement."""
    area = Polygon(xy)
    for opening in openings:
        area = area.difference(opening if isinstance(opening, Polygon) else rectangle(*opening))
    polygons = [area] if area.geom_type=='Polygon' else list(area.geoms)
    for i, polygon in enumerate(polygons):
        if polygon.area < 1e-7:
            continue
        polygon = orient(polygon, sign=1)
        vertices, faces, uv = [], [], []
        def add(corners, coords):
            ix = len(vertices)
            vertices.extend(corners)
            faces.append(tuple(range(ix,ix+len(corners))))
            uv.extend(coords)
        def point(xy, d):
            x,y = xy
            return (x,y,level(x,y)+d)
        def mapped(corners):
            return [((p[0 if across=='x' else 1]+12)/24,1-(p[2]-2.3)/12.9) for p in corners]
        for tri in constrained_delaunay_triangles(polygon).geoms:
            top = list(orient(tri,sign=1).exterior.coords)[:3]
            for part in [[point(q,0) for q in top],[point(q,-.105) for q in reversed(top)]]:
                add(part,mapped(part))
        for border in [polygon.exterior,*polygon.interiors]:
            points = list(border.coords)
            for a,c in zip(points,points[1:]):
                add([point(c,0),point(a,0),point(a,-.105),point(c,-.105)],
                    [(.2,.1),(.4,.1),(.4,.108),(.2,.108)])
        b.add(vertices,faces,CLAY,name+((' '+str(i+1)) if len(polygons)>1 else ''))
        b.parts[-1]['texcoords']=uv


def _beam(b, a, c, width, height, material, label):
    dx, dy, dz = (v - u for u, v in zip(a, c))
    length = math.hypot(dx, dy)
    if length < 1e-8:
        return
    xx, yy = -.5 * width * dy / length, .5 * width * dx / length
    _shell(b, [(a[0] + xx, a[1] + yy, a[2]), (a[0] - xx, a[1] - yy, a[2]),
               (c[0] - xx, c[1] - yy, c[2]), (c[0] + xx, c[1] + yy, c[2])],
           (0, 0, -height), material, label)


MEASURED = json.loads((HERE.parent/'measurements/roof-fascia-and-oriel.json').read_bytes())


def _oriel_cap(b, row, name):
    side = 'left' if row['y_face'] < -2 else 'right'
    points = MEASURED['oriels'][side]['world']
    outer = [points[key] for key in ['back_l','front_l','front_r','back_r']]
    a, c = [points[key] for key in ['ridge_l','ridge_r']]
    z, left = min(p[2] for p in outer), min(p[0] for p in outer)
    for i, face in enumerate([[outer[0], outer[1], a], [outer[1], outer[2], c, a], [outer[2], outer[3], c]]):
        _shell(b, face, (0, 0, -.065), CLAY, name + ' tile hip ' + str(i + 1),
               lambda p: ((p[0] - left) / 20 + .2, .5 - (p[2] - z) / 12.9))
        _beam(b, outer[i], outer[i + 1], .065, .087, EDGE, name + ' eave ' + str(i + 1))


def _dormer(b, name, center, axis, outward, width, sill, head, back_depth, lod):
    # Positions use the plane of the glass. Back depth closes the two cheeks into the pitch.
    def pt(u, d, z):
        return (center[0] + u * axis[0] + d * outward[0],
                center[1] + u * axis[1] + d * outward[1], z)
    def panel(poly, offset, mat, label):
        outer = [pt(*p) for p in poly]
        _shell(b, outer, offset, mat, name + ' ' + label)
    half = width * .5
    is_court = name.startswith('Roof court')
    for sign in [-1, 1]:
        u = sign * (half + .04)
        panel([(u, .025, sill - .065), (u, .025, head), (u + sign * (.23 if is_court else .04), -back_depth, head + .18),
               (u + sign * (.23 if is_court else .04), -back_depth, head - .53)],
              (-sign * axis[0] * .08, -sign * axis[1] * .08, 0), CHEEK, 'cheek ' + str(sign))
    panel([(-half - .13, .105, head + .04), (half + .13, .105, head + .04),
           (half + (.30 if is_court else .13), -back_depth - .08, head + .22), (-half - (.30 if is_court else .13), -back_depth - .08, head + .22)],
          (0, 0, -.10), FLASH, 'shed cap')
    def front(u0, u1, z0, z1, d, depth, mat, label):
        panel([(u0, d, z0), (u1, d, z0), (u1, d, z1), (u0, d, z1)],
              (-outward[0] * depth, -outward[1] * depth, 0), mat, label)
    stile = min(.075, width * .055)
    for i, u in enumerate([-half + stile / 2, 0, half - stile / 2]):
        front(u-stile/2, u+stile/2, sill+.08, head-.075, .014, .065, FRAME, 'stile '+str(i+1))
    for label, z0, z1 in [('head', head-.075, head), ('sill', sill, sill+.08)]:
        front(-half, half, z0, z1, .026, .09, FRAME, label)
    for i, (lo, hi) in enumerate([(-half+stile, -.5*stile), (.5*stile, half-stile)]):
        front(lo, hi, sill+.08, head-.075, -.032, .022, PANE, 'pane '+str(i+1))
    if name.startswith('Roof court'):
        front(-half-.13,half+.13,head-.24,head+.04,.101,.085,FLASH,'cap face')
    if not lod:
        front(-half-.07, half+.07, sill-.068, sill+.01, .076, .15, EDGE, 'drip')


def add_roofs(b, lod, layout):
    """Add the roof to the building assembled from villa-roof-interface.json."""
    create_tile_atlas()
    b.palette.update(PALETTE)
    left, right, arcade = layout['left'], layout['right'], layout['arcade']
    xl, xr = left['x_left']-.22, right['x_right']+.22
    ye, yb = arcade['cornice_face_y'], 8.68
    ze, zr, yr = arcade['z_arcade_top']+.435, 11.50, 2.72
    rl, rr = -2.35, 1.37
    slopes = {
        'court': lambda x,y: ze+(zr-ze)*(y-ye)/(yr-ye),
        'rear': lambda x,y: ze+(zr-ze)*(yb-y)/(yb-yr),
        'outer left': lambda x,y: ze+(zr-ze)*(x-xl)/(rl-xl),
        'outer right': lambda x,y: ze+(zr-ze)*(xr-x)/(xr-rr)}
    rect = [(xl,ye),(xr,ye),(xr,yb),(xl,yb)]
    court_dormers=[(-2.55,1.56,4.68,6.05),(-.07,1.73,4.69,6.08),(2.32,1.73,4.70,6.03)]
    courtyard_slots=[]
    for xc,w,_,_ in court_dormers:
        half=w/2
        # Under the splayed, flashing-clad cheek the top clay is cut to its outer edge.
        courtyard_slots.append(Polygon([(xc-half-.12,-.51),(xc+half+.12,-.51),
                                         (xc+half+.32,.555),(xc-half-.32,.555)]))
    outer_slots=[(xl+.51,y-.76,xl+1.99,y+.76) for y in [1.76,4.83]]
    for side, plane in slopes.items():
        poly = list(rect)
        for other, compare in slopes.items():
            if other != side:
                poly = _clip(poly, lambda x,y: compare(x,y)-plane(x,y))
        _roof_face(b, poly, plane, 'Villa roof | main '+side, 'y' if 'outer' in side else 'x',
                   courtyard_slots if side=='court' else outer_slots if side=='outer left' else ())
    _beam(b, (rl,yr,zr+.045),(rr,yr,zr+.045),.17,.107,CAP,'Villa roof | main ridge')
    for i, (a,c) in enumerate([((xl,ye,ze),(rl,yr,zr)),((xl,yb,ze),(rl,yr,zr)),
                               ((xr,ye,ze),(rr,yr,zr)),((xr,yb,ze),(rr,yr,zr))]):
        _beam(b, (a[0],a[1],a[2]+.035),(c[0],c[1],c[2]+.035),.12,.085,CAP,'Villa roof | hip '+str(i+1))
    for name, row in [('left',left),('right',right)]:
        x0, x1 = row['x_left']-.22, row['x_right']+.22
        # Peak X follows the independently traced facade face, which is slightly asymmetric.
        xc = -7.34 if name=='left' else 6.54
        yfront, peak = row['y_outer_ridge'], row['z_outer_ridge']-.07
        toe = row['z_inner_toe']+.005
        for i, xe in enumerate([x0,x1]):
            def pitch(x,y):
                return peak + (toe-peak)*(x-xc)/(xe-xc)
            # Intersection with the front plane of the central hip.
            def valley_y(x):
                return ye+(pitch(x,0)-ze)*(yr-ye)/(zr-ze)
            xy=[(xe,yfront),(xc,yfront),(xc,valley_y(xc)+.04),(xe,valley_y(xe)+.04)]
            _roof_face(b,xy,pitch,'Villa roof | '+name+' gable '+str(i+1),'y',
                       [(-5.90,-2.89,-5.10,-1.49)] if name=='left' and i==1 else ())
            shape=MEASURED['gables'][name]['world']
            key = 'left' if i == 0 else 'right'
            outer_toe, inner_toe = shape[key+'_o'], shape[key+'_i']
            outer_peak, inner_peak = shape['peak_o'], shape['peak_i']
            def edge(a,c,t):
                return tuple(u+(v-u)*t for u,v in zip(a,c))
            for layer, f0, f1, mat, offset in [
                    ('outside fillet',0,.13,EDGE,-.025),
                    ('flat fascia',.13,.55,EDGE,0),
                    ('pale soffit',.55,1.,LIGHT,.015)]:
                band = [edge(outer_toe,inner_toe,f0),edge(outer_peak,inner_peak,f0),
                        edge(outer_peak,inner_peak,f1),edge(outer_toe,inner_toe,f1)]
                adjusted=[(x,y+offset,z) for x,y,z in band]
                _shell(b,adjusted,(0,.22,0),mat,'Villa roof | '+name+' '+layer+' '+str(i+1))
        _beam(b,(xc,yfront,peak+.035),(xc,valley_y(xc)+.07,peak+.035),.115,.07,CAP,'Villa roof | '+name+' ridge')
        _oriel_cap(b,row,'Villa roof | '+name+' oriel')
    for i,(xc,w,sill,head) in enumerate(court_dormers):
        _dormer(b,'Roof court '+str(i+1),(xc,-.48),(1,0),(0,-1),w,sill,head,1.03,lod)
    _dormer(b,'Roof left inner',(-5.12,-2.19),(0,1),(1,0),1.34,5.17,6.19,.76,lod)
    # The independent street-side photographs show two double lights on the long exterior slope.
    for i, along in enumerate([1.76,4.83]):
        _dormer(b,'Roof left outer '+str(i+1),(xl+.52,along),(0,1),(-1,0),1.51,4.82,5.91,1.52,lod)
    # Rectangular brick stack with a slightly darker top course, below which the roof hides the base.
    x, y = 6.02, .23
    base, top = 5.0, 11.18
    b.box((x,y,(base+top)/2),(1.045,.64,top-base),FLUE,label='Villa roof | brick chimney shaft')
    b.box((x,y,top+.036),(1.075,.665,.072),MORTAR,label='Villa roof | chimney head')
    if not lod:
        for i in range(1,27):
            z=top-i*.17
            if z<=base:
                break
            b.box((x,y-.321,z),(1.041,.009,.007),MORTAR,label='Villa roof | chimney joint '+str(i))
