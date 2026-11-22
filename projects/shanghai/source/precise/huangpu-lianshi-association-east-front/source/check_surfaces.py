"""Check the actual first surfaces of the three delivered meshes, including the open rail panels."""
import numpy as np
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
        passed = (material in expected and interval[0] <= length <= interval[1]) if length is not None else not expected
        results.append({'name': name, 'origin': list(start), 'direction': list(direction), 'material': material,
                        'distance_m': length, 'expected': sorted(expected), 'interval_m': interval, 'passed': passed})

    def straight(label, x, z, acceptable, front_y):
        test(label, (x, -2., z), (0., 1., 0.), acceptable, [2.+front_y[0], 2.+front_y[1]])

    def wall(label,x,z,material,y,delta=.007):
        straight(label,x,z,material,[y-delta,y+delta])
    axes=(-11.006,-7.294,-3.691,0.,3.691,7.294,11.006)
    for i,x in enumerate(axes):
        sign=1 if x<0 else -1
        w=2.64 if i==3 else 1.83
        extent=.80 if i==3 else .71
        for dx in (-.18,.22):
            wall(f'{i+1} upper casement {dx}',x+dx,10.86,['Blue grey street glass'],.256)
            wall(f'{i+1} upper transom {dx}',x+dx,11.44,['Pale transom glass'],.237)
            wall(f'{i+1} upper hood {dx}',x+dx,11.85,['Limestone mouldings'],-.179)
            if distant or i not in (5,6):
                wall(f'{i+1} lower casement {dx}',x+dx,7.15,['Blue grey street glass'],.256)
            wall(f'{i+1} lower hood {dx}',x+dx,8.26,['Limestone mouldings'],-.179)
            wall(f'{i+1} shop glass {dx}',x+dx,2.15,['Blue grey street glass'],.316)
        wall(f'{i+1} balcony coping',x,10.006,['Limestone mouldings'],-extent-.12)
        wall(f'{i+1} balcony projecting slab',x,9.01,['Limestone mouldings'],-extent-.08)
        # The two rays cross the same panel at mid-height, one on the X and
        # the other in a real void, with only recessed glazing visible behind.
        cell=w/(3 if i==3 else 2)
        cx=x-w/2+cell/2
        wall(f'{i+1} crossed stone rail',cx,9.57,['Carved grey balcony rail'],-extent-.065)
        wall(f'{i+1} open centre beside crossed rail',cx+.16,9.57,['Blue grey street glass'],.256)
    for x in (-12.89,-9.20,-5.50,-1.85,1.85,5.50,9.20,12.89):
        wall(f'{x} capital abacus',x,12.50,['Limestone mouldings'],-.194)
    for x in (-9.1357,9.1357):
        for dx in (-1.73,1.73):
            wall(f'{x} rooftop casement {dx}',x+dx+.15,15.22,['Blue grey street glass'],.583)
        wall(f'{x} gable plaster',x+.24,17.79,['Warm grey plaster'],.394)
    for x in (-.18,.18):
        wall(f'tower window {x}',x,15.87,['Blue grey street glass'],.651)
    wall('central pediment field',.07,14.39,['Warm grey plaster'],-.16)
    wall('terrace centre panel',.31,5.47,['Warm grey plaster'],-.795)
    failures=[v for v in results if not v['passed']]
    if failures:
        raise ValueError(f'{len(failures)} failed first surfaces: {failures[:8]}')
    return {'passed':True,'triangles':len(faces),'rays':results}
