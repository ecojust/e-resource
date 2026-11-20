"""Probe the actual decoded render meshes from the garden at fixed metric points."""
import argparse
import hashlib
import json
from pathlib import Path
import runpy
import subprocess
import tempfile



HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
ID = 'jingan-country-hospital'
DECODER = PROJECT / 'vendor/meshopt_decoder.module.js'
READER = PROJECT / 'data/audit/postal-office-v1/independent-glb-review-helpers.py'
SerialScene = runpy.run_path(str(READER))['SerialScene']
UNPACK = PROJECT / 'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check(path):
    scene = SerialScene(path)
    rows = []

    def ray(label,x,z,material,near,far):
        hit = scene.ray([x,-2,z], [0,1,0], length=10)
        y = hit['point_enu_m'][1] if hit else None
        mat = hit['material'] if hit else None
        passed = (y is None) if material is None else (mat==material and near<=y<=far)
        rows.append(dict(probe=label,x_m=round(x,4),z_m=round(z,4),expected_material=material,
                         expected_y_m=[near,far] if material else None,first_y_m=y,
                         first_material=mat,passed=passed))

    # Expected material and depth tolerances in local metres: no builder imported.
    for side,sign in [('west',-1),('east',1)]:
        for n,offset in enumerate([10.75,14.64,18.53,22.42,26.32],1):
            ray(f'{side} arcade {n}: clear to shadow back',sign*offset,1.47,'reveal',4.5,4.75)
            ray(f'{side} window {n}: recessed middle storey',sign*(offset+.34),7.9,'window glass',3.38,3.58)
        for n,offset in enumerate([30.32,33.52,36.76],1):
            ray(f'{side} end portico {n}: lower arched glazing',sign*(offset+.24),1.12,'window glass',.52,.67)
        ray(f'{side} pediment: triangular field',sign*33.5,16.23,'cream render',-.23,-.04)
        ray(f'{side} pediment: above ridge',sign*33.5,17.6,None,0,0)
    ray('central upper balcony: clear to glass',.31,8.38,'window glass',1.95,2.14)
    ray('central gable: tympanum',.30,17.70,'cream render',0.0,.13)
    ray('central gable: above ridge',.30,19.14,None,0,0)
    return dict(triangles=len(scene.tri),probes=rows,passed=all(r['passed'] for r in rows))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest',type=Path,default=PROJECT/'assets/models/candidates'/ID/'manifest.json')
    parser.add_argument('--out',type=Path,default=HERE/'surface-checks.json')
    args=parser.parse_args()
    manifest=json.loads(args.manifest.read_bytes())
    assert manifest['id']==ID
    results={}
    with tempfile.TemporaryDirectory() as directory:
        for role in ['raw','full','lod']:
            asset=manifest['assets'][role]
            path=args.manifest.parent / asset['file']
            assert path.stat().st_size==asset['bytes'] and digest(path)==asset['sha256']
            decoded=path
            if role!='raw':
                decoded=Path(directory)/(role+'.glb')
                subprocess.run(['node',UNPACK,path,decoded,DECODER],check=True,stdout=subprocess.DEVNULL)
            results[role]=dict(file=path.name,sha256=digest(path),**check(decoded))
    report=dict(id=ID,script_sha256=digest(Path(__file__)),manifest_sha256=digest(args.manifest),
                ray_reader_sha256=digest(READER),decoder_sha256=digest(DECODER),unpack_sha256=digest(UNPACK),results=results,
                scope='Garden-front projected ray tests in local coordinates; verifies sampled visible surfaces and voids in each serialized asset. No survey, map or indoor acceptance.')
    args.out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    for role,r in results.items():
        print(role, 'pass' if r['passed'] else [p for p in r['probes'] if not p['passed']])
    return all(r['passed'] for r in results.values())


if __name__=='__main__':
    raise SystemExit(0 if main() else 1)
