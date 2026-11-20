"""Cast rays through the delivered villa at the double gables, stepped roof, chimneys, gallery and west connector."""
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
MODEL = 'changning-luobiegen-garden-villa'
READER = PROJECT / 'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK = PROJECT / 'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER = PROJECT / 'vendor/meshopt_decoder.module.js'
SerialScene = runpy.run_path(str(READER))['SerialScene']


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def probes(mesh):
    scene=SerialScene(mesh)
    records=[]

    def expect(label,origin,direction,material,depth=None):
        hit=scene.ray(origin,direction,30)
        passed=hit is None if material is None else (
            hit is not None and hit['material']==material and abs(hit['distance_m']-depth)<.04)
        records.append({'label':label,'origin_m':origin,'direction':direction,
                        'material':material,'expected_distance_m':depth,'first_hit':hit,'passed':passed})

    # Coordinates below refer to the measured roof grid. The revised model origin
    # is 2.70 metres east along its own X axis from that drawing origin.
    def witness(name, x, y, z, direction, material, depth=None):
        expect(name,[x-2.7,y,z],direction,material,depth)
    front=[0,1,0];down=[0,0,-1]
    for center,width in [(-4.92,5.06),(4.76,6.16)]:
        witness('upper bay glazing',center+.32,-16,4.83,front,'leaded glazing',6.39)
        witness('lower bay casement',center+.32,-16,1.37,front,'leaded glazing',6.39)
        witness('lower casement horizontal sash',center+.32,-16,1.57,front,'window leading',6.31)
        witness('brickwork beside casement',center+width*.43,-16,1.62,front,'brickwork',6.125)
        witness('timbered gable king post',center,-16,7.52,front,'dark Tudor timber',6.01)
    witness('recessed balcony glazing',-.08,-16,4.85,front,'leaded glazing',8.07)
    witness('recessed hall glazing',-.08,-16,1.62,front,'leaded glazing',8.07)
    witness('east ground bay',18,2.67,1.54,[-1,0,0],'leaded glazing',5.40)
    witness('east upper bay',18,-2.39,4.35,[-1,0,0],'leaded glazing',5.40)
    witness('rear upper light',4.63,14,4.84,[0,-1,0],'leaded glazing',4.63)
    witness('rear lower light',4.63,14,1.59,[0,-1,0],'leaded glazing',4.63)
    witness('east chimney flue',11.92,.74,15,down,'deep shade',4.19)
    witness('inner chimney flue',-2.93,2.98,15,down,'deep shade',3.95)
    witness('middle roof pitch',0,-5.02,14,down,'terracotta roofing',4.94)
    # Horizontal rays enter the former open gable ends above adjacent pitches.
    witness('west end of main ridge',-8.52,-2.225,10.20,[1,0,0],'lime plaster',1.03)
    witness('east end of main ridge',8.98,-2.225,10.16,[-1,0,0],'lime plaster',1.11)
    witness('north return of west garden gable',-4.96,1.20,10.41,[0,-1,0],'lime plaster',1.21)
    witness('north return of east garden gable',4.76,1.35,10.45,[0,-1,0],'lime plaster',1.00)
    witness('south return of rear gable',.59,1.95,9.95,[0,1,0],'lime plaster',.86)
    witness('end gable above east room',14.08,-.285,8.09,[-1,0,0],'lime plaster',1.20)
    witness('enclosed ground floor',.35,0,1.75,down,'warm cut stone',1.645)
    for x,y,z in [(-.32,-9.32,1.72),(0,-15,16),(-14.5,4.10,16),(16,0,16)]:
        witness('open balcony threshold, garden or independent structure',x,y,z,down,None)
    return dict(triangles=len(scene.tri),probes=records,passed=all(r['passed'] for r in records))


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
            results[role]=dict(sha256=asset['sha256'],file=path.name,**probes(decoded))
    report={'id':MODEL,'script_sha256':digest(Path(__file__)),'manifest_sha256':digest(args.manifest),
            'decoder_sha256':digest(DECODER),'reader_sha256':digest(READER),'results':results,
            'scope':'Checks only the sampled physical geometry in local axes; placement and viewing use independent records.'}
    args.out.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
    for role,test in results.items():
        print(role,'passed' if test['passed'] else [r for r in test['probes'] if not r['passed']])
    return all(r['passed'] for r in results.values())


if __name__=='__main__':
    raise SystemExit(0 if main() else 1)
