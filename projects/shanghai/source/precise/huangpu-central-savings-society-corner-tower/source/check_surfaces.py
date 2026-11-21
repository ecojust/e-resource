"""Trace the steel gate apertures, sash bars, stone fins, and terrace roofs.

Probe coordinates are in metres in the corner reference frame. Actual decoded
GLB surfaces are tested independently, with a fixed positive direction toward
the building on the frontal measurements.
"""
import numpy as np
STONE='Warm grey dressed stone'
LIGHT='Light arris and crown'
JOINT='Weathered stone joint'
SPANDREL='Fluted spandrel'
WINDOW='Smoked blue steel sash glazing'
STEEL='Oxidised window frames'
IRON='Dark patterned metal leaves'
LOCK='Metal raised medallions'
SHADOW='Entrance interior shade'

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

    def wall(label,x,z,material,y,delta=.007):
        straight(label,x,z,material,[y-delta,y+delta])
    sills = [8.45,11.30,14.48,17.86,20.94,24.18,27.53,29.62]
    heights = [1.73,1.90,1.91,1.91,1.94,1.97,1.49,1.69]
    for idx,(z,h) in enumerate(zip(sills,heights)):
        rows=5 if idx>=6 else 4
        for column,x in enumerate((-1.07,0,1.07)):
            root=f'row {idx+1} / column {column+1}'
            wall(root+' glass',x+.134,z+h*(.57/rows),[WINDOW],.36)
            wall(root+' lower horizontal bar',x+.134,z+h/rows,[STEEL],.294)
            wall(root+' upper rail',x-.173,z+h*(rows-1)/rows,[STEEL],.294)
            wall(root+' jamb',x-.366,z+h*.64,[STEEL],.294)
        for sign in (-1,1):
            wall(f'rib {sign}:{idx+1}',sign*.537,z+.63,[LIGHT],-.253)
    for sign in (-1,1):
        c=sign*.804
        for row,base,step in [('upper',3.99,.307),('lower',1.19,.295)]:
            for j in (0,2,4):
                for col in (0,1,2,3):
                    x=c+(col-1.5)*.337
                    wall(f'{sign} {row} open cell {j}:{col}',x+.090,base+j*step,[SHADOW],.626)
                    wall(f'{sign} {row} bridge {j}:{col}',x,base+j*step,[IRON],.397)
        wall(f'medallion {sign} core',c,3.15,[IRON],.363)
        wall(f'medallion {sign} rim',c+.190,3.15,[LOCK],.333)
        wall(f'rectangular door border {sign}',c+.757,2.54,[LOCK],.366)
        for j in (0,2,4,6,8):
            if sign==-1:
                wall(f'independent rectangular transom {j}',-1.435+j*.315,6.10,[SHADOW],.624)
        for z in (1.93,4.41,6.10):
            wall(f'jamb {sign}:{z}',sign*1.91,z,[STONE],-.158)
        # Skyward pins are masonry and have actual width at their very tops.
        test('stepped rib cap '+str(sign),(sign*.537,-.090,39.),(0,0,-1),[STONE],(3.352,3.369))
    for i in range(4):
        x=.55;y=-(.59-.156*i)
        test('street step '+str(i+1),(x,y,1.4),(0,0,-1),[STONE,LIGHT],(1.4-(i+1)*.116-.005,1.4-(i+1)*.116+.005))
    for x,y in [(-5.15,2.71),(5.38,3.07)]:
        test('roof of upper short return '+str(x),(x,y,37),(0,0,-1),[STONE],(11.44,11.46))
    for x,y in [(-6.70,3.18),(6.29,3.66)]:
        test('roof of lower short return '+str(x),(x,y,37),(0,0,-1),[STONE],(16.84,16.86))
    failures=[r for r in results if not r['passed']]
    if failures:raise ValueError('Unexpected real surfaces '+str(failures))
    return {'passed':True,'triangles':len(faces),'rays':results}
