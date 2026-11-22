"""Intersect independently decoded triangles at posts, clear gallery bays, plaque and steps."""
from pathlib import Path
import numpy as np
from sign_lettering import lettering_shapes
from timber_gallery import AXES, BASE, DARK, GLASS, GOLD, INK, LOW_GLASS, PANEL, POST, RELIEF, RIDGE, SASH, SILL, TILE, roof_height
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

    for i,x in enumerate(AXES):
        for z in (.78,1.22,2.06,3.14,4.61,5.57,6.46):
            wall(f'廊柱 {i+1} {z}',x,z,{POST},-.108)
    for i,(a,b) in enumerate(zip(AXES,AXES[1:])):
        u=(a+b)/2
        for dx in (-.34,.32):
            wall(f'上层木裙板 {i+1} {dx}',u+dx,4.69,{SILL},-.003)
        wall(f'雕木横带实背 {i+1}',u+.08,3.67,{PANEL,RELIEF},-.095,.05)
        # Test the plane of the upper casement. A point on the glass pair is
        # intentionally offset from the fine lozenge and the structural post.
        for dx in (-.21,.36):
            straight(f'上层木窗 {i+1} {dx}',u+dx,5.846,{GLASS,SASH},[-.021,.040])
        if i!=3:
            straight(f'廊后下层格扇 {i+1}',u+.19,2.89,{LOW_GLASS,SASH},[1.45,1.55])
    for j in range(4):
        y=-(.28+(3.5-j)*.335)
        test(f'独立石阶 {j+1}',(.52,y,2.0),(0,0,-1),{BASE},[2-(j+1)*.11-.008,2-(j+1)*.11+.008])
    for x in [-9.8,-3.8,-1.4,0.,1.53,4.56,9.55]:
        test(f'柱廊通道 {x}',(x,.70,2.28),(0,0,-1),{BASE},[1.72,1.74])
    wall('中轴门扇间暗部',0,1.18,{DARK},1.96)
    for x in (-.62,.62):
        straight('中央双扇门 '+str(x),x,1.07,{PANEL,POST},[1.50,1.55])
    for char,shape in lettering_shapes('堂光香',1.63,.285,font=Path(__file__).with_name('HallPlaque.otf')):
        x,z=shape.representative_point().coords[0]
        test('右读匾字 '+char,(x,1.08,z+2.990),(0,1,0),{GOLD},[.30,.34])
    test('黑漆匾底',(-.98,1.08,3.00),(0,1,0),{INK},[.31,.34])
    test('金色匾边',(-1.078,1.08,3.00),(0,1,0),{GOLD},[.34,.39])
    for x in (-10.1,-4.6,0.,3.2,9.66):
        z=roof_height(x,.91)
        test('东坡瓦面 '+str(x),(x,.91,11.0),(0,0,-1),{TILE,RIDGE},[11-z-.12,11-z+.03])
    failures=[f for f in results if not f['passed']]
    if failures:
        raise ValueError(str([(r['name'],r['material'],r['distance_m'],r['interval_m'])for r in failures]))
    return {'rays':results,'passed':True}
