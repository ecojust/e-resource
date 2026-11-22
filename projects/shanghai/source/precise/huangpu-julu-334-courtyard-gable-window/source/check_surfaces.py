from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).absolute().parent
PROJECT=SOURCE.parents[3]
ID='huangpu-julu-334-courtyard-gable-window'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']




def test(scene):
    import runpy
    g=runpy.run_path(str(SOURCE/'courtyard_gable.py'));samples=[]
    def test_surface(label,u,v,depth,mat):
        hit=scene.ray([g['x'](u),-1,g['z'](v)],[0,1,0],1.8)
        samples.append(dict(feature=label,source_pixel=[u,v],expected_distance=1+depth,actual=hit,
                            passed=bool(hit and hit['material']==mat and abs(hit['distance_m']-1-depth)<.0025)))
    for v in [152,167,183,195,209]:
        for u in [151,158,168,236,244,252]:test_surface('gable wall',u,v,0,'white lime render')
    for v in [62,79,100,117]:
        for u in [185,195,205,215]:test_surface('triangular gable',u,v,0,'white lime render')
    for v in [136,139,150,154,158,164,168]:
        for u in [183,188,198,204,218,224]:test_surface('window pane',u,v,.121,'shaded top glass' if v<142 else 'pale reflected glass')
    for v in [136,149,162,170]:
        for u in [178.2,193,211.15,229]:test_surface('upright',u,v,.068,'pale painted frame')
    for u in [182,187,198,203,216,224]:
        for v in [131.6,143.5,172.73]:test_surface('rail',u,v,.065,'pale painted frame')
        test_surface('sill',u,175,-.042,'cream sill')
    return dict(samples=samples,passed=all(i['passed'] for i in samples))

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
