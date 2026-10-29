"""Minglun Hall: text dimensions and explicitly assumed exterior, with limited tree-occluded courtyard-photo context. MIT."""
import argparse
import json
from pathlib import Path
import numpy as np
from shapely.geometry import Polygon, box
from common.photo_architecture import Builder, Facade

ID = 'chongming-minglun-hall'
# The museum does not specify the measurement endpoints. Assigning its length
# and width to the base is a modeling interpretation, not a measured survey.
P = {
    'base_width': 20.6, 'base_depth': 12.7, 'base_height': .72,
    'wall_width': 20.0, 'wall_depth': 11.5, 'wall_thickness': .20,
    'front_divisions': 5, 'roof_width': 21.5, 'roof_depth': 14.0,
    'ridge_under_cap': 10.12, 'eave_top': 6.90, 'total_height': 10.37,
    'window_width': 2.5, 'window_bottom': 1.8, 'window_top': 4.9,
    'window_columns': 4, 'window_rows': 7,
    'door_width': 3.0, 'door_bottom': .72, 'door_top': 5.15,
}
PALETTE = {
    'plaster': {'color': [.77, .76, .70], 'roughness': .96},
    'stone base': {'color': [.45, .46, .43], 'roughness': .97},
    'red brown timber': {'color': [.22, .045, .028], 'roughness': .78},
    'timber edges': {'color': [.29, .067, .043], 'roughness': .76},
    'panel recess': {'color': [.13, .025, .017], 'roughness': .87},
    'inset shadow': {'color': [.018, .024, .020], 'roughness': 1},
    'roof bedding': {'color': [.19, .21, .20], 'roughness': .97},
    'grey tile 0': {'color': [.29, .30, .28], 'roughness': .94},
    'grey tile 1': {'color': [.23, .25, .24], 'roughness': .94},
    'grey tile 2': {'color': [.34, .35, .31], 'roughness': .93},
    'plain ridge': {'color': [.33, .34, .31], 'roughness': .94},
}

