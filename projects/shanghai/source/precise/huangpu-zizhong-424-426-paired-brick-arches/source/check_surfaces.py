from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).absolute().parent
PROJECT=SOURCE.parents[3]
ID='huangpu-zizhong-424-426-paired-brick-arches'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']




def test(scene,role):
    g=runpy.run_path(str(SOURCE/'brick_arches.py'))
    rows=[]
    def check(label,x,z,depth,materials):
        hit=scene.ray([x,-1,z],[0,1,0],1.65)
        rows.append(dict(feature=label,xz_m=[x,z],expected_depth=depth,materials=materials,hit=hit,passed=bool(hit and hit['material'] in materials and abs(hit['distance_m']-1-depth)<.002)))
    count=16 if role=='lod' else 24
    for name,q in g['SURVEY'].items():
        for i in range(count):
            t=(i+.43)/count;outer=g['curve'](q['outer'],t);inner=g['curve'](q['inner'],t)
            for fraction in [.37,.68]:
                x,z=[a*(1-fraction)+b*fraction for a,b in zip(outer,inner)]
                check(name+' brick '+str(i+1),x,z,-.044,['red brick A','red brick B','red brick C'])
        for i in range(9):
            u=.12+.089*i
            a,b,c,d=q['sill'];x,z=[(a[j]+d[j])*.5*(1-u)+(b[j]+c[j])*.5*u for j in (0,1)]
            check(name+' stone sill',x,z,-.138,['stone sill'])
    for k in range(11 if role=='lod' else 19):
        j=(k+.5)/(11 if role=='lod' else 19);check('closed 426 shutter',-1.02+.063*j,.454+.918*j,.154,['dark timber'])
    for j in range(7):check('424 recessed opening',.79+.04*j,.75+.049*j,.29,['open interior'])
    return dict(samples=rows,passed=all(z['passed'] for z in rows))

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
