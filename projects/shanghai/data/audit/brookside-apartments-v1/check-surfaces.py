"""Ray-test all three Brookside Apartments models against the roof arcade, projecting windows, garden steps, rooms and roofs."""
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
MODEL = 'jingan-brookside-apartments'
READER = PROJECT / 'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK = PROJECT / 'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER = PROJECT / 'vendor/meshopt_decoder.module.js'
SerialScene = runpy.run_path(str(READER))['SerialScene']


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def probes(mesh,role):
    scene=SerialScene(mesh)
    records=[]
    def shot(label,origin,direction,material,depth,maximum=8.,tolerance=.045):
        hit=scene.ray(origin,direction,maximum)
        passed=hit is None if material is None else hit is not None and hit['material']==material and abs(hit['distance_m']-depth)<tolerance
        records.append({'label':label,'from':origin,'direction':direction,'expected_material':material,'expected_distance_m':depth,'first_hit':hit,'passed':passed})
    # Fixed local-metre witnesses verify the photograph-derived profiles in each export.
    checks = [
        ('open garden roof arch 1', [-1.0687499999999996, 1.24, 25.43], [0, 1, 0], None, None, 2.8),
        ('open garden roof arch 2', [0.2112500000000015, 1.24, 25.43], [0, 1, 0], None, None, 2.8),
        ('open garden roof arch 3', [1.4912500000000009, 1.24, 25.43], [0, 1, 0], None, None, 2.8),
        ('open garden roof arch 4', [3.5812500000000007, 1.24, 25.96], [0, 1, 0], None, None, 2.8),
        ('open garden roof arch 5', [5.071250000000001, 1.24, 25.96], [0, 1, 0], None, None, 2.8),
        ('open garden roof arch 6', [6.561250000000001, 1.24, 25.96], [0, 1, 0], None, None, 2.8),
        ('open garden roof arch 7', [8.74125, 1.24, 25.96], [0, 1, 0], None, None, 2.8),
        ('open garden roof arch 8', [10.92125, 1.24, 25.96], [0, 1, 0], None, None, 2.8),
        ('open garden roof arch 9', [12.41125, 1.24, 25.96], [0, 1, 0], None, None, 2.8),
        ('open garden roof arch 10', [13.901250000000001, 1.24, 25.96], [0, 1, 0], None, None, 2.8),
        ('open garden roof arch 11', [15.99125, 1.24, 25.43], [0, 1, 0], None, None, 2.8),
        ('open garden roof arch 12', [17.271250000000002, 1.24, 25.43], [0, 1, 0], None, None, 2.8),
        ('open garden roof arch 13', [18.551250000000003, 1.24, 25.43], [0, 1, 0], None, None, 2.8),
        ('arcade pier -9.14', [-0.3987499999999997, 1.24, 25.69], [0, 1, 0], 'cream mineral render', 2.1544, 8.0),
        ('arcade pier -7.9', [0.8412500000000005, 1.24, 25.69], [0, 1, 0], 'cream mineral render', 2.1544, 8.0),
        ('arcade pier -4.415', [4.326250000000001, 1.24, 25.69], [0, 1, 0], 'cream mineral render', 2.1544, 8.0),
        ('arcade pier -2.925', [5.816250000000001, 1.24, 25.69], [0, 1, 0], 'cream mineral render', 2.1544, 8.0),
        ('arcade pier -1.13', [7.611250000000001, 1.24, 25.69], [0, 1, 0], 'cream mineral render', 2.1544, 8.0),
        ('arcade pier 1.12', [9.861250000000002, 1.24, 25.69], [0, 1, 0], 'cream mineral render', 2.1544, 8.0),
        ('arcade pier 2.925', [11.666250000000002, 1.24, 25.69], [0, 1, 0], 'cream mineral render', 2.1544, 8.0),
        ('arcade pier 4.415', [13.15625, 1.24, 25.69], [0, 1, 0], 'cream mineral render', 2.1544, 8.0),
        ('arcade pier 7.9', [16.64125, 1.24, 25.69], [0, 1, 0], 'cream mineral render', 2.1544, 8.0),
        ('arcade pier 9.14', [17.88125, 1.24, 25.69], [0, 1, 0], 'cream mineral render', 2.1544, 8.0),
        ('central raised pediment', [8.92125, 1.24, 28.38], [0, 1, 0], 'cream mineral render', 2.1544, 8.0),
        ('dark timber garden entrance', [9.02125, 1.24, 1.74], [0, 1, 0], 'brown garden entrance door', 2.4744, 8.0),
        ('axial sash 2', [8.961250000000001, 1.24, 5.68], [0, 1, 0], 'desaturated blue grey glass', 2.4744, 8.0),
        ('axial sash 3', [8.961250000000001, 1.24, 9.01], [0, 1, 0], 'desaturated blue grey glass', 2.4744, 8.0),
        ('axial sash 4', [8.961250000000001, 1.24, 12.34], [0, 1, 0], 'desaturated blue grey glass', 2.4744, 8.0),
        ('axial sash 5', [8.961250000000001, 1.24, 15.67], [0, 1, 0], 'desaturated blue grey glass', 2.4744, 8.0),
        ('axial sash 6', [8.961250000000001, 1.24, 18.85], [0, 1, 0], 'desaturated blue grey glass', 2.4744, 8.0),
        ('axial sash 7', [8.961250000000001, 1.24, 22.18], [0, 1, 0], 'desaturated blue grey glass', 2.4744, 8.0),
        ('projecting garden oriel (-8.12, 11.37)', [0.8612500000000016, 1.24, 12.37], [0, 1, 0], 'desaturated blue grey glass', 1.7944, 8.0),
        ('projecting garden oriel (-8.12, 14.7)', [0.8612500000000016, 1.24, 15.7], [0, 1, 0], 'desaturated blue grey glass', 1.7944, 8.0),
        ('projecting garden oriel (-8.12, 18.03)', [0.8612500000000016, 1.24, 19.03], [0, 1, 0], 'desaturated blue grey glass', 1.7944, 8.0),
        ('projecting garden oriel (8.12, 11.37)', [17.101249999999997, 1.24, 12.37], [0, 1, 0], 'desaturated blue grey glass', 1.7944, 8.0),
        ('projecting garden oriel (8.12, 14.7)', [17.101249999999997, 1.24, 15.7], [0, 1, 0], 'desaturated blue grey glass', 1.7944, 8.0),
        ('projecting garden oriel (8.12, 18.03)', [17.101249999999997, 1.24, 19.03], [0, 1, 0], 'desaturated blue grey glass', 1.7944, 8.0),
        ('small upper diamond below the centre arch', [8.74125,1.24,25.29], [0,1,0], None, None, 2.85),
        ('parapet between upper diamonds', [8.86625,1.24,25.29], [0,1,0], 'cream mineral render', 2.1544, 2.85),
        ('upper crest relief', [8.74125,1.24,28.47], [0,1,0], 'pale limestone moulding', 2.0754, 2.85),
        ('middle floor pierced balustrade opening', [13.41625,1.24,14.715], [0,1,0], 'cream mineral render', 2.1544, 3.0),
        ('middle floor solid balustrade beside opening', [13.29125,1.24,14.715], [0,1,0], 'pale limestone moulding', 1.7094, 3.0),
        ('top of exit step', [9.051250000000001, 2.12, 2.42], [0, 0, -1], 'pale limestone moulding', 2.255, 8.0),
        ('garden outside steps', [8.74125, -0.8, 2.82], [0, 0, -1], None, None, 8.0),
        ('garden wing flat roof (9.12, 6.72)', [9.12, 6.72, 28.15], [0, 0, -1], 'weathered dark flat roof', 3.31, 8.0),
        ('garden wing flat roof (-13.2, -4.62)', [-13.2, -4.62, 28.15], [0, 0, -1], 'weathered dark flat roof', 3.31, 8.0),
        ('garden wing flat roof (27.11, 0.87)', [27.11, 0.87, 28.15], [0, 0, -1], 'weathered dark flat roof', 3.31, 8.0),
    ]
    for check in checks:
        shot(*check)
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
