"""Build reviewer-selected acceptance rays from disclosed feature coordinates.

Feature coordinates establish frame only. Independently selected multiple heights,
offsets, solid controls and analytic roof points are then tested against decoded GLB.
The author construction module is never imported or executed.
"""
from pathlib import Path
import hashlib, json, math, sys

directory, output = map(Path, sys.argv[1:3])
features = json.loads((directory / 'features.json').read_text())
disclosed = json.loads((directory / 'surface-probes.json').read_text())
rays, controls = [], []
def glb(p): return [p[0], p[2], -p[1]]
def add(name, point, normal, *, depth=None, interval=None, material=None,
        materials=None, distance=6, clear=False, setback=.6):
    origin = [point[i] + normal[i] * setback for i in range(3)]
    row = {'id': name, 'origin_glb': glb(origin),
           'direction_glb': glb([-n for n in normal]), 'max_distance_m': distance}
    if clear:
        row['expected_open'] = True
    else:
        if interval is not None: row['first_distance_range_m'] = [setback + x for x in interval]
        else: row.update(first_distance_m=setback+depth, tolerance_m=.002)
        if material: row['first_material'] = material
        if materials: row['first_material_in'] = materials
    rays.append(row)

portals = [f for f in features if f['kind'] == 'front_portal']
assert len(portals) == 3
for portal in portals:
    i = portal['index']; center = portal['facade_point_enu']; normal = portal['normal_enu']
    tangent = [-normal[1], normal[0], 0]
    # Includes the former erroneous 1.15m continuous facade-band height.
    for height in [.5, 1.10, 1.15, 1.20, 1.7, 2.8, 4.0, 4.75]:
        for lateral in ([-.65, 0, .65] if height < 4 else [0]):
            p = [center[j] + tangent[j] * lateral for j in range(3)]; p[2] = height
            name = f'portal-{i}-height-{height}-lateral-{lateral}'
            add(name+'-clear-prefix', p, normal, clear=True, distance=1.83)
            add(name+'-deep-termination', p, normal,
                interval=[2.24, 2.27] if i == 1 else [1.30, 1.83],
                materials=['interior shadow'] if i == 1 else ['interior shadow', 'painted window frame'])
    # Independent thin-grid opening and adjacent bar control at actual 2.38m.
    if i != 1:
        p = center[:]; p[2] = 2.38
        add(f'portal-{i}-grid-aperture', p, normal, depth=1.8, material='interior shadow')
        p = [p[j] + .15 * tangent[j] for j in range(3)]
        add(f'portal-{i}-grid-adjacent-bar', p, normal, depth=1.32, material='painted window frame')
    # Space below raised balcony is not a solid front box.
    p = [center[j] + normal[j]*.65 for j in range(3)]
    p[2] = 3.3
    add(f'balcony-{i}-standing-clear', p, [0,0,1], clear=True, distance=2.7, setback=0)
    p[2] = 8.0
    add(f'balcony-{i}-actual-deck', p, [0,0,1], interval=[1.80,1.84],
        material='warm stone', setback=0)
    controls.append({'id':f'below-projecting-balcony-{i}', 'point_local_xy':p[:2],
                     'expected_low_covered':False, 'expected_collision_covered':False,
                     'expected_full_covered':True})
    p = [center[j] - normal[j]*.6 for j in range(3)]
    controls.append({'id':f'actual-door-threshold-{i}', 'point_local_xy':p[:2],
                     'expected_low_covered':True, 'expected_collision_covered':True,
                     'expected_full_covered':True})

upper = [p for p in disclosed if p['label'].startswith('upper-octagonal-')]
assert len(upper) == 32
assert sum(p['normal'][1] > 0 for p in upper) == 16
assert sum(p['normal'][1] < 0 for p in upper) == 16
for i, item in enumerate(upper):
    add(f'upper-window-{i}-actual-glass', item['point'], item['normal'],
        depth=.32, material='recessed glass')
    p = item['point'][:]; p[0] += .95
    add(f'upper-window-{i}-adjacent-solid-wall', p, item['normal'], interval=[-.12,.01],
        materials=['gym brick','carved pale stone'])
lower = [p for p in disclosed if p['label'].startswith('lower-window-')]
assert len(lower) == 28
for i, item in enumerate(lower):
    add(f'lower-window-{i}-actual-recess', item['point'], item['normal'],
        depth=.32, material='recessed glass')
# All disclosed facade-door locations receive independent low/mid-height cuts,
# which cannot be replaced by a z0..2 footprint union.
doors = [p for p in disclosed if p['label'].startswith('side-door-') and p['kind']=='recess']
assert len(doors) == 4
for i, item in enumerate(doors):
    for h in [.5, 1.10, 1.15, 1.20, 1.7]:
        p = item['point'][:]; p[2] = h
        add(f'facade-door-{i}-height-{h}', p, item['normal'],
            interval=[.50,.54], material='dark stone')
for i, item in enumerate(disclosed):
    if item['label'].startswith(('tall-front-window-', 'back-', 'wing-small-window', 'front-small-vent-', 'front-core-upper-return-')):
        add(f'end-window-{i}', item['point'], item['normal'], depth=item['depth'], material=item['material'])
    if 'true-round-hole' in item['label']:
        add(f'balcony-perforation-{i}',item['point'],item['normal'],depth=1.11,material='warm stone')
        p=item['point'][:]; n=item['normal']; p[0]-=n[1]*.35; p[1]+=n[0]*.35
        add(f'balcony-solid-beside-perforation-{i}',p,n,depth=0,material='warm stone')

roof = next(f for f in features if f['kind'] == 'barrel_roof')
for dy in [-22.1,-16,-8,0,8,16,22.1]:
    height = roof['profile_center_height_m'] + math.sqrt(roof['radius_m']**2-dy**2)
    add(f'analytic-barrel-profile-{dy}', [-18.123, roof['profile_center_north_m']+dy, 35],
        [0,0,1], interval=[35-height-.26,35-height+.26],
        materials=['roof sheet','roof zinc','light roof frame'], distance=30, setback=0)
for x in [-7.2, .7, 18.7]:
    add(f'actual-skylight-{x}', [x,roof['profile_center_north_m']+.8,35], [0,0,1],
        interval=[14.7,15.3], materials=['roof glazing','light roof frame'], distance=25,setback=0)
controls += [
    {'id':'closed-main-hall-conservative-interior','point_local_xy':[0,0],
     'expected_low_covered':False,'expected_collision_covered':True,'expected_full_covered':True},
    {'id':'closed-front-foyer-conservative-interior','point_local_xy':[-31,0],
     'expected_low_covered':False,'expected_collision_covered':True,'expected_full_covered':True},
    {'id':'north-exterior-clear','point_local_xy':[0,23.3],
     'expected_low_covered':False,'expected_collision_covered':False,'expected_full_covered':False}]
out = {'schema':'jiangwan-gymnasium-independent-probes-v1',
       'method':'Reviewer-selected cuts, negative controls and analytic roof expectations; disclosed feature coordinates are a frame reference, not proof. Actual active-scene GLB triangles independently decide hits. No author construction module executed.',
       'input_coordinate_disclosures':[{'file':n,'sha256':hashlib.sha256((directory/n).read_bytes()).hexdigest()}
                                     for n in ['features.json','surface-probes.json']],
       'section_heights_m':[.12,.5,1.15,2,5,8,12,16,19],
       'rays':rays,'ground_controls':controls,
       'upper_window_positions_per_side':16,'lower_window_positions_per_side':14}
output.write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({'rays':len(rays),'ground_controls':len(controls)}))
