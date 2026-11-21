"""Trace actual outside surfaces of the Nanshi clock and adjoining street bays."""
import numpy as np
from math import cos, sin, pi
WALL = 'Buff ochre render'
COAT = 'Light ochre quoins'
LIME = 'Pale sand limestone'
STONE = 'Weathered stone mouldings'
GLASS = 'Grey green window glass'
FRAME = 'Dark sash'
METAL = 'Patinated roof'
RIB = 'Dark roof seams'
DIAL = 'Clock enamel'
MARK = 'Raised clock marks'
WOOD = 'Entrance timber'


def check_triangles(triangles, materials, distant):
    faces = np.asarray(triangles, dtype=np.float64)
    labels = np.asarray(materials)
    if faces.shape[1:] != (3, 3) or len(faces) != len(labels):
        raise ValueError('Provide one material name per real triangle in author coordinates')
    edge_one = faces[:, 1]-faces[:, 0]
    edge_two = faces[:, 2]-faces[:, 0]
    results = []

    def test(name, start, direction, expected, interval):
        d = np.asarray(direction, dtype=float)
        d /= np.linalg.norm(d)
        p = np.cross(d, edge_two)
        det = np.einsum('ij,ij->i', edge_one, p)
        front = det > 1e-10
        inv = np.divide(1, det, where=front, out=np.zeros_like(det))
        delta = np.array(start)-faces[:, 0]
        u = np.einsum('ij,ij->i', delta, p)*inv
        q = np.cross(delta, edge_one)
        v = q@d*inv
        t = np.einsum('ij,ij->i', edge_two, q)*inv
        valid = front & (u >= -1e-8) & (v >= -1e-8) & (u+v <= 1+1e-8) & (t >= 0.)
        hit = np.argmin(np.where(valid, t, np.inf))
        length = float(t[hit]) if valid.any() else None
        material = str(labels[hit]) if length is not None else None
        passed = material in expected and interval[0] <= length <= interval[1] if length is not None else False
        results.append({'name': name, 'origin': list(start), 'direction': list(direction), 'material': material,
                        'distance_m': length, 'expected': sorted(expected), 'interval_m': interval, 'passed': passed})

    def straight(label, x, z, acceptable, front_y):
        test(label, (x, -2., z), (0., 1., 0.), acceptable, [2.+front_y[0], 2.+front_y[1]])

    def frontal(label, x, z, accepted, face_y, local_y, epsilon=.009):
        y = face_y+local_y
        straight(label, x, z, accepted, [y-epsilon, y+epsilon])

    def wall(label, x, z, materials, y, slack=.01):
        straight(label, x, z, materials, (y-slack, y+slack))

    for side in (-1, 1):
        for i, u in enumerate((4.18, 6.91, 9.68)):
            x = side*u
            for name, sill, w, h, rise, depth, rows in [
                ('low arched opening', .76, 1.13, 3.15, .55, .34, 3),
                ('upper rectangular window', 6.07, 1.22, 2.69, 0, .27, 3),
                    ('top-floor light', 11.05, 1.17, 2.18, 0, .25, 2)]:
                prefix = f'{side}:{i} {name}'
                wall(prefix+' lower glazing', x+.16*w, sill+.65*(h-rise)/rows, [GLASS], depth)
                wall(prefix+' upright frame', x, sill+.69*(h-rise)/rows, [FRAME], depth-.079)
                wall(prefix+' horizontal sash', x+.18*w, sill+(h-rise)/rows, [FRAME], depth-.079)
            wall(f'wall pier {side}:{i}', x+.70, 5.75, [WALL], 0)
        wall(f'entrance pane {side}', side*.63, 2.65, [GLASS], .353)
        wall(f'door lower panel {side}', side*.62, 1.06, [WOOD], .28)
        wall(f'upper solid pier {side}', side*.756, 12.92, [COAT], .008)
        wall(f'upper dark quarter pane {side}', side*1.48, 12.40, [GLASS], .415)
        wall(f'suspended floral boss {side}', side*2.40, 14.31, [LIME], -.273)
        wall(f'suspended carved drop {side}', side*2.42, 13.88, [LIME], -.273)
        wall(f'central clock corner shaft inner {side}', side*1.83, 17.46, [LIME], 1.038, .025)
        wall(f'central clock corner shaft outer {side}', side*2.17, 17.46, [LIME], 1.038, .025)
        wall(f'cap slab {side}', side*1.83, 19.245, [STONE], .958, .02)
        wall(f'open carving on arched head {side}', side*2.063, 12.20, [STONE], -.16)
    wall('flat head of the rectangular center light', .31, 13.76, [COAT], -.006)
    wall('lowest external apron course', .38, 11.36, [STONE], -.447)
    for side in (-1, 1):
        wall('support under apron '+str(side), side*2.02, 10.86, [STONE], -.25)
    wall('upper middle glass', .26, 12.39, [GLASS], .415)
    wall('central window upright', 0, 12.37, [FRAME], .333)
    wall('arched window crossing transom', .36, 12.675, [FRAME], .355)
    wall('center carved keystone', 0, 14.36, [LIME], -.3545, .01)
    wall('clock pin', 0, 17.82, [MARK], .957, .010)
    wall('minute hand', .55*cos(-.665), 17.82+.55*sin(-.665), [MARK], .988, .008)
    wall('hour hand', .35*cos(2.11), 17.82+.35*sin(2.11), [MARK], .988, .008)
    for n in range(12):
        theta = pi/2-2*pi*n/12
        wall('enamel sector '+str(n), .45*cos(theta+.30), 17.82+.45*sin(theta+.30), [DIAL], 1.058)
        wall('clock tick '+str(n), .762*cos(theta), 17.82+.762*sin(theta), [MARK], 1.036, .008)
    for x in (-2.11, -1.75, 1.75, 2.11):
        test('rolled clock roof shoulder '+str(x), (x, 3.45, 25), (0, 0, -1), [METAL, RIB], (3.56, 4.62))
    for x in (-.99, .99):
        test('short flattened clock roof top '+str(x),
             (x, 3.43, 25), (0, 0, -1), [METAL, RIB], (3.455, 3.50))
    for x, top in [(0, 24.86), (.19, 22.607), (.30, 22.242), (.45, 22.036), (.56, 21.84)]:
        test('upper terminal at '+str(x), (x, 3.31, 26), (0, 0, -1), [RIB], (26-top-.035, 26-top+.035))
    for n in range(4):
        x = .41
        y = -1.12+.28*n+.12
        test('stone tread '+str(n), (x, y, 1), (0, 0, -1),
             [STONE], (1-.128*(n+1)-.006, 1-.128*(n+1)+.006))
    failures = [r for r in results if not r['passed']]
    if failures:
        raise ValueError('Unexpected surface '+str(failures))
    return {'passed': True, 'triangles': len(faces), 'rays': results}