class MinglunHall:
    def __init__(self, lod=False):
        self.b = Builder(PALETTE)
        self.lod = lod
        self.features = []
        # Five front divisions are assumed: the old five-bay description is historical, not a modern grid survey.
        # Local X uses the documented length, without assigning a compass heading.
        # The source specifies neither facade bay count nor entrance direction.
        self.bay_width = P['wall_width'] / P['front_divisions']
        self.window_centres = [i * self.bay_width for i in [-2, -1, 1, 2]]

    def cube(self, centre, size, material, label):
        self.b.box(centre, size, material, label=label)

    def facade(self, edge, label):
        x = P['wall_width'] / 2
        y = P['wall_depth'] / 2
        inner_x = x - P['wall_thickness']
        # Front/rear meet the inner side-wall edge, without exposed coplanar caps.
        if edge == 0:
            return Facade(self.b, [-inner_x, -y], [inner_x, -y], label)
        if edge == 2:
            return Facade(self.b, [inner_x, y], [-inner_x, y], label)
        points = [[-x, -y], [x, -y], [x, y], [-x, y]]
        return Facade(self.b, points[edge], points[(edge + 1) % 4], label)

    def roofz(self, y):
        return P['ridge_under_cap'] - (P['ridge_under_cap'] - P['eave_top']) * abs(y) / (P['roof_depth'] / 2)

    def roof(self):
        # The small tree-occluded photo does not establish the complete Minglun roof topology.
        # Planar gable slopes, tiles and plain caps are all authored approximations.
        half_width = P['roof_width'] / 2
        for side in [-1, 1]:
            end = side * P['roof_depth'] / 2
            profile = Polygon([(0, P['ridge_under_cap']), (end, P['eave_top']),
                               (end, P['eave_top'] - .08), (0, P['ridge_under_cap'] - .08)])
            self.b.prism(profile, -half_width, half_width, lambda y, z, x: (x, y, z),
                         'roof bedding', 'assumed-gable-roof-closed-slope')
            count = 34 if self.lod else 82
            for i, x in enumerate(np.linspace(-half_width + .12, half_width - .12, count)):
                p = np.array([x, 0, P['ridge_under_cap'] + .045])
                q = np.array([x, end, P['eave_top'] + .045])
                direction = q - p
                direction /= np.linalg.norm(direction)
                self.b.tube([p, q], .056, f'grey tile {i % 3}', 6 if self.lod else 10, 'assumed-tile-course')
                self.b.tube([q - direction * .012, q + direction * .045], .071, 'plain ridge', 8, 'round-tile-end')
                if not self.lod:
                    for t in np.linspace(.12, .96, 8):
                        mid = p + (q - p) * t
                        self.b.tube([mid - direction * .010, mid + direction * .010], .060, 'grey tile 2', 8, 'tile-lap-band')
            self.b.tube([(-half_width, end, P['eave_top'] - .07), (half_width, end, P['eave_top'] - .07)],
                        .065, 'red brown timber', 8, 'under-eave-fascia')
            for x in np.linspace(-half_width + .3, half_width - .3, 22 if self.lod else 44):
                start_y = side * (P['wall_depth'] / 2 - .3)
                self.b.tube([(x, start_y, self.roofz(start_y) - .14), (x, end, P['eave_top'] - .14)],
                            .035, 'red brown timber', 6, 'estimated-rafter-end')
            for x in [-half_width, half_width]:
                self.b.tube([(x, 0, P['ridge_under_cap'] + .03), (x, end, P['eave_top'] + .03)],
                            .075, 'plain ridge', 8, 'plain-gable-edge-cap')
        self.cube((0, 0, P['total_height'] - .11), (P['roof_width'], .25, .22),
                  'plain ridge', 'plain-main-ridge-no-finials')
        self.features.append({'kind': 'assumed_roof', 'type': 'simple planar two-slope gable',
                              'ridge_total_height_m': P['total_height'], 'roof_end_type_unverified': True})

    def doors(self, front):
        # Closed double-leaf design is estimated; the pale central photo region cannot identify its true construction.
        bottom, top = P['door_bottom'] + .02, P['door_top'] - .02
        middle = P['door_bottom'] + (P['door_top'] - P['door_bottom']) * .322
        height, centre_z = top - bottom, (top + bottom) / 2
        width = (P['door_width'] - .05) / 2
        for sign in [-1, 1]:
            centre = sign * P['door_width'] / 4
            for x in [centre - (width - .11) / 2, centre + (width - .11) / 2]:
                front.box(x, centre_z, .11, height, .12, -.06, 'red brown timber', 'assumed-door-stile')
            for z, h in [(bottom + .055, .11), (middle, .12), (top - .055, .11)]:
                front.box(centre, z, width, h, .11, -.08, 'red brown timber', 'assumed-door-rail')
            for z0, z1 in [(bottom + .11, middle - .06), (middle + .06, top - .11)]:
                z, h = (z0 + z1) / 2, z1 - z0
                front.box(centre, z, width - .22, h, .10, -.09, 'red brown timber', 'assumed-solid-door-panel')
                front.box(centre, z, width - .36, h - .15, .018, -.031, 'panel recess', 'panel-inset-tone')
                if not self.lod:
                    for zz in [z - (h - .15) / 2, z + (h - .15) / 2]:
                        front.box(centre, zz, width - .34, .024, .018, -.017, 'timber edges', 'simple-panel-edge')
        front.box(0, centre_z, .035, height, .025, .015, 'red brown timber', 'closing-batten')
        for x in [-(P['door_width'] / 2 + .05), P['door_width'] / 2 + .05]:
            front.box(x, centre_z, .12, P['door_top'] - P['door_bottom'], .23, -.04, 'timber edges', 'assumed-door-jamb')
        front.box(0, P['door_top'] + .05, P['door_width'] + .22, .16, .23, -.04, 'timber edges', 'assumed-door-lintel')
        self.features.append({'kind': 'estimated-central-double-door', 'opening_width_m': P['door_width'],
                              'opening_bottom_top_m': [P['door_bottom'], P['door_top']], 'documented': False})

    def walls(self):
        self.cube((0, 0, P['base_height'] / 2), (P['base_width'], P['base_depth'], P['base_height']),
                  'stone base', 'documented-plan-size-assigned-to-base')
        # One closed four-step prism avoids nested coplanar stair boxes.
        stair=Polygon([(-8.15,0),(-6.35,0),(-6.35,.72),(-6.80,.72),(-6.80,.54),(-7.25,.54),(-7.25,.36),(-7.70,.36),(-7.70,.18),(-8.15,.18)])
        self.b.prism(stair,-3.0,3.0,lambda y,z,x:(x,y,z),'stone base','estimated-four-step-closed-profile')
        # The chosen six-column porch is an estimate, not a counted photo grid.
        for x in [-9.6,-6.0,-2.0,2.0,6.0,9.6]:
            self.b.tube([(x,-6.12,.85),(x,-6.12,6.92)],.13,'red brown timber',12 if self.lod else 20,'estimated-porch-column')
            self.cube((x,-6.12,.82),(.42,.42,.20),'stone base','estimated-column-stone-foot')
        self.cube((0,-6.12,6.65),(19.6,.26,.30),'red brown timber','estimated-porch-long-beam')
        for sign in [-1,1]:
            for xx in [3.35,5.2,7.05,8.9,10.0]:
                x=sign*xx
                self.cube((x,-6.15,1.16),(.15,.20,.88),'stone base','estimated-front-rail-post')
            self.cube((sign*6.68,-6.15,1.48),(6.8,.15,.13),'stone base','estimated-front-rail-top')
        self.features.append({'kind':'estimated-front-platform-and-porch','porch_columns':6,'stair_steps':4,'full_photo_grid_accepted':False})
        front = self.facade(0, 'assumed-front')
        windows = [box(c - P['window_width'] / 2, P['window_bottom'], c + P['window_width'] / 2, P['window_top'])
                   for c in self.window_centres]
        wall_top = self.roofz(P['wall_depth'] / 2) - .08
        front.wall(P['base_height'], wall_top,
                   [box(-P['door_width'] / 2, P['door_bottom'], P['door_width'] / 2, P['door_top']), *windows],
                   P['wall_thickness'], 'red brown timber')
        self.doors(front)
        # Build each frame and grid as one closed solid with genuine cut-out panes.
        # No ornamental carving or column/corridor layout is inferred from old text.
        from shapely.ops import unary_union
        for i, (centre, opening) in enumerate(zip(self.window_centres, windows)):
            x0, z0, x1, z1 = opening.bounds
            inner = opening.buffer(-.09, join_style=2)
            bars = [box(x0 + P['window_width'] * k / P['window_columns'] - .028, z0,
                        x0 + P['window_width'] * k / P['window_columns'] + .028, z1)
                    for k in range(1, P['window_columns'])]
            bars += [box(x0, z0 + (z1 - z0) * k / P['window_rows'] - .027,
                         x1, z0 + (z1 - z0) * k / P['window_rows'] + .027)
                     for k in range(1, P['window_rows'])]
            panes = inner.difference(unary_union(bars))
            front.prism(opening.buffer(-.025, join_style=2).difference(panes), -.27, -.16,
                        'red brown timber', f'estimated-window-{i}-frame-grid')
            front.prism(inner, -.34, -.32, 'inset shadow', f'estimated-window-{i}-backing')
            front.box(centre, P['window_bottom'] - .08, P['window_width'] + .16, .12, .28, -.02,
                      'stone base', 'estimated-window-sill')
            self.features.append({'kind': 'estimated-window', 'centre_x_m': centre,
                                  'opening_m': [P['window_width'], P['window_top'] - P['window_bottom']],
                                  'grid': [P['window_columns'], P['window_rows']], 'backing_depth_m': .33})
        self.facade(2, 'unobserved-rear').wall(P['base_height'], wall_top, [], P['wall_thickness'], 'plaster')
        half_depth = P['wall_depth'] / 2
        for edge in [1, 3]:
            facade = self.facade(edge, 'assumed-side-gable')
            outline = Polygon([(-half_depth, P['base_height']), (half_depth, P['base_height']),
                               (half_depth, wall_top), (0, P['ridge_under_cap'] - .08), (-half_depth, wall_top)])
            facade.wall(P['base_height'], P['ridge_under_cap'] - .08, [], P['wall_thickness'], 'plaster', outline=outline)
        half_width = P['wall_width'] / 2
        # Butt joints hide all strip end caps inside adjoining front/rear strips.
        for x in [-half_width + .06, half_width - .06]:
            self.cube((x, 0, .85), (.24, P['wall_depth'] - .36, .26), 'stone base', 'side-skirting')
        self.cube((0, half_depth - .06, .85), (P['wall_width'] + .12, .24, .26), 'stone base', 'rear-skirting')
        outside = half_width + .06
        inside = P['door_width'] / 2 + .10
        for sign in [-1, 1]:
            self.cube((sign * (outside + inside) / 2, -half_depth + .06, .85),
                      (outside - inside, .24, .26), 'stone base', 'front-side-skirting')
        self.features.append({'kind': 'five-assumed-equal-front-divisions', 'bay_width_m': self.bay_width,
                              'equal_spacing_estimated': True, 'division_count_is_documented': False, 'estimated_front_porch': True, 'historical_five_bays_is_not_modern_grid_proof': True})

    def finish(self):
        self.walls()
        self.roof()
        for part in self.b.parts:
            vertices = np.array(part['vertices'])
            triangles = np.array(part['triangles'])
            volume = np.einsum('ij,ij->i', vertices[triangles[:, 0]],
                               np.cross(vertices[triangles[:, 1]], vertices[triangles[:, 2]])).sum() / 6
            assert abs(volume) > 1e-10, part['label']
            if volume < 0:
                part['triangles'] = [(a, c, b) for a, b, c in triangles]
        return self

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--lod', action='store_true')
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    model = MinglunHall(args.lod).finish()
    role = 'lod' if args.lod else 'raw'
    result = model.b.save(args.out / f'{ID}-{role}.glb', metadata={
        'id': ID, 'name': '崇明学宫明伦堂（文字尺寸参照候选）',
        'documentary_dimensions_m': [20.6,12.7,10.37], 'alternate_documented_height_m':10.5, 'chosen_model_height_m':10.37, 'historical_bays':5, 'modern_bays_verified':False,
        'status': 'Text-dimension candidate with partly occluded photo context; no full photographic or geographic acceptance',
        'documented': 'Minglun Hall north of Yimen; old museum page3_3 records width20.6m,depth12.7m,height10.37m,area261.6m2,construction1624 and repair2001. Official2021 height10.5m remains an unresolved alternate.',
        'local_axes': 'Local X20.6 and Y12.7 assigned to base; source measurement endpoints and metric orientation unspecified. Actual front placement unverified.',
        'endpoints': 'Wall/column/base/eave measurement limits unspecified; roof overhang increases total bounds.',
        'historical_only': '1624 start and historical five bays/depth over three zhang do not establish the current facade or metric column grid.',
        'estimated': 'Five equal front divisions, central closed double door, four lattice windows, six porch columns, four steps and simple rails, planar gable roof and tile count, rear/sides and materials are authored estimates. Historical five bays is not modern bay count proof.',
        'code_reuse': 'Facade/roof tooling adapted from Ruxue Gate with independent dimensions and estimated porch/openings. Code reuse is not evidence of matching real buildings.',
        'photo_scope': 'Captioned Minglun courtyard photo only partly shows the hall behind trees; opening counts and roof type are not photo-verified. Unlabelled Chongxian Hall image not used. No full photographic reconstruction acceptance.',
        'area_check': '20.6 x12.7=261.62m2 calculated; museum reported261.6m2 retained separately, not proof of measurement endpoints.',
        'omitted': 'Side corridors, courtyard trees, exact calligraphy/carvings/brackets, interiors and measured courtyard paving',
    })
    (args.out / f'{role}-features.json').write_text(json.dumps(model.features, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'part_summary'}))
