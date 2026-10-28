"""Original Jinshanwei gatehouse double-eaved roof geometry. Agent, MIT.

All dimensions are supplied by the caller's design dictionary. The observed
double-eaved silhouette guides the exterior; hidden hip intersections and
small ceramic ornaments are explicitly estimated. No photographs are read.
"""
from collections import Counter
import math
import numpy as np
from shapely.geometry import box as rect
from shapely.ops import unary_union
from shapely.affinity import translate


class _Roof:
    def __init__(self, builder, design, lod):
        self.b = builder
        self.p = design['pavilion']
        self.lod = bool(lod)
        self.offset = np.array([*self.p['center_architecture_xy'], 0.], float)
        self.inner = (self.p['body_width_m']*.415, self.p['body_depth_m']*.415)
        self.ridge_half = self.p['upper_eave_width_m']*.26
        self.fields = []
        self.tile_count = 0
        self.end_count = 0

    def add(self, vertices, faces, material, label):
        self.b.add(np.asarray(vertices)+self.offset, faces, material, label)

    def tube(self, points, radius, material, sides, label):
        self.b.tube(np.asarray(points)+self.offset, radius, material, sides, label)

    def shell(self, vertices, quads, thickness, label):
        # Weld the singular hip apex before triangulating. This avoids tiny or
        # zero-area triangles without silently losing a face from the solid.
        unique, lookup, mapping = [], {}, []
        for p in vertices:
            key = tuple(np.round(p, 10))
            if key not in lookup:
                lookup[key] = len(unique)
                unique.append(p)
            mapping.append(lookup[key])
        v = np.asarray(unique, float)
        triangles = []
        for q in quads:
            q = [mapping[i] for i in q]
            for k in range(1, len(q)-1):
                t = [q[0], q[k], q[k+1]]
                if len(set(t)) < 3:
                    continue
                normal = np.cross(v[t[1]]-v[t[0]], v[t[2]]-v[t[0]])
                if np.linalg.norm(normal) <= 1e-10:
                    continue
                if normal[2] < 0:
                    t.reverse()
                triangles.append(tuple(t))
        n = len(v)
        verts = np.vstack([v, v-[0, 0, thickness]])
        faces = list(triangles)+[tuple(i+n for i in t[::-1]) for t in triangles]
        counts = Counter(tuple(sorted((a, b)))
                         for t in triangles for a, b in zip(t, t[1:]+t[:1]))
        for t in triangles:
            for a, b in zip(t, t[1:]+t[:1]):
                if counts[tuple(sorted((a, b)))] == 1:
                    faces.append((b, a, a+n, b+n))
        self.add(verts, faces, 'roof underlay', label)

    def parameters(self, tier):
        if tier == 'lower':
            return (self.p['lower_eave_width_m']/2, self.p['lower_eave_depth_m']/2,
                    self.p['lower_eave_center_height_m'], self.p['lower_roof_inner_height_m'],
                    self.p['lower_eave_corner_lift_m'])
        return (self.p['upper_eave_width_m']/2, self.p['upper_eave_depth_m']/2,
                self.p['upper_eave_center_height_m'], self.p['upper_main_ridge_height_m'],
                self.p['upper_eave_corner_lift_m'])

    def width_at(self, tier, field, t):
        hx, hy, *_ = self.parameters(tier)
        if tier == 'lower':
            inner = self.inner[0 if field < 2 else 1]
            outer = hx if field < 2 else hy
            return inner+(outer-inner)*t
        return self.ridge_half+(hx-self.ridge_half)*t if field < 2 else hy*t

    def point(self, tier, field, s, t):
        hx, hy, low, high, lift = self.parameters(tier)
        u = 2*s-1
        if tier == 'lower':
            ix, iy = self.inner
            if field < 2:
                x = u*(ix+(hx-ix)*t)
                y = (-1 if field == 0 else 1)*(iy+(hy-iy)*t)
            else:
                x = (-1 if field == 2 else 1)*(ix+(hx-ix)*t)
                y = u*(iy+(hy-iy)*t)
        elif field < 2:
            x = u*(self.ridge_half+(hx-self.ridge_half)*t)
            y = (-1 if field == 0 else 1)*hy*t
        else:
            x = (-1 if field == 2 else 1)*(self.ridge_half+(hx-self.ridge_half)*t)
            y = u*hy*t
        z = low+(high-low)*(1-t)**1.55 + lift*t**3*abs(u)**8
        return np.array([x, y, z], float)

    def fixed_course(self, tier, field, coordinate, t):
        width = self.width_at(tier, field, t)
        return self.point(tier, field, (coordinate/width+1)/2, t)

    def cap_course(self, points, label, material):
        """Closed half-round tile course, without a stack of cuboids."""
        vertices = []
        sections = 4 if self.lod else 5
        radius = .082 if self.lod else .072
        for k, p in enumerate(points):
            tangent = points[min(k+1, len(points)-1)]-points[max(k-1, 0)]
            tangent /= np.linalg.norm(tangent)
            cross = np.cross(tangent, [0., 0., 1.])
            cross /= np.linalg.norm(cross)
            up = np.cross(cross, tangent)
            for angle in np.linspace(0, math.pi, sections):
                vertices.append(p+radius*(math.cos(angle)*cross+math.sin(angle)*up))
        faces = [tuple(reversed(range(sections))),
                 tuple((len(points)-1)*sections+j for j in range(sections))]
        for k in range(len(points)-1):
            for j in range(sections):
                a = k*sections+j
                b = k*sections+(j+1) % sections
                faces.append((a, b, b+sections, a+sections))
        # The upper half-circle's cross-section uses cross x up = -tangent;
        # reverse its solid winding so all cap and side normals point outward.
        self.add(vertices, [tuple(reversed(f)) for f in faces], material, label)

    def field(self, tier, field):
        n, nu = (3, 8) if self.lod else (8, 14)
        vertices = [self.point(tier, field, s, t)
                    for t in np.linspace(0, 1, n+1) for s in np.linspace(0, 1, nu+1)]
        faces = [(j*(nu+1)+i, j*(nu+1)+i+1,
                  (j+1)*(nu+1)+i+1, (j+1)*(nu+1)+i)
                 for j in range(n) for i in range(nu)]
        label = f'roof/{tier}/field-{field}'
        self.shell(vertices, faces, .12, label+'/closed-curved-slope-shell')
        half = self.width_at(tier, field, 1.)
        inner = self.width_at(tier, field, 0.)
        count = max(6, round(2*half/(.80 if self.lod else .30)))
        actual = 0
        for i in range(count):
            coordinate = -half+(i+.5)*2*half/count
            start = max(.018, (abs(coordinate)-inner)/max(half-inner, 1e-9)+.018)
            if start >= .96:
                continue
            points = [self.fixed_course(tier, field, coordinate, t)+[0, 0, .025]
                      for t in np.linspace(start, 1, 4 if self.lod else 7)]
            self.cap_course(points, label+f'/half-round-tile-course-{i}', f'roof tile {i%3}')
            actual += 1
            self.tile_count += 1
            if not self.lod:
                end = points[-1]
                out = points[-1]-points[-2]
                out /= np.linalg.norm(out)
                self.tube([end-out*.012, end+out*.050], .085, 'ridge ceramic', 6,
                          label+f'/round-eave-end-tile-{i}')
                self.end_count += 1
                # Restrained recessed-centre detail only on the visible front;
                # the exact photographed floral motifs are not resolved.
                if field == 0 and i % 3 == 0:
                    self.tube([end+out*.050, end+out*.054], .024, 'roof tile 0', 6,
                              label+f'/end-tile-centre-{i}')
        fascia = [self.point(tier, field, s, 1)-[0, 0, .095]
                  for s in np.linspace(0, 1, 11 if self.lod else 19)]
        self.tube(fascia, .085, 'dark timber', 5 if self.lod else 6,
                  label+'/continuous-curved-eave-fascia')
        # Long slender rafters are inset underneath the eaves. Use a sparse,
        # independent rhythm, not a tiled surface made of boxes.
        for k, s in enumerate(np.linspace(.08, .92, 3 if self.lod else 8)):
            points = [self.point(tier, field, s, t)-[0, 0, .185]
                      for t in np.linspace(.25, 1, 3 if self.lod else 5)]
            self.tube(points, .048, 'dark timber', 4,
                      label+f'/underside-rafter-{k}')
        self.fields.append({'tier': tier, 'field': field, 'closed_shell_thickness_m': .12,
                            'actual_tile_courses': actual, 'corner_lift_m': self.parameters(tier)[4],
                            'geometry_role': 'Observed curved silhouette; hidden intersections estimated'})

    def ridges(self, tier):
        for field in [0, 1]:
            for side in [0, 1]:
                points = [self.point(tier, field, side, t)+[0, 0, .13]
                          for t in np.linspace(0, 1, 7 if self.lod else 13)]
                self.tube(points, .13, 'ridge ceramic', 5 if self.lod else 6,
                          f'roof/{tier}/hip-{field}-{side}')
                end = self.point(tier, field, side, 1)+[0, 0, .13]
                direction = np.array([-1 if side == 0 else 1, -1 if field == 0 else 1, 0.], float)
                direction /= np.linalg.norm(direction)
                # An upturned ceramic terminal silhouette, not an asserted
                # anatomical reconstruction of unresolved small ridge animals.
                shape = [(0, 0), (.13, .12), (.24, .30), (.27, .49), (.25, .61)]
                self.tube([end+direction*a+[0, 0, z] for a, z in shape],
                          .062, 'ridge ceramic', 5 if self.lod else 7,
                          f'roof/{tier}/estimated-upturned-corner-terminal-{field}-{side}')

    def intertier(self):
        ix, iy = self.inner
        low = self.p['body_eave_m']-.10
        high = self.p['upper_eave_center_height_m']+.05
        # Union the four infill wall plans before extrusion. Their corner
        # tops and undersides each have one owner, retaining the same volume.
        closure=unary_union([rect(-ix,-iy-.06,ix,-iy+.06),
                             rect(-ix,iy-.06,ix,iy+.06),
                             rect(-ix-.06,-iy,-ix+.06,iy),
                             rect(ix-.06,-iy,ix+.06,iy)])
        closure=translate(closure,xoff=self.offset[0],yoff=self.offset[1])
        self.b.plan_prism(closure,low,high,'dark timber',
                         'roof/estimated-intertier-closure/continuous-unioned-walls')

    def main_ridge(self):
        ridge = self.p['upper_main_ridge_height_m']
        half = self.ridge_half
        self.tube([[-half, 0, ridge+.13], [half, 0, ridge+.13]],
                  .13, 'ridge ceramic', 6 if self.lod else 10, 'roof/upper/main-ridge-coping')
        # Estimated fine ridge framing: a genuine gap remains above the coping.
        # Ends stop before the terminal curls; no duplicate coplanar endcaps.
        self.b.box(np.array([0, 0, ridge+.41])+self.offset,
                   [2*half-.16, .18, .08], 'ridge ceramic', label='roof/upper/ridge-openwork-upper-band')
        for k, x in enumerate(np.linspace(-half+.1, half-.1, 13 if self.lod else 27)):
            self.b.box(np.array([x, 0, ridge+.31])+self.offset,
                       [.055, .16, .19], 'ridge ceramic', label=f'roof/upper/ridge-openwork-post-{k}')
        target = self.p['highest_ridge_ornament_target_m']
        radius = .080
        peak = target-radius
        for side in [-1, 1]:
            # This is a deliberately restrained S/curl silhouette following
            # the visible two terminal curls; tiny sculptural anatomy unknown.
            shape = [(-.10, ridge+.12), (.03, ridge+.36), (.11, peak-.16),
                     (.23, peak), (.36, peak-.06), (.38, peak-.22),
                     (.28, peak-.30), (.17, peak-.25)]
            self.tube([[side*(half+x), 0, z] for x, z in shape], radius,
                      'ridge ceramic', 6 if self.lod else 8,
                      f'roof/upper/estimated-curled-ridge-terminal-{side}')

    def build(self):
        start = len(self.b.parts)
        for tier in ['lower', 'upper']:
            for field in range(4):
                self.field(tier, field)
            self.ridges(tier)
        self.intertier()
        self.main_ridge()
        parts = self.b.parts[start:]
        vertices = np.asarray([v for part in parts for v in part['vertices']])
        return {'schema': 'jinshan-double-eave-geometry-v1', 'lod': self.lod,
                'fields': self.fields, 'tile_course_count': self.tile_count,
                'round_end_tile_count': self.end_count,
                'parts': len(parts), 'triangles': sum(len(p['triangles']) for p in parts),
                'bounds_architecture_xyz_m': {'min': vertices.min(0).tolist(), 'max': vertices.max(0).tolist()},
                'intertier_closure_estimated': True,
                'intertier_inner_half_extent_m': list(self.inner),
                'ridge_half_length_m': self.ridge_half,
                'estimated_parts': ['hidden hip intersections', 'intertier timber closure', 'small ridge ornaments', 'tile counts'],
                'scope': 'Eight curved closed slope shells, independent half-round tile courses, round ends, fascia, rafters and ridge ornaments. No whole-enclosure roof.'}


def build_roof(builder, design, lod=False):
    """Append roof parts in architecture XYZ; caller handles ENU rotation."""
    return _Roof(builder, design, lod).build()
