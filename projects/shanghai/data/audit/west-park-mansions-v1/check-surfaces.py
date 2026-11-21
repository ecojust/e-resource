"""Ray-test all three West Park Mansions GLBs against the garden, rear lightwells and pergolas."""
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
MODEL = 'changning-west-park-mansions'
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
        ('upper infilled arch window 1', [-5.303, -11.3, 21.18], [0, 1, 0], 'muted blue grey apartment glazing', 2.16),
        ('top rectangular window 1', [-5.303, -11.3, 24.18], [0, 1, 0], 'muted blue grey apartment glazing', 2.16),
        ('upper infilled arch window 2', [-3.11, -11.3, 21.18], [0, 1, 0], 'muted blue grey apartment glazing', 2.16),
        ('top rectangular window 2', [-3.11, -11.3, 24.18], [0, 1, 0], 'muted blue grey apartment glazing', 2.16),
        ('upper infilled arch window 3', [-0.917, -11.3, 21.18], [0, 1, 0], 'muted blue grey apartment glazing', 2.16),
        ('top rectangular window 3', [-0.917, -11.3, 24.18], [0, 1, 0], 'muted blue grey apartment glazing', 2.16),
        ('upper infilled arch window 4', [1.277, -11.3, 21.18], [0, 1, 0], 'muted blue grey apartment glazing', 2.16),
        ('top rectangular window 4', [1.277, -11.3, 24.18], [0, 1, 0], 'muted blue grey apartment glazing', 2.16),
        ('upper infilled arch window 5', [3.47, -11.3, 21.18], [0, 1, 0], 'muted blue grey apartment glazing', 2.16),
        ('top rectangular window 5', [3.47, -11.3, 24.18], [0, 1, 0], 'muted blue grey apartment glazing', 2.16),
        ('upper infilled arch window 6', [5.662999999999999, -11.3, 21.18], [0, 1, 0], 'muted blue grey apartment glazing', 2.16),
        ('top rectangular window 6', [5.662999999999999, -11.3, 24.18], [0, 1, 0], 'muted blue grey apartment glazing', 2.16),
        ('wide shallow arch recessed glass 1', [-4.1967, -12.07, 18.48], [0, 1, 0], 'light grey enclosed balcony glass', 3.15),
        ('wide arch curved upper band 1', [-4.3867, -11.97, 19.661], [0, 1, 0], 'pale grey rendered lintel', 2.484),
        ('wide shallow arch recessed glass 2', [0.19, -12.07, 18.48], [0, 1, 0], 'light grey enclosed balcony glass', 3.15),
        ('wide arch curved upper band 2', [0, -11.97, 19.661], [0, 1, 0], 'pale grey rendered lintel', 2.484),
        ('wide shallow arch recessed glass 3', [4.576700000000001, -12.07, 18.48], [0, 1, 0], 'light grey enclosed balcony glass', 3.15),
        ('wide arch curved upper band 3', [4.3867, -11.97, 19.661], [0, 1, 0], 'pale grey rendered lintel', 2.484),
        ('west flanking upright bay window', [-8.92, -11.9, 8.58], [0, 1, 0], 'muted blue grey apartment glazing', 2.76),
        ('west pergola rafter', [-8.706000000000001, -7.080000000000001, 32], [0, 0, -1], 'weathered concrete pergola', 3.23),
        ('west pergola open space', [-9.105, -7.160000000000001, 32], [0, 0, -1], 'dark flat roof finish', 5.72),
        ('west transverse support beam', [-10.82, -8.965000000000002, 32], [0, 0, -1], 'weathered concrete pergola', 3.395),
        ('east flanking upright bay window', [9.225000000000001, -11.9, 8.58], [0, 1, 0], 'muted blue grey apartment glazing', 2.76),
        ('east pergola rafter', [9.439, -7.080000000000001, 32], [0, 0, -1], 'weathered concrete pergola', 3.23),
        ('east pergola open space', [9.040000000000001, -7.160000000000001, 32], [0, 0, -1], 'dark flat roof finish', 5.72),
        ('east transverse support beam', [7.325000000000001, -8.965000000000002, 32], [0, 0, -1], 'weathered concrete pergola', 3.395),
        ('open balcony recessed inner glass', [4.61, -12.1, 8.99], [0, 1, 0], 'muted blue grey apartment glazing', 4.12),
        ('open balcony iron handrail', [4.71, -12.1, 8.51], [0, 1, 0], 'iron balustrade', 2.82),
        ('closed balcony front glazing', [-4.11, -12.1, 8.99], [0, 1, 0], 'light grey enclosed balcony glass', 3.18),
        ('garden wall outer brick band', [-11.51, -11.3, 15.64], [0, 1, 0], 'exposed reddish brick', 1.8),
        ('garden entrance flat canopy', [0.23, -10.15, 6], [0, 0, -1], 'weathered concrete pergola', 2.11),
        ('northern central pier inset window', [0.15, 12.3, 11.73], [0, -1, 0], 'muted blue grey apartment glazing', 4.32),
        ('east lightwell window', [4.85, 12.4, 11.85], [0, -1, 0], 'muted blue grey apartment glazing', 7.33),
        ('west lightwell window', [-5.23, 12.4, 14.98], [0, -1, 0], 'muted blue grey apartment glazing', 7.33),
        ('north pier stucco', [1.54, 12.6, 14.81], [0, -1, 0], 'warm grey roughcast', 4.3),
        ('north east shaft stucco', [12.92, 12.45, 17.29], [0, -1, 0], 'warm grey roughcast', 2.42),
        ('main flat roof', [0.73, 0.58, 32], [0, 0, -1], 'dark flat roof finish', 5.72),
        ('lower side roof', [13.55, -3.52, 32], [0, 0, -1], 'dark flat roof finish', 6.84),
        ('south garden clear of building', [0.11, -13.42, 5.1], [0, 0, -1], None, 0),
        ('west circulation space', [-16.1, 0.42, 4.22], [0, 0, -1], None, 0),
        ('east lightwell lower flat roof', [4.72, 6.99, 10.12], [0, 0, -1], 'dark flat roof finish', 4.88),
        ('west lightwell lower flat roof', [-5.12, 7.18, 10.12], [0, 0, -1], 'dark flat roof finish', 4.08),
        ('east lower podium outer wall', [5.95, 11.79, 2.02], [0, -1, 0], 'warm grey roughcast', 3.51),
        ('west lower podium inset pane', [-5.02, 11.63, 3.31], [0, -1, 0], 'muted blue grey apartment glazing', 3.67),
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
