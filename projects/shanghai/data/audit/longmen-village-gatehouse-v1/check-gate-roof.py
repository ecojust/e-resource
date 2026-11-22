"""Check the first, outward-facing triangle against the photographed gate eaves."""
from pathlib import Path
from hashlib import sha256
import argparse
import json
import runpy
import sys
import tempfile
import numpy as np

AUDIT = Path(__file__).resolve().parent
PROJECT = AUDIT.parents[2]
SOURCE = PROJECT / 'source/precise/huangpu-longmen-village-gatehouse/source'
sys.path[:0] = [str(SOURCE), str(PROJECT / 'source/precise/hongkou-general-post-office/source/common')]
from photo_architecture import Builder
from gate_roof import ROOF_MATERIALS, add_roof

read_glb = runpy.run_path(str(PROJECT / 'data/audit/postal-office-v1/independent-glb-review-helpers.py'))['load_triangles']


def test_model(path):
    triangles, material_ids, materials, _ = read_glb(path)
    e1 = triangles[:, 1] - triangles[:, 0]
    e2 = triangles[:, 2] - triangles[:, 0]
    normals = np.cross(e1, e2)
    normals /= np.linalg.norm(normals, axis=1)[:, None]
    records = []

    def ray(name, origin, direction, allowed=None, altitude=None):
        origin = np.asarray(origin, dtype=float)
        direction = np.asarray(direction, dtype=float)
        direction /= np.linalg.norm(direction)
        cross = np.cross(direction, e2)
        determinant = np.einsum('ij,ij->i', e1, cross)
        inv = np.divide(1., determinant, out=np.zeros_like(determinant), where=np.abs(determinant)>1e-10)
        offset = origin - triangles[:, 0]
        u = np.einsum('ij,ij->i', offset, cross)*inv
        q = np.cross(offset, e1)
        v = (q @ direction)*inv
        distance = np.einsum('ij,ij->i', e2, q)*inv
        hits = np.flatnonzero((abs(determinant)>1e-10) & (u>=-1e-7) & (v>=-1e-7) &
                              (u+v<=1+1e-7) & (distance>1e-5))
        first = None
        if len(hits):
            nearest = float(np.min(distance[hits]))
            # When a ray meets a shared edge, use the most directly facing triangle at that distance.
            near = hits[abs(distance[hits]-nearest)<1e-6]
            index = near[np.argmax(-normals[near] @ direction)]
            first = {
                'material': materials[material_ids[index]],
                'point': np.round(origin + direction*nearest, 5).tolist(),
                'normal': np.round(normals[index], 5).tolist(),
                'outward_alignment': float(-normals[index] @ direction)
            }
        if allowed is None:
            passed = first is None
        else:
            passed = first is not None and first['material'] in allowed and first['outward_alignment']>1e-4
        if altitude and first is not None:
            passed = passed and altitude[0] <= first['point'][2] <= altitude[1]
        records.append(dict(name=name, origin=origin.tolist(), direction=direction.tolist(),
                            expected_materials=allowed, first=first, passed=bool(passed)))

    head = ['Longmen grey fired tile ends']
    square = ['Longmen weathered timber ends']
    tile = ['Longmen charcoal cover tiles', 'Longmen weathered pan tiles']
    down = (0, 0, -1)
    # Front elevation references use independent street measurements, without calling the roof generator.
    fronts = [('upper', -2.77, 2.77, 19, 12.86, .79, True, True, (.255,.418,.582,.745)),
              ('west', -3.73, -1.585, 8, 11.49, .72, True, False, (.56,.92)),
              ('east', 1.585, 3.73, 8, 11.49, .72, False, True, (.08,.44))]
    for label, left, right, count, level, lift, west, east, squares in fronts:
        def elevation(u):
            return level + lift*(west*max(0, 1-2*u)**4 + east*max(0, 2*u-1)**4)
        for i in range(count):
            u = (i+.5)/count
            ray(f'{label} street tile head {i+1}', (left+(right-left)*u,-2,elevation(u)+.018), (0,1,0), head)
        for i,u in enumerate(squares):
            ray(f'{label} projecting square timber {i+1}', (left+(right-left)*u,-2,elevation(u)-.22), (0,1,0), square)
    for name,x,limits in [('middle',0,(15.10,15.16)), ('west',-2.73,(13.18,13.36)), ('east',2.73,(13.18,13.36))]:
        ray(name+' ridge', (x,2.045,19), down, ['Longmen grey ridge mortar'], limits)
    for name,y in [('street',.52), ('back',3.57)]:
        ray(name+' central cover tile', (0,y,18), down, [tile[0]])
        ray(name+' open tile channel', (.107,y,18), down, [tile[1]])
        for side,x in [('west',-2.8),('east',2.8)]:
            ray(name+' '+side+' roof', (x,y,18), down, tile)
    for x in (-2.93,-1.11,.12,2.72):
        ray('eave underside '+str(x), (x,-.20,7), (0,0,1),
            ['Longmen dark timber','Longmen dark eave underside','Longmen weathered timber ends'])
    for side,x,y in [('west',-3.85,-.90),('east',3.85,-.86),('street',.1,-1.20),('back',-.5,4.72)]:
        ray(side+' exterior clearance', (x,y,18), down)
    assert len(records)==62
    return dict(passed=all(rec['passed'] for rec in records), sha256=sha256(path.read_bytes()).hexdigest(),
                triangles=len(triangles), xyz_min=triangles.min(axis=(0,1)).tolist(),
                xyz_max=triangles.max(axis=(0,1)).tolist(), probes=records)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=AUDIT/'roof-surface-checks.json')
    args = parser.parse_args()
    cases = {}
    with tempfile.TemporaryDirectory() as tmp:
        for variant, lod in [('near',False), ('far',True)]:
            b = Builder(ROOF_MATERIALS)
            add_roof(b,lod)
            path = Path(tmp)/(variant+'.glb')
            b.save(path, {'model':'roof QA','axes':'X east, Y inward, Z up'})
            cases[variant] = test_model(path)
    result = dict(passed=all(test['passed'] for test in cases.values()), scope='street gate roof module',
                  module_sha256=sha256((SOURCE/'gate_roof.py').read_bytes()).hexdigest(), inspections=cases)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
    assert result['passed']


if __name__=='__main__':
    main()
