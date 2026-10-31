"""Original city-hall exterior component library; all dimensions are metres.

The measured source footprint and photo-estimated architectural dimensions are
separate inputs. These are not construction drawings or a measured placement.
No source photograph is embedded in the geometry.
"""
from __future__ import annotations

import math
import numpy as np
from shapely.geometry import Polygon, box
from common.photo_architecture import opening


PALETTE = {
    'glazed green tile': {'color': [.075, .29, .19], 'roughness': .28},
    'green tile roll': {'color': [.10, .36, .23], 'roughness': .25},
    'golden glazed crest': {'color': [.80, .52, .12], 'roughness': .32},
    'vermilion timber': {'color': [.48, .075, .045], 'roughness': .57},
    'dark red lattice': {'color': [.29, .035, .025], 'roughness': .56},
    'blue painted bracket': {'color': [.045, .20, .37], 'roughness': .59},
    'green painted bracket': {'color': [.075, .30, .23], 'roughness': .59},
    'warm stone': {'color': [.70, .68, .59], 'roughness': .79},
    'stone reveal': {'color': [.54, .53, .47], 'roughness': .85},
    'grey recessed glazing': {'color': [.16, .21, .20], 'roughness': .30},
}


class Surface:
    """Share exact author vertices at roof patch seams before triangulation."""
    def __init__(self):
        self.vertices, self.faces, self.lookup = [], [], {}

    def point(self, p):
        k = tuple(round(float(v), 9) for v in p)
        if k not in self.lookup:
            self.lookup[k] = len(self.vertices)
            self.vertices.append(k)
        return self.lookup[k]

    def face(self, points):
        ids = [self.point(p) for p in points]
        ids = [v for i, v in enumerate(ids) if v != ids[i - 1]]
        if len(set(ids)) >= 3:
            self.faces.append(ids)


