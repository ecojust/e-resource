"""Ray-test all three Customs Club GLBs against the porch, casements, dormers, turret and roof."""
import argparse
import math
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile


SOURCE = Path(__file__).resolve().parent
PROJECT = SOURCE.parents[2]
MODEL = 'xuhui-fenyang-customs-club'
READER = PROJECT / 'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK = PROJECT / 'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER = PROJECT / 'vendor/meshopt_decoder.module.js'
SerialScene = runpy.run_path(str(READER))['SerialScene']


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def probes(mesh,role):
    scene=SerialScene(mesh)
    records=[]
    def shot(label,origin,direction,material,depth,tolerance=.045):
        hit=scene.ray(origin,direction,8)
        passed=hit is None if material is None else hit is not None and hit['material']==material and abs(hit['distance_m']-depth)<tolerance
        records.append({'label':label,'from':origin,'direction':direction,'expected_material':material,'expected_distance_m':depth,'first_hit':hit,'passed':passed})
    # Fixed local-metre witnesses verify the photograph-derived profiles in each export.
    checks = [
        ('south square veranda post 1', [-8.7, -9.5, 3.29], [0, 1, 0], 'cream-painted porch columns and brackets', 1.615),
        ('south square veranda post 2', [-4.34, -9.5, 3.29], [0, 1, 0], 'cream-painted porch columns and brackets', 1.615),
        ('south square veranda post 3', [0, -9.5, 3.29], [0, 1, 0], 'cream-painted porch columns and brackets', 1.615),
        ('south square veranda post 4', [4.34, -9.5, 3.29], [0, 1, 0], 'cream-painted porch columns and brackets', 1.615),
        ('south square veranda post 5', [8.7, -9.5, 3.29], [0, 1, 0], 'cream-painted porch columns and brackets', 1.615),
        ('east sheltered porch floor', [5.6, -6.7, 2.24], [0, 0, -1], 'weathered porch boards', 1.215),
        ('west sheltered porch floor', [-6.4, -6.7, 2.24], [0, 0, -1], 'weathered porch boards', 1.215),
        ('central stair tread', [0.27, -8.62, 2.22], [0, 0, -1], 'grey stone and brick plinth', 1.728),
        ('open garden ahead of central stair', [0.27, -10.25, 4.66], [0, 0, -1], None, 0),
        ('faded green panels in central enclosed porch', [-1.22, -9.2, 1.68], [0, 1, 0], 'dull green door panel', 1.65),
        ('green door upper glazing', [-1.18, -9.2, 3.52], [0, 1, 0], 'recessed grey-green glazing', 1.87),
        ('east central enclosure glass', [1.21, -9.2, 2.22], [0, 1, 0], 'recessed grey-green glazing', 1.87),
        ('weatherboard pier near a central casement', [1.83, -8.9, 2.44], [0, 1, 0], 'weathered pale-grey horizontal boarding', 1.25),
        ('east clapboard wall', [10.88, 0.76, 3.7], [-1, 0, 0], 'weathered pale-grey horizontal boarding', 2.01),
        ('front multi-sided dormer pane', [0.25, -8.43, 7.16], [0, 1, 0], 'recessed grey-green glazing', 2.21),
        ('front dormer sash', [-0.357, -8.43, 7.16], [0, 1, 0], 'faded green painted wooden sash', 2.05),
        ('near eastern dormer pane', [9.8, -2.22, 7.12], [-1, 0, 0], 'recessed grey-green glazing', 2.41),
        ('far eastern dormer pane', [9.8, 2.78, 7.12], [-1, 0, 0], 'recessed grey-green glazing', 2.41),
        ('single clear western dormer pane', [-9.8, 0.74, 7.12], [1, 0, 0], 'recessed grey-green glazing', 2.43),
        ('square northwest turret window', [-10.4, 5.55, 6.97], [1, 0, 0], 'recessed grey-green glazing', 2.035),
        ('northwest turret roof', [-7.48, 5.73, 10.55], [0, 0, -1], 'grey diamond-patterned roof sheets', 1.922),
        ('flat roof cap', [1.26, 0.87, 11.3], [0, 0, -1], 'dark weatherproof flat roof', 2.97),
        ('south sheet slope away from dormer', [-4.33, -6.36, 9.61], [0, 0, -1], 'grey diamond-patterned roof sheets', 3.389),
        ('central dormer cover', [0.61, -5.62, 10.25], [0, 0, -1], 'grey diamond-patterned roof sheets', 1.929),
        ('lawn near east veranda corner', [10.3, -8.98, 3.52], [0, 0, -1], None, 0),
    ]
    for label, origin, direction, material, distance in checks:
        shot(label,origin,direction,material,distance)
    return {'passed':all(v['passed']for v in records),'probe_count':len(records),'probes':records}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest',type=Path,default=PROJECT/'assets/models/candidates'/MODEL/'manifest.json')
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    manifest=json.loads(args.manifest.read_bytes())
    assert manifest['id']==MODEL
    results={}
    with tempfile.TemporaryDirectory() as directory:
        for role in ('raw','full','lod'):
            asset=manifest['assets'][role]
            path=args.manifest.parent/asset['file']
            assert path.stat().st_size==asset['bytes'] and digest(path)==asset['sha256']
            decoded=path
            if role!='raw':
                decoded=Path(directory)/(role+'.glb')
                subprocess.run(['node',UNPACK,path,decoded,DECODER],check=True,stdout=subprocess.DEVNULL)
            results[role]=dict(sha256=asset['sha256'],file=path.name,**probes(decoded,role))
    report={'id':MODEL,'script_sha256':digest(Path(__file__)),'manifest_sha256':digest(args.manifest),
            'decoder_sha256':digest(DECODER),'reader_sha256':digest(READER),'results':results,
            'scope':'Checks only the sampled physical geometry in local axes; placement and viewing use independent records.'}
    args.out.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
    for role,test in results.items():
        print(role,'passed' if test['passed'] else [r for r in test['probes'] if not r['passed']])
    return all(r['passed'] for r in results.values())


if __name__=='__main__':
    raise SystemExit(0 if main() else 1)
