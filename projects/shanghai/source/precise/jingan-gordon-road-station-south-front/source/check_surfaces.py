"""Intersect solid windows, capitals, railings, coping and the recessed door on both model levels."""
import numpy as np
from courtyard import BRICK, HEADER, LIGHT, STONE, TIMBER, GLASS, DARK, ROOF, MORTAR, SOFFIT
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

    def cast(label,x,z,expected,expected_y,tolerance=.053):
        test(label,(x,-3.,z),(0,1,0),set(expected),[3+expected_y-tolerance,3+expected_y+tolerance])

    for side in (-1,1):
        for z in (.27,1.11,2.12):
            cast('Central stone jamb '+str((side,z)),side*1.17,z,[LIGHT],-.18)
        for x in (.19,.50):
            cast('Deep door leaf '+str((side,x)),side*x,1.31,[DARK],.937,.04)
        cast('Splayed portal reveal '+str(side),side*.83,1.30,[STONE],.354,.05)
        for z in (5.40,6.42,7.00,9.79,10.22,11.22):
            cast('Middle or upper timber casement '+str((side,z)),side*.31,z,[GLASS,TIMBER],.286,.085)
        for z in (1.19,6.17,10.03):
            cast('Raised outer brick strip '+str((side,z)),side*2.15,z,[HEADER],-.16)
        cast('Shoulder stone flute '+str(side),side*2.15,12.10,[LIGHT],-.27)
        for x in (2.76,3.42,4.21,5.02,5.44,6.22,6.73):
            for z in (4.38,8.62,5.29,9.53):
                cast('Courtyard rail '+str((side,x,z)),side*x,z,[TIMBER],.96,.06)
        for z in (5.43,7.45,8.78,10.20):
            cast('Red gallery pier '+str((side,z)),side*4.71,z,[BRICK],.82,.04)
        for z in (11.35,11.69,12.14):
            cast('Upper pierced stone order '+str((side,z)),side*4.71,z,[STONE],.83,.14)
        for x in (3.56,5.86):
            cast('Ground recessed glazing '+str((side,x)),side*x,1.36,[TIMBER,GLASS],1.25,.10)
            cast('View through middle arcade '+str((side,x)),side*x,6.13,[TIMBER,GLASS],3.335,.10)
            cast('View through upper arcade '+str((side,x)),side*x,10.27,[TIMBER,GLASS],3.335,.10)
        for x in (.30,1.,1.75,2.08):
            z=15.36-x/2.32*(15.3-12.43)
            test('Terracotta gable roof '+str((side,x)),(side*x,.60,19),(0,0,-1),{ROOF},[19-z-.035,19-z+.035])
    cast('Arched concrete hood',0,3.16,[LIGHT],-.27)
    cast('Peak brick tympanum',.14,14.02,[BRICK,MORTAR],0,.03)
    cast('Upper radiating keystone',.02,11.84,[STONE],-.20)
    failed=[f for f in results if not f['passed']]
    if failed:
        raise ValueError(str([(x['name'],x['material'],x['distance_m'])for x in failed]))
    return {'passed':True,'rays':results}