def roof(builder, *, name, cx, cy, half_width, half_depth, inner_width,
         inner_depth, eave_z, skirt_z, ridge_z, corner_lift=1.05,
         ridge_end_lift=.27, detailed=True):
    """Closed hip-and-gable roof: curved lower hips + raised gabled upper roof.

    inner_width/depth are half extents. The gables face east/west. A closed
    continuous bedding solid includes both vertical triangular gables. Separate
    capped tile-roll/ridge solids carry the editable surface detail.
    """
    assert 0 < inner_width < half_width and 0 < inner_depth < half_depth
    assert eave_z < skirt_z < ridge_z
    nx, ny, rings = (24, 12, 7) if detailed else (12, 6, 4)
    mesh = Surface()

    def perimeter(t):
        hx = half_width + (inner_width - half_width) * t
        hy = half_depth + (inner_depth - half_depth) * t
        pts = []
        # CCW perimeter; do not repeat the four shared corner vertices.
        for side, count in enumerate([nx, ny, nx, ny]):
            for j in range(count):
                f = -1 + 2 * j / count
                if side == 0: x, y = hx * f, -hy
                elif side == 1: x, y = hx, hy * f
                elif side == 2: x, y = -hx * f, hy
                else: x, y = -hx, -hy * f
                z = eave_z + (skirt_z - eave_z) * t ** 1.42
                z += corner_lift * abs(f) ** 8 * (1 - t) ** 2
                pts.append((cx + x, cy + y, z))
        return pts

    all_rings = [perimeter(k / rings) for k in range(rings + 1)]
    count = len(all_rings[0])
    for outer, inner in zip(all_rings, all_rings[1:]):
        for j in range(count):
            k = (j + 1) % count
            mesh.face([outer[j], outer[k], inner[k], inner[j]])

    def upper(x, y):
        f = abs(y) / inner_depth
        z = skirt_z + (ridge_z - skirt_z) * (1 - f ** .88)
        z += ridge_end_lift * (abs(x) / inner_width) ** 10 * (1 - f * f)
        return (cx + x, cy + y, z)

    xs = np.linspace(-inner_width, inner_width, nx + 1)
    ys = np.linspace(-inner_depth, inner_depth, ny + 1)
    for a, b in zip(xs, xs[1:]):
        for c, d in zip(ys, ys[1:]):
            mesh.face([upper(a, c), upper(b, c), upper(b, d), upper(a, d)])
    for x, reverse in [(-inner_width, True), (inner_width, False)]:
        for a, b in zip(ys, ys[1:]):
            face = [(cx+x, cy+a, skirt_z), (cx+x, cy+b, skirt_z),
                    upper(x, b), upper(x, a)]
            mesh.face(list(reversed(face)) if reverse else face)

    bottom = [(x, y, eave_z - .28) for x, y, z in all_rings[0]]
    for j in range(count):
        k = (j + 1) % count
        mesh.face([bottom[j], bottom[k], all_rings[0][k], all_rings[0][j]])
        mesh.face([(cx, cy, eave_z-.28), bottom[k], bottom[j]])
    builder.add(mesh.vertices, mesh.faces, 'glazed green tile', name+' / closed roof bedding')

    # Tile-roll paths use the identical roof equations; they are discrete capped
    # solids, not disconnected open surface strips. LOD retains roof silhouette.
    tile_pitch = .48 if detailed else 1.9
    cross_steps = 13 if detailed else 6
    for sign in [-1, 1]:
        for i, x in enumerate(np.linspace(-inner_width+.16, inner_width-.16,
                                          max(3, int(2*inner_width/tile_pitch)))):
            points = []
            for t in np.linspace(0, 1, cross_steps):
                hx = half_width + (inner_width-half_width)*t
                y = sign*(half_depth+(inner_depth-half_depth)*t)
                px = x/inner_width*hx
                z = eave_z+(skirt_z-eave_z)*t**1.42
                z += corner_lift*(abs(x)/inner_width)**8*(1-t)**2
                points.append((cx+px, cy+y, z+.055))
            for y in np.linspace(sign*inner_depth, 0, cross_steps)[1:]:
                p = upper(x, y)
                points.append((p[0], p[1], p[2]+.055))
            builder.tube(points, .065 if detailed else .055, 'green tile roll',
                         sides=6, label=f'{name} / long-slope tile roll {sign}/{i}')
        # Roof-end hip skirt flows away from the raised triangular gable.
        for i, y in enumerate(np.linspace(-inner_depth+.15, inner_depth-.15,
                                          max(3, int(2*inner_depth/tile_pitch)))):
            points = []
            for t in np.linspace(0, 1, cross_steps):
                hy = half_depth+(inner_depth-half_depth)*t
                x = sign*(half_width+(inner_width-half_width)*t)
                py = y/inner_depth*hy
                z = eave_z+(skirt_z-eave_z)*t**1.42
                z += corner_lift*(abs(y)/inner_depth)**8*(1-t)**2
                points.append((cx+x, cy+py, z+.055))
            builder.tube(points, .065 if detailed else .055, 'green tile roll',
                         sides=6, label=f'{name} / end-hip tile roll {sign}/{i}')

    ridge = [upper(x, 0) for x in np.linspace(-inner_width, inner_width, 25)]
    builder.tube([(x, y, z+.17) for x,y,z in ridge], .20,
                 'golden glazed crest', sides=10, label=name+' / gold ridge')
    for sx in [-1, 1]:
        for sy in [-1, 1]:
            points = []
            for t in np.linspace(0, 1, 13):
                x = sx*(half_width+(inner_width-half_width)*t)
                y = sy*(half_depth+(inner_depth-half_depth)*t)
                z = eave_z+(skirt_z-eave_z)*t**1.42+corner_lift*(1-t)**2+.13
                points.append((cx+x, cy+y, z))
            builder.tube(points, .16, 'golden glazed crest', sides=8,
                         label=f'{name} / gold hip {sx}/{sy}')
        gable_rake = [upper(sx*inner_width, y) for y in ys]
        builder.tube([(x, y, z+.14) for x,y,z in gable_rake], .17,
                     'golden glazed crest', sides=8, label=f'{name} / gable rake {sx}')
        # Abstract raised crest end: no unsupported exact dragon carving claim.
        x = cx+sx*inner_width
        z = ridge_z+ridge_end_lift+.15
        builder.tube([(x-sx*.30,cy,z), (x+sx*.06,cy,z+.35),
                      (x+sx*.17,cy,z+.85), (x-sx*.20,cy,z+1.05)],
                     .23, 'golden glazed crest', sides=10,
                     label=f'{name} / simplified crest finial {sx}')


