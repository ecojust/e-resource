"""Check the three meshes through the foyer portal, window openings and tower colonnade."""
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
    # Horizontal rays originate in the south court. Their first triangle must
    # belong to the measured surface, including the voids between tower posts.
    def south(name,x,z,materials,ylo,yhi):
        test(name,(x,-7.,z),(0.,1.,0.),materials,[ylo+7.,yhi+7.])
    for side in (-1,1):
        for i,x in enumerate((11.45,14.73,18.03,21.30)):
            south(f'{side} upper arch {i}',side*x+.21,16.50,['Recessed window glass'],.32,.35)
            surface=['Metal window frames'] if distant else ['Recessed window glass']
            extent=(.245,.265) if distant else (.32,.35)
            south(f'{side} documented glazing divisions in upper arch {i}',side*x+.21,16.33,surface,*extent)
            south(f'{side} lower narrow window {i}',side*x+.16,12.47,['Recessed window glass'],.32,.35)
            south(f'{side} masonry below windows {i}',side*x,8.51,['Warm cream wall'],-.005,.005)
        south(f'{side} blind entry recess',side*7.2,9.9,['Recessed warm stone'],.94,.96)
        south(f'{side} pavilion recessed masonry',side*19.4+.30,24.0,['Recessed warm stone'],1.47,1.52)
        south(f'{side} pavilion gold cap',side*19.4,29.2,['Gilded tower metal'],1.68,2.38)
    for x in (-3.2,-1.8,-.64,.68,1.82,3.25):
        south(f'recessed portal glazing {x}',x,6.55,['Recessed window glass'],2.55,2.57)
    for z,interval in [(76.,(21.8,22.03)),(90.,(22.3,22.7)),(104.2,(22.4,22.9))]:
        south(f'tapered gold spire {z}',0,z,['Gilded tower metal'],*interval)
    south('red star centre',0,112.09,['Red star glass'],22.78,22.81)
    for n in range(8):
        x=-21.85/2+.59+(21.85-1.18)*n/7
        south(f'open colonnade pier {n+1}',x,36.01,['Carved pale limestone'],11.46,11.66)
    for x in (-7.2,-3.6,0,3.6,7.2):
        south(f'five arched tower windows {x}',x+.19,25.23,['Recessed window glass'],10.80,10.86)
    for x in (-8.87,8.87):
        test(f'open atmospheric gap through gallery {x}',(x,-7.,36.54),(0,1,0),[],[0,75])
    for side in (-1,1):
        for x in (10.70,13.20,16.34,20.19):
            for z in (4.25,6.8,9.33,13.3):
                south(f'{side} south wall pier {x} at {z}',side*x,z,['Warm cream wall'],-.005,.005)
        for x in (5.20,9.02):
            south(f'{side} entrance shaft {x}',side*x,11.45,['Carved pale limestone'],-.86,-.59)
        for idx in range(7):
            x=side*(.45+.18*idx)
            y=-3.85+.52*idx+.12
            h=.36*(idx+1)
            test(f'{side} entrance tread {idx+1}',(x,y,h+.14),(0,0,-1),['Lower stone courses'],[.138,.142])
        for x in (14.22,17.33,20.14):
            south(f'{side} upper wing cornice {x}',side*x,18.09,['Carved pale limestone'],-.563,-.548)
    for z in (35.18,38.21):
        south(f'rear wall of tower gallery central window {z}',.23,z+.17,['Recessed window glass'],17.64,17.70)
    for x in (-3.48,-2.1,-.62,.67,2.1,3.48):
        south(f'recessed shoulder glass {x}',x,13.43,['Recessed window glass'],2.55,2.57)
    # Probe the actual mullions beside the sampled panes, including the
    # radiating fanlight members and the tower core's two middle transoms.
    for z in (35.18,38.21):
        south(f'tower central window transom {z}',.23,z,['Metal window frames'],17.60,17.62)
    for side in (-1,1):
        south(f'{side} lower window edge pane',side*11.11,13.3,['Recessed window glass'],.32,.35)
        south(f'{side} diagonal fanlight member',side*3.2,13.43,['Metal window frames'],2.44,2.46)
    failures=[x for x in results if not x['passed']]
    if failures:raise ValueError(f'{len(failures)} failed first surfaces: {failures[:12]}')
    return {'passed':True,'triangles':len(faces),'rays':results}
