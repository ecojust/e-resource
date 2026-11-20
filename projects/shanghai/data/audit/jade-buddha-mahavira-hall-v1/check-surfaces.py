"""Measure both eaves, the raised terrace, screen doors and source-confirmed signage on the delivered three meshes."""
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
MODEL = 'putuo-jade-buddha-mahavira-hall'
READER = PROJECT / 'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK = PROJECT / 'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER = PROJECT / 'vendor/meshopt_decoder.module.js'
SerialScene = runpy.run_path(str(READER))['SerialScene']


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def probes(mesh, role):
    scene=SerialScene(mesh);records=[]
    def expect(label,origin,direction,material,depth=None,tolerance=.045):
        hit=scene.ray(origin,direction,100)
        passed=hit is None if material is None else (hit is not None and hit['material']==material and abs(hit['distance_m']-depth)<tolerance)
        records.append({'label':label,'origin_m':origin,'direction':direction,'material':material,'expected_distance_m':depth,'tolerance_m':tolerance,'first_hit':hit,'passed':passed})
    def front(label,x,z,mat,dist,tol=.05):
        expect(label,[x,-15,z],[0,1,0],mat,dist,tol)
    def above(label,x,y,mat,height,tol=.09):
        expect(label,[x,y,20],[0,0,-1],mat,20-height,tol)
    tile='weathered graphite clay tiles';cap='silver grey ridge tiles'
    wall='ochre lime plaster';step='pale granite treads';wood='dark lacquered timber'
    dark='recessed door and screen shadow';red='cinnabar plaque and posts';gold='warm gilt lettering'
    # Lower front eaves curve upward towards the east and west hips. Pick
    # material between the tile ribs and clear of the diagonal verge.
    for x,y,h in [(-.26,-9.98,6.01),(3.03,-9.98,6.01),(-8.7,-10,6.12),(8.7,-10,6.12),
                  (-13.15,-10.16,7.00),(13.15,-10.16,6.95)]:
        above('lower eave field; corners rise from the centre',x,y,tile,h,.25)
    for x,y,h in [(.21,-5.82,9.88),(3.11,-5.92,9.80),(-2.77,-5.92,9.80)]:
        material=cap if role=='lod' and x==-2.77 else tile
        above('upper roof plain field or convex tile run in the spaced LOD ribs',x,y,material,h,.14)
    for x in [-3.15,0,3.15]:
        above('top of separate ceramic ridge frieze',x,0,cap,13.185,.04)
    for x in [-4.26,-1.42,1.42,4.26]:
        front('red square tablet outside the lettering',x-.62,8.36,red,8.5925)
    for x in [-10.66,-8.26,8.26,10.66]:
        front('yellow wall flanking screens',x,2.42,wall,8.13)
    for x in [-7.77,-2.65,2.65,7.77]:
        front('round outer timber post',x,2.52,wood,6.94,.04)
    for x in [-7.77,-2.65,2.65,7.77]:
        front('projecting joinery above each porch post',x,5.35,red,6.79,.05)
    for x in [-9.38,9.38]:
        front('carved stone ring cut into ochre wall',x+.77,3.65,step,8.04,.05)
    for x in [-12.9,12.9]:
        expect('walkable space underneath projecting roof',[x,-8.5,1.93],[0,1,0],None)
    front('central stone stair riser',0,.10,step,4.18,.02)
    front('top central tread riser',0,.88,step,5.98,.025)
    # The plate under the larger entrance text is inset from the porch lintel.
    front('inner door panel background clear of inscription',1.43,5.01,gold,6.785,.04)
    for x,y in [(0,-15),(0,-30),(-17,0),(17,0),(0,14)]:
        expect('clear side route or forecourt outside the eaves',[x,y,20],[0,0,-1],None)

    # The four rays cross places where the first native review detected a
    # projecting soffit. Each roofing ray must now see tile from above.
    first=json.loads((SOURCE/'first-eaves-diagnostic.json').read_bytes())
    for point in first['samples']:
        origin=[point['x'],point['y'],18.]
        hit=scene.ray(origin,[0,0,-1],18)
        expected=point['old_roof_hit']['point_enu_m'][2]
        passed=(hit is not None and hit['material'] in (tile,cap)
                and abs(hit['point_enu_m'][2]-expected)<(.27 if role=='lod' else .07))
        records.append({'label':'lower hip tiles conceal the timber soffit','origin_m':origin,
                        'direction':[0,0,-1],'permitted_materials':[tile,cap],
                        'roof_height_m':expected,'first_hit':hit,'passed':passed})
    for x,y in [(-9.68,-.95),(-9.70,1.79),(9.68,-.95),(9.70,1.79)]:
        origin=[x,y,18.]
        hit=scene.ray(origin,[0,0,-1],18)
        passed=(hit is not None and hit['material'] in (tile,cap) and 9.68<hit['point_enu_m'][2]<9.91)
        records.append({'label':'upper roof hides the timber drum at side eaves','origin_m':origin,
                        'direction':[0,0,-1],'permitted_materials':[tile,cap],'first_hit':hit,'passed':passed})
    return {'passed':all(r['passed']for r in records),'probes':records,'probe_count':len(records)}

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