def rail(builder, *, a, b, z, height=1.05, spacing=1.75, label='stone balustrade', detailed=True,
         include_start=True, include_end=True):
    """Open balustrade; uprights and rails are separate closed solids."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    length = np.linalg.norm(b-a)
    n = max(1, int(math.ceil(length/spacing)))
    direction = (b-a)/length
    transverse = np.array([-direction[1], direction[0], 0.])
    basis = [direction, transverse, np.array([0.,0.,1.])]
    for i in range(n+1):
        if (i==0 and not include_start) or (i==n and not include_end):continue
        p = a+(b-a)*i/n
        base = float(p[2])+z
        builder.box((p[0],p[1],base+height/2), (.23,.23,height), 'warm stone',
                    basis=basis,label=f'{label} / upright {i}')
        # Silhouette caps remain in LOD so the delivered geographic envelope is
        # identical; only intermediate balusters are reduced at distance.
        builder.lathe((p[0],p[1]),[(base+height,.17),(base+height+.11,.17),
                       (base+height+.22,.10)], 'warm stone', segments=8,
                      label=f'{label} / cap {i}')
    for h in [.19, height-.16]:
        p, q = a.copy(), b.copy()
        p[2] += z+h; q[2] += z+h
        builder.tube([p,q],.10,'warm stone',sides=8,label=f'{label} / horizontal rail {h}')
    if detailed:
        for i in range(n):
            p = a+(b-a)*(i+.5)/n
            builder.box((p[0],p[1],p[2]+z+height*.48),(.12,.12,height*.54),
                        'warm stone',basis=basis,label=f'{label} / intermediate baluster {i}')


def stairs(builder, *, name, cx, width, y0, y1, z0, z1, count, detailed=True, rail_sides=True):
    """One continuous closed stair solid, profile extruded across the width."""
    assert y1 > y0 and z1 > z0 and count >= 2
    dy, dz = (y1-y0)/count, (z1-z0)/count
    underside=max(0.,z0-.16)
    profile = [(y0,underside), (y1,underside), (y1,z1)]
    for i in range(count-1,-1,-1):
        profile.extend([(y0+i*dy,z0+(i+1)*dz),(y0+i*dy,z0+i*dz)])
    builder.prism(Polygon(profile),cx-width/2,cx+width/2,lambda y,z,x:(x,y,z),
                  'warm stone',name+' / continuous stepped solid')
    for side in ([-1,1] if rail_sides else []):
        x = cx+side*(width/2-.18)
        rail(builder,a=[x,y0,z0],b=[x,y1,z1],z=.10,label=f'{name} / side {side}',detailed=detailed)


def road_bridge(builder, *, name, cx, width, y0, y1, deck_z, arch_width,
                arch_top, arch_rise, detailed=True):
    """True east-west road tunnel, not a decorative front-facing dark arch.

    An arch in the north/south-height plane is extruded east/west. Its bottom is
    below zero so no stone soffit or skin seals the roadway at ground level.
    """
    assert arch_width < y1-y0 and arch_top < deck_z
    middle = (y0+y1)/2
    void = opening(middle,-.5,arch_width,arch_top+.5,arch_rise,
                   segments=32 if detailed else 16)
    body = box(y0,0.,y1,deck_z).difference(void)
    builder.prism(body,cx-width/2,cx+width/2,lambda y,z,x:(x,y,z),
                  'warm stone',name+' / arch-bearing deck and piers')
    # Arch rim follows the actual curve on each transverse end face.
    spring = arch_top-arch_rise
    inner = [(middle+arch_width/2*math.cos(t),spring+arch_rise*math.sin(t))
             for t in np.linspace(0,math.pi,33 if detailed else 17)]
    for side in [-1,1]:
        x = cx+side*(width/2+.035)
        builder.tube([(x,y,z) for y,z in inner],.11,'stone reveal',sides=8,
                     label=f'{name} / actual arch rim {side}')
        rail(builder,a=[x,y0,0],b=[x,y1,0],z=deck_z+.08,
             label=f'{name} / deck edge {side}',detailed=detailed)
    return {'axis':'east-west / local X', 'section_plane':'local YZ',
            'clearance_probe_y':middle,'clearance_probe_z':1.5,
            'arch_crown_estimate_m':arch_top,'width_estimate_m':width,
            'unmeasured':True}


def bracket(builder, x, y, z, outward, label, detailed=True):
    """Layered simplified dougong; all blocks and arms remain solid."""
    dx,dy = outward
    tangent = np.array([-dy,dx,0.])
    normal = np.array([dx,dy,0.])
    basis = [tangent,normal,np.array([0,0,1])]
    for k, (span, depth, h) in enumerate([(1.25,.72,.22),(.92,.95,.23),(.62,1.12,.20)]):
        builder.box((x+dx*k*.09,y+dy*k*.09,z+k*.28),(span,depth,h),
                    'blue painted bracket' if k%2 else 'green painted bracket',
                    basis=basis,label=f'{label} / bracket layer {k}')
        if detailed:
            for side in [-1,1]:
                p = np.array([x,y,z+k*.28])+tangent*(side*span*.35)
                builder.box(p,(.15,depth+.05,h+.12),'golden glazed crest',basis=basis,
                            label=f'{label} / bracket end {k}/{side}')
