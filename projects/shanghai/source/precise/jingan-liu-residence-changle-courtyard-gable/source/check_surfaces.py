"""Check the attic framework, four upper casements, lower opening, folded bay, sign, ashlar and roof against the three delivered meshes."""
from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[3]
ID='jingan-liu-residence-changle-courtyard-gable'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']




def test(scene):
    rows=[]
    def cast(label,x,z,targets,depth):
        hit=scene.ray([x,-2.4,z],[0,1,0],4.8)
        ok=not hit if not targets else bool(hit and hit['material'] in targets and depth[0]<=hit['distance_m']<=depth[1])
        rows.append(dict(check=label,x=x,z=z,materials=targets,interval_m=depth,hit=hit,passed=ok))
    for x in (-2.8,-2.3,-.65,.18,2.59):
        for z in (4.82,5.11,5.79,6.16):cast('courtyard render',x,z,['warm cream render'],(2.388,2.399))
    for x in (-1.30,-.71,.73,1.34):
        for z in (6.91,7.24,7.72,7.99):cast('upper casement panes',x,z,['casement glass'],(2.55,2.57))
    for x in (-1.025,1.055):
        for z in (6.99,7.39,7.84):cast('upper central meeting stile',x,z,['warm white sash'],(2.45,2.47))
    for x in (-1.14,-.45,0,.48,1.34):cast('projecting continuous upper sill',x,6.52,['sill edging'],(2.23,2.25))
    for x in (-2.39,-1.84,-1.24,-.58,.58,1.24,1.82,2.39):
        for z in (8.93,9.24,9.53):cast('attic upright',x,z,['dark painted timber'],(2.288,2.304))
    for x in (-.32,-.15,.17,.33):
        for z in (10.17,10.48,10.83):cast('attic casement glass',x,z,['casement glass'],(2.55,2.57))
    for x in (-2.6,-1.67,-.4,.56,1.63,2.6):cast('projecting timber rail',x,8.73,['dark painted timber'],(2.263,2.28))
    for x in (-1.94,-1.70,-1.37,-1.18):
        for z in (2.31,2.65,3.10):cast('lower white-framed panes',x,z,['casement glass'],(2.55,2.57))
        cast('lower transom glass',x,3.78,['transom glass'],(2.535,2.55))
    for x in (.40,.50,2.40,2.53,3.09,3.19):
        for z in (2.27,2.79,3.08):cast('glazing on bay returns',x,z,['casement glass'],(1.67,2.70))
    for x in (.86,1.16,1.72,2.0):
        for z in (2.03,3.15,3.69):cast('flat rendered pier between turns',x,z,['warm cream render'],(1.54,1.56))
    for x in (1.28,1.42,1.59):
        cast('solid brass plaque',x,2.52,['plaque brass'],(1.51,1.525));cast('recessed plinth vent',x,.31,['basement opening'],(1.69,1.71))
    for x in (.73,1.18,1.79,2.07):cast('projecting bay fascia',x,4.38,['dark painted timber'],(1.37,1.40))
    for x in (-.75,.28,1.18,2.28):cast('stone ground course',x,.91,['base stone'],(1.40,2.41))
    for x in (-4.1,-3.74,4.03,4.4):cast('clear space beside roof',x,10.31,[],(0.,0.))
    return dict(passed=all(v['passed']for v in rows),samples=rows)


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
            if role!='raw':mesh.unlink()
    result=dict(id=ID,manifest_sha256=digest(args.manifest),checker_sha256=digest(Path(__file__)),
                reader_sha256=digest(READER),decoder_sha256=digest(DECODER),results=rows)
    args.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    for role,r in rows.items():print(role,'pass' if r['passed'] else [q for q in r['samples'] if not q['passed']])
    return all(r['passed'] for r in rows.values())


if __name__=='__main__':
    raise SystemExit(0 if main() else 1)
