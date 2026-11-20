"""Check the through passage, both fronts, ceramic roof, four-character plaque and guardian lions."""
from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[3]
ID='xuhui-nanyang-campus-gate'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']


def test(scene):
    import numpy as np
    rows=[]
    def probe(label,origin,direction,material,depth,tol=.043):
        hit=scene.ray(list(origin),list(direction),50)
        ok=hit is None if material is None else bool(hit and hit['material']==material and abs(hit['distance_m']-depth)<tol)
        rows.append(dict(label=label,origin=list(origin),direction=list(direction),reference_depth_m=depth,
                         expected_material=material,hit=hit,passed=ok))

    for x in [-.95,-.32,.0,.32,.95]:
        for z in [.24,1.15,2.02,3.12]:
            probe('clear from street through both door frames',[x,-3,z],[0,1,0],None,None)
            probe('clear reverse sightline out to Huashan Road',[x,15,z],[0,-1,0],None,None)
    for s in [-1,1]:
        for x in [3.25,4.18,6.61]:
            probe('pale stone base of brick wing',[s*x,-.02,.86],[0,1,0],'silvery grey rendered plinth',1.645)
            probe('brick street wall above the base',[s*x,-.02,2.71],[0,1,0],'salmon red brick',1.63)
        for x in [3.72,4.70,5.51,6.46]:
            probe('campus side window glass',[s*x,13,2.65],[0,-1,0],'old smoky glazing',2.61)
            probe('campus side red transom',[s*x,13,3.45],[0,-1,0],'oxblood timber',2.52)
        probe('fixed side door panel in recess',[s*1.98,1.8,1.03],[0,1,0],'oxblood timber',2.93)
        probe('raised stone lion plinth from the road',[s*4.97,-4,.15],[0,1,0],'pale carved lion stone',2.18,.12)
        probe('air under the prow of the long eaves',[s*7.88,-2,3.5],[0,1,0],None,None)
        probe('lion nose in front of the curled mane',[s*4.97,-4,2.238],[0,1,0],'pale carved lion stone',2.27,.05)
    for x,y in [[0,-3.10],[-7.72,-1.4],[7.72,-1.4],[8.65,6.01],[-8.65,6.01],[1.62,12.83]]:
        probe('air beyond gate and independent lions',[x,y,12],[0,0,-1],None,None)
    for x in [-3.61,-1.03,0,1.03,3.61]:
        probe('main ridge rises above the tile fields',[x,6.02,12],[0,0,-1],'dark green glazed tile',3.89)
    for x in [-4.98,4.98]:
        probe('high inward-scroll ridge terminal',[x,6.04,8.27],[0,1,0],'dark green glazed tile',.086,.28)
    for g in json.loads((SOURCE/'name-probes.json').read_text()):
        probe('visible stroke of '+g['char'],[g['x'],-2,g['z']],[0,1,0],'ink black',3.511)
    for z in [3.58,3.03,2.48]:
        probe('white sign between adjacent characters',[3.62,-2,z],[0,1,0],'ivory signboard',3.53,.045)
    return dict(triangles=len(scene.tri),samples=rows,passed=all(x['passed']for x in rows))


def digest(p):
    return sha256(p.read_bytes()).hexdigest()


def main():
    ap=ArgumentParser(description=__doc__)
    ap.add_argument('--manifest',type=Path,default=PROJECT/'assets/models/candidates'/ID/'manifest.json')
    ap.add_argument('--out',required=True,type=Path)
    args=ap.parse_args()
    m=json.loads(args.manifest.read_bytes())
    assert m['id']==ID
    rows={}
    with tempfile.TemporaryDirectory() as directory:
        for role in ('raw','full','lod'):
            a=m['assets'][role]
            original=args.manifest.parent/a['file']
            assert original.stat().st_size==a['bytes'] and digest(original)==a['sha256']
            mesh=original
            if role!='raw':
                mesh=Path(directory)/(role+'.glb')
                subprocess.run(['node',UNPACK,original,mesh,DECODER],check=True,stdout=subprocess.DEVNULL)
            rows[role]=dict(sha256=a['sha256'],**test(SerialScene(mesh)))
    result=dict(id=ID,manifest_sha256=digest(args.manifest),checker_sha256=digest(Path(__file__)),
                reader_sha256=digest(READER),decoder_sha256=digest(DECODER),results=rows)
    args.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    for role,r in rows.items():print(role,'pass' if r['passed'] else [q for q in r['samples'] if not q['passed']])
    return all(r['passed'] for r in rows.values())


if __name__=='__main__':
    raise SystemExit(0 if main() else 1)
