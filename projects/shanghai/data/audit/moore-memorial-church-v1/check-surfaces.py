"""Probe the three finished meshes for the three western gables, recessed nave window, two belfry stages, independent annexes and open courtyards."""
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
CROSS_MATERIAL='painted red iron cross'
MODEL = 'huangpu-moore-memorial-church'
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

    def native(x,y,z):return [-y,x,z]
    def west(label,x,y,z,material,depth=2):
        expect(label,native(x-2,y,z),[0,1,0],material,depth)
    def down(label,x,y,z,material,depth=None):
        expect(label,native(x,y,z),[0,0,-1],material,depth)
    cy=1.20;clay='dark red face brick';stone='pale limestone bands';glass='blue grey church glass'
    west('recessed sanctuary glazing',-14.20,cy-.52,11.47,glass,2.366)
    west('western sanctuary timber door behind open porch',-14.20,cy+.27,2.3,'wood door',2.466)
    west('stone front porch jamb',-15.72,cy-2.0,2.25,stone,2)
    west('western cross relief',-14.20,cy,19.47,stone,1.867)
    for name,x,y,w in [('northwest',-29.91,(10.53+25.21)/2,14.68),('southwest',-25.15,(-21.42-7.90)/2,13.52)]:
        for sg in [-1,1]:
            west(name+' lower paired windows '+str(sg),x,y+sg*w*.29+.21,2.06,glass,2.366)
        for z in [5.41,9.12]:
            west(name+' projecting three-light oriel',x,y+.51,z,glass,1.72)
        west(name+' attic gable solid masonry',x,y+2.6,14.96,clay)
        west(name+' upper small window',x,y-.47+.135,16.58,glass,2.366)
    west('tower lower stage glazed lancets',-8.30,-10.66+.54,16.04,glass,2.366)
    west('tower upper stage dark screen',-8.30,-10.66+.55,29.78,'metal belfry screens',2.366)
    west('tower crown masonry',-8.30,-10.66+.51,36.83,clay)
    down('belfry cross upright',-4.58,-10.66,45,CROSS_MATERIAL,2.17)
    down('belfry cross horizontal arm',-4.58,-11.58,45,CROSS_MATERIAL,3.50)
    down('east annex low roof',27,-15,23,'roof zinc',10.73)
    for x,y,name in [(-20,0,'western forecourt'),(8,-15,'lane between tower and rear wing'),(28,0,'open east corner'),(-33,16,'Tibet Road pavement')]:
        down(name,x,y,25,None)
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
