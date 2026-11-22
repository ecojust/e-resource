from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).absolute().parent
PROJECT=SOURCE.parents[3]
ID='jingan-percy-woo-three-pointed-arches'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']








def test(scene,role):
    from math import sqrt
    src=runpy.run_path(str(SOURCE/'brick_arcade.py'));rows=[]
    def probe(label,x,z,mats,lo,hi):
        hit=scene.ray([x,-.6,z],[0,1,0],1.25)
        ok=hit is not None and hit['material'] in mats and lo<=hit['distance_m']<=hi
        rows.append(dict(feature=label,x=x,z=z,expected_material=sorted(mats),distance_interval_m=[lo,hi],hit=hit,passed=ok))
    for j,c in enumerate(src['CENTERS']):
        for k in range(1,8):
            x=c+src['HALF']*(k-4)/5
            probe('blind arch panel',x,2.24+(k%2)*.055,{'recessed lime'},.711,.715)
        for side in (-1,1):
            divisions=9 if role=='lod' else 12
            for k in range(divisions-1):
                t=(k+.5)/divisions
                x,z=src['curve'](c,side,t,.049)
                probe('individual radial brick',x,z,{f'face brick {m+1}'for m in range(5)},.579,.583)
        for side in (-1,1):
            for z in (.55,1.05,1.48,1.78):
                probe('recessed painted window',c+side*.233,z,{'glazing shadow','blue glazing'},.805,.809)
        for k in range(5):
            probe('stone head',c+(k-2)*.12,2.04,{'cut stone'},.637,.641)
    for x in src['AXES']:
        for k in range(29):
            z=.11+k*.062
            probe('twisted shaft central section',x,z,{'spiral stone'},.474,.502)
        for k in range(7):probe('broad capital abacus',x+(k-3)*.028,2.066,{'carved highlight'},.424,.428)
    return dict(samples=rows,passed=all(s['passed'] for s in rows))

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
            rows[role]=dict(sha256=a['sha256'],**test(SerialScene(mesh),role))
            if role!='raw':mesh.unlink()
    result=dict(id=ID,manifest_sha256=digest(args.manifest),checker_sha256=digest(Path(__file__)),
                reader_sha256=digest(READER),decoder_sha256=digest(DECODER),results=rows)
    args.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    for role,r in rows.items():print(role,'pass' if r['passed'] else [q for q in r['samples'] if not q['passed']])
    return all(r['passed'] for r in rows.values())


if __name__=='__main__':
    raise SystemExit(0 if main() else 1)
