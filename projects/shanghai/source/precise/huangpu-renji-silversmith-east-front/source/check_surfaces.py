"""Check actual first surfaces and twelve through-spaces between carved stone balusters."""
import numpy as np
GLASS='Smoky glass'
SASH='Dark red timber sash'
STONE='Cream stone and mouldings'
HONEY='Ochre relief highlights'
PLASTER='Pale weathered shop stucco'
BOARD='Boarded street opening'
METAL='Southern shutter'
DARK='Grey recessed stone'
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
    for sign in (-1,1):
        x=sign*3.773
        for z,span,height in [(6.60,1.36,1.66),(9.99,1.42,1.46)]:
            boarded=sign==1 and z<9.
            for dx in (-.24,.24):
                for fraction in (.15,.45,.82):
                    wall(f'{sign} wing window {z} {dx} {fraction}',x+dx,z+height*fraction,
                         [BOARD if boarded else GLASS],.205)
            if not boarded:
                wall(f'{sign} timber centre {z}',x,z+.24,[SASH],.135)
                wall(f'{sign} timber crossbar {z}',x+.17,z+height/3,[SASH],.135)
            wall(f'{sign} full stone sill {z}',x+.16,z-.102,[STONE],-.252)
            wall(f'{sign} framed apron {z}',x,z-.35,[STONE],-.102)
        wall(f'{sign} pilaster cap',sign*2.39,11.702,[STONE],-.172)
        wall(f'{sign} highest shoulder',sign*5.36,12.465,[STONE],-.510)
        wall(f'{sign} outer pier square',sign*5.34,13.57,[DARK],-.243)
        for j,xrail in enumerate(np.linspace(2.90,4.93,6)):
            straight(f'{sign} turned baluster {j}',sign*xrail,13.09,[STONE],[-.19,-.169])
        for j,xrail in enumerate(np.linspace(2.90,4.93,6)[:-1]):
            test(f'{sign} daylight between balusters {j}',(sign*(xrail+.201),-2.,13.12),(0,1,0),[],(0,0))
        wall(f'{sign} roof rail end gap',sign*2.775,13.18,[],0)
    for x in (-1.74,0,1.74):
        for dx in (-.115,.115):
            wall(f'upper small light {x} {dx}',x+dx,10.36,[GLASS],.205)
            wall(f'upper small light bar {x} {dx}',x+dx,10.614,[SASH],.135)
    for x in (-1.31,1.31):
        wall(f'bow side light {x}',x+.105,8.35,[GLASS],.205)
    for x in (-.62,-.22,.22,.62):
        wall(f'bow central glass {x}',x,8.40,[GLASS],.204)
        wall(f'bow transom {x}',x,9.259,[SASH],.128)
    for x in (-.44,0,.44):
        wall(f'bow central timber {x}',x,8.40,[SASH],.128)
    wall('central arch glass above crossbar',.19,9.48,[GLASS],.204)
    wall('raised key over bow',.02,9.89,[HONEY],-.355)
    wall('main shallow crown arch',0,13.84,[STONE],-.474)
    wall('ground arch below central windows',0,6.01,[STONE],-.184)
    wall('upper central blank tablet',.19,15.02,[STONE],-.088)
    wall('two actual closed street doors',.36,1.28,[METAL],-.015)
    wall('street-level door seam',0,1.28,[PLASTER],.008)
    for z in (1.05,2.17):
        straight(f'southern shutter {z}',-3.74,z,[METAL],[.11,.16])
    test('flat protected shop crest',(0,-.07,19.),(0,0,-1),[STONE],(2.80,2.82))
    failures=[r for r in results if not r['passed']]
    if failures:raise ValueError(str([(x['name'],x['material'],x['distance_m'],x['expected'],x['interval_m'])for x in failures]))
    return {'passed':True,'triangles':len(faces),'rays':results}
